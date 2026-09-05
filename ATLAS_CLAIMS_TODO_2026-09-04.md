# Atlas claims still to correct (2026-09-04)

Found by the read-only claims pass in `DESLOP_3C_2026-09-04.md` §3 and left
for a pass of their own. Each is a sentence on a page or in the app that
the code, the payload, or a run does not bear out. Evidence is where the
3c note says; none of these has been touched. The three that were fixed
before the push (the §2 table, "calibrated", the model-code row) are not
here. The demand-response link problem is a model bug, not copy, and has
its own document: `ATLAS_DEMAND_RESPONSE_2026-09-04.md`.

1. **"Settles in between twenty and fifty steps"** — `atlas.html` lines 24
   and 66. The engine converges on `mx < 1e-5` with a cap of 60; across
   the 60 scenarios the range is 5 to 42 and 14 settle in fewer than 20 (a
   single-node push, 11). The upper bound holds; say "in fewer than sixty
   steps, usually a few dozen" or give the measured range. The comment at
   `atlas-app.js` line 68 ("settle in 30 to 40") is wrong the same way.
2. **"Every node holds one measured quantity and names where it came
   from"** — `atlas.html` line 22; the app header's "Every parameter comes
   from a public data set" (`atlas-app.js` lines 1177–1179). 1,142
   consumer nodes carry "elasticity from literature; size from real
   demand", all 24 behaviour nodes carry "a model of where demand is
   decided, not a measurement", and 2,896 ports carry a name and a harbour
   size class and no number. `res`, the one per-node number the engine
   reads, is a per-type assumption (`model.html` §5.2). Say what is
   measured and what is assumed, per layer.
3. **`model.html` §4 step 2 "(1 − inertia)"** is `(1 − 0.6·RES)` in code
   (`atlas-app.js` line 154). The inertia table in §5 gives single values
   where the payload holds ranges (event 0.15–0.55, consumer 0.18–0.73,
   station 0.14–0.74, psych 0.30–0.76, market 0.089–0.62); the weight
   table's "grid→district 0.60 fixed" is 0.42–0.60 and "station→grid 0.45
   ÷ plant count" is a stored weight of 0.204–0.750 (the division is the
   engine's fan-in). "Event→grid log10 of real damage cost": 8,733 of the
   9,259 events are USGS earthquakes with no damage cost.
4. **Minor.** "Starting at the most connected power plant… moves one other
   node" (`atlas.html` line 113): Lake Hargy pushed moves only itself.
   "Reach spans five orders of magnitude": 2 to 77,669 is 4.6. "Every
   position is a real coordinate" (app header): the 24 behaviour nodes and
   the sun sit at 0,0. The tab subtitles "2,896 ports and benchmarks" and
   "34,065 settlements" sit beside legends that count 3,627 and 35,207.
5. **`model.html` §7 "How to run the model"** — the three commands run the
   July 2026 Julia build (7,192 nodes; `energy_terminal.py` and
   `make_chart.py` are in `01 ARCHIVE/18 Final Deliverables`), not the
   model the page describes. The paragraph under it now says so; the
   section's title and table still read as the current model's.
6. **No test compares the two engines.** `atlas-app.js` (the app) and
   `build_atlas_figures.py` (the figures) implement the same arithmetic
   separately; the comment that claimed a test ran both is corrected, and
   the test it named should exist.
