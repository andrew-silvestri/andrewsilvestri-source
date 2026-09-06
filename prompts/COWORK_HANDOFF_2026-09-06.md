# Cowork handoff — andrewsilvestri.com, 2026-09-06

Written for the Cowork session picking this up. The previous session ran from
the morning of 4 September to the small hours of 6 September. This is the state,
the method, and what is owed.

**Your job in Cowork is not to edit the site.** It is to read what the Claude
Code terminals report, verify their load-bearing claims independently, and write
the message Andrew pastes back into each one. The terminals do the work.

---

## 1. What this is

`C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH` is a hand-built static
site — plain HTML, one stylesheet, no framework, no build step. `site/` **is**
the website. Everything else in the folder generates or verifies part of it.
`publish.sh` (Git Bash, **not** `publish.ps1` — that one is retired and
untested) mirrors `site/` into `~/andrew-silvestri.github.io` and pushes to
GitHub Pages. Live at `andrewsilvestri.com`.

`HANDOFF.md` in that folder is the system's own map: §4 the house style, §6 the
engine and its five properties, §8 **twenty-three** traps, §11 the current
state. It was rewritten on 5 September, corrected on 6 September, and is
current. Read it before advising on anything structural.

Two numbering faults in it were fixed on 6 September and old pointers will
still be wrong: §6's heading said "four properties" over a list of five, and
§8 numbered its traps 1–20 and then restarted at 12, 13, 14. The tail is now
21, 22, 23, so **"trap 14" now means only the briefs-are-leads trap** and the
payload hand-patch is **trap 23**. Anything written before 6 September that
says "trap 14" about the payload means 23.

`prompts/` holds every brief written for the terminals. `NEW_PROJECTS.md` is the
three-stage method the six new projects run on.

---

## 2. The method, and why it works

Every piece of work runs in **stages with hard stops**. The instance does one
stage, stops, reports, and waits. Andrew pastes the reply. Nothing crosses a
stop without a go-ahead.

For new projects (`prompts/NEW_PROJECTS.md`):

| Stage | Mode | What it produces |
|---|---|---|
| 1 Research | auto | Does this project exist? A feasibility document. |
| 2 Design | **plan** | What the page is. No code. |
| 3 Build | auto | The page, figures, tests, archive. |

Plan mode for Stage 2 specifically, because it cannot write files and therefore
forces a proposal before code. Research needs writes, so it runs in auto.

**Model:** Fable for long investigative work and every build; Opus 5 where the
data source is known and the job is characterising it.

### The rules that made the work hold

These are the load-bearing ones. Repeat them in briefs rather than assuming
they are remembered.

- **Never invent data.** Every number traces to a public dataset, an exact
  computation, or a named publication. Anything assumed is labelled *assumed*.
  If a number cannot be sourced, the feature is not built and the page says why.
- **Where a claim cannot be made true, change the claim, not the data.**
- **Fix the generator or template first**, then the shipped file, then prove a
  rebuild is a no-op.
- **Break every new test before trusting it.** Introduce the defect it exists to
  catch, confirm it fails, fix it, confirm it passes. This found more real bugs
  than any other single practice.
- **Treat a brief's factual premises as leads, not facts.** Roughly a dozen of
  the previous session's premises did not survive contact. Saying so each time
  is why the work held.

---

## 3. Where things stand

### Published

The site was published nine times on 5 September (twelve times over 4–5
September). The redesign is live: Yacht club palette, IBM Plex, one left edge,
a layer diagram as the home hero, projects as an index with one sentence each.

**Live is the mirror's `72d928e`** — "Continents move in the reconstruction
viewer", 2026-09-05 16:52. **Rollback is `a55c566`**, 15:34 the same day, the
neuron-and-continents publish. `shoes.html` went out earlier, at `791dfe3`
(13:51), whose rollback was `6d0316e`; that pair is history now, not the
current one.

`site/` in `00 PUBLISH` is identical to the mirror's head, checked file by
file on 6 September. **Nothing is built-but-unpublished.**

### Previously listed as unpublished — they are live

`site/neuron.html`, `neuron-app.html`, `continents.html` and
`continents-app.html` were still in the tree when this file was written, and
were published four minutes after they were written on 5 September. All four
answer 200 on `andrewsilvestri.com`. Andrew got the one publish he asked for;
the note that they were waiting is what was behind, not the work.

### Blocked

**§1 beauty** (`00 PUBLISH/beauty/`) — everything built and tested against
placeholders. Blocked on two credentials only Andrew can obtain:

- IUCN Red List API token — register at `api.iucnredlist.org`, arrives by email
  in a day or two. Set as `IUCN_TOKEN`.
- OpenAlex key — free account at `openalex.org`, no card. Set as `OPENALEX_KEY`.

The per-species OpenAlex fetch then takes about two days on the free tier.
**Check whether these have been done; if not, that is the first thing to raise.**

### The nav retaxonomy — landed, and not in the shape planned

It is live, and the shipped taxonomy is **Home / Energy / Running / Misc /
Code**, replacing Home / The atlas / Energy / Others / Code.

There is **no Mind group**. The plan above described Energy / Mind / Running /
Misc; what shipped folded the atlas into Energy (that decision held) and put
`neuron` under Misc instead of standing Mind up for one page. Misc now carries
six items — climate-cost, food, continents, longevity, skyline, neuron —
against Energy's six and Running's two, and **Misc is the group that will need
splitting when beauty lands**. That is still Andrew's decision; shipping this
did not make it. Verified against the live `index.html`, not against a
generator: `rebuild_nav.py` writes the nav on every page, and HANDOFF §8 trap
11 is about exactly this kind of claim.

### Open, by name

- ~~`add_citations.py` is disarmed behind a guard and drifts on three pages.~~
  **Closed 6 September — it is armed and it does not drift.** The guard and the
  flag that bypassed it are both gone from `tests/test_generators.py`, and the
  script's banner marks all four defects resolved. Reproduced independently:
  `site/` copied to a scratch directory, `python add_citations.py --apply` run
  against the copy, byte-identical output on all seven pages it owns — heat 4
  markers, economy 10, neuron 17, continents 13, food 10, storage 5,
  climate-cost 8 — its only report `beauty.html does not exist`, exit 0. The
  `longevity.html` reference list is a separate open item and stays open: that
  page left `PAGES` because its own generator owns it, and its nine unmarked
  references are recorded in HANDOFF §11.
- The continents archive is 1.85 MB, 3.5× the previous largest. Kept
  deliberately so the build reproduces without re-fetching.
- `beauty/data/iucn_table1a.csv` is **kept deliberately**, on
  `beauty/DATA_SOURCES.md`'s authority: it is a cited aggregate summary table,
  not the per-species Red List categories the Red List terms forbid
  redistributing. Those are gitignored (`iucn_aves.csv`, `birds_joined.csv`,
  `data/raw/`). Checked on 6 September, not overlooked — do not raise it again
  as a licence problem without reading that file.
- `neuron/neuron-app.html` and `neuron/data/_work/` were gitignored on
  6 September. The second is empty in a clean tree and fills with ~1,500
  sampled SWC files when the fetch runs, which is one `git add -A` from
  HANDOFF §8 trap 18.
- **`site/downloads/` is gitignored in full**, so no source archive is in the
  repository. `code.html` links sixteen; `rezip_downloads.py` rebuilds ten of
  them (it also builds `beauty-code.zip`, not yet linked); and six —
  `climate-cost`, `deliverables`, `model`, `web-v3`, `web-v4`, `web-v5` — have
  **no generator anywhere in the tree** and survive only in the working copy
  and the published mirror. See HANDOFF §10.
- Eight high-side longevity demotions held at grade C, with reasons recorded.

---

## 4. The six projects

| § | Project | State |
|---|---|---|
| 1 | Beauty in research — who gets studied | Stage 3, blocked on keys |
| 2 | A neuron, and what is measured | Built, unpublished |
| 3 | The science of modern food | **Published** |
| 4 | Where the ground goes — continents | Built, unpublished |
| 5 | Economy is not time — running | **Published** |
| 6 | What a fast shoe is worth | **Published** |

Every one came back from Stage 1 **narrower than the brief and better for it**.
Food went industry → preparation → addition. Beauty lost the zoo figure and the
harm forecast. Shoe lost half of itself. That is the method working, not the
briefs failing.

---

## 5. What the previous session got wrong

Kept because the pattern matters more than the instances. The terminals caught
all of these:

- "The current palette passes AA" — it was 2.91:1 on every button on every page.
- "The nav is generated, never hand-edit" — the generator had drifted from the
  shipped nav; following the instruction would have reverted a deliberate change.
- "Use `publish.ps1`" — `publish.sh` is the tested one; `publish.ps1` had shipped
  two faults.
- "`skyline` and `bookshelf` have no source" — both were in `site/downloads/`,
  the directory the site's own Code page exists to publish.
- "Test 1a will guard against a refit" — it passed while the coefficients were
  wrong, because the published values were ratios and errors cancelled.
- "Beauty and continents both carry weak checks" — both had already reached the
  sharper form. The terminal verified before writing and refused the premise.
- Three screenshot diagnoses where the cause was elsewhere: the crop was baked
  into the assets not the CSS; the softness was a display-size mismatch; the
  figure was off-centre inside its frame, not on the page.

**The habit to keep: verify a claim before putting it in a brief.** Compute the
contrast ratio. Open the zip. Read the generator. The terminals do this now and
will catch you if you don't — but the cost is a wasted cycle each time.

---

## 6. How to run a cycle

1. Andrew pastes a terminal's output. Terminal outputs are often garbled by
   wrapping — read for substance, and say plainly when a verdict is missing
   rather than guessing.
2. **Identify which terminal it is by its `※ recap:` line**, and label your reply
   with that recap so Andrew can match it. There are usually four or five
   running.
3. Verify the load-bearing claims yourself where you can — arithmetic, file
   contents, contrast ratios. Use the shell.
4. Reply with: what you verified, what you disagree with, and a **copy-pasteable
   block** for that terminal. Andrew pastes; he does not rewrite.
5. Say when a decision is genuinely his — palette, scope, what a page claims —
   rather than deciding for him.

### Parallelism

Read-only work runs in parallel safely. **Anything writing to `site/` does not.**
Two sessions in one folder corrupted `storage-code.zip` on 4 September, and a
near-miss on 5 September almost shipped a table of `SYNTHETIC` placeholder counts
into an archive. When several terminals are live, only one writes at a time.

### Archive before anything destructive

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH"
git add -A; git commit -m "<what changed>"
git tag "<stage>-2026-09-06"
git bundle create "$HOME\Desktop\00-PUBLISH-2026-09-06.bundle" --all
```

~~`00 PUBLISH` has no git remote.~~ **It does, as of 6 September:** `origin` is
`https://github.com/andrew-silvestri/andrewsilvestri-source.git`, branch
`master` is pushed, and `git ls-remote --heads origin` answers with the local
head. The standing recommendation was acted on. Note that this claim lived
**here**, in this file, and never in `HANDOFF.md` — an earlier brief
attributed it to `HANDOFF.md` and cost a terminal a grep to disprove.

`HANDOFF.md` §10 said nothing about this repository's own remote or backup at
all; that gap is now filled there too.

The bundle habit is still worth keeping before anything destructive, but a
bundle on `~/Desktop` is on the same disk as the repository and is not a
backup. The bundles on disk are dated 4 and 5 September; the remote is newer
than all of them. Andrew's other repositories are
`andrew-silvestri.github.io` (the generated mirror, `site/` only) and
`energy-web` (a different project); neither is the source, which is why the
third one exists.

---

## 7. One thing to look at when there is a lull

`energy-web`'s GitHub description reads *"Nonlinear, empirically calibrated,
historically validated model of the global energy system w/benchmarks."*

The site's own "calibrated" claim was removed on 5 September: the artifact
existed, but it recorded a retired 7,192-node build and was a Python-versus-Julia
parity check — a reproducibility test, not a comparison against observation.
Wrong model, wrong kind of check.

That description may be earned. But it uses the same word plus a stronger one,
and it is worth the same question: what artifact would you point at, and does it
compare a run to something observed?
