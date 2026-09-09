# Pre-specification: the topic-stratum test

**Written 9 September 2026, BEFORE any topic data exists.** No
`primary_topic` counts have been fetched for any species at the time of
writing; `beauty/data/` holds no such table and `fetch_topics.py` has not been
run. Choosing strata after seeing coefficients is a forking path that leaves no
trace — every number correctly computed, the conclusion still unearned — so the
rule is committed here first and the report is written against it, including the
strata that disappoint.

## The question

`STEP0_2026-09-09.md` finds that threatened birds get **more** research, not
less: CR at 2.65× Least Concern on the total (no-views) specification, 1.90× on
the direct (full) one, p < 1e-22 throughout.

**The rival explanation this test exists to kill or confirm:** Red List
assessment itself generates literature naming the species — status reviews, Red
List updates, assessment documents. If the CR advantage is made of those, the
response variable is partly caused by the listing and the effect is an
instrument artefact.

**The distinction that decides it.** Papers *about the listing* are the
artefact. Papers *prompted by* the listing are the finding — being listed
causing research is a result; being listed causing paperwork that mentions the
name is an instrument problem. Each stratum below is labelled with which of the
two it can measure.

## The data to be fetched

One `group_by=primary_topic.field.id` call per species, over the pinned
`filter=title_and_abstract.search:"<name>",publication_year:2015-2024`. Billed
as a search, $0.001 per species.

- **Tonight:** all 1,837 non-LC modelled species (NT 808, VU 579, EN 315,
  CR 135). $1.84 against $3.1668 prepaid.
- **Tomorrow:** 1,000 LC species **matched**, not randomised — drawn to match
  the non-LC set on family, log₁₀-mass bin (0.5 dex) and description-year
  decade, all already on disk. $1.00 against the free daily budget.

Matching is the point of the design: within-stratum comparison needs LC birds in
the same strata the non-LC birds occupy, not wherever LC birds happen to cluster.

## Amendment 1 — 9 September 2026, before any coefficient was seen

**The sampling clause above is superseded. The fetch takes the whole modelled
population, all 9,113 species.** The clause as written is left standing so the
change is legible.

**What it said:** all 1,837 non-LC species tonight, plus 1,000 LC species
matched on family, log₁₀-mass bin and description-year decade.

**Why it fails, and this is the reason for the amendment.** `match_lc.py` was
run and reported that **543 of the 1,245 non-LC strata contain no LC bird at
all** — 44% of the strata cannot support a within-stratum comparison, which is
the comparison the whole test is built on. Exact family × mass-bin × decade is
too fine-grained for a 1,000-species draw to fill, and the matched design would
answer the primary comparison over a little more than half the strata while
appearing to answer it over all of them. That is a defect in the design, not in
its execution.

**Cost is secondary and is named honestly as such.** A `group_by` call bills at
1 credit, $0.0001 — a tenth of the list call, measured twice: `meta.cost_usd`
0.0001 across a five-species trial, and a two-call probe in which the group_by
call left prepaid at $3.1668 while the list call immediately after took $0.0010
off it. So the population costs $0.91 against $3.1668 available, less than the
$1.84 the sample was budgeted at. **This is not the justification.** A pre-spec
amended on budget grounds invites the next one to be amended on convenience; the
justification is the 543 empty strata, and the price merely means nothing had to
be traded to fix it.

**No coefficients had been seen when this changed.** No stratified fit has been
run, `data/topic_counts.csv` holds no rows at the time of writing, and the rule
below — cell size, primary comparison, failure condition — is **unchanged**.

**`data/lc_matched.csv` is kept, not deleted.** A population fetch makes it
unnecessary; it does not make it wrong, and it is the record of what the matched
design would have been.

**The rule binds harder now, not less.** With every stratum populated, the
temptation is to report the ones that worked. The minimum cell size, the primary
comparison and the failure condition stand exactly as written, and the report
names the strata that disappoint.

**Fetch order: non-LC first, and this is a design choice about an unknown
rather than an assumption about it.** The fetch walks its list in order, so a
run cut short by a 429, a kill or a mispriced call keeps whatever it reached.
Alphabetical order tracks genus and therefore family — the strongest term in the
model at ΔR² 0.1415 — so a truncated block is a family-biased sample, not a
random one. Putting the 1,837 non-LC species ahead of the 7,276 LC ones means
the categories that bind the cell-size rule are complete before any truncation
can bite, and **CR, at 135 species, cannot afford to lose any**. The per-call
rate was genuinely uncertain when the run started — two earlier attempts to
price it were unsound — and this ordering is what made a wrong answer
survivable instead of fatal. A design that limits the damage from an unknown is
worth more than one that assumes the unknown away.

## Strata

OpenAlex `primary_topic.field.id`. Fields are pre-assigned by OpenAlex and are
not chosen by this project.

| field | id | measures | artefact-prone? |
|---|---|---|---|
| Agricultural and Biological Sciences | 11 | ecology, behaviour, systematics | **partly** — carries conservation biology |
| Environmental Science | 23 | conservation, biodiversity policy | **yes** — where status reviews land |
| Biochemistry, Genetics and Molecular Biology | 13 | genomics, phylogenetics | **no** |
| Immunology and Microbiology | 24 | pathogens, disease ecology | **no** |
| Medicine | 27 | veterinary, zoonoses | **no** |
| Neuroscience | 28 | song, cognition | **no** |
| Earth and Planetary Sciences | 19 | palaeo, biogeography | **no** |

## The rule, committed

1. **Minimum cell size.** A stratum is reported only if **every** Red List
   category in it has **≥ 30 species with ≥ 1 work** in that field. Strata below
   that are listed by name with their cell counts and explicitly **not
   interpreted**. CR has 135 species in total, so this is the binding
   constraint and some strata will fail it — that is expected and is not a
   result.

2. **PRIMARY comparison.** The Red List coefficient on
   log(1 + works in field 13, Biochemistry/Genetics/Molecular Biology),
   same reduced specification as `selection_check.py` (family, mass, range,
   described, category; HC1). Genomics is the cleanest artefact-free stratum: a
   status review cannot land in it, and a phylogenetics paper naming a CR bird
   is research the listing may have prompted but did not manufacture.

3. **SECONDARY, pre-ordered.** Field 28 (Neuroscience), field 24 (Immunology and
   Microbiology), field 27 (Medicine), field 19 (Earth and Planetary Sciences),
   then field 11 (Agricultural and Biological Sciences). Field 11 is secondary
   and not primary precisely because it carries conservation biology. Field 23
   (Environmental Science) is **not** a test of the effect at all; it is the
   artefact's own home and is reported as the positive control — the effect
   should be **largest** there if the artefact is real.

4. **The contrast, predicted in advance.** The crude whole-corpus exclusion —
   refit on total works minus fields 23 and 11 — is run alongside and is
   **expected to be worse** than the stratified test, because it deletes genuine
   conservation biology, which is research effort on the species. It trades one
   artefact for another and will understate the effect. Saying so here is what
   makes it evidence rather than a story told afterwards.

## What counts as the effect FAILING to survive

Stated before the numbers exist:

- **Fails** if the CR coefficient in the primary stratum (field 13) is not
  positive at p < 0.05, **or** if its point estimate is below **+0.20** — under
  a third of the total-specification CR coefficient of +0.9738. A threat effect
  that exists only where status reviews can be published is an artefact.
- **Fails** if the effect is present in field 23 and in **no** artefact-free
  stratum meeting the cell-size rule.
- **Survives** if the CR coefficient is positive at p < 0.05 with a point
  estimate ≥ +0.20 in the primary stratum **and** in at least one secondary
  artefact-free stratum meeting the cell-size rule.
- **Indeterminate** if fewer than two artefact-free strata meet the cell-size
  rule. Indeterminate is reported as indeterminate; it is not resolved by
  lowering the threshold, and the page then rests on the total effect with the
  artefact named as an unresolved limitation.

No result here licenses a causal claim. `RESEARCH.md` §1's refusals stand
whatever the strata say.

## What the fetcher must carry

`fetch_topics.py` is a new script and inherits none of `fetch_openalex.py`'s
protections unless they are written in — a new fetcher with the old bug is trap
24, a harness inheriting every default nobody set. Required, and proven before
use:

- `netutil.Lock` with a heartbeat, so `check_settled()` can see a live fetch;
- a per-row `fetched` ISO-date stamp, so placeholder data cannot reach a payload
  (trap 18);
- `netutil.trim_partial_row` on start and `check_header`, so a kill cannot
  corrupt the table;
- the pinned `title_and_abstract.search` filter, no bare `search=` (the guard in
  `test_beauty.openalex_query()` exists for this);
- `try / except BaseException: … raise / finally:` around the run so **every**
  exit path writes the run log, the exception class named in the line;
- a `break_topics.py` over the same five exit paths as `break_log.py` — clean,
  402, persistent 5xx, KeyboardInterrupt, Budget — asserting the log **is**
  written, the rows are intact and the exit is **non-zero**; and it must be
  shown to FAIL under a deliberate mutation before it is believed.

## Budget reporting

Report which budget paid. Tonight draws prepaid ($3.1668, leaving ~$1.33).
Tomorrow's 1,000 LC species draw the $1.00 free daily with zero margin; the 429
path is resumable and now logged, but silently drawing prepaid when free budget
was intended only shows up in a balance, so both are read before and after.
