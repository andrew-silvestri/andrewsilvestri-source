/* The browser engine, run headless, for tests/test_parity.py.
 *
 * Boots site/assets/atlas-app.js against the same DOM and three.js stubs the
 * interaction test uses, then runs every prepared scenario through
 * window.__atlasEngine.propagate - the engine of record - and writes each
 * settled state as raw float64 (one file per scenario) plus a JSON index of
 * the steps each took. test_parity.py runs build_throughlines.engine() on
 * the same shocks and compares.
 *
 *   node tests/parity_engine.js <out-dir> [scenario-key ...]
 *
 * Only the engine is exercised; the file returns before the renderer because
 * THREE is a stub, exactly as the interaction test relies on.
 */
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const out = process.argv[2];
if (!out) { console.error('usage: node tests/parity_engine.js <out-dir> [key ...]'); process.exit(2); }
fs.mkdirSync(out, { recursive: true });

const raw = fs.readFileSync(root + '/site/assets/atlas-data.js', 'utf8');
const D = JSON.parse(raw.slice(raw.indexOf('=') + 1, raw.lastIndexOf(';')));
const THREE = require('./three-stub.js');

function El(id) {
  return { id: id, textContent: '', innerHTML: '', value: '0', style: {},
    className: '', dataset: {}, children: [], offsetWidth: 100, offsetHeight: 40,
    clientWidth: 900, clientHeight: 600,
    appendChild(c) { this.children.push(c); return c; },
    addEventListener() {}, removeEventListener() {}, setAttribute() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 900, height: 600 }; },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    querySelector() { return El('q'); }, querySelectorAll() { return []; },
    getContext() { return {
      createRadialGradient() { return { addColorStop() {} }; },
      createLinearGradient() { return { addColorStop() {} }; },
      fillRect() {}, clearRect() {}, beginPath() {}, arc() {}, fill() {}, stroke() {},
      moveTo() {}, lineTo() {}, closePath() {}, save() {}, restore() {},
      translate() {}, scale() {}, rotate() {}, drawImage() {}, fillText() {},
      measureText() { return { width: 10 }; },
      getImageData() { return { data: new Uint8ClampedArray(4) }; },
      putImageData() {}, set fillStyle(v) {}, set strokeStyle(v) {},
      set font(v) {}, set globalAlpha(v) {}, set lineWidth(v) {} }; },
    focus() {}, blur() {}, width: 256, height: 256 };
}
const reg = {};
global.document = {
  getElementById(id) { return reg[id] || (reg[id] = El(id)); },
  createElement(t) { return El('new-' + t); },
  querySelector() { return El('q'); }, querySelectorAll() { return []; },
  addEventListener() {}, body: El('body'), documentElement: El('html')
};
global.window = { ATLAS: D, THREE: THREE, addEventListener() {},
  innerWidth: 1400, innerHeight: 900, devicePixelRatio: 1,
  getComputedStyle() { return { getPropertyValue() { return '#8b7ff2'; } }; },
  requestAnimationFrame() { return 0; } };
global.requestAnimationFrame = () => 0;
global.getComputedStyle = global.window.getComputedStyle;
global.navigator = { userAgent: 'node' };

try { eval(fs.readFileSync(root + '/site/assets/atlas-app.js', 'utf8')); }
catch (e) { console.error('BOOT FAILED:', e.message); process.exit(1); }
const ENGINE = global.window.__atlasEngine;
if (!ENGINE) { console.error('no engine handle: atlas-app.js did not expose __atlasEngine'); process.exit(1); }

const ids = D.idMap;
const keys = process.argv.length > 3 ? process.argv.slice(3) : Object.keys(D.scenarios);
const index = {};
for (const key of keys) {
  const sc = D.scenarios[key];
  if (!sc) { console.error('no scenario', key); process.exit(1); }
  const shocks = {};
  for (const [id, v] of Object.entries(sc.shocks)) if (id in ids) shocks[ids[id]] = v;
  const [state] = ENGINE.propagate(shocks);
  fs.writeFileSync(path.join(out, key + '.f64'), Buffer.from(state.buffer, state.byteOffset, state.byteLength));
  index[key] = { steps: ENGINE.getSteps(), touched: ENGINE.touched(state), shocks: Object.keys(shocks).length };
}
fs.writeFileSync(path.join(out, 'index.json'), JSON.stringify({ n: D.n, scenarios: index }));
console.log(`${keys.length} scenario(s) run in the browser engine, states in ${out}`);
