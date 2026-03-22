from datetime import date

import pytest

from food.core.history import ListEntry
from food.core.model import Predictor

_DAYS = ["2026-01-01", "2026-01-08", "2026-01-15", "2026-01-22", "2026-01-29", "2026-02-05"]
_HISTORY = [ListEntry(item, day, need)
            for i, day in enumerate(_DAYS)
            for item, need in [("milk", True), ("bread", i % 2 == 0), ("eggs", i % 3 == 0), ("tofu", False)]]


def test_rank_items_orders_active_items_by_probability():
    """Only active items are ranked, most likely first, with probabilities in [0, 1]."""
    ranked = Predictor(_HISTORY, {"milk", "bread", "eggs"}).rank_items(date(2026, 2, 12))

    assert {p.item for p in ranked} == {"milk", "bread", "eggs"}
    assert [p.prob for p in ranked] == sorted((p.prob for p in ranked), reverse=True)
    assert all(0 <= p.prob <= 1 for p in ranked)
    assert ranked[0].item == "milk"


def test_cv_aucs_are_per_held_out_commit():
    """CV scores are keyed by commit date and are valid AUCs, available right after construction."""
    predictor = Predictor(_HISTORY, {"milk", "bread", "eggs"})

    assert predictor.cv_aucs
    assert set(predictor.cv_aucs) <= {date.fromisoformat(d) for d in _DAYS}
    assert all(0 <= auc <= 1 for auc in predictor.cv_aucs.values())


def test_too_little_history_fails_clearly():
    """With fewer than two commits there is nothing to learn from, so construction says so."""
    one_commit = [p for p in _HISTORY if p.date == _DAYS[0]]

    with pytest.raises(ValueError, match="at least two commits"):
        Predictor(one_commit, {"milk", "bread", "eggs"})
