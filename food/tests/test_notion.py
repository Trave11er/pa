import json

import pytest
import requests
import responses

from food.connectors.notion import NotionJson, NotionList
from food.core.shopping_list import Box
from food.tests.conftest import todo

_API = "https://api.notion.com/v1"


@responses.activate
def test_fetch_boxes_flattens_nesting_and_inverts_checked():
    """Nested boxes are found and Notion's checked (have it) becomes need=False."""
    toggle = {NotionJson.TYPE: "toggle", NotionJson.ID: "t1", NotionJson.HAS_CHILDREN: True}
    responses.get(f"{_API}/blocks/page/children",
                  json={NotionJson.RESULTS: [todo("b1", "Milk", False), toggle], NotionJson.HAS_MORE: False})
    responses.get(f"{_API}/blocks/t1/children",
                  json={NotionJson.RESULTS: [todo("b2", "Eggs 2", True)], NotionJson.HAS_MORE: False})

    boxes = NotionList("page", "tok").fetch_boxes()

    assert sorted(boxes, key=lambda b: b.id) == [Box("Milk", True, "b1"), Box("Eggs 2", False, "b2")]
    assert responses.calls[0].request.headers["Authorization"] == "Bearer tok"


@responses.activate
def test_fetch_boxes_skips_databases():
    """Databases aren't descended into, so their rows never pose as boxes."""
    database = {NotionJson.TYPE: NotionJson.CHILD_DATABASE, NotionJson.ID: "d1", NotionJson.HAS_CHILDREN: True}
    responses.get(f"{_API}/blocks/page/children",
                  json={NotionJson.RESULTS: [todo("b1", "Milk", False), database], NotionJson.HAS_MORE: False})

    assert NotionList("page", "tok").fetch_boxes() == [Box("Milk", True, "b1")]
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_boxes_raises_on_failed_or_truncated_block():
    """A failed or >100-child block raises, so pull never commits a partial page."""
    toggle = {NotionJson.TYPE: "toggle", NotionJson.ID: "t1", NotionJson.HAS_CHILDREN: True}
    responses.get(f"{_API}/blocks/page/children",
                  json={NotionJson.RESULTS: [toggle], NotionJson.HAS_MORE: False})
    responses.get(f"{_API}/blocks/t1/children", status=500)
    with pytest.raises(requests.HTTPError):
        NotionList("page", "tok").fetch_boxes()

    responses.replace(responses.GET, f"{_API}/blocks/t1/children",
                      json={NotionJson.RESULTS: [], NotionJson.HAS_MORE: True})
    with pytest.raises(RuntimeError, match=">100 children"):
        NotionList("page", "tok").fetch_boxes()


@responses.activate
def test_set_boxes_checked_patches_each_box():
    """Each box gets one PATCH carrying the requested checked state."""
    responses.patch(f"{_API}/blocks/b1", json={})
    responses.patch(f"{_API}/blocks/b2", json={})
    notion = NotionList("page", "tok")

    notion.set_boxes_checked([Box("Milk", False, "b1")], True)
    notion.set_boxes_checked([Box("Eggs", False, "b2")], False)

    assert [c.request.url for c in responses.calls] == [f"{_API}/blocks/b1", f"{_API}/blocks/b2"]
    assert [json.loads(c.request.body or "{}")[NotionJson.TO_DO][NotionJson.CHECKED]
            for c in responses.calls] == [True, False]


@responses.activate
def test_failed_patch_raises():
    """A rejected write surfaces as an HTTP error rather than a silent partial push."""
    responses.patch(f"{_API}/blocks/b1", status=403)

    with pytest.raises(requests.HTTPError):
        NotionList("page", "tok").set_boxes_checked([Box("Milk", False, "b1")], False)


def test_open_grocery_page_needs_token(monkeypatch):
    """Without the env token the CLI fails with a message naming the variable."""
    monkeypatch.setenv("NOTION_FOOD_PAGE_ID", "page")
    monkeypatch.delenv("NOTION_FOOD_PAGE_TOKEN", raising=False)

    with pytest.raises(KeyError, match="NOTION_FOOD_PAGE_TOKEN"):
        NotionList.open_grocery_page()


def test_open_grocery_page_needs_page_id(monkeypatch):
    """Without the env page id the CLI fails with a message naming the variable."""
    monkeypatch.setenv("NOTION_FOOD_PAGE_TOKEN", "tok")
    monkeypatch.delenv("NOTION_FOOD_PAGE_ID", raising=False)

    with pytest.raises(KeyError, match="NOTION_FOOD_PAGE_ID"):
        NotionList.open_grocery_page()
