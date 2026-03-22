"""Names shared by restock.py and predictor.py: data files and their keys/columns.

Stdlib-only so restock.py's environment can import it without pandas or sklearn.
"""

from enum import StrEnum
from pathlib import Path

_ROOT = Path(__file__).parent.parent  # food/: data/ lives beside core/
# Earlier names and places of the data files, relative to food/, mapped to where they live now.
_STALE_FILES = {
    "grocery_db.csv": "data/history.csv",
    "items.yaml": "data/catalogue.yaml",
    "data/grocery_db.csv": "data/history.csv",
    "data/items.yaml": "data/catalogue.yaml",
}


class File:
    """Resource paths are anchored at the repo root, independent of the cwd."""
    CATALOGUE = str(_ROOT / "data" / "catalogue.yaml")
    HISTORY = str(_ROOT / "data" / "history.csv")
    TEMP_CATALOGUE_STUBS = "/tmp/catalogue_stubs.yaml"
    TEMP_PREDICT = "/tmp/predict.yaml"


class ItemKey(StrEnum):
    ITEM = "item"
    ALIASES = "aliases"
    ACTIVE = "active"


class RowKey(StrEnum):
    DATE = "date"
    NEED = "need"
    ITEM = "item"
    PROB = "prob"


def warn_stale_files():
    """Flag data files left under an earlier name or place, which the scripts would silently ignore."""
    for stale, current in _STALE_FILES.items():
        if (_ROOT / stale).exists():
            print(f"WARNING: food/{stale} found; the scripts read food/{current}. "
                  f"Move it: mv food/{stale} food/{current}")
