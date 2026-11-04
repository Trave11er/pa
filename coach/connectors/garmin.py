"""Garmin Connect: logs in and downloads sessions.

Field names come from Garmin's session-list JSON, which the garminconnect library passes through untouched.
Garmin's JSON shape, and its word "activity" for a session, never leave this module.
"""

from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from coach.core.sessions import Session, Type


class _GarminJson(StrEnum):
    ID = "activityId"
    START_LOCAL = "startTimeLocal"  # "YYYY-MM-DD HH:MM:SS"
    TYPE = "activityType"
    TYPE_KEY = "typeKey"
    ELAPSED = "elapsedDuration"  # seconds, start to stop
    DURATION = "duration"  # seconds; fallback when elapsed is absent
    SUMMARY = "summaryDTO"  # in a session's detail, which holds the RPE the list leaves out
    RPE = "directWorkoutRpe"  # 10-100, inside SUMMARY
    AVG_HR = "averageHR"


class GarminClient(Protocol):
    def get_activities_by_date(self, startdate: str, enddate: str | None = None) -> list[dict[str, Any]]:
        """Get the raw sessions started between two dates, without their RPE; faked in tests."""
        ...

    def get_activity(self, activity_id: str) -> dict[str, Any]:
        """Get one raw session's detail, the only place Garmin returns its RPE; faked in tests."""
        ...


class UnknownTypesError(Exception):
    """Raised for typeKeys missing from Type, so sync can refuse them instead of logging a type the report can't group."""


def login(email: str | None, password: str | None, tokenstore: Path) -> GarminClient:
    """Log in with cached tokens when they work, else with credentials, prompting for MFA on the terminal."""
    # imported here, not at the top, so tests run without the library
    from garminconnect import Garmin

    client = Garmin(email, password, prompt_mfa=lambda: input("Garmin MFA code: "))
    client.login(str(tokenstore))  # saves fresh tokens to tokenstore after a credential login
    return client


def _convert_to_session(raw: dict[str, Any], detail: dict[str, Any]) -> Session:
    """Convert one raw Garmin session and its detail to a Session, scaling RPE to 1-10 and seconds to minutes."""
    seconds = raw.get(_GarminJson.ELAPSED) or raw[_GarminJson.DURATION]
    rpe = detail.get(_GarminJson.SUMMARY, {}).get(_GarminJson.RPE)
    avg_hr = raw.get(_GarminJson.AVG_HR)
    return Session(str(raw[_GarminJson.ID]), date.fromisoformat(raw[_GarminJson.START_LOCAL][:10]),
                   Type(raw[_GarminJson.TYPE][_GarminJson.TYPE_KEY]), seconds / 60,
                   round(rpe / 10) if rpe is not None else None, float(avg_hr) if avg_hr is not None else None)


def _find_unknown_types(raw_sessions: list[dict[str, Any]]) -> list[str]:
    """Find typeKeys missing from Type, so download_sessions can refuse the whole batch."""
    keys = {raw[_GarminJson.TYPE][_GarminJson.TYPE_KEY] for raw in raw_sessions}
    return sorted(keys - {t.value for t in Type})


def download_sessions(client: GarminClient, start: date, end: date) -> list[Session]:
    """Download the sessions started from start to end; raises UnknownTypesError before returning any."""
    raw_sessions = client.get_activities_by_date(start.isoformat(), end.isoformat())
    unknown = _find_unknown_types(raw_sessions)
    if unknown:
        raise UnknownTypesError(", ".join(unknown))
    return [_convert_to_session(raw, client.get_activity(str(raw[_GarminJson.ID]))) for raw in raw_sessions]
