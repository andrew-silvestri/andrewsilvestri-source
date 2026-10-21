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

  4. The app's opening state against the page's table (Q2). site/meter-app.html
     is loaded in Chromium untouched: the system it builds before anyone moves
     a control must be model.default_meters() field for field, its sharing
     controls must be the first row's (C independent, by tap and beta band,
     every other shared fraction 0), its gas, calibrations and price the
     payload's; then Run is pressed and its u(I) and throughput must agree
     with that row's within the two sides' own tolerances.

--break port     perturbs one RHG coefficient in the JS (0.0261 -> 0.0262), as a
                 port that drifted would; part 1 must fail, and the run exits 1.
--break opening  serves the app with its pre-Q2 opening state (its own controls'
                 system, the C slider at 0.50), which opened at 95 MMcf/d and
                 0.12% against the page's 101 and 0.18%; part 4 must fail, exit 1.

Run:  python tests/test_parity_meter.py [--break port|opening]
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

BREAK_MODE = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
if BREAK_MODE not in (None, "port", "opening"):
    sys.exit(f"unknown --break {BREAK_MODE}")
BREAK = BREAK_MODE == "port"
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
    opening()
    print(f"{len(fails)} failure(s)")
    return 1 if fails else 0


OPEN_JS = r"""
const pw = require('playwright');
(async () => {
  const b = await pw.chromium.launch();
  const page = await b.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('file:///' + process.argv[2].replace(/\\/g, '/'));
  const st = await page.evaluate(() => {
    // the meters as handed to the engine: buildSystem solves the deliveries' dp in place
    const orig = E.buildSystem; let seen = null;
    E.buildSystem = (g, ms) => { seen = JSON.parse(JSON.stringify(ms)); return orig(g, ms); };
    try { system(); } finally { E.buildSystem = orig; }
    const v = id => document.getElementById(id).value;
    return { meters: seen, C: +v('fC'), X: +v('fX'), G: +v('fG'), A: +v('fA'),
             cls: document.querySelector('input[name=cls]:checked').value, gas: v('gas'),
             ints: +v('ints'), price: v('price') };
  });
  await page.click('#go');
  await page.waitForFunction(() => window.__meterLast, null, { timeout: 600000 });
  st.run = await page.evaluate(() => window.__meterLast);
  st.shown = { u: await page.textContent('#o_u'), tp: await page.textContent('#o_tp') };
  process.stdout.write(JSON.stringify(st));
  await b.close();
})().catch(e => { console.error(e); process.exit(2); });
"""


def opening():
    root = os.path.dirname(HERE)
    app = os.path.join(root, "site", "meter-app.html")
    pay = json.load(open(os.path.join(METER, "outputs", "payload.json"), encoding="utf-8"))
    row = pay["system"]["fC0"]["results"]["imb_e"]
    with tempfile.TemporaryDirectory() as td:
        if BREAK_MODE == "opening":
            src = open(app, encoding="utf-8").read()
            for o, n in (('name="sys" value="page" checked>', 'name="sys" value="page">'),
                         ('name="sys" value="own">', 'name="sys" value="own" checked>'),
                         ('id="fC" min="0" max="1" step="0.05" value="0"', 'id="fC" min="0" max="1" step="0.05" value="0.5"')):
                if src.count(o) != 1:
                    check("break found its target", False, o)
                    return
                src = src.replace(o, n)
            app = os.path.join(td, "meter-app.html")
            open(app, "w", encoding="utf-8", newline="\n").write(src)
        js = os.path.join(td, "open.js")
        open(js, "w", encoding="utf-8").write(OPEN_JS)
        env = dict(os.environ, NODE_PATH=os.path.join(HERE, "node_modules"))
        r = subprocess.run(["node", js, app], capture_output=True, text=True, env=env)
    if r.returncode != 0:
        check("the app opened and ran in Chromium", False, f"exit {r.returncode}: {r.stderr[-500:]}")
        return
    o = json.loads(r.stdout)
    want = [dict(name=m.name, role=m.role, D=m.D, beta=m.beta, p1=m.p1, T1=m.T1, span_dp=m.span_dp,
                 dp=m.dp, share=m.share, taps=m.taps) for m in M.default_meters()]
    got = [{k: m.get(k) for k in want[0]} for m in o["meters"]]
    eq = lambda a, b: (abs(a - b) <= 1e-12 * max(1, abs(b))) if isinstance(b, float) else a == b  # noqa: E731
    diff = [(w["name"], k, g[k], w[k]) for g, w in zip(got, want) for k in w if not eq(g[k], w[k])]
    same = len(got) == len(want) and not diff
    check("app opens on the page's system (model.default_meters, field for field)", same,
          f"{len(got)} meters vs {len(want)}; {len(diff)} field(s) differ" + (f", first {diff[0]}" if diff else ""))
    from update_page import cents
    ctl = (o["C"], o["cls"], o["X"], o["G"], o["A"], o["gas"], o["ints"], o["price"])
    exp = (0.0, "beta", 0.0, 0.0, 0.0, pay["gas"], pay["intervals"], cents(pay["price"]["median"]))
    check("app opens on the table's first row (C independent; nothing else shared) and the payload's gas, "
          "calibrations and price", ctl == exp, f"{ctl} vs {exp}")
    run = o["run"]
    tol = run["delta"] + row["delta"]
    check("app's u(I) at opening = the page's first row", abs(run["u"] - row["u"]) <= tol,
          f"app {run['u']:.5e} (shown {o['shown']['u']}) vs page {row['u']:.5e}; tolerance {tol:.1e}")
    tp = pay["throughput"]["mmcfd"]
    check("app's throughput at opening = the page's", abs(run["mmcfd"] - tp) <= 1e-9 * tp,
          f"app {run['mmcfd']:.6f} (shown {o['shown']['tp']}) vs page {tp:.6f} MMcf/d")


if __name__ == "__main__":
    sys.exit(main())
