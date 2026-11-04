"""CLI printing fitness, fatigue and form per day, and load, monotony and strain per week.

Reads data/sessions.csv only; never talks to Garmin. Run sync.py first for fresh numbers.
"""

import argparse
from datetime import date, datetime

from coach.core.load import Day, Week, measure_weekly_strain, track_form
from coach.core.sessions import LOG, Session, read_sessions


def _render_daily_form(days: list[Day]) -> str:
    """Render the daily form, marking the calibration period, so the latest form can be read against the days before it."""
    lines = [f"{'date':<10}  {'load':>5}  {'fatigue':>7}  {'fitness':>7}  {'form':>6}"]
    for day in days:
        mark = "  calibrating" if day.calibrating else ""
        lines.append(f"{day.date}  {day.daily_load:5.0f}  {day.fatigue:7.1f}  {day.fitness:7.1f}  {day.form:6.1f}{mark}")
    return "\n".join(lines)


def _render_weekly_strain(weeks: list[Week]) -> str:
    """Render each week's load per type, monotony, strain and unrated sessions, because those only make sense over a week."""
    lines: list[str] = []
    for week in weeks:
        monotony = "-" if week.monotony is None else f"{week.monotony:.2f}"
        strain = "-" if week.strain is None else f"{week.strain:.0f}"
        lines.append(f"week of {week.start}: {week.load:.0f} load, monotony {monotony}, strain {strain}")
        for type_, totals in week.by_type.items():
            lines.append(f"  {type_}: {totals.session_count} sessions, {totals.minutes:.0f} min, {totals.load:.0f} load")
        lines.extend(f"  unrated: {s.date} {s.type}" for s in week.unrated)
    return "\n".join(lines)


def render_report(sessions: list[Session], today: date, day_count: int, week_count: int) -> str:
    """Render the last days and weeks up to today; with no sessions, point at coach.sync instead."""
    if not sessions:
        return "No sessions yet: run python3 -m coach.sync first."
    days = track_form(sessions, today)[-day_count:]
    weeks = measure_weekly_strain(sessions, today)[-week_count:]
    return f"{_render_daily_form(days)}\n\n{_render_weekly_strain(weeks)}"


def main() -> None:
    """Parse the window sizes and print the report from the stored sessions."""
    parser = argparse.ArgumentParser(description="Report fitness, fatigue and form from data/sessions.csv.")
    parser.add_argument("--days", type=int, default=14, help="days of daily form to show")
    parser.add_argument("--weeks", type=int, default=8, help="ISO weeks of strain to show")
    args = parser.parse_args()
    print(render_report(read_sessions(LOG), datetime.now().astimezone().date(), args.days, args.weeks))


if __name__ == "__main__":
    main()
