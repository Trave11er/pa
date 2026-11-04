"""Load: turns sessions into daily fitness, fatigue and form, and weekly monotony and strain.

Load is session-RPE (RPE x minutes) for every type; unrated sessions add no load.
"""

import statistics
from datetime import date, timedelta
from typing import NamedTuple

from coach.core.sessions import Session, Type

_FATIGUE_DAYS = 7
_FITNESS_DAYS = 42
_SEED_DAYS = 28
_CALIBRATION_DAYS = 42


class Day(NamedTuple):
    date: date
    daily_load: float
    fatigue: float  # ATL, after the day's load
    fitness: float  # CTL, after the day's load
    form: float  # TSB, at the start of the day
    calibrating: bool  # within the first _CALIBRATION_DAYS of the log


class TypeTotals(NamedTuple):
    session_count: int
    minutes: float
    load: float


class Week(NamedTuple):
    start: date  # ISO Monday
    by_type: dict[Type, TypeTotals]
    load: float
    monotony: float | None  # None when every day had the same load
    strain: float | None
    unrated: list[Session]  # so the user knows which sessions to rate on Garmin


def _measure_load(session: Session) -> float:
    """Measure one session's load, so unrated sessions count as zero in one place."""
    if session.rpe is None:
        return 0.0
    return session.rpe * session.duration_min


def _sum_daily_load(sessions: list[Session], end: date) -> list[tuple[date, float]]:
    """Sum the daily load from the first session to end, with rest days as zero so fitness and fatigue decay."""
    if not sessions:
        return []
    totals: dict[date, float] = {}
    for session in sessions:
        totals[session.date] = totals.get(session.date, 0.0) + _measure_load(session)
    first = min(totals)
    days = (first + timedelta(n) for n in range((end - first).days + 1))
    return [(day, totals.get(day, 0.0)) for day in days]


def track_form(sessions: list[Session], today: date) -> list[Day]:
    """Track fitness, fatigue and form per day up to today, seeded at typical daily load so early weeks are less skewed."""
    daily = _sum_daily_load(sessions, today)
    if not daily:
        return []
    fatigue = fitness = statistics.fmean(daily_load for _, daily_load in daily[:_SEED_DAYS])
    days: list[Day] = []
    for index, (day, daily_load) in enumerate(daily):
        form = fitness - fatigue  # before the day's load: how fresh you started it
        fatigue += (daily_load - fatigue) / _FATIGUE_DAYS
        fitness += (daily_load - fitness) / _FITNESS_DAYS
        days.append(Day(day, daily_load, fatigue, fitness, form, index < _CALIBRATION_DAYS))
    return days


def measure_weekly_strain(sessions: list[Session], today: date) -> list[Week]:
    """Measure each ISO week's load per type, monotony and strain, which only make sense over a week; today's week counts its days so far."""
    daily = _sum_daily_load(sessions, today)
    if not daily:
        return []
    weeks: dict[date, list[tuple[date, float]]] = {}
    for day, daily_load in daily:
        weeks.setdefault(day - timedelta(day.weekday()), []).append((day, daily_load))
    return [_measure_week(start, days, sessions) for start, days in weeks.items()]


def _measure_week(start: date, days: list[tuple[date, float]], sessions: list[Session]) -> Week:
    """Measure one week from its days so far, so a partial first or current week averages only the days it has."""
    if days[0][0] != start:  # the log began mid-week: the days before it were rest days
        days = [(start + timedelta(n), 0.0) for n in range((days[0][0] - start).days)] + days
    loads = [daily_load for _, daily_load in days]
    dates = {day for day, _ in days}
    in_week = [s for s in sessions if s.date in dates]
    by_type: dict[Type, TypeTotals] = {}
    for type_ in dict.fromkeys(s.type for s in in_week):
        of_type = [s for s in in_week if s.type == type_]
        by_type[type_] = TypeTotals(len(of_type), sum(s.duration_min for s in of_type),
                                    sum(_measure_load(s) for s in of_type))
    spread = statistics.pstdev(loads)
    monotony = statistics.fmean(loads) / spread if spread else None
    strain = sum(loads) * monotony if monotony is not None else None
    return Week(start, by_type, sum(loads), monotony, strain, [s for s in in_week if s.rpe is None])
