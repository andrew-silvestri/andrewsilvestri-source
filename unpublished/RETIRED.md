# Retired pages

Kept, not linked, not published. `publish.sh` mirrors `site/` only, so
nothing here ships. Each entry: what it was, when it came off, why. There
was no note here before 2026-09-05; the list lived in HANDOFF.md section 2,
which still carries the one-line version.

- **The bookshelf** - `desktop.html`, `bookshelf-app.html`,
  `assets/bookshelf-demo-*.{webp,png}`, `downloads/bookshelf-code.zip`,
  `build_bookshelf_demo.js`. A wallpaper built in the browser from a
  Goodreads export: drawn spines, or real covers fetched by ISBN from Open
  Library. Retired 2026-09-05 (PHASE5, Part 1): a desktop toy on a site
  about energy models, and the one page whose privacy claim ("nothing else
  from your export") could not be shortened for a card without becoming
  false. The sources are `bookshelf/` (README, wallpaper setter, demo
  render) and the app file here; the last download archive is in
  `downloads/`. The live URLs 404 from the publish that followed.
- **The neuron constraint app** - `neuron-app.html`, with its sources in
  `neuron/` here (`template-app.html`, `build_app.py`). Five checkboxes over
  the 32 precomputed subset counts of the NeuroMorpho census, reorderable,
  so that each constraint's cost could be read in the order ticked. Retired
  2026-09-06: it showed one of the 120 orders at a time, and a still figure
  shows all of them at once (`neuron_fig6_orders.png`, drawn by
  `neuron/fig_neuron.py` from `cascade.order_costs` in the payload), which
  is the case `prompts/NEW_PROJECTS.md` §2 says to build the still figure
  in. The card copy it carried ("costs almost nothing when applied first")
  was also wrong: the shrinkage correction is the least order-dependent of
  the five. The live URL 404s from the publish that followed.
- **dac.html**, **holdup.html**, **beans.html** - direct air capture,
  pipeline liquid holdup, the legume symbiosis. Retired before 2026-08-30;
  their figures are in `assets/` (moved out of the site on 2026-09-04).
- **running-shoes.html**, **running-shoes-app.html** - a shoe in parts, a
  three.js exploded view (opening state from
  `?shoe=1&part=2&explode=1&az=&el=`). Retired before 2026-08-30.
- **energy-web.html**, **hobbies.html**, **hobbies-app.html**,
  **navigator.html**, **navigator5.html**, **zoom_explorer.html** - earlier
  generations of the atlas and of the site (August 2026). Kept for their
  code.

## 2026-09-06, with the nonlinear hero

- **build_thumbnails.py** - the six mosaic tiles on the home page. The mosaic
  went when the home page became the hero canvas plus the index; `index.html`
  was the only page that ever referenced a `*-thumb.png`, and `library.html`
  shows those same six figures at full size, so nothing a reader could see was
  lost. The six PNGs are deleted. `sitefig.thumbnail()` stays, uncalled, for
  the crop lesson in its docstring.
- **build_model_chart.py** - `energy_model_chart.png`, the four-panel "model at
  a glance" figure. Also home-page-only, and also cut with the atlas blocks.
  Removed from `rezip_downloads.py`'s atlas-code.zip file list at the same
  time, so the archive does not ship a builder for a figure the site no longer
  has.

Both were retired rather than left building unshipped, for the reason the 714
layer render was: a generator that writes a file nothing reads goes stale
silently, and deleting the file while the generator still names it turns
`tests/test_generators.py` red instead.

