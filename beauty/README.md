# Studied, not endangered

Source for `site/beauty.html`: does being endangered get a bird studied?
The page fits research effort per species (papers naming the species,
2015–2024) against Red List category, body mass, range size, years since
description, rated attractiveness and public attention, with family fixed
effects, for the world's birds; and sets that beside the published
species-level models for other taxa.

## What is in the archive, and what is not

This archive is thinner than the site's others, for a reason the page
states: the IUCN Red List's terms of use forbid redistributing Red List
data, so no file here carries a Red List category beside a species name.
Everything else is here: every script, every join, and every input whose
licence allows it (AVONET and the attractiveness scores, CC BY 4.0;
Wikipedia pageviews and OpenAlex counts, CC0; the Red List summary table,
a cited aggregate). The Red List column comes from your own token, free,
and the build labels what it ran with.

What does travel is a digest of it. `manifest.json` carries the SHA-256 of
the Red List table this page was built from, in a canonical form (sorted
`species,category` lines, LF endings, UTF-8, no header), so after fetching
the categories yourself you can run

```
python3 build_beauty.py --verify-categories
```

and be told whether you have the same table, a later Red List version, or
a name-matching problem. A digest is 64 characters and cannot be inverted
to recover a single category, so it goes where the table may not.
`manifest.json` also hashes every shipped input, so a changed file shows up
as a changed hash rather than as a quietly different number on a rebuild.

## Run

```
python3 fetch_traits.py      # AVONET + attractiveness deposit, hash-pinned  (network once)
python3 fetch_years.py       # year of description, GBIF/Catalogue of Life   (~4 h, no key)
python3 fetch_wikipedia.py   # English Wikipedia pageviews 2016-2025         (~3 h, no key)
python3 fetch_openalex.py    # papers per species                             (OPENALEX_KEY; see cost)
python3 fetch_iucn.py        # Red List category per species                 (IUCN_TOKEN)
python3 fetch_groups.py      # Red List Table 1a + class-level paper counts  (10 OpenAlex calls)
python3 build_beauty.py      # join, models, bootstrap -> outputs/beauty_payload.json
python3 fig_beauty.py        # three figures -> site/assets/, each must report 0 layout problems
python3 update_page.py --apply
python3 test_beauty.py
```

**The order is enforced, not merely recommended.** `build_beauty.py`
refuses to run while any fetch is still writing, or while any per-species
table is short of the full species list, and names what is missing. It has
to: the manifest is a claim about files as they stand at that instant, so
hashing a table that is still growing would publish a digest of something
that stops existing a second later. A run that is interrupted leaves a
heartbeat file under `data/raw/.locks/`; the build treats one that has not
beaten for two minutes as a dead fetch and says which script to re-run.

Every fetch script stamps each row it writes with the date it ran, and the
build refuses any input whose stamp is not a date. That is what keeps a
table generated to exercise the code from reaching a payload, a figure or
this archive; it is a cheap guard against the one mistake this project
could not survive making.

Every fetch script is resumable: re-run it and it continues from the
species it has. `data/openalex_counts.csv`, `data/wikipedia_views.csv`,
`data/description_years.csv`, `data/avonet_slim.csv`,
`data/attractiveness_slim.csv`, `data/iucn_table1a.csv` and
`data/group_counts.csv` ship, so a reader can go straight to
`fetch_iucn.py` and the build.

## Keys

Two environment variables, read at run time and never from disk:

- `IUCN_TOKEN`: register at https://api.iucnredlist.org/ and generate a
  token; it arrives by email, usually within a day or two. The token is
  personal to the account, and by using it you accept the Red List terms
  (non-commercial, no redistribution). IUCN asks that a copy of any
  publication using the data be sent to them.
- `OPENALEX_KEY`: optional. Create a free account at https://openalex.org
  (no card) for $1.00 of usage a day; without a key the allowance is $0.10 a
  day and the script stops at that point and continues the next day.

## Cost of reproducing

OpenAlex meters list-and-filter calls at $0.0001 each. The per-species
fetch is one call per species, so the full run for 11,009 birds is about
$1.10: two days on a free key, eleven days without one. The class-level
fetch is ten calls. `data/openalex_run_log.txt` records what each run
actually cost, and the page quotes that log. Everything else is free.

Without `IUCN_TOKEN` the build still runs: it takes the Red List category
from the Santangeli et al. 2023 deposit, which carries the categories as
the authors had them in 2021, and stamps the payload
`redlist_source: santangeli_2021_fallback`. The shipped page is built from
the API (`redlist_source: api`), and `test_beauty.py` fails otherwise.

## What it does not claim

- That appeal causes neglect. Every input is observational; the page
  reports how the fit partitions among terms and no more.
- Anything across kingdoms. The class-level paper counts are drawn for
  five vertebrate classes only, because a name-based literature proxy
  fails for plants, insects and fungi (Stage 1, `RESEARCH.md` §4).
- A forecast of harm.

## Files

| File | What |
|---|---|
| `netutil.py` | the shared GET: descriptive User-Agent, backoff, clean stop on 429 |
| `fetch_*.py` | one script per source; each says what it writes and under what licence |
| `build_beauty.py` | join, two OLS fits with family fixed effects, g-computed category means, drop-one R², bootstrap |
| `fig_beauty.py` | the three figures through `sitefig.py` |
| `update_page.py` | renders `template.html` from the payload into `site/beauty.html` |
| `test_beauty.py` | the archive-contents check, the API-source check, the coefficient recomputation, the page drift check |
| `models.json` | the published species-level models and what each reports for threat status, with the read status of each |
| `manifest.json` | written by the build: the digest of the withheld Red List table, and a hash of every shipped input |
| `DATA_SOURCES.md` | every input, its licence, and whether it ships |
| `RESEARCH.md` | the Stage 1 feasibility document, the provenance record |
