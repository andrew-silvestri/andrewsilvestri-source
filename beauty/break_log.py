"""Break the run log on purpose and check every exit path still writes it.

A test nobody has seen fail is a claim, not a check. fetch_openalex.main()
caught only Budget until 8 September 2026, so a 402, a 403 or a 5xx that
outlived four retries exited on a traceback with the rows flushed and
nothing in data/openalex_run_log.txt -- the file README.md tells a reader
the page's cost figure is quoted from. The fix is a finally. A finally that
swallows the traceback would be worse than no finally, so this asserts all
three things at once, per exit path:

  the log IS written        the run's spend reaches the file the page cites
  the rows are intact       what was paid for is still on disk
  the exit is NON-ZERO      the failure is still a failure

Nothing touches the real data/: each case runs against a temporary HERE
with its own species list, output table, log and lock directory, and the
network is replaced by a stub.

Run:  python3 break_log.py
"""

import csv
import importlib
import io
import os
import contextlib
import sys
import tempfile
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SPECIES = ["Aa aa", "Bb bb", "Cc cc", "Dd dd", "Ee ee"]
FAIL_AFTER = 3          # three rows written, then the fault


def sandbox(mod, tmp):
    """Point the module at a throw-away tree."""
    data = os.path.join(tmp, "data")
    os.makedirs(data, exist_ok=True)
    with open(os.path.join(data, "avonet_slim.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["species"])
        for s in SPECIES:
            w.writerow([s])
    mod.HERE = tmp
    mod.SPECIES = os.path.join(data, "avonet_slim.csv")
    mod.OUT = os.path.join(data, "openalex_counts.csv")
    mod.LOG = os.path.join(data, "openalex_run_log.txt")
    return mod.OUT, mod.LOG


def stub(fault):
    """A get_json that answers FAIL_AFTER times, then raises `fault`."""
    calls = {"n": 0}

    def inner(url, **kw):
        calls["n"] += 1
        if fault is not None and calls["n"] > FAIL_AFTER:
            raise fault
        return {"meta": {"count": 42, "cost_usd": 0.001}}
    return inner


def run(label, fault, want_rows, want_exit, want_in_log):
    mod = importlib.reload(importlib.import_module("fetch_openalex"))
    tmp = tempfile.mkdtemp(prefix="beauty-breaklog-")
    out, log = sandbox(mod, tmp)
    mod.get_json = stub(fault)
    os.environ.pop("OPENALEX_KEY", None)

    code = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mod.main()
    except BaseException:                                        # noqa: BLE001
        code = 1

    rows = 0
    if os.path.exists(out):
        rows = sum(1 for _ in csv.DictReader(open(out, encoding="utf-8")))
    logged = open(log, encoding="utf-8").read() if os.path.exists(log) else ""

    fails = []
    if not logged.strip():
        fails.append("the log was NOT written")
    elif want_in_log not in logged:
        fails.append(f"the log does not name the fault; wanted {want_in_log!r}, "
                     f"got {logged.strip()[-70:]!r}")
    if rows != want_rows:
        fails.append(f"{rows} rows on disk, expected {want_rows}")
    if code != want_exit:
        fails.append(f"exit {code}, expected {want_exit}"
                     + (" - a finally that swallows the traceback" if code == 0 else ""))
    mark = "ok " if not fails else "FAIL"
    print(f"  {mark} {label:26s} rows={rows} exit={code} log={'yes' if logged.strip() else 'NO'}")
    for f in fails:
        print(f"       - {f}")
    return fails


def main():
    http402 = urllib.error.HTTPError("https://api.openalex.org/works", 402,
                                     "Payment Required", None, None)
    import fetch_openalex as F0
    cases = [
        # label,            fault,                     rows, exit, log must contain
        ("clean run",       None,                      5,    0,    "species=5"),
        ("402 mid-loop",    http402,                   3,    1,    "HTTPError"),
        ("5xx that sticks", urllib.error.URLError("conn reset"), 3, 1, "URLError"),
        ("keyboard kill",   KeyboardInterrupt(),       3,    1,    "KeyboardInterrupt"),
        ("budget 429",      F0.Budget("429 from https://api.openalex.org/works"),
                            3,    0,    "stopped at 429"),
    ]
    bad = []
    for label, fault, rows, code, want in cases:
        bad += [f"{label}: {f}" for f in run(label, fault, rows, code, want)]
    print(f"  {len(cases) - len({b.split(':')[0] for b in bad})}/{len(cases)} exit paths log correctly")
    for b in bad:
        print("  PROBLEM: " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
