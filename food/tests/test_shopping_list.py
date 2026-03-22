from datetime import date

import pytest

from food.core import history
from food.core.catalogue import Catalogue
from food.core.shopping_list import Box, ShoppingList

_DAY = date(2026, 1, 1)
_BOXES = [Box("Milk", True, "b1"), Box("Eggs 2", False, "b2"),
          Box("Tofu", True, "b3"), Box("OldItem", True, "b4")]


def test_list_reports_unknown_inactive_missing_and_counts_rows(tmp_path, write_items):
    """Unknown, inactive and missing items are reported; a quantity note adds no history rows."""
    shopping_list = ShoppingList(_BOXES, Catalogue(write_items(["milk", "eggs", "bread"], ["olditem"])))

    assert (shopping_list.unknowns, shopping_list.inactives, shopping_list.missing) == (["Tofu"], ["OldItem"], ["bread"])
    assert shopping_list.rows == 2
    with pytest.raises(ValueError):
        shopping_list.commit(_DAY, str(tmp_path / "db.csv"))
    assert not (tmp_path / "db.csv").exists()


def test_commit_records_resolved_boxes(tmp_path, write_items):
    """A clean list lands in history as one list entry per item, dated by the commit, need taken from the box."""
    shopping_list = ShoppingList(_BOXES[:2], Catalogue(write_items(["milk", "eggs"])))
    db = str(tmp_path / "db.csv")

    assert shopping_list.commit(_DAY, db) == 2
    assert sorted(history.read(db)) == [("eggs", "2026-01-01", False), ("milk", "2026-01-01", True)]


def test_duplicate_boxes_block_commit(tmp_path, write_items):
    """Two boxes resolving to one item make its need ambiguous, so the list refuses to commit."""
    shopping_list = ShoppingList(_BOXES[:2] + [Box("milk", False, "b5")], Catalogue(write_items(["milk", "eggs"])))

    assert shopping_list.duplicates == ["milk"]
    with pytest.raises(ValueError):
        shopping_list.commit(_DAY, str(tmp_path / "db.csv"))


def test_missing_active_item_blocks_commit(tmp_path, write_items):
    """An active item with no box would leave the commit silent about it, so the list refuses to commit."""
    shopping_list = ShoppingList(_BOXES[:2], Catalogue(write_items(["milk", "eggs", "bread"])))

    assert shopping_list.missing == ["bread"]
    with pytest.raises(ValueError):
        shopping_list.commit(_DAY, str(tmp_path / "db.csv"))
    assert not (tmp_path / "db.csv").exists()


def test_find_boxes_returns_matches_and_items_without_box(write_items):
    """Push gets the box of each predicted item, and the predicted items with no box."""
    shopping_list = ShoppingList(_BOXES[:2], Catalogue(write_items(["milk", "eggs"])))

    boxes, absent = shopping_list.find_boxes(["milk", "spinach"])

    assert [b.id for b in boxes] == ["b1"]
    assert absent == ["spinach"]
