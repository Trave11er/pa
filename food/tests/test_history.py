from food.core import history
from food.core.history import ListEntry


def test_appends_accumulate_under_one_header(tmp_path):
    """Each entry is one row and read back as one ListEntry; appends accumulate under one header."""
    db = tmp_path / "history.csv"

    assert history.append([("eggs", "2026-01-01", True), ("milk", "2026-01-01", False)], db) == 2
    assert history.append([("milk", "2026-01-08", True)], db) == 1

    assert db.read_text().count("item,date,need") == 1
    assert history.read(db) == [
        ListEntry("eggs", "2026-01-01", True),
        ListEntry("milk", "2026-01-01", False),
        ListEntry("milk", "2026-01-08", True),
    ]


def test_read_merges_same_item_and_date_as_any_need(tmp_path):
    """Duplicate (item, date) rows collapse to one ListEntry, needed if any row was."""
    db = tmp_path / "history.csv"
    history.append([("eggs", "2026-01-01", False), ("eggs", "2026-01-01", True)], db)

    assert history.read(db) == [ListEntry("eggs", "2026-01-01", True)]
