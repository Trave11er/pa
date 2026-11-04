from datetime import date

import pytest

from coach import sync
from coach.connectors import garmin
from coach.connectors.garmin import _GarminJson
from coach.core import sessions
from coach.core.sessions import Merged, Session, Type
from coach.tests.fakes import FakeGarmin, fake_garmin_json


def test_sync_converts_garmin_rpe_and_duration_and_keeps_unrated(tmp_path):
    """Garmin's 10-100 RPE becomes 1-10, seconds become minutes (duration when elapsed is absent), and no RPE stays unrated."""
    log = tmp_path / "sessions.csv"
    client = FakeGarmin([fake_garmin_json(1, "2026-01-05", elapsed=2700.0, rpe=70),
                         fake_garmin_json(2, "2026-01-06", type_key="boxing", elapsed=None, rpe=None)])

    sync.sync_sessions(client, log, date(2026, 1, 10))

    assert sessions.read_sessions(log) == [Session("1", date(2026, 1, 5), Type.RUNNING, 45.0, 7, 140.0),
                                           Session("2", date(2026, 1, 6), Type.BOXING, 50.0, None, 140.0)]


def test_first_sync_covers_90_days_and_resync_overlaps_and_updates(tmp_path):
    """An empty log syncs 90 days; later syncs re-sync from 3 days before the latest session, picking up RPE added on Garmin."""
    log = tmp_path / "sessions.csv"
    client = FakeGarmin([fake_garmin_json(1, "2026-01-05", rpe=None), fake_garmin_json(2, "2026-01-07")])

    assert sync.sync_sessions(client, log, date(2026, 1, 10)) == Merged(added=2, updated=0)
    assert client.requests[-1] == ("2025-10-12", "2026-01-10")

    client.raw_sessions[0][_GarminJson.RPE] = 60
    client.raw_sessions.append(fake_garmin_json(3, "2026-01-12"))
    assert sync.sync_sessions(client, log, date(2026, 1, 12)) == Merged(added=1, updated=1)
    assert client.requests[-1] == ("2026-01-04", "2026-01-12")

    assert [s.rpe for s in sessions.read_sessions(log)] == [6, 5, 5]


def test_sync_since_overrides_the_automatic_start(tmp_path):
    """--since reaches further back than the overlap, e.g. to backfill an edit to an old session."""
    client = FakeGarmin([])

    sync.sync_sessions(client, tmp_path / "sessions.csv", date(2026, 1, 10), since=date(2025, 6, 1))

    assert client.requests == [("2025-06-01", "2026-01-10")]


def test_sync_with_an_unknown_type_writes_nothing(tmp_path):
    """An unknown type aborts the whole sync, known sessions included, so the log never holds a type the report can't group."""
    log = tmp_path / "sessions.csv"
    client = FakeGarmin([fake_garmin_json(1, "2026-01-05"), fake_garmin_json(2, "2026-01-06", type_key="other")])

    with pytest.raises(garmin.UnknownTypesError, match="other"):
        sync.sync_sessions(client, log, date(2026, 1, 10))

    assert not log.exists()
