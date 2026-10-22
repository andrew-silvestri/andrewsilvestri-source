"""The lost-gas app's engine (lauf/engine.js) against the Python model (lauf/model.py).

On the tests/test_parity.py pattern: the same inputs through both, compared.

  1. Identical draws: numpy generates the standard normals once; model.from_draws and
     engine.fromDraws both turn them into every system's figure in both years, for the defaults
     and 200 random settings inside the app's slider limits. Every value must agree to 1e-12.
  2. The app's own sampler: engine.summary at the defaults (its own mulberry32 draws) must agree
     with model.summary's quantiles to sampling error (0.05 points at the app's 20,000 systems).

--break   swaps the JS temperature bias to its inverse, (T_base / T - 1), the sign a port gets wrong
          when it reads "billed as if at 60 F" the other way round; the run must exit 1.

Run:  python tests/test_parity_lauf.py [--break]
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAUF = os.path.join(os.path.dirname(HERE), "lauf")
sys.path.insert(0, LAUF)
import model as M   # noqa: E402

BREAK = "--break" in sys.argv
TOL = 1e-12
N = 400

NODE = r"""
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8');
if (process.argv[4] === 'break') {
  const target = 'kelvin(gasTempF) / kelvin(T_BASE_F)';
  if (src.split(target).length !== 2) { console.error('break did not find its target'); process.exit(3); }
  src = src.replace(target, 'kelvin(T_BASE_F) / kelvin(gasTempF)');
}
const m = { exports: {} };
new Function('module', 'window', src)(m, undefined);
const E = m.exports;
const job = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const z = {};
for (const k in job.z) z[k] = job.z[k].map(r => Float64Array.from(r));
const out = job.settings.map(p => E.fromDraws(p, z).map(a => Array.from(a)));
const summ = E.summary(job.defaults, 20000, 20261022);
process.stdout.write(JSON.stringify({ out, summ }));
"""


def main():
    rng = np.random.default_rng(7)
    z = M.draws(N, rng)
    settings = [dict(M.DEFAULTS)]
    for _ in range(200):
        p = {}
        for k, (lo, hi) in M.LIMITS.items():
            p[k] = float(rng.uniform(lo, hi)) if k != "n_meters" else int(rng.integers(lo, hi))
        settings.append(p)
    with tempfile.TemporaryDirectory() as td:
        job = os.path.join(td, "job.json")
        json.dump({"z": {k: v.tolist() for k, v in z.items()}, "settings": settings, "defaults": M.DEFAULTS},
                  open(job, "w", encoding="utf-8"))
        js = os.path.join(td, "run.js")
        open(js, "w", encoding="utf-8").write(NODE)
        r = subprocess.run(["node", js, os.path.join(LAUF, "engine.js"), job, "break" if BREAK else ""],
                           capture_output=True, text=True)
    if r.returncode != 0:
        print("  FAIL node ran the engine:", r.returncode, r.stderr[-400:])
        return 1
    res = json.loads(r.stdout)
    worst = 0.0
    for p, (j1, j2) in zip(settings, res["out"]):
        y1, y2 = M.from_draws(p, z)
        worst = max(worst, float(np.max(np.abs(np.array(j1) - y1))), float(np.max(np.abs(np.array(j2) - y2))))
    fails = 0
    ok1 = worst <= TOL
    print(f"  {'OK  ' if ok1 else 'FAIL'} identical draws, {len(settings)} settings x {N} systems x 2 years: "
          f"worst |JS - Python| = {worst:.2e} points (tolerance {TOL:g})")
    fails += not ok1
    py = M.summary({})
    js = res["summ"]
    dev = max(abs(js[part][q] - py[part][q]) for part in ("level", "change") for q in ("p10", "p25", "p50", "p75", "p90"))
    ok2 = dev <= 0.05
    print(f"  {'OK  ' if ok2 else 'FAIL'} the app's own sampler at the defaults against model.summary: "
          f"worst quantile difference {dev:.3f} points (tolerance 0.05)")
    fails += not ok2
    print("OK" if not fails else f"{fails} failure(s)" + (" (break run)" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
