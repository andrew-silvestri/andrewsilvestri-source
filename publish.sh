#!/usr/bin/env bash
# Publish 00 PUBLISH/site to the andrewsilvestri.com repository.
#
# Run this from Git Bash, which ships with Git for Windows. Right-click in the
# 00 PUBLISH folder and choose "Open Git Bash here", then:
#
#     ./publish.sh --dry-run     # show what would change, push nothing
#     ./publish.sh               # do it
#     ./publish.sh --discard     # throw away local changes in the mirror first
#
# Why bash and not PowerShell: this file can be executed and tested on the
# machine it was written on. The PowerShell version could not be, and shipped
# two faults in a row because of it - an encoding problem that made the parser
# choke, and a dry run that left the working tree dirty.
#
# The repository is treated as a generated mirror. Everything in it is deleted
# and replaced by the contents of site/, then committed. History is kept: this
# is an ordinary commit that happens to delete a lot, not a force push, so the
# previous state stays recoverable.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE="${SITE:-$HERE/site}"
REPO="${REPO:-$HOME/andrew-silvestri.github.io}"
URL="${URL:-https://github.com/andrew-silvestri/andrew-silvestri.github.io.git}"

DRY=0; DISCARD=0; MSG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run|-n) DRY=1 ;;
    --discard)    DISCARD=1 ;;
    -m)           shift; MSG="${1:-}" ;;
    -h|--help)    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   %s\n' "$1"; }
die()  { printf '\n   %s\n\n' "$1" >&2; exit 1; }

# ------------------------------------------------------------ source check --
step "Checking the source folder"
[ -d "$SITE" ]              || die "Site folder not found: $SITE"
[ -f "$SITE/index.html" ]   || die "index.html is not at the top of $SITE. Pages needs it there."
[ -f "$SITE/CNAME" ]        || die "CNAME is missing. Without it the custom domain drops on the next push."

cname="$(tr -d '[:space:]' < "$SITE/CNAME")"
[ "$cname" = "andrewsilvestri.com" ] || die "CNAME says '$cname', expected 'andrewsilvestri.com'."

big="$(find "$SITE" -type f -size +50M -print | head -5 || true)"
[ -z "$big" ] || { printf '   files over 50 MB, GitHub will refuse these:\n%s\n' "$big"; die "Remove or shrink them first."; }

count="$(find "$SITE" -type f | wc -l | tr -d ' ')"
size="$(du -sh "$SITE" | cut -f1)"
ok "$count files, $size"
ok "index.html present, CNAME = $cname"

# -------------------------------------------------------------------- git ---
step "Getting the repository"
command -v git >/dev/null || die "git is not on PATH."

# git refuses to commit without an identity, and the message it gives is five
# lines of boilerplate that buries the fix. Check up front instead.
if [ -z "$(git config --get user.email || true)" ] || \
   [ -z "$(git config --get user.name  || true)" ]; then
  printf '\n   git has no identity configured, so it cannot commit.\n\n' >&2
  printf '   Set one once, globally:\n\n' >&2
  printf '       git config --global user.name  "Andrew Silvestri"\n' >&2
  printf '       git config --global user.email "dasilvestri@utexas.edu"\n\n' >&2
  printf '   The address must be one registered on your GitHub account,\n' >&2
  printf '   or the commits will not be attributed to you.\n\n' >&2
  exit 1
fi

if [ ! -d "$REPO/.git" ]; then
  [ -e "$REPO" ] && die "$REPO exists but is not a git repository. Move it aside."
  ok "cloning into $REPO"
  git clone "$URL" "$REPO"
else
  git -C "$REPO" fetch --quiet origin
  if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
    if [ "$DISCARD" -eq 1 ]; then
      git -C "$REPO" reset --hard --quiet
      git -C "$REPO" clean -qfd
      ok "discarded local changes as asked"
    else
      printf '\n   %s has uncommitted changes.\n\n' "$REPO" >&2
      printf '   It is a generated mirror of site/, so there is almost never\n' >&2
      printf '   anything worth keeping. To throw them away and continue:\n\n' >&2
      printf '       ./publish.sh --discard\n\n' >&2
      printf '   To look first:\n\n' >&2
      printf '       git -C "%s" status\n\n' "$REPO" >&2
      exit 1
    fi
  fi
  branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
  git -C "$REPO" reset --hard --quiet "origin/$branch"
fi

branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
ok "repository at $REPO (branch $branch)"

# keep a LICENSE that lives in the repo but not in site/
license_tmp=""
if [ -f "$REPO/LICENSE" ] && [ ! -f "$SITE/LICENSE" ]; then
  license_tmp="$(mktemp)"
  cp "$REPO/LICENSE" "$license_tmp"
  ok "keeping the existing LICENSE"
fi

# ------------------------------------------------------------------- wipe ---
step "Replacing the contents"
find "$REPO" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$SITE/." "$REPO/"
[ -n "$license_tmp" ] && cp "$license_tmp" "$REPO/LICENSE" && rm -f "$license_tmp"

[ -f "$REPO/index.html" ] || die "index.html did not land at the repository root. Nothing pushed."
[ -f "$REPO/CNAME" ]      || die "CNAME did not copy across. Nothing pushed."
ok "$(find "$REPO" -type f -not -path '*/.git/*' | wc -l | tr -d ' ') files in place"

# ----------------------------------------------------------------- commit ---
step "Staging"
git -C "$REPO" add -A
stat="$(git -C "$REPO" diff --cached --shortstat || true)"
if [ -z "$stat" ]; then
  ok "No differences. The published site already matches this folder."
  exit 0
fi
ok "$(echo "$stat" | sed 's/^ *//')"

if [ "$DRY" -eq 1 ]; then
  printf '\n   Dry run: nothing committed or pushed.\n   Changed paths (first 40):\n\n'
  git -C "$REPO" diff --cached --name-status | head -40 | sed 's/^/   /'
  # Put the repository back exactly as it was found. Leaving the wiped and
  # recopied files in the working tree is what made the next run refuse to
  # start.
  git -C "$REPO" reset --hard --quiet HEAD
  git -C "$REPO" clean -qfd
  printf '\n   working tree restored; the repository is untouched\n'
  exit 0
fi

[ -n "$MSG" ] || MSG="Rebuild site: globe atlas, 3D brain, wider layout, corrected models ($(date +%Y-%m-%d))"
git -C "$REPO" commit -q -m "$MSG"
ok "committed: $MSG"

step "Pushing"
if ! git -C "$REPO" push origin "$branch"; then
  cat >&2 <<'HELP'

   The push was refused. The commit is safe on this machine; only the
   upload failed.

   If the message above says "Permission ... denied to <some-name>", git is
   signed in as a different GitHub account than the one that owns this
   repository. Windows caches the first account you ever used and reuses it
   silently. Clear it and sign in again:

       printf "protocol=https\nhost=github.com\n\n" | git credential reject
       ./publish.sh

   A browser window will open. Sign in as the account that owns the
   repository. You can check which one that is by opening the repository
   page on GitHub and reading the owner in the URL.

   Windows also keeps the credential in Control Panel -> Credential Manager
   -> Windows Credentials, listed as git:https://github.com, if you would
   rather remove it there.

HELP
  exit 1
fi
ok "pushed"

cat <<'EOF'

   Live in a minute or two:
     https://andrewsilvestri.com
     https://andrew-silvestri.github.io

   If the pages look stale, hard reload with Ctrl+F5. The old stylesheet and
   favicon cache aggressively.
EOF
