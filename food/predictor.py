"""Train a need classifier on history and rank active items for today."""

import argparse
from datetime import datetime

import numpy as np

from food.core import history
from food.core.catalogue import Catalogue
from food.core.model import Predictor
from food.core.prediction import Prediction
from food.core.shared import File, warn_stale_files

_TOP_N_DEFAULT = 25


def main() -> None:
    """CLI: train on history, report CV AUCs, write today's top-N handoff (--top-n)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=_TOP_N_DEFAULT,
                        help=f"Number of items to write to {File.TEMP_PREDICT} (default {_TOP_N_DEFAULT})")
    args = parser.parse_args()
    warn_stale_files()

    active = Catalogue(File.CATALOGUE).active_items
    entries = history.read()
    print(f"Active items: {len(active)}, list entries: {len(entries)}")
    predictor = Predictor(entries, active)
    for day, auc in predictor.cv_aucs.items():
        print(f"Holdout {day}: AUC={auc:.3f}")
    if predictor.cv_aucs:
        print(f"Mean CV AUC: {np.mean(list(predictor.cv_aucs.values())):.3f}")

    today = datetime.now().astimezone().date()
    ranked = predictor.rank_items(today)
    print(f"\n=== Top {args.top_n} predicted needed on {today} ===")
    for p in ranked[:args.top_n]:
        print(f"{p.item:<30} {p.prob:.3f}")
    print("\n=== Bottom 10 (least likely) ===")
    for p in ranked[-10:]:
        print(f"{p.item:<30} {p.prob:.3f}")

    Prediction.write_handoff(ranked[:args.top_n])
    print(f"Wrote {File.TEMP_PREDICT} ({len(ranked[:args.top_n])} items)")


if __name__ == "__main__":
    main()
