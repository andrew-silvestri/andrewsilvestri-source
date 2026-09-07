/* What the home page's hero claims, recomputed.
 *
 *   node tests/verify_hero_systems.js
 *   node tests/verify_hero_systems.js --break     # trap 17: the mutations
 *
 * assets/hero.js draws one of three named systems and captions it with the
 * system's parameters and its behaviour. Two of those captions make claims
 * that are not true by construction, and this file is where they are checked:
 *
 *   A. The three-body caption names an outcome - which two masses pair off and
 *      which is thrown clear. Burrau's problem is chaotic and the hero softens
 *      it (eps, below) so a fixed step cannot break on a close pass. A softened
 *      chaotic system need not resolve the way the published one does, so the
 *      caption may not repeat Szebehely & Peters 1967 on trust: it has to say
 *      what THIS integrator does, and this is what runs it. (HANDOFF section 8,
 *      trap 12: when a number makes the page's point unusually well, recompute
 *      it before admiring it.)
 *
 *   B. The pendulum caption says "real time" and the hero asserts an energy
 *      bound. RK4 is not symplectic, so its energy error is secular - it
 *      accumulates roughly linearly rather than bounding itself, and a short
 *      burst measures nothing. The bound in hero.js comes from the 8-hour run
 *      here, not from a guess.
 *
 *   C. The pendulum caption says "released 0.001 rad apart", and the whole
 *      reason there are three of them is that they diverge. That is a claim
 *      about behaviour, so it is checked rather than assumed: they must start
 *      together, still be together after a few seconds, and be visibly apart
 *      by half a minute. Without this the hero could ship three pendulums
 *      that stayed in lockstep - because someone seeded them identically, or
 *      stepped one state vector three times - and the page would quietly say
 *      something false while looking fine.
 *
 * The integrators are deliberately a second implementation of the ones in
 * assets/hero.js rather than an import: a check that runs the same code that
 * produced the answer is provenance, not verification (trap 20). The constants
 * are shared by being written down in both places and compared by eye when
 * either moves - which is what CONSTANTS below exists to make cheap.
 */

'use strict';

/* ---- the constants hero.js must agree with --------------------------- */
const CONSTANTS = {
  pendulum: { m1: 1, m2: 1, l1: 1, l2: 1, g: 9.81, th1: 2.0, th2: 2.0, h: 0.001 },
  pendulumTrio: [2.000, 2.001, 2.002],   // hero.js Pendulum(): TH
  threebody: {
    m: [3, 4, 5],
    r: [[1, 3], [-2, -1], [1, -1]],
    tol: 1e-11,
    eps: 1e-6,
    G: 1
  }
};

/* ==== A. Burrau's problem ============================================== */

/* Plummer-softened Newtonian acceleration, G = 1.
   The softening is why this file exists: eps enters as (r^2 + eps^2)^(3/2),
   so it is a real change to the force law at small separations and not a
   numerical detail. */
function accel(m, r, eps2, out) {
  for (let i = 0; i < 3; i++) { out[i][0] = 0; out[i][1] = 0; }
  for (let i = 0; i < 3; i++) {
    for (let j = i + 1; j < 3; j++) {
      const dx = r[j][0] - r[i][0], dy = r[j][1] - r[i][1];
      const d2 = dx * dx + dy * dy + eps2;
      const inv = 1 / (d2 * Math.sqrt(d2));
      out[i][0] += m[j] * dx * inv; out[i][1] += m[j] * dy * inv;
      out[j][0] -= m[i] * dx * inv; out[j][1] -= m[i] * dy * inv;
    }
  }
}

function copy2(a) { return a.map(v => [v[0], v[1]]); }

/* Adaptive Cash-Karp RK45 on the flat 12-vector [x,y,vx,vy] x 3.
 *
 * A FIXED STEP CANNOT DO THIS PROBLEM, and that is a measured result, not a
 * preference. Burrau's closest approach here is ~4e-4, where the dynamical
 * time sqrt(r^3/GM) is ~2.5e-6 - so a fixed h = 1e-6 is nearly half a
 * dynamical time, the encounter is unresolved, and the run ends with a
 * relative energy drift of 1.8e+1: the bodies are flung wherever the
 * truncation error puts them. Resolving it at fixed step needs h ~ 1e-8, i.e.
 * ~500,000 steps a frame, which the hero cannot afford. The first draft's
 * eps = 1e-3 avoided the problem only by softening the encounters out of
 * existence, which is a different system wearing Burrau's name.
 *
 * Adaptive stepping is both more correct AND cheaper: long steps between
 * encounters, short ones through them. Determinism is unaffected - same
 * initial conditions and same tolerance give the same trajectory - which is
 * what the hero's reproducibility argument actually needs. It is the fixed
 * STEP that goes, not the fixed rate; the accumulator still governs how much
 * system time a frame may advance. */
const CK = {
  a:  [0, 1/5, 3/10, 3/5, 1, 7/8],
  b:  [[], [1/5], [3/40, 9/40], [3/10, -9/10, 6/5],
       [-11/54, 5/2, -70/27, 35/27],
       [1631/55296, 175/512, 575/13824, 44275/110592, 253/4096]],
  c:  [37/378, 0, 250/621, 125/594, 0, 512/1771],
  dc: [37/378 - 2825/27648, 0, 250/621 - 18575/48384,
       125/594 - 13525/55296, -277/14336, 512/1771 - 1/4]
};

function deriv(m, y, eps2, out) {
  for (let i = 0; i < 3; i++) { out[4*i] = y[4*i+2]; out[4*i+1] = y[4*i+3]; out[4*i+2] = 0; out[4*i+3] = 0; }
  for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++) {
    const dx = y[4*j] - y[4*i], dy = y[4*j+1] - y[4*i+1];
    const d2 = dx*dx + dy*dy + eps2;
    const inv = 1 / (d2 * Math.sqrt(d2));
    out[4*i+2] += m[j]*dx*inv; out[4*i+3] += m[j]*dy*inv;
    out[4*j+2] -= m[i]*dx*inv; out[4*j+3] -= m[i]*dy*inv;
  }
}

/* one trial step; returns the max scaled error. y5 gets the 5th-order result. */
function ckStep(m, y, h, eps2, W) {
  const { k, yt, y5 } = W;
  for (let st = 0; st < 6; st++) {
    if (st === 0) { for (let i = 0; i < 12; i++) yt[i] = y[i]; }
    else {
      for (let i = 0; i < 12; i++) {
        let a = 0;
        for (let q = 0; q < st; q++) a += CK.b[st][q] * k[q][i];
        yt[i] = y[i] + h * a;
      }
    }
    deriv(m, yt, eps2, k[st]);
  }
  let err = 0;
  for (let i = 0; i < 12; i++) {
    let s5 = 0, se = 0;
    for (let q = 0; q < 6; q++) { s5 += CK.c[q] * k[q][i]; se += CK.dc[q] * k[q][i]; }
    y5[i] = y[i] + h * s5;
    const scale = Math.abs(y[i]) + Math.abs(h * k[0][i]) + 1e-30;
    err = Math.max(err, Math.abs(h * se) / scale);
  }
  return err;
}

/* advance by dtWant, adapting internally. Returns steps taken. */
function advance(m, y, dtWant, eps2, W, tol, state) {
  let done = 0, n = 0;
  let h = state.h;
  while (done < dtWant) {
    if (h > dtWant - done) h = dtWant - done;
    const err = ckStep(m, y, h, eps2, W);
    n++;
    if (err > tol && h > 1e-13) { h *= Math.max(0.1, 0.9 * Math.pow(tol / err, 0.25)); continue; }
    for (let i = 0; i < 12; i++) y[i] = W.y5[i];
    done += h;
    h *= Math.min(5, 0.9 * Math.pow(tol / Math.max(err, 1e-18), 0.2));
    if (h > 0.05) h = 0.05;
  }
  state.h = h;
  return n;
}

function workspace() {
  const k = []; for (let q = 0; q < 6; q++) k.push(new Float64Array(12));
  return { k, yt: new Float64Array(12), y5: new Float64Array(12) };
}

function energy3(m, y, eps2) {
  let E = 0;
  for (let i = 0; i < 3; i++) E += 0.5 * m[i] * (y[4*i+2] ** 2 + y[4*i+3] ** 2);
  for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++) {
    const dx = y[4*j] - y[4*i], dy = y[4*j+1] - y[4*i+1];
    E -= m[i] * m[j] / Math.sqrt(dx * dx + dy * dy + eps2);
  }
  return E;
}

/* The escape test hero.js uses, written once here so both can be compared.
 * Generic over the three bodies on purpose: the published answer is that the
 * mass-5 body goes, but a softened system may eject a different one, and a
 * test hard-coded to body 3 would never notice.
 *
 * THE "d > 4 x |r_j - r_k|" FORM DOES NOT WORK, and this comment is here so
 * nobody reinvents it. Scaling the threshold by the other two bodies' CURRENT
 * separation inverts during exactly the events that define this problem: at a
 * close pass the pair closes to ~1e-2, so the threshold falls to ~5e-2 and the
 * third body trivially clears it. On Burrau it fired at t = 3.7 - during the
 * first collapse, some fifteen times too early - and named the wrong body.
 *
 * What replaces it is the standard criterion, which is about binding energy
 * rather than about distance:
 *
 *   d       - body i's distance from the barycentre of the other two
 *   receding - it is moving away from that barycentre
 *   unbound  - its two-body energy against the pair is positive, so it is on a
 *              hyperbolic path and is not coming back
 *
 * plus an absolute floor on d, because the initial configuration spans about 3
 * units and an excursion inside that is not news. Energy is what separates an
 * escape from an excursion; the floor just stops the test firing on the
 * opening transient. */
const ESCAPE_FLOOR = 8;

function escaped(m, y) {
  for (let i = 0; i < 3; i++) {
    const j = (i + 1) % 3, k = (i + 2) % 3;
    const mp = m[j] + m[k];
    const px = (m[j]*y[4*j] + m[k]*y[4*k]) / mp;
    const py = (m[j]*y[4*j+1] + m[k]*y[4*k+1]) / mp;
    const pvx = (m[j]*y[4*j+2] + m[k]*y[4*k+2]) / mp;
    const pvy = (m[j]*y[4*j+3] + m[k]*y[4*k+3]) / mp;
    const dx = y[4*i] - px, dy = y[4*i+1] - py;
    const d = Math.hypot(dx, dy);
    if (d < ESCAPE_FLOOR) continue;
    const wx = y[4*i+2] - pvx, wy = y[4*i+3] - pvy;
    if (dx * wx + dy * wy <= 0) continue;                   // not receding
    const mu = m[i] * mp / (m[i] + mp);
    if (0.5 * mu * (wx*wx + wy*wy) - m[i] * mp / d > 0) return i;   // unbound
  }
  return -1;
}

function runBurrau(opts) {
  const C = CONSTANTS.threebody;
  const m = opts.m || C.m.slice();
  const r0 = opts.r || C.r;
  const y = new Float64Array(12);
  for (let i = 0; i < 3; i++) { y[4*i] = r0[i][0]; y[4*i+1] = r0[i][1]; }
  const eps2 = (opts.eps === undefined ? C.eps : opts.eps) ** 2;
  const tol = opts.tol || C.tol;
  const tMax = opts.tMax || 100, CH = 0.01;      // report interval
  const W = workspace(), st = { h: 1e-4 };
  const E0 = energy3(m, y, eps2);
  let t = 0, who = -1, minSep = Infinity, steps = 0;
  while (t < tMax) {
    steps += advance(m, y, CH, eps2, W, tol, st);
    t += CH;
    for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++)
      minSep = Math.min(minSep, Math.hypot(y[4*j]-y[4*i], y[4*j+1]-y[4*i+1]));
    if (!isFinite(y[0])) return { ok: false, reason: 'non-finite at t=' + t.toFixed(2) };
    who = escaped(m, y);
    if (who >= 0) break;
  }
  const E1 = energy3(m, y, eps2);
  return {
    ok: true, t, who, minSep, steps,
    binary: who < 0 ? null : [0, 1, 2].filter(i => i !== who),
    dE: Math.abs((E1 - E0) / E0)
  };
}

/* ==== B. the double pendulum =========================================== */

function pendDeriv(s, P, out) {
  const [t1, t2, w1, w2] = s;
  const { m1, m2, l1, l2, g } = P;
  const d = t1 - t2, den = 2 * m1 + m2 - m2 * Math.cos(2 * d);
  out[0] = w1; out[1] = w2;
  out[2] = (-g * (2 * m1 + m2) * Math.sin(t1) - m2 * g * Math.sin(t1 - 2 * t2)
          - 2 * Math.sin(d) * m2 * (w2 * w2 * l2 + w1 * w1 * l1 * Math.cos(d)))
          / (l1 * den);
  out[3] = (2 * Math.sin(d) * (w1 * w1 * l1 * (m1 + m2) + g * (m1 + m2) * Math.cos(t1)
          + w2 * w2 * l2 * m2 * Math.cos(d))) / (l2 * den);
}

function pendEnergy(s, P) {
  const [t1, t2, w1, w2] = s;
  const { m1, m2, l1, l2, g } = P;
  const T = 0.5 * m1 * (l1 * w1) ** 2
          + 0.5 * m2 * ((l1 * w1) ** 2 + (l2 * w2) ** 2
            + 2 * l1 * l2 * w1 * w2 * Math.cos(t1 - t2));
  const V = -(m1 + m2) * g * l1 * Math.cos(t1) - m2 * g * l2 * Math.cos(t2);
  return T + V;
}

function runPendulum(opts) {
  const P = Object.assign({}, CONSTANTS.pendulum, opts || {});
  const h = P.h, hours = opts && opts.hours || 8;
  let s = [P.th1, P.th2, 0, 0];
  const k1 = [0, 0, 0, 0], k2 = [0, 0, 0, 0], k3 = [0, 0, 0, 0], k4 = [0, 0, 0, 0];
  const tmp = [0, 0, 0, 0];
  const E0 = pendEnergy(s, P);
  const steps = Math.round(hours * 3600 / h);
  const marks = [], every = Math.floor(steps / 8);
  for (let n = 1; n <= steps; n++) {
    pendDeriv(s, P, k1);
    for (let i = 0; i < 4; i++) tmp[i] = s[i] + 0.5 * h * k1[i];
    pendDeriv(tmp, P, k2);
    for (let i = 0; i < 4; i++) tmp[i] = s[i] + 0.5 * h * k2[i];
    pendDeriv(tmp, P, k3);
    for (let i = 0; i < 4; i++) tmp[i] = s[i] + h * k3[i];
    pendDeriv(tmp, P, k4);
    for (let i = 0; i < 4; i++) s[i] += h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    if (n % every === 0) marks.push({ h: n * h / 3600, d: Math.abs((pendEnergy(s, P) - E0) / E0) });
  }
  return { E0, marks, worst: marks[marks.length - 1].d };
}

/* Three pendulums from the trio's initial angles, reporting the maximum
   pairwise |theta1| separation at a few marks. Deliberately a second
   implementation of the same step as runPendulum above, for the reason in the
   header: a check that runs the same code that produced the answer is
   provenance, not verification. */
function runTrio(opts) {
  const P = Object.assign({}, CONSTANTS.pendulum, opts || {});
  const angles = (opts && opts.angles) || CONSTANTS.pendulumTrio;
  const h = P.h, secs = (opts && opts.secs) || 30;
  const st = angles.map(a => [a, a, 0, 0]);
  const k1 = [0,0,0,0], k2 = [0,0,0,0], k3 = [0,0,0,0], k4 = [0,0,0,0], tmp = [0,0,0,0];
  const spread = () => {
    let m = 0;
    for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++)
      m = Math.max(m, Math.abs(st[i][0] - st[j][0]));
    return m;
  };
  const steps = Math.round(secs / h), marks = [];
  const at = new Set([0, 1, 2, 5, 10, 20, 30].map(t => Math.round(t / h)));
  if (at.has(0)) marks.push({ t: 0, d: spread() });
  for (let n = 1; n <= steps; n++) {
    for (const y of st) {
      let i;
      pendDeriv(y, P, k1);
      for (i = 0; i < 4; i++) tmp[i] = y[i] + 0.5 * h * k1[i];
      pendDeriv(tmp, P, k2);
      for (i = 0; i < 4; i++) tmp[i] = y[i] + 0.5 * h * k2[i];
      pendDeriv(tmp, P, k3);
      for (i = 0; i < 4; i++) tmp[i] = y[i] + h * k3[i];
      pendDeriv(tmp, P, k4);
      for (i = 0; i < 4; i++) y[i] += h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    }
    if (at.has(n)) marks.push({ t: n * h, d: spread() });
  }
  return { marks, start: marks[0].d, end: marks[marks.length - 1].d };
}

/* ==== reporting ======================================================== */

const NAME = ['b1 (mass 3)', 'b2 (mass 4)', 'b3 (mass 5)'];
let failures = 0;
const say = (ok, msg) => { if (!ok) failures++; console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${msg}`); };

function runA() {
  console.log('\nA. Burrau 1913, softened - what this integrator actually does');
  const C = CONSTANTS.threebody;
  console.log(`   eps ${C.eps}, adaptive Cash-Karp RK45, tolerance ${C.tol}`);
  const t0 = Date.now();
  const R = runBurrau({});
  console.log(`   ran in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  if (!R.ok) { say(false, `integration failed: ${R.reason}`); return R; }
  say(R.who >= 0, `resolves: ${R.who < 0 ? 'NO ESCAPE inside t=80' : NAME[R.who] + ' escapes at t = ' + R.t.toFixed(1)}`);
  if (R.who >= 0) console.log(`       binary: ${R.binary.map(i => NAME[i]).join(' + ')}`);
  console.log(`       closest approach seen: ${R.minSep.toExponential(2)}  (eps = ${C.eps})`);
  console.log(`       energy drift over the run: ${R.dE.toExponential(2)}`);
  console.log(`       adaptive steps taken: ${R.steps.toLocaleString()}`);
  say(R.minSep > C.eps * 10,
      `closest approach is ${(R.minSep / C.eps).toFixed(0)}x eps - softening is below the encounter scale`);
  say(R.who === 2, 'the escaper is b3 (mass 5), as Szebehely & Peters 1967 report');
  say(R.dE < 1e-6, `energy conserved to ${R.dE.toExponential(2)} - the encounters are resolved`);
  say(R.who === 2 && R.t > 40 && R.t < 90, `resolution time ${R.t.toFixed(1)} is near the published t = 60`);
  return R;
}

function runB() {
  console.log('\nB. Double pendulum - RK4 energy drift over 8 hours of system time');
  const t0 = Date.now();
  const R = runPendulum({ hours: 8 });
  console.log(`   ran in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  for (const m of R.marks) console.log(`       ${m.h.toFixed(1).padStart(4)} h   |dE/E| ${m.d.toExponential(2)}`);
  say(isFinite(R.worst), 'the integrator stayed finite for 8 hours');
  return R;
}

function runC() {
  console.log('\nC. Three pendulums 0.001 rad apart - do they actually diverge?');
  const R = runTrio({});
  for (const m of R.marks)
    console.log(`       t = ${String(m.t.toFixed(0)).padStart(2)}s   max pairwise |dtheta1| ${m.d.toExponential(2)}`);
  say(R.start <= 0.0021, `they start together: ${R.start.toExponential(2)} rad apart`);
  const early = R.marks.find(m => m.t === 2);
  say(early && early.d < 0.05, `still together at 2s: ${early ? early.d.toExponential(2) : 'n/a'} rad`);
  say(R.end > 1.0, `visibly apart by 30s: ${R.end.toFixed(2)} rad`);
  return R;
}

/* trap 17: a check nobody has seen fail is a claim, not a check. */
function runBreak() {
  console.log('\nBREAK (trap 17) - each mutation must be noticed\n');

  console.log('  1. one initial coordinate corrupted (b1 x: 1 -> 1.5)');
  const bad = runBurrau({ r: [[1.5, 3], [-2, -1], [1, -1]] });
  const base = runBurrau({});
  const differs = !bad.ok || bad.who !== base.who || Math.abs(bad.t - base.t) > 1;
  say(differs, `outcome changed: escaper ${bad.who < 0 ? 'none' : NAME[bad.who]} at t = ${bad.ok ? bad.t.toFixed(1) : 'n/a'} vs ${NAME[base.who]} at t = ${base.t.toFixed(1)}`);

  console.log('\n  2. softening raised to the encounter scale (eps 1e-6 -> 1e-3)');
  const soft = runBurrau({ eps: 1e-3 });
  say(true, `eps=1e-3: escaper ${soft.who < 0 ? 'none' : NAME[soft.who]} at t = ${soft.ok ? soft.t.toFixed(1) : 'n/a'}, closest ${soft.ok ? soft.minSep.toExponential(2) : 'n/a'}`);
  console.log('       (reported, not asserted - this is the value the first draft of');
  console.log('        the plan proposed, and the point is to see what it does)');

  console.log('\n  3. the three pendulums seeded identically (all 2.000 rad)');
  const same = runTrio({ angles: [2.0, 2.0, 2.0] });
  say(same.end < 1e-12,
      `lockstep run ends ${same.end.toExponential(2)} rad apart, so the 1.0 rad ` +
      `assertion in C would fail - the check is not passing on the maths alone`);

  console.log('\n  4. pendulum step inflated 100x (h 2ms -> 200ms)');
  const coarse = runPendulum({ h: 0.2, hours: 8 });
  const fine = runPendulum({ hours: 8 });
  /* A blown-up integrator gives NaN, not a large number, and `NaN > x` is
     false - so a naive comparison reports the mutation as unnoticed when it is
     the most obvious failure there is. Non-finite counts as caught. */
  const caught = !isFinite(coarse.worst) || coarse.worst > fine.worst * 100;
  say(caught, `drift ${isFinite(coarse.worst) ? coarse.worst.toExponential(2) : 'NaN (blew up)'} vs ${fine.worst.toExponential(2)} - the check separates them`);
}

const args = process.argv.slice(2);
console.log('Recomputing what the hero captions claim.');
if (args.includes('--break')) { runBreak(); }
else { runA(); runB(); runC(); }
console.log(`\n  ${failures ? failures + ' FAILED' : 'all checks passed'}\n`);
process.exit(failures ? 1 : 0);
