# Sweep — the shared edits nobody else was allowed to make

Run this **last**, in the main instance, after 3b Part 2 and all four app fixes
have landed and stopped. Every other brief in this set was forbidden from
touching these files precisely so that one pass could do it coherently.

## 1. The home-page copy the bookshelf fix could not touch

`index.html`'s bookshelf card says the CSV "never leaves it." The bookshelf
audit proved that is true in default mode and false in cover mode, which sends
one request per ISBN — 682 for a real export — to Open Library and on to
archive.org. `FIX_BOOKSHELF_2026-09-04.md` carries the agreed wording. Apply it
to the home card, and check `desktop.html` and the zip README agree with it
word for word. Three places said three different things; they should now say
one.

## 2. The systemic defect: shipped files drifting from their generators

This is now the most common defect in the repository. Today alone:

- `rebuild_nav.py`'s `NAV` did not match the shipped nav
- `longevity-app.html` carries a palette fix and a `-999` fix absent from its
  `template.html`
- `climate-cost-app.html` carries palette and `touch-action` fixes absent from
  its `template.html`
- `skyline-code.zip`'s template is three palette lines behind `site/`
- `build_site.py` has been stale since 1 August and would revert a month

Every one of these means running the generator silently destroys shipped work,
and none of them announces itself. Individually they have all been fixed. The
class has not.

Write a check that catches the class: for each generator, run it into a
temporary directory and diff against what is shipped. Any difference is either
drift to reconcile or an intended change to apply — the check does not care
which, it just refuses to let the difference stay invisible. Add it to
`tests/`, run it, and report what it finds now that everything is supposedly
reconciled. I expect it to find something.

## 3. Traps for `HANDOFF.md` §8

Three lessons from today, written for a maintainer who was not here:

- **A claim that flatters the page's own argument is the one nobody audits.**
  The climate-cost shoe said allocation tripled the footprint; the true figure
  was ×1.2. It survived because it made the page's point better than the truth
  did. Four separate instances of the same shape were found in one day across
  climate-cost, skyline, longevity and the bookshelf: in every case the prose
  claimed more than the code delivered.
- **A generator is a claim about the shipped file, and it goes stale silently.**
  See the list above, and the new check.
- **A brief's factual premises are leads, not facts.** Corrections found today
  include: "the palette passes AA" (it was 2.91:1), "the nav is generated" (it
  had been hand-edited), "use `publish.ps1`" (`publish.sh` is the tested one),
  "the four numbers are on `atlas.html`" (one is on `model.html`), "skyline and
  bookshelf have no source" (both are in `site/downloads/` and
  `dumpNew/PyProjects/`), and three stale premises in the longevity brief.

Also correct §2's archive table, which still points at workspace-root folders
that moved into `01 ARCHIVE/` or are gone.

## 3b. Damage from the parallel runs — verified, fix these

Running four instances at once produced real artifacts, not just a noisy
`git status`. Each of these is confirmed, not reported:

1. **`site/downloads/storage-code.zip` is polluted.** It contains
   `__pycache__/` (two `.pyc` files) and `outputs/` (eight files, ~443 KB of
   generated figures and CSVs), timestamped 2026-09-04 16:31–16:37 — during the
   parallel runs. The skyline session hit the same `rezip_downloads.py`
   collision and restored `heat-code.zip`; storage was left. Rebuild it and
   **check all twelve archives**, not just this one. A download that ships
   compiled bytecode and stale generated outputs is a defect a reader meets
   before any of your prose.

2. **Commit `c2d02aa` swept up work from three different tasks** under a message
   about climate-cost, including the built `skyline/skyline-app.html` and
   `package*.json`. Those are now tracked and should not be:
   `git rm --cached` them; `.gitignore` was already updated. A second commit
   carries the bookshelf privacy fix under a message about figures.

   Do not rewrite history to fix this. Record it: the repository now has commits
   whose messages describe changes they do not contain, which is the same defect
   class as a stale generator, in git. One honest note commit is enough.

3. **`rezip_downloads.py` has no locking and a `--verify` run rewrites the
   archive it is verifying.** That is why the pollution happened. A verify that
   mutates is not a verify — fix it, or the next parallel session repeats this.

## 4. Close out

- `python bust_cache.py` — the only run in this whole sequence.
- All test suites, including `tests/test_layout.js` and the new generator check.
- Commit with a message that names the class of fix, not just the files.
- **Then stop.** Publishing is 3c and I will say when.

## Write-up

`FIX_SWEEP_2026-09-04.md`: what the generator check found, the final wording
that shipped in all three bookshelf places, and a one-paragraph statement of
what is still open across the whole site. That last paragraph is the one I will
actually use.
