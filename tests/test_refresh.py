"""The monthly refresh's own checks (R1 section 5).

    python tests/test_refresh.py                 exit 1 on any failure
    python tests/test_refresh.py --break <name>  reproduce a fault; must exit 1

  coverage  every suite in tests/ is in refresh/suites.py (FIXED, OPTIONAL) or
            named in SKIP, so a suite added later cannot be published past.
            --break coverage: a new tests/test_*.js the list does not know.
  stamp     an enabled registry entry's page carries "Data through <month>"
            (_INSIGHT rule 5): refreshing a page whose reader cannot see the
            data's date moves its figures silently.
            --break stamp: the meter entry turned on while its page has no
            stamp, the mistake the registry's comment warns about.
  preflight a dirty tree, a branch other than master, or REPO/PUBLISH_MIRROR
            set (D-08) each stop the run; clean master starts it.
            --break preflight: preflight() stops reading git status, so a run
            would start in a tree a terminal is working in.
  lock      a second run is refused while one holds refresh/RUNNING.
            --break lock: the lock opened without O_EXCL, so two runs start.
  guard     a run whose tree has left its branch stops before any write.
            --break guard: the check removed - what happened on 2026-10-23,
            when a dry run's cleanup switched another branch to master.
  archives  a run that returns to master unmerged rebuilds site/downloads,
            which is gitignored and so not restored by the switch.
            --break archives: the rebuild removed - the DRIFT downloads of
            2026-10-23 (meter-code.zip holding a dry run's fetched.json).
  month     only a DONE or NOCHANGE line for this month stops a repeat run;
            a DRY, BUSY or RED line does not.
  publish   publish.sh's --dry-run file lines (letter, TAB, path) are what
            monthly.publish_files() counts.
  task      the XML the task is registered from asks for StartWhenAvailable,
            the monthly and the daily trigger, and this repository's
            monthly.py. (What Windows holds is read back by
            refresh/register_task.py --show, not here: that is machine state.)
"""
import importlib.util
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RF = os.path.join(ROOT, "refresh")
BREAKS = ["coverage", "stamp", "preflight", "lock", "guard", "archives"]
BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
if BREAK is not None and BREAK not in BREAKS:
    sys.exit("--break takes one of: " + " | ".join(BREAKS))
sys.path.insert(0, ROOT)
sys.path.insert(0, RF)


def load(name, mutate=None):
    path = os.path.join(RF, name + ".py")
    src = open(path, encoding="utf-8").read()
    if mutate:
        a, b = mutate
        n = src.count(a)
        if n != 1:
            sys.exit("mutation matched %d times, not 1: %r" % (n, a))
        src = src.replace(a, b)
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    mod.__file__ = path
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


fails = checks = 0


def say(ok, what):
    global fails, checks
    checks += 1
    fails += not ok
    print(("  ok   " if ok else "  FAIL ") + what)


# coverage
suites = load("suites")
known = {c.split()[1].split("/")[-1] for c in suites.FIXED + suites.OPTIONAL if c.split()[1].startswith("tests/")}
files = [f for f in os.listdir(HERE) if f.endswith((".py", ".js")) and (f.startswith(("test_", "verify_")) or f == "fig_served_widths.js")]
if BREAK == "coverage":
    files.append("test_new_gate.js")
missing = sorted(f for f in files if f not in known and f not in suites.SKIP)
say(not missing, "coverage: %d suite files in tests/, every one listed or skipped by name%s" % (len(files), (": missing " + ", ".join(missing)) if missing else ""))
absent = [c for c in suites.FIXED if not os.path.exists(os.path.join(ROOT, c.split()[1]))]
say(not absent, "coverage: every FIXED suite exists%s" % ((": " + ", ".join(absent)) if absent else ""))

# stamp
registry = load("registry")
entries = [dict(e) for e in registry.ENTRIES]
if BREAK == "stamp":
    for e in entries:
        if e["page"] == "meter":
            e["enabled"] = True
need = {"page", "cwd", "fetch", "build", "keys", "enabled", "why"}
shape = [e.get("page", "?") for e in entries if set(e) != need or not os.path.isdir(os.path.join(ROOT, e["cwd"]))]
say(not shape, "registry: %d entries, each with exactly %s and a real folder%s" % (len(entries), "/".join(sorted(need)), (": " + ", ".join(shape)) if shape else ""))
import re  # noqa: E402
nostamp = []
for e in entries:
    if not e["enabled"]:
        continue
    page = os.path.join(ROOT, "site", e["page"] + ".html")
    html = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    if not re.search(r'<p class="stamp">Data through <time datetime="\d{4}-\d{2}">', html):
        nostamp.append(e["page"])
say(not nostamp, "stamp: %d enabled entr(y/ies), each page shows Data through <month>%s" % (sum(e["enabled"] for e in entries), (": no stamp on " + ", ".join(nostamp)) if nostamp else ""))

# preflight
MUT = {"preflight": ('    if status.strip():\n        return "the tree has', '    if False:\n        return "the tree has'),
       "lock": ("os.O_CREAT | os.O_EXCL | os.O_WRONLY", "os.O_CREAT | os.O_WRONLY"),
       "archives": ('    run.sh(["python", "rezip_downloads.py"], check=False)', '    pass'),
       "guard": ('        if cur != branch:\n            raise Red("the tree moved', '        if False:\n            raise Red("the tree moved')}
monthly = load("monthly", mutate=MUT.get(BREAK))
cases = [(" M site/index.html", "master", {}, False), ("", "rework/takeaway", {}, False),
         ("", "master", {"REPO": "x"}, False), ("", "master", {"PUBLISH_MIRROR": "x"}, False),
         ("?? meter/new.csv", "master", {}, False), ("", "master", {}, True),
         (" M meter/data/fetched.json", "data/refresh-2026-10", {}, False)]
bad = [c for c in cases if (monthly.preflight(c[0], c[1], c[2]) is None) != c[3]]
intr = monthly.preflight("", "data/refresh-2026-10", {}) or ""
say("interrupted" in intr, "preflight: a tree left on a refresh branch is named as an interrupted run")
say(not bad, "preflight: %d cases, a run starts only on clean master with neither variable set%s" % (len(cases), (": wrong on " + repr(bad[0][:2])) if bad else ""))

# lock and guard: the two faults of 2026-10-23, when a dry run outlived its
# shell and its cleanup switched another branch to master
import tempfile  # noqa: E402
import time as _t  # noqa: E402
tmpd = tempfile.mkdtemp()
monthly.LOCK = os.path.join(tmpd, "RUNNING")
first, second = monthly.lock(), monthly.lock()
os.utime(monthly.LOCK, (_t.time() - 13 * 3600,) * 2)
stale = monthly.lock()
os.remove(monthly.LOCK)
say(first is None and second is not None and stale is None,
    "lock: a second run is refused while the first holds it; a lock older than any run is cleared")


class FakeRun:
    def __init__(self, cur):
        self.cur = cur

    def git(self, *a, check=True):
        return self.cur


guard = monthly.Run.on
moved = None
try:
    guard(FakeRun("kit/refresh-interrupted"), "data/refresh-2026-10")
except monthly.Red as e:
    moved = str(e)
try:
    guard(FakeRun("data/refresh-2026-10"), "data/refresh-2026-10")
    stays = True
except monthly.Red:
    stays = False
say(moved is not None and "moved" in moved and stays,
    "guard: a run whose tree has left its branch stops before writing; on its branch it goes on")

# month
log ="\n".join(["2026-11-02 06:00 REFRESH DRY 2026-11: ...", "2026-11-02 06:00 REFRESH BUSY 2026-11: ...",
                 "2026-11-03 06:30 REFRESH RED 2026-11: ...", "2026-12-02 06:00 REFRESH DRY NOCHANGE 2026-12: ..."])
m_ok = (not monthly.done_this_month("2026-11", log) and not monthly.done_this_month("2026-12", log)
        and monthly.done_this_month("2026-11", log + "\n2026-11-04 06:30 REFRESH DONE 2026-11: ...")
        and monthly.done_this_month("2027-01", "2027-01-02 06:00 REFRESH NOCHANGE 2027-01: no page"))


# leaving a branch unmerged rebuilds the gitignored archives on master
class RecRun:
    def __init__(self):
        self.calls = []

    def git(self, *a, check=True):
        self.calls.append("git " + " ".join(a))
        return ""

    def sh(self, cmd, cwd=None, timeout=None, check=True):
        self.calls.append(" ".join(cmd))
        return 0, ""


rr = RecRun()
monthly.back_to_master(rr, "data/refresh-2026-10-dry-1", delete=True)
say(rr.calls[:2] == ["git switch -q master", "git branch -q -D data/refresh-2026-10-dry-1"]
    and rr.calls[-1] == "python rezip_downloads.py",
    "archives: a run that leaves its branch unmerged switches to master, then rebuilds site/downloads")
say(m_ok,"month: DRY, BUSY and RED lines do not end a month; DONE and NOCHANGE do")

# the file list a run logs and counts, against publish.sh's real format
# (`git diff --cached --name-status | sed 's/^/   /'`: letter, TAB, path).
# A first version split on a space and would have counted zero files.
sample = ("   1 file changed, 2 insertions(+)\n\n   Dry run: nothing committed or pushed.\n"
          "   Changed paths (first 40):\n\n   M\tmeter.html\n   A\tassets/clips/x.mp4\n   R100\ta.png\tb.png\n"
          "   M not-a-file-line\n")
got = monthly.publish_files(sample)
say(got == ["M\tmeter.html", "A\tassets/clips/x.mp4", "R100\ta.png\tb.png"],
    "publish list: publish.sh's name-status lines are read, prose lines are not (%d read)" % len(got))

# task
reg = load("register_task")
ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
t = ET.fromstring(reg.xml().replace('encoding="UTF-16"', ""))
swa = t.find("t:Settings/t:StartWhenAvailable", ns)
trig = t.findall("t:Triggers/t:CalendarTrigger", ns)
day = t.find("t:Triggers/t:CalendarTrigger/t:ScheduleByMonth/t:DaysOfMonth/t:Day", ns)
arg = t.find("t:Actions/t:Exec/t:Arguments", ns).text
say(swa is not None and swa.text == "true" and len(trig) == 2 and day is not None and day.text == "2"
    and os.path.normcase(arg.strip('"')) == os.path.normcase(os.path.join(RF, "monthly.py")),
    "task: StartWhenAvailable, a monthly trigger on the 2nd and a daily retry, running this repository's monthly.py")

print("\n%d/%d passed%s" % (checks - fails, checks, (" (--break %s)" % BREAK) if BREAK else ""))
sys.exit(1 if fails else 0)
