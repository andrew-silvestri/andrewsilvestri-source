# Six briefs — four audits, two builds

Written 2026-09-04, after the deslop pass's Phase 2.

| File | What it is | Touches `site/`? |
|---|---|---|
| `AUDIT_longevity.md` | Audit `longevity-app.html` | No — read-only |
| `AUDIT_skyline.md` | Audit `skyline-app.html` | No — read-only |
| `AUDIT_bookshelf.md` | Audit `bookshelf-app.html` | No — read-only |
| `AUDIT_climate-cost.md` | Audit `climate-cost-app.html` | No — read-only |
| `BUILD_heat_visualiser.md` | New interactive for `heat.html` | **Yes** |
| `BUILD_storage_visualiser.md` | New interactive for `storage.html` | **Yes** |

## Sequencing — read this before launching anything

**The four audits can run in parallel right now.** They are read-only: each
writes one markdown file at the repo root and an evidence folder it gitignores,
and nothing else. Four instances will not collide.

**The two builds must not start yet.** Two reasons:

1. Deslop Phase 3 has not run. You have not picked an option, and Phase 3 will
   rewrite `style.css` and possibly markup across every page. A build landing
   in the middle of that produces a merge you will have to untangle by hand.
2. Both builds add a link to a content page (`heat.html`, `storage.html`) and
   both would want to run `bust_cache.py` and commit. Run them concurrently
   with each other or with Phase 3 and they will fight over the same files.

So: **audits now, in parallel. Builds after Phase 3 is committed, one at a
time.** If you want them sooner, give each its own `git worktree` — but the
merge back is real work and I would not bother for two files.

## Launching

Each in its own terminal, from `00 PUBLISH`:

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH"
claude --model fable
```

First message, substituting the file:

```
Read prompts/AUDIT_longevity.md and follow it. Stop where it tells you to stop.
```

Point at the file rather than pasting it — each brief has a sealed section at
the bottom, and pasting defeats it. (Note the seal is soft: `cat` reveals it.
The last instance disclosed reading it that way, which is the behaviour you
want. Ask each of these to disclose the same.)

Serve on a different port per instance if you run several at once —
`python -m http.server 8801`, `8802`, and so on — or they will collide on 8000.

## Something all six briefs say, because it keeps being true

`HANDOFF.md` describes a repository that has partly moved on. As of today:

- Its §2 archive table lists `24 Skyline Sonifier/`, `25 Desktop Gallery/`,
  `18 Final Deliverables/`, `16 Presentation Architecture/` and `PyProjects/`
  at the workspace root. **None of those paths exist.** The numbered archives
  now live under `01 ARCHIVE/` (10, 11, 13–18, 20, 21), and 24 and 25 are not
  anywhere in the workspace.
- **CORRECTED 2026-09-04, after the audits ran.** I concluded from that missing
  folder that `skyline-app.html` and `bookshelf-app.html` had no source in the
  workspace. **That was wrong.** `site/downloads/skyline-code.zip` holds the
  full pipeline — `build_skylines.py`, `supplement.py`, `keys.py`,
  `template.html`, `app.js`, tests and `skylines.json`. The bookshelf's museum
  sibling survives under `dumpNew/PyProjects/`. Only the raw Wikidata pull
  behind the skyline data is genuinely absent, so the 24 Wikidata cities cannot
  be regenerated from scratch, but everything else can.

  I searched for a folder name and never looked in `site/downloads/` — the
  directory the site's own Code page exists to publish. Both audits checked it
  and found the source. Take this as the standing lesson: **a brief's factual
  premises are leads, not facts**, including the ones about what is missing.

The archive table in `HANDOFF.md` §2 is still stale and should be corrected or
deleted — that part holds. It is the same class of defect as trap 11: a
document describing a state the repository has left.
