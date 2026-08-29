# 23 — Longevity Quotient

How long an animal lives, against how long an animal of its size should live.

Body mass predicts lifespan. Over the 417 species in `data/animals.csv` — from a
nematode at a microgram to a blue whale at 150 tonnes, twenty orders of
magnitude — each tenfold increase in mass buys roughly a 1.5-fold increase in
maximum lifespan. The longevity quotient is what remains once that relationship
is divided out:

    LQ = observed lifespan / lifespan predicted from body mass

Built by analogy with the encephalisation quotient, which does the same thing to
brain size. LQ = 1 is exactly as long-lived as expected. The interesting animals
are the ones far from 1.

## Run it

```
python3 build_lq.py
```

No packages needed for the model or the visualiser; `matplotlib` only for the
four figures, and the script degrades gracefully without it. Writes
`longevity.html` (self-contained, opens offline), `outputs/lq_table.csv`,
`outputs/group_summary.csv`, `outputs/summary.json`, and the figures.

## The visualiser

`longevity.html` is one file with the data inside it. Every species is a row
with two bars — wild maximum in green, captive maximum in gold — and a tick at
the average of the two. Rows animate to their new positions when the sort
changes, so you watch the ranking rearrange rather than reading a new table.

| Control | Does |
|---|---|
| View | species, or groups aggregated at a taxonomic rank |
| Rank | phylum, class, order, family, or genus (groups view) |
| Compare by | mean quotient, median lifespan, longest lived, species count (groups view) |
| Min species | drop groups below a size threshold; default 3 |
| Sort by | quotient, lifespan, body mass, or name (species view) |
| Lifespan used | wild, captive, average of the two, or the longer of them |
| Baseline | the species' own group, or a single fit across all animals |
| Filter to | any taxon at any rank |
| Colony ages | exclude (default) or include the four colonial organisms |
| Names | scientific with common in parentheses (default), common only, or scientific only |
| Order | high-first or low-first, to reach either end of a capped list |
| Rows shown | 200 / 400 / 1000 / all — the animation stops being smooth past about a thousand |
| Scale | logarithmic or linear — the range spans 0.055 to 11,000 years, so log is the default |

Sorting by quotient switches the bars from years to multiples of predicted, with
a marked line at 1.

## Comparing groups

The groups view aggregates every species in a taxon and compares taxa against
each other at any rank from phylum down to genus. The bar is the **geometric
mean** quotient of the group's species, with a faint line showing the range from
its lowest to its highest member. The geometric mean is the right average for
ratios: a species at 4× and one at 0.25× should average to 1, not to 2.1.

Clicking a group drops into the species view filtered to it. The minimum-species
control matters most at family and genus rank, where most groups hold a single
animal and the "group statistic" is just that animal — which is why the default
is 3.

What the comparison shows, at order rank: Chiroptera (bats, 2.5×), Perciformes,
Psittaciformes (parrots), Primates (1.8×) and Procellariiformes (albatrosses and
petrels) sit at the top; Eulipotyphla (shrews, moles and hedgehogs, 0.37×),
Galliformes (0.43×), Salmoniformes and Lagomorpha at the bottom. At family rank
the bats of Vespertilionidae reach 3.1× and the rockfish of Sebastidae 3.5×.
Flight, burrowing, venom, armour and being hard to swallow all show up as
elevated quotients; being a ground bird or a small terrestrial insectivore shows
up as the reverse.

## The fits

Ordinary least squares of log10(lifespan) on log10(body mass), fitted globally
and within each group. Colonial organisms are excluded from every fit.

| Baseline | n | slope b | r² | predicted at 1 kg |
|---|---|---|---|---|
| All animals | 413 | 0.182 | 0.46 | 21.8 yr |
| Mammals | 147 | 0.146 | 0.49 | 17.2 yr |
| Birds | 89 | 0.167 | 0.41 | 31.0 yr |
| Reptiles | 45 | 0.158 | 0.26 | 32.5 yr |
| Fish | 46 | 0.173 | 0.38 | 25.3 yr |
| Invertebrates | 62 | 0.253 | 0.43 | 23.8 yr |

Slopes near 0.15 for mammals and birds are what the comparative literature
reports. Birds come out about 1.8× longer-lived than mammals of equal mass, also
as expected — which is exactly why the group fit is the default. A single global
fit charges every bird a bonus it did not earn and every mammal a penalty it
does not deserve. Fish classes are pooled, and the many small invertebrate
classes are pooled into one baseline, because separately they are too thin to
fit.

**A fit is only used if it is worth using.** The amphibian regression returns
r² = 0.12 across 24 species, which is not a relationship. `build_lq.py` rejects
any group fit with a non-positive slope or r² below 0.15 and falls back to the
global baseline, reporting which groups were rejected and why. Amphibians are
currently the only rejection.

## Colonial organisms

Four entries are colonies, not individuals: a black coral at 4,265 years, a
boulder star coral, a giant barrel sponge, and a glass sponge whose spicule
growth rings have been read as 11,000 years. Those are colony ages; the polyps
composing them live ordinary short lives. They are excluded from every
regression, and hidden from the rankings by default, because an
eleven-thousand-year colony sits at the top of every sort and buries the actual
result. Switch **Colony ages** to Include to see them.

## What comes out

Highest quotients against their own group: the ocean quahog (45×), a garden ant
queen (27×), a cold-seep tubeworm (22×), the freshwater pearl mussel (15×), a
leafcutter ant queen and the red sea urchin (10×). Lowest: the silkmoth (0.04×),
a wasp worker (0.05×), Labord's chameleon (0.06×), the longfin inshore squid and
the common octopus (0.06×).

Three of those are the point of the whole exercise. The honey bee worker and the
honey bee queen are the same genome, an order of magnitude apart in lifespan;
caste and diet set the outcome, not genetics. The giant Pacific octopus is
large, long-brained, and dead in five years, because it breeds once and then
stops eating — while the chambered nautilus, a cephalopod that does not breed
once and die, lives twenty. And Labord's chameleon spends most of its existence
as an egg, then lives four or five months as an adult: the shortest lifespan of
any four-limbed vertebrate, in a body the size that predicts eight years. None
of this is visible in a lifespan table sorted by years. All of it is obvious the
moment mass is divided out.

## Data

`data/animals.csv` — 417 species with full taxonomy (kingdom, phylum, class,
order, family, genus), adult body mass, wild maximum, captive maximum, a
colonial flag, a quality grade, and a note. The table spans 10 phyla, 30
classes, 127 orders, 263 families and 387 genera. Compiled from the comparative longevity
literature. Grades: **A** documented and verified, **B** defensible literature
estimate, **C** uncertain. Disputed records are excluded in favour of verified
ones — the 226-year koi and the 120-year cockatoo are both out.

## Going past 417 species — the AnAge merge

417 is the ceiling on what can be compiled and checked by hand. Past that you
need **AnAge**, the reference comparative longevity database: roughly 4,200
species with maximum longevity and adult body mass, curated at the University of
Liverpool. Three steps, all on your machine — the sandbox this was built in
cannot reach `genomics.senescence.info`.

```powershell
cd "23 Longevity Quotient/data"
Invoke-WebRequest https://genomics.senescence.info/species/dataset.zip -OutFile dataset.zip
python3 load_anage.py      # dataset.zip -> animals_anage.csv
python3 merge_anage.py     # + animals.csv -> animals_merged.csv + merge_report.txt
cd ..
python3 build_lq.py --data data/animals_merged.csv
```

On macOS or Linux the download is
`curl -LO https://genomics.senescence.info/species/dataset.zip`. There is no
unzip step either way; `load_anage.py` extracts the archive itself and prints
the right download command if it finds neither file.

That takes the table to roughly 4,300 species and about six seconds to build.

### What the merge does, and why it is a merge and not a replacement

The two tables are good at different things. The curated one is small and
hand-checked, and every row carries a wild maximum *and* a captive maximum —
the comparison this whole project is built around. AnAge is large and
machine-readable but carries one longevity figure per species. Replacing the
first with the second would trade the comparison for coverage.

So `merge_anage.py` follows six rules:

1. **Curated rows win.** A species in both keeps its curated row.
2. **AnAge fills gaps, never overwrites.** A missing captive figure gets filled
   if AnAge has one and its specimen was captive; the note records that it came
   from AnAge. Existing numbers are never replaced.
3. **Species only AnAge has are added outright.** This is where the count grows.
4. **Disagreements are reported, not silently resolved.** Where both tables have
   a figure for the same species differing by more than 2× (or 3× on mass), the
   pair goes into `merge_report.txt` for you to look at. A factor-of-two gap
   usually means a different subspecies, a disputed record, or a units error.
5. **Duplicate scientific names are locked.** The honey bee appears twice on
   purpose, as queen and as worker — same genome, tenfold lifespan difference.
   Matching on scientific name alone would collapse them, so any name appearing
   more than once is never merged into.
6. **Colonial flags survive.** AnAge has no notion of a colony.

`--check-taxonomy` additionally lists taxon names present in one table but not
the other. This matters more than it sounds: AnAge and the curated table
occasionally disagree on higher taxonomy (Artiodactyla against
Cetartiodactyla, for instance), which shows up as two group rows that ought to
be one.

### What gets worse at 4,300 species, and what to do about it

**The wild-against-captive view thins out.** Every AnAge row arrives with one
figure. After a merge, only about 7% of the table carries both a wild and a
captive maximum, against 74% before. The pairs are still there and still
correct; they are simply a small minority. Filtering to a taxon you care about
is the way to keep the comparison usable.

**A row per species stops being viable.** The re-sort animation is the whole
point of the species view, and it will not stay smooth while moving four
thousand DOM nodes — measured at 3.3 seconds per re-sort against 0.2 for the
capped view. So the species view caps at 400 rows by default, taking them from
the end of the current sort, which is where the interesting animals are anyway.
The **Order** control flips to the other end of the ranking and **Rows shown**
raises or removes the cap. The groups view is unaffected and becomes the right
way to see everything at once.

**The fits get better and the outliers get less impressive.** With 4,300 species
the global r² rises from 0.46 to about 0.61, because a bigger sample pins the
relationship down. Individual quotients shift accordingly, so a number quoted
from the 417-species build will not match one from the merged build. Say which
build a figure came from.

### Further still

A full source-by-source survey — including the invertebrate databases AnAge
barely touches — is in **`DATA_SOURCES.md`**. Short version: after an AnAge
merge the table holds 1,384 birds and 19 insects, while the top of the quotient
ranking is almost entirely invertebrate. The sources that would change what the
model *says*, rather than just how big it is, are SeaLifeBase, Add-my-Pet, the
Moss et al. bivalve sclerochronology compilation, and hand-curation of the
social insects.

AnAge is the deepest source but not the only one. The **Amniote Life History
Database** carries about 21,000 species and much better reptile and bird
coverage than AnAge. **FishBase**, reachable through the `rfishbase` package,
covers the fish, which is where the largest lifespan uncertainties in this
table sit. **PanTHERIA** and **EltonTraits** add life-history and diet variables
rather than more species — which is what a second regressor needs. All four use
scientific name as the join key, so the merge tool extends to them with a new
loader and no change to the merge logic.

Adding a predation-risk proxy as a second regressor is the obvious next
modelling step. Flight, burrowing, armour and venom account for most of the top
of the mammal list, and they are currently absorbed into the residual that the
quotient measures.

## Caveats

**Maximum longevity is an extreme-value statistic.** Its expected value rises
with the number of individuals anyone observed, so a thinly-studied species
looks short-lived for reasons that have nothing to do with ageing. This is
invisible in the hand-curated 417 — everything there is well studied — and
obvious after an AnAge merge, where the bottom of the ranking fills with obscure
species whose "maximum" is one banded individual.

AnAge's own *Data quality* field does not catch it, because that field records
whether the record was **verified**, not how many animals were watched: a single
banded thrush can be a perfectly verified record of a perfectly unrepresentative
bird. The field that does catch it is **Sample size**, so `load_anage.py`
demotes tiny and small samples to grade C.

What to do with grade C is an empirical question, and `test_fit_strategy.py`
settles it by simulation — build a table whose slope is known because it was put
there by hand, contaminate a third of it the way the artefact contaminates real
data, and see which method gets the slope back:

| grade-C records skew | keep all | **drop C** | down-weight C | truth |
|---|---|---|---|---|
| small-bodied | 0.199 | **0.160** | 0.175 | 0.160 |
| large-bodied | 0.120 | **0.160** | 0.146 | 0.160 |
| no mass skew | 0.171 | **0.160** | 0.164 | 0.160 |

Dropping grade C recovers the true slope exactly in every scenario; weighting
gets 3–9% of the way wrong; keeping everything costs up to a quarter of the
slope. The reason is that grade C marks a **bias**, not merely noise — those
lifespans are systematically depressed — and down-weighting a bias still lets it
through. So `FIT_STRATEGY = "filter"` is the default, and `--weights weighted`
or `--weights none` are available to check.

The test states its own assumption: that the depression is roughly
multiplicative and independent of mass. Run all three on real data and compare
rather than trusting the simulation in the abstract.

Grade C is also hidden from the visualiser's rankings by default, under **Data
grade**, because a record excluded from the fit but left in the display is being
scored against a baseline it did not contribute to — it piles up at the bottom
looking like a finding when it is the sampling effort showing through.

**These are maxima, not averages**, and a maximum is sensitive to how many
individuals were watched and for how long. Captive maxima are better documented
than wild maxima for nearly every species here, because captive animals get
counted and wild ones do not. That asymmetry inflates the apparent captive
advantage. It is real for small prey animals, which mostly die of being eaten,
and it reverses for large social mammals: elephants and killer whales have lower
*median* lifespans in captivity than in the wild whatever their record holders
show.

**r² is measured on the logarithms.** An r² of 0.46 across four orders of
magnitude still permits a factor-of-two error on any individual species. The
quotient is a lens for finding outliers, not a measurement.

**Body mass is one variable.** Metabolic rate, age at first reproduction,
whether the animal flies, whether it lives underground, and whether it breeds
once or repeatedly all carry real signal. Flight and burrowing between them
explain most of the top of the mammal list. Adding predation-risk proxies as a
second regressor is the obvious next build.

## Figures

`outputs/fig1_allometry.png` — lifespan against mass on log-log axes, class
coloured, global fit line, outliers labelled.
`outputs/fig2_lq_ranked.png` — the top and bottom of the quotient ranking.
`outputs/fig3_wild_vs_captive.png` — dumbbell plot of wild against captive,
sorted by the size of the gap.
`outputs/fig4_orders.png` — every order with four or more species, ranked by
geometric mean quotient.

`outputs/group_summary.csv` carries the aggregate for every group at every
rank: species count, colonial count, geometric mean quotient, median lifespan,
mass range, and the longest-lived member.
