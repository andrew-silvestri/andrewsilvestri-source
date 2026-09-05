# The atlas: source

The scripts that build the 86,622-node model the atlas draws, the pages
that describe it, the figures, the app as shipped, and the tests. Laid out
the way the repository is, so every relative path in the scripts holds:

    build_atlas_global.py .. build_scenarios.py   the pipeline, in the order HANDOFF lists it
    build_throughlines.py                         the propagation engine the figures use
    build_*_figures / _chart / _diagram .py       the figures, through sitefig.py (fonts/ is theirs)
    update_atlas_pages.py                         regenerates atlas.html and model.html from the payload
    site/atlas-app.html, site/assets/atlas-app.js the app; its engine is the model of record
    tests/test_parity.py, tests/parity_engine.js  the browser engine against the figures' engine, all 60 scenarios
    tests/test_atlas_interaction.js               boots the app headless against a three.js stub

Not included: the payload, `site/assets/atlas-data.js` (10 MB). It is the
file the site serves, https://andrewsilvestri.com/assets/atlas-data.js;
put it at `site/assets/atlas-data.js` and the tests, the figures and the
page generator run. The raw data the pipeline reads (GeoNames, WRI, USGS,
EM-DAT, NOAA, EI/OWID, Allen Brain Atlas) is not included either; each
script names its source at the top.

The tests need Python 3 with numpy, scipy, matplotlib and Pillow, and node
for the two JavaScript harnesses (`tests/parity_engine.js` needs nothing
beyond node).
