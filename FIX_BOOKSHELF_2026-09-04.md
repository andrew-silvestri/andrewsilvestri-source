# Fix — the bookshelf (2026-09-04)

Acts on `AUDIT_BOOKSHELF_2026-09-04.md` and `prompts/FIX_bookshelf.md`.
Local URL: **http://127.0.0.1:8803/bookshelf-app.html** (page:
http://127.0.0.1:8803/desktop.html). Verification evidence in
`_audit-bookshelf/fix_results.json`, `_audit-bookshelf/fix_verify.js`,
`_audit-bookshelf/shots/fix_*.png`.

## Three things to know before the rest

1. **I did not commit; something else did.** Commit `577d582` ("Phase 3b …",
   17:00:57) was made by a sibling session 24 seconds after my last edit and
   swept the working tree, including `site/bookshelf-app.html`,
   `site/desktop.html`, `rezip_downloads.py` and the new `bookshelf/` folder,
   into its message. HEAD is byte-identical to my finished state (checked
   with `git diff --quiet` on each file), so nothing is lost or half-done at
   the tip, but the commit message describes figures, not this work, and the
   shared rule "do not commit" was not honoured by the repository as a whole.
   `bust_cache.py` was not run; `bookshelf-app.html` is linked without a
   stamp and `desktop.html`'s stamps are whatever the sweep leaves.
2. **The app's panel is now on the site's palette.** Item 6 said "fix with
   the tokens now in `style.css`, not new literals". The tokens now in
   `style.css` are the light "Yacht club" set, and the site is single-theme,
   so the control column moved from its own dark greys (`#0b0d12`,
   `#10131b`, `#8b8fa3`, violet) to `--bg-lift` / `--card` / `--ink` /
   `--dim` / `--acc-fill`, copied by name and value into the app's inline
   `:root` (the file has to work alone from a folder, so it cannot load
   `style.css`). This is a visible change, larger than item 6 asked for, and
   the reason it is not smaller is below under item 6. The other four apps
   still carry the violet palette; that is theirs to fix.
3. **One shared file was touched: `rezip_downloads.py`.** The download zip
   had no generator and no source folder, so the README could only be edited
   inside the zip — the drift class the shared rules name. It now has a
   `bookshelf/` source folder and a target in the script. Details and the
   no-op proof at the end.

---

## The blocking one: the privacy claim

### What is true, precisely

Default mode: one HTTP request (the page). Nothing stored. Re-verified after
the changes with the real 764-book export, all controls, and a download:
**0 requests left the browser** (`fix_results.json → defaultPrivacy`).

Cover mode, after the changes: one `GET` per book with an ISBN to
`covers.openlibrary.org`, now sent with `referrerPolicy: "no-referrer"` and
`credentials: "omit"`, so the request carries the ISBN in the URL and what any
HTTP request carries (the reader's address and browser string) — verified:
`Referer` empty, no `Origin`, no cookie (`demoLive.headers`). The 302 to
Internet Archive download hosts still follows.

### What changed in the design, not only the copy

The brief asked whether cover mode should be opt-in at the point of the click
rather than in prose elsewhere. It now is, in three ways:

- **The tick is per file.** Loading a file while the box is ticked unticks it
  and says "Real covers switched off for this file. Tick it again to look up
  *N* ISBNs on Open Library." Verified: box ticked on the demo, real file
  loaded → 0 requests, box off (`autoUntick`, `coversParam`). A shared link
  with `?covers=1` can therefore only ever fetch the 44 public demo ISBNs.
- **The checkbox says what a tick does** — one request per book, to whom,
  carrying what, and why that matters ("sent together, those ISBNs are a list
  of your books").
- **The panel reports what came back**, on its own line that nothing
  overwrites (item 2).

### Proposed wordings

**`index.html` card** (not touched — the sweep owns it; current text: "The CSV
is parsed in the browser and never leaves it."):

- *A.* "The CSV is parsed in the browser and never leaves it. The optional
  cover mode sends each book's ISBN to Open Library, and nothing else."
- *B.* "Built in the browser: the CSV never leaves it. Real covers, if you
  tick them, are fetched from Open Library one ISBN at a time — your book
  list, sent to one place, only when you ask."
- *C.* "Parsed, drawn and saved in the browser; nothing is sent anywhere
  unless you tick *Real covers*, which sends each book's ISBN to Open
  Library."

**Ship B.** A keeps the sentence that was wrong and bolts a qualifier on; C is
accurate but reads as a disclaimer. B says the three things that matter in
the order a reader needs them: what stays, what can go, that it is a list and
that it is a choice.

**`desktop.html`** — shipped (paragraph "Cover mode turns the shelf…"):

> It is the page's one use of the network, and it is worth being exact about:
> when you tick *Real covers*, the page sends one request per book to Open
> Library, an Internet Archive project, carrying that book's ISBN from your
> export and nothing else from it — no title, no rating, no shelf, no cookie,
> not even which site sent it. But an ISBN is a book, and several hundred of
> them sent together are a list of your books, so the box is off until you
> tick it, switches itself off again whenever you load a file, and the panel
> reports what came back …

The alternative I did not ship: "the request carries the ISBN and nothing
else from your export" (the audit's suggested minimum). Accurate, but it
still lets a reader think an ISBN is a small thing. The shipped version says
what the list is.

**Card on `desktop.html`** — shipped: "The page works with the network cable
out. Tick *Real covers* and it sends each book's ISBN to Open Library to
fetch its cover — the one thing it ever sends anywhere, and only when you
ask."

**Zip README** — shipped, same substance as the desktop paragraph, in
`bookshelf/README.md`.

---

## The rest, in the brief's order

### 1. Cover failures are now four facts, not one

Covers are fetched with `fetch()` instead of `<img>`, because an `<img>`
cannot tell 404 from 403 from no network. Each ISBN ends in one of: cover;
**not on Open Library** (404); **could not be fetched** (network error,
blocked, non-2xx); **not tried** (after the first 403/429 the queue stops —
Open Library's documented 100-per-5-minutes limit — and the rest are not
asked); and books **with no ISBN in the export** are counted without ever
being requested. The caption and the panel line list the non-zero ones.
Re-ticking the box retries the "failed" and "not tried" ones.

Verified with routes that returned 404 for most, 403 after the 40th, and
dropped every 7th (`simulatedOutcomes`): "Covers: 0 of 55 on the wall. Left
off: 10 with no ISBN in the export, never looked up; 35 not on Open Library;
6 could not be fetched (offline, or blocked?); 4 not tried: Open Library
allows 100 lookups per address per five minutes." Switching to Everything
afterwards sent **0** further requests and reported 641 not tried. Live on
the demo shelf: "Covers: 43 of 44 on the wall. Left off: 1 not on Open
Library."

### 2. The summary survives

`#stats` is the library line; a new `#coverline` (both `aria-live="polite"`)
carries the cover accounting; `build()` never writes to `#coverline` and the
`coverStatus` flag is gone. Verified live: the line is still there 1.5 s
after completion and after a subsequent rebuild.

### 3. Label spines use the label

The paper label now spans 6–66 % of the spine and the title is drawn on it
in the label ink; the author sits on the cloth below in the cloth's own ink
(the `lum2` rule the other modes use). Worst case for the title, label over
the darkest cloth at 93 % opacity: **12.37:1** (was 1.59:1).
`shots/fix_crop_labels.png`.

### 4. Keyboard

`#drop` is `tabindex="0" role="button"` with Enter/Space opening the picker;
the hidden input is `aria-hidden` and out of the tab order; `:focus-visible`
draws a 2 px `--acc` ring (5.71:1 on the panel); the canvas has
`role="img"` and a name. Verified: first Tab lands on the drop zone, Enter
opens the file chooser, the chosen file loads (`keyboard`). Also fixed while
there: a file dropped *anywhere* on the page is now caught and loaded instead
of navigating the browser to the CSV (`documentDrop`), and a `FileReader`
error is reported rather than silent.

### 5. Assumed values are labelled

- No page count → the spine is drawn at the **median page count of the
  reader's own library** (an exact computation from their data), not a
  hash-seeded random number; if nothing has a page count, 300, and the
  caption says so.
- No year → a new **"plain"** dress: cloth, no era marks.
- The caption counts both ("· 11 spines at the library's median width (no
  page count in the export)", "· 7 dressed plain (no year in the export)"),
  and "What is real here" gains an "Assumed, and counted in the caption"
  sentence. `desktop.html`'s spine paragraph says the same.

Verified: real export → 11 spines at median width; the no-pages/no-year
fixture → both counts, with the "nothing has one, so 300 pages" note.

### 6. Control boundaries — and why the palette moved

Every boundary was recomputed. The site's own `--rule` (`#BBBDBC`) is
**1.66:1** on `--bg` and 1.52:1 on `--bg-lift`: it is a hairline token and
cannot be a control boundary anywhere on the site. So fields, buttons and the
drop zone use `--dim` as their edge:

| pair | ratio |
|---|---|
| ink `--ink` on panel `--bg-lift` | 13.25:1 |
| dim `--dim` on panel (labels, hints, stats) | 5.30:1 |
| dim on field `--card` (drop zone text) | 6.26:1 |
| dim on `--bg` (caption) | 5.80:1 |
| field border `--dim` vs panel / vs field | 5.30:1 / 6.26:1 |
| primary button `--acc-ink` on `--acc-fill` | 7.10:1 |
| primary button boundary vs panel | 5.71:1 |
| hover / focus `--acc` vs panel | 5.71:1 |
| button hover text `--acc` on field | 6.75:1 |
| `--rule` hairlines (aside edge, canvas edge) — decorative only | 1.66:1 |

Type: the three under-12 px styles (`h2` 11, hints 11.5) are now 12 px;
nothing on the page is under 12 px (`under12: []`). Font stack is the site's
`--sans` without the `@font-face` (Plex loads on machines that have it, and
falls to `system-ui` elsewhere, which is what a standalone file can do).

Why not keep the dark panel and just import a token: on `#10131b` the only
`style.css` tokens that pass 3:1 are `--rule` (9.8:1, a white line on every
field) and `--acc-dim` (4.8:1, a blue line on every field). Both would have
been a literal-free fix that looked wrong, and DESLOP F11 had already named
the app's private greys as a Phase 3 debt. The screenshots
`shots/app_1280.png` (before) and `shots/fix_app_1280.png` (after) are the
comparison.

---

## The museum note — is the reasoning genuinely lost?

Yes, as far as the repository can tell. `dumpNew/PyProjects/philbrook_museum/`
holds the generator (`museum_app.py`), its data and an `images_full/` folder,
and no `PUBLISHING-NOTE.md`, no README, no comment in the code about rights
or publication (grep for permission / licence / rights / terms / publish over
the folder hits only the venv). What survives is the *decision* — the folder
of artwork images was never put on the site — and `HANDOFF.md:65`'s one-line
memory that a note about "the image permissions required before any of it
goes on the site" once existed. The reasoning itself (which works, whose
rights, what would have to be asked) is not recorded anywhere I can find. For
the bookshelf that matters less than it might: the covers are fetched by the
reader, for the reader, and the page now names the source; but if the
museum wall is ever revived, the permissions question starts from zero.

---

## Generator first, shipped file second, rebuild is a no-op

- `bookshelf-app.html` and `desktop.html` have no generator (`build_site.py`
  is retired; `rebuild_nav.py` owns only the nav, which was not touched). The
  shipped files are the source.
- The download zip: created `bookshelf/` (`README.md`, `set_wallpaper.py`,
  unpacked from the old zip, README rewritten) and added to
  `rezip_downloads.py` a third target whose `bookshelf-app.html` entry is
  pulled from `site/` by name, so the download cannot drift from the app
  again. The change is additive (an optional `extras` map; heat and storage
  behave as before).

Proof, run after the last edit:

```
bookshelf-code.zip: namelist() identical (3 -> 3 entries)   # verify()
zip app == shipped: True
rebuild no-op (CRCs): True                                  # second rebuild, member CRCs equal
```

The old zip is kept at `_audit-bookshelf/bookshelf-code.zip.before`.

---

## Verification summary (`fix_results.json`)

| check | result |
|---|---|
| default mode, real export, every control, download | 0 remote requests; no storage; 1400×900 PNG |
| cover mode with 404 / 403 / dropped answers | four categories reported correctly; 0 requests after the limit |
| cover mode live, demo | 43 of 44; summary line persists; `Referer` empty |
| box ticked, then a file loaded | box unticks, 0 requests, line explains |
| `?covers=1`, then a file loaded | 44 demo requests, then 0 |
| keyboard | Tab → drop zone; Enter → file chooser; file loads |
| drop on the canvas | caught, loaded, no navigation |
| assumed values | counted in the caption for both fixtures |
| page errors, console errors | none |
| type under 12 px | none |

## Not fixed, and why

- **`index.html` card wording** — out of bounds for this brief; proposal B
  above.
- **Cover aspect clamp (0.52–0.85)** and the stretched-cover wording — the
  panel now says "each fitted to a spine-like proportion"; the clamp itself
  is a design choice for a wall of uniform shelves and stays.
- **Empty shelves get no board** (audit F13) — cosmetic; the caption's row
  count is the fit search's number, not the drawn boards. Left as is.
- **Cover rights sentence** on `desktop.html` — not added. The page now names
  Open Library and the Internet Archive and says the request is per reader;
  a rights sentence would be a claim about publishers' terms that the
  repository has no source for (the note that had it is gone).
- **iOS canvas ceiling** — no device to test; no message added for a canvas
  that comes back blank at 5K+.
- **Custom exclusive shelves** (e.g. `did-not-finish`) still fold into
  "Unread" — unchanged behaviour, now unlabelled only in the sense that the
  menu does not list them.
