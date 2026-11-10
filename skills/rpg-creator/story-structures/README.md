# Story structures — pick ONE spine per game

Each file is a different story shape: its phase layout, pressure source, opposition, endings, cast
pattern (`cast_pattern:` line, read by `compile.py` / `roll.py` / `scorecard.py`), beat shape,
main-arc.md layout, pitfalls, and which golden rules it swaps. `scripts/roll.py` draws from these
names. During authoring, read only the chosen file.

- `conspiracy-mystery` — pull one thread, uncover a hidden web; 3 acts, a dated clock (rotating)
- `heist` — job, crew, legwork, execution, fallout; the window + heat (fixed-party)
- `siege-survival` — hold a place while resources run out; hard allocations (revolving)
- `political-intrigue` — factions trade favors toward a scheduled decision (rotating)
- `road-journey` — a chain of waystations that change the traveler (revolving)
- `time-loop` — one stretch of time repeats; knowledge and cost ratchet (solo)
- `tournament-ascent` — an underdog climbs a bracket of admirable rivals (revolving)
- `doomed-cause` — a tragedy chosen with open eyes; meaning over outcome (fixed-party)
- `seasons-of-a-community` — slice of life through a year; hangout with purpose (rotating)
- `expedition-into-unknown` — a team fills in a blank map, and pays for it (fixed-party)
- `revenge` — work through a list; each name costs a piece of the self (solo)
