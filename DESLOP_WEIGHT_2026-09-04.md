# Page weight — andrewsilvestri.com — 2026-09-04

Amendment 2 of the Phase 2 go-ahead: weight is an asset problem, not a style
problem, so it is written up here and **not implemented**. Numbers are from
`_deslop/results.json` (Chromium 151, dark scheme, motion on, 1440×900 and
390×844). "Needed" pixels assume a 2× display, so an image rendered at *w* CSS
px needs at most 2*w* source pixels; anything wider is bytes the reader never
sees. Bytes are the on-disk PNG/WebP/MP4 sizes as served.

The brief's discipline is 300–600 KB per page. Six of eleven pages are over it.

## Summary

| page | loaded (motion on) | loaded (motion off) | images | video | CDN JS | est. after fix | over 600 KB? |
|---|---|---|---|---|---|---|---|
| index | 1555 | 1437 | 1231 | 0 | 118 | ~723 | **yes** |
| atlas | 257 | 202 | 138 | 0 | 56 | ~202 | no |
| model | 562 | 507 | 443 | 0 | 56 | ~385 | no |
| library | 981 | 981 | 903 | 0 | 0 | ~620 | **yes** |
| code | 40 | 40 | 0 | 0 | 0 | ~40 | no |
| heat | 736 | 552 | 476 | 185 | 0 | ~600 | **yes** |
| storage | 912 | 696 | 622 | 216 | 0 | ~720 | **yes** |
| climate-cost | 579 | 324 | 244 | 255 | 0 | ~532 | no |
| longevity | 1294 | 1106 | 977 | 189 | 0 | ~956 | **yes** |
| skyline | 404 | 155 | 80 | 250 | 0 | ~404 | no |
| desktop | 921 | 532 | 458 | 389 | 0 | ~921 | **yes** |

"Est. after fix" applies only the image fixes below (resize to 2× rendered width, palette/WebP recompression at an assumed 0.6 ratio, thumbnails for mosaic/card images). It does not remove video, CDN scripts or scene scripts; those are decisions, listed per page.

## Per page

### index.html — 1555 KB loaded (1437 KB with motion off)

Largest requests: energy_model_chart.png 219K · cdn:ajax/libs/three.js/r128/three.min.js 118K · climate_chain_tomato.png 116K · lq_ranked.png 113K · 07_arrival_order.png 110K · hero-data.js 107K · 09_size_vs_lowcarbon.png 105K · storage_fig3_duration_value.png 103K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| 07_arrival_order.png | 1470×810 | 180 | 168 | 360 | 110 | 23 | thumbnail render (≤360 px) + lazy |
| 02_demand_distribution.png | 1425×780 | 180 | 168 | 360 | 42 | 9 | thumbnail render (≤360 px) + lazy |
| 09_size_vs_lowcarbon.png | 1425×840 | 180 | 168 | 360 | 105 | 22 | thumbnail render (≤360 px) + lazy |
| 04_inertia_by_type.png | 1425×810 | 180 | 168 | 360 | 55 | 12 | thumbnail render (≤360 px) + lazy |
| 05_link_structure.png | 1425×810 | 180 | 168 | 360 | 65 | 14 | thumbnail render (≤360 px) + lazy |
| 06_scenario_reach.png | 1470×810 | 180 | 168 | 360 | 55 | 12 | thumbnail render (≤360 px) + lazy |
| energy_model_chart.png | 2019×1306 | 1140 | 350 | 2019 | 219 | 132 | recompress (palette PNG/WebP) + lazy |
| heat_fig1_breakeven_price.png | 1350×810 | 502 | 308 | 1004 | 77 | 25 | thumbnail render (≤1000 px wide) + lazy |
| storage_fig3_duration_value.png | 1725×900 | 502 | 308 | 1004 | 103 | 22 | thumbnail render (≤1000 px wide) + lazy |
| climate_chain_tomato.png | 1870×833 | 1082 | 308 | 1870 | 116 | 70 | thumbnail render (≤1000 px wide) + lazy |
| skyline_spectrum_poster.png | 1920×1080 | 309 | 308 | 618 | 80 | 17 | thumbnail render (≤1000 px wide) + lazy |
| lq_ranked.png | 1350×1320 | 309 | 308 | 618 | 113 | 24 | thumbnail render (≤1000 px wide) + lazy |
| desktop_spines_poster.png | 1920×1080 | 309 | 308 | 618 | 90 | 19 | thumbnail render (≤1000 px wide) + lazy |

Image bytes now 1231 KB; estimated after resize + recompression 399 KB.

CDN JS: 118 KB (https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js). three.js for the GL hero; the 2D hero already works without it — a decision for the chosen option, not a weight fix.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### atlas.html — 257 KB loaded (202 KB with motion off)

Largest requests: atlas_layers.png 138K · cdn:npm/force-graph@1.51.4/dist/force-graph.min.js 56K · style.css 29K · atlas.html 15K · force-bg.js 7K · force-graph-data.js 7K · lightbox.js 4K · motion.js 2K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| atlas_layers.png | 1824×1104 | 1140 | 350 | 1824 | 138 | 83 | recompress (palette PNG/WebP) + lazy |

Image bytes now 138 KB; estimated after resize + recompression 83 KB.

CDN JS: 56 KB (https://cdn.jsdelivr.net/npm/force-graph@1.51.4/dist/force-graph.min.js). force-graph for the background graph; if the chosen option drops the graph this goes with it.

### model.html — 562 KB loaded (507 KB with motion off)

Largest requests: energy_model_throughlines.png 381K · model_propagation_step.png 62K · cdn:npm/force-graph@1.51.4/dist/force-graph.min.js 56K · style.css 29K · model.html 14K · force-bg.js 7K · force-graph-data.js 7K · lightbox.js 4K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| model_propagation_step.png | 1680×690 | 1140 | 350 | 1680 | 62 | 37 | recompress (palette PNG/WebP) + lazy |
| energy_model_throughlines.png | 1870×2261 | 1140 | 350 | 1870 | 381 | 229 | recompress (palette PNG/WebP) + lazy |

Image bytes now 443 KB; estimated after resize + recompression 266 KB.

CDN JS: 56 KB (https://cdn.jsdelivr.net/npm/force-graph@1.51.4/dist/force-graph.min.js). force-graph for the background graph; if the chosen option drops the graph this goes with it.

### library.html — 981 KB loaded (981 KB with motion off)

Largest requests: 14_space_layer.png 133K · 07_arrival_order.png 110K · 09_size_vs_lowcarbon.png 105K · 11_climate_record.png 99K · 08_response_curve.png 72K · 13_provenance.png 68K · 10_capacity_by_fuel.png 67K · 05_link_structure.png 65K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| 02_demand_distribution.png | 1425×780 | 1082 | 308 | 1425 | 42 | 25 | thumbnail render (≤1000 px wide) + lazy |
| 04_inertia_by_type.png | 1425×810 | 1082 | 308 | 1425 | 55 | 33 | thumbnail render (≤1000 px wide) + lazy |
| 05_link_structure.png | 1425×810 | 1082 | 308 | 1425 | 65 | 39 | thumbnail render (≤1000 px wide) + lazy |
| 06_scenario_reach.png | 1470×810 | 1082 | 308 | 1470 | 55 | 33 | thumbnail render (≤1000 px wide) + lazy |
| 07_arrival_order.png | 1470×810 | 1082 | 308 | 1470 | 110 | 66 | thumbnail render (≤1000 px wide) + lazy |
| 08_response_curve.png | 1470×810 | 1082 | 308 | 1470 | 72 | 43 | thumbnail render (≤1000 px wide) + lazy |
| 09_size_vs_lowcarbon.png | 1425×840 | 1082 | 308 | 1425 | 105 | 63 | thumbnail render (≤1000 px wide) + lazy |
| 10_capacity_by_fuel.png | 1425×840 | 1082 | 308 | 1425 | 67 | 40 | thumbnail render (≤1000 px wide) + lazy |
| 11_climate_record.png | 1425×930 | 1082 | 308 | 1425 | 99 | 59 | thumbnail render (≤1000 px wide) + lazy |
| 12_recorded_events.png | 1425×780 | 1082 | 308 | 1425 | 33 | 20 | thumbnail render (≤1000 px wide) + lazy |
| 14_space_layer.png | 1650×735 | 1082 | 308 | 1650 | 133 | 80 | thumbnail render (≤1000 px wide) + lazy |
| 13_provenance.png | 1650×840 | 1082 | 308 | 1650 | 68 | 41 | thumbnail render (≤1000 px wide) + lazy |

Image bytes now 903 KB; estimated after resize + recompression 542 KB.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### code.html — 40 KB loaded (40 KB with motion off)

Largest requests: style.css 29K · code.html 5K · lightbox.js 4K · motion.js 2K

No images.

### heat.html — 736 KB loaded (552 KB with motion off)

Largest requests: heat_breakeven.mp4 185K · heat_breakeven_poster.png 135K · heat_fig5_emissions_parity.png 81K · heat_fig1_breakeven_price.png 77K · heat_fig3_costgap_contour.png 69K · heat_fig4_tornado.png 61K · heat_fig2_lcoh_stacked.png 52K · style.css 29K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| heat_fig2_lcoh_stacked.png | 1050×825 | 1140 | 350 | 1050 | 52 | 31 | upscaled: regenerate at ≥ rendered width |
| heat_fig1_breakeven_price.png | 1350×810 | 1140 | 350 | 1350 | 77 | 46 | recompress (palette PNG/WebP) + lazy |
| heat_fig3_costgap_contour.png | 1200×900 | 1140 | 350 | 1200 | 69 | 42 | recompress (palette PNG/WebP) + lazy |
| heat_fig4_tornado.png | 1350×825 | 1140 | 350 | 1350 | 61 | 37 | recompress (palette PNG/WebP) + lazy |
| heat_fig5_emissions_parity.png | 1200×825 | 1140 | 350 | 1200 | 81 | 49 | recompress (palette PNG/WebP) + lazy |

Image bytes now 476 KB; estimated after resize + recompression 340 KB.

Video: assets/heat_breakeven.mp4?v=b65a7d4b — loaded only with motion on (185 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### storage.html — 912 KB loaded (696 KB with motion off)

Largest requests: storage_duration.mp4 216K · storage_fig2_dispatch_week.png 155K · storage_duration_poster.png 142K · storage_fig3_duration_value.png 103K · storage_fig1_prices.png 94K · storage_fig4_sensitivity.png 93K · storage_fig5_monthly.png 34K · style.css 29K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| storage_fig3_duration_value.png | 1725×900 | 1140 | 350 | 1725 | 103 | 62 | recompress (palette PNG/WebP) + lazy |
| storage_fig2_dispatch_week.png | 1650×975 | 1140 | 350 | 1650 | 155 | 93 | recompress (palette PNG/WebP) + lazy |
| storage_fig5_monthly.png | 1275×750 | 1140 | 350 | 1275 | 34 | 20 | recompress (palette PNG/WebP) + lazy |
| storage_fig4_sensitivity.png | 1275×825 | 1140 | 350 | 1275 | 93 | 56 | recompress (palette PNG/WebP) + lazy |
| storage_fig1_prices.png | 1950×720 | 1140 | 350 | 1950 | 94 | 56 | recompress (palette PNG/WebP) + lazy |

Image bytes now 622 KB; estimated after resize + recompression 430 KB.

Video: assets/storage_duration.mp4?v=de7cbd29 — loaded only with motion on (216 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### climate-cost.html — 579 KB loaded (324 KB with motion off)

Largest requests: climate_allocation.mp4 255K · climate_allocation_poster.png 127K · climate_chain_tomato.png 116K · style.css 29K · margin-scene.js 28K · climate-cost.html 16K · lightbox.js 4K · motion.js 2K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| climate_chain_tomato.png | 1870×833 | 1140 | 350 | 1870 | 116 | 70 | recompress (palette PNG/WebP) + lazy |

Image bytes now 244 KB; estimated after resize + recompression 197 KB.

Video: assets/climate_allocation.mp4?v=a2ffe294 — loaded only with motion on (255 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### longevity.html — 1294 KB loaded (1106 KB with motion off)

Largest requests: lq_allometry.png 237K · lq_orders.png 231K · longevity_quotient.mp4 189K · lq_explained.png 172K · longevity_quotient_poster.png 130K · lq_ranked.png 113K · lq_wild_captive.png 95K · biome-scene.js 30K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| lq_explained.png | 2108×1394 | 1140 | 350 | 2108 | 172 | 103 | recompress (palette PNG/WebP) + lazy |
| lq_allometry.png | 1425×990 | 1140 | 350 | 1425 | 237 | 142 | recompress (palette PNG/WebP) + lazy |
| lq_ranked.png | 1350×1320 | 1140 | 350 | 1350 | 113 | 68 | recompress (palette PNG/WebP) + lazy |
| lq_orders.png | 1950×1638 | 1140 | 350 | 1950 | 231 | 138 | recompress (palette PNG/WebP) + lazy |
| lq_wild_captive.png | 1350×1170 | 1140 | 350 | 1350 | 95 | 57 | recompress (palette PNG/WebP) + lazy |

Image bytes now 977 KB; estimated after resize + recompression 638 KB.

Video: assets/longevity_quotient.mp4?v=aff98c8e — loaded only with motion on (189 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 30 KB (margin/biome scene) — decided by the chosen option.

### skyline.html — 404 KB loaded (155 KB with motion off)

Largest requests: skyline_spectrum.mp4 250K · skyline_spectrum_poster.png 80K · style.css 29K · margin-scene.js 28K · skyline.html 10K · lightbox.js 4K · motion.js 2K · bgloop.js 1K

No images.

Video: assets/skyline_spectrum.mp4?v=4e10e985 — loaded only with motion on (250 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

### desktop.html — 921 KB loaded (532 KB with motion off)

Largest requests: desktop_spines.mp4 389K · bookshelf-demo-covers.webp 260K · bookshelf-demo-shelf.webp 108K · desktop_spines_poster.png 90K · style.css 29K · margin-scene.js 28K · desktop.html 10K · lightbox.js 4K

| image | natural | rendered 1440 | rendered 390 | needed (2×) | KB now | KB est. | fix |
|---|---|---|---|---|---|---|---|
| bookshelf-demo-shelf.webp | 2200×1280 | 1140 | 350 | 2200 | 108 | 108 | recompress (palette PNG/WebP) + lazy |
| bookshelf-demo-covers.webp | 2200×1280 | 1140 | 350 | 2200 | 260 | 260 | recompress (palette PNG/WebP) + lazy |

Image bytes now 458 KB; estimated after resize + recompression 458 KB.

Video: assets/desktop_spines.mp4?v=c1e586f5 — loaded only with motion on (389 KB); the poster (≈80–142 KB PNG) is loaded either way and is itself a 1920×1080 PNG rendered at 1140 px. Fix: poster as WebP at 1200–1400 px (est. 25–40 KB); consider `preload="none"` plus a play affordance instead of autoplay so the MP4 is fetched on intent rather than on scroll.

Scene script: 28 KB (margin/biome scene) — decided by the chosen option.

## The fixes, in order of bytes saved per hour of work

1. **Thumbnail renders for the home page** (mosaic ×6 at ≤360 px, card images ×6 at ≤1000 px). Saves ~600 KB on index.html alone; one resize step in `sync_assets.py` (Pillow, `Image.thumbnail`, palette PNG or WebP q85), new filenames so the full-size figures are untouched, `bust_cache.py` stamps them. Nothing regenerated.
2. **`loading="lazy"` on every `<img>` and `<video>` below the first figure** on every page. Zero bytes on disk; the phone stops fetching 10 figures it has not scrolled to. Only index.html has it today.
3. **Recompress the figure PNGs** (palette-quantise to 8-bit where the figure has < 256 colours, which is every matplotlib figure here; or WebP lossless/q90). Typical 40–60% saving with no visible change; `lq_allometry.png` 237 KB and `energy_model_throughlines.png` 381 KB are the two to test first. Add a `--optimise` step to each builder's save, or a one-off pass in `sync_assets.py`.
4. **Posters as WebP at 1200–1400 px.** Six posters, 80–142 KB each as 1920×1080 PNG, rendered at ≤1140 px. ~500 KB across the six pages.
5. **Regenerate the oversize figures at rendered geometry.** `lq_explained` (2108 px), `lq_orders` (1950), `storage_fig1_prices` (1950), `energy_model_chart` (2019), `energy_model_throughlines` (1870×2261), `climate_chain_tomato` (1870), `atlas_layers` (1824) all exceed 2× their 1140 px slot by less than 2×, so the saving is modest (10–25%) — worth doing only when those builders are next touched. Note the 2026-08-30 rule: `on_screen_px = pt * 1140 / (72 * figsize_in)`; dpi does not help legibility and only adds bytes.
6. **`srcset` for the phone.** A 700 px variant of each wide figure (2× of the 350 px phone column) would cut phone image bytes by ~75%, but the figures are already illegible at 350 px (audit F4); a phone-specific render with larger type is the honest fix and belongs with item 5, not here.
7. **`heat_fig2_lcoh_stacked.png`** is upscaled (1050 px into 1140). Regenerate at ≥1200 px next time `heat/model.py` runs.
8. **The six orphaned assets** (`dac_fig1/2/3/5`, `nitrogen_fixation`, `running_shoe`, ~1 MB) are shipped but never loaded; they cost the publish, not the reader. Decision pending from the revamp log.

What is *not* a weight problem: `style.css` (29 KB), the HTML (5–22 KB), `atlas-data.js` (9.8 MB, but only on the app page and it is the product). Self-hosting a typeface (Phase 2) adds 45–95 KB per first visit, cached across pages; it should be paid for by item 1 before it ships.
