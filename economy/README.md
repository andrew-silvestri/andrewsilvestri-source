# Economy is not time

The code behind [economy.html](https://andrewsilvestri.com/economy.html).

A four per cent gain in running economy is not four per cent off a marathon.
The exchange rate between a metabolic saving and race time is about seven
tenths at racing paces, it varies with how fast the runner is going, and above
about a 3:52 marathon it is below one — so the faster you already are, the less
a given saving is worth. This page computes that exchange rate from published
cost-of-running curves and checks it against the one place it has been measured
directly.

## Running it

```
python3 fetch_data.py       # verify the two cohort tables against pinned hashes
python3 build_economy.py    # -> outputs/economy_payload.json
python3 fig_economy.py      # -> ../site/assets/economy_fig*.png
python3 update_page.py --apply
python3 test_economy.py
```

Python 3.12 with `openpyxl`, `matplotlib` and `pillow`. Both data files ship in
this archive, so nothing needs downloading; `fetch_data.py` re-fetches the
Vickers table from Springer if it is missing and hash-checks whatever it finds.

## What is here

| File | What it does |
|---|---|
| `model.py` | The physics. Five published cost-of-running curves, the elasticity of speed to metabolic cost, the finite solver behind it, both routes to the transfer coefficient, and the compounding identity. No fitting anywhere. |
| `fetch_data.py` | Verifies the two cohort tables by SHA-256 and stops the build on a mismatch. |
| `build_economy.py` | Writes `outputs/economy_payload.json`: every number the page states, each with a `source`. Refuses to write if the transcribed coefficients do not reproduce the source paper's own results. |
| `fig_economy.py` | The four figures, through `sitefig.py`, with the layout and size-floor audit. |
| `template.html`, `update_page.py` | The prose, and the generator that fills it from the payload. |
| `test_economy.py` | This project's own failure modes. See below. |
| `DATA_SOURCES.md` | Every source, what it contributes, its licence, and what was deliberately not used. |
| `RESEARCH.md` | The Stage 1 research document, moved here as the provenance record. It concluded that the brief's central claim did not survive, which is why this page is about the exchange rate and not about compounding. |

## The test that matters, and its limit

The page is arithmetic over five transcribed polynomials, so a single wrong
digit would move every number together and move it quietly. Nothing in the
site's layout audits or its drift check would see it.

The obvious defence is that the source paper states three results of its own,
so the transcription can be made to prove itself. That check is in place and it
catches gross errors: a sign flip on the linear term lands a quarter of a
percentage point out.

**It is weaker than it looks, and the weakness was measured rather than
assumed.** Perturbing any single coefficient by one per cent or less passes it.
A five per cent error in the linear term actually *lowers* the residual to
below what the correct coefficients give. The three published results are all
ratios evaluated at two speeds, so errors in different terms trade off inside
them. Reproducing a paper's stated percentages is good evidence about the shape
of a curve and weak evidence about its coefficients.

So the coefficients are also held in two places — `model.py` and
`test_economy.py` — and compared digit for digit. That is what actually guards
the page: any edit fails immediately whether or not it moves a published
number, and a curve refitted to other data cannot be substituted quietly.

## What this page will not do

It will not tell you what a shoe will do for you, because the published
measurements of advanced footwear disagree with each other by a factor of
nearly four and individual response spans more than twenty percentage points.
That is a separate subject.

It has no calculator. The exchange rate is a function of one variable, so a
curve shows every reader their own answer at a glance while a slider would show
one point of it at a time. And a calculator would have to accept the three
terms as independent inputs, which is the one thing the literature says they
are not.

Nothing here comes from a training manual. *Advanced Marathoning* and books
like it are copyrighted, their tables and prescriptions cannot be reproduced,
paraphrased closely or rebuilt as a calculator, and none was consulted. The
test fails the build if any source string names one.
