# Climate cost — remove a fabricated claim, then rebuild the showcase honestly

Read `prompts/_HOUSE_RULES.md` first. This brief acts on
`AUDIT_CLIMATE_COST_2026-09-04.md`, which you wrote.

**This is publish-blocking.** Phase 3c cannot ship while a false number is on
the page. It is also a content job, not a presentation job, so the deslop
brief's "do not change content" rule does not apply here — but every rule about
sourcing does, twice over.

## What is wrong

The video and poster say the leather shoe goes from 3.66 to 11.65 kg CO2e
("triples") under 7% mass allocation. The arithmetic is
`3.66 × (7 ÷ 2.2) = 11.645`. That operation scales the **whole shoe** by the
ratio of allocation factors, which is only valid if the shoe were entirely
hide. It is not: the hide stage is about 9% of the total. The model gives
**4.40 kg, ×1.2**.

The same claim is in prose at `climate-cost/data/processes.py:1079` — *"By mass
it would be about 7%, and the shoe would triple"* — which ships inside the
downloadable source archive, so it is wrong in two places.

No Python file in the repository references `climate_allocation`. The `.mp4`
and its poster cannot be regenerated. They are orphans, the third pair on this
site after `skyline-app.html` and `bookshelf-app.html`.

The decision is to **move the showcase to a product where allocation genuinely
dominates**, rather than tell a quieter true story about the shoe.

---

# Phase 1 — the prerequisite, and then the search

## 1a. Disambiguate the `allocation` field first

Your own audit found `allocation` holding `1.6` and `1.2`. **An allocation
share cannot exceed 1.** The field carries at least three different meanings —
share of a joint product, amortisation over a lifetime, and shipment mass.

This is not a side issue. The entire task is "vary the allocation factor and
see what moves," and **you cannot vary a field that means three things**. That
ambiguity is also the most plausible mechanism for how the original error was
made: if `allocation` sometimes means share and sometimes means amortisation,
then "scale it from 2.2% to 7%" is not a well-defined operation and no reader
could have caught it.

Split it into three named fields. Migrate every process. The parity test must
still pass and every published total must be unchanged — this is a rename, not
a remodel, and if any number moves you have found a second bug and should stop
and say so.

## 1b. Then compute the sensitivity across all twenty products

For every product, for every stage carrying a real allocation *share*, compute
what the total becomes under an alternative allocation basis. Report a table:
product, contested stage, that stage's share of the total, the factor under
each basis, and the resulting swing.

**Do not assume the answer.** I suggested cheese and beef because they carry
0.85–0.90 on stages that look dominant. That is a hypothesis from reading, not
a measurement, and acting on it unverified would repeat the exact failure this
brief exists to correct.

## 1c. Every counterfactual factor must be sourced

The original error was not only arithmetic — "about 7%" was itself unsourced.
For any product you propose, the alternative allocation factor must come from a
named publication or standard, quoted with its number, or the product is
disqualified however good the story is. Your audit found only 4 of 42 processes
carry a citation; **prefer a showcase product whose numbers are among the
cited ones**, and say so in your reasoning.

If no product in the set has both a large, real swing and a sourceable
alternative factor, say that plainly. "The honest showcase does not exist in
this data" is a valid finding and I would rather have it than a manufactured
one.

## 1d. Stop

Present the table, your two or three candidates with their sourcing, and your
recommendation. Do not build anything. Do not touch `site/`.

---

# Phase 2 — after I choose a product

1. **Remove the false assets.** Delete `site/assets/climate_allocation.mp4` and
   `climate_allocation_poster.png` and every reference to them. Do not keep
   them "for reference"; an orphan asset with a false number in it is exactly
   how this survived.
2. **Correct `processes.py:1079`.** State the true sensitivity for the shoe —
   hide is ~9% of the total, mass allocation moves it ×1.2 — and label the
   alternative factor's source, or drop the counterfactual from the note if it
   cannot be sourced.
3. **Build the new showcase with a generator that lives in the repo.** A script
   in `climate-cost/` that produces the figure from the data, reproducible,
   named in the page's provenance. This is non-negotiable: the reason a false
   number survived is that nobody could regenerate the thing that carried it.
4. **Watch the template trap.** Your audit found `climate-cost-app.html` ships
   fixes (palette, `touch-action`) that `template.html` lacks, so a rebuild
   reverts them. Reconcile the template before any rebuild, or you will fix one
   bug and reintroduce two.
5. Re-run the parity test and both suites. `python bust_cache.py`. Do not
   publish.

## Write-up

`CLIMATE_COST_FIX_2026-09-04.md`: the field migration and proof that no total
moved, the sensitivity table, the sourcing for whatever you chose, and what the
new showcase claims in one sentence you would be willing to defend.

Add a line to `HANDOFF.md` §8 as a trap: a claim that flatters the page's own
argument is the one nobody audits. That is the actual lesson here, and it is
worth more than the fix.
