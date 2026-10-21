"""The takeaway app's engine (takeaway/engine.js) against the Python model (takeaway/model.py).

On the tests/test_parity.py pattern: the same inputs through both, compared.
The inputs are the ones the app ships (takeaway/build_app.app_data), so a
difference is the port, not the data.

  The default setting and 200 random ones (growth 0-15%/yr, k 0.60-0.90, each
  reference month the app offers, delay 0-24 months, each expected line in or
  out at random): every month's headroom must agree to 1e-12 Bcf/d, and the
  first month below zero must be the same month.

--break   swaps the JS growth formula (1 + r)^(n/12) for (1 + r/12)^n, the
          nominal-monthly reading of "r per year"; the run must exit 1.

Run:  python tests/test_parity_takeaway.py [--break]
"""
import json
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TAKEAWAY = os.path.join(os.path.dirname(HERE), "takeaway")
sys.path.insert(0, TAKEAWAY)

import build_app as B   # noqa: E402
import model as M       # noqa: E402

BREAK = "--break" in sys.argv
TOL = 1e-12

NODE = r"""
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8');
if (process.argv[4] === 'break') {
  const target = 'Math.pow(1.0 + r, monthsBetween(last, t) / 12.0)';
  if (src.split(target).length !== 2) { console.error('break did not find its target'); process.exit(3); }
  src = src.replace(target, 'Math.pow(1.0 + r / 12.0, monthsBetween(last, t))');
}
const m = { exports: {} }; new Function('module', 'window', src)(m, undefined); const E = m.exports;
const job = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const D = job.data;
const entries = D.entries.map(e => Object.assign({}, e, { month: E.parse(e.month) }));
const out = job.runs.map(s => {
  const r = E.scenario(D.P, E.parse(D.last), entries, s.k, E.parse(s.t0), s.r, s.delay, E.parse(D.until),
                       s.include ? new Set(s.include) : null);
  return { H: r.H, first: r.first };
});
process.stdout.write(JSON.stringify(out));
"""


def ym(s):
    y, m = s.split("-")
    return (int(y), int(m))


def key(t):
    return f"{t[0]}-{t[1]:02d}"


def main():
    D = B.app_data(json.loads(B.PAYLOAD.read_text(encoding="utf-8")))
    expected = [e["key"] for e in D["entries"] if e["status"] == "expected"]
    rng = random.Random(20261018)
    runs = [{"r": 0.0, "k": D["k_default"], "t0": D["t0"], "delay": 0, "include": None},
            {"r": 0.05, "k": D["k_default"], "t0": D["t0"], "delay": 0, "include": None}]
    for _ in range(200):
        runs.append({"r": rng.uniform(0, 0.15), "k": rng.uniform(0.60, 0.90), "t0": rng.choice(D["t0_options"]),
                     "delay": rng.randint(0, 24), "include": [k for k in expected if rng.random() < 0.6]})
    with tempfile.TemporaryDirectory() as tmp:
        job = os.path.join(tmp, "job.json")
        script = os.path.join(tmp, "run.js")
        with open(job, "w", encoding="utf-8") as f:
            json.dump({"data": D, "runs": runs}, f)
        with open(script, "w", encoding="utf-8") as f:
            f.write(NODE)
        res = subprocess.run(["node", script, str(B.ENGINE), job, "break" if BREAK else "clean"],
                             capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        print("FAIL: node exited", res.returncode)
        return 1
    js = json.loads(res.stdout)
    P = {ym(k): v for k, v in D["P"].items()}
    entries = [dict(e, month=ym(e["month"])) for e in D["entries"]]
    worst, first_bad, n = 0.0, 0, 0
    for s, j in zip(runs, js):
        H, first = M.scenario(P, ym(D["last"]), entries, s["k"], ym(s["t0"]), s["r"], s["delay"], ym(D["until"]),
                              set(s["include"]) if s["include"] is not None else None)
        if set(key(t) for t in H) != set(j["H"]):
            print("FAIL: months differ for", s)
            return 1
        for t, v in H.items():
            worst = max(worst, abs(v - j["H"][key(t)]))
            n += 1
        if (key(first) if first else None) != j["first"]:
            first_bad += 1
    print(f"  {len(runs)} settings, {n} months: worst |H_py - H_js| = {worst:.2e} Bcf/d (tolerance {TOL:g}); "
          f"first month below zero differs in {first_bad}")
    ok = worst <= TOL and first_bad == 0
    print(("OK" if ok else "FAIL") + (" (break run)" if BREAK else ""))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
