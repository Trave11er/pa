# Coach

A personal training log: it turns past sessions into fitness, fatigue and form, so training can be moderated by how tired you are.

## Language

### Sessions

**Session**:
One bout of training recorded on the watch, of a single type, belonging to the day it started, identified by its Garmin id. Combined training (e.g. run then strength training) is recorded as separate sessions, one per type.
_Avoid_: Activity (Garmin's word for it), workout, exercise

**Duration**:
How long a session lasted from start to stop, rests included.
_Avoid_: Moving time, active time

**Unrated session**:
A session with no RPE. It still happened, so its day is not a rest day, but it adds no load, so its load is understated.
_Avoid_: Missing session, incomplete session

**Type**:
The kind of training a session was, exactly as Garmin names it (e.g. running, strength training).
_Avoid_: Sport, activity type, category

**RPE**:
How hard the whole session felt, rated by the user from 1 to 10 after it ended.
_Avoid_: Effort, intensity, perceived effort

**Sync**:
Copying new sessions from Garmin into the log.
_Avoid_: Import, fetch, pull

### Load

**Load**:
How much training a session was: its RPE times its duration in minutes. Comparable across all types.
_Avoid_: Training load, TSS, stress, volume

**Daily load**:
The total load of every session on one day.
_Avoid_: Day total

**Rest day**:
A day with no sessions, rated or unrated; its daily load is zero.
_Avoid_: Off day, gap

### Fitness and fatigue

**Fatigue** (ATL):
Recent daily load, weighted towards the last week; how tired training has made you.
_Avoid_: Tiredness, acute load

**Fitness** (CTL):
Long-run daily load, weighted over about six weeks; how much training you are used to.
_Avoid_: Chronic load, base

**Form** (TSB):
Fitness minus fatigue at the start of a day. Very negative means carrying a lot of fatigue; around zero or slightly positive means fresh.
_Avoid_: Freshness, readiness, balance

**Calibration period**:
The first six weeks of the log, while fitness and fatigue are still settling and not yet trustworthy.
_Avoid_: Warm-up, burn-in, settling period

**Monotony**:
How alike a week's daily loads are: their mean divided by their spread. High means too few easy days.
_Avoid_: Variety, sameness

**Strain**:
A week's total load multiplied by its monotony.
_Avoid_: Stress, overload
