"""History: the append-only history.csv log of every committed shopping list.

Older commits stored a quantity N as N identical rows; read() collapses them, so callers
never see that encoding. Stdlib-only so predictor.py's PEP 723 `uv run` environment can import it.
"""

import csv
import os
from typing import NamedTuple

from food.core.shared import File, RowKey

_FIELDS = [RowKey.ITEM, RowKey.DATE, RowKey.NEED]


class ListEntry(NamedTuple):
    item: str
    date: str  # ISO date of the commit
    need: bool


def append(entries, path=None):
    """Append [(item, date, need)] and return the number of rows written.

    `path` defaults to File.HISTORY at call time, so tests can redirect it."""
    path = path or File.HISTORY
    write_header = not os.path.exists(path)
    written = 0
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if write_header:
            writer.writeheader()
        for item, day, need in entries:
            writer.writerow({RowKey.ITEM: item, RowKey.DATE: day, RowKey.NEED: need})
            written += 1
    return written


def read(path=None):
    """One ListEntry per (item, date); need is True if any of its rows was needed."""
    path = path or File.HISTORY
    merged = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            key = (r[RowKey.ITEM], r[RowKey.DATE])
            merged[key] = merged.get(key, False) or r[RowKey.NEED] == "True"
    return [ListEntry(item, day, need) for (item, day), need in merged.items()]
