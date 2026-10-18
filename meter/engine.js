// The meter model in the browser: a port of meter/model.py's meter equation,
// error model and JCGM 101 7.9.4 Monte Carlo. GERG-2008 is not ported; Z1,
// kappa and the composition Jacobian come from a table build_app.py writes
// from the NIST reference code per example gas: Z1 and kappa on a fine (T, p)
// grid read by biquadratic interpolation, the Jacobian on a coarse one read
// bilinearly (Python reads the same table for the parity test,
// tests/test_parity_meter.py). Loaded by node for that test and inlined into
// site/meter-app.html by build_app.py.
(function (root) {
  "use strict";
  const PSI = 6.894757293168361, R_GERG = 8.314472;
  const P_BASE = 14.73 * PSI, T_BASE = (60 - 32) / 1.8 + 273.15;
  const MU = 1.1e-5, SQ3 = Math.sqrt(3);
  // model.py's constants, same names
  const K = {
    DP_REF: 0.0004, DP_AMB_SPAN: 0.0004, DP_AMB_URL: 0.00009, DP_URL: 100.0, DP_STATIC: 0.00075,
    P_REF: 0.0004, T_SENSOR: [0.15, 0.002], T_XMTR: 0.12, T_INSTALL: 0.5,
    D_BORE: 0.0005, D_PIPE: 0.0025, Z_U_REF: 0.0005,
  };

  function cdU(beta) { return (beta <= 0.6 ? 0.005 : (1.667 * beta - 0.5) / 100) / 2; }

  function rhg(beta, D, Re, L1, L2) {
    const A = Math.pow(19000 * beta / Re, 0.8);
    const M2 = 2 * L2 / (1 - beta);
    const b4 = Math.pow(beta, 4);
    let C = 0.5961 + 0.0261 * beta * beta - 0.216 * b4 * b4
      + 0.000521 * Math.pow(1e6 * beta / Re, 0.7)
      + (0.0188 + 0.0063 * A) * Math.pow(beta, 3.5) * Math.pow(1e6 / Re, 0.3)
      + (0.043 + 0.080 * Math.exp(-10 * L1) - 0.123 * Math.exp(-7 * L1)) * (1 - 0.11 * A) * b4 / (1 - b4)
      - 0.031 * (M2 - 0.8 * Math.pow(M2, 1.1)) * Math.pow(beta, 1.3);
    if (D < 0.07112) C += 0.011 * (0.75 - beta) * (2.8 - D / 0.0254);
    return C;
  }

  function tapsL(taps, D) {
    if (taps === "flange") return [0.0254 / D, 0.0254 / D];
    if (taps === "corner") return [0, 0];
    if (taps === "D") return [1, 0.47];
    throw new Error(taps);
  }

  // model.mass_flow, one meter: kg/s. d, D m; dp, p1 kPa; T1 K; MW g/mol.
  function massFlow(d, D, dp, p1, T1, MW, Z1, kappa, L1, L2, cErr, mu) {
    mu = mu || MU; cErr = cErr || 0;
    const beta = d / D;
    const rho1 = p1 * 1e3 * MW * 1e-3 / (Z1 * R_GERG * T1);
    const eps = 1 - (0.351 + 0.256 * Math.pow(beta, 4) + 0.93 * Math.pow(beta, 8)) * (1 - Math.pow((p1 - dp) / p1, 1 / kappa));
    const k = (Math.PI / 4) * d * d * eps * Math.sqrt(2 * rho1 * dp * 1e3) / Math.sqrt(1 - Math.pow(beta, 4));
    let C = 0.6;
    for (let i = 0; i < 60; i++) {
      const Re = 4 * C * k / (Math.PI * D * mu);
      const Cn = rhg(beta, D, Re, L1, L2) * (1 + cErr);
      if (Math.abs(Cn / C - 1) < 1e-13) { C = Cn; return C * k; }
      C = Cn;
    }
    throw new Error("C / Re_D did not converge");
  }

  // ---- the gas table --------------------------------------------------------
  // gas = {Tf, pf: the fine grid (K, kPa) for lnZ1 and kappa; T, p: the coarse grid for JZ1[c],
  //        the d ln Z1 / d e_c table per component; Zb, MW, HN; Jb [4][21] (rows MW, -, Zb, HN)}
  function bilinear(g, grid, T, p) {
    const { i, j, u, v } = cell(g, T, p);
    const a = grid[i][j], b = grid[i + 1][j], c = grid[i][j + 1], d = grid[i + 1][j + 1];
    return (1 - u) * (1 - v) * a + u * (1 - v) * b + (1 - u) * v * c + u * v * d;
  }
  function cell(g, T, p) {
    const i = Math.min(Math.max(0, search(g.T, T)), g.T.length - 2);
    const j = Math.min(Math.max(0, search(g.p, p)), g.p.length - 2);
    const u = (T - g.T[i]) / (g.T[i + 1] - g.T[i]), v = (p - g.p[j]) / (g.p[j + 1] - g.p[j]);
    if (u < -1e-9 || u > 1 + 1e-9 || v < -1e-9 || v > 1 + 1e-9) throw new Error("outside the gas table");
    return { i, j, u, v };
  }
  function search(xs, x) { let i = 0; while (i < xs.length - 2 && x > xs[i + 1]) i++; return i; }
  // biquadratic (three-point Lagrange) on the fine grid: build_app.quad(), same arithmetic
  function lag(xs, i, t) {
    const a = xs[i - 1], b = xs[i], c = xs[i + 1];
    return [(t - b) * (t - c) / ((a - b) * (a - c)), (t - a) * (t - c) / ((b - a) * (b - c)),
            (t - a) * (t - b) / ((c - a) * (c - b))];
  }
  function nearest(xs, t) {
    let k = 0; for (let q = 1; q < xs.length; q++) if (Math.abs(xs[q] - t) < Math.abs(xs[k] - t)) k = q;
    return Math.min(Math.max(k, 1), xs.length - 2);
  }
  function quad(g, grid, T, p) {
    const Ts = g.Tf, Ps = g.pf;
    if (T < Ts[0] || T > Ts[Ts.length - 1] || p < Ps[0] || p > Ps[Ps.length - 1]) throw new Error("outside the gas table");
    const i = nearest(Ts, T), j = nearest(Ps, p), wt = lag(Ts, i, T), wp = lag(Ps, j, p);
    let s = 0;
    for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) s += wt[a] * wp[b] * grid[i - 1 + a][j - 1 + b];
    return s;
  }

  function gasAt(g, T, p) {
    const J = [g.Jb[0].slice(), new Array(21).fill(0), g.Jb[2].slice(), g.Jb[3].slice()];
    for (let c = 0; c < 21; c++) {
      if (g.JZ1[c]) J[1][c] = bilinear(g, g.JZ1[c], T, p);
    }
    return { Z1: Math.exp(quad(g, g.lnZ1, T, p)), kappa: quad(g, g.kappa, T, p),
             Zb: g.Zb, MW: g.MW, HN: g.HN, J };
  }

  // ---- system --------------------------------------------------------------
  function state(g, m, dp) {
    const s = gasAt(g, m.T1, m.p1);
    const [L1, L2] = tapsL(m.taps || "flange", m.D);
    const qm = massFlow(m.beta * m.D, m.D, dp, m.p1, m.T1, s.MW, s.Z1, s.kappa, L1, L2, 0);
    return Object.assign(s, { m: Object.assign({}, m, { dp }), qm, L1, L2 });
  }

  function solveDp(g, m, target) {
    const mol = dp => state(g, m, dp).qm / (g.MW * 1e-3);
    let a = 0.1 * m.span_dp, b = 0.9 * m.span_dp, fa = mol(a) - target, fb = mol(b) - target;
    for (let i = 0; i < 100; i++) {
      const c = b - fb * (b - a) / (fb - fa), fc = mol(c) - target;
      if (Math.abs(fc) < 1e-14 * target) return c;
      a = b; fa = fb; b = c; fb = fc;
    }
    throw new Error(m.name + ": dp did not converge");
  }

  function buildSystem(g, meters) {
    const st = [];
    let total = 0;
    for (const m of meters) if (m.role === "R") {
      const s = state(g, m, m.dp); st.push(s); total += s.qm / (s.MW * 1e-3);
    }
    const shares = meters.filter(m => m.role === "D").reduce((a, m) => a + m.share, 0);
    for (const m of meters) if (m.role === "D") st.push(state(g, m, solveDp(g, m, total * m.share / shares)));
    for (const s of st) {
      const m = s.m;
      if (!(m.dp / m.span_dp >= 0.1 - 1e-9 && m.dp / m.span_dp <= 1 && m.dp / m.p1 <= 0.25))
        throw new Error(m.name + ": dp " + m.dp.toFixed(2) + " kPa is outside 10-100% of its span");
    }
    return st;
  }

  // ---- random numbers: xoshiro128**, seeded; normal by Box-Muller ----------
  function rngFrom(seed) {
    let a = seed >>> 0, b = 0x9e3779b9, c = 0x243f6a88, d = 0xb7e15162;
    function next() {
      const r = Math.imul(rotl(Math.imul(b, 5), 7), 9) >>> 0;
      const t = b << 9; c ^= a; d ^= b; b ^= c; a ^= d; c ^= t; d = rotl(d, 11);
      return r / 4294967296;
    }
    function rotl(x, k) { return (x << k) | (x >>> (32 - k)); }
    for (let i = 0; i < 20; i++) next();
    let spare = null;
    return {
      uniform: next,
      normal() {
        if (spare !== null) { const s = spare; spare = null; return s; }
        let u = 0; while (u === 0) u = next();
        const v = next(), r = Math.sqrt(-2 * Math.log(u));
        spare = r * Math.sin(2 * Math.PI * v); return r * Math.cos(2 * Math.PI * v);
      },
    };
  }
  function unit(rng, dist) { return dist === "normal" ? rng.normal() : (rng.uniform() * 2 - 1) * SQ3; }

  // model.default_comps, with the same names and semantics
  function comps(f, cClass) {
    f = f || {}; const g = (k, d) => (k in f ? f[k] : d);
    return [
      ["dp reference", "dp", "dp_kpa", "rect", g("dp", 0), "interval"],
      ["dp ambient", "dp", "dp_kpa", "rect", g("dp", 0), "interval"],
      ["dp static span", "dp", "dp_gain", "rect", g("dp", 0), "interval"],
      ["p reference", "p1", "p_kpa", "rect", g("p1", 0), "interval"],
      ["T sensor", "T1", "T_K", "rect", g("T1", 0), "interval"],
      ["T transmitter", "T1", "T_K", "rect", g("T1", 0), "interval"],
      ["T installation", "T1", "T_K", "rect", g("T1", 0), "interval"],
      ["C", "C", "rel_C", "normal", g("C", 0), "period", true, cClass || "beta"],
      ["bore d", "d", "rel_d", "rect", g("d", 0), "period"],
      ["pipe D", "D", "rel_D", "rect", g("D", 0), "period"],
      ["composition", "composition", "comp", "normal", g("composition", 0), "interval"],
      ["Z equation", "Z", "zeq", "normal", 1, "period"],
    ].map(a => ({ name: a[0], group: a[1], kind: a[2], dist: a[3], f: a[4], redraw: a[5],
                  byClass: !!a[6], classKey: a[7] || "beta" }));
  }

  function scaleOf(c, s) {
    const m = s.m;
    switch (c.name) {
      case "dp reference": return K.DP_REF * m.span_dp / SQ3;
      case "dp ambient": return (K.DP_AMB_SPAN * m.span_dp + K.DP_AMB_URL * K.DP_URL) / SQ3;
      case "dp static span": return K.DP_STATIC * (m.p1 / (1000 * PSI)) / SQ3;
      case "p reference": return K.P_REF * 1.5 * m.p1 / SQ3;
      case "T sensor": return (K.T_SENSOR[0] + K.T_SENSOR[1] * Math.abs(m.T1 - 273.15)) / SQ3;
      case "T transmitter": return K.T_XMTR / SQ3;
      case "T installation": return K.T_INSTALL / SQ3;
      case "C": return cdU(m.beta);
      case "bore d": return K.D_BORE / SQ3;
      case "pipe D": return K.D_PIPE / SQ3;
      default: return 1;
    }
  }
  function classOf(s, key) {
    return key === "role" ? s.m.role : (s.m.taps || "flange") + ":" + Math.floor(s.m.beta * 10 + 1e-9);
  }

  // model.simulate: K trials, `intervals` calibration intervals per period.
  // Returns Float64Arrays imb_v, imb_e, rec_v (relative to true throughput).
  function simulate(states, gas, cs, Kn, rng, intervals, zRef) {
    intervals = intervals || 4;
    const n = states.length, T = intervals;
    const role = states.map(s => (s.m.role === "R" ? 1 : -1));
    const nTrue = states.map(s => s.qm / (s.MW * 1e-3));
    const vbTrue = states.map((s, i) => nTrue[i] * s.Zb * R_GERG * T_BASE / (P_BASE * 1e3));
    const eTrue = states.map((s, i) => nTrue[i] * s.HN * 1e3);
    let thV = 0, thE = 0;
    for (let i = 0; i < n; i++) if (role[i] > 0) { thV += vbTrue[i]; thE += eTrue[i]; }
    const a = K.Z_U_REF / (1 - zRef);
    const compU = gas.compU;                   // relative standard uncertainty per NIST component
    const out = { imb_v: new Float64Array(Kn), imb_e: new Float64Array(Kn), rec_v: new Float64Array(Kn) };
    const classes = {};
    for (const c of cs) if (c.byClass) {
      const keys = states.map(s => classOf(s, c.classKey));
      const uniq = [...new Set(keys)].sort();
      classes[c.name] = keys.map(k => uniq.indexOf(k)); classes[c.name].n = uniq.length;
    }
    const scales = cs.map(c => states.map(s => scaleOf(c, s)));
    // per-trial work arrays
    const e = { dp: new Float64Array(n), gain: new Float64Array(n), p1: new Float64Array(n), T1: new Float64Array(n),
                C: new Float64Array(n), d: new Float64Array(n), D: new Float64Array(n) };
    const dln = [0, 1, 2, 3].map(() => new Float64Array(n));
    const held = cs.map(() => null);
    for (let k = 0; k < Kn; k++) {
      let sv = 0, se = 0, sr = 0;
      // period-held components: draw once per trial
      for (let ci = 0; ci < cs.length; ci++) {
        const c = cs[ci];
        if (c.redraw === "period") held[ci] = draw(c, ci);
      }
      for (let t = 0; t < T; t++) {
        for (const key in e) e[key].fill(0);
        for (const r of dln) r.fill(0);
        for (let ci = 0; ci < cs.length; ci++) {
          const c = cs[ci];
          const u = c.redraw === "period" ? held[ci] : draw(c, ci);
          apply(c, ci, u);
        }
        let v = 0, en = 0, rv = 0;
        for (let i = 0; i < n; i++) {
          const s = states[i], m = s.m;
          const qm = massFlow(m.beta * m.D * (1 + e.d[i]), m.D * (1 + e.D[i]), m.dp * (1 + e.dp[i] + e.gain[i]),
            m.p1 * (1 + e.p1[i]), m.T1 * (1 + e.T1[i]), s.MW * Math.exp(dln[0][i]), s.Z1 * Math.exp(dln[1][i]),
            s.kappa, s.L1, s.L2, e.C[i]);
          const nm = qm / (s.MW * Math.exp(dln[0][i]) * 1e-3);
          const vb = nm * s.Zb * Math.exp(dln[2][i]) * R_GERG * T_BASE / (P_BASE * 1e3);
          const en_ = nm * s.HN * Math.exp(dln[3][i]) * 1e3;
          v += role[i] * vb; en += role[i] * en_; if (role[i] > 0) rv += vb;
        }
        sv += v; se += en; sr += rv;
      }
      out.imb_v[k] = sv / T / thV; out.imb_e[k] = se / T / thE; out.rec_v[k] = sr / T / thV - 1;
    }
    return out;

    function draw(c, ci) {
      // unit draws with sharing; for composition one per (component, meter)
      if (c.kind === "comp") {
        const z = new Float64Array(21), u = [];
        for (let j = 0; j < 21; j++) z[j] = unit(rng, c.dist);
        for (let i = 0; i < n; i++) {
          const row = new Float64Array(21);
          for (let j = 0; j < 21; j++) row[j] = Math.sqrt(c.f) * z[j] + Math.sqrt(1 - c.f) * unit(rng, c.dist);
          u.push(row);
        }
        return u;
      }
      let zs;
      if (c.byClass) { const cl = classes[c.name]; zs = []; for (let q = 0; q < cl.n; q++) zs.push(unit(rng, c.dist)); }
      else zs = [unit(rng, c.dist)];
      const u = new Float64Array(n);
      for (let i = 0; i < n; i++) {
        const z = c.byClass ? zs[classes[c.name][i]] : zs[0];
        u[i] = Math.sqrt(c.f) * z + Math.sqrt(1 - c.f) * unit(rng, c.dist);
      }
      return u;
    }
    function apply(c, ci, u) {
      if (c.kind === "comp") {
        for (let i = 0; i < n; i++) {
          const J = states[i].J;
          for (let j = 0; j < 21; j++) {
            if (!compU[j] || !gas.x[j]) continue;
            const w = u[i][j] * compU[j];
            for (let r = 0; r < 4; r++) dln[r][i] += w * J[r][j];
          }
        }
        return;
      }
      if (c.kind === "zeq") {
        for (let i = 0; i < n; i++) {
          dln[1][i] += u[i] * a * (1 - states[i].Z1); dln[2][i] += u[i] * a * (1 - states[i].Zb);
        }
        return;
      }
      const sc = scales[ci];
      for (let i = 0; i < n; i++) {
        const m = states[i].m, w = u[i] * sc[i];
        switch (c.kind) {
          case "dp_kpa": e.dp[i] += w / m.dp; break;
          case "dp_gain": e.gain[i] += w; break;
          case "p_kpa": e.p1[i] += w / m.p1; break;
          case "T_K": e.T1[i] += w / m.T1; break;
          case "rel_C": e.C[i] += w; break;
          case "rel_d": e.d[i] += w; break;
          case "rel_D": e.D[i] += w; break;
        }
      }
    }
  }

  // ---- JCGM 101 7.9.2 and 7.9.4 --------------------------------------------
  function tolerance(u, ndig) {
    ndig = ndig || 2;
    if (u === 0) return 0;
    const ex = Math.floor(Math.log10(Math.abs(u)));
    const r = Math.round(Math.abs(u) / Math.pow(10, ex - (ndig - 1))) * Math.pow(10, ex - (ndig - 1));
    const l = Math.floor(Math.log10(r)) - (ndig - 1);
    return 0.5 * Math.pow(10, l);
  }
  function quantile(sorted, q) {          // numpy's default (linear) definition
    const h = (sorted.length - 1) * q, lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
  }
  function summarise(y, p) {
    p = p || 0.95;
    let m = 0; for (const v of y) m += v; m /= y.length;
    let s = 0; for (const v of y) s += (v - m) * (v - m);
    const sorted = Float64Array.from(y).sort();
    return { mean: m, u: Math.sqrt(s / (y.length - 1)), low: quantile(sorted, (1 - p) / 2), high: quantile(sorted, (1 + p) / 2) };
  }
  function adaptive(runBatch, keys, opts) {
    opts = opts || {};
    const p = opts.p || 0.95, ndig = opts.ndig || 2, Kb = opts.K || Math.max(Math.ceil(100 / (1 - p)), 10000);
    const maxB = opts.maxBatches || 400, minB = opts.minBatches || 5;
    const batches = {}, pooled = {};
    for (const k of keys) { batches[k] = []; pooled[k] = []; }
    let h;
    for (h = 1; h <= maxB; h++) {
      const out = runBatch(Kb);
      for (const k of keys) { batches[k].push(summarise(out[k], p)); pooled[k].push(out[k]); }
      if (h < Math.max(2, minB)) continue;
      let done = true;
      for (const k of keys) {
        const all = concat(pooled[k]);
        const delta = tolerance(summarise(all, p).u, ndig);
        for (const stat of ["mean", "u", "low", "high"]) {
          const v = batches[k].map(b => b[stat]);
          const mv = v.reduce((a, b) => a + b, 0) / h;
          const s = Math.sqrt(v.reduce((a, b) => a + (b - mv) * (b - mv), 0) / (h * (h - 1)));
          if (2 * s >= delta) done = false;
        }
      }
      if (done) break;
      if (opts.onBatch) opts.onBatch(h);
    }
    if (h > maxB) h = maxB;
    const res = {};
    for (const k of keys) {
      const all = concat(pooled[k]);
      const r = summarise(all, p);
      r.delta = tolerance(r.u, ndig); r.trials = all.length; r.batches = h; r.stable = h < maxB;
      res[k] = r;
    }
    return res;
  }
  function concat(arrs) {
    let n = 0; for (const a of arrs) n += a.length;
    const o = new Float64Array(n); let i = 0; for (const a of arrs) { o.set(a, i); i += a.length; } return o;
  }

  const api = { quad, bilinear, PSI, T_BASE, P_BASE, R_GERG, MU, K, cdU, rhg, tapsL, massFlow, gasAt, state, solveDp,
                buildSystem, rngFrom, comps, simulate, tolerance, summarise, adaptive };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.MeterEngine = api;
})(this);
