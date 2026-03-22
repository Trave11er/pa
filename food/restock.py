"""CLI syncing the Notion shopping list with history and predictions.

Subcommands: pull [--commit], push, tick-all. Thin glue: prints and decides, logic lives in the modules it calls.
Exits 1 whenever it aborts, so a calling script stops instead of carrying on.
"""

import argparse
import sys
from datetime import datetime

from food.connectors.notion import NotionList
from food.core.catalogue import Catalogue
from food.core.prediction import Prediction
from food.core.shared import File, warn_stale_files
from food.core.shopping_list import ShoppingList


def _pull(notion: NotionList, commit: bool) -> None:
    """Pull the shopping list; dry run unless commit, and stop on unknown, inactive, duplicate or missing items."""
    boxes = notion.fetch_boxes()
    catalogue = Catalogue.load_or_create(list(dict.fromkeys(b.label for b in boxes)), File.CATALOGUE)
    shopping_list = ShoppingList(boxes, catalogue)

    if shopping_list.missing:
        print(f"WARNING: {len(shopping_list.missing)} active item(s) missing from Notion list: "
              f"{', '.join(shopping_list.missing)}")
        print(f"Add a box for each on Notion or set active: false in {File.CATALOGUE}, then re-run pull.")
    if shopping_list.inactives:
        print(f"WARNING: {len(shopping_list.inactives)} inactive item(s) on Notion list: "
              f"{', '.join(shopping_list.inactives)}")
        print(f"Reactivate in {File.CATALOGUE} or remove from Notion, then re-run pull.")
    if shopping_list.unknowns:
        written = catalogue.write_stubs(shopping_list.unknowns, File.TEMP_CATALOGUE_STUBS)
        print(f"WARNING: {len(written)} unknown item(s) written to {File.TEMP_CATALOGUE_STUBS}: {', '.join(written)}")
        print(f"Move wanted entries from {File.TEMP_CATALOGUE_STUBS} into {File.CATALOGUE}, then re-run pull.")
    if shopping_list.duplicates:
        print(f"WARNING: {len(shopping_list.duplicates)} item(s) with several boxes on Notion: "
              f"{', '.join(shopping_list.duplicates)}")
        print("Keep one box per item on Notion, then re-run pull.")
    if shopping_list.unknowns or shopping_list.inactives or shopping_list.duplicates or shopping_list.missing:
        sys.exit("Aborting: resolve the issues above, then re-run pull.")

    if not commit:
        print(f"DRY RUN: would append {shopping_list.rows} row(s) to {File.HISTORY}. "
              f"Nothing was written. Re-run with --commit to actually commit the list.")
        return
    print(f"Appended {shopping_list.commit(datetime.now().astimezone().date())} rows to {File.HISTORY}")


def _push(notion: NotionList) -> None:
    """Push saved predictions as suggestions by unticking their boxes; abort on duplicate items or predicted items with no box."""
    try:
        preds = Prediction.read_handoff()
    except FileNotFoundError:
        sys.exit(f"{File.TEMP_PREDICT} not found. Run predictor.py first.")
    if not preds:
        print(f"{File.TEMP_PREDICT} is empty. Nothing to push.")
        return

    shopping_list = ShoppingList(notion.fetch_boxes(), Catalogue(File.CATALOGUE))
    if shopping_list.duplicates:
        print(f"ABORT: {len(shopping_list.duplicates)} item(s) with several boxes on Notion: "
              f"{', '.join(shopping_list.duplicates)}")
        sys.exit("Keep one box per item on Notion (pull would refuse them), then re-run push.")
    boxes, absent = shopping_list.find_boxes([p.item for p in preds])
    if absent:
        print(f"ABORT: {len(absent)} predicted item(s) have no box on the Notion page:")
        for item in absent:
            print(f"  - {item}")
        sys.exit("Add these to the Notion page, then re-run push.")

    notion.set_boxes_checked(boxes, False)
    print(f"Suggested {len(preds)} item(s): unticked {len(boxes)} box(es) on Notion. Check them against what you have.")


def _reset(notion: NotionList) -> None:
    """Reset the shopping list by ticking every box, so suggestions and checking start from a blank slate."""
    boxes = notion.fetch_boxes()
    needed = [b for b in boxes if b.need]
    if not needed:
        print(f"All {len(boxes)} box(es) already ticked. Nothing to do.")
        return
    notion.set_boxes_checked(needed, True)
    print(f"Ticked {len(needed)} box(es) on Notion ({len(boxes)} total). "
          "Untick the ones you need to buy later.")


def main() -> None:
    """Parse the subcommand and run it against the production Notion page."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pull = sub.add_parser("pull", help=f"Resolve the Notion list against {File.CATALOGUE}; dry run unless --commit")
    pull.add_argument("--commit", action="store_true", help=f"Actually commit the list to {File.HISTORY}")
    sub.add_parser("push", help=f"Suggest the items in {File.TEMP_PREDICT} by unticking their boxes")
    sub.add_parser("tick-all", help="Reset: tick every box on Notion; no history write")
    args = parser.parse_args()
    warn_stale_files()

    notion = NotionList.open_grocery_page()
    if args.command == "pull":
        _pull(notion, args.commit)
    elif args.command == "push":
        _push(notion)
    else:
        _reset(notion)


if __name__ == "__main__":
    main()
