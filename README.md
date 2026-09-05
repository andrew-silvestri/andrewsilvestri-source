# 00 PUBLISH — everything that goes on andrewsilvestri.com

This is the landing area. If it is in here, it is either live on the site or
one step from being live. Everything else in `13 - Energy Modeling` is working
material: the numbered folders 01–21 are the archive and are unchanged.

## Layout

| Path | What it is |
|---|---|
| `site/` | The website itself. Plain files, no build step, no dependencies. Upload the **contents** of this folder to the repo root. |
| `site/downloads/` | The per-project source archives the Code page links to. Rebuilt by hand when a project changes. |
| `site/assets/` | Figures and images used by the pages. |
| `longevity-quotient/` | The longevity quotient project — model, data, tests, and the visualiser template it generates. |
| `build_site.py` | The generator that produced the first version of the site pages. |
| `build_layer_diagram.py` | Draws the front-page hero, the nine-layer diagram, from the atlas payload (see below). |
| `build_hero_figure.py` | Draws the globe on the atlas page from the atlas payload. |
| `HANDOFF.md` | **Read this first.** Orientation for anyone, human or AI, picking the project up cold. |
| `backups/` | Dated byte-identical copies of `site/` taken before a deploy. |
| `tests/` | Node harnesses that boot the atlas headlessly and check it. |

## The front-page hero

The home page opens on the model's nine layers, `assets/atlas_layers-notes.png`
(a 350px render for phones beside it), drawn by `build_layer_diagram.py`: the
layers as bands with their node counts, every link between layers as an arc,
one-way links on the right with one head and two-way links on the left with
two, the stroke as the number of links. Every number and every link is read
from the payload, and the rank rule that decides direction from `atlas-app.js`.
It replaced the globe on 2026-09-04 because a globe of dots is a map of where
things are, and the first picture should say what the model *is*. The globe,
`assets/hero_globe.png` by `build_hero_figure.py`, now sits on the atlas page,
where a map is the right object. Re-run both builders after the payload
changes; `tests/test_generators.py` covers the layer diagram.

## Publishing

Upload the contents of `site/` — not the folder itself — to the root of the
`andrew-silvestri.github.io` repository. `index.html` must land at the top
level. The `CNAME` file in there is what keeps the custom domain attached
across pushes; do not drop it.

The domain already resolves: Cloudflare DNS → four GitHub Pages A records,
grey-cloud, with `www` as a CNAME. Nothing about that needs touching again.

## Where the published work came from

The site publishes results from the numbered folders. Those stay where they
are; only the published form lives here.

| On the site | Source folder |
|---|---|
| Industrial heat break-even | `01 Industrial Heat Breakeven` |
| Direct air capture TEA | `02 DAC Adsorption TEA` |
| Battery revenue simulator | `03 Storage Revenue Stack` |
| World energy web, v1–v5 | `10`, `11`, `13`, `14` |
| The calibrated model and atlas | `16`, `17`, `18`, `19` |
| Pipeline liquid holdup | `12 Targa Holdup App` — page only, code not published |
| Longevity quotient | `00 PUBLISH/longevity-quotient` (lives here) |

The holdup work came out of an internship, so the method and the result are on
the site but the engine, the simulation library and the source workbook are not.
