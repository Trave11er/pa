from datetime import date

from coach.core import sessions
from coach.core.sessions import Merged, Session, Type


def test_merge_adds_new_updates_changed_and_keeps_unrated_empty(tmp_path):
    """Re-merging an id replaces its row; an unrated session round-trips as None, not zero."""
    log = tmp_path / "sessions.csv"
    unrated = Session("1", date(2026, 1, 5), Type.RUNNING, 30.0, None, None)
    rated = Session("2", date(2026, 1, 4), Type.BOXING, 60.0, 8, 150.0)
    assert sessions.merge_sessions([unrated, rated], log) == Merged(added=2, updated=0)
    assert sessions.merge_sessions([unrated._replace(rpe=6), unrated._replace(garmin_id="3")], log) == Merged(1, 1)

    assert sessions.read_sessions(log) == [rated, unrated._replace(rpe=6), unrated._replace(garmin_id="3")]
    assert log.read_text().splitlines().count(",".join(Session._fields)) == 1  # one header row


def test_absent_log_reads_as_empty(tmp_path):
    """Before the first sync there is no file, and that is an empty log rather than an error."""
    assert sessions.read_sessions(tmp_path / "sessions.csv") == []
