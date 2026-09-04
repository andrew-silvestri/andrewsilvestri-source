# Audit — the bookshelf

Read `prompts/_HOUSE_RULES.md` first. Then this.

You are auditing `site/bookshelf-app.html` (37 KB) and, where it bears on the
app, `site/desktop.html`. **Read-only.** Change nothing in `site/`.

## What this thing is

A desktop wallpaper built from a Goodreads export: your books as drawn spines,
or as a wall of their real covers brought to one finish. The page states that
**the CSV is parsed in the browser and never leaves it.** That is a privacy
claim about someone else's reading history, and verifying it is the first job
of this audit.

At 37 KB it is the smallest app on the site, which makes it the one where a
complete read of the source is actually feasible. Do that.

## The source is missing

`HANDOFF.md` §2 says this comes from `25 Desktop Gallery/` at the workspace
root, alongside a deliberately unpublished museum-wallpaper generator with a
`PUBLISHING-NOTE.md` about image permissions. **That folder does not exist** —
not at the root, not under `01 ARCHIVE/`. Confirm that yourself, report it, and
audit the artifact alone. Do not reconstruct the generator.

Note the second-order problem: if the unpublished museum generator's
image-permissions note is also gone, then whatever it was warning about is now
undocumented. Say so if you find that to be the case.

## Do your own work first

Do not open `DESLOP_AUDIT_2026-09-04.md`, `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`
or the checklist below until §5.

## 1. Verify the privacy claim

Do this before anything else, and be rigorous, because it is the one claim on
this page that could hurt someone if it is wrong.

- Read the entire file. At 37 KB you can.
- Enumerate every network call the app can make: `fetch`, `XMLHttpRequest`,
  `sendBeacon`, `WebSocket`, `EventSource`, dynamic `import`, an `<img>` or
  `<script>` whose `src` is built from user data, a form, an iframe, a CSS
  `url()` built at runtime. Report every one and what it carries.
- Cover selection is the likely edge: if covers are fetched by title, ISBN or
  Goodreads ID, then book identifiers **are** leaving the browser, to whoever
  serves those images. That may be entirely reasonable, but it is not "never
  leaves it", and the page would need to say so.
- Check for anything written to `localStorage`, `sessionStorage`, IndexedDB or
  a cookie, and whether it persists a stranger's library on a shared machine.
- Then verify by instrumentation, not only by reading: load a real CSV through
  Playwright with request interception on, and log every outbound request.
- State your conclusion plainly. If the claim holds, say it holds and on what
  evidence. If it needs qualifying, say exactly how the sentence should read.

## 2. Does it work

- Feed it a genuine Goodreads export. Their format has changed over the years —
  find out which columns the app requires and what happens when a column is
  missing, renamed, or empty.
- Malformed CSV: embedded commas, quoted newlines, a BOM, CRLF, non-ASCII
  titles, an empty file, a file that is not a CSV at all, a very large library.
- What does a reader see before uploading anything? Is the empty state an
  invitation or a blank?
- What does the output actually do — can the reader get the wallpaper out at
  their own screen resolution, and does the download work in the browsers
  people use? Note that a `<a download>` inside a sandboxed context can fail
  silently; check the real behaviour.
- Failure messaging: when something goes wrong, does the reader learn what to
  fix, or just see nothing happen?

## 3. Is it honest

- The spine drawings are invented — the app has no idea what these books look
  like. Is that stated?
- Where covers are real, where are they from, and what are the terms? The
  missing `PUBLISHING-NOTE.md` suggests someone once thought carefully about
  image permissions for a sibling feature. Whatever that reasoning was, check
  whether this shipped app respects it.
- Anything inferred from the CSV rather than read from it — genre, colour,
  ordering — labelled as inferred?

## 4. Measure it

Weight, cold load, time to usable. Type inventory, flag under 12px — the
external audit measured this app's control-panel labels at about 10px, so start
by confirming or refuting that. Compute every contrast ratio; the apps carry
their own inline CSS and were only partly swept in the 2026-09-04 palette
correction. Mobile at 390px: is a wallpaper builder meaningful on a phone at
all, and if not, does the page say so rather than offering a broken one?
Motion contract.

## 5. Then cross-check

`DESLOP_AUDIT_2026-09-04.md`, then `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` (its
finding 4 concerns `desktop.html` margin decorations colliding with the nav),
then the checklist below.

## 6. Write it

`AUDIT_BOOKSHELF_2026-09-04.md` at the repo root. Evidence in
`_audit-bookshelf/`, gitignored. Lead with the privacy verdict — it is the
finding that governs whether anything else matters. Then the rest, ranked.
Include **"What is good and must survive"**.

Then stop.

---

## Appendix — completeness checklist

**Do not read until §6 is written.**

<details>
<summary>Open only after your own findings are written.</summary>

- Cover fetching may send book identifiers to a third party, which would
  qualify the "never leaves the browser" claim.
- The generator folder, and its image-permissions note, are missing.
- Control-panel labels around 10px.
- Drifting book cards on `desktop.html` slide under the top nav.
- Goodreads export format drift breaking the parser.
- App-local CSS may still carry the 2.91:1 accent failure.

</details>
