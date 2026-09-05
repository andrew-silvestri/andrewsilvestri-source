"""The two engines must agree.

The propagation exists twice: site/assets/atlas-app.js, the browser copy and
the model of record, and build_throughlines.py's engine(), the sparse
linear-algebra copy every figure builder uses. HANDOFF section 6 lists four
properties of that engine that took a long time to get right and says any
change goes into both; until 2026-09-05 nothing checked that they had. This
runs every prepared scenario through both - the browser engine headless via
tests/parity_engine.js, the Python engine directly - and compares the settled
state of all 86,622 nodes, scenario by scenario, plus the number of rounds
each took to settle.

Tolerance: TOL below, on the largest absolute difference in any node's
effect. The two engines do the same arithmetic in a different order (a
per-edge loop against a sparse matrix product), so agreement is to
floating-point rounding, not to zero: the measured worst case on 2026-09-05
was 1.1e-15 over all sixty scenarios, with every step count equal. TOL is
three orders above that, and the worst number is printed so a drift shows up
as a number before it shows up as a failure.

Run:  python tests/test_parity.py            # all 60 scenarios
      python tests/test_parity.py --only fusion   # keys containing a string
Exit status 1 on any scenario outside TOL, on a step-count disagreement, or
if either engine cannot run.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

TOL = 1e-12


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="run scenarios whose key contains this")
    args = ap.parse_args()

    from build_throughlines import engine  # noqa: E402  (imports matplotlib; fine)
    raw = open(os.path.join(ROOT, "site", "assets", "atlas-data.js"), encoding="utf-8").read()
    D = json.loads(raw[raw.index("=") + 1:raw.rindex(";")])
    ids = {k: int(v) for k, v in D["idMap"].items()}
    keys = [k for k in D["scenarios"] if not args.only or args.only.lower() in k.lower()]
    if not keys:
        print("no scenario matches", args.only)
        return 1

    tmp = tempfile.mkdtemp(prefix="parity-")
    try:
        r = subprocess.run(["node", os.path.join(HERE, "parity_engine.js"), tmp] + keys,
                           capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            print("browser engine failed:\n" + (r.stderr or r.stdout))
            return 1
        js = json.load(open(os.path.join(tmp, "index.json")))
        if js["n"] != D["n"]:
            print(f"node counts differ: browser {js['n']}, payload {D['n']}")
            return 1
        run, _ = engine(D)
        worst, bad = 0.0, 0
        print(f"  {'scenario':34s} {'steps js/py':>12s} {'touched':>8s} {'max |diff|':>12s}")
        for key in keys:
            sc = D["scenarios"][key]
            shocks = {ids[i]: a for i, a in sc["shocks"].items() if i in ids}
            st, hist = run(shocks)
            steps_py = len(hist) - 1
            a = np.fromfile(os.path.join(tmp, key + ".f64"), dtype="<f8")
            diff = float(np.abs(a - st).max())
            steps_js = js["scenarios"][key]["steps"]
            worst = max(worst, diff)
            ok = diff <= TOL and steps_js == steps_py
            bad += not ok
            print(f"  {'ok  ' if ok else 'FAIL'} {key[:29]:29s} {steps_js:5d}/{steps_py:<6d} "
                  f"{js['scenarios'][key]['touched']:8d} {diff:12.2e}")
        print(f"\n  {len(keys) - bad}/{len(keys)} scenarios agree to {TOL:g}; "
              f"worst disagreement {worst:.2e}")
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
