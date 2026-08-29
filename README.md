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
| `build_hero.py` | Builds the front-page hero data by sampling the live payload: coastlines and 3,996 of the model's nodes at their real coordinates. |
| `HANDOFF.md` | **Read this first.** Orientation for anyone, human or AI, picking the project up cold. |
| `backups/` | Dated byte-identical copies of `site/` taken before a deploy. |
| `tests/` | Node harnesses that boot the atlas headlessly and check it. |

## The front-page hero, and the graphics decision

The hero is the model on a rotating globe. Nothing on it is decorative:
coastline rings from the country polygon set, and 3,996 of the 86,622 nodes
at their recorded coordinates, coloured by kind. Each layer has a quota, because
a uniform sample of this payload would be four parts power station and nothing
else. It reads the same file the atlas runs on, so the front page cannot drift
away from the model. The only invention is the flow field, which is a smooth
analytic function rather than wind data, and the code says so where it is
defined.

It renders twice, deliberately.

`assets/hero.js` is a 2D canvas version with no dependencies. It starts
immediately, works in every browser, and is what the page ships with.

`assets/hero-gl.js` then tries to upgrade it. If the browser reports WebGL, it
fetches three.js from a CDN, builds the same scene in 3D, and once it has a
frame on screen fades out the 2D layers and stops their loop. If any link in
that chain fails — no WebGL, blocked CDN, slow network, thrown error — nothing
happens and the 2D hero keeps running. The page never waits on it.

What 3D actually buys: real depth, so geometry behind the globe is occluded by
the depth buffer rather than by a hand-written facing test; additive blending,
so overlapping light accumulates the way light does, which is where the glow
comes from; and trails as real geometry, each particle carrying a nine-point
history, so a streamline has a gradient along its length instead of being a
smear left in a fading framebuffer. About 23,000 line segments and 1,900
sprites, roughly ten times what the 2D path can carry.

**WebGPU is deliberately not used.** Its support still trails WebGL by a wide
margin, and this is a front page rather than a demo — a blank hero for a share
of visitors is not worth the marginal gain. The structure would take a WebGPU
renderer later without changes to anything above it.

Tested in three states: no WebGL (falls back cleanly, 2D keeps drawing), WebGL
present (three.js requested, 2D still drawing until the handover), and
reduced-motion (one static frame, no CDN request, no animation loop).

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
