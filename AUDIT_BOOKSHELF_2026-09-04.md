# Audit — the bookshelf (`site/bookshelf-app.html`, `site/desktop.html`)

Date: 2026-09-04. Read-only; nothing under `site/` was changed. Evidence in
`_audit-bookshelf/` (gitignored): `results.json` (every measurement below),
`shots/`, `fixtures/`, `run.js` (the Playwright harness), `curl_headers.txt`,
`concurrent-worktree-changes.diff`.

**What was audited.** `site/bookshelf-app.html` at HEAD `37401cc`, md5
`e12b1b47a0e243c62ea1bb850615bfd6`, 37,526 bytes, 906 lines, read in full.
`site/desktop.html` at HEAD and, because it changed under me (see
"Disclosures"), also in the working tree.

## Disclosures, first

- **The sealed appendix was shown to me before §1.** The brief's checklist is
  inside a `<details>` block in the same file, and `cat prompts/AUDIT_bookshelf.md`
  printed it. I read it once at the start and did not return to it until §5. Every
  finding below was reached from the source and the instrumentation, and the
  cross-check section says which checklist items I confirm, refute, or find
  already resolved.
- **The working tree changed during the audit.** The session began clean. Partway
  through, fourteen files under `site/` were modified by something other than
  this session: the motion contract was rewritten to `prefers-reduced-motion`
  only (the footer toggle and `localStorage` override removed), `desktop.html`
  gained `main.notes` and `grid-row: span 21` on its marginalia, and
  `style.css` changed by 147 lines. `bookshelf-app.html` was **not** touched
  (md5 above matches HEAD). desktop.html measurements are reported for both
  versions. Diff saved as evidence.
- **A real export was used.** `C:/Users/dasil/Documents/0 - Inbox/goodreads_library_export.csv`
  (764 rows, the owner's own) was fed to the app on this machine only. The
  privacy runs against it had every non-localhost request aborted at the browser,
  so no ISBN from it reached anyone. Only aggregate counts of it appear here.
- **Live requests to Open Library were made from this machine:** 44 (the demo
  shelf) and 3 × 130 synthetic ISBNs (the rate-limit probe). ~430 in ~15 minutes.

---

## 1. Privacy verdict

**In its default mode the claim holds, on evidence, and is stronger than the
page says. In cover mode the reader's ISBNs leave the browser, one request per
book, and the sentence on `index.html` does not say so.**

### What the source can do (full read)

The only network primitive in 906 lines is `new Image()` at `bookshelf-app.html:359`,
inside `fetchCovers`, reached only from `startCovers()`, which runs only when the
"Real covers" checkbox is checked (lines 814, 817, 877, 898). There is no
`fetch`, `XMLHttpRequest`, `sendBeacon`, `WebSocket`, `EventSource`, dynamic
`import`, `<form>`, `<iframe>`, `<script src>`, CSS `url()`, or `navigator.*`
call anywhere in the file (grep, zero hits). The page loads no stylesheet, font,
script or image from anywhere. Nothing is written to `localStorage`,
`sessionStorage`, IndexedDB or a cookie; the library lives in a `var` and is gone
on reload, which is the right behaviour on a shared machine.

### What the browser actually sent (Playwright, Chromium, request interception)

| run | what happened | requests leaving 127.0.0.1 |
|---|---|---|
| default mode, real 764-book export, shelf switched to Everything, Rearrange, Fit every book, wood changed, PNG downloaded | 1 request total, the HTML | **0** |
| cover mode, same export, Read then Everything (all remote requests aborted at the browser) | app attempted one `GET` per unique ISBN | **682**, all to `covers.openlibrary.org` |
| `?covers=1` in the URL, fresh load, no file | box pre-ticked, demo ISBNs requested before any click | 44 |
| cover mode, demo shelf, live | 44 to Open Library → 46 `302`s → `archive.org` and seven `ia*.us.archive.org` hosts; 43 covers, 1 `404` | 90 |

Each cover request is `https://covers.openlibrary.org/b/isbn/<ISBN>-M.jpg?default=false`,
sent with `Referer: <origin>/` (origin only, per the default referrer policy),
`Origin`, `User-Agent`, and the reader's IP. No cookies in either direction
(`crossOrigin="anonymous"`; response has no `Set-Cookie`, `curl_headers.txt`).
The 302 then takes the browser to Internet Archive download hosts (the redirect
URL carries an Open Library cover id, not the ISBN, but the same IP and referer).
CORS is confirmed live: `Access-Control-Allow-Origin: *`, which is what lets the
canvas read the pixels; a multi-year history of GitHub issues says this header
has been absent at times, so cover mode depends on a third party's config.

### Is that disclosed?

- **`bookshelf-app.html` — yes, well.** "Offline by default: the CSV is parsed here,
  the shelf is drawn here, the PNG is written here" (line 82) and, on the checkbox
  itself, "The one thing that uses the network: each book's published cover is
  fetched from Open Library by the ISBN in your export" (line 98). That is honest
  and in the right place.
- **`index.html:114` — no.** "The CSV is parsed in the browser and never leaves
  it." The CSV file does not leave; the ISBN column does, in cover mode, and a
  list of ISBNs is exactly the sensitive part of a reading history. Unqualified.
- **`desktop.html:62` — overstated.** "the request carries the ISBN and nothing
  else." It carries the ISBN, the reader's IP, browser identity, and the site
  origin, and is answered by a redirect to archive.org. "Nothing else *from your
  file*" is what is true.
- **`downloads/bookshelf-code.zip` README — same problem as index**, "Nothing
  leaves the page", corrected two paragraphs later.

### How the sentences should read

- index.html: "The CSV is parsed in the browser and never leaves it. The optional
  cover mode sends each book's ISBN to Open Library, and nothing else."
- desktop.html: "the request carries the ISBN and nothing else from your export —
  Open Library (an Internet Archive project) sees the ISBN, your IP address and
  this site's address, as any image request would."

Two smaller points that belong under privacy:

- **`?covers=1` turns the network on by link** (line 898). The checkbox is
  visibly ticked, so it is not hidden, but a shared link puts the box in the
  "on" state before the reader has read what it does, and a file dropped
  afterwards is looked up immediately (line 877). Low severity; either drop the
  parameter or make it only pre-tick without fetching.
- **Scale.** A 764-book export produces 682 requests in a burst of six at a time
  from the reader's IP. Open Library's covers documentation says the API "is
  intended for displaying covers on public facing websites and not for bulk
  download" and that ISBN lookups are limited to 100 requests per IP per 5
  minutes, answered with `403`. I sent 3 × 130 synthetic ISBNs (all `404`,
  4.5 s per batch) and 44 real ones inside 15 minutes and saw **no 403**; the
  limit is documented but was not enforced today. If it ever is, see finding 2.

---

## 2. The source is missing — confirmed, with a correction

`25 Desktop Gallery/` does not exist at the workspace root, under `01 ARCHIVE/`
(which holds 10, 11, 13, 14, 15, 16, 17, 18, 20, 21), or anywhere within depth 4
of the workspace. `HANDOFF.md:65` still points to it and to its
`PUBLISHING-NOTE.md`. No `PUBLISHING-NOTE.md` exists within depth 4 of the workspace, including inside the museum folder below.

**The correction:** the house rules say 24 and 25 "are gone entirely". Half of 25
is not. The museum-wallpaper generator survives at
`dumpNew/PyProjects/philbrook_museum/` (`museum_app.py`, 17 KB, PyQt6;
`artworks.json`; `images_full/`; a venv), which is also where the `PyProjects/`
folder that `HANDOFF.md:66` places at the root actually lives. What is gone is
the permissions note, so **whatever it warned about is now undocumented**: the
only trace of the reasoning is the fact that the museum app ships a folder of
artwork images and was never published. The bookshelf app's own source has no
copy outside the artifact; the zip in `site/downloads/` is the same file one
line older (see finding 12).

I did not reconstruct the generator.

---

## 3. Findings, ranked

### F1 — The privacy sentence on `index.html` is unqualified · **high** (governs everything else)
Covered in §1. The app page is honest; the home-page card and the zip README
say "never leaves" / "nothing leaves" without the cover-mode qualifier.

### F2 — Every cover failure is reported as "no cover on file" · **medium-high**
`build()` computes `omitted` as books whose cache entry is not an object (line
465), and `img.onerror` sets `"none"` for *any* failure (line 365): a 404, a 403
rate-limit, a CORS refusal, a blocked tracker list, or being offline. Books with
no ISBN are never looked up but are counted the same way. Instrumented: with
the network blocked the caption read "764 left off (no cover on file)"; in the
real export **82 of 764 rows have no ISBN at all** and would be reported as
"no cover on file" while never having been asked for. Under the house rule,
"no cover on file" is a claim about Open Library's holdings that the app cannot
make; it should say "no cover fetched (N had no ISBN, M not found, K failed)".

### F3 — The cover-mode summary line never appears · **medium** (bug, confirmed live)
`startCovers`'s completion callback writes "Cover art on file for 43 of 44
books" to `#stats` and then calls `build()` (lines 849–851); `build()` ends by
overwriting `#stats` because `coverStatus` is now false (line 570). Observed:
"Covers: 35 of 44 checked…" at 5 s, then "Showing the built-in demo shelf. 44
books." from 10 s on, forever. The only surviving trace is the caption's
"1 left off". Fix is to set `coverStatus = false` *after* `build()`, or to make
`build()` not touch `#stats`.

### F4 — Label-mode spines carry an empty label and near-invisible title · **medium**
`drawSpine` in `label` mode paints a cream label at 8–32 % of the spine height
(line 697), sets `ink = "#1c1a14"` (line 699), then draws the title at 52 %
height — on the cloth, not the label. Computed: that ink is under 3:1 on
**15 of the 18** cloth colours (1.59:1 to 2.94:1), and `label` is the dress
for 28 % of pre-1900 and 45 % of 1900–1960 books. `shots/crop_labels2.png`:
"Bleak House", "Ulysses", "Les Misérables" on the demo shelf. Either the title
belongs on the label (and the label should be tall enough for it) or the ink
should follow the `lum2` rule the other modes use.

### F5 — Upload is mouse-only · **medium** (accessibility)
`#drop` is a `div` with `onclick`, no `tabindex`, no `role`, no key handler;
`#file` is `display:none`. Tab order measured: shelf → covers → w → h → mine →
wood → fit → shuffle → dl → body. A keyboard or switch user cannot load a file.
The canvas has no accessible name. Every other control is labelled.

### F6 — Control boundaries fail non-text contrast · **medium**
Text passes everywhere (below). The boxes do not: input/select fill `#0d1017`
on panel `#10131b` = **1.02:1**, their border `#232636` = **1.24:1**, button
fill `#161a26` = **1.07:1**, drop-zone dashed border `#4d4685` = **2.24:1**.
WCAG 1.4.11 asks 3:1 for a control's boundary. The number fields are located
by their label and their text, not by any edge.

### F7 — A file dropped anywhere but the 300 px box replaces the app · **medium-low** (from source, not instrumented)
Only `#drop` prevents default on `dragover`/`drop` (lines 860–865). A CSV
dropped on the canvas or the panel is handled by the browser, which navigates
to the file and unloads the page, library and all. A synthetic drop cannot
reproduce browser navigation, so this is from reading; a `document`-level
`dragover`/`drop` `preventDefault` is the usual guard.

### F8 — Two inferences are not labelled as inferred · **medium-low** (house rule)
- Missing page count → width from a hash-seeded random 180–500 pages (line
  507). 8 of 764 real rows. The panel says "its width from its page count".
- Missing year → dressed as 1960 (lines 649, 721). 96 of 764 real rows lack
  "Original Publication Year"; all had "Year Published", so the fallback chain
  covered them, but the 1960 default is silent when neither is present.
- A custom exclusive shelf (the real export has `did-not-finish`) is not
  offered in the menu and is folded into "Unread". Fine, but unstated.
The "What is real here" panel is otherwise the best statement of provenance on
the site; these are its three gaps.

### F9 — Three text styles under 12 px · **low**; external "~10 px" refuted
Measured computed sizes: `h2` 11 px (uppercase, tracked), `.check .sub`
11.5 px, the `#drop` hint 11.5 px, `#cap` 12 px, labels and `p.small` 12.5 px,
controls 14 px. Nothing is at 10 px; the smallest is 11 px. On the phone the
controls go to 16 px (no iOS zoom); the three small styles do not.

### F10 — Cover art rights are unstated, and the reasoning that once existed is lost · **low-medium**
Open Library disclaims any rights over covers; the Internet Archive's rights
page puts non-infringement on the user. Compositing a reader's own covers into
a wallpaper for their own screen is about as low-risk a use as exists, and the
page does not distribute the result. But the site says where the images come
from and nothing about whose they are, and the sibling generator's
`PUBLISHING-NOTE.md` — the one place this was thought through — is gone (§2).
One sentence on `desktop.html` ("the covers remain their publishers'; the
wallpaper is for your screen") would close it.

### F11 — Cover images are stretched, and "untouched" is slightly generous · **low**
Aspect is clamped to 0.52–0.85 (line 489), so a square or very tall cover is
distorted to fit. Exposure, saturation, warm wash and grain are all applied
before "untouched except for one shared finish" — the phrase is fair, the
clamp is not covered by it.

### F12 — The downloadable zip is one line behind the shipped app · **trivial**
`bookshelf-code.zip/bookshelf-app.html` (10 Aug) differs from the shipped file
only at line 10: the two `--acc-fill*` tokens added by the palette sweep, which
nothing in the file uses. Harmless dead tokens; the zip's README carries the
same "nothing leaves" wording as F1.

### F13 — Smaller things
- `FileReader.onerror` is not handled; a read failure is silence.
- The series-stripping regex `\s*\(.*?\)\s*$` also removes a genuine
  parenthetical at the end of a title.
- Author surname is the last whitespace-separated token: "Le Guin" → GUIN.
- The five-star gilt dot is explained on `desktop.html`, not in the app.
- At 1280×800 the control column is 1161 px tall and scrolls internally;
  the primary Download button sits below the fold with no scroll affordance.
- Empty shelves get no board: at 1920×1080 the caption says "44 of 44 books on
  4 shelves" but only 3 boards are drawn and the bottom quarter is bare wall
  (`shots/dl_webkit_1920x1080.png`). Either draw the board or say 3.
- `desktop.html` marginalia de-accent names (Bronte, Miserables, Garcia
  Marquez) that the app's demo data spells with diacritics.
- Chromium's PNG encoder writes 1.7 MB at 1080p and 10 MB at 8K where
  Firefox writes 0.44 MB and 2.0 MB for the same canvas. Not the app's fault;
  worth a note next to the button for 4K+ readers.

---

## 4. Does it work

**The real export (764 rows, 2026 format).** Its header has 23 columns —
"Average Rating" is absent, which differs from the 24-column list Goodreads'
own forum describes, so the format has drifted at least twice (five purchase
columns removed mid-2022; this one since). The app needs only `Title` and
`Author` (line 251) and reads `Number of Pages`, `Original Publication Year`,
`Year Published`, `Exclusive Shelf`, `My Rating`, `ISBN13`, `ISBN`,
`Bookshelves`, all by case-insensitive header name, so neither drift touches
it. Parsed: 764 books, 55 read, 3 currently reading, 705 to-read, 9 user
shelves offered with counts. ISBN cells arrive as `"=""9780…"""` and are
cleaned correctly. Fit every book: 764 of 764 on 13 shelves at 1400×900.

**Malformed input** (`fixtures/`, all uploaded via the real `<input type=file>`):

| file | result |
|---|---|
| current format, embedded commas, quoted newlines, `"` inside a shelf name, `<b>` in a shelf name, CJK, Hebrew, emoji titles | all 10 rows parsed; shelf names HTML-escaped in the menu |
| BOM + CRLF | identical result |
| `Author` column removed | "That file has no Title and Author columns — is it the Goodreads export?" |
| `Title` renamed | same message |
| `ISBN13` column removed | parsed; falls back to `ISBN` |
| pages and both years empty | parsed; widths and dress from the silent fallbacks (F8) |
| only `Title,Author` | parsed, 10 books |
| header only / empty file / PNG bytes / JSON / semicolon-delimited / tab-delimited | same one message |
| 5,000 rows | parsed in 4.4 s; Fit every book in 0.34 s → 4,622 of 5,000 on 36 shelves, the rest reported in the caption |

No page errors in any case. The single error message is accurate for six
different failures; a semicolon or tab file gets no hint that the delimiter is
the problem.

**Before uploading** the reader sees the 44-book demo shelf drawn at their own
screen's pixel size, with "Showing the built-in demo shelf" — an invitation,
not a blank. All 44 demo ISBNs pass the ISBN-13 checksum.

**Output.** Width/height default to `screen.width × devicePixelRatio`, which is
the physical resolution, and are clamped 640–7680 × 400–4320. Download is
`canvas.toBlob` → blob URL → `a.click()`. The page is opened top-level via
`target="_blank" rel="noopener"`, not in a sandbox, so the `<a download>` caveat
does not apply. Verified end to end, file saved and PNG header read:

| browser | 1920×1080 | 3840×2160 | 7680×4320 |
|---|---|---|---|
| Chromium 151 | 1.68 MB ✓ | 3.96 MB ✓ | 10.1 MB ✓ |
| Firefox | 0.44 MB ✓ | 0.83 MB ✓ | 1.99 MB ✓ |
| WebKit (desktop) | 0.28 MB ✓ | 0.43 MB ✓ | 0.73 MB ✓ |

All nine files open as valid PNGs at the requested size with the shelf drawn
(`shots/dl_*_1920x1080.png`); the size spread is the three PNG encoders, not
the app.

iOS Safari was not available; its per-canvas pixel ceiling (historically
16.7 M px) would refuse 5K and above, and the app has no message for a canvas
that silently comes back blank.

**Failure messaging** is the weak side: one message for bad files, a clobbered
summary for covers (F3), a misattributed reason for every missing cover (F2),
silence for a read error.

---

## 5. Is it honest

- **The spines are invented, and it says so** — twice, well: "Chosen: the
  drawn spines — a design keyed to each book … No database of photographed
  book spines exists, for any price, so this page does not pretend to one"
  (app), and the "Two shelves, one honest split" section on `desktop.html`.
  This is the model for the rest of the site.
- **Covers are real and their source is named** on both pages. Their *terms*
  are not (F10).
- **Inferred vs read:** width from page count and dress from era are stated;
  the fallbacks when those fields are empty are not (F8). Colour is stated as
  chosen. Ordering is a hash of title, author and seed — "deterministic per
  title" is stated on `desktop.html`; "Rearrange" makes it clear it is not
  meaningful.
- The demo shelf's comment says "page counts are of commonly printed
  editions and only set spine width" — correctly labelled as assumed.

---

## 6. Measurements

**Weight and load.** One request, 37,526 B (13.6 KB gzip, 11.5 KB brotli),
no fonts, no scripts, no images. First shelf drawn 96 ms after navigation
start on localhost. This is the lightest interactive on the site by a factor
of ten.

**Text contrast** (computed from the inline CSS; all pass AA):

| pair | ratio |
|---|---|
| ink `#e8e6f0` on panel `#10131b` | 15.04:1 |
| dim `#8b8fa3` on panel (labels, h2, hints, stats) | 5.80:1 |
| dim on bg `#0b0d12` (caption) | 6.07:1 |
| accent `#8b7ff2` on panel (checkbox) | 5.67:1 |
| primary button: `#0b0d12` on `#8b7ff2` | 5.94:1 |
| `--acc-fill #5a4fb0` (defined, unused) on panel | 2.81:1 |

The 2.91:1 failure in the deslop audit was `#f2f0ff` on `#8b7ff2`; this app
puts *dark* ink on the violet and never had it. The sweep added `--acc-fill`
tokens to this file's `:root` and nothing uses them. Non-text boundaries fail
(F6).

**Type inventory:** 19 / 14 / 12.5 / 12 / 11.5 / 11 px; three styles under
12 px (F9).

**Mobile, 390×844 @3×.** The layout stacks (controls then canvas), no horizontal
overflow, controls at 16 px. The default output is 1170×2532, a phone
wallpaper, drawn on 7 shelves — with 44 books, the top 2.3 shelves are full and
the rest bare, so "Fit every book" is the button a phone reader needs and
nothing says so. A wallpaper builder is meaningful on a phone; this one works
there; it just does not know it is on one.

**Motion.** No animation, transition or `@keyframes` in the file; zero
`document.getAnimations()`; the page does not read `data-motion` and does not
need to. Compliant by having nothing that moves.

**`desktop.html`.** 985 KB at 1280 with motion on (mp4 399 KB, cover-mode WebP
266 KB, shelf WebP 111 KB, four Plex woff2 82 KB, poster 92 KB, CSS 27 KB);
586 KB at 390 (lazy images not reached). The two card images are WebP now, not
the 2.15 MB / 840 KB PNGs of the earlier diagnosis. Marginalia are static
(`.long` → `position: static`), `getAnimations()` = 0, and **no marginalia item
overlaps `nav.top` at 1280, 1024 or 390, at rest or scrolled, at HEAD or in the
working tree.** In the working tree, `reducedMotion: reduce` yields
`data-motion="off"`, the spines video is never given a `src` and never
requested; with no preference it loads and plays when scrolled into view and
pauses when scrolled past. That contract works.

---

## 7. Cross-check

**`DESLOP_AUDIT_2026-09-04.md`.** Its weight for desktop (921 KB) matches mine
(985 KB, motion on, different viewport). Its F1 (2.91:1) correctly lists
bookshelf as the one app without the failure. Its F11 note that this app has its
own greys and 6–9 px radii where the site uses 2 px is accurate and is a
consistency choice, not a defect. It records that the external audit noted
"~10 px labels in bookshelf-app only" and did not re-measure; the true floor is
11 px.

**`DESIGN_AUDIT_EXTERNAL_2026-08-30.md`.** Finding 4, "drifting book cards slide
under the top nav" on `desktop.html`, described the old `margin-scene.js`
canvas decoration. That script is no longer loaded by `desktop.html` (HEAD or
working tree); the book list is now two static HTML asides, and I measured zero
overlap at three widths. **Resolved by removal.** Finding 12's "~10 px" for this
app's labels: **refuted**, 11–11.5 px.

**The appendix checklist**, read once early (disclosed above), item by item:
cover fetching sends ISBNs to a third party — **confirmed and quantified** (§1);
generator folder and note missing — **confirmed, with the museum half found**
(§2); labels around 10 px — **refuted**, 11 px; drifting cards under the nav —
**already gone**; Goodreads format drift — **real (two drifts found) but the
parser is immune to both**; the 2.91:1 accent failure in app-local CSS —
**never present in this app**; its dead `--acc-fill` tokens are the only trace
of the sweep.

---

## 8. What is good and must survive

- **The privacy architecture.** One network primitive, one gate, off by
  default, no persistence, no third-party script, no font, no analytics. The
  instrumented default run made exactly one HTTP request. Fix the sentences,
  not the design.
- **The disclosure on the checkbox itself.** "The one thing that uses the
  network…" sits at the point of decision, which is where every such sentence
  on the site should be.
- **"What is real here."** The clearest provenance statement on the site, and
  the "no database of photographed spines exists" line is the house rule done
  right: the missing data is named and the feature is built around its absence.
- **The parser.** A hand-written quoted-field CSV reader that survived BOM,
  CRLF, quoted newlines, embedded quotes, three scripts, an emoji, HTML in a
  shelf name, two format drifts and 5,000 rows without an error. Header
  matching by name, not position, is why the drift does not matter.
- **The demo shelf as empty state**, with real ISBNs that all checksum.
- **One `pass()` for measuring and drawing**, so the fit search cannot drift
  from the renderer; 5,000 books fitted in 340 ms.
- **The single-file, zero-dependency artifact.** 37 KB, 96 ms, works from a
  double-clicked file with the cable out, as the README says.
- **The uniform cover finish** — the mean-luminance correction is a real,
  small, honest piece of image work and makes cover mode look like one shelf.
- **The phone layout.** Stacking with 16 px controls and normal scroll is the
  right call for a form; it did not need the touch-action trick the other apps
  use, and the CSS comment says exactly why.

---

## Evidence index

- `_audit-bookshelf/results.json` — every number above, by scenario
  (`privacy_default`, `privacy_covers_real_intercepted`, `covers_demo_live`,
  `covers_ratelimit_live`, `parser`, `metrics`, `download_browsers`,
  `desktop_page`, `desktop_reduced`).
- `_audit-bookshelf/run.js` — the harness; `node run.js <scenario>` with
  `NODE_PATH` at `_audit-longevity/node_modules`, server on 8803.
- `_audit-bookshelf/fixtures/` — 15 CSVs (synthetic; the real export is not copied).
- `_audit-bookshelf/shots/` — `app_1280.png`, `app_390_full.png`,
  `crop_labels*.png` (F4), `covers_demo_1400.png`, `parser_*.png`,
  `desktop_*` at three widths × motion state, `dl_*_1920x1080.png`.
- `_audit-bookshelf/curl_headers.txt` — Open Library cover response headers.
- `_audit-bookshelf/concurrent-worktree-changes.diff` and `.when.txt` — what
  changed under the audit, and when.
- `_audit-bookshelf/bookshelf-app.md5` — the file this report describes.
