"""CLI syncing sessions from Garmin into data/sessions.csv.

Reads GARMIN_EMAIL and GARMIN_PASSWORD from the environment (source coach/.env first); cached tokens make them optional after the first login.
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from coach.connectors.garmin import (
    GarminClient,
    UnknownTypesError,
    download_sessions,
    login,
)
from coach.core.sessions import LOG, Merged, Session, merge_sessions, read_sessions

_TOKENS = Path(__file__).parent / "data" / ".garmin_tokens"
_OVERLAP_DAYS = 3  # re-sync recent days so RPE added on Garmin after a sync is picked up
_FIRST_SYNC_DAYS = 90


def _choose_sync_start(stored: list[Session], today: date) -> date:
    """Choose where an unbounded sync starts, overlapping the last one so late Garmin edits are caught."""
    if not stored:
        return today - timedelta(days=_FIRST_SYNC_DAYS)
    return max(s.date for s in stored) - timedelta(days=_OVERLAP_DAYS)


def sync_sessions(client: GarminClient, log: Path, today: date, since: date | None = None) -> Merged:
    """Sync sessions from since (or an automatic start) to today into the log; an unknown type writes nothing."""
    start = since or _choose_sync_start(read_sessions(log), today)
    fresh = download_sessions(client, start, today)
    return merge_sessions(fresh, log)


def main() -> None:
    """Parse --since, log in to Garmin and sync into the session log, exiting on unknown types."""
    parser = argparse.ArgumentParser(description="Sync sessions from Garmin into data/sessions.csv.")
    parser.add_argument("--since", type=date.fromisoformat, help="first day to re-sync, YYYY-MM-DD")
    args = parser.parse_args()
    client = login(os.environ.get("GARMIN_EMAIL"), os.environ.get("GARMIN_PASSWORD"), _TOKENS)
    try:
        merged = sync_sessions(client, LOG, datetime.now().astimezone().date(), args.since)
    except UnknownTypesError as error:
        sys.exit(f"Unknown types: {error}. Add them to Type in coach/core/sessions.py and re-sync; nothing was written.")
    print(f"{merged.added} added, {merged.updated} updated in {LOG}")


if __name__ == "__main__":
    main()
