# RETIRED 2026-09-04. Kept for reference only; do not run it.
#
# publish.sh (Git Bash) is the tested publish path. This PowerShell version
# could not be executed or tested on the machine it was written on and shipped
# two faults because of it: an encoding fault that choked the parser, and a
# dry run that left the working tree dirty. Both scripts target the same
# repository and the same URL; the difference is which one has been run.
#
#     ./publish.sh --dry-run
#     ./publish.sh
#
# See HANDOFF.md section 10 and DESLOP_RUNBOOK.md.

<#
.SYNOPSIS
    Replace everything in the andrewsilvestri.com repository with the current
    contents of 00 PUBLISH\site, and push.

.DESCRIPTION
    Clones the repository if it is not already on disk, deletes every tracked
    file, copies the new site in, and commits the difference. History is kept:
    this is an ordinary commit that happens to delete a lot, not a force push,
    so the previous state of the site stays recoverable.

    Two things are checked before anything is pushed. index.html must sit at
    the repository root, and CNAME must be present and say andrewsilvestri.com.
    GitHub Pages serves nothing without the first and drops the custom domain
    without the second, and both fail silently.

    This file is deliberately pure ASCII. Windows PowerShell 5.1 reads scripts
    as Windows-1252 unless they carry a UTF-8 byte order mark, and a UTF-8 em
    dash decoded that way ends in byte 0x94, which is a closing curly quote and
    terminates whatever string it lands in. Keeping to ASCII removes the whole
    class of problem.

.EXAMPLE
    .\publish.ps1 -DryRun
    .\publish.ps1
#>

[CmdletBinding()]
param(
    [string]$Site    = (Join-Path $PSScriptRoot 'site'),
    [string]$RepoDir = (Join-Path $HOME 'andrew-silvestri.github.io'),
    [string]$RepoUrl = 'https://github.com/andrew-silvestri/andrew-silvestri.github.io.git',
    [string]$Message = '',
    [switch]$DryRun,
    [switch]$DiscardLocalChanges
)

$ErrorActionPreference = 'Stop'

function Step { param($t) Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Ok   { param($t) Write-Host "   $t" -ForegroundColor Green }
function Warn { param($t) Write-Host "   $t" -ForegroundColor Yellow }
function Die  { param($t) Write-Host ''; Write-Host "   $t" -ForegroundColor Red; Write-Host ''; exit 1 }

# ------------------------------------------------------------ source check --
Step 'Checking the source folder'

if (-not (Test-Path $Site)) { Die "Site folder not found: $Site" }
if (-not (Test-Path (Join-Path $Site 'index.html'))) {
    Die "index.html is not at the top of $Site. GitHub Pages needs it there."
}
$cnamePath = Join-Path $Site 'CNAME'
if (-not (Test-Path $cnamePath)) {
    Die "CNAME is missing from $Site. Without it the custom domain drops on the next push."
}
$cname = (Get-Content $cnamePath -Raw).Trim()
if ($cname -ne 'andrewsilvestri.com') {
    Die "CNAME says '$cname', expected 'andrewsilvestri.com'."
}

$files = Get-ChildItem $Site -Recurse -File -Force
$big = $files | Where-Object { $_.Length -gt 50MB }
if ($big) {
    Warn 'Files over 50 MB. GitHub will refuse these:'
    foreach ($f in $big) { Warn ("  {0:N1} MB  {1}" -f ($f.Length / 1MB), $f.Name) }
    Die 'Remove or shrink them first.'
}
$mb = [math]::Round((($files | Measure-Object Length -Sum).Sum / 1MB), 1)
Ok "$($files.Count) files, $mb MB"
Ok "index.html present, CNAME = $cname"

# -------------------------------------------------------------------- git ---
Step 'Checking git'
try { $gitVersion = (git --version) } catch {
    Die 'git is not on PATH. Install it from https://git-scm.com/download/win'
}
Ok $gitVersion

Step 'Getting the repository'
if (-not (Test-Path (Join-Path $RepoDir '.git'))) {
    if (Test-Path $RepoDir) {
        Die "$RepoDir exists but is not a git repository. Move it aside."
    }
    Write-Host "   cloning into $RepoDir"
    git clone $RepoUrl $RepoDir
    if ($LASTEXITCODE -ne 0) {
        Die 'Clone failed. Check the URL and that you are signed in to GitHub.'
    }
}
else {
    Push-Location $RepoDir
    git fetch --quiet origin
    # Refuse to run on a dirty tree. Uncommitted work would be destroyed by the
    # wipe below with no way to get it back.
    $dirty = git status --porcelain
    if ($dirty -and $DiscardLocalChanges) {
        git reset --hard --quiet
        git clean -qfd
        Ok 'discarded local changes as asked'
        $dirty = git status --porcelain
    }
    if ($dirty) {
        Pop-Location
        Write-Host ''
        Write-Host "   $RepoDir has uncommitted changes." -ForegroundColor Red
        Write-Host ''
        Write-Host '   This folder is a generated mirror of 00 PUBLISH\site, so there is'
        Write-Host '   almost never anything in it worth keeping. To throw the changes'
        Write-Host '   away and continue, run:'
        Write-Host ''
        Write-Host '       .\publish.ps1 -DiscardLocalChanges' -ForegroundColor Cyan
        Write-Host ''
        Write-Host '   To look first:'
        Write-Host ''
        Write-Host "       git -C `"$RepoDir`" status" -ForegroundColor Cyan
        Write-Host ''
        exit 1
    }
    $b = (git rev-parse --abbrev-ref HEAD).Trim()
    git reset --hard --quiet "origin/$b"
    Pop-Location
}
Ok "repository at $RepoDir"

Push-Location $RepoDir
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    Ok "branch: $branch"

    # ------------------------------------------------------------- wipe -----
    # A LICENSE already in the repository is worth keeping. It is not part of
    # the generated site, so the wipe below would drop it silently.
    $licenseKept = $null
    $licensePath = Join-Path $RepoDir 'LICENSE'
    if ((Test-Path $licensePath) -and -not (Test-Path (Join-Path $Site 'LICENSE'))) {
        $licenseKept = Get-Content $licensePath -Raw
        Ok 'keeping the existing LICENSE'
    }

    Step 'Removing the current contents'
    $old = Get-ChildItem -Path $RepoDir -Force | Where-Object { $_.Name -ne '.git' }
    if ($old) {
        $old | Remove-Item -Recurse -Force
        Ok "removed $(@($old).Count) top-level item(s)"
    }
    else {
        Ok 'repository was already empty'
    }

    # ------------------------------------------------------------- copy -----
    Step 'Copying the new site'
    # Trailing \* copies the contents rather than the folder. Copying the folder
    # itself would nest the site one level down and Pages would serve nothing.
    Copy-Item -Path (Join-Path $Site '*') -Destination $RepoDir -Recurse -Force

    if (-not (Test-Path (Join-Path $RepoDir 'index.html'))) {
        Die 'index.html did not land at the repository root. Nothing was pushed.'
    }
    if (-not (Test-Path (Join-Path $RepoDir 'CNAME'))) {
        Die 'CNAME did not copy across. Nothing was pushed.'
    }
    if ($licenseKept) {
        Set-Content -Path (Join-Path $RepoDir 'LICENSE') -Value $licenseKept -NoNewline
        Ok 'LICENSE restored'
    }
    $landed = @(Get-ChildItem $RepoDir -Recurse -File -Force |
                Where-Object { $_.FullName -notlike '*\.git\*' }).Count
    Ok "$landed files in place, index.html and CNAME at the root"

    # ----------------------------------------------------------- commit -----
    Step 'Staging'
    git add -A
    $stat = git diff --cached --shortstat
    if (-not $stat) {
        Ok 'No differences. The published site already matches this folder.'
        exit 0
    }
    Ok $stat.Trim()

    if ($DryRun) {
        Write-Host ''
        Warn 'Dry run: nothing committed or pushed.'
        Write-Host '   Changed paths (first 40):'
        git diff --cached --name-status | Select-Object -First 40
        # Put the repository back exactly as it was found. Unstaging alone
        # would leave the wiped-and-recopied files sitting in the working tree,
        # and the next run would refuse to start on a dirty tree - which is
        # exactly what happened the first time this was used.
        git reset --hard --quiet HEAD
        git clean -qfd
        Write-Host ''
        Ok 'working tree restored; the repository is untouched'
        exit 0
    }

    if (-not $Message) {
        $stamp = Get-Date -Format 'yyyy-MM-dd'
        $Message = "Rebuild site: globe atlas, 3D brain, wider layout, corrected models ($stamp)"
    }
    git commit -q -m $Message
    Ok "committed: $Message"

    Step 'Pushing'
    git push origin $branch
    if ($LASTEXITCODE -ne 0) {
        Die 'Push failed. If GitHub asked for credentials, sign in and run this again.'
    }
    Ok 'pushed'

    Write-Host ''
    Write-Host '   Live in a minute or two:' -ForegroundColor Green
    Write-Host '     https://andrewsilvestri.com'
    Write-Host '     https://andrew-silvestri.github.io'
    Write-Host ''
    Write-Host '   If the pages look stale, hard reload with Ctrl+F5. The old'
    Write-Host '   stylesheet and favicon cache aggressively.'
}
finally {
    Pop-Location
}
