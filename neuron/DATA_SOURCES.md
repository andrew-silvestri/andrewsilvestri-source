# Data sources

## Used

**NeuroMorpho.Org**, version 8.x. Every reconstruction in the archive, taken
through the REST API (`https://neuromorpho.org/api`, no key) and the
documented static file paths under `/dableFiles/`. The HTML pages must not be
scraped and are not touched. Licence **CC BY 4.0**. Redistribution and
commercial use are permitted with attribution, and the terms require three
citations: the originating paper for each reconstruction, which the API
supplies per neuron as `reference_doi`; NeuroMorpho.Org (RRID:SCR_002145); and

> Ascoli, Donohue & Halavi, *The Journal of Neuroscience* 27(35):9247–9251,
> 2007, doi:10.1523/JNEUROSCI.2055-07.2007
>
> Tecuatl, Ljungquist & Ascoli, *FASEB BioAdvances* 6(7):207–221, 2024,
> doi:10.1096/fba.2024-00048

Two things about the files matter and are not obvious. The CNG-standardised
copy is **re-oriented** — the soma is translated to the origin and the axes
rotated onto the principal components of the coordinates — so it is not in
anatomical orientation. And for the whole-brain archives the standardisation
rewrites the radius column: the depositor's own file carries a single value
on every point, and the standardised copy carries one value for neurites and
another for the soma. Both versions are downloadable, at
`/dableFiles/<archive>/CNG version/<name>.CNG.swc` and
`/dableFiles/<archive>/Source-Version/<name>.swc`, with that capitalisation
exactly.

**Allen Cell Types Database**, through the Allen Institute API
(`http://api.brain-map.org/api/v2/data/query.json`, no key). Fetched
separately because its archive name on NeuroMorpho contains spaces and the
Solr endpoint cannot be queried for a multiword value. The reconstruction file
is well-known-file type `303941301`; type `486753749` is a marker file and is
not wanted. Terms of use are free but **non-commercial**, with an explicit
carve-out permitting publication of a limited set of the content in a
journalistic publication with citation. Cite the database
(RRID:SCR_014806) and:

> Gouwens *et al.*, *Nature Neuroscience* 22(7):1182–1195, 2019,
> doi:10.1038/s41593-019-0417-0

The distributed coordinates are **not shrinkage-corrected**; see below.

## Looked up, not recomputed

Each carries its citation in `outputs/neuron_payload.json` under `looked_up`,
and on the page under Sources.

| Value | Source |
|---|---|
| Diffraction limit, 200–300 nm laterally | Huang, Bates & Zhuang, *Annu Rev Biochem* 78:993–1016, 2009 |
| Thinnest axon shaft, 0.17 µm | Shepherd & Harris, *J Neurosci* 18(20):8300–8310, 1998 |
| Spine neck, 0.15 µm | Harris & Stevens, *J Neurosci* 9(8):2982–2997, 1989 |
| Axon lost to a 300 µm slice, 48–49% | van Pelt, van Ooyen & Uylings, *Front Neuroanat* 8:54, 2014 |
| z shrinkage in 350 µm slices, 63 ± 10% | Mohan *et al.*, *Cereb Cortex* 25(12):4839–4853, 2015 |
| Vibratome shrinkage by embedding method | Gardella *et al.*, *J Neurosci Methods* 124(1):45–59, 2003 |
| Correction factors ×1.1 and ×2.1 | Marx & Feldmeyer, *Cereb Cortex* 23(12):2803–2817, 2013, attributing Marx *et al.*, *Nat Protoc* 7(2):394–407, 2012 |
| Diameter excluded from DIADEM | Gillette, Brown & Ascoli, *Neuroinformatics* 9(2–3):233–245, 2011 |
| Two pipelines, same eight cells | Blackman *et al.*, *Front Neuroanat* 8:65, 2014 |
| Inter-operator agreement, IoU 0.470 | Fernholz *et al.*, *PLoS Comput Biol* 20(2):e1011774, 2024 |
| Spine membrane factor, F = 1.78–2.39 | Eyal *et al.*, *eLife* 5:e16553, 2016 |
| Synaptic delay, 0.4–0.5 ms minimum | Katz & Miledi, *Proc R Soc Lond B* 161(985):483–495, 1965 |
| Central synapse release, 150 µs | Sabatini & Regehr, *Nature* 384(6605):170–172, 1996 |
| Whole-brain axon, >85 m over >1,000 cells | Winnubst *et al.*, *Cell* 179(1):268–281.e13, 2019 |
| SWC format | Cannon, Turner, Pyapali & Wheal, *J Neurosci Methods* 84(1–2):49–54, 1998 |

Two of these are on the page because they are cited wrongly elsewhere, and
that is the page's subject rather than a digression. Megías *et al.*,
*Neuroscience* 102(3):527–540, 2001, doi:10.1016/S0306-4522(00)00496-6 is
often given as the source of a dendritic-spine membrane-area factor and
contains none; it is the source for where spines are, which is why the real
factor applies only beyond 60 µm from the soma. And the familiar "0.5 ms
synaptic delay" is the upper bound of a *minimum*, measured at a frog
neuromuscular junction at 20 °C in low-calcium Ringer.

## Rejected

**MouseLight on figshare** (collection 3924088, 303 articles). Holds no SWC
files — every article is a link to `mouselight.janelia.org` — and the
deposits are CC BY-NC 4.0, which conflicts with NeuroMorpho's site-wide CC BY
4.0 for the same reconstructions. The NeuroMorpho `MouseLight` archive is used
instead, under NeuroMorpho's terms.

**Blue Brain / EPFL microcircuit portal.** CC BY-NC-SA 4.0, and the
morphologies are Neurolucida ASCII rather than SWC.

**Allen z coordinates.** Present in every file and unusable. The Allen Cell
Types technical white paper documents no shrinkage correction; Gouwens *et
al.* 2019 handled the compression by excluding z-derived features from their
own classification rather than by correcting the coordinates, and a per-cell
correction appears only downstream, in the Patch-seq pipeline of Lee *et al.*,
*eLife* 10:e65482, 2021. Both figures that draw a reconstruction are flat
projections, and `swclib.load_xy()` returns two columns so that nothing can
quietly use the third.

**FlyWire** (CC BY-NC 4.0) and the dense electron-microscopy volumes
(MICrONS, H01). Not needed: the question is about what light-microscopy
reconstructions record, and these are a different measurement entirely.
