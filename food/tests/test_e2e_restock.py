import json
import os
import sys

import pytest
import responses
import yaml

from food import restock
from food.connectors.notion import NotionJson, NotionList
from food.core import history, shared
from food.core.prediction import Prediction
from food.tests.conftest import todo

_API = "https://api.notion.com/v1"
_PAGE = "page"


def _serve_page(*blocks):
    """Serve blocks as the page's only children, so the real NotionList fetches them over (mocked) HTTP."""
    url = f"{_API}/blocks/{_PAGE}/children"
    responses.get(url,
                  json={NotionJson.RESULTS: list(blocks), NotionJson.HAS_MORE: False})


def _run(monkeypatch, *args):
    """Invoke the CLI as `restock.py <args>`."""
    argv = ["restock.py", *args]
    monkeypatch.setattr(sys, "argv", argv)
    restock.main()


@pytest.fixture(autouse=True)
def fake_page(monkeypatch):
    """Point the CLI at a fake page id, keeping the real NotionList so HTTP is exercised."""
    monkeypatch.setattr(NotionList, "open_grocery_page", staticmethod(lambda: NotionList(_PAGE, "tok")))


@responses.activate
def test_pull_commit_records_notion_list_ignoring_qty_note(monkeypatch, write_items):
    """Checked means have-it (need False) and 'Eggs 2' lands as a single eggs row."""
    _serve_page(todo("b1", "Milk", True), todo("b2", "Eggs 2", False), todo("b3", "Bread", False))
    write_items(["milk", "eggs", "bread"])

    _run(monkeypatch, "pull", "--commit")

    assert sorted((p.item, p.need) for p in history.read()) == [("bread", True), ("eggs", True), ("milk", False)]
    with open(shared.File.HISTORY) as f:
        assert len(f.readlines()) == 1 + 3  # header + milk + eggs + bread


@responses.activate
def test_pull_aborts_on_unknown_and_inactive_and_writes_stubs(monkeypatch, write_items):
    """Unknown or inactive labels exit non-zero, write nothing to history and stub only the unknowns."""
    _serve_page(todo("b1", "Milk", False), todo("b2", "Tofu", False), todo("b3", "OldItem", False))
    write_items(["milk"], inactive=["olditem"])

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "pull", "--commit")

    assert exc.value.code not in (None, 0)
    assert not os.path.exists(shared.File.HISTORY)
    with open(shared.File.TEMP_CATALOGUE_STUBS) as f:
        assert [s["item"] for s in yaml.safe_load(f)] == ["tofu"]


@responses.activate
def test_push_unchecks_only_predicted_boxes(monkeypatch, write_items):
    """Push PATCHes exactly the predicted items' blocks, each to checked=False."""
    _serve_page(todo("b1", "Milk", True), todo("b2", "Eggs", True), todo("b3", "Bread", True))
    responses.patch(f"{_API}/blocks/b1", json={})
    responses.patch(f"{_API}/blocks/b3", json={})
    write_items(["milk", "eggs", "bread"])
    Prediction.write_handoff([Prediction("milk", 0.9), Prediction("bread", 0.8)])

    _run(monkeypatch, "push")

    patches = [c for c in responses.calls if c.request.method == "PATCH"]
    assert [c.request.url for c in patches] == [f"{_API}/blocks/b1", f"{_API}/blocks/b3"]
    assert all(json.loads(c.request.body or "{}") == {NotionJson.TO_DO: {NotionJson.CHECKED: False}} for c in patches)
