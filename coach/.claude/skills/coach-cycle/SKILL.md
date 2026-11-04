---
name: coach-cycle
description: Run the coach Garmin sync and training-load report (coach.sync / coach.report). Use when asked to sync Garmin, check fitness, fatigue or form, or whether to train hard or easy.
---

# Coach cycle

`coach.sync` syncs sessions from Garmin into `coach/data/sessions.csv`. `coach.report` reads only that file and prints fitness, fatigue and form per day, and load, monotony and strain per week.

## Environment

- Credentials live in `coach/.env`. Never read it, with `cat` or any other tool; a `Read(**/.env)` deny rule protects it. Source it to run sync, as in step 1 below.
- If `garminconnect` is missing, replace `python3` with `uv run --with garminconnect==0.3.2` in step 1.
- The first login may prompt for an MFA code. You can't answer it, so ask the user to run step 1 themselves, prefixed with `!`.

## Instructions

1. Sync: `source coach/.env && python3 -m coach.sync`. It only reads Garmin and writes the local log, so it needs no confirmation. Pass `--since YYYY-MM-DD` to re-sync further back.
2. Report: `python3 -m coach.report` (`--days N`, `--weeks N`).
3. Tell the user today's form, fatigue and fitness, how they compare with the last few days, the latest week's monotony, and any unrated sessions. Ask them to rate those on Garmin and re-sync.

## Cautions

- Rows marked `calibrating` (the first 42 days of the log) aren't trustworthy yet. Say so.
- Describe the numbers; don't prescribe sessions. They don't predict injury: point the user to sleep, HRV and how they feel too.
- Never hand-edit `sessions.csv` to change RPE. Rate the session on Garmin and re-sync, or the next sync overwrites the edit.
