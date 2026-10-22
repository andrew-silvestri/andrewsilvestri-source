/* The lost-gas simulator's engine: model.py's from_draws() in JavaScript, and the draws and
 * quantiles the app needs around it. tests/test_parity_lauf.py feeds this and model.py identical
 * draws and holds them to 1e-12; the app draws its own normals (mulberry32 + Box-Muller), so its
 * figures are a fresh Monte Carlo sample, not the payload's, and agree with it to sampling error.
 */
(function (root) {
  'use strict';
  const T_BASE_F = 60.0;
  const DRAWS = [['cg_p', 1], ['cg_t', 2], ['fleet', 1], ['drift', 1], ['scatter', 2], ['temp', 2], ['timing', 2]];

  function kelvin(f) { return (f - 32.0) / 1.8 + 273.15; }

  // relative misstatement of delivered standard volume by an uncompensated meter, %
  function tempBiasPct(gasTempF) { return 100.0 * (kelvin(gasTempF) / kelvin(T_BASE_F) - 1.0); }

  // z: {name: [row0, row1?]} with Float64Array rows of length n. Returns [y1, y2], LAUF in %.
  function fromDraws(p, z) {
    const n = z.cg_p[0].length;
    const cgVar = p.cg_u * p.cg_u;
    const sP = Math.sqrt(cgVar * p.cg_persist), sT = Math.sqrt(cgVar * (1 - p.cg_persist));
    const sScatter = p.meter_sd / Math.sqrt(p.n_meters);
    const out = [new Float64Array(n), new Float64Array(n)];
    for (let i = 0; i < n; i++) {
      const cgP = z.cg_p[0][i] * sP, fleet = z.fleet[0][i] * p.fleet_mean_sd, drift = z.drift[0][i] * p.fleet_drift;
      for (let y = 0; y < 2; y++) {
        const eIn = cgP + z.cg_t[y][i] * sT;
        const tb = p.uncomp_share * tempBiasPct(p.gas_temp_f + z.temp[y][i] * p.gas_temp_sd_f);
        const eOut = fleet + (y === 1 ? drift : 0.0) + z.scatter[y][i] * sScatter + tb + z.timing[y][i] * p.timing_sd;
        out[y][i] = 100.0 * ((1 + eIn / 100.0) / (1 + eOut / 100.0) - 1.0);
      }
    }
    return out;
  }

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function draws(n, seed) {
    const u = mulberry32(seed);
    const normal = () => {                       // Box-Muller; 1 - u keeps log() away from 0
      const a = 1 - u(), b = u();
      return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b);
    };
    const z = {};
    for (const [k, rows] of DRAWS) {
      z[k] = [];
      for (let r = 0; r < rows; r++) { const a = new Float64Array(n); for (let i = 0; i < n; i++) a[i] = normal(); z[k].push(a); }
    }
    return z;
  }

  // numpy.percentile's default (linear) method, so the app's quantiles read like the payload's
  function percentile(sorted, q) {
    const h = (sorted.length - 1) * q / 100, lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo);
  }

  function summary(p, n, seed) {
    const [y1, y2] = fromDraws(p, draws(n, seed));
    const ch = new Float64Array(n);
    for (let i = 0; i < n; i++) ch[i] = y2[i] - y1[i];
    const lv = Float64Array.from(y1).sort(), cs = Float64Array.from(ch).sort();
    const q = {};
    for (const k of [10, 25, 50, 75, 90]) q['p' + k] = [percentile(lv, k), percentile(cs, k)];
    return {
      level: Object.fromEntries(Object.entries(q).map(([k, v]) => [k, v[0]])),
      change: Object.fromEntries(Object.entries(q).map(([k, v]) => [k, v[1]])),
    };
  }

  const api = { T_BASE_F, DRAWS, tempBiasPct, fromDraws, draws, percentile, summary };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LaufEngine = api;
})(typeof window !== 'undefined' ? window : this);
