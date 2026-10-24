# Skylines, played

A skyline and a spectrum analyser are the same picture: a row of vertical bars
of varying height. So the picture is played. Each city's standing buildings,
from Wikidata and checked against OpenStreetMap, are drawn as a wheel of
towers and sounded as a chord that changes as the listener turns. The taller
the towers in view, the louder the chord.

## Contents

| File | What it is |
|---|---|
| `fetch_wikidata.py` | Pulls every tall item near each city from Wikidata, with its classes, state of use, dates and whether it is inside the city, and archives the whole answer in `data/raw/`. |
| `fetch_osm.py` | Pulls the buildings OpenStreetMap maps near each city, archived the same way. |
| `build_skylines.py` | Builds `data/skylines.json` from the two archived pulls: which towers stand, which cities have enough of them for a wheel, and the wheel and meter for each. Its docstring lists every filter. Writes `data/filter_report.json`, every dropped item and why. |
| `test_skylines.py` | Recomputes from the raw pulls that every tower on every wheel stands, is a building, is in its city and appears once; that each city's tallest tower is its loudest bar; and that the build reproduces the payload. Each check has a `--break` that puts back the fault it exists for. |
| `keys.py` | What key each city is in, and why that is chosen rather than derived from the buildings. |
| `app.js` | The app: the wheel, the meter, the synthesis and the keyboard handling. |
| `template.html` | The app's shell and its styles. |
| `build_app.py` | Assembles `template.html`, `data/skylines.json` and `app.js` into one self-contained `skyline-app.html`. |
| `test_app.js` | Checks on the built app: no empty bearing, no tower name colliding with another or with the compass, no bar reaching into the foot, the sound stopping when the tab is hidden. |
| `update_page.py`, `page.html` | Write `site/skyline.html`; every number on it comes from the payload. |
| `data/raw/` | The archived pulls, with their licences (`data/raw/README.md`). |

## Run it

```
python fetch_wikidata.py         # minutes; writes data/raw/wikidata_<date>.json
python fetch_osm.py              # ten minutes or so; writes data/raw/osm_<date>.json.gz
python build_skylines.py --apply # writes data/skylines.json
python test_skylines.py          # exit 0 when every check passes
python build_app.py              # writes skyline-app.html, self-contained
node test_app.js
```

`test_app.js` needs jsdom. The archive carries no `package.json` and no
`node_modules`, so install it yourself before running the harness.

A fresh pull will not give the same towers: Wikidata and OpenStreetMap are
edited every day. The archived pulls in `data/raw/` reproduce the shipped
payload exactly, and `test_skylines.py` checks that they do.

## What is measured and what is invented

- **Measured.** Each building's height and coordinate (Wikidata), that it
  stands (Wikidata has no demolition date or unbuilt status for it, and
  OpenStreetMap maps it), and the true compass order of the towers around the
  wheel, from the height-weighted centre of the city.
- **Chosen.** The floors: the wheel takes buildings of 55 m and up, at most
  120, and the headline count uses 80 m. A tower closer than 400 m to the
  centre is held at 400 m. A city needs at least 7 towers of 80 m and 16 on
  the wheel; cities Wikidata records too thinly are dropped and named. Masts,
  TV towers and observation towers are left out: they are not buildings.
- **Rearranged.** The spacing around the wheel. Towers hold their true compass
  order; the angle between any two of them does not survive, because a
  downtown occupies perhaps forty degrees of a real horizon and a wheel
  reproducing that would be almost nine-tenths empty.
- **Invented.** The sound, all of it. There is no sense in which a city has a
  pitch. A tower's height, as a share of its city's tallest, to the power 1.6,
  sets how loud its note is; the mapping is written out in full on the page
  and in `app.js`, and the same city at the same bearing always makes the same
  sound.
