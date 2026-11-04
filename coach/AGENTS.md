# coach

- `core` never imports `connectors`; only the CLIs (`sync.py`, `report.py`) wire the two together.
- Import as `coach.core…` / `coach.connectors…` and run the CLIs from the repo root as `python3 -m coach.sync` / `python3 -m coach.report`.
- Load is session-RPE (RPE x minutes) for every type. Don't mix in heart rate or Garmin's training load: the types would stop sharing one scale.
- Use the terms in `GLOSSARY.md` (fatigue/fitness/form in code, not atl/ctl/tsb).
