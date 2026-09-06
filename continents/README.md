# Where the ground goes

Three questions that look like one, with answers five orders of magnitude
apart: how well present-day plate motion is measured, how much published
reconstructions of the past disagree, and how far apart the published futures
are.

Builds `site/continents.html`, `site/continents-app.html` and six figures.

## Run order

```
python3 fetch_ngl.py          # MIDAS GNSS velocities   -> data/stations.csv
python3 fetch_static.py       # ITRF2020-PMM, PB2002, NNR-MORVEL56 Table 1
python3 fetch_osf.py          # the four future scenarios -> data/future_masks.npz
python3 fetch_gplates.py      # 335 cached reconstructions -> data/gplates_cache.json
python3 fetch_land.py         # 153 reconstructed coastline frames -> data/land.json
python3 build_continents.py   # every gate, then outputs/continents_payload.json
python3 fig_continents.py     # six figures -> ../site/assets/, each audited (0 problems)
python3 build_app.py          # ../site/continents-app.html
python3 update_page.py --apply
python3 test_continents.py
python3 break_gates.py     # every gate, broken on purpose; the build must refuse
node test_app.js
```

`fetch_gplates.py` makes 335 requests at one a second and `fetch_land.py`
another 153 much larger ones; together about half an hour. Everything else is
quick. All four fetchers are idempotent and the
build never touches the network.

## Files

| File | What it is |
|---|---|
| `fetch_ngl.py` | MIDAS velocities and NGL's plate assignment. Asserts the IGS20 frame (gate B7). NGL rebuilds these weekly, so a stale pin is reported rather than treated as corruption. |
| `fetch_static.py` | ITRF2020-PMM and PB2002 verbatim. Extracts NNR-MORVEL56 Table 1 from the Argus et al. 2011 PDF and cross-checks all 25 plates against MintPy's independent transcription. |
| `fetch_osf.py` | Reads the 50 scenario grids straight out of the 4.5 MB archive without extracting it, normalises longitude, runs gates A1-A6, records the A4 negative control, and packs the masks to 0.7 MB. |
| `fetch_gplates.py` | 8 pinned models x 51 ages, cached. Runs gates C1 and C2. |
| `fetch_land.py` | Reconstructed coastlines for three of those models at every age, unwrapped, unioned, clipped at the seam, simplified and delta-encoded. This is what makes the continents move in the viewer. Nothing modern is drawn at any age. |
| `geo.py` | Equal Earth forward and inverse, the limb, the graticule, and the antimeridian split. |
| `otis_grid.py` | The OTIS reader and the anchor gate. Read its docstring before touching the longitude handling. |
| `plates.py` | Euler-vector fitting, the distance field, the exclusion rule, and the two ITRF comparisons. |
| `break_b1.py` | The experiment that broke the first version of the plate gate. Writes nothing. |
| `build_continents.py` | Computes, gates, then writes. Nothing on a failed gate. |
| `fig_continents.py` | The six figures, through `sitefig.py`. |
| `build_app.py` | The reconstruction viewer, payload inlined. |
| `update_page.py` | Renders the page; idempotent on the shipped tree. |
| `test_continents.py` | The failure modes, including two negative controls. |
| `break_gates.py` | Damages each input in a way that produces a plausible wrong answer and checks the build refuses. A gate never seen to fail is not known to work, and that applies to the gates. |
| `test_app.js` | The viewer's failure modes: the sentinel, the three states, no interpolation, great-circle parity. |

## What it does not claim

- Where any named place will be, at any confidence, for any of the four
  futures. The four are not ranked; the paper that built all of them ranks
  none above the others.
- A formal uncertainty on any reconstruction. None is published, and the
  field's own review names uncertainty quantification as an open problem.
- That a scenario's south polar land is Antarctica. The future grids carry no
  plate identities, so the page says "land in the south polar region".
- Any cause for the boundaries that have changed speed.
- Anything past 500 million years, where fewer than half the models reach.

## The two traps

Both are in the data rather than in the code, and both produce a confident
wrong number rather than an error.

**The longitude convention.** Two of the four scenario grids declare
-180..180 and two declare 0..360. Read as they come, two of the four sit half
a world out and the four present-day grids appear to disagree about 34 per
cent of the planet instead of 0.8. That would have been the page's headline.
`otis_grid.normalise` reads each file's own header, and `anchor_check` tests
the result against twelve named points whose answer comes from an ordinary
world map — an anchor from outside the data, because four grids read by one
reader cannot catch an error they share.

**A station that is not on its plate.** Kilauea's south flank moves for its
own reasons and it contaminates the Pacific's fitted rotation; `ILSG` on
Salas y Gomez is filed under the Pacific and is on Nazca. The first ruins the
rotation, the second ruins the residual while leaving the rotation intact, so
there are two gates and not one. The exclusion is a stated rule, not a list of
names.
