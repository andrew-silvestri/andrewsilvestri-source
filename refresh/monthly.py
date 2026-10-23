"""The monthly data refresh (R1 section 5, D-42). Run by a Windows scheduled
task on Andrew's laptop; nobody needs to start it.

    python refresh/monthly.py            the real run (what the task starts)
    python refresh/monthly.py --dry-run  everything up to the publish, which
                                         is a publish.sh --dry-run; then the
                                         tree goes back to clean master and
                                         the branch is deleted
    python refresh/monthly.py --dry-run --with meter
                                         include a registry entry that is not
                                         yet enabled (dry runs only)

What a run does, in order, and it stops at the first thing that is not green:

  1. preflight   the tree is clean master, REPO and PUBLISH_MIRROR are unset
                 (D-08), this month has not already been published, and
                 master is level with origin. A tree a terminal is working in
                 is never touched: the run logs "busy" and the daily retry
                 trigger tries again tomorrow.
  2. branch      data/refresh-YYYY-MM from master.
  3. fetch       each enabled entry in refresh/registry.py: its fetchers, then
                 its payload builders, with keys read from C:\\Users\\dasil\\.env
                 by variable name through envfile.py (D-42). No key is ever
                 printed or logged; a missing key names the variable and stops.
  4. ordering    trap 33's rule, from the page generators registered in
                 tests/test_generators.py through test_generators.py LAST.
  5. suites      the full suite set (refresh/suites.py). Any non-zero exit is
                 red.
  6. publish     if anything changed: commit the tracked files that changed
                 (git add -u, never -A), publish.sh --dry-run with the file
                 list logged, publish.sh, merge --no-ff to master, push. The
                 gate in CLAUDE.md, run by a script.

Red anywhere: nothing is published, the branch is kept (not pushed) for a
person to read, master is checked out clean, and one RUNLOG line says what
failed. Every run, green or red, appends exactly one RUNLOG line and writes a
full log under refresh/logs/ (gitignored).
"""
import argparse
import datetime
import importlib.util
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envfile  # noqa: E402
import registry  # noqa: E402
import suites  # noqa: E402

RUNLOG = os.path.join(os.path.dirname(ROOT), "03 RESEARCH", "oct-2026", "RUNLOG.md")
LOGDIR = os.path.join(ROOT, "refresh", "logs")
BASH = r"C:\Program Files\Git\bin\bash.exe"   # Git Bash; the PATH bash is WSL (CLAUDE.md)
# the ordering rule's tail, after the page generators (trap 33)
TAIL = [("rezip", ["rezip_downloads.py"]), ("code rows", ["sync_code_rows.py", "--apply"]),
        ("img dims", ["sync_img_dims.py"]), ("bust", ["bust_cache.py"]),
        ("sitemap", ["build_sitemap.py", "--apply"]), ("drift check LAST", ["tests/test_generators.py"])]
TAIL_SCRIPTS = {c[0] for _, c in TAIL}


class Red(Exception):
    """Something is not green: publish nothing, say what."""


class Busy(Exception):
    """The tree is in use or not where a run can start: touch nothing."""


def now():
    return datetime.datetime.now()


class Run:
    def __init__(self, dry, month):
        self.dry, self.month = dry, month
        os.makedirs(LOGDIR, exist_ok=True)
        self.logpath = os.path.join(LOGDIR, "%s%s.log" % (now().strftime("%Y-%m-%d_%H%M%S"), "_dry" if dry else ""))
        self.fh = open(self.logpath, "w", encoding="utf-8", newline="\n")
        # REPO and PUBLISH_MIRROR are never passed on (D-08): publish.sh reads
        # PUBLISH_MIRROR as the mirror, and REPO once took the source tree for it
        self.env = {k: v for k, v in os.environ.items() if k not in ("REPO", "PUBLISH_MIRROR")}
        self.env["NODE_PATH"] = os.path.join(ROOT, "tests", "node_modules")
        self.env["PYTHONIOENCODING"] = "utf-8"

    def log(self, msg):
        line = "%s  %s" % (now().strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        self.fh.write(line + "\n")
        self.fh.flush()

    def sh(self, cmd, cwd=ROOT, timeout=3600, check=True):
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=cwd, env=self.env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = 124, "timed out after %ds" % timeout
        self.fh.write("$ %s  (cwd %s)\n%s\n[rc=%d, %.0fs]\n" % (" ".join(cmd), os.path.relpath(cwd, ROOT), out, rc, time.time() - t0))
        self.fh.flush()
        if check and rc != 0:
            last = [ln for ln in out.strip().splitlines() if ln.strip()][-1:] or [""]
            raise Red("%s exited %d: %s" % (" ".join(cmd), rc, last[0][:160]))
        return rc, out

    def git(self, *a, check=True):
        return self.sh(["git"] + list(a), check=check)[1].strip()

    def on(self, branch):
        """Refuse to go on if the tree has left this run's branch. Found
        2026-10-23: a dry run kept running after its launching shell died,
        and its cleanup switched a terminal's branch to master. Every step
        that writes to the tree or to git checks this first."""
        cur = self.git("branch", "--show-current", check=False)
        if cur != branch:
            raise Red("the tree moved under the run: on %s, expected %s; touching nothing" % (cur or "(detached)", branch))


LOCK = os.path.join(ROOT, "refresh", "RUNNING")
STALE_S = 12 * 3600   # longer than the task's 8 h limit


def lock():
    """One run at a time. Returns None, or why the lock is held."""
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        age = time.time() - os.path.getmtime(LOCK)
        if age < STALE_S:
            return "another refresh run holds refresh/RUNNING (%.0f min old)" % (age / 60)
        os.remove(LOCK)   # older than any run can last: its run is gone
        return lock()
    os.write(fd, ("%d %s\n" % (os.getpid(), now().isoformat(timespec="seconds"))).encode())
    os.close(fd)
    return None


def runlog(line):
    with open(RUNLOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s %s\n" % (now().strftime("%Y-%m-%d %H:%M"), line))


def done_this_month(month, text=None):
    if text is None:
        try:
            text = open(RUNLOG, encoding="utf-8").read()
        except OSError:
            return False
    return ("REFRESH DONE %s" % month) in text or ("REFRESH NOCHANGE %s" % month) in text


def preflight(status, branch, env):
    """Pure, so tests/test_refresh.py can drive it. Returns None or why not."""
    if env.get("REPO") or env.get("PUBLISH_MIRROR"):
        return "REPO or PUBLISH_MIRROR is set (D-08)"
    if branch.startswith("data/refresh-"):
        # a run that was killed (shutdown, closed session) stops here, on its
        # own branch, possibly with fetched files modified: found 2026-10-23
        # when a dry run was killed mid-suite. Nothing repairs it unattended.
        return ("a refresh run was interrupted and left the tree on %s; read its log in "
                "refresh/logs, then restore the tree to clean master and delete that branch" % branch)
    if branch != "master":
        return "the tree is on %s, not master" % branch
    if status.strip():
        return "the tree has %d uncommitted line(s)" % len(status.strip().splitlines())
    return None


def entries(with_pages, dry, reg=None):
    reg = registry.ENTRIES if reg is None else reg
    out = [e for e in reg if e["enabled"]]
    for p in with_pages:
        if not dry:
            raise Red("--with is for dry runs only")
        e = [x for x in reg if x["page"] == p]
        if not e:
            raise Red("--with %s: no such registry entry" % p)
        if e[0] not in out:
            out.append(e[0])
    return out


def publish_files(out):
    """The file lines publish.sh --dry-run prints: `git diff --cached
    --name-status | head -40`, indented three spaces, so a status letter, a
    TAB and a path ("   M\\tindex.html"). At most 40; the shortstat line above
    them carries the full count."""
    return [ln.strip() for ln in out.splitlines() if re.match(r"^   [MADRCT]\d*\t\S", ln)]


def back_to_master(run, branch, delete):
    """Leave the run's branch for master, and rebuild the download archives.
    site/downloads/ is gitignored, so switching branches restores the sources
    but not the archives built from them: on 2026-10-23 a dry run's rezip left
    meter-code.zip holding the newly fetched data/fetched.json while master
    held the old one, and tests/test_generators.py reported DRIFT downloads on
    every run after it."""
    run.git("switch", "-q", "master", check=False)
    if delete:
        run.git("branch", "-q", "-D", branch, check=False)
    run.sh(["python", "rezip_downloads.py"], check=False)


def ordering(run):
    spec = importlib.util.spec_from_file_location("tg", os.path.join(ROOT, "tests", "test_generators.py"))
    tg = importlib.util.module_from_spec(spec)
    saved, sys.argv = sys.argv, ["test_generators.py"]
    try:
        spec.loader.exec_module(tg)
    finally:
        sys.argv = saved
    steps = [(n, c, cwd) for n, c, cwd, mode in tg.GENERATORS if mode == "site" and c[0] not in TAIL_SCRIPTS]
    steps += [(n, c, ".") for n, c in TAIL]
    for name, cmd, cwd in steps:
        run.log("ordering: %s" % name)
        run.sh(["python"] + cmd, cwd=os.path.join(ROOT, cwd))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with", dest="with_pages", action="append", default=[])
    a = ap.parse_args()
    month = now().strftime("%Y-%m")
    tag = "REFRESH DRY" if a.dry_run else "REFRESH"
    if not a.dry_run and done_this_month(month):
        print("refresh: %s already done" % month)
        return 0
    held = lock()
    if held:
        runlog("%s BUSY %s: %s; nothing touched" % (tag, month, held))
        print("refresh: " + held)
        return 3
    run = Run(a.dry_run, month)
    run.log("refresh %s%s, log %s" % (month, " (dry run)" if a.dry_run else "", run.logpath))
    branch = None
    try:
        why = preflight(run.git("status", "--short"), run.git("branch", "--show-current"), os.environ)
        if why:
            raise Busy(why)
        run.git("fetch", "-q", "origin", "master")
        ahead = run.git("rev-list", "--count", "origin/master..master")
        if ahead != "0":
            raise Busy("master is %s commit(s) ahead of origin; a terminal has not pushed" % ahead)
        if run.git("rev-list", "--count", "master..origin/master") != "0":
            run.git("merge", "-q", "--ff-only", "origin/master")
        es = entries(a.with_pages, a.dry_run)
        pages = ", ".join(e["page"] for e in es)
        if not es and not a.dry_run:
            runlog("%s NOCHANGE %s: no page is enabled in refresh/registry.py" % (tag, month))
            run.log("no enabled entries")
            return 0
        for e in es:
            for k in e["keys"]:
                if not envfile.get(k):
                    raise Red("missing key %s in C:\\Users\\dasil\\.env (needed by %s)" % (k, e["page"]))
        branch = "data/refresh-%s%s" % (month, now().strftime("-dry-%H%M%S") if a.dry_run else "")
        n = 2
        while run.git("branch", "--list", branch):
            branch = "data/refresh-%s-%d" % (month, n)
            n += 1
        run.git("switch", "-q", "-c", branch)
        run.log("branch %s; pages: %s" % (branch, pages or "none"))
        for e in es:
            run.on(branch)
            for cmd in e["fetch"] + e["build"]:
                run.log("%s: %s" % (e["page"], " ".join(cmd)))
                run.sh(cmd, cwd=os.path.join(ROOT, e["cwd"]), timeout=7200)
        run.on(branch)
        ordering(run)
        run.on(branch)
        cmds, red = suites.commands(ROOT), []
        for c in cmds:
            rc, _ = run.sh(c.split(), timeout=3600, check=False)
            run.log("suite rc=%d  %s" % (rc, c))
            if rc != 0:
                red.append(c)
        if red:
            raise Red("%d of %d suites red: %s" % (len(red), len(cmds), "; ".join(red[:4])))
        run.on(branch)
        status = run.git("status", "--short", "--untracked-files=all")
        untracked = [ln[3:] for ln in status.splitlines() if ln.startswith("??")]
        if untracked:
            raise Red("new untracked file(s) the registry does not declare: %s" % ", ".join(untracked[:5]))
        if not status:
            back_to_master(run, branch, delete=True)
            runlog("%s NOCHANGE %s: fetched %s, ordering and %d suites green, nothing on the site changed; log %s"
                   % (tag, month, pages or "nothing", len(cmds), os.path.relpath(run.logpath, ROOT)))
            run.log("nothing changed")
            return 0
        run.git("add", "-u")
        run.git("commit", "-q", "-m", "refresh %s: %s\n\nMonthly data refresh (refresh/monthly.py, D-42)." % (month, pages))
        _, out = run.sh([BASH, "./publish.sh", "--dry-run"], timeout=1800)
        files = publish_files(out)
        run.log("publish.sh --dry-run: %d file(s)\n    %s" % (len(files), "\n    ".join(files)))
        if a.dry_run:
            run.on(branch)
            back_to_master(run, branch, delete=True)
            runlog("%s %s: fetched %s, ordering and %d suites green, publish dry run %d file(s); nothing published, branch deleted; log %s"
                   % (tag, month, pages, len(cmds), len(files), os.path.relpath(run.logpath, ROOT)))
            return 0
        mirror = os.path.join(os.path.expanduser("~"), "andrew-silvestri.github.io")
        before = run.sh(["git", "-C", mirror, "rev-parse", "--short", "HEAD"])[1].strip()
        run.sh([BASH, "./publish.sh", "-m", "refresh %s" % month], timeout=1800)
        after = run.sh(["git", "-C", mirror, "rev-parse", "--short", "HEAD"])[1].strip()
        if before == after:
            raise Red("publish.sh ran but the mirror did not move (%s)" % before)
        run.on(branch)
        run.git("switch", "-q", "master")
        run.git("merge", "-q", "--no-ff", branch, "-m", "Merge: refresh %s" % month)
        run.git("push", "-q", "origin", "master")
        run.git("branch", "-q", "-d", branch)
        runlog("%s DONE %s: %s; mirror %s -> %s, master %s; %d file(s); rollback: in the mirror, git revert %s"
               % (tag, month, pages, before, after, run.git("rev-parse", "--short", "HEAD"), len(files), after))
        return 0
    except Busy as e:
        runlog("%s BUSY %s: %s; nothing touched, the daily trigger retries" % (tag, month, e))
        run.log("busy: %s" % e)
        return 3
    except Red as e:
        run.log("RED: %s" % e)
        kept = ""
        if branch and run.git("branch", "--show-current", check=False) == branch:
            if run.git("status", "--short", check=False):
                # tracked changes, and new files named one by one (never add -A),
                # so master is left clean whatever the run wrote
                run.git("add", "-u", check=False)
                new = run.git("ls-files", "--others", "--exclude-standard", check=False).splitlines()
                if new:
                    run.git("add", "--", *new, check=False)
                run.git("commit", "-q", "-m", "refresh %s: RED, kept for reading\n\n%s" % (month, e), check=False)
            back_to_master(run, branch, delete=a.dry_run)
            if not a.dry_run:
                kept = "; branch %s kept, not pushed" % branch
        runlog("%s RED %s: %s; nothing published%s; log %s" % (tag, month, e, kept, os.path.relpath(run.logpath, ROOT)))
        return 1
    finally:
        run.fh.close()
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
