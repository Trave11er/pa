"""Test data: sessions, and raw Garmin sessions keyed by _GarminJson like the real ones."""

import itertools
from datetime import date
from typing import Any

from coach.connectors.garmin import _GarminJson as J
from coach.core.sessions import Session, Type

_garmin_ids = itertools.count(1)


def build_session(day: str, minutes: float = 60.0, rpe: int | None = 5, type_: Type = Type.RUNNING) -> Session:
    """Build a session from the fields load cares about, with a fresh Garmin id."""
    garmin_id = str(next(_garmin_ids))
    return Session(garmin_id, date.fromisoformat(day), type_, minutes, rpe, None)


def fake_garmin_json(garmin_id: int, start: str, type_key: str = "running", elapsed: float | None = 3600.0,
                     rpe: int | None = 50) -> dict[str, Any]:
    """Fake one raw session, omitting the fields Garmin omits; FakeGarmin serves its RPE from the detail, as Garmin does."""
    raw: dict[str, Any] = {J.ID: garmin_id, J.START_LOCAL: f"{start} 07:00:00",
                           J.TYPE: {J.TYPE_KEY: type_key}, J.DURATION: 3000.0, J.AVG_HR: 140.0}
    if elapsed is not None:
        raw[J.ELAPSED] = elapsed
    if rpe is not None:
        raw[J.RPE] = rpe
    return raw


class FakeGarmin:
    """Stand in for the Garmin client, recording each requested window so tests can check where sync starts."""

    def __init__(self, raw_sessions: list[dict[str, Any]]) -> None:
        """Hold the raw sessions the fake account contains."""
        self.raw_sessions = raw_sessions
        self.requests: list[tuple[str, str | None]] = []

    def get_activities_by_date(self, startdate: str, enddate: str | None = None) -> list[dict[str, Any]]:
        """Get the canned raw sessions inside the window, as Garmin filters by start date."""
        self.requests.append((startdate, enddate))
        return [{k: v for k, v in a.items() if k != J.RPE} for a in self.raw_sessions
                if startdate <= a[J.START_LOCAL][:10] <= (enddate or "9999")]

    def get_activity(self, activity_id: str) -> dict[str, Any]:
        """Get a canned raw session's detail, the only place real Garmin returns RPE."""
        (raw,) = [a for a in self.raw_sessions if str(a[J.ID]) == activity_id]
        summary = {J.RPE: raw[J.RPE]} if J.RPE in raw else {}
        return {J.ID: raw[J.ID], J.SUMMARY: summary}
