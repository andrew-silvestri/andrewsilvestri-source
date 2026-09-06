# Research and feasibility: beauty in research

Stage 1 of `00 PUBLISH/prompts/NEW_PROJECTS.md` §1. Written 5 September 2026.
Lives in `03 RESEARCH/beauty/` with the pilot computation (`pilot/`, scripts
`01_parse_iucn.py` through `04_analyze.py`, outputs `pilot_table.csv` and
`pilot_scatter.png`, provenance in `pilot/README.md`), the raw literature
verification (`literature_notes.md`) and the raw data-access verification
(`data_notes.md`). Nothing in `00 PUBLISH` was touched. No design decisions
are made here.

## 1. Verdict

**The project exists, and the honest version is stronger than the brief's
loud version.** The bias is an established, repeatedly replicated finding with
species-level models behind it. The most surprising and best-supported result
is not "pandas get more than frogs" but that, once you know a species' taxon,
size, range and how long it has been described, *its extinction risk adds
nothing* to how much it gets studied. In several models the sign is negative.

Supportable claim, one sentence: *Across vertebrates, research effort and
conservation spending per species track what people find appealing (body
size, measured attractiveness, online attention) and what is easy to study
(range size, years since description, the research capacity of the countries
it lives in) far more than its Red List status, which is null or negative in
most species-level models; the groups that carry most of the extinction
burden (amphibians, reptiles, invertebrates, plants) receive an order of
magnitude less attention per threatened species than birds and mammals.*

Not supportable as a finding: that beauty *determines* funding. Every dataset
is observational, the aesthetic proxies differ between studies, and
taxonomic group absorbs 60–75% of the variance in every model that fits one.
The page can say "here is the gap, and here is how much of it appeal and size
account for after size, range and description date are held fixed". It cannot
say "beauty causes neglect".

Not supportable as a finding: the forecast. "How it will harm us" is
argument. What is documented is narrower (§2.5): most Data Deficient
amphibians and mammals are predicted to be threatened, most threatened
tetrapods have no demographic data, and a large share of extinctions are of
species never described. The canonical anecdote of a place lost before it was
studied (Centinela) has been refuted, and the canonical Australian cases were
monitored for years and lost through inaction, not ignorance.

## 2. The primary literature

Full citations with DOIs, sample sizes and the numbers that could not be
verified from open text are in `literature_notes.md`. Journals and years were
checked; several in the brief's implied summary were wrong (Donaldson 2016 is
in *FACETS*, not *Conservation Biology*; dos Santos 2020 is *Animal
Conservation*; Adamo is 2021; Santangeli's bird attractiveness paper is 2023
in *npj Biodiversity*; Jarić's "societal extinction" is 2022).

### 2.1 The bias exists and has not narrowed

- Clark & May 2002, *Science* 297:191. The founding letter. Vertebrates
  grossly over-represented in conservation journals relative to species
  richness. Paywalled; its percentages must be read from the PDF before
  quoting.
- Donaldson et al. 2016, *FACETS* 1:105. Over 10,000 Red-Listed animal
  species against Web of Science counts; extreme skew toward threatened
  vertebrates over threatened invertebrates in both terrestrial and aquatic
  habitats.
- Titley, Snaddon & Turner 2017, *PLoS ONE* 12:e0189577. 526 sampled
  biodiversity papers; bias stronger in highly cited papers.
- Troudet et al. 2017, *Sci Rep* 7:9132. 626 million GBIF records across 24
  classes; the data gap correlates with societal preference, not with
  research activity.
- Rosenthal et al. 2017, *Anim Behav* 127:83. Chordates are about 70% of
  recent animal-behaviour papers and under 7% of animal species.
- Tam et al. 2022, *GigaScience* 11:giac074. 7,521 mammals; one third have
  an h-index of zero. Mammola et al. 2023, *eLife* 12:RP88251. 3,019
  species across 29 phyla; 52% have zero papers. Caldwell et al. 2024,
  *Cell Rep Sustain* 1:100082. 17,502 articles in four journals, 1980–2020;
  the bias is entrenched, not shrinking.

### 2.2 Funding tracks charisma, not priority rank

- Metrick & Weitzman 1996, *Land Economics* 72:1. US Endangered Species Act
  spending FY1989–91: "visceral" traits (body length, mammal or bird) outweigh
  "scientific" traits (endangerment rank, taxonomic uniqueness); over half of
  spending to ten species. The origin of the whole literature.
- Restani & Marzluff 2002, *BioScience* 52:169. Spending tracks the agency's
  own recovery priority rank poorly; politics and litigation drive allocation.
- Dawson & Shogren 2001, *Land Econ* 77:527. Panel of 241 vertebrates
  1993–96 with fixed effects: only time-invariant traits such as charisma can
  explain outlays.
- Bellon 2019, *Environ Econ Policy Stud* 21:399. FY2013 federal spending on
  listed vertebrates: priority rank non-significant, charisma (Google hits)
  significant. Coefficients paywalled.
- Davies et al. 2018, *PLoS ONE* 13:e0203694. 36,873 vertebrates, Google
  Trends 2004–14, aid flows: 3,789 Critically Endangered or Endangered
  species had negligible search interest; 57 of the 100 most searched are
  mammals, none are amphibians; interest predicts aid.
- Mammides 2019, *Biodivers Conserv* 28:1291. EU LIFE: over 800 species
  projects since 1992, about half on birds, about 7% on invertebrates or
  plants; birds and mammals take 75% of the species budget.
- Guénard et al. 2025, *PNAS* 122:e2412479122. About 14,600 conservation
  projects over 25 years worldwide: about 6% of threatened species ever
  funded; 29% of funds went to Least Concern species. Its Dataset S1 is
  downloadable (§3.5).
- Gerber 2016, *PNAS* 113:3563. Less than a quarter of the money ESA
  recovery plans say they need is allocated. No charisma test; useful for the
  scale of the shortfall.

### 2.3 Charisma is measurable and is orthogonal to threat

- Albert, Luque & Courchamp 2018, *PLoS ONE* 13:e0199149; Courchamp et al.
  2018, *PLoS Biol* 16:e2003997. The twenty most charismatic species are
  large exotic mammals; the top ten are all threatened; their ubiquity as
  images creates "virtual populations" that mask decline.
- Colléony et al. 2017, *Biol Conserv* 206:263. 10,066 zoo-adoption donors:
  IUCN status did not predict which species people chose or how much they
  gave; charisma and phylogenetic closeness did.
- Frynta and colleagues (Marešová & Frynta 2008; Frynta et al. 2010, 2013;
  Landová et al. 2018). Rated attractiveness of boas, parrots and mammal
  families predicts which species zoos hold and how many; rarity and IUCN
  status are consistently non-significant.
- Santangeli et al. 2023, *npj Biodiversity* 2:20. 6,212 raters, over
  400,000 scores, 11,319 bird taxa; attraction to small, vivid, ornamented,
  wide-ranging species. The species-level scores are deposited (§3.4).
- Miralles, Raymond & Lecointre 2019, *Sci Rep* 9:19555. Empathy toward a
  species falls with evolutionary divergence time.
- Berti et al. 2020, *Biol Conserv* 251:108790. Body size is a good charisma
  proxy across 13,680 species; the compilation is on GitHub (§3.4).
- Adamo et al. 2021, *Nature Plants* 7:574. 113 Alpine plants: flower colour,
  conspicuousness and range predict research attention; rarity does not.
- A 2026 *Current Biology* paper on beauty bias in butterfly research and EU
  protection (doi 10.1016/j.cub.2026.07.049) was found but its authorship
  and abstract were not fully verified. Check before citing.

### 2.4 The confounders, and who has partitioned them

This is the thread that decides whether the honest claim is defensible. Ten
species-level multivariable models were found (details and coefficients in
`literature_notes.md`, thread 4). The pattern:

- **Phylogeny or taxonomic group** absorbs most of the variance wherever it
  is fitted: 74% in birds (Ducatez & Lefebvre 2014), 66% in turtles (Ducatez
  & DeVore 2026), heritability 0.64 in mammals (Tam et al. 2022).
- **Range size**, **body mass**, **years since description** and
  **range-country research capacity** are the consistent positive predictors
  (Brooke et al. 2014; Fleming & Bateman 2016; dos Santos et al. 2020;
  Guedes et al. 2023; Machado et al. 2023).
- **IUCN threat status** is non-significant in six of these models, weak in
  one, negative in two (Ducatez & Lefebvre: Least Concern birds have twice
  the papers of threatened ones; Tam et al.: research declines as risk
  rises), and positive only in reptiles and for "assessed versus unassessed".
- **A named appeal proxy** has been fitted in only three: flower colour
  (Adamo 2021), colourfulness (Mammola 2023, affects public attention but not
  scientific attention) and Google Trends interest (Tam 2022, where it is the
  single strongest fixed effect).

So the claim "appeal explains more than threat" is supported, but by few
studies with different proxies. The claim "threat explains nothing once you
know the taxon" is supported by nine of ten. That asymmetry should shape what
the page leads with.

### 2.5 Consequences: documented, not documented, refuted

Documented:
- Bland et al. 2015, *Conserv Biol* 29:250: 64% of Data Deficient mammals
  predicted threatened. Borgelt et al. 2022, *Commun Biol* 5:679: 85% of
  Data Deficient amphibians likely threatened.
- Conde et al. 2019, *PNAS* 116:9658: 1.3% of 32,144 tetrapods have
  comprehensive demographic data; 65% of threatened tetrapods have none.
- Tedesco et al. 2014, *Conserv Biol* 28:1360: undescribed species are
  15–59% of all extinctions. Régnier et al. 2015, *PNAS* 112:7761: a
  land-snail sample implies about 130,000 species already lost against 799
  listed. Cowie et al. 2022, *Biol Rev* 97:640: 7.5–13% of the roughly two
  million known species extinct since 1500, against 0.04% on the Red List.
- Eisenhauer et al. 2019, *Nat Commun* 10:50: about 0.8% of insects assessed.
- Woinarski et al. 2017, *Conserv Biol* 31:13: three recent Australian
  extinctions, explicitly citing inadequate resources for non-charismatic
  species.

Refuted or misframed:
- "Centinelan extinction" (Dodson & Gentry 1991; Wilson 1992) is refuted by
  White et al. 2024, *Nature Plants* 10:1627: 99% of Centinela's supposed
  microendemics have been collected elsewhere. It is now an example of
  under-sampling producing a false conclusion, which is a different and
  better point.
- The Christmas Island pipistrelle was monitored for 15 years (Martin et al.
  2012, *Conserv Lett* 5:274); the failure was decision delay. "Monitored to
  extinction", not "unstudied".
- Costello, May & Stork 2013, *Science* 339:413 is an optimistic paper
  (most species will be described before they go extinct) and should not be
  cited as alarm.

### 2.6 Zoos

Conde et al. 2013, *PLoS ONE* 8:e80311: 3,955 species in 837 zoos, 23%
threatened, only 2 of 59 orders hold more threatened species than random
would. Biega et al. 2019, Wahle et al. 2025, Lennon et al. 2026 confirm the
pattern for birds and UK collections. The Frynta papers are the only ones
regressing holdings on measured attractiveness. The zoo thread is citable but
not computable here (§3.6), so it is a paragraph, not a figure.

## 3. The primary data

Every source below was hit on 5 September 2026; exact URLs, HTTP codes and
sample responses are in `data_notes.md`.

### 3.1 Threat status: IUCN Red List

- Group-level tables (1a by class, 1b by order and family, 2 by Red List
  version 1996–2026): free, no login, **PDF only**, Cloudflare in front, so a
  browser User-Agent and PDF table extraction are required. The pilot did
  this without trouble.
- Species-level: API v4 needs a token requested through a web form (reported
  turnaround hours to two days). The spec has `/taxa/class/{name}` paginated
  at 100 per page, so a whole class is a few hundred calls. Advanced search
  export needs a manual login.
- **Licence trap.** The terms forbid reposting or redistributing Red List
  data without written permission. This site ships payloads and a download
  archive. A species-level table carrying IUCN categories cannot go in the
  archive. Aggregates, regression outputs and figures are the safe output.
  ReptTraits (CC BY) and Berti's compilation carry IUCN categories already,
  which sidesteps the API but not the redistribution question.

### 3.2 Research effort

- OpenAlex (CC0). **Changed in February 2026:** a free self-serve key is
  now needed for real use ($1 per day of usage, about 10,000 filter calls),
  and `search=` is now full-text. Per-species `title_and_abstract.search`
  filter calls cost $0.0001 each, so 10,000 species is one day of the free
  tier. Confirmed counts: lion 3,459 title-and-abstract works, purple frog
  138 full-text works.
- PubMed E-utilities (free, no key) as a cross-check; lion 701, one obscure
  threatened frog 6. MeSH organism tree gives class-level counts.
- Web of Science and Scopus are paid. Every paper in §2 that used them
  cannot be reproduced exactly; OpenAlex is the reproducible substitute.

### 3.3 Public attention

- Wikipedia pageviews API: free, no key, **CC0**, per-article monthly series
  from July 2015. Giant panda about 130,000 views per month; purple frog
  about 4,500. This is the proxy Roll 2016 and Mittermeier 2019/2021 used.
- iNaturalist and GBIF observation counts: free, no key. GBIF is 63% eBird
  records, so it measures birders, not research. Note GBIF has no Reptilia
  taxon; sum Squamata, Testudines and Crocodylia.

### 3.4 Appeal scores

- Santangeli et al. 2023 species-level predicted attractiveness for 11,319
  bird taxa: figshare, CC BY 4.0, 687 KB. The best species-level
  attractiveness dataset that exists.
- Berti et al. 2020 compilation of 13,687 species (reptiles from Roll 2016,
  mammals from Macdonald 2015, birds from Garnett 2018, Flickr from Willemen
  2015) with IUCN class and mass: GitHub, no licence file. Usable for
  analysis; ask before redistributing.
- Albert et al. 2018 raw survey (20,037 rows, common names, no licence file):
  covers about twenty species, so it is illustration, not a covariate.
- Frynta lab ratings are not deposited.

### 3.5 Funding

- US Fish and Wildlife Service expenditure reports FY1989–FY2022, per
  species, public domain, **PDF only**, 20–31 MB each. Gerber's 2016
  compilation (1,124 rows) is a CSV on Defenders of Wildlife's GitHub without
  a licence file. A full series is a PDF-extraction job of about thirty
  reports.
- Guénard et al. 2025 Dataset S1: 14,612 projects with funder, species name,
  group and amount, downloadable from Europe PMC (3.4 MB). This is the one
  global per-species funding table.
- EU LIFE: the Commission's own site returned HTTP 500 on test day; the
  Zenodo mirror (CC BY 4.0, extracted July 2022) has project budgets and
  target species, budget apportioned per project, not per species.
- NSF award API works but has no taxon field.

### 3.6 Zoos

Species360 ZIMS is member-only. Zootierliste has no export or reuse terms.
EAZA publishes a programme list PDF (about 475 programmes). Conde's
supplements are class and order counts, not species lists. **There is no
free species-level captive-collection dataset.** This sub-claim is
literature-only.

### 3.7 Confounders

All one-click downloads, all CC BY 4.0 unless noted: PanTHERIA (5,416
mammals, mass and range area), COMBINE (6,263 mammals with an IUCN-name
crosswalk), AVONET (11,009 birds, mass and range size), AmphiBIO (6,776
amphibians, mass), ReptTraits (12,060 reptiles, mass, description year, IUCN
category), Amniote Database (21,322 rows). Description year for anything:
Catalogue of Life API, CC BY. Range polygons from IUCN need a manual login
and cannot be redistributed; the trait tables' range fields are the fallback.

### 3.8 What that adds up to

Birds are the one class where every term of the honest claim has a free,
licensed, species-level source: threat (API token), papers (OpenAlex),
attention (Wikipedia), rated attractiveness (Santangeli), mass and range
(AVONET), description year (Catalogue of Life). Mammals are nearly as
complete but with a weaker appeal proxy (Berti's compilation or Wikipedia
alone). Amphibians and reptiles have traits and Wikipedia but no rated
attractiveness. Invertebrates and plants have neither a usable threat
denominator nor an appeal score. Funding at species level exists for the US
(PDF extraction) and for the Guénard global table.

## 4. Feasibility check: is the gap real at the coarse level?

The pilot joined IUCN Red List 2026-1 Table 1a (20 groups) to OpenAlex works
2015–2024 matching the group name with a biology or environment primary
topic, and to GBIF occurrence counts. Scripts, queries and every URL are in
`pilot/README.md`; the table is `pilot/pilot_table.md`.

Within vertebrates, where conservation abstracts reliably name the class,
the signal is clean. OpenAlex works per threatened species, 2015–2024:

| Group | Threatened spp | Works per threatened sp |
|---|---|---|
| Birds | 1,256 | 102 |
| Fishes | 4,168 | 57 |
| Mammals | 1,372 | 39 |
| Reptiles | 1,865 | 11 |
| Amphibians | 2,940 | 9 |

Amphibians have the highest threat rate of any fully assessed group (41%
best estimate) and a tenth of the attention per threatened species that
birds get. Reptiles sit beside them.

Outside vertebrates the proxy fails, and the pilot says so rather than
reporting the numbers: flowering plants score 0.6 works per threatened
species because papers on rice or Arabidopsis never say "angiosperm"; fungi
score high because "fungal" is pathology vocabulary; and "threatened" counts
for insects, molluscs and arachnids are artefacts of 1–4% assessment
coverage. The cross-kingdom version of this figure would be a fabrication
dressed as a finding. That is a known trap for this project (§6).

The pilot answers the Stage 1 question: the gap is measurable from free
sources at the group level within vertebrates, and the tools needed for the
species-level version (where charisma and confounders enter) all respond.
The species-level computation itself was not run; it needs an IUCN token,
an OpenAlex key and a Stage 2 decision about which class to fit.

## 5. What a reader already believes, and what this adds

A reader already believes:
- Pandas, tigers and elephants get more attention and money than frogs and
  beetles. True, and not news.
- Conservation funding is inadequate overall. True (Gerber 2016), and not
  news.

What this project can tell them that they do not already know:
- **Being endangered does not buy a species attention.** In nine of ten
  species-level models, Red List status is null or negative once taxon,
  size and range are fixed. The reader expects a bias *toward* the
  charismatic; they do not expect *no* countervailing pull toward the
  endangered. That is the finding to lead with.
- **How much of the gap size and appeal account for**, with the residual
  labelled as unexplained rather than attributed. No popular treatment shows
  the partition.
- **The denominator problem.** The Red List has assessed 78–100% of
  vertebrates and 0.1–4% of everything else, so the extinction burden of the
  neglected groups is invisible in the very statistic used to measure
  neglect. Cowie's 7.5–13% against the Red List's 0.04% is the number a
  reader has not seen.
- **The refutations.** Centinela did not happen as told; the pipistrelle was
  watched to death. A page that corrects the reader's favourite anecdotes
  earns the right to make its own claim.

If the page can only say the first bullet under "already believes", it is
not worth building. It can say all four under "adds".

## 6. Traps found

1. **Cause versus association.** Every dataset is observational; every
   appeal proxy is itself correlated with size, range and familiarity. The
   page reports partitions of variance, not effects of beauty.
2. **Cross-kingdom publication counts.** Name-based literature proxies fail
   for plants, insects and fungi (§4). Any figure spanning kingdoms needs a
   taxon-resolved literature source, which does not exist for free.
3. **The Red List denominator.** "Share of threatened species" for
   under-assessed groups measures IUCN effort, not biology. The page must
   show assessment coverage beside every threat number or not show the
   number.
4. **IUCN redistribution terms.** Species-level Red List categories cannot
   go in the site's download archive. Decide in Stage 2 what is published as
   data and what only as figures and aggregates.
5. **OpenAlex changed under the literature.** It is now keyed and metered,
   and `search=` became full-text search in 2026. The pilot's queries use
   the title-and-abstract filter and record every URL; a rebuild must pin
   the same filter.
6. **GBIF has no Reptilia.** Class-level reptile counts silently return
   zero unless the three current classes are summed.
7. **Paywalled coefficients.** Clark & May's percentages, Bellon's and
   Restani & Marzluff's coefficients, dos Santos's relative importances and
   Adamo's effect sizes were not read from full text. None goes on a page
   until it has been.
8. **The anecdotes.** Centinela is refuted and the pipistrelle was
   monitored. Using either in the brief's form would repeat an error the
   literature has already corrected.
9. **Wikipedia pageviews are English Wikipedia.** They measure Anglophone
   attention. Roll and Mittermeier used the same proxy; say so.
10. **The forecast half of the brief.** "How it will harm us" has no dataset.
    It is argument and gets labelled as such or is cut.

## 7. Kill criteria

Checked against the list at the end of `NEW_PROJECTS.md`:

- *Data does not exist or is not obtainable.* Not triggered. Every term of
  the honest claim has a free source for at least one vertebrate class.
- *Data supports only a much weaker claim that is not interesting.* Not
  triggered. The weaker claim (threat status adds nothing) is the more
  interesting one.
- *Reader already knows the honest version.* Not triggered (§5).
- *Only copyrighted sources.* Not triggered. The bibliometric substitutes
  for Web of Science are open, and the trait, attention and attractiveness
  data are CC0 or CC BY.

Two sub-claims from the brief die here: the zoo-composition figure (no free
species-level data; literature only) and the forecast of harm (no data;
argument only).

## 8. Reproducing the check

```
cd "03 RESEARCH/beauty/pilot"
python 01_parse_iucn.py     # reads iucn_table1a_2026-1.pdf -> iucn_table1a.csv
python 02_openalex.py       # ~80 filter calls, keyless tier -> openalex_counts.csv
python 03_gbif.py           # taxonKey lookups + counts -> gbif_counts.csv
python 04_analyze.py        # -> pilot_table.csv, pilot_table.md, pilot_scatter.png
```

Python 3.12, pandas, matplotlib, pypdf; `urllib` only. Group definitions and
search strings live in `groups.py`. Counts drift as OpenAlex and GBIF update;
the run date is in `run_log_04.txt`.

## 9. Open before Stage 2

These are facts Stage 2 needs, not proposals:

- An IUCN API token and an OpenAlex key have not been requested. Both are
  free; the IUCN one takes up to two days.
- The species-level model has not been fitted. Its feasibility rests on the
  sources in §3.8 responding, which they do, not on a result.
- Which class to fit is a design decision. Birds are the only class with a
  deposited attractiveness score; the brief's mental image is mammals.
- Whether any species-level table can be published at all depends on the
  IUCN terms (§6.4) and on Berti's and Gerber's missing licence files.
