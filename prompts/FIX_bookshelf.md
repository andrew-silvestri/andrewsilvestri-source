# Fix — the bookshelf

Acts on `AUDIT_BOOKSHELF_2026-09-04.md`, which you wrote. Read
`prompts/_HOUSE_RULES.md` and the **shared rules** at the bottom of this file.

## The blocking one: the privacy claim is wrong in a mode you ship

Your own instrumented evidence: default mode makes exactly one HTTP request.
Cover mode makes **one request per ISBN — 682 for a real 764-book export** — to
Open Library, redirecting to archive.org hosts. The app's own checkbox is
honest about this. Three other places are not: the home-page card ("never
leaves it"), `desktop.html` ("the ISBN and nothing else"), and the zip README.

This is a promise about a stranger's reading history, and it is the highest
priority on the site after the climate-cost fabrication. **Fix the claim, not
the evidence.**

"The ISBN and nothing else" is closer to true than "never leaves it", but it is
still wrong in a way that matters: an ISBN sent one-per-book, in order, to a
third party *is* the person's library, disclosed one row at a time. Say what
actually happens, to whom, and when.

Propose the wording; do not just write it. Give me two or three versions and
say which you would ship. Consider alongside them whether cover mode should be
opt-in with the disclosure at the point of the click rather than in prose
elsewhere — a checkbox that is honest in the app and dishonest on the page that
sends people to the app is a design problem, not only a copy problem.

## The rest, in the order your report ranked them

1. **Every cover failure reports as "no cover found."** A book with no ISBN
   (82 of 764 in the real export), a network error, a rate limit and being
   offline are four different facts and the reader gets one sentence for all
   four. Distinguish at least "no ISBN to look up" from "looked and failed".
2. **The "Cover art on file for N of M" summary is overwritten by `build()`
   and never appears.** It is the one honest accounting the app offers about
   its own coverage. Make it survive.
3. **Label-style spines** draw an empty paper label and put the title on the
   cloth, under 3:1 on 15 of 19 sampled. The label is there; use it.
4. **Upload is mouse-only.** The drop zone is not focusable and the file input
   is hidden. Make the whole flow reachable by keyboard.
5. **Two silent fallbacks** — a random width when page count is missing, 1960
   when the year is missing — are unlabelled. Under the house rule an assumed
   value is labelled assumed. Either mark those spines or stop inventing.
6. **Control boundaries at 1.02–1.24:1.** Below the 3:1 floor for UI
   boundaries. Fix with the tokens now in `style.css`, not new literals.

## What your report says is already fine

The parser survived every malformed fixture and two real Goodreads format
drifts; downloads verified across three browsers at 1080p, 4K and 8K; smallest
type is 11px not 10px; the drifting-cards overlap is gone. Do not re-litigate
any of that.

## One correction to my brief

I told you the museum generator was "gone entirely." You found it under
`dumpNew/PyProjects/`. I searched for a folder name and did not look where the
files actually were — the same mistake I made about the skyline source, which
is in `site/downloads/skyline-code.zip`. Note in your write-up whether the
missing `PUBLISHING-NOTE.md` means the image-permissions reasoning is genuinely
lost, because that is the part that would matter.

---

## Shared rules — every fix brief in this set

- **Fix the template or generator first**, then the shipped file, then prove a
  rebuild is a no-op. Shipped-vs-template drift is now the most common defect
  class in this repository; do not add another instance while fixing one.
- **Do not touch** `site/index.html`, `site/style.css`, `bust_cache.py`, or
  anything outside your own app and its page. A separate sweep collects the
  home-page copy, the cache stamp and the commit.
- **Do not run `bust_cache.py`. Do not commit. Do not publish.**
- Where a claim cannot be made true, **change the claim, not the data**.
- Recompute every contrast ratio you touch. AA or better.
- Write `FIX_BOOKSHELF_2026-09-04.md` at the repo root: what changed, the
  proposed wordings with your recommendation, the rebuild-is-a-no-op proof, and
  anything you decided not to fix and why.
- Stop when it is written. Give me the local URL.
