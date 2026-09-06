# What a fast shoe is worth

Every published measurement of what an advanced-footwear racing shoe does to
the energy cost of running, collected into one table and put on one axis. The
thirteen laboratory comparisons range from 1.1% to 4.2%; the individual runners
inside the studies that report them range far wider, and three of the four
published ranges cross zero.

The finding is the spread, not the mean.

## Run it

```
python3 build_shoes.py           # the table -> outputs/shoes_payload.json
python3 fig_shoes.py             # four figures -> ../site/assets/shoes_f*.png, each audited (must print 0 problems)
python3 update_page.py --apply   # writes ../site/shoes.html from template.html and the payload
python3 test_shoes.py            # the failure modes this project is exposed to
```

Everything runs offline. There is no `fetch_data.py`: no public dataset carries
these numbers, so `data/studies.py` is itself the data. `fig_shoes.py` needs
matplotlib and Pillow and the site's `sitefig.py`, `fig_floor.py` and `fonts/`
one level up. The whole build takes a couple of seconds.

## What it computes

- The spread across the advanced-footwear comparisons: the extremes, the
  median, the ratio between them, and how many published a dispersion at all.
- Each published individual range: its width, and whether it crosses zero.
- The transfer coefficient between a metabolic saving and race time, as one
  published row divided by another, with its own interval from the two
  confidence intervals. **The derivation and the reason the rate is not one
  belong to `economy.html`**; this project recomputes the number rather than
  reading that project's payload, so neither can break the other, and
  `test_shoes.py` asserts the two agree.
- The laboratory range pushed through that coefficient — the only derived
  quantity here, carrying `assumed: true` into the payload and the word
  *assumed* onto the page — against the two intervals observed in real races.
- The counts the Limits section reports: rows with women, rows measured
  outdoors, rows measuring time rather than oxygen.

Nothing is fitted, smoothed or regressed. It is arithmetic over a sourced
table.

## The two rules the data obeys

**Sign.** `effect_pct` is positive when the energy cost of running fell. So
every `family="aft"` row is positive and every `family="mass"` row is negative,
and `build_shoes.py` refuses to run if one is not. The worst number this site
has shipped came from an operation on a signed field nobody had pinned down.

**Dispersion.** `sd_pct` and `ci_pct` are different quantities, are never both
set, and neither is derived from the other. Seven of the thirteen comparisons
published no dispersion at all; those rows are drawn as a dot and nothing else.
`test_shoes.py` checks this against the line collections actually on the axes,
not against the intention — the page's argument is about dispersion, so
inventing dispersion is its characteristic way to lie.

## Files

| File | What |
|---|---|
| `data/studies.py` | the declared table: 21 rows, each with sample, setting, note, source and DOI, plus the one study-to-colour map both figures read |
| `build_shoes.py` | the arithmetic; writes the payload |
| `fig_shoes.py` | the four figures, through `sitefig.py` |
| `template.html`, `update_page.py` | the page, every number from the payload |
| `test_shoes.py` | eight failure modes, the first read off the drawn output |
| `outputs/shoes_payload.json` | everything the page and figures read |
| `DATA_SOURCES.md` | every source, what it gives and what it lacks |
| `RESEARCH.md` | the Stage 1 research and feasibility memo, including the autopsy of the page this replaced; this is the only copy (`03 RESEARCH/shoe/` holds a pointer and the scratch work it superseded) |

## What it does not claim

It does not say which shoe to buy, and it cannot: nothing in the literature
predicts where an individual runner falls inside the published ranges, and no
free source gives shoe mass, stack height, foam type or plate geometry by
model, so the page compares studies rather than shoes.

It makes no causal claim about mechanism. Bending stiffness alone and midsole
energy return alone are each non-significant in meta-analysis; only their
interaction is. "The carbon plate does it" is not what the evidence says.

The table is a collection, not a systematic review. It was assembled by one
literature search, and it says so on the page.

There is no calculator and no interactive. The finding is a spread, and a
spread is a still picture — and the obvious widget, a slider from an effect
size to a predicted finishing time, would invite the reader to pick a number
the page exists to say nobody can pick for them.
