"""The shopping list: Notion boxes resolved against the catalogue.

Hides label resolution and the "safe to commit" rule.
"""

from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

from food.core import history
from food.core.catalogue import Catalogue, Status


@dataclass(frozen=True)
class Box:
    """One to-do checkbox on the shopping list, so neither core nor callers touch connector JSON."""
    label: str
    need: bool  # unchecked on Notion: lacking at home
    id: str


class _Line(NamedTuple):
    """One resolved box, before a commit's date turns it into a list entry."""
    item: str
    box: Box


class ShoppingList:
    """Resolve boxes into items in one place, so pull and push resolve labels identically."""
    unknowns: list[str]  # labels matching no catalogue alias; block commit
    inactives: list[str]  # labels matching an inactive item; block commit
    duplicates: list[str]  # items with several boxes, whose need would be ambiguous; block commit and push
    missing: list[str]  # active items with no box on the page; block commit
    rows: int  # history rows commit() would append, one per resolved box
    _lines: list[_Line]

    def __init__(self, boxes: list[Box], catalogue: Catalogue) -> None:
        """Resolve boxes without I/O so the list can be inspected before anything is committed."""
        self.unknowns, self.inactives, self._lines = [], [], []
        for box in boxes:
            status, item = catalogue.classify(box.label)
            if status == Status.OK:
                self._lines.append(_Line(item, box))
            elif status == Status.INACTIVE:
                self.inactives.append(item)
            else:
                self.unknowns.append(item)
        resolved = [line.item for line in self._lines]
        self.duplicates = sorted({item for item in resolved if resolved.count(item) > 1})
        self.missing = sorted(catalogue.active_items - set(resolved))
        self.rows = len(self._lines)

    def find_boxes(self, wanted: list[str]) -> tuple[list[Box], list[str]]:
        """Find wanted items' boxes via this list's resolution, so push unticks exactly what pull reads back."""
        by_item = {line.item: line.box for line in self._lines}
        found = [by_item[item] for item in wanted if item in by_item]
        return found, [item for item in wanted if item not in by_item]

    def commit(self, day: date, path: str | None = None) -> int:
        """Commit the list's needs to history (default File.HISTORY) dated day, so they become training data; ValueError if any label is unresolved or active item missing."""
        if self.unknowns or self.inactives or self.duplicates or self.missing:
            raise ValueError(f"unresolved labels: unknown {self.unknowns}, inactive {self.inactives}, "
                             f"duplicate {self.duplicates}; missing active items {self.missing}")
        iso = day.isoformat()
        return history.append([(line.item, iso, line.box.need) for line in self._lines], path)
