# Research and feasibility: how will the continents shift?

Stage 1 of `00 PUBLISH/prompts/NEW_PROJECTS.md` section 4. Written 5 September
2026. Lives in `03 RESEARCH/continents/` with every download and script used
below. Nothing in `00 PUBLISH` was touched. No design decisions are made here.

Nine checks were run against real data rather than cited: `plate_check.py`,
`rigidity_check.py`, `outlier_check.py`, `crosscheck.py`, `itrf_compare.py` and
`geologic_vs_geodetic.py` for the present; `model_spread.py` for the past;
`otis_grid.py` and `future_spread.py` for the future.

## 1. Verdict

**The project exists, and the brief's proposed structure is the right one.**
Three regimes with three epistemic statuses is not a framing device: each
status is a number, each number comes from a public file, and all three were
measured today.

Supportable claim, one sentence: *Plate motion is measured to a fraction of a
millimetre a year and the plates are rigid to that same fraction, but the three
things a reader wants from that fact have three different standings — the
present is settled, the reconstructed past degrades from a few hundred
kilometres of model disagreement at 10 million years to more than ten thousand
at 500 million, and the future is four named scenarios whose own authors call
them a thought experiment and which disagree about the land-or-ocean status of
up to 47 per cent of the Earth's surface.*

Three corrections to the brief as written:

- **"Extrapolable" is the weak word.** Running present-day poles forward is
  arithmetic, not prediction. The naive extrapolation is worth computing
  precisely so it can be taken away (section 8).
- **The future scenarios are not competing predictions and should not be drawn
  as if they were.** They are four end-members of a spectrum, in the words of
  the paper that built all four. One of the four has no peer-reviewed primary
  source at all; it was devised for a television series.
- **"Deep-future projections exist as a small number of named competing
  scenarios" understates the position in one way and overstates it in
  another.** The geometry is freely available under CC0, which is better than
  the brief assumes. But all four geometries were built by one three-author
  group in one 2018 paper, so they are not four independent lines of evidence.

Not supportable: any statement of where a named place will be in 200 million
years, at any confidence. Also not supportable from published sources: a formal
uncertainty on any past reconstruction, because the field's own leading review
names uncertainty quantification as an open problem.

## 2. The primary literature

### The measured present

**Blewitt, G., Kreemer, C., Hammond, W.C., Gazeaux, J. (2016).** MIDAS robust
trend estimator for accurate GPS station velocities without step detection.
*Journal of Geophysical Research: Solid Earth* 121(3), 2054-2068,
doi:10.1002/2015JB012552. CC BY-NC-ND 4.0. The estimator behind every velocity
used here. Stated accuracy, verbatim: *"Statistical tests using GPS data in the
rigid North American plate interior show plus or minus 0.23 mm/yr
root-mean-square (RMS) accuracy in horizontal velocity."* Blind tests on
synthetic data give 0.33 mm/yr horizontal, 1.1 mm/yr vertical.

**Altamimi, Z., Metivier, L., Rebischung, P., Collilieux, X., Chanard, K.,
Barneoud, J. (2023).** ITRF2020 Plate Motion Model. *Geophysical Research
Letters* 50(24), e2023GL106373, doi:10.1029/2023GL106373. 13 plates, 518 sites.
Verbatim: *"The overall precision with which the ITRF2020 velocity field is
represented by the rigid ITRF2020-PMM is at the level of 0.25 mm/yr WRMS."*

**Altamimi, Z., Metivier, L., Rebischung, P., Rouby, H., Collilieux, X.
(2017).** ITRF2014 plate motion model. *Geophysical Journal International*
209(3), 1906-1912, doi:10.1093/gji/ggx136. 11 plates, 297 sites after the
rejection of 21. **Equations 1 and 2 of this paper are the citation for the
Euler-pole-to-surface-velocity formula.** Neither MORVEL nor Argus et al. 2011
states it; MORVEL contains only two numbered equations and neither is this one.

**DeMets, C., Gordon, R.G., Argus, D.F. (2010).** Geologically current plate
motions. *Geophysical Journal International* 181(1), 1-80,
doi:10.1111/j.1365-246X.2009.04491.x. MORVEL: 25 plates, 97 per cent of the
surface, 2203 data. The averaging interval is **not** a single number — ten of
seventeen spreading centres are averaged over 0.78 Myr, seven over 3.16 Myr,
and five or six plates rest on GPS alone. Section 7.4.2, verbatim: *"The rms
difference between the MORVEL and GPS plate motion estimates is 2.9 mm yr-1."*
Section 7.4.3 documents boundaries that have slowed within the last few million
years; section 5 below reproduces three of them independently.

**Argus, D.F., Gordon, R.G., DeMets, C. (2011).** Geologically current motion
of 56 plates relative to the no-net-rotation reference frame. *Geochemistry,
Geophysics, Geosystems* 12(11), Q11001, doi:10.1029/2011GC003751.
NNR-MORVEL56. Section 4.3, verbatim: *"The velocity of Earth's surface differs
between NNR-MORVEL56 and NNR-GSRM-2 by an RMS velocity of 7.2 mm a-1, but the
RMS velocity difference for the part of Earth's surface covered by the 27
plates in common is smaller, 3.2 mm a-1."* The per-plate spread runs 1 to
16 mm/yr.

**Kreemer, C., Blewitt, G., Klein, E.C. (2014).** A geodetic plate motion and
Global Strain Rate Model. *Geochemistry, Geophysics, Geosystems* 15(10),
3849-3889, doi:10.1002/2014GC005407. GSRM v2.1: 50 plates, 22,511 velocities.
Verbatim: *"About 14% of the Earth is allowed to deform in 145,086 deforming
grid cells."* That 14 per cent is the same fact section 4 measures from the
other direction.

**Bird, P. (2003).** An updated digital model of plate boundaries.
*Geochemistry, Geophysics, Geosystems* 4(3), 1027, doi:10.1029/2001GC000252.
PB2002: 52 plates and 13 orogens. The boundary geometry every distance
calculation below uses.

### The reconstructed past

**Merdith, A.S., Williams, S.E., Collins, A.S., Tetley, M.G., Mulder, J.A.,
Blades, M.L., Young, A., Armistead, S.E., Cannon, J., Zahirovic, S., Muller,
R.D. (2021).** Extending full-plate tectonic models into deep time.
*Earth-Science Reviews* 214, 103477, doi:10.1016/j.earscirev.2020.103477.
1000-0 Ma, palaeomagnetic frame. The deposit's own read-me warns: *"if you want
to analyse the Pacific Ocean, including hotspot motion, Hawaiian-Emperor Bend
kinematics etc. you should not use this model."*

**Muller, R.D., Flament, N., Cannon, J., Tetley, M.G., Williams, S.E., Cao, X.,
Bodur, O.F., Zahirovic, S., Merdith, A. (2022).** A tectonic-rules-based mantle
reference frame since 1 billion years ago. *Solid Earth* 13(7), 1127-1159,
doi:10.5194/se-13-1127-2022. CC BY 4.0. **Solid Earth, not Earth-Science
Reviews**, which is how it is often miscited. States the central limitation
plainly: *"since the Earth's magnetic dipole field is radially symmetric,
paleo-longitudinal information cannot be determined from paleomagnetic data
alone."*

**Muller, R.D., Zahirovic, S., Williams, S.E., Cannon, J., Seton, M., et al.
(2019).** A Global Plate Model Including Lithospheric Deformation Along Major
Rifts and Orogens Since the Triassic. *Tectonics* 38(6), 1884-1907,
doi:10.1029/2018TC005462. 250-0 Ma. The only widely used model with deforming
networks rather than rigid blocks.

**Buffan, L., Jones, L.A., Domeier, M., Scotese, C.R., Zahirovic, S., Varela,
S. (2023).** Mind the uncertainty: Global plate model choice impacts deep-time
palaeobiological studies. *Methods in Ecology and Evolution* 14, 3007-3019,
doi:10.1111/2041-210X.14204. **The paper the second regime rests on.** Five
models on a 100 km hexagonal grid: cells disagreeing by more than 5 degrees of
palaeolatitude are 1.9 per cent in the Cenozoic, 14.8 per cent in the Mesozoic,
53.8 per cent in the Palaeozoic, about 76 per cent in the Cambrian. Section 6
reproduces the shape of this independently.

**van Hinsbergen, D.J.J., et al. (2015).** *PLoS ONE* 10(6), e0126946,
doi:10.1371/journal.pone.0126946. Reference-frame choice alone *"may introduce
errors in paleolatitude of more than 15 degrees (>1500 km)"* in the early
Cenozoic and *"more than 20 degrees (>2200 km)"* in the Mesozoic.

**Seton, M., et al. (2023).** *Nature Reviews Earth and Environment* 4,
185-204, doi:10.1038/s43017-022-00384-8. The field's own review names
*quantification of uncertainty* and *intercomparisons between models* as still
open problems. **This is the citation for why no reconstruction on the page can
carry a formal error bar.**

Also: Torsvik et al. 2012, *Earth-Science Reviews* 114, 325-368 —
palaeolongitude is not constrained, and the "quasi-stationary African
assumption" used in its place is conceded to be *"somewhat arbitrary"*. Vaes
and van Hinsbergen 2025, *AGU Advances* 6, e2024AV001515 — true polar wander
over 320-0 Ma at 0.34 plus or minus 0.14 deg/Myr, and a retraction of a
Torsvik 2012 headline rate as *"the result of temporal bias"*. Doubrovine et
al. 2012, *JGR* 117, B09101 — hotspot-frame RMS misfit rising from about
130 km at 10-40 Ma to 708 km at 80 Ma, and the Pacific plate circuit breaking
entirely before 83.5 Ma.

### The projected future

**Davies, H.S., Green, J.A.M., Duarte, J.C. (2018).** Back to the future:
Testing different scenarios for the next supercontinent gathering. *Global and
Planetary Change* 169, 133-144, doi:10.1016/j.gloplacha.2018.07.015. **This one
paper built all four geometries**, in GPlates, in a deliberately standardised
way. Its own abstract: *"these modes should be treated as end-members of a
spectrum of possibilities."*

**Davies, H.S., Green, J.A.M., Duarte, J.C. (2020).** Back to the future II:
tidal evolution of four supercontinent scenarios. *Earth System Dynamics*
11(1), 291-299, doi:10.5194/esd-11-291-2020. CC BY 4.0. The paper the CC0 grids
belong to.

The four scenarios, with what each actually rests on:

| Scenario | Primary source | Assembly | Mechanism |
|---|---|---|---|
| Pangaea Proxima, formerly Ultima | Scotese, C.R. and van der Pluijm, B.A. 2020, *Earth and Space Science* 7(11), e2019EA000989, doi:10.1029/2019EA000989, section 11 and figure 12 | +250 Myr | introversion, the Atlantic closes |
| Novopangaea | **none** | +200 Myr | extroversion, the Pacific closes |
| Aurica | Duarte, J.C., Schellart, W.P., Rosas, F.M. 2018, *Geological Magazine* 155(1), 45-58, doi:10.1017/S0016756816000716 | +250 Myr | both close, a new ocean opens across Asia |
| Amasia | Mitchell, R.N., Kilian, T.M., Evans, D.A.D. 2012, *Nature* 482(7384), 208-211, doi:10.1038/nature10800 | **no date given in the paper** | orthoversion, 90 degrees from the predecessor, the Arctic closes |

Two of these need flagging on any page that uses them.

**Novopangaea has no peer-reviewed primary source.** Roy Livermore devised it
in the late 1990s for the BBC series *The Future Is Wild*. Its first print
appearance is Nield, T. (2007), *Supercontinent*, Granta, whose opening chapter
is titled "Novopangaea — a science fiction". Livermore's own 2018 book cites
Nield rather than any work of his own. His remark on it, in *New Scientist*
2007: *"The beauty of all this is that no one will ever be able to prove me
wrong."*

**Mitchell et al. 2012 gives no assembly date.** The paper predicts a
*location* — 90 degrees from the predecessor's centre, measured at 88 and 87
degrees for the two previous transitions — and not a time. The widely quoted
"50 to 200 million years" comes from the press release. Davies et al. adopt
+200 Myr for modelling convenience.

Downstream users, each of which takes one or two scenarios and says so:
Farnsworth et al. 2023, *Nature Geoscience* 16(10), 901-908,
doi:10.1038/s41561-023-01259-3, CC BY 4.0, uses Pangaea Ultima only — *"PU is
only one of four potential configurations"*. Way et al. 2021, *Geochemistry,
Geophysics, Geosystems* 22(8), e2021GC009983, doi:10.1029/2021GC009983, uses
Aurica and Amasia only, and calls them *"two plausible scenarios"*.

## 3. The primary data

All free, none requiring a key or a login. Sizes are what was actually
downloaded today.

| Source | What it is | Size | Licence |
|---|---|---|---|
| NGL MIDAS IGS20 `midasfile` | 21,910 GNSS stations, velocity and uncertainty, IGS20 frame, updated 2026-09-04 | 5.5 MB | none stated; cite Blewitt et al. 2016 |
| NGL `platevel.all` | station-to-plate assignment plus NGL's own model velocity | 1.6 MB | as above |
| `ITRF2020-PMM.dat` | 13 geodetic Euler poles, deg/Myr, **no uncertainties** | 872 B | none stated |
| `ITRF2020-PMM-residuals.dat` | the 518 sites behind it, with sigmas and post-fit residuals | 56 KB | none stated |
| GSRM v2.1 `poles.NNR` | 50 plates, lat/lon/rate, no uncertainties | 1.8 KB | none stated |
| MintPy `euler_pole.py` | NNR-MORVEL56 (56), GSRM v2.1 (50), ITRF2014-PMM (11) as Python dicts | 769 lines | BSD |
| PB2002 boundaries | 241 segments, 6,292 vertices, as GeoJSON and as Bird's own `.dig` | 226 KB / 188 KB | see below |
| PB2002 plates and orogens | 52 plates, 13 diffuse deformation zones | 328 KB / small | see below |
| GPlates Web Service | 15 named rotation models; reconstruct points, coastlines, topologies | API | per model |
| OSF 8NEQ4 `Grid files.zip` | **all four future scenarios**, 0.25 deg, 20 Myr steps, land mask and bathymetry | 4.5 MB | **CC0 1.0** |
| EarthByte Zenodo rotation models | Merdith 2021 (8.7 MB), Muller 2019 (481 MB), Muller 2022, Seton 2012, PALEOMAP 2016 | varies | CC BY 4.0 |

**Licences are the weak spot and need stating on the page.**

- **NNR-MORVEL56 and MORVEL are not openly licensed.** The project's own
  citation page: *"No restrictions are placed on non-commercial uses... The
  authors retain all commercial rights."*
- **GSRM, NGL MIDAS and the ITRF products state no licence at all.** They ask
  for a citation. This is the same position as Torsvik and Cocks' CEED6, which
  is downloadable and carries only a copyright line.
- **Scotese's website material is restricted** by a bespoke non-commercial
  licence that names *"web sites on the Internet"* among prohibited commercial
  uses. Do not lift images from `scotese.com`. The 2020 *Earth and Space
  Science* figure is the open alternative, though its licence metadata
  conflicts: Crossref and Semantic Scholar say CC BY 4.0, Unpaywall and
  OpenAlex say CC BY-NC-ND.
- **OSF 8NEQ4 is CC0**, confirmed two ways: the OSF licence API returns
  "CC0 1.0 Universal", and the paper's data availability statement reads *"The
  data is freely available to use according to the CC0 1.0 license."* The
  cleanest licence in the subject belongs to its least certain data.
- **The MORVEL host is dead.** `www.geology.wisc.edu` resolves but refuses
  connections; `geoscience.wisc.edu/~chuck/MORVEL/` is a 404. Both were
  confirmed here. Its calculators were server-side PHP and are unrecoverable,
  and the NNR-MORVEL56 pole table at source is a **JPEG**. The usable
  machine-readable copy is MintPy's transcription.

Not obtainable: **any GPlates-native rotation file for the future.** The
GPlates forum, the EarthByte collections, Zenodo, figshare, PANGAEA, Dryad and
GitHub all return nothing. A future shapefile did once exist as a 99-dollar
Scotese product; the order page now reads "NO Longer Available". Also not
obtainable: a formal uncertainty on any global reconstruction, because none is
published.

## 4. Feasibility, regime one: the measured present

Cuts: time series at least 5 years, east and north velocity uncertainty at most
0.5 mm/yr. That takes 21,910 stations to 14,404, of which 14,390 carry a plate
code, across 18 plates. Column meanings come from NGL's own `midas.readme.txt`,
saved here as `midas_format.txt`, not reverse-engineered.

`plate_check.py` fits one Euler vector per plate by weighted least squares and
reports the residual. It runs from 0.86 mm/yr RMS on Africa to 24 mm/yr on
Sunda. That spread is not plates behaving differently; it is how much of each
plate's network sits in a boundary zone. Pooling all 18 and binning by distance
to the nearest PB2002 boundary:

| distance to boundary | stations | median residual | 90th |
|---|---|---|---|
| 0-100 km | 1,747 | 9.11 mm/yr | 21.86 |
| 100-250 km | 1,675 | 9.08 | 24.82 |
| 250-500 km | 1,676 | 3.35 | 9.84 |
| 500-1,000 km | 1,977 | 0.98 | 3.30 |
| 1,000-2,000 km | 4,980 | 0.62 | 2.13 |
| over 2,000 km | 2,311 | 0.62 | 1.76 |

Refit on stations more than 500 km from a boundary and plate interiors come out
at a median 0.34 to 0.64 mm/yr against a single rigid rotation. Africa: 100
stations, median 0.34, RMS 0.75. Australia: 624 stations, median 0.34,
RMS 0.91.

**This is the strongest single result available to the project.** A tectonic
plate really is a rigid body, to a third of a millimetre a year, across
thousands of kilometres, and everything that happens happens in belts a few
hundred kilometres wide.

### The exception is a trap, not a finding

The Pacific fits at 21.7 mm/yr RMS. `outlier_check.py` takes it apart. Of its
79 stations more than 500 km from a boundary, 46 are on Hawaii and 33 of those
on the Big Island, where Kilauea's south flank moves independently of the
plate. Four more of the worst residuals are above 50 degrees north in western
Alaska, which NGL files under PA but which sits on the Bering block.

| group | n | pole lat | pole lon | deg/Myr | median | RMS |
|---|---|---|---|---|---|---|
| Hawaii, all | 46 | -62.38 | 115.90 | 0.659 | 1.91 | 6.30 |
| Big Island only | 33 | 2.90 | -164.51 | 1.937 | 2.44 | 7.22 |
| Kauai, Oahu, Maui | 13 | -63.19 | 99.48 | 0.706 | **0.21** | **0.58** |

Thirteen stations on three quiet islands fit one rotation to a median
0.21 mm/yr. The Big Island alone returns a pole at 2.9 N turning at
1.94 deg/Myr, which is not a plate, it is a volcano. **Stage 3 needs a test for
this**: a station's velocity is not evidence about a plate until you know the
station is not on something moving for its own reasons.

### It agrees with the official model

`itrf_compare.py` compares the fitted far-field rotations against ITRF2020-PMM,
estimated independently from 518 selected sites. Frames are compatible: MIDAS
IGS20 sits in IGS20, the IGS realisation of ITRF2020.

| plate | n | fitted here | ITRF2020-PMM | v diff | obs vs ITRF |
|---|---|---|---|---|---|
| NA | 4,569 | -6.12, -87.60, 0.191 | -8.35, -86.10, 0.187 | 0.58 | 0.94 |
| EU | 3,447 | 56.87, -96.05, 0.267 | 55.05, -99.33, 0.255 | 0.47 | 0.62 |
| AU | 624 | 32.40, 38.17, 0.629 | 32.83, 38.31, 0.627 | 0.60 | 0.71 |
| SA | 286 | -19.41, -136.15, 0.115 | -22.26, -132.76, 0.115 | 0.44 | 0.77 |
| AF | 100 | 49.90, -81.35, 0.266 | 50.45, -81.25, 0.258 | 0.82 | 0.89 |
| AN | 87 | 59.17, -129.29, 0.215 | 58.73, -130.74, 0.220 | 0.59 | 0.88 |
| IN | 23 | 51.51, 0.52, 0.514 | 51.77, 0.67, 0.510 | 0.50 | 0.70 |
| SO | 44 | 48.96, -95.04, 0.316 | 50.07, -96.43, 0.313 | 0.89 | 1.35 |
| PA | 79 | -63.69, 101.52, 0.655 | -62.99, 111.59, 0.672 | 3.83 | 1.51 |

Poles are lat, lon, deg/Myr; the last two columns are median speed differences
in mm/yr at that plate's own far-field stations. Eight of nine agree to under
0.9 mm/yr. The Pacific's 3.83 is Kilauea again, in this fit and not in theirs.
`crosscheck.py` separately reproduces NGL's own model to 0.08-0.74 mm/yr, which
checks the arithmetic; the table above checks the science.

**"Measured" here means two independent international analyses of the same
physical quantity differ by well under a millimetre a year.** That is a number
the page can stand on. It is worth setting against the formal uncertainties:
ITRF2020's median per-site formal sigma is 0.085 mm/yr while the actual scatter
about the best rigid plate is 0.31 mm/yr RMS. Formal uncertainty understates
real error by a factor near four.

## 5. Feasibility, regime one and a half: geologic against geodetic

`geologic_vs_geodetic.py` compares NNR-MORVEL56, averaged over 0.78 to
3.16 Myr, against ITRF2020-PMM and against the MIDAS fit, averaged over
decades. Comparisons are on **relative** motion between plate pairs only,
because the models sit in different reference frames and only relative motion
is frame independent.

| boundary | pair | NNR-MORVEL56 | ITRF2020-PMM | MIDAS, here | geol minus geod |
|---|---|---|---|---|---|
| Peru-Chile trench | NZ-SA | 73.2 mm/yr, 075 | 66.1, 077 | - | **7.7** |
| San Andreas, central | PA-NA | 50.8, 324 | 48.2, 323 | 42.4, 321 | 2.9 |
| Himalaya | IN-EU | 45.0, 022 | 37.4, 015 | 36.7, 013 | **9.0** |
| Mid-Atlantic, south | NU-SA | 32.8, 078 | 30.6, 077 | 31.1, 076 | 2.2 |
| SE Indian ridge | AU-AN | 70.4, 016 | 72.9, 016 | 72.9, 016 | 2.4 |
| Zagros | AR-EU | 28.7, 009 | 21.3, 001 | - | **8.1** |
| East African rift | SM-NU | 4.6, 093 | 4.3, 087 | 3.7, 083 | 0.6 |

Speeds in mm/yr, azimuths in degrees clockwise from north.

This independently reproduces DeMets et al. 2010 section 7.4.3. India-Eurasia
is 9.0 mm/yr slower now than its few-million-year average; Nazca-South America
7.7 slower; Arabia-Eurasia 8.1 slower. The mid-ocean ridges and the East
African rift agree to about 2 mm/yr. **Some plate boundaries have measurably
slowed within the last few million years.** That is the single best empirical
argument against extrapolating today's poles, and it comes from two files
totalling under a megabyte.

The PA-NA figure from the MIDAS fit is 5.8 mm/yr below ITRF's, which is the
Kilauea contamination surfacing a third time. It is not a separate finding.

## 6. Feasibility, regime two: the reconstructed past

`model_spread.py` asks eight published global models where six present-day
cities were, at nine past ages, through the GPlates Web Service, and measures
the great-circle distance between every pair of answers. Models are named
explicitly, because the service's default is documented as liable to change and
named models' rotation files are updated in place. 65 requests, cached in
`model_spread.json`.

| age | models | max pairwise disagreement | median pairwise |
|---|---|---|---|
| 10 Ma | 8 | 393-601 km | 147-236 km |
| 30 Ma | 8 | 640-936 km | 294-374 km |
| 50 Ma | 8 | 1,107-1,362 km | 394-563 km |
| 100 Ma | 8 | 1,079-2,070 km | 568-992 km |
| 150 Ma | 8 | 1,636-2,592 km | 903-1,302 km |
| 200 Ma | 8 | 2,369-3,347 km | 751-1,820 km |
| 250 Ma | 7 | 787-1,352 km | 422-737 km |
| 400 Ma | 5-6 | 5,159-10,158 km | 2,823-6,143 km |
| 500 Ma | 4 | 10,060-15,713 km | 5,354-10,228 km |

Ranges are across the six cities. Three things here are each worth a figure.

**At 500 Ma the models put Nagpur's ground in places 15,713 km apart**, more
than a third of the way round the Earth. Denver, 10,346 km.

**At 400 and 500 Ma some models return no position at all** for Sydney: the
site has no plate id, meaning the model does not place any crust there. Three
of the four models covering 500 Ma do this, so Sydney drops out of that row
entirely. **The models do not merely disagree about where the ground was; they
disagree about whether it existed.** That is a better fact than the distances.

**The 250 Ma row is narrower than the 200 Ma row.** That is Pangaea: with
everything assembled there is less room to differ, and the spread reopens
behind it. The disagreement is not monotonic in time, and a figure that assumes
it is will be wrong.

This is the same shape Buffan et al. 2023 report from a global hexagonal grid,
arrived at here independently from six sites and a public API. Their paper
carries a caveat this check inherits: the models share ancestry, so the true
spread of admissible reconstructions is **wider** than the measured inter-model
spread, not narrower.

## 7. Feasibility, regime three: the projected future

The four scenarios are gridded at 0.25 degrees in 20 Myr steps in OSF 8NEQ4
under CC0: 50 files, 4.5 MB, `pun` Pangaea Ultima and `aurn` Aurica to 250 Myr,
`novon` Novopangaea and `amn` Amasia to 200 Myr. The format is OTIS binary,
big-endian, with a MATLAB reader shipped alongside; `otis_grid.py` is that
reader ported to Python in about forty lines. `hz` is depth, `mz` is the mask
with 0 for land.

**The files are not on a common longitude convention.** Pangaea Ultima and
Amasia run -180 to 180; Novopangaea and Aurica run 0 to 360. Read as they come,
two of the four scenarios sit 180 degrees wrong, and the four present-day grids
— which are all the same map of today's Earth — appear to disagree over 32 per
cent of the planet. Roll by half the width and they agree to 0.9 per cent. This
was hit here, and it is the second thing Stage 3 must have a test for.

The authors also state that *"the resulting maps were then given an artificial
land mask 2 degrees wide on both poles to allow for numerical convergence"*, so
everything poleward of 88 degrees is an artefact. Everything below drops it.

Share of the Earth's surface two scenarios disagree about, land against ocean,
area weighted:

| Myr | PU/Nov | PU/Aur | PU/Ama | Nov/Aur | Nov/Ama | Aur/Ama | max |
|---|---|---|---|---|---|---|---|
| 0 | 0.8 | 0.8 | 0.0 | 0.0 | 0.8 | 0.8 | 0.8 |
| 20 | 4.2 | 0.5 | 0.1 | 4.4 | 4.2 | 0.5 | 4.4 |
| 40 | 25.3 | 20.4 | 21.4 | 26.0 | 25.2 | 16.7 | 26.0 |
| 100 | 33.4 | 38.3 | 34.4 | 36.2 | 37.9 | 41.6 | 41.6 |
| 200 | 45.7 | 47.2 | 35.9 | 29.0 | 38.2 | 44.4 | **47.2** |

Land is under 30 per cent of the globe, so a 47 per cent surface disagreement
means the configurations are close to non-overlapping. **The scenarios are
indistinguishable for the first 20 million years and then diverge almost
completely.**

Where the land sits, at each scenario's final snapshot:

| scenario | Myr | land % | % in north | % within 30 deg | land above 60 N | land below 60 S |
|---|---|---|---|---|---|---|
| Pangaea Ultima | 250 | 27.4 | 65 | 59 | 2 | 1 |
| Novopangaea | 200 | 26.8 | 71 | 57 | 22 | 0 |
| Aurica | 250 | 27.2 | 60 | 69 | 2 | 0 |
| Amasia | 200 | 26.5 | 88 | 20 | 91 | 35 |
| today | 0 | 29.1 | 69 | 45 | 52 | 35 |

**Aurica and Amasia are a genuine either/or.** Aurica is an equatorial
supercontinent with 69 per cent of land in the tropics and both polar zones
open ocean. Amasia is a circumpolar northern landmass with 20 per cent of land
in the tropics, 91 per cent of the region above 60 N dry, and Antarctica left
where it is — the south polar zone is 36 per cent land against 35 per cent
today. Same planet, same 200 to 250 million years, opposite consequences for
albedo, ice and ocean circulation.

The centre-of-mass track in `future_spread.out` shows the same thing as motion:
the four land centroids start together and end in four different quadrants,
with the concentration measure rising from 0.36 today to 0.44 for Pangaea
Ultima, 0.47 Aurica, 0.54 Amasia and 0.62 Novopangaea.

**But none of this is a prediction, and the sources say so.** Evans, Li and
Murphy 2016: the configuration *"cannot be tested realistically"* and the
alternatives are *"a thought experiment"*. Scotese, to NASA in 2000: *"It's all
pretty much fantasy to start with. But it's a fun exercise to think about what
might happen."* Davies et al. 2018: *"end-members of a spectrum of
possibilities."* Davies et al. 2020 ranks none of the four above the others.

Nor are the four independent. All four geometries come from that one 2018
paper, deliberately standardised so they could be compared. Two of the
underlying scenarios have a peer-reviewed primary source, one has had one only
since 2020, and one has none.

## 8. Naive extrapolation, and why it is a strawman worth computing

Rotating each site about its own plate's present-day pole gives, as
great-circle displacement from the starting point, with arc length along the
small circle in brackets:

| site | speed | 10 Myr | 50 Myr | 100 Myr |
|---|---|---|---|---|
| Sydney | 57.3 mm/yr | 573 km | 2,855 (2,865) | 5,632 (5,730) |
| Nagpur | 52.5 | 525 | 2,620 (2,625) | 5,218 (5,250) |
| Kinshasa | 29.3 | 293 | 1,466 | 2,932 |
| Warsaw | 25.6 | 256 | 1,277 | 2,550 |
| Denver | 16.0 | 160 | 797 | 1,592 |
| Brasilia | 12.7 | 127 | 636 | 1,271 |

One millimetre a year is one kilometre per million years, exactly. That is the
only unit arithmetic a reader needs on this subject.

The rotation-versus-translation distinction is real but small: over 100 Myr
Sydney's path along its small circle is 5,730 km and its net displacement
5,632 km, under 2 per cent apart. **So the naive extrapolation is not wrong
because of geometry.** It is wrong because poles do not hold — section 5 shows
three boundaries that have changed speed within the last few million years —
because plates break and new boundaries form, and because none of that is in
the arithmetic. That is a far more interesting reason to reject it than "it is
a long time".

## 9. What a reader already believes, and what this adds

Already believed: the continents drift, Pangaea existed, and in 250 million
years there will be a new supercontinent called Pangaea Ultima. The last is
close to a folk fact and is the one worth taking apart.

1. **Plates are rigid to a third of a millimetre a year, and all the motion is
   in narrow belts.** Median residual 9.1 mm/yr within 250 km of a boundary,
   0.62 mm/yr beyond 1,000 km. Readers know continents move; they do not know
   the interiors do not deform at all at this precision, or that the whole
   deformation budget is spent in a few per cent of the surface.
2. **Some plate boundaries have measurably slowed in the last few million
   years.** India-Eurasia by 9 mm/yr against its geological average. Plate
   motion is not a constant, and this is measured rather than modelled.
3. **The reconstructed past has a disagreement you can put a number on, and it
   is not monotonic.** It narrows at Pangaea and explodes in the Palaeozoic. By
   500 Ma the models disagree about whether the ground under a city existed.
4. **Palaeolongitude is not uncertain, it is undetermined.** Palaeomagnetism
   cannot constrain it in principle, not merely in practice. Every deep-time
   map a reader has seen contains an east-west position that is an assumption.
   Best-case anchoring against plume generation zones is 3 to 13 degrees, and
   only where a datable large igneous province exists; before Pangaea there are
   three.
5. **The named futures are one paper's four end-members, not four predictions,
   and one of them was invented for television.** A reader who has heard of
   Pangaea Ultima has not heard that.

If the honest answer to "what does this add" were "nothing", it would be here.
It is not: points 2, 3 and 4 each run against what a well-read non-specialist
would say, and all three are measurable from public files.

## 10. Traps found

- **Any single future map presented as the answer.** The brief already says
  this. The data makes it worse than the brief assumes: the scenarios are
  indistinguishable for 20 Myr, then disagree about nearly half the planet.
- **Treating the four futures as independent.** One paper, one group, one
  standardisation. Drawing them side by side is right; implying four teams
  reached four conclusions is not.
- **The 0-360 versus -180-180 longitude split in the OSF grids.** Silent, and
  it puts two scenarios exactly wrong. Needs a test.
- **The 2-degree artificial polar land mask in the same grids.** Counting it
  inflates every polar statistic.
- **Stations that move for their own reasons.** Kilauea's flank produced a fake
  Pacific plate pole three separate times in these checks. Any station-level
  analysis needs a written-down exclusion rule.
- **NGL's plate assignment is not authoritative.** Western Alaska is filed
  under the Pacific plate. Trust the file for convenience, not for truth.
- **Mixing reference frames.** Single-plate velocities from different models are
  not comparable; only relative motion between plate pairs is. Section 5 is
  built that way, and section 4 states why its one direct comparison is
  legitimate.
- **Formal uncertainties.** ITRF2020's per-site sigma understates real scatter
  by a factor near four. Do not put a formal error bar on a page without saying
  what it excludes.
- **Reconstruction models are updated in place.** The GPlates Web Service
  default model can change, and named models' rotation files have been updated
  as recently as September 2025. Pin the model and record the date.
- **MORVEL's averaging interval is not one number.** 0.78 Myr for ten spreading
  centres, 3.16 Myr for seven, decades for five or six plates carried on GPS.
- **The site's own house rule cuts against this project.** `HANDOFF.md` section
  4: *"a globe is a map, and the first picture should say 'this is a model',
  not 'this is a map'."* This is inherently a map subject. Stage 2 has to
  answer that, not work around it.
- **`paleomap.org` is not Scotese's site and never was.** It is a parked domain
  turned unrelated tool. Citing it is an error that appears in the wild.
- **Licences.** MORVEL reserves commercial rights; GSRM, NGL and ITRF state
  none; Scotese's website is non-commercial-with-permission and names websites
  among prohibited uses. Only the OSF future grids are unambiguously free.

## 11. Kill criteria

None met, but two need stating rather than waving through.

- *The central claim needs data that does not exist or is not obtainable*:
  **not met.** Every regime has free public data, and all three were run today.
- *The data supports only a much weaker claim, and the weaker claim is not
  interesting*: **not met, though the claim does weaken.** "Where the
  continents end up" is not answerable. "Here are three regimes with three
  epistemic statuses, and here are the numbers" is answerable, and is a better
  page.
- *The honest version is something a reader already knows*: **not met**, per
  section 9 points 2, 3 and 4.
- *The only sources are copyrighted works*: **not met**, but close on one
  flank. Scotese's renderings cannot be reproduced; the geometry underlying
  them is a scientific hypothesis and not copyrightable, and the CC0 grids give
  an independent construction of the same scenario. Redraw, never lift.

## 12. Reproducing the checks

```
python plate_check.py          # Euler fits per plate, writes plate_fit.json
python rigidity_check.py       # adds PB2002 distance, writes rigidity_fit.json
python outlier_check.py        # the Pacific, taken apart
python crosscheck.py           # arithmetic against NGL's own model
python itrf_compare.py         # science against ITRF2020-PMM
python geologic_vs_geodetic.py # MORVEL against the geodetic models
python model_spread.py         # eight reconstructions, cached in model_spread.json
python future_spread.py        # four futures from the CC0 grids
python feas_plot.py            # scratch figure, not a site figure
```

Downloads, all fetched 5 September 2026:

- `https://geodesy.unr.edu/gps_timeseries/IGS20/midas/midasfile` and
  `platevel.all`, plus `https://geodesy.unr.edu/velocities/midas.readme.txt`
- `https://itrf.ign.fr/docs/solutions/itrf2020/ITRF2020-PMM.dat` and
  `ITRF2020-PMM-residuals.dat`
- `https://geodesy.unr.edu/GSRM/poles.NNR`
- `https://raw.githubusercontent.com/insarlab/MintPy/main/src/mintpy/objects/euler_pole.py`
- `https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json`,
  `PB2002_plates.json`, `PB2002_orogens.json`, and
  `http://peterbird.name/oldFTP/PB2002/PB2002_boundaries.dig.txt` (http only;
  the https host does not respond)
- `https://osf.io/download/k6cbj/` for `Grid files.zip`, plus `grd_in.m` and
  `Read me.txt` from OSF 8NEQ4
- `https://gws.gplates.org/model/list/` and `/reconstruct/reconstruct_points/`

`feas_rigidity.png` is a scratch matplotlib plot with no palette and no
`sitefig.py`. It exists to show the distance-residual relationship is real and
monotonic, and it is not a candidate figure.

## 13. Gaps, and what was not verified

- **No full 56-row NNR-MORVEL56 table from the authors' own site**, because
  that table is published as a JPEG and the host is dead. Everything here uses
  MintPy's transcription. Stage 3 should re-derive it from Argus et al. 2011
  Table 1 rather than trusting a third-party Python file.
- **PB2002 distances are to the nearest boundary vertex, not the nearest point
  on the segment.** Vertices are closely spaced so the error is small, but it
  is a slight overestimate of distance where segments are sparse.
- **The orogen area figure computed here, 7.5 per cent of the sphere by
  equal-area shoelace on `PB2002_orogens.json`, is not checked against Bird
  2003's own stated value**, and three of the plate polygons cross the dateline
  in a way that breaks the same calculation. Do not quote 7.5 per cent without
  checking the paper.
- **`model_spread.py` uses six cities, not a global grid.** It reproduces the
  shape of Buffan et al. 2023 but is not a substitute for it. A Stage 3 version
  should either use their published numbers or run a proper grid.
- **The future grids carry no plate identities.** "Antarctica" in section 7
  strictly means "land in the south polar zone"; the identification comes from
  the published scenario descriptions, not from the files.
- **The licence conflict on Scotese and van der Pluijm 2020 is unresolved.**
  Crossref and Semantic Scholar say CC BY 4.0; Unpaywall and OpenAlex say
  CC BY-NC-ND. Nobody has read the PDF masthead.
- **Hoffman's 1992 coining of "Amasia"** is a single-source claim; Eos meeting
  supplements are not indexed and the page could not be confirmed.
- Several publisher sites (Wiley, Elsevier, Nature, Annual Reviews) refuse
  automated fetches, so a number of the verbatim quotations above were read
  from green open-access copies and preprints rather than the version of
  record. Anything that reaches a published page should be checked against the
  article of record.

## 14. Corrections, found while designing Stage 2

Recorded here rather than silently patched, because four of the nine scripts
above are the prototype Stage 3 builds from and two of these are live hazards
to anyone reusing them.

- **`otis_grid.cell_centres()` was wrong, and is now fixed.** It treated the
  grid as 721 latitude cells spanning 180 degrees, giving 0.2497 degree spacing
  and an axis running -89.875 to 89.880. The grid is 721 latitude *nodes* at
  exactly 0.25 degrees from -90 to +90, and 1440 periodic longitude nodes. The
  old axis was shifted about 0.12 degrees and stretched 0.1 per cent, which
  biased every area weight and put the 88 degree cut one row off. Re-running
  `future_spread.py` on the corrected axis moves five cells in section 7 by one
  in the last digit, and those cells are corrected above. **Every headline
  number survives unchanged**: 47.2 per cent maximum disagreement, 0.945 per
  cent agreement at t = 0, 29.1 per cent land. The function keeps its name
  because callers use it, and carries the old behaviour in its docstring.
- **There is a third contaminated Pacific station, and section 4 misses it.**
  `ILSG` on Salas y Gomez (-26.47, -105.36) is filed by NGL under the Pacific
  plate but sits east of the East Pacific Rise, on Nazca; its residual is
  137.7 mm/yr, roughly the full PA-NZ spreading rate. The hand-drawn Hawaii and
  Alaska boxes in `outlier_check.py` do not catch it. Worse, neither does the
  ITRF comparison in section 4: with `ILSG` retained the Pacific fit still
  agrees with ITRF2020-PMM to 0.99 mm/yr, because one station cannot move a
  weighted fit. It only ruins the RMS. **The trap has two shapes and needs two
  checks** — one on the pole, one on the worst single residual.
- **The hand-drawn exclusion boxes are themselves the failure they guard
  against.** `haw` and `big` in `outlier_check.py` are a hard-coded answer for
  today's contaminants. They were the right tool for showing that the Pacific's
  residual is a volcano rather than a plate, and they are the wrong tool for a
  build. Stage 3 replaces them with a stated iterated rule and keeps the boxes
  only as an assertion about that rule's output.
- **`read_grid` carries dead code and a mislabelled field.** The
  `if lons[0] < 0 and lons[1] < 0 and dt > 0: lons += 360` branch, inherited
  from the authors' MATLAB reader, never fires on any of the 50 files; an
  untested heuristic in a loader is a future misfire. The field that reader
  calls `dt` and labels "Time step (sec)" is 0.25 — it is the grid spacing.
- **Section 7's land-distribution table compares different ages.** It reports
  each scenario's final snapshot, which is 250 Myr for Pangaea Ultima and
  Aurica and 200 Myr for Novopangaea and Amasia. That is a valid statement
  about each scenario and it is not a comparison between them. Any figure
  putting the four side by side must recompute at 200 Myr, the only age all
  four reach.
- **The 250 Ma narrowing is real, and is now measured rather than asserted.**
  Section 6 explains it as Pangaea leaving less room to differ, but the row
  also drops from eight models to seven, which would explain it equally well.
  Holding the model set fixed: on the seven models that reach 250 Ma the max
  spread goes 3,347 km at 200 Ma to 1,352 km at 250 Ma; on the four that reach
  500 Ma it goes 2,586 to 1,217. The narrowing is not an artefact of which
  models stop where.
- **`model_spread.py` has an unverified assumption that regime 2 cannot
  otherwise catch.** It sends points to the GPlates Web Service as `"lon,lat"`
  and reads them back as `[lon, lat]`, and nothing confirms the order. If the
  service ever swaps it, Denver lands in the Indian Ocean and every pairwise
  distance still looks plausible — a fabricated disagreement number in the one
  regime that has no external anchor. Requesting age 0 and asserting each model
  returns the input coordinate costs eight requests and closes it.

- **Section 4's distance bands are not the numbers the page ships, and the
  difference is method rather than error.** Stage 1 fitted each plate on all
  of its stations and reported the residual of the same stations. The build
  fits on interior stations only, after the stated exclusion rule, and then
  reports the residual of every station on the plate against that fit - so a
  near-boundary station is a prediction being tested rather than part of what
  was fitted. That moves the near-boundary median from 9.11 to 13.95 mm/yr
  and the deep-interior median from 0.62 to 0.47. The build's version is the
  one on the page and the one to trust.
- **The mutual-agreement percentages here are unweighted cell counts.** The
  page area-weights everything, which turns Stage 1's 32.07 and 0.945 per
  cent into 33.96 and 0.78. Same files, same finding, a weighting that Stage
  1 applied inconsistently between the two.
