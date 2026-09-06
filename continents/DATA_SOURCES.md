# Data sources

Every download is pinned by SHA-256 and recorded in `data/*_provenance.json`.
The build reads only committed files and never the network.

## Used

**MIDAS GNSS station velocities.** Nevada Geodetic Laboratory,
`geodesy.unr.edu/gps_timeseries/IGS20/midas/`. 21,910 stations, 5.5 MB, in
IGS20 — the IGS realisation of ITRF2020, which is what makes the comparison
with ITRF2020-PMM a comparison of models rather than of reference frames.
Columns are read from NGL's own `midas.readme.txt`, not reverse-engineered.
Slimmed to `data/stations.csv` (1.6 MB, committed, all 21,910 rows so the cut
to 14,404 is checkable). **No licence stated**; NGL asks for: Blewitt, G.,
Kreemer, C., Hammond, W.C. and Gazeaux, J. (2016), *Journal of Geophysical
Research: Solid Earth* 121(3), 2054-2068, doi:10.1002/2015JB012552.
NGL rebuilds `midasfile` weekly, so the pin records which snapshot the page
was built from rather than gating the build.

**ITRF2020-PMM.** `itrf.ign.fr/docs/solutions/itrf2020/`. Two files, 872 bytes
and 56 KB, committed verbatim: 13 plate rotation vectors in deg/Myr, and the
518 sites behind them with formal errors and post-fit residuals. The pole file
carries no uncertainties; those are in the paper's Table 1. **No licence
stated.** Altamimi, Z., et al. (2023), *Geophysical Research Letters* 50(24),
e2023GL106373, doi:10.1029/2023GL106373.

**PB2002 plate boundaries.** 241 segments, 6,292 vertices, 226 KB, committed
verbatim. **No licence stated**; cite Bird, P. (2003), *Geochemistry,
Geophysics, Geosystems* 4(3), 1027, doi:10.1029/2001GC000252.

**NNR-MORVEL56.** Argus, D.F., Gordon, R.G. and DeMets, C. (2011),
*Geochemistry, Geophysics, Geosystems* 12(11), Q11001,
doi:10.1029/2011GC003751. **Extracted from Table 1 of the paper**, because the
authors' own site no longer answers and the copy in the Internet Archive
publishes the table as a JPEG. All 25 MORVEL plates are cross-checked against
MintPy's independent transcription to 0.01 degrees and 0.001 deg/Myr. The
paper also carries the 95 per cent uncertainties, which that transcription
drops. **Not an open licence** — the MORVEL site's citation page: *"No
restrictions are placed on non-commercial uses of graphics or results from
this web site. The authors retain all commercial rights."*

**The four future scenarios.** OSF 8NEQ4, doi:10.17605/OSF.IO/8NEQ4,
**CC0 1.0**, stated in the paper's data availability section. 4.5 MB archive
holding 50 OTIS grids at 0.25 degrees; never extracted, packed to
`data/future_masks.npz` (0.7 MB, committed). Davies, H.S., Green, J.A.M. and
Duarte, J.C. (2020), *Earth System Dynamics* 11(1), 291-299,
doi:10.5194/esd-11-291-2020. The geometries themselves are from Davies et al.
(2018), *Global and Planetary Change* 169, 133-144,
doi:10.1016/j.gloplacha.2018.07.015. **The grids are a digitisation of maps
that were drawn**, not the output of a plate model; the deposit's read-me says
so. They carry a 2-degree artificial land mask at both poles for numerical
convergence, which this project excludes from every area statistic.

**Reconstructions.** GPlates Web Service, `gws.gplates.org`, 8 models named
explicitly in every request, 51 ages, 12 places, 335 responses cached in
`data/gplates_cache.json` (90 KB, committed). The service's default model is
documented as liable to change and named models' rotation files are updated in
place, so nothing here relies on a default. Each model is cited on the page.

**Reconstructed coastlines.** Same service, `/reconstruct/coastlines/`, for
three of the eight models at every age the viewer shows. These are each
model's own paleogeography, not modern outlines moved around: nothing the
viewer draws is today's world at any age but zero. A raw frame is about
2.4 MB and 100,000 points; each is unwrapped in longitude, unioned so the
per-plate pieces stop leaving slivers, clipped at the antimeridian, simplified
with topology preserved, and delta-encoded on a quarter-degree grid. The
result is `data/land.json`, and `site/assets/continents-land.js` is built from
it.

## Looked up, not recomputed

- Earth's land fraction, 29.2 per cent of the surface. Used as the external
  anchor for the scenario grids.
- MIDAS's stated accuracy, 0.23 mm/yr RMS horizontal on the stable North
  American interior (Blewitt et al. 2016).
- ITRF2020-PMM's fit, 0.25 mm/yr WRMS (Altamimi et al. 2023).
- MORVEL's averaging intervals: 0.78 Myr for ten spreading centres, 3.16 for
  seven, decades for the five or six plates carried on GPS (DeMets et al.
  2010).
- That palaeomagnetism cannot determine palaeolongitude (Müller et al. 2022).
- That uncertainty quantification for global plate models is an open problem
  (Seton et al. 2023).

## Considered and not used

**PB2002 plate and orogen polygons.** They would support one number, the share
of the surface in a diffuse deformation zone. Three of the plate polygons
cross the dateline in a way that breaks an equal-area shoelace, and the
resulting figure was never checked against Bird's own. A number that cannot be
checked is not put on the page.

**Müller et al. 2019 age grids**, 1.8 GB, and the EarthByte rotation models as
files, 8.7 MB to 481 MB. The web service reconstructs both the points and the
coastlines this project needs, from the same models, and the files would only
be needed to reconstruct geometry the service does not already serve.

**Scotese's PALEOMAP website imagery.** Its licence names websites among
prohibited commercial uses. The Pangaea Ultima geometry here is redrawn from
the CC0 grids instead, and no image is lifted.

**Coastlines for all eight models.** Three are shipped, not eight. Switching
among three already shows that the models disagree about where the land was;
eight would be six megabytes to make the same point, and the dots carry the
full eight-model disagreement for the place the reader picked.

**Open Food Facts-style crowdsourced sets** have no analogue here; there is no
crowdsourced plate model.
