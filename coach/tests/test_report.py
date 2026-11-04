from datetime import date

from coach import report
from coach.core.sessions import Type
from coach.tests.fakes import build_session


def test_report_renders_daily_form_and_weekly_strain():
    """From plain sessions: daily form in the calibration period, weekly per-type totals and the unrated session."""
    sessions = [build_session("2026-01-05", 60, 5), build_session("2026-01-07", 45, None, Type.BOXING)]

    out = report.render_report(sessions, date(2026, 1, 7), day_count=3, week_count=8)

    assert out.count("calibrating") == 3
    assert "running" in out and "300 load" in out
    assert "unrated" in out and "2026-01-07 boxing" in out


def test_report_without_sessions_points_at_sync():
    """With nothing synced the report says to run sync instead of printing empty tables."""
    assert "coach.sync" in report.render_report([], date(2026, 1, 7), day_count=14, week_count=8)
