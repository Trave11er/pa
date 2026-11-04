import statistics
from datetime import date

import pytest

from coach.core import load
from coach.core.sessions import Type
from coach.tests.fakes import build_session


def test_daily_load_fills_rest_days_and_counts_unrated_as_zero():
    """Rest days and unrated-only days have zero daily load, so fitness and fatigue keep decaying through them."""
    sessions = [build_session("2026-01-01"), build_session("2026-01-01", 30, 8, Type.STRENGTH_TRAINING),
                build_session("2026-01-03", rpe=None)]

    days = load.track_form(sessions, date(2026, 1, 4))

    assert [(d.date, d.daily_load) for d in days] == [
        (date(2026, 1, 1), 540.0), (date(2026, 1, 2), 0.0), (date(2026, 1, 3), 0.0), (date(2026, 1, 4), 0.0)]


def test_form_seeds_at_mean_daily_load_and_uses_previous_day():
    """Fatigue and fitness start at the mean daily load; form is set before the day's load is applied."""
    first, second = load.track_form([build_session("2026-01-01", minutes=14)], date(2026, 1, 2))  # loads 70, 0

    assert first.form == 0.0  # seed is 35 for both
    assert first.fatigue == pytest.approx(35 + 35 / 7)
    assert first.fitness == pytest.approx(35 + 35 / 42)
    assert second.form == pytest.approx(first.fitness - first.fatigue)


def test_calibration_period_is_the_first_42_days():
    """Days 1-42 of the log are in the calibration period; day 43 is the first trustworthy one."""
    days = load.track_form([build_session("2026-01-01")], date(2026, 2, 12))

    assert all(d.calibrating for d in days[:42])
    assert days[42].date == date(2026, 2, 12) and not days[42].calibrating


def test_weekly_strain_totals_per_type_with_monotony_and_unrated_sessions():
    """A week sums load per type, monotony is mean over spread of its daily loads, and unrated sessions are listed."""
    unrated = build_session("2026-01-07", rpe=None)
    sessions = [build_session("2026-01-05"), build_session("2026-01-06", 30, 8, Type.STRENGTH_TRAINING), unrated]

    (week,) = load.measure_weekly_strain(sessions, date(2026, 1, 11))

    assert week.start == date(2026, 1, 5)
    assert week.by_type[Type.RUNNING] == load.TypeTotals(2, 120.0, 300.0)
    assert week.by_type[Type.STRENGTH_TRAINING] == load.TypeTotals(1, 30.0, 240.0)
    assert week.load == 540.0
    loads = [300.0, 240.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert week.monotony == pytest.approx(statistics.fmean(loads) / statistics.pstdev(loads))
    assert week.monotony is not None
    assert week.strain == pytest.approx(540 * week.monotony)
    assert week.unrated == [unrated]


def test_current_week_of_identical_days_has_no_monotony():
    """The current week counts only its days so far; with no spread, monotony is undefined rather than infinite."""
    (week,) = load.measure_weekly_strain([build_session("2026-01-05")], date(2026, 1, 5))

    assert week.monotony is None and week.strain is None
