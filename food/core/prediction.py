"""Handoff of ranked predictions from predictor.py to restock.py push.

Needs only pyyaml, so restock's environment can import it without pandas or sklearn.
"""

from dataclasses import dataclass

import yaml

from food.core.shared import File, RowKey


@dataclass(frozen=True)
class Prediction:
    """One item's buy probability; owns the handoff file so its format lives in one place."""
    item: str
    prob: float

    @staticmethod
    def write_handoff(preds: list["Prediction"], path: str | None = None) -> None:
        """Write predictions in order to the handoff file (default File.TEMP_PREDICT) for a later push."""
        data = [{str(RowKey.ITEM): p.item, str(RowKey.PROB): round(p.prob, 4)} for p in preds]
        with open(path or File.TEMP_PREDICT, "w") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @staticmethod
    def read_handoff(path: str | None = None) -> list["Prediction"]:
        """Read the handoff file write_handoff wrote, so push never parses the file format itself."""
        with open(path or File.TEMP_PREDICT) as f:
            data = yaml.safe_load(f) or []
        return [Prediction(d[RowKey.ITEM], d[RowKey.PROB]) for d in data]
