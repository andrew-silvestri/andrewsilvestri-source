/* Checks on the built app.
 *
 * The one that matters is the last one, and it exists because the previous
 * version of this file did not have it. It counted the rectangles the wheel
 * drew, found four hundred and thirty-two of them, and reported everything
 * fine while the panel was blank in a browser - because every rectangle was
 * less than a pixel tall. Drawing something and drawing something visible are
 * different claims, and only one of them was being tested.
 *
 * Run:  node test_app.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const PAGE = path.join(__dirname, 'skyline-app.html');
let fails = 0, checks = 0;
function ok(cond, label, detail) {
  checks++;
  console.log((cond ? '  ok    ' : '  FAIL  ') + label +
              (detail ? '   ' + detail : ''));
  if (!cond) fails++;
}

const VW = 1400, VH = 900;
let rects = [];
function stub() {
  return { clearRect() {}, strokeStyle: '', lineWidth: 0, globalAlpha: 1,
    fillStyle: '', font: '', textAlign: '', beginPath() {}, moveTo() {},
    lineTo() {}, stroke() {},
    createLinearGradient: () => ({ addColorStop() {} }),
    fillRect(x, y, w, h) { rects.push({ x, y, w, h }); },
    fillText() {}, measureText: () => ({ width: 40 }) };
}

/* A Web Audio stub, only as much of it as the app touches. It exists for one
   check: that the sound actually stops when the tab is hidden. Without a
   context the app never starts, so the silencing path would never be
   exercised and could rot unnoticed. */
function param(v) {
  return { value: v, setTargetAtTime(x) { this.value = x; },
           setValueAtTime(x) { this.value = x; },
           cancelScheduledValues() {}, linearRampToValueAtTime(x) { this.value = x; } };
}
function node(extra) {
  const n = { connect(d) { return d; }, disconnect() {}, start() {}, stop() {} };
  return Object.assign(n, extra || {});
}
function FakeCtx() {
  this.currentTime = 0;
  this.state = 'running';
  this.destination = node();
  this.sampleRate = 48000;
}
FakeCtx.prototype.createGain = function () { return node({ gain: param(1) }); };
FakeCtx.prototype.createOscillator = function () {
  return node({ frequency: param(440), detune: param(0), type: 'sine' });
};
FakeCtx.prototype.createBiquadFilter = function () {
  return node({ frequency: param(1000), Q: param(1), gain: param(0), type: 'lowpass' });
};
FakeCtx.prototype.createDynamicsCompressor = function () {
  return node({ threshold: param(-24), knee: param(30), ratio: param(12),
                attack: param(0.003), release: param(0.25) });
};
FakeCtx.prototype.createWaveShaper = function () {
  return node({ curve: null, oversample: 'none' });
};
FakeCtx.prototype.resume = function () { this.state = 'running'; };
FakeCtx.prototype.suspend = function () { this.state = 'suspended'; };
FakeCtx.prototype.close = function () { this.state = 'closed'; };

const errs = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errs.push(e.message));
const dom = new JSDOM(fs.readFileSync(PAGE, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
  beforeParse(w) {
    w.matchMedia = () => ({ matches: false, addEventListener() {} });
    w.AudioContext = FakeCtx;
    w.requestAnimationFrame = () => 0;
    w.HTMLCanvasElement.prototype.getContext = stub;
    w.HTMLCanvasElement.prototype.getBoundingClientRect =
      () => ({ left: 0, top: 0, width: VW, height: VH,
               right: VW, bottom: VH });
  }
});
const win = dom.window, doc = win.document, K = win.__sky;

console.log('\n  Boot');
ok(errs.length === 0, 'no errors on load', errs[0] || '');
ok(!!K, 'the app exposes its handle');
if (!K) process.exit(1);
win.dispatchEvent(new win.Event('resize'));
/* Not fifty. Fifty was the ask and the database will not support it: only
   this many cities have enough buildings on record to fill a wheel, and a
   sparse wheel was the complaint that started this. Publishing the ones that
   work says something true about the data; padding to fifty would say
   something false about the cities. */
ok(K.cities.length >= 20, 'enough cities to be worth browsing',
   K.cities.length + ' published');

console.log('\n  Data');
ok(K.cities.every(c => c.ring && c.ring.length >= 7),
   'every city has a ring');
ok(K.cities.every(c => c.rprof.length === 360 &&
                       c.rprof.every(v => v > 0.001)),
   'no bearing in any city is empty');
ok(K.cities.every(c => c.key && c.key.why), 'every city has a sourced key');
const c0 = K.cities.find(c => c.city === 'New York');
ok(c0.ring.every((r, i, a) => i === 0 || a[i - 1][6] <= r[6]),
   'ring keeps true compass order');
ok(new Set(c0.ring.map((r, i) =>
     +(r[0] - 360 * i / c0.ring.length).toFixed(3))).size === 1,
   'ring spacing is exactly equalised');

console.log('\n  The wheel is actually visible');
/* Split what is drawn into the two panels by where it sits, and require the
   top panel to contain bars of a real size. A panel of hairlines passes a
   count and fails a person. */
let worstTall = 1e9, worstCity = '', worstFill = 1e9, fillCity = '';
let spilled = 0, spillCity = '';
for (let i = 0; i < K.cities.length; i++) {
  K.S.i = i; K.setKey(); K.S.az = 0;
  for (let s = 0; s < 40; s++) K.step(0.016);
  rects = []; K.draw();
  /* The divider, in device pixels. Everything the wheel draws must sit above
     it - that is the check, not a convenience for the filter. The first
     version of this test filtered on it instead of asserting it, and so
     quietly threw away the front half of the wheel and then complained the
     wheel was short. */
  /* Read the canvas rather than assuming the device pixel ratio. Hard-coding
     a factor of two made the panel look twice its real height and reported
     every wheel as a third too short - a measurement bug wearing a drawing
     bug's clothes, for the second time in this file. */
  const split = Math.round(doc.getElementById('c').height * 0.56);
  const top = rects.filter(r => r.y < split && r.h > 1.5);
  const spill = top.filter(r => r.y + r.h > split + 2).length;
  if (spill) { spilled += spill; spillCity = K.cities[i].city; }
  const tallest = top.reduce((m, r) => Math.max(m, r.h), 0);
  const frac = tallest / split;
  if (frac < worstTall) { worstTall = frac; worstCity = K.cities[i].city; }
  // and the wheel must be populated, not one lonely spike
  const solid = top.filter(r => r.h > tallest * 0.08).length;
  if (solid < worstFill) { worstFill = solid; fillCity = K.cities[i].city; }
}
ok(worstTall > 0.35,
   'in every city the tallest tower fills a good part of the panel',
   `worst ${(worstTall * 100).toFixed(0)}% (${worstCity})`);
ok(worstFill >= 12, 'and the wheel is populated, not one lonely spike',
   `worst ${worstFill} visible towers (${fillCity})`);
ok(spilled === 0, 'and no part of it hangs down over the meter',
   spilled ? `${spilled} bars spill in ${spillCity}` : '');

console.log('\n  The meter');
K.S.i = 0; K.setKey();
let minSum = 1e9;
for (let az = 0; az < 360; az += 10) {
  K.S.az = az;
  for (let s = 0; s < 40; s++) K.step(0.016);
  minSum = Math.min(minSum, [...K.levels()].reduce((a, v) => a + v, 0));
}
ok(minSum > 1, 'no bearing leaves the meter silent',
   `quietest total ${minSum.toFixed(1)}`);

console.log('\n  The sidebar describes the wheel');
K.S.i = 0; K.S.az = 0; K.panel();
const stats = doc.getElementById('stats').textContent;
ok(/On the wheel/.test(stats) && /Standing/.test(stats),
   'stats mention the ring and where you stand');
ok(!/Viewpoint/.test(stats), 'and no longer the retired panorama viewpoint');
const li = doc.querySelectorAll('#towers li');
ok(li.length > 20, 'the tower list is the wheel, not twenty',
   li.length + ' rows');
ok(doc.querySelectorAll('#towers li.in').length < li.length,
   'and marks which of them are behind you');



/* ------------------------------------------------- 7. is it kind? -------- */
/* "Sounds harsh" is not a measurement either. These are: how many partials
   sound at once, how much energy sits in the 2-4 kHz band the ear is sharpest
   in, whether any interval in the sounding set is a semitone or a tritone, and
   whether total power swings as you turn. Every city, every bearing, both
   modes. The mapping cannot know what hurts; the instrument has to be built so
   that it cannot produce it. */
console.log('\n  Harshness');

function soundingSet() {
  // reproduce the gain stage the app runs, without needing an audio context
  const mx = K.peak(), lv = K.levels(), pitches = K.pitches();
  const acc = new Float64Array(pitches.length);
  for (let k = 0; k < K.BARS; k++) {
    const j = K.barOf(k);
    const a = Math.pow(Math.min(1, lv[k] / mx), 1.6);
    if (a > acc[j]) acc[j] = a;
  }
  const VOICES = 7;
  const idx = [...acc.keys()].sort((p, q) => acc[q] - acc[p])
                .slice(0, VOICES).filter(j => acc[j] > 1e-4);
  // tilt first, then normalise - the same order the app uses
  const want = idx.map(j => ({ j, w: acc[j] / Math.sqrt(j * 0.5 + 1) }));
  let sum = 0; want.forEach(x => { sum += x.w * x.w; });
  const norm = sum > 0 ? 0.46 / Math.sqrt(sum) : 0;
  return want.map(x => ({ f: pitches[x.j], g: x.w * norm }));
}

{
  let maxVoices = 0, maxHi = 0, worstIvl = 99, powLo = 1e9, powHi = 0;
  let topF = 0, badCity = '';
  for (let i = 0; i < K.cities.length; i++) {
    K.S.i = i; K.setKey();
    for (let az = 0; az < 360; az += 12) {
      K.S.az = az;
      for (let s = 0; s < 40; s++) K.step(0.016);
      const set = soundingSet();
      maxVoices = Math.max(maxVoices, set.length);
      let pow = 0, hi = 0;
      set.forEach(v => {
        pow += v.g * v.g;
        if (v.f >= 2000 && v.f <= 4500) hi += v.g * v.g;
        if (v.f > topF) { topF = v.f; badCity = K.cities[i].city; }
      });
      if (pow > 1e-6) {
        powLo = Math.min(powLo, pow); powHi = Math.max(powHi, pow);
        maxHi = Math.max(maxHi, hi / pow);
      }
      // closest interval between any two sounding partials, in semitones
      for (let a = 0; a < set.length; a++)
        for (let b = a + 1; b < set.length; b++) {
          const semi = Math.abs(12 * Math.log2(set[b].f / set[a].f));
          if (semi > 0.01) worstIvl = Math.min(worstIvl, semi);
        }
    }
  }
  const swing = powHi / Math.max(1e-9, powLo);
  console.log('    musical:');
  ok(maxVoices <= 7,
     '      never more than 7 voices at once',
     `worst ${maxVoices}`);
  ok(topF < 1600,
     '      nothing shrill in the set',
     `highest partial ${topF.toFixed(0)} Hz (${badCity})`);
  ok(maxHi < 0.45, '      the 2-4 kHz band never dominates',
     `worst ${(maxHi * 100).toFixed(0)}% of power`);
  ok(worstIvl >= 2.9,
     '      no painful interval can occur',
     `closest ${worstIvl === 99 ? 'n/a' : worstIvl.toFixed(1)} semitones`);
  ok(swing < 3.2, '      turning does not become a volume ride',
     `loudest bearing is ${swing.toFixed(1)}x the quietest`);
}

console.log('\n  The voicing');
{
  /* Each mode voiced on its own terms, and the minor-third safety net never
     fires. Before 2026-09-04 eight modes collapsed to five sounds and Dubai
     in D hijaz was Vienna in D major, note for note. */
  const shapes = new Map();   // mode -> pitch classes sounding
  const byKey = new Map();    // root + classes -> label
  let bad = '';
  for (let i = 0; i < K.cities.length; i++) {
    K.S.i = i; K.setKey();
    const p = K.pitches();
    const pcs = [...new Set(p.map(f => Math.round(12 * Math.log2(f / p[0])) % 12))]
      .sort((a, b) => a - b).join(',');
    const c = K.cities[i];
    if (shapes.has(c.key.mode) && shapes.get(c.key.mode) !== pcs) bad = c.city;
    shapes.set(c.key.mode, pcs);
    const kk = c.key.root + '|' + pcs;
    if (byKey.has(kk) && byKey.get(kk) !== c.key.label) bad = c.city + ' = ' + byKey.get(kk);
    byKey.set(kk, c.key.label);
    const vo = K.voicing[c.key.mode];
    if (!vo || !vo.ground.concat(vo.upper).every(d => c.key.steps.includes(d)))
      bad = c.city + ': voiced note not in the mode';
  }
  ok(K.clashes() === 0, 'the minor-third net never removes a voiced note',
     `${K.clashes()} removed`);
  ok(new Set(shapes.values()).size === shapes.size,
     'every mode sounds different from every other',
     `${new Set(shapes.values()).size} shapes for ${shapes.size} modes`);
  ok(!bad, 'no two keys with different names sound alike, and every voiced note is in its mode', bad);
}

console.log('\n  Reduced motion');
{
  doc.documentElement.dataset.motion = 'off';
  doc.dispatchEvent(new win.Event('motionchange'));
  ok(K.motionOff() === true, 'the app reads data-motion=off');
  ok(doc.getElementById('spin').hidden === true, 'and hides Spin');
  K.S.i = 0; K.setKey(); K.S.az = 90; K.step(0.016);
  const lv = K.levels(), b = K.bars();
  let snapped = true;
  for (let k = 0; k < K.BARS; k++) if (Math.abs(lv[k] - b[k]) > 1e-6) snapped = false;
  ok(snapped, 'the meter snaps instead of easing');
  doc.documentElement.dataset.motion = 'on';
  doc.dispatchEvent(new win.Event('motionchange'));
  ok(doc.getElementById('spin').hidden === false, 'and Spin comes back when motion does');
}

console.log('\n  The sidebar says where the numbers come from');
{
  const fw = K.cities.findIndex(c => c.city === 'Fort Worth');
  K.S.i = fw; K.setKey(); K.panel();
  const stats = doc.getElementById('stats').textContent;
  ok(/at or above 55 m/.test(stats), 'the ring floor is on screen');
  ok(/published tallest-buildings list/.test(stats) && /above 61 m/.test(stats),
     'a supplemented city names its source and the override floor');
  ok(/Voiced as/.test(doc.getElementById('voice').textContent), 'the voicing is stated');
  K.S.i = 0; K.setKey(); K.panel();
  ok(/Wikidata/.test(doc.getElementById('stats').textContent), 'a Wikidata city says so');
}

console.log('\n  The sound stops when the page does');
{
  const play = doc.getElementById('play');
  play.dispatchEvent(new win.Event('click', { bubbles: true }));
  ok(K.S.playing === true && K.audio().gain > 0, 'pressing Play starts it',
     `gain ${K.audio().gain.toFixed(2)}`);

  Object.defineProperty(doc, 'hidden', { value: true, configurable: true });
  doc.dispatchEvent(new win.Event('visibilitychange'));
  ok(K.S.playing === false && K.audio().gain === 0, 'hiding the tab stops it',
     `gain ${K.audio().gain.toFixed(2)}`);
  ok(play.textContent === 'Play', 'and the button says so');

  // and coming back does not restart it on its own
  Object.defineProperty(doc, 'hidden', { value: false, configurable: true });
  doc.dispatchEvent(new win.Event('visibilitychange'));
  ok(K.S.playing === false, 'coming back leaves it stopped');

  play.dispatchEvent(new win.Event('click', { bubbles: true }));
  ok(K.S.playing === true && K.audio().gain > 0,
     'and Play still works afterwards');

  // into the back-forward cache and out again: the context must survive, or
  // be rebuilt, rather than leaving a button that does nothing
  const hideCached = new win.Event('pagehide');
  Object.defineProperty(hideCached, 'persisted', { value: true });
  win.dispatchEvent(hideCached);
  ok(K.S.playing === false, 'going into the back-forward cache stops it');
  play.dispatchEvent(new win.Event('click', { bubbles: true }));
  ok(K.S.playing === true && K.audio().state === 'running' &&
     K.audio().gain > 0, 'and it plays again when the page comes back',
     `state ${K.audio().state}, gain ${K.audio().gain.toFixed(2)}`);

  // and after a real teardown, where the context is closed for good
  const hideGone = new win.Event('pagehide');
  Object.defineProperty(hideGone, 'persisted', { value: false });
  win.dispatchEvent(hideGone);
  ok(K.S.playing === false, 'leaving the page for good stops it');
  play.dispatchEvent(new win.Event('click', { bubbles: true }));
  ok(K.S.playing === true && K.audio().state === 'running' &&
     K.audio().gain > 0, 'a closed context is rebuilt, not trusted',
     `state ${K.audio().state}, gain ${K.audio().gain.toFixed(2)}`);
}

console.log(`\n  ${checks - fails}/${checks} checks passed` +
            (fails ? `, ${fails} FAILED` : ''));
process.exit(fails ? 1 : 0);
