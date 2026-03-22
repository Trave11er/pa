"""Catalogue: catalogue.yaml, mapping labels to canonical item names, aliases and active flags.

Both restock.py and predictor.py go through Catalogue, so the file format and the "active" rule
live in one place. Needs only pyyaml, which predictor.py's PEP 723 environment already has.
"""

import os
from enum import StrEnum

import yaml

from food.core.shared import ItemKey


class Status(StrEnum):
    OK = "ok"
    UNKNOWN = "unknown"
    INACTIVE = "inactive"


class Catalogue:
    def __init__(self, path):
        """Load the catalogue that maps labels to canonical item names."""
        self.path = path
        with open(path) as f:
            self._entries = yaml.safe_load(f) or []

    @classmethod
    def load_or_create(cls, todos, path):
        """Bootstrap catalogue.yaml from the current shopping list on first run, otherwise load it."""
        if not os.path.exists(path):
            return cls._create(todos, path)
        return cls(path)

    @classmethod
    def _create(cls, todos, path):
        """Seed one active entry per Notion label so a first run has a catalogue to resolve against."""
        entries = []
        for name in todos:
            item = _strip_quantity(name)
            entries.append({str(ItemKey.ITEM): item.lower(), str(ItemKey.ALIASES): [item], str(ItemKey.ACTIVE): True})
        with open(path, "w") as f:
            yaml.dump(entries, f, allow_unicode=True, default_flow_style=False)
        print(f"Created {path} with {len(entries)} items. Review and edit aliases/active flags before next run.")
        return cls(path)

    @property
    def active_items(self):
        """Canonical names that must be on every committed list; a commit missing one is refused."""
        return {e[ItemKey.ITEM] for e in self._entries if e.get(ItemKey.ACTIVE)}

    def classify(self, raw):
        """Resolve a raw Notion label, e.g. 'Eggs 2', to (status, item); the trailing number is only a shop note.

        Status.OK: item is the canonical name of an active entry with a matching alias; otherwise the
        cleaned label. An active match wins over an inactive entry sharing the alias."""
        clean = _strip_quantity(raw)
        matches = [e for e in self._entries
                   if any(clean.lower() == a.lower() for a in e.get(ItemKey.ALIASES, []))]
        for entry in matches:
            if entry.get(ItemKey.ACTIVE):
                return Status.OK, entry[ItemKey.ITEM]
        return (Status.INACTIVE if matches else Status.UNKNOWN), clean

    def write_stubs(self, raws, path):
        """Write unknown items as stubs to path, deduped against existing entries."""
        existing_known = {a.lower() for e in self._entries for a in e.get(ItemKey.ALIASES, [])}
        seen = set()
        stubs = []
        for raw in raws:
            if raw.lower() not in existing_known and raw.lower() not in seen:
                stubs.append({str(ItemKey.ITEM): raw.lower(), str(ItemKey.ALIASES): [raw], str(ItemKey.ACTIVE): True})
                seen.add(raw.lower())
        with open(path, "w") as f:
            yaml.dump(stubs, f, allow_unicode=True, default_flow_style=False)
        return [s[ItemKey.ITEM] for s in stubs]


def _strip_quantity(raw):
    """Drop a trailing shop-note number, e.g. 'eggs 2' -> 'eggs', since quantity is not part of an item."""
    parts = raw.rsplit(None, 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0].strip()
    return raw.strip()
