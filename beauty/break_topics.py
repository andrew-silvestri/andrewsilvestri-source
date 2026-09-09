"""Break fetch_topics.py's exit paths and check every one writes the log.

fetch_topics.py is a NEW fetcher and inherits none of fetch_openalex.py's
protections; it only has them because they were written in again. This
proves the last and newest of them - the try/finally - the same way
break_log.py proves fetch_openalex.py's, over the same five exit paths:

  the log IS written        the run's spend reaches the file that records it
  the rows are intact       what was paid for is still on disk
  the exit is NON-ZERO      the failure is still a failure

A finally that swallows the traceback is worse than no finally, so all
three are asserted together. Nothing touches the real data/: each case runs
against a temporary HERE with its own tables, log and lock directory, and
the network is replaced by a stub.

WHAT 5/5 DOES NOT PROMISE. The guarantee is "every exit path THE INTERPRETER
CONTROLS", not every exit path. All five cases below are Python-level: an
exception can be caught and a finally can run. **A SIGKILL cannot be caught,
so the finally does not run, the log line is not written and the lock is not
released.** That is not a gap this harness can close or test - it is the
boundary of the mechanism, and it was observed on 9 September 2026 when a
run was stopped from outside: rows survived (each is flushed as written) and
the log line did not exist. Five green lines are not a promise about power
cuts, kill -9 or a task runner stopping the process.

RECOVERING FROM AN ORPHANED LOCK, so nobody improvises it mid-run:

  1. read data/raw/.locks/<name>.lock - the first field is the pid;
  2. confirm that pid is GONE (PowerShell: Get-Process -Id <pid>);
  3. only then remove the file.

netutil.Lock.STALE is 120 s and locks() reports a lock older than that as
dead, so waiting two minutes and letting the mechanism say so is the better
move when there is no hurry - it tests the dead-lock path with a real
orphan, which is the only way that path is ever exercised. Deleting a lock
without step 2 can delete a LIVE one and let a build hash a table that is
still growing, which is the whole reason the lock exists.

Run:  python3 break_topics.py
"""

import contextlib
import csv
import importlib
import io
import os
import sys
import tempfile
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SPECIES = ["Aa aa", "Bb bb", "Cc cc", "Dd dd", "Ee ee"]
FAIL_AFTER = 3
# two fields with counts, so a species yields two rows and the row count
# and the species count cannot be confused for one another
GROUPS = [{"key": "11", "count": 7}, {"key": "13", "count": 2}]


def sandbox(mod, tmp):
    data = os.path.join(tmp, "data")
    os.makedirs(data, exist_ok=True)
    mod.HERE = tmp
    mod.DATA = data
    mod.OUT = os.path.join(data, "topic_counts.csv")
    mod.LOG = os.path.join(data, "topic_run_log.txt")
    mod.targets = lambda which: list(SPECIES)
    return mod.OUT, mod.LOG


def stub(fault):
    calls = {"n": 0}

    def inner(url, **kw):
        calls["n"] += 1
        if fault is not None and calls["n"] > FAIL_AFTER:
            raise fault
        return {"meta": {"count": 9, "cost_usd": 0.001}, "group_by": list(GROUPS)}
    return inner


def run(label, fault, want_species, want_exit, want_in_log):
    mod = importlib.reload(importlib.import_module("fetch_topics"))
    tmp = tempfile.mkdtemp(prefix="beauty-breaktopics-")
    out, log = sandbox(mod, tmp)
    mod.get_json = stub(fault)
    os.environ.pop("OPENALEX_KEY", None)

    code = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mod.main("nonlc", 0)
    except BaseException:                                        # noqa: BLE001
        code = 1

    rows = 0
    species = set()
    if os.path.exists(out):
        for r in csv.DictReader(open(out, encoding="utf-8")):
            rows += 1
            species.add(r["species"])
    logged = open(log, encoding="utf-8").read() if os.path.exists(log) else ""

    fails = []
    if not logged.strip():
        fails.append("the log was NOT written")
    elif want_in_log not in logged:
        fails.append(f"log does not name the fault; wanted {want_in_log!r}, "
                     f"got {logged.strip()[-70:]!r}")
    if len(species) != want_species:
        fails.append(f"{len(species)} species on disk, expected {want_species}")
    if rows != want_species * len(GROUPS):
        fails.append(f"{rows} rows, expected {want_species * len(GROUPS)}")
    if code != want_exit:
        fails.append(f"exit {code}, expected {want_exit}"
                     + (" - a finally that swallows the traceback" if code == 0 else ""))
    mark = "ok " if not fails else "FAIL"
    print(f"  {mark} {label:26s} species={len(species)} rows={rows} exit={code} "
          f"log={'yes' if logged.strip() else 'NO'}")
    for f in fails:
        print(f"       - {f}")
    return fails


def main():
    import fetch_topics as F0
    http402 = urllib.error.HTTPError("https://api.openalex.org/works", 402,
                                     "Payment Required", None, None)
    cases = [
        ("clean run",       None,                                5, 0, "species=5"),
        ("402 mid-loop",    http402,                             3, 1, "HTTPError"),
        ("5xx that sticks", urllib.error.URLError("conn reset"), 3, 1, "URLError"),
        ("keyboard kill",   KeyboardInterrupt(),                 3, 1, "KeyboardInterrupt"),
        ("budget 429",      F0.Budget("429 from https://api.openalex.org/works"),
                            3, 0, "stopped at 429"),
    ]
    bad = []
    for label, fault, sp, code, want in cases:
        bad += [f"{label}: {f}" for f in run(label, fault, sp, code, want)]
    ok = len(cases) - len({b.split(":")[0] for b in bad})
    print(f"  {ok}/{len(cases)} exit paths log correctly")
    for b in bad:
        print("  PROBLEM: " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
