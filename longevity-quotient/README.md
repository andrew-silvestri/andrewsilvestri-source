# Longevity quotient

How long an animal lives, against how long an animal of its size should live.
This is the code and data behind andrewsilvestri.com/longevity.html.

    LQ = observed maximum lifespan / lifespan predicted from body mass

The quotient was introduced by Austad and Fischer (*Journal of Gerontology*
46:B47, 1991), by analogy with Jerison's encephalisation quotient. LQ = 1 means
a species lives exactly as long as its body mass predicts.

Every number below is from the current build: `outputs/summary.json`,
`outputs/ingest_report.json` and the tables beside them.

## What is in this archive

| File | What it is |
|---|---|
| `data/animals.csv` | the hand-checked seed table, 417 rows |
| `data/ingest.py` | merges the seed with five databases, merges synonyms, files each genus under one family and applies the recorded corrections; writes `data/animals_merged.csv`, `outputs/provenance.csv`, `outputs/synonyms.csv`, `outputs/genus_families.csv`, `outputs/ingest_report.json` |
| `data/animals_merged.csv` | the merged table, 7,791 species |
| `data/synonyms_manual.csv` | the hand list of synonym pairs: both names, the name kept, and the source in this archive that states the synonymy, quoted |
| `data/anage_sample.py`, `data/anage_sample.csv` | AnAge's own sample-size band per species, from the raw zip; `build_lq.py`'s study-effort check reads the CSV |
| `build_lq.py` | the fits, the quotients, the group summaries, the figures and the visualiser |
| `fig_lq_explained.py` | the explainer figure |
| `template.html` | the visualiser, before `build_lq.py` puts the data in it |
| `update_page.py` | writes the page's data-dependent numbers from `outputs/` |
| `test_merge.py`, `test_fit_strategy.py`, `test_perf.js` | checks on the merge, the fit strategy, and the visualiser's speed |
| `test_lq.py` | the amphibian fallback in the group tables, the study-effort check against the audit's figures, and the page against `summary.json`; `--break fallback\|effort\|page\|rail` each must fail |
| `outputs/lq_table.csv` | every species: taxonomy, mass, lifespans, both predictions, both quotients, grade, note |
| `outputs/provenance.csv` | which source each record and each mass came from |
| `outputs/synonyms.csv` | every name merged into another as a synonym, the rule that joined them, and the record kept |
| `outputs/genus_families.csv` | every genus its sources filed under more than one family: the families before, the family chosen, and the source that decided |
| `outputs/group_summary.csv` | every group at every rank: count, geometric-mean quotient, which baseline scored it (`own`, `global` for amphibians, `mixed`), median lifespan, mass range, longest-lived member |
| `outputs/summary.json` | the fits, the census, the figures the page names (`headline`) and the study-effort check (`effort_check`) |
| `data/load_anage.py`, `data/merge_anage.py` | the retired seed-plus-AnAge path; `ingest.py` replaced it and the build does not use them |

Not included: the raw source files (`data/raw/`, 39 MB; `DATA_SOURCES.md` says
where each comes from), the figures, and the built visualiser (the site serves
it as `longevity-app.html`).

## Run it

```
python data/ingest.py --apply
python build_lq.py
python test_merge.py
python test_fit_strategy.py
python test_lq.py
```

`ingest.py` needs the raw files in `data/raw/` and pandas (with openpyxl and
pyarrow, for AVONET's spreadsheet and FishBase's parquet). Without `--apply` it
reports and writes nothing. `build_lq.py` reads `data/animals_merged.csv` when it
exists and `data/animals.csv` otherwise. It imports `sitefig.py`, the site's
shared figure style, from the directory above, and that file and the site's
fonts are not in this archive, so `build_lq.py` and `test_merge.py` (which
imports it) do not run from the archive alone.

## The data

Six sources carry a maximum lifespan. A species in more than one takes its
record from the highest in this order and lists the others as corroboration.

| Source | Records with a lifespan | Used as the record |
|---|---|---|
| hand-checked seed table | 417 | 416 |
| AnAge build 15 | 4,141 | 3,466 |
| Amniote life-history database | 5,500 | 2,590 |
| PanTHERIA | 1,013 | 0 |
| AmphiBIO | 359 | 116 |
| FishBase v25.04 | 2,088 | 1,203 |

Two binomials are one species when they carry the same common name in the
same class and their epithets agree (once the Latin gender ending is set
aside, or to within one letter for epithets of six letters or more), or when
AVONET's BirdLife-eBird or BirdLife-BirdTree crosswalk pairs them one to one;
never when one source lists both. A third route is the hand list,
`data/synonyms_manual.csv`: a pair is listed only where a source in this
archive states the synonymy in its own words, quoted in the file (all seven
so far are FishBase remarks, such as *Pristis microdon* and *P. perotteti*
as synonyms of *Pristis pristis*), and a listed pair is merged even where
that source carries both names. The merged record is the one the precedence
order picks, under its own name (a hand-listed pair takes the name the list
keeps), with the other name in its note. That folds 115 second names into
113 species (`outputs/synonyms.csv`).

8,464 species carried a lifespan after the merge. 673 had no body mass in any
source and were dropped, which leaves 7,791. Masses come from the record's own
source where it has one. AVONET (birds only), PanTHERIA and Amniote together
hold a mass for 14,673 species. 557 records took a mass from elsewhere: 542
from another lifespan record of the same species (468 AnAge records from
FishBase, 59 from AmphiBIO, 14 from Amniote, and Labord's chameleon from
AnAge), and 15 from AVONET. 620 fish
masses are computed from maximum length through FishBase's length-weight
relationship, and their notes say so.

The table spans 10 phyla, 32 classes, 199 orders, 751 families and 2,896
genera, from a rotifer at 0.5 µg to a blue whale at 150 tonnes. 2,889 species
have a maximum their source labels wild, 1,795 one it labels captive, 308 have
both, and 3,415 carry a maximum whose source does not say.

Fifty genera are filed under two families by their sources (AnAge's
Serranidae and FishBase's Epinephelidae for the groupers, Colubridae and
Natricidae for the garter snakes). Each takes one family for all its
species: the one its highest-precedence source gives, and within that source
the one it gives most members. `outputs/genus_families.csv` lists each genus,
its families before and the source that decided.

## Grades

- **A** (145): 87 rows of the seed table, each checked against a citation,
  and 58 AnAge records that AnAge grades "high".
- **B**: AnAge "acceptable", every Amniote record (the compilation has no
  quality field), and 309 seed rows.
- **C**: AnAge "questionable" or "low", every FishBase and AmphiBIO record, 20
  seed rows, the olm's projected age (below), and the outlier demotions
  below.

AnAge's sample-size field is not used. On arrival the grades are A 145, B 6,217,
C 1,429. Two records are demoted by name first (`DEMOTE_BY_NAME` in
`build_lq.py`: the toolache wallaby and the lesser cane rat, below). A preliminary fit per group then
demotes any grade-B record more than 3 residual standard deviations from it,
in either direction: 58 records (31 mammals, 10 birds, 8 fish, 8 reptiles, 1
amphibian). The four colonies (one B, three C) are held out of everything, so
the model runs on A 145, B 6,156, C 1,486.

## The fits

Ordinary least squares, unweighted, of log10 maximum lifespan in years on log10
adult mass in grams, over the grade-A and B records. Grade C is held out of
every fit and scored against the result (`FIT_STRATEGY = "filter"`;
`--weights weighted` and `--weights none` are there to compare).

| Baseline | Species in fit | Slope b | r² | Predicted at 1 kg |
|---|---|---|---|---|
| All animals | 6,302 | 0.189 | 0.32 | 14.0 yr |
| Mammals | 2,528 | 0.216 | 0.40 | 10.0 yr |
| Birds | 1,842 | 0.215 | 0.43 | 22.4 yr |
| Reptiles | 901 | 0.211 | 0.36 | 17.3 yr |
| Fish | 893 | 0.240 | 0.57 | 12.5 yr |
| Invertebrates | 57 | 0.256 | 0.41 | 23.0 yr |

Fish classes are pooled, and the invertebrate classes are pooled into one
baseline. A group fit with a non-positive slope or an r² below 0.15 is
rejected. The amphibian fit is the only one: r² 0.087 over 81 species, so
amphibian species are scored against the global fit, and so are their groups
in `group_summary.csv` (until October 2026 the groups were left blank, so
Anura and Urodela dropped out of the rankings). On that line Urodela ranks
first of the 83 orders at 2.89, which is not the scale the other orders are
on. Every fish in the fish fit
is from the seed table or AnAge, because the FishBase rows are grade C.

`test_fit_strategy.py` simulates a table with a known slope (0.160), lowers
the lifespans of a third of it and flags those records C, then compares the
three strategies. Dropping C recovers 0.160 in all three scenarios;
down-weighting is 3 to 9% off; keeping everything is up to 25% off. It assumes
the grade marks the depressed records. In the real table grade C is the list
above.

## The visualiser

One self-contained HTML file. Every species is a row with up to three bars, for
a wild maximum, a captive maximum and a maximum of unrecorded origin, and a
tick at the average of whichever exist. The groups view aggregates any rank
from phylum to genus by geometric-mean quotient. Controls: View, Rank, Sort by,
Order, Rows shown, Compare by, Min species, Data grade, Colony ages, Lifespan
used, Baseline, Filter to, Names, Search.

## Corrections made in the data

Found by the site's QA audit of October 2026 and corrected in the pipeline, each
with its reason recorded where it is applied:

- Synonyms: species were matched on the binomial alone, so a species named two
  ways was two records, and where both were grade A or B it entered the fits
  twice (*Centrochelys* and *Geochelone sulcata*; the pink cockatoo and Major
  Mitchell's cockatoo, *Cacatua* and *Lophochroa leadbeateri*). `ingest.py`
  now merges them by the two rules and the hand list under The data. After the
  merge, 33 common names are still carried by two or more binomials, for 26 of
  them at least two copies grade A or B (`update_page.py` counts them): species
  one source splits and another does not, distinct species that share a name,
  and possibly a few synonyms that no rule joins and no source here states,
  such as the sperm whale as *Physeter catodon* (Amniote, PanTHERIA) and
  *P. macrocephalus* (AnAge, seed table).
- Genus *Sebastes* was filed under Sebastidae by the seed table and FishBase and
  under Scorpaenidae by AnAge, so the rockfishes set the Scorpaenidae figure.
  `one_family_per_genus` in `ingest.py` now gives every genus filed under two
  families the family of its highest-precedence source (2026-11-10): fifty
  genera, *Sebastes* among them, so all 46 *Sebastes* records that reach the
  fits are Sebastidae. The family figures moved with it.
- The toolache wallaby's 13 months at 10 kg (Amniote, grade B) is very likely
  a data error that fell 0.006 log units inside the outlier cut. No other source
  here records its lifespan, so it is demoted to C by name, not replaced.
- The lesser cane rat's 10 months at 2.3 kg (Amniote, grade B) is the same kind
  of likely error, just inside the cut; demoted to C by name the same way
  (2026-11-10).
- The olm's 100 years in the seed table is Voituron et al.'s projection
  (*Biology Letters* 7:105, 2011, about 102 years), its "wild" 68 is their mean
  adult lifespan in a laboratory population, and AnAge's 102 years is the same
  projection, filed as a wild maximum. `CORRECTIONS` in `ingest.py` drops the
  seed's two figures and carries AnAge's 102 years as a projection: moved to
  the column of unrecorded origin, graded C so it stays out of the fits, with a
  note that opens by calling it a projection (2026-11-10). AmphiBIO's 12 years,
  which gives no origin, is not used. The mass is AnAge's 17 g.
- Labord's chameleon had 25 g in the seed table, which cites no source for it,
  against 8.73 g in AnAge and Amniote. `CORRECTIONS` drops the seed mass, so
  the record takes AnAge's 8.73 g; the reptile fit predicts 6.4 years at that
  mass, against 7.9 at 25 g.

## Known limits

- A maximum lifespan is an extreme value: it rises with the number of animals
  anyone watched, so a thinly studied species looks short-lived. Amniote
  supplies a record only where AnAge has none, the less-studied species, and
  is 60% of the mammal fit, 59% of reptiles and 27% of birds. At equal mass
  within family its records sit x0.60 (mammals), x0.75 (reptiles) and x0.81
  (birds) below AnAge's medium-sample records. `build_lq.py`'s
  `effort_check()` rescales every non-seed record to that level and re-runs
  the same fits: birds against mammals 2.23 -> 1.80, mammal at 1 kg 10.0 ->
  13.4 years, human 5.0 -> 4.1, Brandt's bat 11.9 -> 7.9, order ranking
  Spearman 0.994. The page keeps the pooled figures and prints both.
- AnAge's sample-size field is not used for grading (the retired
  `load_anage.py` demoted tiny and small samples; `ingest.py` does not), so
  178 tiny and 837 small AnAge samples are grade B in the fits.
- Species are plain OLS points; related species are not independent, and
  within mammal families the slope is lower than across them.

`outputs/lq_table.csv` rounds to four decimals, except masses under a gram,
which keep six significant figures.

## Licences of the data

AnAge is CC BY 3.0. HAGR asks users to cite de Magalhães et al., *Nucleic Acids
Research* 52:D900, 2024. FishBase is CC BY-NC 4.0, so the 1,203 rows with
`taken_from = fishbase` in `outputs/provenance.csv` carry its non-commercial
term. For the other sources, see their own terms; `DATA_SOURCES.md` links each
one.
