"""Sessions: the sessions.csv log of every synced training session, one row per Garmin id."""

import csv
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

LOG = Path(__file__).parent.parent / "data" / "sessions.csv"  # the CLIs' default; core functions take the path


class Type(StrEnum):
    """Garmin's typeKeys for the types trained; a new type is added here, and sync refuses any it doesn't list."""
    RUNNING = "running"
    TRAIL_RUNNING = "trail_running"
    TREADMILL_RUNNING = "treadmill_running"
    STRENGTH_TRAINING = "strength_training"
    BOXING = "boxing"  # martial arts; check the key on the first sync
    MIXED_MARTIAL_ARTS = "mixed_martial_arts"
    LAP_SWIMMING = "lap_swimming"  # pool
    OPEN_WATER_SWIMMING = "open_water_swimming"


class Session(NamedTuple):
    garmin_id: str
    date: date  # local date the session started
    type: Type
    duration_min: float
    rpe: int | None  # 1-10; None for an unrated session
    avg_hr: float | None  # stored, never used for load


class Merged(NamedTuple):
    added: int
    updated: int


def _parse_optional(value: str) -> int | None:
    """Parse an optional RPE, keeping empty cells distinct from zero so an unrated session never reads as RPE 0."""
    if not value:
        return None
    return int(value)


def read_sessions(path: Path) -> list[Session]:
    """Read every stored session, oldest first; an absent log is an empty one."""
    if not path.exists():
        return []
    with path.open(newline="") as file:
        rows = list(csv.reader(file))[1:]  # columns are Session._fields, as merge_sessions writes them
    stored = [Session(garmin_id, date.fromisoformat(day), Type(type_), float(minutes), _parse_optional(rpe),
                      float(avg_hr) if avg_hr else None)
              for garmin_id, day, type_, minutes, rpe, avg_hr in rows]
    return sorted(stored, key=lambda s: s.date)


def merge_sessions(fresh: list[Session], path: Path) -> Merged:
    """Merge fresh sessions into the log so re-syncing picks up edits on Garmin, creating the log if absent."""
    by_id = {s.garmin_id: s for s in read_sessions(path)}
    added = sum(s.garmin_id not in by_id for s in fresh)
    updated = sum(s.garmin_id in by_id and by_id[s.garmin_id] != s for s in fresh)
    by_id.update({s.garmin_id: s for s in fresh})
    merged = sorted(by_id.values(), key=lambda s: s.date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(Session._fields)
        writer.writerows(merged)
    return Merged(added, updated)
