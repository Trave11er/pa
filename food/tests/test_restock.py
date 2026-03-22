import os
import sys
from unittest.mock import Mock

import pytest
import yaml

from food import restock
from food.connectors.notion import NotionList
from food.core import history, shared
from food.core.prediction import Prediction
from food.core.shopping_list import Box

_BOXES = [Box("Milk", True, "b1"), Box("Eggs", False, "b2"), Box("Bread", True, "b3")]


@pytest.fixture()
def notion(monkeypatch, write_items):
    """Swap the production Notion page for a mock returning _BOXES, over a catalogue that resolves them."""
    write_items(["milk", "eggs", "bread"])
    fake = Mock(fetch_boxes=Mock(return_value=_BOXES))
    monkeypatch.setattr(NotionList, "open_grocery_page", staticmethod(lambda: fake))
    return fake


def _run(monkeypatch, *args):
    """Invoke the CLI as `restock.py <args>`."""
    argv = ["restock.py", *args]
    monkeypatch.setattr(sys, "argv", argv)
    restock.main()


@pytest.mark.usefixtures("notion")
def test_pull_writes_history_only_with_commit(monkeypatch):
    """A plain pull is a dry run; pull --commit commits today's list with need taken from each box."""
    _run(monkeypatch, "pull")
    assert not os.path.exists(shared.File.HISTORY)

    _run(monkeypatch, "pull", "--commit")
    assert sorted((p.item, p.need) for p in history.read()) == [("bread", True), ("eggs", False), ("milk", True)]


def test_pull_aborts_on_duplicate_boxes(notion, monkeypatch):
    """Two boxes for one item make its need ambiguous, so pull --commit writes nothing."""
    notion.fetch_boxes.return_value = [*_BOXES, Box("Milk", False, "b4")]

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "pull", "--commit")

    assert exc.value.code not in (None, 0)
    assert not os.path.exists(shared.File.HISTORY)


def test_pull_dry_run_aborts_on_missing_active_item(notion, monkeypatch):
    """An active item with no box stops even a dry run, so it never promises rows the commit would refuse."""
    notion.fetch_boxes.return_value = _BOXES[:2]

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "pull")

    assert exc.value.code not in (None, 0)
    assert not os.path.exists(shared.File.HISTORY)


def test_first_pull_seeds_one_catalogue_entry_per_label(notion, monkeypatch):
    """Without catalogue.yaml, repeated labels seed a single entry each."""
    os.remove(shared.File.CATALOGUE)
    notion.fetch_boxes.return_value = [*_BOXES, Box("Milk", False, "b4")]

    with pytest.raises(SystemExit):
        _run(monkeypatch, "pull")

    with open(shared.File.CATALOGUE) as f:
        assert sorted(e["item"] for e in yaml.safe_load(f)) == ["bread", "eggs", "milk"]


def test_push_unticks_predicted_boxes(notion, monkeypatch):
    """Push unticks the boxes of handed-off predictions and nothing else."""
    Prediction.write_handoff([Prediction("milk", 0.9), Prediction("eggs", 0.6)])

    _run(monkeypatch, "push")

    notion.set_boxes_checked.assert_called_once()
    boxes, checked = notion.set_boxes_checked.call_args.args
    assert (sorted(b.id for b in boxes), checked) == (["b1", "b2"], False)


def test_push_aborts_on_duplicate_boxes(notion, monkeypatch):
    """Push refuses an item with several boxes, since pull --commit would refuse it after the review."""
    notion.fetch_boxes.return_value = [*_BOXES, Box("Bread", False, "b4")]
    Prediction.write_handoff([Prediction("milk", 0.9)])

    with pytest.raises(SystemExit):
        _run(monkeypatch, "push")
    notion.set_boxes_checked.assert_not_called()


def test_push_aborts_when_a_prediction_has_no_box(notion, monkeypatch):
    """A predicted item missing from Notion stops push before any write."""
    Prediction.write_handoff([Prediction("milk", 0.9), Prediction("spinach", 0.7)])

    with pytest.raises(SystemExit):
        _run(monkeypatch, "push")
    notion.set_boxes_checked.assert_not_called()


def test_push_without_predictions_writes_nothing(notion, monkeypatch):
    """A missing handoff aborts and an empty one is a no-op; neither touches Notion."""
    with pytest.raises(SystemExit):
        _run(monkeypatch, "push")

    Prediction.write_handoff([])
    _run(monkeypatch, "push")
    notion.set_boxes_checked.assert_not_called()


def test_tick_all_ticks_only_unticked_boxes(notion, monkeypatch):
    """tick-all resets the list by ticking every needed box, and does nothing once all are ticked."""
    _run(monkeypatch, "tick-all")
    boxes, checked = notion.set_boxes_checked.call_args.args
    assert ({b.id for b in boxes}, checked) == ({"b1", "b3"}, True)

    notion.fetch_boxes.return_value = [Box("Milk", False, "b1")]
    notion.set_boxes_checked.reset_mock()
    _run(monkeypatch, "tick-all")
    notion.set_boxes_checked.assert_not_called()
