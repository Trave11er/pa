---
name: grocery-cycle
description: Run the food/grocery Notion sync + prediction workflow (restock.py / predictor.py). Use when asked to fetch the Notion food page, predict what to buy, push predictions to Notion, or run the full restock cycle.
---

# Grocery cycle

This skill runs the repo's grocery tracker. It reads a Notion to-do page, predicts what to buy next, and syncs the results back. The two scripts are `restock.py`, which reads and writes Notion and history but never trains, and `predictor.py`, which trains and predicts but never touches Notion.

`restock.py` takes a required subcommand (`pull`, `push`, `tick-all`); running it with no arguments is an error. It exits 1 whenever it aborts.

## When to use

- The user asks to "fetch / pull the latest food Notion page" or check what's on the list.
- The user asks to "run predict" / "what should I buy next".
- The user asks to push predictions to Notion or run the whole restock cycle.
- Any task touching `restock.py`, `predictor.py`, `catalogue.yaml`, `history.csv`, or `/tmp/*` handoff files.

## Environment setup (do this first, every time)

- **Token.** `restock.py` needs `NOTION_FOOD_PAGE_TOKEN`, which lives only in `food/.env`. It is NOT in the shell environment by default. Run commands from the repo root and prefix every Notion command with `source food/.env &&`:
  ```
  source food/.env && python3 -m food.restock pull
  ```
  Do not read `food/.env`, with `cat` or any other tool. A `Read(**/.env)` deny rule protects it. Sourcing it to run a script is fine.
- **Predictor deps.** `predictor.py` needs pinned versions (numpy 1.26.4, pandas 2.1.1, sklearn 1.3.1). The system `python3` (`/opt/conda/bin/python3`) already has exactly those, so run it directly:
  ```
  python3 -m food.predictor
  ```
  `predictor.py` doesn't call Notion, so it doesn't need `source food/.env`, though sourcing it does no harm.

## Instructions

### See the latest Notion page (read-only, the default for "fetch")
```
source food/.env && python3 -m food.restock pull
```
Without `--commit` this is a dry run: it changes neither Notion nor `history.csv`. It prints, and you report to the user:
- Unknown, inactive, duplicate or missing (active but no box) items. Any of them aborts the pull (exit 1). Unknown labels are written as stubs to `/tmp/catalogue_stubs.yaml`; see the cautions below on `catalogue.yaml`.
- Otherwise `DRY RUN: would append N row(s)`: one row per item (a trailing number like `eggs 2` is only a shop note).

There is no snapshot file of the fetched page. To see the item-by-item state, the pull's output is all there is.

### Predict what to buy
```
python3 -m food.predictor
```
It prints the CV AUC for each held-out commit and their mean, a top-N table and a bottom-10 table, then writes the top items to `/tmp/predict.yaml`. Report the mean AUC, the top predicted items with their probabilities. `--top-n` changes how many items are written (default 25).

### Push predictions to Notion (changes Notion, so confirm first)
```
source food/.env && python3 -m food.restock push
```
This reads `/tmp/predict.yaml` and suggests those items: it **unticks** their boxes, so they show as needed until the user checks them. If a predicted item has no checkbox on the page, it lists those items, changes nothing and aborts. In that case, tell the user to add those items to Notion and re-run `push`. It aborts the same way if any item has several boxes; tell the user to keep one box per item.

### Full cycle
Predict, then push, then pause so the user can review and check off items on Notion. Then pull as described in the next section.

### Commit the list to history (changes `history.csv`, needs `--commit`, confirm first)
The pull resolves the page against `catalogue.yaml` and **commits the list**, dated today, to `history.csv`, **but only when you pass `--commit`**:
```
source food/.env && python3 -m food.restock pull            # dry run: prints what it would append, writes nothing
source food/.env && python3 -m food.restock pull --commit   # appends to history.csv (confirm with the user first)
```
Default to the dry run. Only add `--commit` when the user has explicitly asked to save the pull into history.

To recover from an abort on unknown or inactive items, fix `catalogue.yaml` and re-run `pull`. A missing active item is fixed by adding its box on Notion or setting `active: false`. An abort on duplicate items (several boxes resolving to one item) is fixed on Notion: keep one box per item. This fetches the live page again and stamps today's date, so if the user has since changed Notion, the commit records the page as it is now.

### Other subcommands
- `tick-all` resets the list by ticking every box on Notion. It doesn't write history or train. It changes Notion, so confirm first.

## Conventions and cautions

- **Never write `history.csv` unless the user asked for it.** A pull without `--commit` is a dry run, and the script appends to history only with `--commit`. Confirm with the user before passing it. Before this guard existed, a plain pull appended a day's snapshot without anyone noticing. The `--commit` flag and the `ask` rules in `.claude/settings.json` are there to stop that happening again.
- **Confirm before any Notion mutation** (`push`, `tick-all`) or before committing to `history.csv`. The dry-run `pull` and `predictor.py` change neither Notion nor history, so you can run them without asking.
- **Never edit `catalogue.yaml` destructively.** `history.csv` references canonical item names. Retire items with `active: false`, never delete. The script writes unknown items as stubs to `/tmp/catalogue_stubs.yaml`, and the user moves the ones they want into `catalogue.yaml`.
- **Watch the feedback loop.** If the user accepts pushed predictions without checking, the next round trains on the model's own output. When the user reviews Notion, remind them to check what they actually have instead of accepting the predictions.
- If it's unclear whether the user wants a read-only fetch, or a push or full cycle that changes Notion, ask them with the AskUserQuestion tool.
