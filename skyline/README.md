# Skylines, played

A skyline and a spectrum analyser are the same picture: a row of vertical bars
of varying height. So the picture is played. Twenty-seven cities, built from
published building heights and coordinates, drawn as a wheel of towers and
sounded as a chord that changes as the listener turns.

## Contents

| File | What it is |
|---|---|
| `build_skylines.py` | Builds `data/skylines.json` from the published records: which cities, which towers, and the floors below. |
| `supplement.py` | The published-list supplement for cities whose records are thin; its docstring says which and why. |
| `prune_payload.py` | A one-off, kept for the record: it stripped the retired panorama out of `data/skylines.json` on 2026-09-04, and `build_skylines.py` was changed the same day to emit the shape it left. |
| `keys.py` | What key each city is in, and why that is chosen rather than derived from the buildings. |
| `app.js` | The app: the wheel, the meter, the synthesis and the keyboard handling. |
| `template.html` | The app's shell and its styles. |
| `build_app.py` | Assembles `template.html`, `data/skylines.json` and `app.js` into one self-contained `skyline-app.html`. |
| `test_app.js` | 43 checks: no empty bearing, no tower name colliding with another or with the compass, no bar reaching into the foot. |
| `data/skylines.json` | The payload: 27 cities, each with its towers, its key and its mode. |

## Run it

```
python3 build_app.py     # writes skyline-app.html, self-contained
node test_app.js         # prints "43/43 checks passed"
```

`test_app.js` needs jsdom. The archive carries no `package.json` and no
`node_modules`, so install it yourself before running the harness.

The built `skyline-app.html` is not in this archive either: it is generated,
and `build_app.py` writes it in a second.

**`build_skylines.py` will not re-run.** Its raw input, the Wikidata building
dump, was never archived, so `data/skylines.json` here is the last output of a
pipeline nobody can repeat; the script is included because it is the account of
how the payload was built, not because it can rebuild it. Everything downstream
of the payload - the app, the tests, the key table - does run.

## What is measured and what is invented

- **Measured.** Each building's structural height and coordinate, and the true
  compass order of the towers around the wheel, from the height-weighted centre
  of the city.
- **Chosen.** The floors. `build_skylines.py` holds `RING_FLOOR = 55.0` metres
  for what the wheel draws and `MIN_HEIGHT = 80.0` metres for the headline
  count, and clamps a tower closer than 400 metres to 400 so a building the
  listener is standing under cannot dwarf the rest.
- **Rearranged.** The spacing around the wheel. Towers hold their true compass
  order; the angle between any two of them does not survive, because a downtown
  occupies perhaps forty degrees of a real horizon and a wheel reproducing that
  would be two-thirds empty.
- **Invented.** The sound, all of it. There is no sense in which a city has a
  pitch. The mapping is written out in full on the page and in `app.js`: 96
  bars feed at most 7 voices at once, and the same city at the same bearing
  always makes the same sound.
