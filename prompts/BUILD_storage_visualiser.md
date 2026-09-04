# Build — battery revenue simulator, interactive

Read `prompts/_HOUSE_RULES.md` first. Then this.

**Do not start until the deslop pass's Phase 3 is committed, and do not run
this concurrently with the heat build.** Both touch `site/`, both want
`bust_cache.py`, both want a commit.

## What you are building

`storage.html` reports a perfect-foresight LP dispatch of a 1 MW battery
against 8,760 hourly prices, and shows that arbitrage value flattens above
about four hours of duration. There is no interactive. You are building one:
`site/storage-app.html`, standalone, own inline CSS, no shared nav, linked from
`storage.html` with `target="_blank"`.

## Read `storage/model.py` before you design anything

This is the hard one of the two builds, and the reason is in the source. Three
things are true simultaneously, and all three have to survive into the
interface.

**1. The optimiser cannot run in a browser.** The model is a linear program
solved with PuLP over 8,760 hours:

> max sum_t p_t·(dis_t − ch_t) − c_deg·(dis_t + ch_t)/2
> s.t. soc_{t+1} = soc_t + eta_c·ch_t − dis_t/eta_d, 0 ≤ soc ≤ E,
>      0 ≤ ch_t, dis_t ≤ P_max

GitHub Pages is static. There is no server to solve on. So a control that
changes an LP input cannot re-solve the LP live. Your options are: precompute a
grid of solutions and interpolate between them; implement a dispatch heuristic
in JS and be explicit that it is not the LP; or restrict interactivity to
things that do not require re-solving. **Whichever you choose, the interface
must say which it is doing.** An interactive that silently interpolates while
implying it optimised is the exact failure the house rule exists to prevent.

**2. The prices are synthetic.** From the docstring: real ERCOT settlement data
was not reachable, so the model generates a documented synthetic hourly year
calibrated to ERCOT DAM statistics — diurnal and seasonal shape, scarcity
spikes, occasional negative prices, seed 42. Drop a real CSV at
`storage/data/prices.csv` and it is used instead.

So every dollar figure this app can show rests on invented prices. That is
defensible and documented, but it must be visible in the interface, not only in
the source. Check first whether real ERCOT data is obtainable now — if it is,
getting it is worth more than anything else in this brief, and you should stop
and tell me rather than building on the synthetic year.

**3. Perfect foresight is an upper bound.** The model says so and says to note
it in write-ups. A real operator does not know tomorrow's prices. Whatever
revenue this app shows is a ceiling no battery achieves. Say so where the
number is.

Three stacked caveats is a lot to carry without the page becoming a disclaimer.
Solving that is the actual design problem here. Do not solve it by dropping
caveats.

## The question the app should answer

`DESIGN_AUDIT_EXTERNAL_2026-08-30.md` makes two points about this project that
are worth more than a generic explorer:

- **Finding 5**: the duration chart draws three near-equal zero-based bars
  ($98, $107, $111/kW-yr) to make a point about flattening, which makes the
  flattening invisible and at a glance suggests more duration keeps paying. The
  question is about the increment, so plot the increment: +$9 going 2h→4h, +$4
  going 4h→8h.
- **What's missing §4**: the page never answers what a reader actually wants to
  know — what does a battery *cost* per kW-yr? Does it pay? One line and one
  dashed line on the duration chart.

That second one is the strongest candidate for what this app is *for*. A
reader who can move the cost line and watch the payback duration move has
learned something no static figure on the site currently teaches. Treat it as
the leading proposal, not as an instruction — argue for something better if you
have one.

## Phase 1 — propose, then stop

Write `STORAGE_APP_PROPOSAL.md` at the repo root:

1. **Whether real ERCOT prices are obtainable.** Answer this first. It changes
   everything downstream.
2. **The computation strategy** — precomputed grid, JS heuristic, or restricted
   interactivity — with the honest tradeoff of each, and how the interface
   states which one is running. If precomputing, say what grid, how large the
   payload gets, and how interpolation error is bounded and disclosed.
3. **The question**, the controls, the reading. As with heat: fewer and better.
4. **How the three caveats are carried** — synthetic prices, non-live solve,
   perfect foresight — without burying the reader.
5. **What it will not do.**
6. **A sketch** I can look at.

Then stop and wait.

## Phase 2 — build, after I approve

Same rules as the heat build: standalone `site/storage-app.html`, own inline
CSS, no framework, no CDN, tokens taken from the winning deslop stylesheet
rather than invented, motion contract honoured, every contrast ratio computed
and passing AA, usable at 390×844, inside the size discipline, linked with
`target="_blank" rel="noopener"`, added to `sitemap.xml`, `bust_cache.py` run.

If you precompute, the generator that produces the payload goes in `storage/`
alongside `model.py`, is reproducible, and is named in the app's provenance
line. A payload nobody can regenerate is the defect two other apps on this site
already have — `skyline-app.html` and `bookshelf-app.html` have no source in
this workspace at all. Do not make it three.

**Do not publish.** Show me the local URL and stop.
