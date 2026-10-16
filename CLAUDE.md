# CLAUDE.md - andrewsilvestri.com source tree

## Who does what

- Andrew does not edit the site. Terminals do the work and verify their own
  claims. Andrew reads `../03 RESEARCH/oct-2026/DECISIONS.md` on a manual pass
  and answers there.
- You were started with a job packet. Do that job and nothing adjacent to it.
  If you find something outside it, write it to DECISIONS.md or the packet's
  findings file and keep going.

## Before any change

Read, in this order: your packet; `HANDOFF.md` sections 1, 7, 8 (all traps),
10; `../03 RESEARCH/site-sweep/STATE.md` (durable half). Your packet names
anything else.

## Rules that have each caused a bug when broken

- One branch per change. Sequential. Never `git add -A`. Never two changes in
  the working tree: `publish.sh` mirrors the working tree, not a commit.
- `python`, not `python3` (`python3` is a WindowsApps shim with no numpy).
- `publish.sh` runs under Git Bash: `"C:\Program Files\Git\bin\bash.exe"`.
  The `bash` on PATH is `C:\Windows\system32\bash.exe`, which is WSL. Wrong one.
- Ordering rule (trap 33): change -> page generators -> rezip_downloads.py ->
  sync_code_rows.py -> bust_cache.py -> tests/test_generators.py LAST.
- Publish gate: `git status --short` clean, ordering rule, full suite, then
  `./publish.sh --dry-run` with the file list reported, then publish, merge to
  master with --no-ff, check master out, `git push origin master`.
- Report file paths, commands and exit codes. A finding without the command
  that produced it is not a finding. A reply that claims a change with no diff
  is a failed turn.
- An instrument decides nothing until you have varied its input and watched the
  output move. A check that has only gone green is a claim.
- Never describe a page from memory or from its markup. Measure the rendered
  page. Trap 11: anything describing the site describes a state it may have left.
- Truncated output is not a list. Do not `tail` evidence you are about to count.

## Escalate, do not decide

Write the item to DECISIONS.md in its format and move to the next independent
step. Escalate when a change would: alter a displayed figure; change any
existing page's words; remove content a reader can reach; reverse a decision a
comment records; choose a Phase 2 invariant or threshold; publish a NEW page;
or touch anything that may derive from an employer.

## Employer material

Nothing derived from the summer 2026 internship (Targa Resources) goes in this
tree: no data, no workbook, no method ported from company files, no figure. The
precedent is `unpublished/holdup.html`, retired for exactly this. Public
standards, public correlations, public data and synthetic inputs only, each
cited.

## Retired, do not act on

`.claude/retired/` holds two August-era handoffs describing pages that have
since been unpublished (atlas, library, desktop, model). Their open questions
are moot. They are kept so nobody re-derives them.
