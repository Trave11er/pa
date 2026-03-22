"""The Notion grocery page seen as a flat list of checkboxes.

Hides the Notion HTTP API, block recursion and the "checked = already have it" convention.
"""

import os
from enum import StrEnum
from typing import Any, Self

import requests

from food.core.shopping_list import Box

_API = "https://api.notion.com/v1"
_API_VERSION = "2022-06-28"
_PAGE_ID_ENV = "NOTION_FOOD_PAGE_ID"
_TOKEN_ENV = "NOTION_FOOD_PAGE_TOKEN"


class NotionJson(StrEnum):
    """Notion block JSON keys and block types, named once so NotionList and its tests can't drift apart."""
    TYPE = "type"
    ID = "id"
    RESULTS = "results"
    HAS_MORE = "has_more"
    HAS_CHILDREN = "has_children"
    CHECKED = "checked"
    RICH_TEXT = "rich_text"
    PLAIN_TEXT = "plain_text"
    TO_DO = "to_do"  # block type and the key holding its payload
    CHILD_DATABASE = "child_database"  # block type never descended into


class NotionList:
    """The only door to Notion, so the API version, auth and JSON shape live in one place."""
    _session: requests.Session
    _page_id: str

    def __init__(self, page_id: str, token: str) -> None:
        """Bind to one page with an explicit token so nothing is read from hidden globals."""
        self._page_id = page_id
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Notion-Version": _API_VERSION,
        })

    @classmethod
    def open_grocery_page(cls) -> Self:
        """Open the grocery page named by NOTION_FOOD_PAGE_ID with the NOTION_FOOD_PAGE_TOKEN token, for the CLI."""
        missing = [name for name in (_PAGE_ID_ENV, _TOKEN_ENV) if not os.environ.get(name)]
        if missing:
            raise KeyError(f"{', '.join(missing)} not set; `source .env` first")
        return cls(os.environ[_PAGE_ID_ENV], os.environ[_TOKEN_ENV])

    def fetch_boxes(self) -> list[Box]:
        """Fetch every checkbox on the page, nested ones included, so pull and push see the same list."""
        boxes: list[Box] = []
        self._collect_boxes(self._page_id, boxes)
        return boxes

    def set_boxes_checked(self, boxes: list[Box], checked: bool) -> None:
        """Set boxes checked (have it) or not (to buy); the only writes made to Notion."""
        for box in boxes:
            res = self._session.patch(f"{_API}/blocks/{box.id}", json={NotionJson.TO_DO: {NotionJson.CHECKED: checked}})
            res.raise_for_status()

    def _collect_boxes(self, block_id: str, boxes: list[Box]) -> None:
        """Collect boxes under block_id depth-first, since items nest under headings and toggles."""
        for block in self._fetch_children(block_id):
            btype = block[NotionJson.TYPE]
            if btype == NotionJson.TO_DO:
                todo = block.get(NotionJson.TO_DO, {})
                label = "".join(t.get(NotionJson.PLAIN_TEXT, "") for t in todo.get(NotionJson.RICH_TEXT, [])).strip()
                if label:
                    boxes.append(Box(label, not todo.get(NotionJson.CHECKED, False), block[NotionJson.ID]))
            if block.get(NotionJson.HAS_CHILDREN) and btype != NotionJson.CHILD_DATABASE:
                self._collect_boxes(block[NotionJson.ID], boxes)

    def _fetch_children(self, block_id: str) -> list[dict[str, Any]]:
        """Fetch one level of child blocks, raising on any gap so a partial page is never committed as a trip."""
        res = self._session.get(f"{_API}/blocks/{block_id}/children")
        res.raise_for_status()
        data = res.json()
        if data.get(NotionJson.HAS_MORE):
            raise RuntimeError(f"block {block_id} has >100 children; pagination is not supported")
        return data.get(NotionJson.RESULTS, [])
