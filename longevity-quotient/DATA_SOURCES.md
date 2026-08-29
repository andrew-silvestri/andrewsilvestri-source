# Where to get more data — a source-by-source survey

Written after the first AnAge merge took the table from 417 to 3,334 species,
and after noticing what that merge did to the composition:

```
merged table by class:
    Aves            1384
    Mammalia        1037
    Reptilia         374
    Actinopterygii   375
    Insecta           19      <- every insect on Earth
    Bivalvia           6
    Cephalopoda        5
    Arachnida          5
```

Nineteen insects. Six bivalves. Five cephalopods. Meanwhile the top of the
quotient ranking is almost entirely invertebrate — *Arctica islandica* (ocean
quahog) at 47×, *Lamellibrachia luymesi* (cold-seep tubeworm) at 23×,
*Lasius niger* (black garden ant) at 29×, *Mesocentrotus franciscanus* (red sea
urchin) at 10×. **The most interesting animals in the model are the ones the
pipeline covers worst**, because AnAge is a vertebrate database with an
invertebrate appendix, and every merge so far has widened that bias rather than
narrowed it.

This document is organised by taxon for that reason. The vertebrate sources are
listed because they are easy and large; the invertebrate sources are listed
because they are the ones that would actually change what the model says.

---

## Part 1 — The invertebrate problem

### SeaLifeBase — the single biggest opportunity

The companion to FishBase for **everything marine that is not a finfish**:
molluscs, crustaceans, echinoderms, cnidarians, worms. Established 2006,
targeting ~240,000 species of the roughly 300,000 known in that category.

It matters here because it is the only large, structured, freely queryable
source covering the phyla where this model's most striking results live. It is
reachable from the same R package as FishBase — `rfishbase` fronts both — so one
loader covers both.

Coverage of longevity specifically is patchier than FishBase's, and much of
SeaLifeBase's depth is in size and distribution rather than lifespan. Expect to
harvest hundreds of usable longevity records rather than tens of thousands. That
is still two orders of magnitude more invertebrates than you have now.

**Verdict: first invertebrate source to add.** Same tooling as FishBase, so the
marginal cost after doing FishBase is nearly zero.

### The Add-my-Pet (AmP) collection — the most underrated source on this list

A Dynamic Energy Budget parameter collection built by ~125 contributors, one
entry per species, giving **250–280 traits per species including lifespan**,
with the referenced underlying data attached. Coverage spans the whole animal
kingdom rather than the vertebrates, and every entry is a fitted energetic model
rather than a scraped number.

Two things make it unusually good for this project. First, its lifespan values
come out of a model fitted to growth and reproduction data, so they are less
hostage to the "who happened to recapture one" problem than a raw maximum.
Second, it carries **ultimate body weight** in the same entry, which is exactly
the mass variable the allometry needs, measured consistently rather than
assembled from twelve sources.

The awkwardness: it is distributed as MATLAB/Octave data structures rather than
a CSV, so the loader is more work than a `read_csv`. You already have Octave
ports elsewhere in this folder, so that is less of an obstacle here than it
would be for most people.

**Verdict: highest quality-per-species of anything on this list.** Worth the
loader.

### The Coral Trait Database

150 traits for scleractinian corals, 56 of them error-checked, validated and
referenced. Focused on shallow-water zooxanthellate reef-builders. There is now
a companion **Octocoral Trait Database** (*Scientific Data*, 2024) covering soft
corals and sea fans.

Relevant to a specific problem you already have. Your four colonial entries —
*Leiopathes glaberrima* (black coral) at 4,265 years, *Orbicella faveolata*
(boulder star coral), *Xestospongia muta* (giant barrel sponge), *Monorhaphis
chuni* (glass sponge) — are currently excluded from the fits and hidden by
default because a colony age is not a lifespan. The coral databases carry growth
rates and colony-level demography, which is the raw material for doing something
more interesting than excluding them: computing a **polyp** turnover rate and
treating the colony as a population rather than an individual.

**Verdict: not a volume play. A way to stop throwing away four of your most
interesting rows.**

### Bivalve sclerochronology — Moss et al. 2016

*Proceedings of the Royal Society B*, "Lifespan, growth rate, and body size
across latitude in marine Bivalvia": a compilation of **1,084 bivalve
populations** with maximum reported lifespans, including at least nine
centenarian taxa. Modal bivalve lifespan is 3 years, and the tail runs to
*Arctica islandica* at 507.

This is a published dataset rather than a maintained database, which means one
download and no updates — but 1,084 populations against your current six
bivalves is a two-order-of-magnitude improvement in the group that currently
holds your single highest quotient. It also carries shell size and growth rate,
so it comes with its own mass proxy and a second regressor.

Bivalve ages are read from annual shell growth increments, the same method used
on fish otoliths and tree rings, and are among the most reliable ages in the
entire animal kingdom — far better than a captive maximum. **Sclerochronology is
where invertebrate lifespan data is at its best**, and almost none of it is in
AnAge.

**Verdict: the highest-value single paper on this list.**

### The World Spider Trait database

A curated, expert-maintained, open repository for spider traits — morphology,
ecology, ecophysiology, behaviour — linked to the World Spider Catalog, with
location and method metadata on every record. Your five arachnids currently
produce a group quotient of 1.6× on the strength of two tarantulas.

Tarantula longevity is genuinely remarkable for the body size (female
*Brachypelma hamorii* at 30 years in a 20 g animal), and five species is not
enough to say whether that is an Araneae pattern or a Theraphosidae one. This
database would settle it.

### Social insects — a literature problem, not a database problem

There is no maintained longevity database for ants, bees, wasps and termites.
The standard reference is **Keller & Genoud's review of queen lifespan and
colony characteristics in ants and termites**, plus per-species primary
literature. AnAge does carry a handful of **taxon-level** entries (its build
includes ~26 taxa alongside its species) including Formicidae, which is worth
harvesting even though it breaks the one-row-per-species assumption.

This is the group where the model has its sharpest result and its thinnest data.
*Lasius niger* queens at 28.75 years against workers at two months — same
genome, two orders of magnitude — is the single best illustration of what the
quotient exposes, and it currently rests on two rows. Caste-resolved data would
turn one anecdote into a pattern across dozens of species.

**Verdict: hand-curated, slow, and the highest-payoff qualitative work
available.** It is also the part of the table where being careful about what
counts as "an individual" matters most.

### Encyclopedia of Life TraitBank — the catch-all

An open repository of traits for all taxa across the tree of life, aggregating
many contributed datasets, with a search-and-download interface that filters by
attribute and taxon. Includes Insecta, Mollusca, Echinodermata and Cnidaria.

Quality is heterogeneous by construction, because it is an aggregator rather
than a curator — but it is the only place to sweep for maximum-lifespan records
across the invertebrate phyla in one query. Treat the output as a lead list to
be checked rather than as data to be trusted, and grade everything from it **C**
on arrival.

**Verdict: use it to find species, not to settle numbers.**

---

## Part 2 — Vertebrate volume and quality

### AnAge — done

Build 12: ~4,200 species, of which the loader kept 3,210 with usable mass.
Manually curated, quality-graded, the benchmark. Its limitation is structural:
one longevity figure per species, so a merge drops the wild-and-captive pairing
from 74% of rows to 9%.

### Amniote Life History Database — the biggest easy win

Myhrvold et al. 2015, *Ecology* (Ecological Archives E096-269): up to 29
life-history parameters for **21,322 species** of birds, mammals and reptiles.
Five times AnAge's amniote coverage, plain CSV, free.

It is a consolidation rather than fresh curation, so it inherits its sources'
errors and overlaps AnAge heavily — which is precisely what your merge tool's
conflict report is for. It also carries **age at first reproduction**, the
classic second variable in life-history theory.

### FishBase — closes your weakest fit

~35,000 fish species via `rfishbase`, carrying a **`LongevityWild`** field: the
wild-lifespan column AnAge does not have. Your fish fit is the weakest of the
vertebrate groups (r² = 0.175 in your merged run), and fish hold a
disproportionate share of the extremes — *Somniosus microcephalus* (Greenland
shark) at 392 years, *Sebastes aleutianus* (rougheye rockfish) at 205,
*Ictiobus cyprinellus* (bigmouth buffalo) at 112, *Hoplostethus atlanticus*
(orange roughy) at 149.

Fish ages come from otolith annuli and bomb-radiocarbon dating, both far more
reliable than captive maxima. **Fish are the one vertebrate group where more
data will also mean better data.**

### ReptTraits and AmphiBIO — the clade-specific fillers

**ReptTraits** (*Scientific Data*, 2024): 40 traits from **12,060 reptile
species**, drawn from 1,288 sources published 1820–2023, including life-history
traits and IUCN status.

**AmphiBIO** (*Scientific Data*, 2017): 17 traits for **6,775 amphibian
species** across all three orders, from 1,500+ sources.

AmphiBIO addresses a specific failure you can see in every run: **the amphibian
fit is rejected every time** — r² = 0.12 at both 24 and 29 species — so
amphibians fall back to the global baseline. With 6,775 species available,
either the relationship appears or its absence becomes a real finding about
amphibians rather than an artefact of a small sample.

### AVONET — fixes bird mass, not bird lifespan

Tobias et al. 2022, *Ecology Letters*: eleven morphological traits measured on
**90,020 individuals across 11,009 bird species** — essentially every bird on
Earth, measured consistently.

No longevity. But look at your merge report: two-thirds of the flagged
disagreements are **body mass**, not lifespan, and they run to 12×. Mass is half
of this model and it is currently the sloppier half. AVONET would replace every
bird mass in the table with a consistently measured value from a known sample
size, which tightens the bird fit without adding a single species.

### USGS Bird Banding Laboratory longevity records — real wild data

The oldest known individual of each North American bird species, verified by BBL
biologists from a century of banding returns (individual encounter data from
1913). Explicitly **excludes captive-reared, rehabilitated and vagrant birds**,
and excludes same-season recaptures.

This is the wild counterpart AnAge lacks, for the group where AnAge is largest.
It is also the honest way to fix the artefact at the bottom of your ranking: the
Bassian thrush at 0.04× is a sampling problem, and banding records come with the
effort behind them. **EURING** provides the European equivalent.

---

## Part 3 — Demography, which is the real quality fix

Everything above is still *maximum longevity*: a record, not a rate, and
therefore a function of how hard anyone looked. Two sources escape that.

**DATLife** (Max Planck Institute for Demographic Research) holds curated **life
tables** — age-specific mortality and fertility with source quality assessed and
recorded. A life table gives median lifespan, life expectancy at maturity, and
the shape of the mortality curve, none of which a maximum can provide. It
covers thousands rather than tens of thousands of species, biased toward
well-studied vertebrates, and it is free. **malddaba** (Ronget et al., *Journal
of Animal Ecology*, 2025) is a newer open-access mammalian equivalent.

**Species360 ZIMS**: 1,400+ institutions, 100+ countries, **21,000 species, 10
million individuals, 170 million medical and husbandry records** — real
survivorship curves for captive animals. The published work using it is exactly
your question's shape: zoo elephant survival across six decades, big-cat life
expectancy across 150 years of records. Access runs through the Species360
Conservation Science Alliance as an academic collaboration, which as a UT
student with a faculty co-signer is a realistic ask rather than a fantasy.

**COMADRE** holds matrix population models across animals — same category, useful
as a cross-check.

Adding DATLife would let you report **a second quotient computed on median
lifespan instead of maximum**. Where the two disagree, you have found a species
whose record-holder is unrepresentative — which is a result, not a caveat.

---

## Part 4 — The second regressor

Body mass explains about half the variance in log lifespan. The quotient is the
other half, and the group view already suggests what is in it: bats, parrots,
primates and albatrosses high; ground birds, shrews, opossums and bandicoots
low. That is a predation-risk gradient — flight, burrowing, armour, venom and
being awkward to swallow all buy the same thing.

- **COMBINE** (Soria et al. 2021, *Ecology*): 54 traits for **6,234 mammals**,
  a taxonomically harmonised integration of PanTHERIA, EltonTraits and others,
  so it **supersedes both** on the mammal side. Carries `life habit`
  (fossorial, arboreal, aerial) — a direct test of the bat-and-mole-rat
  hypothesis.
- **EltonTraits** (Wilman et al. 2014): foraging attributes for the world's
  birds and mammals, CC BY 4.0. Still the standard for **birds**, which COMBINE
  does not cover.
- **PanTHERIA** (Jones et al. 2009): CC0, mammals, the original. Superseded by
  COMBINE unless you need its geographic variables.
- **Amniote** again, for age at first reproduction.

---

## Recommended order

| # | Source | Buys | Effort |
|---|---|---|---|
| 1 | **Amniote Life History DB** | 21,322 amniotes | low — CSV |
| 2 | **Quality filtering on what you have** | removes the thrush artefact | trivial — done |
| 3 | **FishBase + SeaLifeBase** (`rfishbase`) | fish + marine invertebrates, wild longevity | medium — R |
| 4 | **Moss et al. 2016 bivalves** | 1,084 populations, best-quality ages on the list | low — one paper |
| 5 | **AVONET** | fixes bird mass, the sloppy half of the model | low — CSV |
| 6 | **COMBINE + EltonTraits** | the second regressor | medium |
| 7 | **USGS BBL + EURING** | genuine wild longevity for birds | medium — scrape |
| 8 | **Add-my-Pet** | best per-species quality, all taxa | high — MATLAB structures |
| 9 | **DATLife** | median lifespan; a second quotient | medium |
| 10 | **ZIMS** | a captive side as good as the wild side | high — institutional |

Social insects, spiders and corals sit outside this ranking because they are
curation projects rather than downloads. They are also where the model says the
most interesting things, so they are worth doing slowly.

## What none of this fixes

Some of the best rows in the table will never come from a database. *Arctica
islandica* at 507 years, *Lamellibrachia luymesi* at 250, *Monorhaphis chuni* at
11,000 — these are individually-published records, each its own paper, each with
its own dating method and its own argument. They stay hand-curated, and the
**A/B/C quality grades stay the honest way to say so**.

---

**Sources**

- [AnAge / HAGR, *Nucleic Acids Research* 2024](https://academic.oup.com/nar/article/52/D1/D900/7337614) · [genomics.senescence.info](https://genomics.senescence.info/)
- [SeaLifeBase](https://www.sealifebase.ca/) · [rfishbase on CRAN](https://cran.r-project.org/package=rfishbase)
- [Add-my-Pet / AmP project, *PLOS Computational Biology* 2018](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006100) · [About Add-my-Pet](https://www.bio.vu.nl/thb/deb/deblab/add_my_pet/about.html)
- [Coral Trait Database, *Scientific Data* 2016](https://www.nature.com/articles/sdata201617) · [coraltraits.org](https://coraltraits.org) · [Octocoral Trait Database, *Scientific Data* 2024](https://www.nature.com/articles/s41597-024-04307-8)
- [Moss et al. 2016, bivalve lifespan across latitude, *Proc. R. Soc. B*](https://royalsocietypublishing.org/doi/10.1098/rspb.2016.1364)
- [World Spider Trait database, *Database* 2021](https://academic.oup.com/database/article/doi/10.1093/database/baab064/6397506)
- [EOL TraitBank](https://eol.org/traitbank)
- [Myhrvold et al. 2015, Amniote Life History Database, *Ecology*](https://esajournals.onlinelibrary.wiley.com/doi/10.1890/15-0846R.1)
- [ReptTraits, *Scientific Data* 2024](https://www.nature.com/articles/s41597-024-03079-5) · [AmphiBIO, *Scientific Data* 2017](https://www.nature.com/articles/sdata2017123)
- [AVONET, *Ecology Letters* 2022](https://onlinelibrary.wiley.com/doi/full/10.1111/ele.13898)
- [USGS Bird Banding Laboratory longevity records](https://www.pwrc.usgs.gov/BBL/longevity/longvrec.php)
- [DATLife / MPIDR](https://www.demogr.mpg.de/En/projects_publications/online_databases_1906/) · [malddaba, *J. Animal Ecology* 2025](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2656.70276)
- [Species360 ZIMS](https://species360.org/zims/)
- [Soria et al. 2021, COMBINE, *Ecology*](https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecy.3344) · [EltonTraits, *Ecology* 2014](https://esajournals.onlinelibrary.wiley.com/doi/10.1890/13-1917.1) · [PanTHERIA, *Ecology* 2009](https://esajournals.onlinelibrary.wiley.com/doi/10.1890/08-1494.1)
