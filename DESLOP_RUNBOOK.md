# Deslop runbook — PowerShell

> **Corrected 2026-09-04.** Publishing is done with `publish.sh` from Git
> Bash, not `publish.ps1`. The PowerShell script could not be tested on this
> machine and shipped two faults; it is now marked retired at the top of the
> file and kept only for reference. Everything else here still runs in
> PowerShell. Where this file said `publish.ps1` it now says `publish.sh`.

The brief for the Fable instance is `DESLOP_PROMPT.md` in this folder. This
file is just the commands, in order.

The pass has **three phases with hard stops**: Fable audits and stops; you read
the audit; it builds three options and stops; you pick one; it applies and
publishes. Nothing reaches GitHub until you have seen the options.

---

## Before anything else

Run these yourself, in a normal PowerShell window.

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH"

# 1. Checkpoint the ~20 uncommitted files sitting in the tree, so the
#    deslop diff is readable.
git status
git add -A
git commit -m "Checkpoint before the deslop pass"
```

```powershell
# 2. Snapshot the current source site. backups/ is gitignored, so this is
#    local-only and non-published -- but also not protected by git.
$stamp = Get-Date -Format 'yyyy-MM-dd'
$snap  = "backups\site-pre-deslop-$stamp"
New-Item -ItemType Directory -Path $snap -Force | Out-Null
Copy-Item -Path "site\*" -Destination $snap -Recurse -Force
Write-Host "Source snapshot: $snap"
```

```powershell
# 3. Snapshot what is CURRENTLY LIVE. publish.sh mirrors into this folder,
#    so pull it fresh -- a stale local copy is not the live state.
$repo = Join-Path $HOME 'andrew-silvestri.github.io'
if (Test-Path (Join-Path $repo '.git')) {
    git -C $repo fetch origin
    $branch = (git -C $repo rev-parse --abbrev-ref HEAD).Trim()
    git -C $repo reset --hard "origin/$branch"
} else {
    git clone https://github.com/andrew-silvestri/andrew-silvestri.github.io.git $repo
}

$livesnap = "backups\published-live-$stamp"
New-Item -ItemType Directory -Path $livesnap -Force | Out-Null
Get-ChildItem $repo -Force | Where-Object { $_.Name -ne '.git' } |
    Copy-Item -Destination $livesnap -Recurse -Force

# Record the exact live commit so a rollback is one command later.
git -C $repo rev-parse HEAD | Out-File "$livesnap\LIVE_COMMIT.txt" -Encoding ascii
Write-Host "Live snapshot: $livesnap"
git -C $repo log --oneline -5
```

```powershell
# 4. Optional: look at the site as it stands, so you have a baseline in your
#    head before Fable starts. Ctrl+C to stop the server.
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH\site"
Start-Process "http://localhost:8000/"
python -m http.server 8000
```

---

## Permission mode

Run it in **auto mode** — this is a long task and most of it is file edits and
reads inside the working directory, which skip the classifier entirely, so auto
costs nothing there and saves you hundreds of prompts. On a Pro/Max/Team plan
in a terminal, auto is already the built-in starting mode; `Shift+Tab` cycles if
you need to change it. (Built-in auto needs v2.1.233+ on native Windows — you'll
clear that when you update for Fable 5.1.)

Two things to know:

**Auto mode is not a sandbox on Windows.** The Bash sandbox is macOS/Linux/WSL2
only. On native Windows, auto mode is classifier review with no containment
underneath it.

**Telling it "stop after Phase 1" in chat is not a hard stop.** The classifier
treats a stated boundary as a block signal, but it re-reads it from the
transcript on every check — so a long session that compacts can lose it. The
only hard guarantee is a rule.

That is why `.claude/settings.local.json` in this folder now carries `ask` rules
on `publish.sh`, `publish.ps1`, `git push` and `build_site.py`. Ask rules still prompt in auto
mode, so those three stay under your hand no matter what the transcript does:

```json
"permissions": {
  "ask": [
    "Bash(*publish.sh*)",    "PowerShell(*publish.sh*)",
    "Bash(*publish.ps1*)",   "PowerShell(*publish.ps1*)",
    "Bash(git push*)",       "PowerShell(git push*)",
    "Bash(*build_site.py*)", "PowerShell(*build_site.py*)"
  ]
}
```

`build_site.py` is in there because it is the one command that can silently
undo a month of work (see Traps, below).

Note the Pages repo is a *separate* repo from this working directory, so auto
mode would likely stop the publish on its own — pushing to a repository you are
not working in is not auto-approved. The ask rule makes that deterministic
rather than a judgement call.

## Start Fable

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH"
claude --model fable
```

Then, as your first message — don't paste the whole brief, point at it:

```
Read DESLOP_PROMPT.md in this folder and follow it. Start with Phase 1 and
stop where it tells you to stop.
```

The prompt is written to be read as a file: it has a sealed appendix Fable is
told not to open until its own audit is written, and pasting the text inline
defeats that.

---

## Between Phase 1 and Phase 2

Fable writes `DESLOP_AUDIT_2026-09-04.md` at the repo root. Read it. Push back
on anything that looks like it was asserted rather than measured — the brief
tells it to make every finding checkable in under a minute, so hold it to that.

When you're satisfied, tell it to proceed to Phase 2.

## Between Phase 2 and Phase 3

Serve the previews and compare:

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH\site"
python -m http.server 8000
```

Open, in four tabs:

```
http://localhost:8000/index.html                    <- current, for comparison
http://localhost:8000/_preview/option-a/index.html
http://localhost:8000/_preview/option-b/index.html
http://localhost:8000/_preview/option-c/index.html
```

Also check `model.html` and `heat.html` under each option — the home page
flatters a design, a long prose page and a figure-dense page do not.

Name your choice. Fable runs Phase 3 and publishes, from Git Bash:

```bash
cd "/c/Users/dasil/Documents/50 - ENERGY MODEL/00 PUBLISH"
./publish.sh --dry-run
./publish.sh
```

---

## Rollback

To revert the live site to what it was before the pass:

```powershell
$repo  = Join-Path $HOME 'andrew-silvestri.github.io'
$stamp = '<the date stamp you used above>'
$old   = Get-Content "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH\backups\published-live-$stamp\LIVE_COMMIT.txt"
git -C $repo revert --no-edit "$old..HEAD"
git -C $repo push
```

To restore the source instead and republish from it:

```powershell
Set-Location "C:\Users\dasil\Documents\50 - ENERGY MODEL\00 PUBLISH"
$stamp = '<the date stamp you used above>'
Remove-Item site\* -Recurse -Force
Copy-Item "backups\site-pre-deslop-$stamp\*" site\ -Recurse -Force
python bust_cache.py
```

then, from Git Bash (not PowerShell; `publish.ps1` is retired):

```bash
cd "/c/Users/dasil/Documents/50 - ENERGY MODEL/00 PUBLISH"
./publish.sh --dry-run
./publish.sh
```

---

## Traps, for when you're reading Fable's output

Worth knowing so you can catch it going wrong:

- **`build_site.py` is stale (1 Aug)** and does not know about the mosaic,
  sys-log, margin scenes or motion toggle. If Fable runs it, the HTML silently
  reverts a month. The prompt forbids it; watch for it anyway.
- **`atlas.html` is generated** by `update_atlas_pages.py` — edits to the file
  are lost on the next run.
- **The nav is generated** by `rebuild_nav.py` from its `NAV` list.
- **`bust_cache.py` must run before every publish**, or the change looks like
  it didn't take.
