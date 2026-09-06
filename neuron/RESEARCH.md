# Research and feasibility: a neuron, visualised

Stage 1 of `00 PUBLISH/prompts/NEW_PROJECTS.md` §2. Written 5 September 2026.
Lives in `03 RESEARCH/neuron/` with the archive census (`census.py`, writes
`census.json` and `neurons.csv.gz`), the cross-tabulation (`crosstab.py`), the
two downloaders (`fetch_allen.py`, `fetch_neuromorpho.py`), the morphometry
(`swc_check.py`, writes `swc_metrics.csv`), the class split and clamp test
(`split_check.py`), the source-versus-CNG comparison (`source_check.py`), the
diameter-flag audit (`diameter_audit.py`), the projection-neuron check
(`projection_check.py`), the
scale arithmetic (`scale_check.py`) and the feasibility
figure (`feas_fig.py`, writes `feas_neuron.png`). No design decisions are made
here. Nothing in `00 PUBLISH` was touched.

Numbers marked **[computed]** were computed in this folder today from files
downloaded today, and are reproducible with the scripts named in §8. Numbers
with a DOI are from the literature; see §10 on how far each was verified.

## 1. Verdict

**The project exists, but not as the brief frames it, and the question it
should answer is not the one it starts from.**

The brief asks whether a visualisation built from a real traced morphology
would show a reader something a textbook diagram does not, and names as one
candidate question "how much of what a textbook diagram shows is schematic
rather than measured". That is the right question. The answer is not the
expected one.

The expected answer is that the textbook diagram is schematic and the
reconstruction is real. What the data says is that **the reconstruction is also
partly schematic, in a different place, and it says so in its own metadata.**
Of the 298,339 reconstructions in NeuroMorpho.Org, 7.5% contain a soma, a
dendrite and an axon; 70.1% record no measured thickness anywhere; 22.1% are
flat; 2.7% are corrected for the tissue shrinkage that halves the z axis. The
number that carries every property a true-proportion drawing needs — all three
compartments, a measured diameter, three dimensions, an axon its depositor
marked complete, and a shrinkage correction — is **104. That is 0.03% of the
archive.** Those 104 come from six labs, contain no human cell, and are almost
all cells whose axon never leaves the neighbourhood. Relaxing the shrinkage
requirement admits 1,651 more, including whole-brain projection neurons — but
those pass the diameter test on a technicality, and the technicality is the
finding (§4d). [computed]

And the shortage is structural rather than incidental. The datasets that
contain a complete axon are whole-brain preparations that record no diameter at
all: of 36,582 reconstructions whose axon is marked complete, 14.8% carry a
measured diameter. [computed] In the 200 MouseLight whole-brain cells I
downloaded, every neurite in every file is drawn at one placeholder value and
the soma at another — two distinct numbers per file, 0.25 µm and 2 µm.
[computed] In the Allen Cell Types database, which does measure diameter,
50.9% of all 4,030,735 reconstruction points sit at exactly the same clamped
minimum, 0.2288 µm — a floor at the diffraction limit of the microscope.
[computed]

Supportable claim, one sentence: *In the published record of what neurons
actually look like, the further an axon travels the coarser its recorded
thickness becomes — every sampled reconstruction carrying more than 15 mm of
axon records its whole arbor at between three and eighty-one distinct
diameters, most of it at a single value — so a drawing of one neuron at true
proportions cannot be made from any single file, and the schematic in the
textbook and the reconstruction in the archive are each inventing a different
half of the picture.*

Not supportable: that a real morphology drawn at true proportions is simply
available and only needs rendering. Not supportable as an absolute, though I
drafted it that way first: that the archive contains **no** projection neuron
with a complete axon and a measured diameter — the metadata says 1,651
reconstructions qualify, and the honest finding is what happens when you open
them (§4d). Also not supportable, from this data, that textbook diagrams have
been shown to be inaccurate — see §7, trap 2.

There is a second finding, cleanly measured, that the brief did not anticipate
and that is the more direct answer to "what would a reader not already know":
**the axon is not a stub.** In whole-brain reconstructions the median cell
carries 96 mm of axon against 6.5 mm of dendrite, a ratio of 13.8, and 99% of
cells have more axon than dendrite. [computed] The most-published picture of a
pyramidal neuron — the Allen mouse spiny cell, dendrite-only — has a median of
**41 µm of axon** against 3,362 µm of dendrite. [computed]

## 2. Finding the question

"A neuron" is a subject. Four candidate questions were tested against the data
before writing this. Three fail and one survives.

- **"How does a signal travel?"** — Fails as a still figure and is expensive as
  an interactive. The measured numbers exist (§6) but the honest version
  contradicts the animation everyone expects: the spike starts 35.6 ± 2.3 µm
  out the axon, not at the soma (Palmer & Stuart, *J Neurosci* 26(6):1854–1863,
  2006, doi:10.1523/JNEUROSCI.4812-05.2006); it runs backwards into the
  dendrites (Stuart & Sakmann, *Nature* 367(6458):69–72, 1994,
  doi:10.1038/367069a0); those backward spikes fail at branch points so
  different parts of the same tree see different signals (Spruston, Schiller,
  Stuart & Sakmann, *Science* 268(5208):297–300, 1995,
  doi:10.1126/science.7716524); and the dendrites generate their own spikes
  that never reach the soma (Schiller, Schiller, Stuart & Sakmann, *J Physiol*
  505(3):605–616, 1997). Simulating this on a real morphology costs, on one
  laptop core, between about 31 minutes and 5.8 hours per simulated second
  (Oláh, Pedersen & Rowan, *eLife* 11:e79535, 2022, doi:10.7554/eLife.79535),
  so it is precomputed or it is not done. It is a good §3-of-a-page, not a page.
- **"Why does the morphology look like that?"** — Real literature exists, but
  answering it needs the branching statistics whose measurement is least
  trustworthy (§5) and the answer is a modelling result, not an observation.
- **"What is the real scale relationship between soma, dendrite and axon?"** —
  Survives, and is measurable. See §4.
- **"How much of the picture is measured?"** — Survives, is measurable, and is
  the one nobody has drawn. See §4.

The last two are the same page. The scale relationship is what the textbook
gets wrong; the measurement question is what the archive gets wrong; and the
two are causally linked, because it is precisely the parts that are too thin to
resolve that are too thin to draw.

**The link, computed.** A true-proportion drawing of the median whole-brain
cell spans 5,194 µm end to end. Real thin axons in the same tissue measure
0.17 ± 0.04 µm by electron microscopy (Shepherd & Harris, *J Neurosci*
18(20):8300–8310, 1998). That is a dynamic range of 1:30,556 — **4.5 orders of
magnitude in one picture.** At 1,000 pixels wide the thinnest neurite is 0.033
of a pixel; rendering it as a single pixel needs a canvas 30,556 px wide. On a
180 mm printed page it is 0.0059 mm, fourteen times below a 300 dpi press dot.
[computed]

**The schematic is not a casual lie. It is a forced one.** A page holds about
three orders of magnitude between its largest and smallest mark; this cell
needs four and a half. That is a computable reason for the diagram to exist,
and stating it is more interesting — and much harder to argue with — than
catching a textbook out.

## 3. The primary data

All free. None needs a key for bulk download. Verified reachable and
downloaded from today.

| Source | Contents | N | Format | Access | Licence |
|---|---|---|---|---|---|
| **NeuroMorpho.Org** v8.6.124 (rel. 2026-08-07) | every deposited morphology, 95 species, ~490 regions, 1,011 labs | **298,339** | SWC (CNG-standardised + source) | REST API, no key; files at `/dableFiles/<archive>/CNG version/<name>.CNG.swc` | **CC BY 4.0** |
| **Allen Cell Types** | patch-clamp biocytin fills, morphology **and ephys on the same cells** | 667 (509 mouse, 158 human); 367 full, 300 dendrite-only | SWC + NWB | HTTP API, no key | free, **non-commercial**, explicit journalistic carve-out |
| **MouseLight** (via NeuroMorpho archive `MouseLight`) | whole-brain single neurons, complete long-range axon | 1,112 on NeuroMorpho; 1,653 in Janelia's browser | SWC | as NeuroMorpho | **licence conflict — see §7** |
| **Peng / fMOST** (NeuroMorpho archive `Peng`) | whole-brain fMOST reconstructions | 1,743 | SWC | as NeuroMorpho | CC BY 4.0 via NeuroMorpho |
| FlyWire, hemibrain, MICrONS, H01 | connectome EM volumes | large | precomputed / meshes | account gate on some | CC BY 4.0 except FlyWire (**NC**) |

Canonical citations: Ascoli, Donohue & Halavi, *J Neurosci* 27(35):9247–9251,
2007, doi:10.1523/JNEUROSCI.2055-07.2007, and Tecuatl, Ljungquist & Ascoli,
*FASEB BioAdvances* 6(7):207–221, 2024, doi:10.1096/fba.2024-00048 (NeuroMorpho
requires both, plus the originating paper per neuron, which the API supplies as
`reference_doi`). Allen: Gouwens et al., *Nat Neurosci* 22(7):1182–1195, 2019,
doi:10.1038/s41593-019-0417-0. MouseLight: Winnubst et al., *Cell*
179(1):268–281.e13, 2019, doi:10.1016/j.cell.2019.07.042. fMOST: Peng et al.,
*Nature* 598(7879):174–181, 2021, doi:10.1038/s41586-021-03941-1. SWC format:
Cannon, Turner, Pyapali & Wheal, *J Neurosci Methods* 84(1–2):49–54, 1998,
doi:10.1016/S0165-0270(98)00091-0.

**Two access rules that bind.** NeuroMorpho forbids scraping its HTML pages and
`robots.txt` disallows all non-search agents; the API and the `dableFiles`
paths are the sanctioned routes, and the scripts here use only those. And
**the CNG-standardised file is re-oriented** — soma translated to the origin,
axes rotated onto the principal components of the coordinates — so a CNG file
is not in anatomical orientation, and its radii are not always the depositor's
(§4b). Both versions are downloadable: `/dableFiles/<archive>/CNG version/`
`<name>.CNG.swc` and `/dableFiles/<archive>/Source-Version/<name>.swc`, that
capitalisation exactly.

**One dead end, recorded so it is not retried.** The Janelia MouseLight
figshare collection (3924088, 303 articles) holds no SWC files — each article
is a link to `mouselight.janelia.org`. `fetch_mouselight.py` in this folder
demonstrates it and returns nothing; the NeuroMorpho `MouseLight` archive is
the working route.

**Tooling.** `neurom` 4.0.5, `morphio` 3.5.0, `navis` 1.12.0 are alive on PyPI;
the well-known `BlueBrain/*` GitHub repos were archived 2025-02-26 and moved to
`openbraininstitute`. The Blue Brain microcircuit portal is **CC BY-NC-SA** and
is not usable here. Nothing in the analysis below needed any of them — the SWC
parser in `swc_check.py` is 20 lines — and Stage 3 should keep it that way.

**Prior art to look at before proposing an interactive.** DendroTweaks
(Roshchin et al., *eLife* 2025) is already a browser front-end for exploring a
single neuron's morphology and channels, with simulation delegated to a server.
The brief's warning that a rotating 3D neuron is a screensaver has a stronger
form: the interactive that seems obvious here has been built.

## 4. Feasibility check: what a deposited reconstruction actually contains

Two independent passes, both run today.

### 4a. The archive census — all 298,339 records

`census.py` pages the whole `/api/neuron/select` endpoint and tallies every
categorical field; `crosstab.py` joins them. This is a complete enumeration,
not a sample. Retrieved 2026-09-05 07:53 UTC.

**What is in a file** [computed]:

| Property | n | % |
|---|---|---|
| has a soma | 214,733 | 72.0 |
| has an axon | 55,015 | 18.4 |
| axon marked complete | 36,582 | 12.3 |
| has a measured diameter | 89,132 | 29.9 |
| 3D (not flattened) | 232,322 | 77.9 |
| shrinkage corrected | 7,927 | **2.7** |

**Everything a true-proportion drawing needs, accumulated** [computed]:

| Requirement | n | % |
|---|---|---|
| soma + dendrite + axon | 22,491 | 7.54 |
| … and a measured diameter | 12,123 | 4.06 |
| … and 3D | 11,968 | 4.01 |
| … and the axon marked complete | 1,651 | 0.55 |
| … and shrinkage corrected | **104** | **0.03** |

**What the 104 are** [computed]. They come from six laboratories
(Feldmeyer 48, Conte 24, Petersen 15, Ascoli 12, Turner 3, Szucs 2) and are 65 rat,
24 *Xenopus laevis*, 15 mouse — **no human cell at all**. By region: 48 are
layer-4 barrel cortex, 18 spinal cord, 15 layer-2 barrel cortex, 6 brainstem,
6 hippocampal CA3. By type they are mostly interneurons, with 15 pyramidal
projection cells.

That composition matters more than the count. These reconstructions are
complete because they are of cells **whose axon stays local** — barrel-cortex
interneurons and spinal neurons — not because anyone solved the problem for a
projecting cell. The 104 are not a small supply of the thing the project wants;
they are 104 examples of a different thing.

**The trade-off is structural** [computed]. Of the 36,582 reconstructions whose
axon is marked complete, only 5,420 — 14.8% — carry a measured diameter. The
archives supplying most axon-complete cells are whole-brain or invertebrate
preparations: Chiang/FlyCircuit 23,635, Baier 2,581, Peng 1,720, MouseLight
1,111. All 23,635 Chiang cells are flagged "No Diameter".

Two supporting distributions [computed]: 59.8% of the archive is *in vitro*
(slice), 21.2% *in vivo*, 16.2% culture; 53.7% mouse, 20.6% rat, 12.5%
*Drosophila*, 5.3% human. The controlled vocabulary is not clean — the
shrinkage field contains "Not reported", "Not Reported", "N" and "Correced".

The nearest published comparison is Parekh, Armañanzas & Ascoli, *Cell Tissue
Res* 360(1):121–127, 2015, doi:10.1007/s00441-014-2103-6, which reviewed all
226 source publications behind v5.7 and found 53.5% of *datasets* carried soma,
axon and dendrite but under a quarter were "reasonably complete in regard of
physical integrity". Their unit is the dataset and mine is the reconstruction,
and the archive has grown 26-fold since; the two are consistent in direction
and are not the same measurement.

### 4b. The files themselves — 727 reconstructions parsed

`swc_check.py` reads the SWC files directly and computes path length per
compartment, so nothing here depends on anyone's metadata. Medians:

| | Allen (350 µm slice) n=527 | MouseLight (whole brain) n=200 |
|---|---|---|
| soma diameter | 12.58 µm | **2.00 µm (placeholder)** |
| dendritic length | 2,938 µm | 6,457 µm |
| **axonal length** | **160 µm** | **96,269 µm** |
| axon : dendrite | 0.05 | **13.83** |
| max extent | 571 µm | 5,195 µm |
| z extent | 102 µm | 4,045 µm |
| axonal branch points | 0 | 261 |
| distinct diameters in file | 1,644 | **2** |
| share of length at one diameter | 19% | **99.9%** |
| axon longer than dendrite | 40% of cells | **99% of cells** |

By cell class, which matters because the classes are reconstructed to different
standards [computed]:

| Species / class / type | n | dendrite | axon | axon:dend |
|---|---|---|---|---|
| mouse / spiny / dendrite-only | 189 | 3,362 µm | **41 µm** | 0.01 |
| mouse / aspiny / full | 126 | 2,377 µm | 10,470 µm | 4.40 |
| human / spiny / full | 69 | 7,860 µm | 5,046 µm | 0.64 |
| human / aspiny / full | 29 | 3,502 µm | 11,597 µm | 3.31 |
| mouse / sparsely spiny / full | 24 | 2,699 µm | 11,676 µm | 4.33 |

Three things fall out.

1. **The pyramidal cell everybody has seen has no axon.** The mouse spiny
   reconstruction, which is the modal published picture of a cortical neuron,
   carries 41 µm of axon. The whole-brain median is 96 mm. These are different
   cell populations from different labs and the comparison is **not** a
   truncation factor — see §7, trap 1 — but the contrast in what a reader is
   shown is real.
2. **Human dendrites are 2.3× mouse dendrites** (7,860 vs 3,362 µm for spiny
   cells), which is measured here and is a fact most readers do not have.
3. **The diameter in the whole-brain files does not exist, and the archive
   invents part of it.** Every MouseLight CNG file has exactly two distinct
   radius values; in the sampled file 3,988 of 3,991 points carry 0.125 µm and
   3 carry 1.0 µm. The 2 µm "soma diameter" in the table above is that
   placeholder, not a measurement — real somata are 12–15 µm, as the Allen
   column shows.

   **The depositing lab's own file is more uniform still.** Comparing
   NeuroMorpho's `Source-Version` against its CNG version for 10 MouseLight
   neurons (`source_check.py`), **all 10 source files carry a single radius
   value, 1.0, on every point** — 1,116 to 46,186 points each — and **all 10
   CNG files carry exactly two, 0.125 and 1.0.** [computed] The two-value
   structure that looks like a soma/neurite distinction is produced by
   NeuroMorpho's standardisation, not by the measurement. A figure that draws
   somata and neurites at different widths from a CNG whole-brain file is
   drawing the curation pipeline.

**The clamp.** In the Allen files, which do measure diameter, 96% share an
identical minimum of 0.2288 µm, and **2,053,244 of 4,030,735 points — 50.9% —
sit at exactly that value.** [computed] It is a floor, and it is at the
diffraction limit: visible light resolves 200–300 nm laterally and 500–700 nm
axially (Huang, Bates & Zhuang, *Annu Rev Biochem* 78:993–1016, 2009,
doi:10.1146/annurev.biochem.77.061906.092014). Every structure thinner than the
limit is recorded as being exactly at the limit.

That matters because the structures that carry the argument are thinner than
it. Measured by electron microscopy: CA3→CA1 axon shafts 0.17 ± 0.04 µm
(Shepherd & Harris 1998, above); cerebellar parallel fibres 0.16 ± 0.04 µm
(Perge, Niven, Mugnaini, Balasubramanian & Sterling, *J Neurosci*
32(2):626–638, 2012); CA1 spine necks 0.15 ± 0.06 µm (Harris & Stevens,
*J Neurosci* 9(8):2982–2997, 1989). **Half the thickness data in the best
light-microscopy morphology set is a constant standing in for something the
microscope could not see.**

### 4c. Is the headline number soft? A check against my own claim

The 70.1% rests on NeuroMorpho's `attributes` flag, and that flag is weak:
its own documentation defines "Diameter" as meaning only that the non-soma
radii are *not all identical*. A file with three distinct values passes. If
many flagged files were nearly degenerate, 70.1% would be an understatement
dressed up as a measurement — so `diameter_audit.py` samples files that carry
the flag and asks what thickness information they actually hold.

156 files across 13 archives (up to 12 per archive, drawn at random from each
archive's first 500 records — **not** a uniform sample of the whole archive):

| Degeneracy test | files | share |
|---|---|---|
| ≤ 3 distinct diameters | 9 | 5.8% |
| ≤ 20 distinct diameters | 20 | 12.8% |
| ≥ 80% of length at one value | 13 | 8.3% |
| ≥ 90% of length at one value | 11 | 7.1% |

Median across the sample: **176 distinct diameters and 11% of length at the
commonest value.** [computed] The flag is mostly honest. One archive is not —
Helmstaedter's files carry a median of 3 distinct values covering 97% of their
length, and pass as "Diameter".

**So the claim survives, and it was conservative.** Taking the ≥80% test as
the threshold for "no usable thickness", about 8% of the flagged 29.9% is
degenerate too, which moves the real figure from 70.1% to roughly **73%**. The
document keeps 70.1% because that is the number the archive's own flag
supports and it is the smaller of the two. A Stage 3 page should quote 70.1%
and state that the true figure is somewhat higher.

`feas_neuron.png` draws both panels: axon against dendrite per cell, where the
two datasets occupy disjoint regions with no cell in the corner that has both;
and the length-weighted diameter distribution, where MouseLight is a single
spike and Allen is a spike at the clamp with a tail.

### 4c-bis. A miscount, corrected at Stage 3

This document said the 104 came from **five** laboratories. It is six: the
sixth, Szucs, contributes two cells and fell outside the five rows the Stage 1
script printed. The count was never computed, only read off a truncated
display. The page takes the number from `describe_104()` rather than from
here.

### 4d. The one place I overstated it, and what the check found instead

Drafting this, I wrote that no long-range projection neuron in the archive has
both a complete axon and a measured diameter. **That was wrong, and the way it
is wrong is worth more than the claim was.**

Dropping the shrinkage requirement, 1,651 reconstructions pass soma + dendrite
+ axon, the "Diameter" flag, 3D and "Axon Complete" — and they include 229
MouseLight and 100-plus fMOST whole-brain cells, with 268 typed as projection
neurons. On the face of it the combination exists.

`projection_check.py` samples them and measures both quantities on the same
file [computed]:

| Archive | axon (mm) | distinct diameters | share of length at one value |
|---|---|---|---|
| MouseLight | 51.7 – 117.5 | 3 – 7 | 81 – 92% |
| Peng / fMOST | 16.9 – 59.9 | 3 | 100% |
| Tolias | 13.4 – 19.0 | 20 – 81 | 74 – 87% |
| Sjöström | 0.3 – 8.1 | 286 – 1,422 | 0 – 2% |
| Wang (retina) | 0.4 – 0.6 | 21 – 28 | 40 – 65% |

Across the 15 sampled: every cell with more than 15 mm of axon carries between
3 and 81 distinct diameter values with **75–100% of its length at a single
value**; every cell with a genuinely resolved diameter profile (>200 distinct
values) has an axon of **0.3–8.1 mm**.

So the flag is passed, and the thickness is still not measured — it is
quantised into a handful of steps. The accurate statement, and the one the
page should make, is not that the combination is absent from the archive but
that **it is absent from the data even where the metadata says it is present**:
the further an axon goes, the coarser its recorded thickness, with no sampled
exception. That is a stronger claim than the one I started with because it is
measured on the files rather than counted from flags, and it is the reason
§4c's audit mattered — a flag is not a measurement.

### 4e. The 104, opened (added at Stage 3, 6 September 2026)

Everything above about the 104 was read from flags. None of their six
archives was in the Stage 1 or Stage 3 sample, so until today no file from the
complete set had been opened, which is the mistake trap 11 describes,
committed on the page's own punchline. `fetch_data.py --complete-only` now
opens all of them and `data/complete_metrics.csv` holds the result.
[computed]:

| Opened | n |
|---|---|
| pass the width rule (≥4 distinct values, ≤90% of length at one) | 82 of 104 |
| fail it | 22: Conte 20, Feldmeyer 1, Turner 1 |
| hold **one** width and carry the "Diameter" flag | 2 (Conte) |
| projection cells, 2.1–6.5 mm reach, 45–74 mm axon, 20–71 widths | 15 (Petersen; mouse L2 barrel cortex, in vivo) |
| Turner CA3 cells spliced from two cells ("Dendrite-…-Axon" in the name) | 3 |
| depositor's Source-Version available on NeuroMorpho | Ascoli only; Feldmeyer and Petersen return 404 |

**§1's "almost all cells whose axon never leaves the neighbourhood" is wrong
for fifteen of them.** The Petersen cells look like the thing §1 says no file
contains. Their paper — Yamashita et al., *Front Neuroanat* 12:33, 2018,
doi:10.3389/fnana.2018.00033 — was searched in full text: no occurrence of
"shrink", "shrinkage", "correction" or "corrected"; on completeness, "we
cannot exclude that some axons might have been incompletely traced, and it is
likely that some axons were incompletely labeled" and "in most cases we lost
the axon within the callosal fiber tract". So the archive's *Corrected* and
*Axon Complete* fields on those 15 are curation values the source does not
support. That is trap 11 again, and the page now states it with the citation.

**The cell the page draws** is chosen by rule (`fetch_data.pick_drawn()`):
the largest single-paper group among the 104 (the 48 Feldmeyer cells whose
correction §10 verified), less the one that fails the width rule, then the
cell nearest the group's median reach and axon length: BC150319A_28, a rat
L4 barrel-cortex Martinotti-like interneuron, reach 725 µm, 37.1 mm of axon,
3.6 mm of dendrite, 21 distinct widths. Its axon holds 10 widths with 64% of
its length at 0.24 µm — the diffraction floor again — and its dendrites 18
widths from 0.41 to 3.15 µm. [computed] Even in the corrected corner the
axon's width is a floor and the dendrite's is a measurement. The CNG file is
PCA-rotated (trap 5) and no Source-Version exists for the archive, so the
drawing is in the archive's orientation and says so.

**Why the Conte cells are not cited on the page.** Twenty of the 22 files that
fail the width rule are the Conte archive's *Xenopus* tadpole spinal neurons
(Conte, Borisyuk, Hull & Roberts, *J Neurosci Methods* 351:109062, 2021,
doi:10.1016/j.jneumeth.2020.109062). The page names them only inside a
generated list ("Conte 20, Feldmeyer 1, Turner 1"), and `add_citations.py`
attaches a marker to a fixed phrase in the prose; there is no sentence about
them to anchor one to, and an anchor inside a generated list would break the
next time the counts moved. The citation is recorded here instead. If the
page ever gains a sentence about them, that is where the marker goes.

## 5. What the literature says about why

The archive's shortcomings are documented, in pieces, by the people who built
it. This is the corroboration that turns a metadata count into a finding.

**Slicing removes the axon.** van Pelt, van Ooyen & Uylings, *Front Neuroanat*
8:54, 2014, doi:10.3389/fnana.2014.00054, applied a mass-density completion to
three rat L2/3 pyramidal datasets and found **48–49% of intracortical axon lost
in a 300 µm slice against 15–17% of dendrite**; their NETMORPH validation gives
85.9% of axonal length lost at 100 µm, 60.2% at 200 µm, 39.7% at 300 µm. That
is *local* axon only; essentially all long-range projection axon is lost.
Reimann et al., *eLife* 13:RP99688, report that repair algorithms "could not
capture detailed axonal properties beyond 1000 µm". Parekh et al. 2015 state it
plainly: "the vast majority of the axonal length is lost when cortical pyramidal
cells or other projection neurons are traced from typical electrophysiological
preparations in vitro".

**Dendrites are truncated too.** Oberlaender et al., *Cereb Cortex*
22(10):2375–2391, 2012, doi:10.1093/cercor/bhr317, found in vivo dendritic
lengths 1.5–2.7× the in vitro values for matched types.

**The z axis is wrong by about half.** Mohan et al., *Cereb Cortex*
25(12):4839–4853, 2015, doi:10.1093/cercor/bhv188, measured 350 µm slices at
137–141 µm after mounting — **63 ± 10% z shrinkage** — and, importantly, found
total dendritic length rises only 11 ± 2% when corrected, because most branches
run in plane. Gardella et al., *J Neurosci Methods* 124(1):45–59, 2003,
doi:10.1016/S0165-0270(02)00363-1, measured vibratome sections at 39.7% of
nominal thickness. The Feldmeyer group's standard correction is ×1.1 in x–y and
×2.1 in z (Marx & Feldmeyer, *Cereb Cortex* 23(12):2803–2817, 2013,
doi:10.1093/cercor/bhs254; stated verbatim and attributed to Marx et al.,
*Nat Protoc* 7(2):394–407, 2012, doi:10.1038/nprot.2011.449, in Emmenegger,
Qi, Wang & Feldmeyer, *Cereb Cortex* 28(4):1439–1457, 2018,
doi:10.1093/cercor/bhx352). **The 2.1 is protocol-specific, not a constant** —
a 2020 study of conventional embedding measured z shrinkage of 32% at day 3 and
40% at day 6, factors of about 1.5–1.7.

A detail worth keeping: 48 of the 104 fully-qualified reconstructions in §4a
are Feldmeyer barrel-cortex cells carrying exactly that
doi:10.1093/cercor/bhx352. The archive's shrinkage-corrected corner is small
because it is essentially a few labs that correct as a matter of protocol. **The shape is wrong; the length mostly is not.**
That is a specific, useful distinction for any figure.

**Diameter is known to be unreliable, and was excluded from the field's own
benchmarks for that reason.** Gillette, Brown & Ascoli, *Neuroinformatics*
9(2–3):233–245, 2011, doi:10.1007/s12021-011-9117-y: "Diameter evaluation is
highly subjective at resolutions used for full neuronal arbor reconstruction,
and was not considered in the DIADEM competition." Polavaram et al., *Front
Neuroanat* 8:138, 2014, doi:10.3389/fnana.2014.00138, excluded all
diameter-derived measures for "strong dependence on imaging resolution, optical
magnification, and other experimental details causing excessive inter-laboratory
variability". Blackman et al., *Front Neuroanat* 8:65, 2014,
doi:10.3389/fnana.2014.00065, reconstructed the same eight cells two ways and
got **1.80 ± 0.15 µm vs 0.91 ± 0.09 µm on visually matched segments** (p<0.001)
— a factor of two between two competent light-microscopy pipelines on the same
tissue — with simulated EPSP peaks of 6.27 vs 15.65 mV as a consequence.

**There is no single true morphology.** Three experts tracing the same dendrite
agreed to an intersection-over-union of **0.470 ± 0.071**, and one person
re-tracing after a fortnight agreed with themselves 87.5% (Fernholz, Guggiana
Nilo, Bonhoeffer & Kist, *PLoS Comput Biol* 20(2):e1011774, 2024,
doi:10.1371/journal.pcbi.1011774). Across BigNeuron's benchmark the best
automatic tracers differed from the human gold standard in a median 18% of
their structure and the median algorithm in 44% (Manubens-Gil et al., *Nat
Methods* 20(6):824–835, 2023, doi:10.1038/s41592-023-01848-5). Human agreement
is good on sparse isolated axons and poor on dense tissue: trace-length
agreement 0.995 vs 0.838 (Gala, Chapeton, Jitesh, Bhavsar & Stepanyants,
*Front Neuroanat* 8:37, 2014, doi:10.3389/fnana.2014.00037).

**The Allen coordinates are not shrinkage-corrected, and this is now settled.**
The technical white paper (June 2018, v.7) uses the word "shrinkage" once, to
say soma markers "may be used to track tissue shrinkage" — it describes no
correction. Gouwens et al. 2019 handled z-compression by *excluding* z-derived
features from their classification, and restored volumes only as a robustness
check, publishing the per-cell adjustments in a supplementary spreadsheet
rather than in the database. A correction is applied in the later Patch-seq
pipeline — per cell, from the soma-to-cut-surface distance, plus a tilt
correction — in Lee et al., *eLife* 10:e65482, 2021, doi:10.7554/eLife.65482.
**Allen SWC files as distributed are uncorrected.** Any Stage 3 figure using
them inherits a z axis that is wrong by roughly a factor of two.

**Which cells get drawn is a filtered sample.** The Allen Institute
reconstructed 461 of 1,938 cells that had already passed electrophysiology QC —
23.8% — and states the exclusions: "lack of healthy and/or intact axon (aspiny
neurons only)" and "already having a large number of neurons (n>30) with a
similar morphology (spiny neurons only)" (Gouwens et al. 2019, above). The
second is a deliberate quota that makes the set intentionally unrepresentative
of cell-type abundance. Mohan et al. 2015 rejected about 80% of recovered human
neurons, "mainly because of obvious truncation of the apical dendrite". And
only 21% of the reconstructions identified in the published literature are
shared at all (Halavi, Hamilton, Parekh & Ascoli, *Front Neurosci* 6:49, 2012,
doi:10.3389/fnins.2012.00049); requests for the rest go unanswered ~70% of the
time (Akram et al., *Sci Data* 5:180006, 2018, doi:10.1038/sdata.2018.6).

**Spines are absent from the format, and they are about half the membrane.**
SWC has no representation for a spine. Eyal et al., *eLife* 5:e16553, 2016,
doi:10.7554/eLife.16553, measured the correction on human L2/3 pyramidal cells
from >8,900 fully reconstructed spines (the spine data is Benavides-Piccione
et al., *Cereb Cortex* 23(8):1798–1810, 2013, doi:10.1093/cercor/bhs154):
**F = 1.78–2.39 across four cortex-and-donor combinations, mean 1.946**, and
they model with F = 1.9 — "implying that almost 50% of the dendritic membrane
area in L2/3 neurons are in dendritic spines". That is a membrane-area share of
**44–58%**, and it is applied only beyond 60 µm from the soma, because proximal
dendrites are sparsely spiny. For Purkinje cells the factor is about 3: Rapp,
Segev & Yarom, *J Physiol* 474(1):101–118, 1994,
doi:10.1113/jphysiol.1994.sp020006, put ~100,000 of ~150,000 µm² of membrane in
spines, **66.7%** — though from assumed spine size and density rather than
measured areas.

Two cautions. The mouse F in Eyal et al. is *assumed equal to the human value*,
not measured. And Megías et al., *Neuroscience* 102(3):527–540, 2001,
doi:10.1016/S0306-4522(00)00496-6, which is often reached for here, contains no
F value at all — it is the source for *where* spines are (68.5% of the CA1 tree
is densely spiny, proximal dendrites are not), which is what justifies applying
the factor by distance rather than uniformly.

## 6. The signalling numbers, if Stage 2 wants them

Held here because they are well-sourced and would otherwise be re-researched.
They support a section, not a page.

| Quantity | Value | Source |
|---|---|---|
| AP initiation site | 35.6 ± 2.3 µm out the axon, not the soma | Palmer & Stuart 2006, doi:10.1523/JNEUROSCI.4812-05.2006 |
| AIS leads soma | 150 ± 10 µs | same |
| Transmitter release after presynaptic AP onset | **150 µs** at physiological temperature | Sabatini & Regehr, *Nature* 384(6605):170–172, 1996, doi:10.1038/384170a0 |
| Whole local cortical connection, spike → EPSP | **1.7 ± 0.9 ms** at 32–34 °C | Markram, Lübke, Frotscher, Roth & Sakmann, *J Physiol* 500(2):409–440, 1997, doi:10.1113/jphysiol.1997.sp022031 |
| Synaptic delay, frog NMJ at 20 °C | minimum **0.4–0.5 ms**, modal **~0.75 ms** | Katz & Miledi, *Proc R Soc Lond B* 161(985):483–495, 1965, doi:10.1098/rspb.1965.0016 |
| AP half-width at 35–37 °C | regular-spiking **0.80 ± 0.18 ms**, fast-spiking **0.32 ± 0.10 ms** | McCormick, Connors, Lighthall & Prince, *J Neurophysiol* 54(4):782–806, 1985, doi:10.1152/jn.1985.54.4.782 |
| Synaptic contacts per connection | 5.5 ± 1.1 | same |
| Membrane time constant, L5, 35–37 °C | 12.4 ± 0.5 ms | Stuart & Spruston, *J Neurosci* 18(10):3501–3510, 1998 |
| Somatopetal attenuation reaches 50% | ~332 µm from soma | same |
| Distal apical EPSP attenuation | >40-fold | Williams & Stuart, *Science* 295(5561):1907–1910, 2002, doi:10.1126/science.1067903 |
| Conduction velocity, thin axon in slice at 23–25 °C | 0.24–0.38 m/s | Kress et al., *J Neurophysiol* 100(1):281–291, 2008; Schmidt-Hieber, Jonas & Bischofberger, *J Physiol* 586(7):1849–1857, 2008 |
| Conduction velocity, cortical axons in vivo, awake | 1.4–3.5 m/s | Swadlow, *J Neurophysiol* 59(4):1162–1187, 1988 |
| Macaque pyramidal tract | median 47 m/s; **52% of axons <1 µm** | Firmin et al., *J Neurophysiol* 112(6):1229–1240, 2014, doi:10.1152/jn.00720.2013 |

Two notes on that table. The textbook "0.5 ms synaptic delay" is the **upper
bound of a minimum, measured in frog neuromuscular junction at 20 °C in
low-calcium Ringer**; the modal delay in that same preparation is 0.75 ms, and
the fast central number is Sabatini & Regehr's 150 µs. They are three different
quantities and are routinely conflated. The McCormick half-widths were recorded
at 35–37 °C, so unlike most of the slice numbers here they need no temperature
correction — which is why they are usable and the 23 °C conduction velocities
are not.

**The textbook account of signal flow is documented as wrong, in the abstracts
of the papers that overturned it.** Stuart & Sakmann 1994 open by naming the
passive-dendrite view as the thing they are refuting. Add: bAPs fail at branch
points so neighbouring dendritic regions see different signals (Spruston et al.
1995); dendritic Ca spikes that never reach the soma (Schiller et al. 1997);
two initiation zones coupled within a few milliseconds (Larkum, Zhu & Sakmann,
*Nature* 398(6725):338–341, 1999, doi:10.1038/18686); NMDA spikes amplifying
somatic response 226 ± 46% (Schiller, Major, Koester & Schiller, *Nature*
404(6775):285–289, 2000, doi:10.1038/35005094); graded dendritic Ca APs in human
cortex performing a computation "conventionally thought to require multilayered
networks" (Gidon et al., *Science* 367(6473):83–87, 2020,
doi:10.1126/science.aax6239); analog signals travelling along axons alongside
spikes (Alle & Geiger, *Science* 311(5765):1290–1293, 2006,
doi:10.1126/science.1119055); and axons that leave from a dendrite rather than
the soma (Thome et al., *Neuron* 83(6):1418–1430, 2014,
doi:10.1016/j.neuron.2014.08.013).

**An animation of a signal flowing dendrite → soma → axon depicts a view the
field abandoned in 1994.** If Stage 2 proposes one, that is the constraint.

## 7. Traps found

1. **The truncation factor I can compute is not a truncation factor.** Allen
   mouse spiny cells have 41 µm of axon and MouseLight cells have 96 mm, but
   they are different populations, labs, species-region mixes and protocols.
   The ratio is a cross-dataset comparison and must be labelled as one. The
   matched, published number is van Pelt 2014's 48–49% of *intracortical* axon
   in a 300 µm slice. **No published paired slice-versus-whole-brain axonal
   length for the same cell type exists** — that gap was searched for and not
   found.
2. **"Textbook diagrams are inaccurate" has not been published and must not be
   asserted as a finding.** A search of the biomedical literature for any
   quantification of textbook neuron-diagram accuracy returned nothing. That is
   "not found in PubMed", not "shown not to exist" — education and
   science-communication databases were not swept. The defensible framing is
   the one in §2: the drawing requires 4.5 orders of magnitude, a page holds
   three, and the primary literature repeatedly names the textbook account as
   what it is overturning. Both of those are sourced. An accuracy audit of
   diagrams is not, and would be this project's own claim to defend.
3. **Do not draw MouseLight or FlyCircuit cells at "true thickness".** The
   thickness is a placeholder. Any rendering that varies their line width is
   inventing data. This is the trap most likely to produce exactly the
   fabricated number the site rules exist to prevent.
4. **Do not treat "Axon Complete" as measured.** NeuroMorpho defines physical
   integrity as the depositor's own judgement with no quantitative threshold,
   and for a slice reconstruction "complete" can only mean complete within the
   slice. The `domain` and `physical_Integrity` fields also disagree with each
   other by about 4% on which cells have an axon. [computed]
5. **The CNG file is re-oriented, and it is not the depositor's file.** Soma
   at origin, axes rotated onto the principal components of the coordinates, so
   a figure asserting anatomical orientation from a CNG file is wrong. The
   source version is at `/dableFiles/<archive>/Source-Version/<name>.swc`
   (that exact capitalisation; the other four variants tested return 404) and
   is the file to use when orientation or the depositor's own radii matter.
6. **Shrinkage breaks shape, not length.** A 63% z collapse changes total
   dendritic length by 11%. Any claim about a cell's 3D form needs the
   correction; a claim about its total length mostly does not. Getting this
   backwards in either direction is a real error.
7. **MouseLight's licence is unresolved.** The figshare deposits are CC BY-NC
   4.0; NeuroMorpho redistributes the same archive under its site-wide CC BY
   4.0. Those conflict, and the site is a commercial-adjacent publication.
   Stage 3 must resolve it or use the `Peng` fMOST archive instead. The Allen
   terms are non-commercial with an explicit carve-out for journalistic
   publication with citation, which appears to cover this use but is a
   judgement, not a permission.
8. **Every cross-preparation comparison needs its temperature and protocol.**
   In vitro conduction velocities at 23–25 °C and in vivo velocities at 37 °C
   differ by an order of magnitude for nominally similar axons, and no verified
   Q10 for CNS conduction exists. Do not print a single "speed of a nerve
   impulse".
9. **Spines are not in the file.** A membrane-area figure computed from SWC
   understates the real value by F = 1.9 in cortical pyramidal cells (44–58% of
   the membrane is in spines) and by about 3 in Purkinje cells — and the factor
   applies only beyond ~60 µm from the soma, so a flat doubling is itself
   wrong. See §5.
10. **Allen files are not shrinkage-corrected.** Their z axis is compressed by
   roughly a factor of two and no correction is applied to the distributed
   coordinates (§5). Anything drawn from them in 3D, or any depth measurement,
   inherits that.
11. **A metadata flag is not a measurement, and this project's whole subject is
   the difference.** Both times I trusted a NeuroMorpho flag without opening the
   files, it was misleading in the direction that flattered the story: the
   "Diameter" flag passes files with three quantised values (§4c, §4d), and
   "Axon Complete" is a depositor's unquantified judgement (trap 4). Every
   number that reaches a page must be computed from the files. The scripts here
   do that; a Stage 3 generator must keep doing it.

## 8. Reproducing the checks

```
python census.py                    # all 298,339 records -> census.json, neurons.csv.gz  (~11 min)
python crosstab.py                  # the joint counts in 4a
python fetch_allen.py               # 527 SWC + allen_index.csv   (well_known_file_type_id 303941301)
python fetch_neuromorpho.py MouseLight 200
python swc_check.py allen=swc/allen mouselight=swc/mouselight
python split_check.py               # class split + the 0.1144 um clamp
python source_check.py mouselight 10 # does CNG standardisation invent diameters?
python diameter_audit.py 12         # is the 'Diameter' flag worth anything?
python projection_check.py          # long axon and real diameter in one file?
python scale_check.py               # dynamic range arithmetic
python feas_fig.py                  # feas_neuron.png
```

No API key at any step. `census.py` is the only slow one. The morphometry is a
plain SWC parse — segment length is the Euclidean distance between a point and
its parent, summed by structure type — with no library dependency beyond numpy,
which is deliberate: a Stage 3 generator should be able to carry it unchanged.

## 9. Kill criteria

None met, but the first one was close enough to be worth stating.

- *Data does not exist or is not obtainable* — **no.** Free, public, complete
  enumeration done today. But the data needed for the project **as briefed** —
  one reconstruction complete enough to draw at true proportions — genuinely
  does not exist, and finding that out is the project.
- *Data supports only a weaker claim, and the weaker claim is not interesting*
  — **no.** The weaker claim is the more interesting one, and it is measured
  rather than argued.
- *The honest version is something a reader already knows* — **no.** A reader
  does not know that the axon is fourteen times the dendritic tree, that the
  standard published picture of a pyramidal cell contains 41 µm of axon, or
  that half the thickness values in the best morphology database are a
  constant standing in for the diffraction limit.
- *Sources are copyright-locked* — **no**, with the MouseLight licence conflict
  in §7 to resolve at Stage 3.

## 10. Provenance, and what has been verified

Every number marked **[computed]** was produced in this folder by the scripts in
§8 from files downloaded on 5 September 2026, and I ran and read all of them.
The census is a complete enumeration of the archive, not a sample. Where a
computed claim was checked against my own reasoning and failed, the failure is
recorded rather than removed — §4c and §4d.

The literature in §5 and §6 was gathered by research agents that fetched and
quoted the sources, and NeuroMorpho's published totals were cross-checked
against my independent API census, which matched exactly (298,339). Five items
were flagged as second-hand on the first pass and have since been checked
against the sources; all five are resolved.

| Item | Status |
|---|---|
| Spine surface-area factors | **Verified and corrected.** Eyal et al. 2016 give F = 1.78–2.39, mean 1.946. The membrane share is **44–58%**, not the 49–58% first reported to me. Purkinje ≈3 / 66.7% from Rapp et al. 1994. Megías et al. 2001 contains no F value and must not be cited for one. |
| Marx et al. 2012 shrinkage factors | **Not retrievable** — closed access, no PMC copy, no archived PDF; the abstract confirms factors exist but gives none. The ×1.1/×2.1 values are quoted verbatim and attributed to it by the same senior author in Emmenegger et al. 2018. Usable with that attribution; **not** usable as a universal constant (other protocols give 1.5–1.7). |
| Katz & Miledi 1965 synaptic delay | **Verified from the scanned paper.** Minimum 0.4–0.5 ms, modal ~0.75 ms, frog sartorius NMJ at 20 °C in low-calcium Ringer. The paper gives no mammalian or 37 °C value. |
| Gasser/Erlanger velocity ranges | **Not traceable.** The A/B/C and Aα–Aδ scheme is Erlanger & Gasser's, consolidated in a 1937 monograph; the tabulated m/s bins do not correspond to any single primary measurement and their boundaries differ between textbooks. Do not print them as measured constants. |
| Allen shrinkage correction | **Confirmed: none applied to the distributed files.** See §5. The correction exists only downstream in the Patch-seq pipeline (Lee et al. 2021). |
| McCormick et al. 1985 temperature | **Verified: 35–37 °C**, guinea pig, in vitro. Half-widths 0.80 ± 0.18 and 0.32 ± 0.10 ms confirmed from Table 1. Now used in §6. |

Absences worth recording, because a later session will otherwise search for
them again: no paired slice-versus-whole-brain axon length for one cell type;
no published audit of default, clamped or quantised radii in deposited
reconstructions (the 70.1%, the 50.9% clamp and the §4d quantisation appear to
be the first); no published measurement of light-microscopy diameter error
against electron-microscopy ground truth on the same identified neurite; no
verified Q10 for CNS axonal conduction; and no quantification of textbook
diagram accuracy in the biomedical literature, though education and
science-communication databases were not swept and should be before §7 trap 2
is relied on.
