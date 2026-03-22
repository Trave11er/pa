# Food

A personal grocery tracker: it learns from past shopping lists which items will be needed next.

## Language

### Items

**Item**:
A thing that gets bought, under one canonical name.
_Avoid_: Product, entry

**Catalogue**:
The set of all known items, each with its aliases and whether it is active.
_Avoid_: Items, items.yaml

**Active item**:
An item that must appear on the shopping list at every commit; a commit missing one is refused.
An item that is not active (inactive) is retired: it stays in the catalogue so history still refers to it, but a commit listing it is refused.
_Avoid_: Expected item, deleted item, removed item

**Label**:
The text written on the shopping list for an item. A trailing number (e.g. "eggs 2") is a note for the shop, not part of the item and not part of its need.
_Avoid_: Name, box text

**Alias**:
A label the catalogue recognises as meaning a particular item.
_Avoid_: Known-as, synonym

### Lists and history

**Shopping list**:
The list of items with, for each, whether it is currently needed. Each item appears on it at most once.
_Avoid_: Trip, page, snapshot

**Commit**:
Recording the shopping list's current needs into history, whenever the user chooses. A commit is dated by when it was made, which stands for when the needs were checked; when anything was bought is never recorded.
_Avoid_: Trip, shop, pull, purchase date

**List entry**:
One item on one committed shopping list, together with whether it was needed.
_Avoid_: Purchase, row, observation

**Need**:
Whether an item was lacking at home when the list was committed, regardless of whether it was then bought. Only the user decides a need, by checking at home.
_Avoid_: Buy, bought, purchase

### Prediction

**Prediction**:
The model's probability that an item is needed right now.
_Avoid_: Score, forecast

**Suggestion**:
An item marked as needed on the shopping list by the predictor rather than the user; a guess the user reviews before committing. Only the top-N predictions become suggestions; the rest are dropped.
_Avoid_: Push, prediction, need

**Reset**:
Marking every item on the shopping list as not needed, to start a fresh round of suggestions and checking.
_Avoid_: Tick-all, clear
