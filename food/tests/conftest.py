import pytest
import yaml

from food.connectors.notion import NotionJson
from food.core import shared


def todo(block_id, label, checked, has_children=False):
    """Fake a Notion to_do block so tests describe the page by label and checked state."""
    return {NotionJson.TYPE: NotionJson.TO_DO, NotionJson.ID: block_id,
            NotionJson.HAS_CHILDREN: has_children,
            NotionJson.TO_DO: {NotionJson.RICH_TEXT: [{NotionJson.PLAIN_TEXT: label}], NotionJson.CHECKED: checked}}


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    """Redirect every data file into tmp_path so no test touches the real catalogue, history or /tmp handoffs."""
    for name in ("CATALOGUE", "HISTORY", "TEMP_CATALOGUE_STUBS", "TEMP_PREDICT"):
        monkeypatch.setattr(shared.File, name, str(tmp_path / name.lower()))
    return tmp_path


@pytest.fixture()
def write_items():
    """Provide a catalogue writer where each item is known by its own name, so tests choose what resolves."""
    def write(active, inactive=()):
        entries = [{"item": n, "aliases": [n], "active": True} for n in active]
        entries += [{"item": n, "aliases": [n], "active": False} for n in inactive]
        with open(shared.File.CATALOGUE, "w") as f:
            yaml.dump(entries, f)
        return shared.File.CATALOGUE
    return write
