# The true climate cost of a thing

A life-cycle model that shows its working. Give it an item, a producing region
and a destination, and it returns the chain as it happens: a spine of stages
from the field to the bin, with a branching tree under each stage showing where
that stage's emissions came from. The branches have branches, and every edge
carries the share of that process the product is charged for.

## Contents

| File | What it is |
|---|---|
| `lca.py` | The engine and the command line. Also writes the visualiser with `--build`. |
| `data/processes.py` | The process graph: every process, its direct emissions, its inputs, and the allocation basis on each edge, each with the note and source it came from. |
| `engine.js` | The same arithmetic in JavaScript, so the page recomputes rather than looking answers up. `climate-cost/test_scene.js` checks the two against each other. |
| `scene.js` | The visualiser's drawing. |
| `template.html` | The visualiser's shell; `lca.py --build` fills in the engine, the scene and the data. |
| `test_lca.py` | The model against its published ranges, the tree summing at every node, allocation compounding down each chain, and the levers moving the answer the way physics says. |
| `test_scene.js` | The JavaScript engine against `lca.py`, plus the scene's layout and overlap checks. |

## Run it

```
python3 lca.py                      # the default item, a field tomato, Spain to Texas
python3 lca.py --list               # every item, region and freight mode
python3 lca.py --all                # one line per item at its default route
python3 lca.py --item cheese --from FR --to US-NY
python3 lca.py --build              # writes climate-cost.html, self-contained
python3 test_lca.py                 # prints "0 failure(s)"
```

`test_scene.js` is here for completeness and does **not** run from this archive:
it loads jsdom and three from the site repository's `tests/node_modules`, which
is not part of it.

## What to expect

`--all` prints twenty items at their default routes, from beef at 75.49 kg CO2e
per kilogram as eaten down to a field tomato at 0.67. `test_lca.py` prints
`0 failure(s)`; every total lands inside the published range it is checked
against, and the cutoff it applies discards under 1% of any total.

## The assumptions, which are the point

- **Allocation is stated on every edge**, not buried. A slaughterhouse also
  makes leather, a dairy cow also becomes beef, and the share charged to the
  product in the model is a judgement with a named basis. Where the shared
  stage is most of the answer - cheese - the published bases disagree by half
  again, and the model runs each of them rather than picking one.
- **Global warming potentials are 100-year values** and `data/processes.py`
  names which: nitrous oxide at 273 times carbon dioxide, and fugitive methane
  at 28 kg CO2e per kg, the AR5 100-year value, with the AR6 figure of 29.8 for
  fossil methane recorded beside it.
- **A vehicle's factory is divided by the distance it will cover**, and that
  lifetime is an assumption rather than a measurement. It is exposed as a
  control so it can be argued with instead of inherited.
- **Production electricity and consumption electricity are charged
  separately**, at the grid of the region where each happens.
