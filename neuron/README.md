# The measured neuron

How much of a drawn neuron was measured. Every picture of a neuron is
schematic; so, in a different place, is every reconstruction in the public
archive, and the archive says which place in its own metadata.

The page is `site/neuron.html`. It had a reorderable-cascade interactive
until 2026-09-06; figure 6 now holds every order at once, and the app is in
`unpublished/`.

## Run it

```
python3 fetch_data.py            # both APIs, ~1 hour; writes data/ and data/manifest.json
python3 build_neuron.py          # the census, the trade-off, the gradient test, the opened set, the order costs -> outputs/neuron_payload.json
python3 fig_neuron.py            # six figures -> ../site/assets/neuron_fig*.png, each audited (must print 0 problems)
python3 update_page.py --apply   # writes ../site/neuron.html from template.html and the payload
python3 test_neuron.py           # the project's own failure modes
python3 test_neuron.py --network # and the parser against L-Measure's independent computation

python3 fetch_data.py --exemplars-only   # re-choose the two cells figure 2 draws
python3 fetch_data.py --complete-only    # open the complete set again (~2 min) and re-choose the cell figure 5 draws
```

`fetch_data.py` is the only step that touches the network, and it is the only
slow one. Everything after it runs from `data/`.

## Files

| File | What it does |
|---|---|
| `fetch_data.py` | Pages the whole NeuroMorpho.Org API into `data/neurons.csv.gz`, samples reconstructions across many archives, takes their metrics, opens every file that passes all five constraints, keeps the three files the figures draw, and records a SHA-256 of each output in `data/manifest.json`. |
| `swclib.py` | Parses SWC, and holds the rule about depth: `load_xy()` returns two columns and is what the figures use; `load_xyz()` reads its provenance from the file's directory and refuses anything that came out of a slice. Run it directly for a self-check against `tests/fixture.swc`. |
| `build_neuron.py` | The cascade, all 32 subsets and what each constraint costs at each position over all 120 orders, the trade-off measured both from metadata and from files, the within-archive gradient test, the span arithmetic, the complete set as its files hold it, and the geometry of the two drawing figures (the panel boxes, and what a pixel is in each). Writes `outputs/neuron_payload.json`. |
| `fig_neuron.py` | The six figures, through `sitefig.py`. No figure uses a z coordinate. Figures 2 and 5 draw widths as polygons in data units, so a width is the file's number at the panel's scale; a file holding one width is drawn as a hairline. |
| `update_page.py` | Writes `../site/neuron.html` from `template.html` and the payload. |
| `test_neuron.py` | Nine failure modes, listed in its docstring. |
| `tests/fixture.swc` | A synthetic reconstruction whose every quantity was worked out by hand. |
| `data/neurons.csv.gz` | The frozen census: one row per reconstruction. |
| `data/swc_metrics.csv` | Morphometrics for the sampled files, computed by `swclib`. |
| `data/complete_metrics.csv` | The same, for every file that passes all five constraints: the complete set, opened. |
| `data/swc/<source>/` | The three reconstructions the figures draw, and only those: the two in figure 2, and the one from the complete set in figure 5, chosen by the rule in `fetch_data.pick_drawn()`. |

## Two things that would be easy to get wrong

**Depth.** Reconstructions made in slices are distributed without a shrinkage
correction, and the tissue loses roughly half its thickness. Drawing them in
three dimensions would produce a figure wrong by about a factor of two in one
axis and entirely plausible to look at. `load_xy()` returns two columns so
that reaching for z is an error rather than a picture, and `test_neuron.py`
check 1 asserts that no figure reaches for it by any route.

**The parser.** Everything on the page rests on segment arithmetic, and a
parser can be wrong in several ways and still produce a total near a published
average, because an average is a loose target and usually not even the same
statistic. So the parser is pinned to `tests/fixture.swc`, which was computed
by hand, and cross-checked against L-Measure's independent computation of the
same quantities on the same bytes. Neither check is an aggregate.
