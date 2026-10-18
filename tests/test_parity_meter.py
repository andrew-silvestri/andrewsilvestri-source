"""The meter app's engine (meter/engine.js) against the Python model (meter/model.py).

On the tests/test_parity.py pattern: the same inputs through both, compared.

  1. The meter equation, deterministic: 200 random meter states (beta, D, dp,
     p1, T1, gas, tap layout, an error on C) through model.mass_flow and
     engine.massFlow, with Z1 and kappa read from the SAME shipped table by
     both (build_app.quad and engine.quad), so any difference is the port.
     Must agree to 1e-12 relative (the plan review's finding 16).
  2. The table against the reference code it was built from: every fine-cell
     midpoint, Z to 1e-5 and kappa to 1e-4 relative (build_app.midpoint_error,
     recomputed here, not read from the build's output).
  3. The Monte Carlo: u(I) and the 95% interval of the default system's energy
     imbalance, JS against Python, each run to JCGM 101 7.9.4, must agree within
     the sum of their two numerical tolerances. Different random streams, so
     this is a statistical agreement, and the tolerance is the one each side
     reports for itself.

--break port   perturbs one RHG coefficient in the JS (0.0261 -> 0.0262), as a
               port that drifted would; part 1 must fail, and the run exits 1.

Run:  python tests/test_parity_meter.py [--break port]
"""
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
METER = os.path.join(os.path.dirname(HERE), "meter")
sys.path.insert(0, METER)

import numpy as np                       # noqa: E402

import model as M                        # noqa: E402
import build_app as B                    # noqa: E402
from aga8lib import AGA8                 # noqa: E402

BREAK = "--break" in sys.argv
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


NODE = r"""
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8');
if (process.argv[4] === 'break') {
  const n = src.split('0.0261 * beta').length - 1;
  if (n !== 1) { console.error('break did not find its target'); process.exit(3); }
  src = src.replace('0.0261 * beta', '0.0262 * beta');
}
const m = { exports: {} }; new Function('module', src)(m); const E = m.exports;
const job = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const tab = job.table;
const gas = Object.fromEntries(tab.gases.map(g => [g.name, g]));
const out = {};
out.det = job.states.map(s => {
  const g = gas[s.gas], Z1 = Math.exp(E.quad(g, g.lnZ1, s.T1, s.p1)), kap = E.quad(g, g.kappa, s.T1, s.p1);
  const [L1, L2] = E.tapsL(s.taps, s.D);
  return E.massFlow(s.beta * s.D, s.D, s.dp, s.p1, s.T1, g.MW, Z1, kap, L1, L2, s.cErr);
});
if (job.mc) {
  const g = gas['Gulf Coast'];
  const st = E.buildSystem(g, job.mc.meters);
  for (const s of st) s.J = E.gasAt(g, s.m.T1, s.m.p1).J;
  const rng = E.rngFrom(12345);
  const cs = E.comps({ C: 0.5 });
  const t0 = Date.now();
  const r = E.adaptive(K => E.simulate(st, g, cs, K, rng, 4, tab.z_ref), ['imb_e']);
  out.mc = Object.assign(r.imb_e, { seconds: (Date.now() - t0) / 1000 });
}
process.stdout.write(JSON.stringify(out));
"""


def table_states(table, n=200, seed=3):
    rng = np.random.default_rng(seed)
    gases = [g["name"] for g in table["gases"]]
    out = []
    for _ in range(n):
        D = float(rng.choice([0.0779, 0.1023, 0.1541, 0.2027, 0.3048]))
        beta = float(rng.uniform(0.2, 0.72))
        p1 = float(rng.uniform(150, 1400)) * M.PSI
        dp = float(rng.uniform(5, 100))
        out.append({"gas": str(rng.choice(gases)), "D": D, "beta": beta, "p1": p1,
                    "T1": float(rng.uniform(40, 120) - 32) / 1.8 + 273.15, "dp": min(dp, 0.2 * p1),
                    "taps": str(rng.choice(["flange", "corner", "D"])), "cErr": float(rng.normal(0, 0.003))})
    return out


def main():
    table = json.load(open(os.path.join(METER, "outputs", "app_table.json"), encoding="utf-8"))
    gas = {g["name"]: g for g in table["gases"]}
    states = table_states(table)
    meters = [dict(name=m.name, role=m.role, D=m.D, beta=m.beta, p1=m.p1, T1=m.T1, span_dp=m.span_dp,
                   dp=m.dp, share=m.share, taps=m.taps) for m in M.default_meters()]
    with tempfile.TemporaryDirectory() as td:
        js = os.path.join(td, "run.js")
        job = os.path.join(td, "job.json")
        open(js, "w", encoding="utf-8").write(NODE)
        json.dump({"table": table, "states": states, "mc": None if BREAK else {"meters": meters}},
                  open(job, "w", encoding="utf-8"))
        r = subprocess.run(["node", js, os.path.join(METER, "engine.js"), job, "break" if BREAK else ""],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-2000:])
            check("node ran the engine", False, f"exit {r.returncode}")
            return 1
        out = json.loads(r.stdout)

    # 1. deterministic
    worst = 0.0
    for s, js_q in zip(states, out["det"]):
        g = gas[s["gas"]]
        Z1 = math.exp(B.quad(g, "lnZ1", s["T1"], s["p1"]))
        kap = B.quad(g, "kappa", s["T1"], s["p1"])
        L1, L2 = M.taps_L(s["taps"], s["D"])
        py_q, _, _ = M.mass_flow(s["beta"] * s["D"], s["D"], s["dp"], s["p1"], s["T1"], g["MW"], Z1, kap,
                                 L1, L2, c_err=s["cErr"])
        worst = max(worst, abs(js_q / float(py_q) - 1))
    check("meter equation, JS vs Python, 200 states, same table", worst < 1e-12, f"worst relative {worst:.1e}")
    if BREAK:
        print(f"{len(fails)} failure(s)")
        return 1 if fails else 0

    # 2. table vs reference
    aga = AGA8()
    wz = wk = 0.0
    for g in table["gases"]:
        ez, ek = B.midpoint_error(aga, g)
        wz, wk = max(wz, ez), max(wk, ek)
    check("table vs NIST reference code at every fine-cell midpoint", wz < B.MID_TOL and wk < B.KAPPA_TOL,
          f"worst Z {wz:.1e} (bound {B.MID_TOL:g}), kappa {wk:.1e} (bound {B.KAPPA_TOL:g})")

    # 3. Monte Carlo
    st, x = M.build_system(M.default_meters(), aga=aga)
    rng = np.random.default_rng(12345)
    comps = M.default_comps({"C": 0.5})
    py = M.adaptive(lambda K: M.simulate(st, x, comps, K, rng), ["imb_e"])["imb_e"]
    js = out["mc"]
    for k in ("u", "low", "high"):
        tol = py["delta"] + js["delta"]
        check(f"Monte Carlo {k} of the energy imbalance, JS vs Python", abs(js[k] - py[k]) <= tol,
              f"JS {js[k]:.5e} ({js['batches']} batches, {js['seconds']:.0f} s) vs Python {py[k]:.5e}; "
              f"tolerance {tol:.1e}")
    print(f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
