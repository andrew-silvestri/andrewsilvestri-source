# Audit — the true climate cost calculator

Read `prompts/_HOUSE_RULES.md` first. Then this.

You are auditing `site/climate-cost-app.html` (277 KB) and, where it bears on
the app, `site/climate-cost.html`. **Read-only.** Change nothing in `site/`.

## What this thing is

Twenty products taken apart stage by stage — a tomato traced back through
fertiliser, ammonia synthesis and natural gas extraction — with the allocation
factor and the CO2e on every edge, and the lifetime of every vehicle exposed
rather than buried. The page's claim: **change the route and it recomputes,
instead of looking up an answer somebody prepared.**

That claim is testable, and testing it is the centre of this audit.

Source is in `climate-cost/`: `lca.py`, `engine.js`, `scene.js`,
`template.html`, `data/` (including `coast.json` and `processes.py`), and tests
`test_lca.py` and `test_scene.js`. **This app has its source and a test suite.**
Use both.

## Do your own work first

Do not open `DESLOP_AUDIT_2026-09-04.md`, `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`
or the checklist below until §5.

## 1. Is it really computing

- Read `engine.js` and `lca.py`. Are they the same model? There is a known
  pattern on this site of an engine existing twice and the two drifting — the
  atlas propagation engine lives in both `atlas-app.js` and
  `build_throughlines.py`, and `HANDOFF.md` §6 says they must agree and be
  verified for parity. Find out whether the same discipline was applied here.
  If the two implementations disagree anywhere, that is the headline finding.
- Run `test_lca.py` and `test_scene.js`. Report what they cover and, more
  usefully, what they do not.
- Then test the claim directly: change a route in the app and verify the output
  against an independent computation you do yourself from the same data. Pick
  at least three products, including one with deep chain nesting.
- Look specifically for precomputed answers. If any combination returns a
  stored value rather than a computed one, the page's central sentence is
  wrong, and that is worth knowing precisely.

## 2. Is the allocation honest

Allocation is where LCA hides its assumptions, and this page's pitch is that it
does not hide them.

- Every edge carries an allocation factor. Is the *method* stated — economic,
  mass, energy, system expansion — per edge, or only in general?
- The external audit describes a figure making the point that the same hide at
  2.2% economic and 7% mass allocation gives 3.66 versus 11.65 kg CO2e. Find
  where the app lets a reader see that choice, and whether it lets them change
  it.
- Where do emission factors come from? Named database, named publication, or
  unattributed? Check `data/processes.py` and report the provenance honestly.
- Vehicle lifetimes are claimed to be "exposed rather than buried" — verify.
- Cut-off: every LCA truncates its chain somewhere. Where does this one stop,
  and does the reader learn that the number they are looking at excludes
  everything past that boundary?
- Anything assumed and not labelled *assumed* is a house-rule violation. Say so
  plainly if you find it.

## 3. Does it work

Twenty products, every route, every control. Extremes and nonsense inputs.
What happens with a route that has no data — a real answer, a zero, or a blank?
Does the tree stay readable as it deepens? Is there any state worth sharing,
and does the URL carry it?

## 4. Measure it

Weight — what are the 277 KB, and how much is the process database. Cold load
and time to first interaction at both viewports, throttled. Type inventory,
flag under 12px. Compute every contrast ratio, including text over the chain
diagram; the apps carry their own inline CSS and were only partly swept in the
2026-09-04 palette correction. Mobile at 390px — a nested chain diagram is the
hardest thing on this site to make work on a phone, so say plainly whether it
does. Motion contract.

## 5. Then cross-check

`DESLOP_AUDIT_2026-09-04.md`, then `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`
(finding 8 and "What's missing" §8 concern this page), then the checklist
below. Append what each caught that you missed and vice versa.

## 6. Write it

`AUDIT_CLIMATE_COST_2026-09-04.md` at the repo root. Evidence in
`_audit-climate-cost/`, gitignored. Lead with the two claims — does it really
compute, and is the allocation honest — then the rest, ranked. Include
**"What is good and must survive"** and **"Engine parity"** stating whether
`engine.js` and `lca.py` agree and how you established it.

Then stop.

---

## Appendix — completeness checklist

**Do not read until §6 is written.**

<details>
<summary>Open only after your own findings are written.</summary>

- `engine.js` and `lca.py` may have drifted, with no parity test between them.
- The "one hide" figure on `climate-cost.html` reads as broken — one bar, no
  axis, no comparison, in a 650px-tall card.
- The 20-item table spans 0.56 to 75.49 with no inline bars, so the reader
  cannot see that a flight and a t-shirt are different animals.
- Emission-factor provenance may be thinner than the page implies.
- The cut-off boundary may be unstated.
- The chain diagram may be unusable at 390px.
- App-local CSS may still carry the 2.91:1 accent failure.

</details>
