# Build — industrial heat break-even, interactive

Read `prompts/_HOUSE_RULES.md` first. Then this.

**Do not start until the deslop pass's Phase 3 is committed.** That pass
rewrites `style.css` and possibly markup across every page; landing this on top
of an uncommitted redesign creates a merge nobody wants. Check `git log` and
ask me if you are unsure.

## What you are building

`heat.html` explains when an electric boiler beats a gas boiler for industrial
process steam in Texas, and carries five static figures. There is no
interactive. You are building one: `site/heat-app.html`, following the site's
app convention — a standalone full-screen page with its own inline CSS, no
shared nav, linked from `heat.html` with `target="_blank"`.

## The good news, and why this app is the easy one of the pair

Read `heat/model.py` before designing anything. The model is:

> LCOH = fuel + levelized capex + fixed O&M, all per MMBtu of useful heat
> delivered to process.

That is closed-form algebra. It runs in JavaScript, exactly, in microseconds.
The break-even is the electricity price at which the two LCOH expressions are
equal — also closed form. **This means every number the interactive shows can
be genuinely computed from the reader's inputs, with no approximation and no
precomputed lookup.** Build it that way. If you find yourself interpolating
between stored results, you have taken a wrong turn.

Port the model faithfully. `heat/model.py` is the model of record; your JS is a
second implementation of it, which means the atlas problem applies — two
engines that must agree. Write a parity check: sample the input space, run both,
assert agreement to a stated tolerance, and keep it as a test. `HANDOFF.md` §6
describes the same discipline for the atlas engine; follow it.

There is a Julia version in `heat/julia/model.jl` and an Octave version in
`heat/octave/model.m`. If they disagree with the Python, that is a finding to
report before you build on either.

## The honesty problem, which is smaller here but real

`heat/model.py`'s own docstring says its baseline numbers are **placeholders**
traceable to a source assumption table (LBNL/DOE IAC Tipsheet #3, NREL EFS,
Zuberi et al., EPA), and that prices should be updated from EIA before use —
there is a template at `heat/data/eia_price_template.csv`.

So the interactive must not present its defaults as current market prices. Per
the house rule, anything assumed is labelled *assumed* where the reader is
looking, not in a footnote. Decide how to do that without turning every control
into a disclaimer, and say what you decided and why.

Check whether current EIA figures are obtainable and, if they are, whether the
honest move is to ship them as the default with a stated retrieval date.
Do not invent a price.

## Phase 1 — propose, then stop

Do not write the app yet. Write `HEAT_APP_PROPOSAL.md` at the repo root
covering:

1. **What question the reader arrives with**, and what they should be able to
   answer after two minutes. `heat.html`'s existing claim is that break-even
   electricity is about 1.5 cents/kWh at $3.50 gas and that capital cost barely
   moves it. An interactive that only restates that is not worth building — the
   figure already does. What can a reader learn by *moving* something that they
   cannot learn from a static plot?
2. **The controls**: which parameters, over what ranges, with what defaults, and
   why those and not others. Fewer and better beats a wall of sliders.
3. **The reading**: what is on screen, and what changes when a control moves.
   The site's strongest figures direct-label rather than legend, and name the
   break-even point on the plot — `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` calls
   the heat figure suite the best on the site and the template others should
   follow. Do not throw that away for a generic chart.
4. **How the provenance and the placeholder status are shown.**
5. **What it will not do**, and why. Scope this to one question answered well.
6. **A sketch** — a static mock, or a rough working page, enough that I can see
   it rather than imagine it.

Then stop and wait.

## Phase 2 — build, after I approve the proposal

- `site/heat-app.html`, standalone, own inline CSS, no framework, no CDN.
  Match whichever stylesheet option won the deslop pass — read
  `DESLOP_OPTIONS_2026-09-04.md` and the current `site/style.css` and take the
  tokens, do not invent a second palette.
- Compute in the browser from the reader's inputs. No stored answers.
- Honour the motion contract (`data-motion="off"` stops anything that moves).
- Compute every contrast ratio; AA or better. The main palette was corrected on
  2026-09-04 — use `--acc-fill`, not raw `--acc`, behind white text.
- Usable at 390×844. If a control cannot work on a phone, design for the phone
  first rather than shipping a desktop app with a broken narrow layout.
- Keep the page under the site's 300–600 KB discipline. It should not be close.
- Link it from `heat.html` with `target="_blank" rel="noopener"`, add it to
  `sitemap.xml`, and check whether `code.html` should carry its source.
- Ship the parity test in `tests/`.
- Run `python bust_cache.py`.
- **Do not publish.** Show me the local URL and stop.

## What good looks like

The heat figure suite is already the best work on this site — serif annotations
inside the chart matching the body face, direct labels instead of legends, the
break-even and parity points named on the plot. The interactive should feel
like those figures gained a control, not like a calculator was bolted to the
page.
