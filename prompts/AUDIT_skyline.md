# Audit — skylines, played

Read `prompts/_HOUSE_RULES.md` first. Then this.

You are auditing `site/skyline-app.html` (341 KB) and, where it bears on the
app, `site/skyline.html`. **Read-only.** Change nothing in `site/`.

## What this thing is

A skyline and a spectrum analyser are the same picture, so the picture is
played. Twenty-seven cities built from real building heights and coordinates;
turn on the spot and the sound turns with you. The page claims that what is
measured, what is assumed and what is invented are each labelled — **that claim
is the centre of this audit.**

## The source is missing, and that is finding zero

`HANDOFF.md` §2 says this app is built from `24 Skyline Sonifier/` at the
workspace root, with Austin, Nashville and Fort Worth carried in a
`supplement.py` from published tallest-buildings lists. **That folder does not
exist.** It is not at the workspace root, not under `01 ARCHIVE/`, and not
anywhere else in the workspace. `site/skyline-app.html` and `site/skyline.html`
are the only artifacts.

So:

1. Confirm this yourself before reporting it — search properly, including
   inside `site/downloads/` for a source archive, and check whether the app
   embeds enough to reconstruct its own provenance.
2. Report it as a first-class finding. A published page whose generator cannot
   be found is a page nobody can correct, regenerate or verify.
3. Then audit the artifact on its own terms, because that is all there is.

Do not reconstruct the generator. Do not regenerate anything. Say what is
missing and what that costs.

## Do your own work first

Do not open `DESLOP_AUDIT_2026-09-04.md`, `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`
or the checklist at the bottom of this file until §5.

## 1. Drive it

Serve locally (`python -m http.server 8802` from `site/`). Playwright, scratch
folder outside `site/`, gitignored. 1440×900 and 390×844, motion on and off.

Audio makes this harder than the other apps. Playwright can drive it with
autoplay policy relaxed; you can also inspect the Web Audio graph directly from
the page context rather than trying to listen. What you cannot verify by
instrumentation, verify by reading the code, and say which is which.

## 2. Does it work

All 27 cities. Every control. The "turn on the spot" interaction specifically —
what actually changes in the audio graph when the listener rotates, and does it
match what the page says happens.

- What happens on a browser that blocks autoplay until a gesture? Is there an
  affordance, or does it look broken?
- What happens with no audio output device?
- Does anything leak — an oscillator that keeps running after you navigate
  away, a graph that is rebuilt rather than reused on every change?
- Is there a way to stop the sound that a reader will find immediately?

## 3. Is it honest — the main event

The page's distinguishing claim is that measured, assumed and invented are each
labelled. Test it as a claim, not as a feature.

- Take the three cities `HANDOFF.md` names as special-cased (Austin, Nashville,
  Fort Worth). Does the app tell the reader those were handled differently from
  the other 24? If the supplement logic is embedded, extract and describe it.
- Where do building heights come from, and does the app say, per city or only
  in general?
- The mapping from height to frequency is an invention — a choice, not a
  measurement. Is it labelled as one, and is the actual mapping stated
  anywhere a reader can find?
- Same for amplitude, timbre, stereo placement, and anything spatial.
- Find anything presented as measured that is actually chosen. That is the
  failure mode that would matter most here.

## 4. Measure it

- **Weight.** What are the 341 KB? How much is city data, how much is code?
- **Cold load and time to first sound**, both viewports, throttled.
- **Type and contrast.** Every rendered size, flag under 12px; compute every
  ratio. The apps carry their own inline CSS and were only partly swept in the
  2026-09-04 palette correction — check whether this one still fails.
- **Mobile.** 390px with touch, not a narrow desktop window. Can a phone reader
  do the thing the page promises?
- **Motion contract.** Does `data-motion="off"` reach this app at all? Note
  that reduced-motion and reduced-audio are different preferences and a reader
  who wants one may not want the other — say what the app currently assumes.
- **Accessibility beyond contrast.** This is the one app on the site whose
  primary output is not visual. Is there any path through it for someone who
  cannot hear? Is there any for someone who cannot see? Do not turn this into a
  compliance checklist — say what is actually possible and what is not.

## 5. Then cross-check

`DESLOP_AUDIT_2026-09-04.md`, then `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`, then
the checklist below. Append what each caught that you missed and vice versa.

## 6. Write it

`AUDIT_SKYLINE_2026-09-04.md` at the repo root. Evidence in `_audit-skyline/`,
gitignored. Findings ranked, each with observation, cost, severity, fix cost.
Include **"What is good and must survive"** and **"What cannot be fixed without
the missing source"** — the second section is the one that decides whether this
page has a future.

Then stop.

---

## Appendix — completeness checklist

**Do not read until §6 is written.**

<details>
<summary>Open only after your own findings are written.</summary>

- The generator folder is missing from the workspace entirely.
- Whether the measured/assumed/invented labelling actually covers the
  height→frequency mapping, or only the height data.
- Autoplay-blocked first load reading as a broken page.
- App-local inline CSS may still carry the 2.91:1 accent failure corrected in
  the main stylesheet on 2026-09-04.
- No path through the app for a reader who cannot hear.
- Control labels below 12px.

</details>
