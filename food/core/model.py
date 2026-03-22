"""Need classifier: features, model and leave-one-commit-out CV behind Predictor."""

from datetime import date
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from food.core.history import ListEntry
from food.core.prediction import Prediction
from food.core.shared import RowKey

_NUMERIC_FEATURES = [
    "days_since_last_need",
    "days_since_last_appearance",
    "inter_need_avg",
    "inter_need_std",
    "item_need_rate",
    "times_needed_last_60d",
    "month",
    "day_of_week",
    "days_since_last_commit",
]
# Plain str, not RowKey: sklearn rejects mixed str/StrEnum feature names.
_ITEM_FEATURE = str(RowKey.ITEM)
_FEATURE_COLS = _NUMERIC_FEATURES + [_ITEM_FEATURE]
_TARGET = "target"

# Sentinel for "no history yet"; large enough that LR's recency feature treats it as far in the past.
_NO_HISTORY = 999
_RECENT_WINDOW_DAYS = 60


class Predictor:
    """Hide features, model and CV so callers only see items and probabilities."""
    cv_aucs: dict[date, float]  # leave-one-commit-out AUC per held-out commit
    model: Pipeline  # fitted on all history; exposed for experiment logging

    def __init__(self, entries: list[ListEntry], active: set[str]) -> None:
        """Train on construction so rank_items() can never be called on an unfitted model."""
        db = pd.DataFrame(entries, columns=list(ListEntry._fields))
        db[RowKey.DATE] = pd.to_datetime(db[RowKey.DATE])
        self._db = db[db[RowKey.ITEM].isin(active)].reset_index(drop=True)
        self._active = sorted(active)
        frame = _build_training_frame(self._db, self._active)
        if frame.empty:
            raise ValueError("need at least two commits with active items to train on")
        self.cv_aucs = _cross_validate(frame)
        self.model = _build_pipeline()
        self.model.fit(frame[_FEATURE_COLS], frame[_TARGET])

    def rank_items(self, day: date) -> list[Prediction]:
        """Rank active items by need probability on day, so push can suggest the top ones."""
        target = pd.Timestamp(day)
        frame = pd.DataFrame([_compute_features(self._db, target, item) for item in self._active])
        probs = self.model.predict_proba(frame[_FEATURE_COLS])[:, 1]
        ranked = [Prediction(item, float(prob)) for item, prob in zip(self._active, probs)]
        return sorted(ranked, key=lambda p: p.prob, reverse=True)


def _count_days_since(target_date: pd.Timestamp, dates) -> int:
    """Count days since the last date, shared by all three recency features; _NO_HISTORY if none."""
    if not len(dates):
        return _NO_HISTORY
    return (target_date - dates.max()).days


def _compute_features(db: pd.DataFrame, target_date: pd.Timestamp, item: str) -> dict[str, Any]:
    """Compute an item's features from history before target_date; shared by training and ranking so they can't drift."""
    item_hist = db[(db[RowKey.ITEM] == item) & (db[RowKey.DATE] < target_date)]
    need_hist = item_hist[item_hist[RowKey.NEED]]
    all_dates_before = db.loc[db[RowKey.DATE] < target_date, RowKey.DATE].unique()

    if len(need_hist) >= 2:
        diffs = need_hist[RowKey.DATE].sort_values().diff().dt.days.dropna()
        inter_need_avg = float(diffs.mean())
        inter_need_std = float(diffs.std()) if len(diffs) > 1 else 0.0
    else:
        inter_need_avg = float(_NO_HISTORY)
        inter_need_std = 0.0

    cutoff = target_date - pd.Timedelta(days=_RECENT_WINDOW_DAYS)

    return {
        _ITEM_FEATURE: item,
        "days_since_last_need": _count_days_since(target_date, need_hist[RowKey.DATE]),
        "days_since_last_appearance": _count_days_since(target_date, item_hist[RowKey.DATE]),
        "inter_need_avg": inter_need_avg,
        "inter_need_std": inter_need_std,
        # Beta(1,1)-smoothed need rate
        "item_need_rate": (len(need_hist) + 1) / (len(item_hist) + 2),
        "times_needed_last_60d": int((need_hist[RowKey.DATE] >= cutoff).sum()),
        "month": target_date.month,
        "day_of_week": target_date.weekday(),
        "days_since_last_commit": _count_days_since(target_date, all_dates_before),
    }


def _build_training_frame(db: pd.DataFrame, active_items: list[str]) -> pd.DataFrame:
    """Build one labelled row per (item, commit), skipping the first commit since it has no history to learn from."""
    unique_dates = sorted(db[RowKey.DATE].unique())
    rows = []
    # Skip earliest date: no history → all features are sentinels, useless for training
    for day in unique_dates[1:]:
        for item in active_items:
            mask = (db[RowKey.ITEM] == item) & (db[RowKey.DATE] == day)
            if not mask.any():
                continue  # item not on this commit's list
            feats = _compute_features(db, day, item)
            feats[_TARGET] = int(db.loc[mask][RowKey.NEED].iloc[0])
            feats[RowKey.DATE] = day
            rows.append(feats)
    return pd.DataFrame(rows)


def _build_pipeline() -> Pipeline:
    """Build the single definition of the production model: scaled numerics + one-hot item into logistic regression."""
    preproc = ColumnTransformer(
        [
            ("num", StandardScaler(), _NUMERIC_FEATURES),
            ("item", OneHotEncoder(handle_unknown="ignore"), [_ITEM_FEATURE]),
        ]
    )
    return Pipeline(
        [("preproc", preproc), ("lr", LogisticRegression(max_iter=1000, C=1.0))]
    )


def _cross_validate(frame: pd.DataFrame) -> dict[date, float]:
    """Cross-validate leaving one commit out; random splits would leak same-commit context."""
    aucs = {}
    for held_out in sorted(frame[RowKey.DATE].unique()):
        train = frame[frame[RowKey.DATE] != held_out]
        test = frame[frame[RowKey.DATE] == held_out]
        if test[_TARGET].nunique() < 2:
            continue  # AUC undefined if test has only one class
        pipe = _build_pipeline()
        pipe.fit(train[_FEATURE_COLS], train[_TARGET])
        probs = pipe.predict_proba(test[_FEATURE_COLS])[:, 1]
        aucs[pd.Timestamp(held_out).date()] = float(roc_auc_score(test[_TARGET], probs))
    return aucs
