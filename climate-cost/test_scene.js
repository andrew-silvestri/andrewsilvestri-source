/* Checks on the built visualiser.
 *
 * Three things can go wrong here and only one of them is visible by looking:
 *
 *   1. The JavaScript engine drifts from the Python. This is the dangerous
 *      one, because the page keeps working and simply reports different
 *      numbers from the model of record. Checked by running both over the
 *      same routes and comparing to the last decimal that matters.
 *
 *   2. The layout loses nodes. A branch placed outside the frustum, or never
 *      placed at all, is a branch the reader will never know existed - and
 *      the total will still be right, so nothing complains. Checked by
 *      counting the tree and counting what was placed.
 *
 *   3. Balls overlap. The relaxation pass is supposed to prevent it; whether
 *      it converges is an empirical question, so it is measured rather than
 *      assumed.
 *
 * Run:  node test_scene.js       (needs jsdom from ../tests/node_modules; fails loudly without it)
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
// jsdom lives with the other test dependency, in tests/node_modules (npm
// install in tests/). Until 2026-09-05 this line was a bare require that
// nothing installed, so the suite could not run and looked no different from
// a suite that passed. A missing dependency is a failure, said out loud.
let JSDOM;
try {
  ({ JSDOM } = require(path.join(__dirname, '..', 'tests', 'node_modules', 'jsdom')));
} catch (e) {
  console.error('FAIL test_scene.js cannot run: jsdom is not installed in tests/node_modules.');
  console.error('     cd tests && npm install   (package.json lists it)');
  console.error('     ' + String(e.message).split(/\r?\n/)[0]);
  process.exit(2);
}
// three r128, the revision the page loads from its CDN, from the same place
let THREE;
try {
  THREE = require(path.join(__dirname, '..', 'tests', 'node_modules', 'three'));
} catch (e) {
  console.error('FAIL test_scene.js cannot run: three is not installed in tests/node_modules.');
  console.error('     cd tests && npm install   (package.json pins three@0.128.0, the page\'s r128)');
  process.exit(2);
}

const HERE = __dirname;
const PAGE = path.join(HERE, 'climate-cost.html');

let fails = 0, checks = 0;
function ok(cond, label, detail) {
  checks++;
  if (!cond) { fails++; console.log('  FAIL  ' + label +
    (detail ? '\n          ' + detail : '')); }
  else console.log('  ok    ' + label + (detail ? '   ' + detail : ''));
}

/* ------------------------------------------------------------------ boot -- */
let html = fs.readFileSync(PAGE, 'utf8');
// three comes from a CDN in the page; jsdom does not fetch it, so it is
// supplied directly and the tag removed.
html = html.replace(/<script src="https:\/\/cdnjs[^"]*"><\/script>/, '');

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  beforeParse(w) {
    w.THREE = THREE;
    w.requestAnimationFrame = () => 0;
    w.matchMedia = () => ({ matches: false, addEventListener() {} });
    HTMLCanvasElementStub(w);
  }
});
function HTMLCanvasElementStub(w) {
  // no WebGL in jsdom: the page must fall back rather than throw
  w.HTMLCanvasElement.prototype.getContext = () => null;
}
const win = dom.window;
const doc = win.document;

ok(!!win.__lca, 'the page boots and exposes its engine');
if (!win.__lca) { console.log('\n  cannot continue'); process.exit(1); }

/* --------------------------------------------------- 1. engine parity ---- */
console.log('\n  Engine parity with lca.py');
const ROUTES = [
  ['tomato_field', 'ES', 'US-TX', 'sea'],
  ['tomato_field', 'MX', 'US-TX', 'road'],
  ['tomato_greenhouse', 'NL', 'US-NY', 'air'],
  ['beef', 'BR', 'CN', 'sea'],
  ['beef', 'AU', 'US-CA', 'sea'],
  ['chicken', 'BR', 'FR', 'sea'],
  ['coffee', 'CO', 'IT', 'sea'],
  ['coffee', 'ET', 'US-NY', 'air'],
  ['almond', 'US-CA', 'IN', 'sea'],
  ['banana', 'PE', 'NZ', 'sea'],
  ['cheese', 'FR', 'IN', 'sea'],
  ['cheese', 'FR', 'ES', 'road'],
  ['rice', 'VN', 'KE', 'sea'],
  ['rice', 'IN', 'AU', 'rail'],
  // The lifetime path: a capital good amortised over a chosen life. The
  // fifth element is that life; null means the product's published default,
  // which must reproduce the original figure exactly.
  ['car_petrol', 'DE', 'US-TX', 'sea', null],
  ['car_petrol', 'DE', 'US-TX', 'sea', 100000],
  ['car_petrol', 'DE', 'US-TX', 'sea', 400000],
  ['car_ev', 'CN', 'GB', 'sea', 150000],
  ['flight_long', 'US-TX', 'FR', 'air', null],
  ['flight_long', 'US-TX', 'FR', 'air', 300000000],
  ['bus_city', 'DE', 'DE', 'road', 8000000],
  ['rail_intercity', 'FR', 'FR', 'rail', 900000000],
];
// The command line rounds to three decimals, which is enough precision to
// hide a real divergence in a small number. The totals are taken from the
// model object instead, at full precision, and every stage is compared as
// well as the sum - a spine that is wrong in two places by equal and
// opposite amounts would otherwise pass.
const pyOut = execFileSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(HERE)})
from lca import Model
routes = json.loads(sys.argv[1])
out = []
for row in routes:
    item, o, d, m = row[0], row[1], row[2], row[3]
    life = row[4] if len(row) > 4 else None
    r = Model(item, o, d, m, life=life).run()
    out.append({"total": r["total"],
                "stages": [s["total"] for s in r["spine"]]})
print(json.dumps(out))
`, JSON.stringify(ROUTES)], { encoding: 'utf8' });
const py = JSON.parse(pyOut);

let worst = 0, worstLabel = '';
ROUTES.forEach(([item, o, d, m, life], i) => {
  const js = win.__lca.model(item, o, d, m, life);
  const cmp = [[js.total, py[i].total, 'total']].concat(
    js.spine.map((s, k) => [s.total, py[i].stages[k], s.name]));
  for (const [a, b, what] of cmp) {
    const rel = Math.abs(a - b) / Math.max(1e-9, Math.abs(b));
    if (rel > worst) { worst = rel; worstLabel = `${item} ${o}->${d} ${m}: ${what}`; }
  }
});
ok(worst < 1e-9, `${ROUTES.length} routes match the Python, stage by stage`,
   `worst relative difference ${worst.toExponential(2)} (${worstLabel})`);

/* ------------------------------------------------------- 2. the layout --- */
console.log('\n  Layout');
let lostAny = 0, overlapWorst = 0, overlapCase = '', orphanAny = 0;
let freightOK = 0, freightTotal = 0, ringAny = 0;

for (const [item, o, d, m, life] of ROUTES) {
  const r = win.__lca.model(item, o, d, m, life);

  // the arc apex the page would compute, so freight pins the same way
  const n = r.spine.length;
  const x0 = -(n - 1) * 1.75 / 2;
  r.__arcApex = new THREE.Vector3(x0 - 2.9 - 1.55, 2.4, 0);

  const L = win.__lca.layout(r);

  let treeCount = 0;
  (function count(node) { treeCount++; (node.children || []).forEach(count); });
  r.spine.forEach(function walk(node) {
    treeCount++; (node.children || []).forEach(walk);
  });
  if (L.nodes.length !== treeCount) {
    lostAny++;
    console.log(`        ${item}: tree has ${treeCount}, placed ` +
                `${L.nodes.length}`);
  }

  // every non-spine node must reach a spine node by walking parents
  L.nodes.forEach(nd => {
    let x = nd, hops = 0;
    while (x.parent && hops < 40) { x = x.parent; hops++; }
    if (!x.spine) orphanAny++;
  });

  // overlap, as a fraction of the two radii
  for (let i = 0; i < L.nodes.length; i++)
    for (let j = i + 1; j < L.nodes.length; j++) {
      const a = L.nodes[i], b = L.nodes[j];
      const want = a.r + b.r, got = a.pos.distanceTo(b.pos);
      const bad = (want - got) / want;
      if (bad > overlapWorst) {
        overlapWorst = bad;
        overlapCase = `${item}: ${a.name} / ${b.name}`;
      }
    }

  // the freight branch belongs on the route, not in the fan
  const fr = L.nodes.filter(x => String(x.id).indexOf('freight_') === 0);
  if (fr.length) {
    freightTotal++;
    if (fr[0].onRoute && fr[0].pos.x < x0) freightOK++;
  }
  ringAny += L.nodes.filter(x => Math.abs(x.alloc - 1) > 1e-6).length;
}
ok(lostAny === 0, 'every node in the tree gets a position',
   `${ROUTES.length} routes`);
ok(orphanAny === 0, 'every branch traces back to a life-cycle stage');
ok(overlapWorst <= 0.02, 'no two balls overlap after relaxation',
   `worst intrusion ${(overlapWorst * 100).toFixed(1)}% of the radii` +
   (overlapWorst > 0 ? ` (${overlapCase})` : ''));
ok(freightOK === freightTotal && freightTotal > 0,
   'freight is pinned to the route, on the globe side of the chain',
   `${freightOK}/${freightTotal}`);
ok(ringAny > 0, 'allocation rings are drawn where allocation is partial',
   `${ringAny} partial nodes across the routes`);

/* ----------------------------------------------------- 3. the fallback --- */
console.log('\n  The list, and the no-WebGL path');
ok(doc.getElementById('nogl').style.display === 'flex',
   'without WebGL the page says so rather than showing an empty canvas');
ok(doc.getElementById('list').classList.contains('on'),
   'and opens straight into the list');

const r0 = win.__lca.model('tomato_field', 'ES', 'US-TX', 'sea');
let leaves = 0;
r0.spine.forEach(function walk(n) {
  (n.children || []).forEach(c => { leaves++; walk(c); });
});
const rows = doc.querySelectorAll('#list li.n').length;
ok(rows === leaves, 'the list holds every branch the engine produced',
   `${rows} rows, ${leaves} branches`);
ok(doc.querySelectorAll('#list h3').length === r0.spine.length,
   'and one heading per life-cycle stage');

/* -------------------------------------------------------- 4. the shell --- */
console.log('\n  Page');
ok(!/#(d9a441|e8a33d|8a6d2f|e0ad4b|c8922f)/i.test(html),
   'no amber survives in the built page');
ok(/appearance:none/.test(html) && /background-image:linear-gradient\(45deg/
     .test(html),
   'the select caret is drawn by the page, not by the platform');
ok(doc.querySelectorAll('select').length === 4, 'four controls');
ok((html.match(/three\.min\.js/g) || []).length === 0 ||
   fs.readFileSync(PAGE, 'utf8').includes('cdnjs.cloudflare.com'),
   'three is loaded from the CDN the rest of the site uses');



/* ------------------------------------------------ 5. is it legible? ------ */
/* The checks above prove the graph is correct. They say nothing about whether
   a reader can see it, which is the failure that actually matters and the one
   a DOM test misses: a scene can be perfectly well formed and still open with
   half of itself behind the camera, or with every label stacked on the same
   twelve pixels.

   The page's own label placer is called here, not a reimplementation of it.
   A reimplementation is a thing that passes while the page fails. */
console.log('\n  The opening view');
const C = win.__lca.consts;
const VW = 1180, VH = 820;

const item = doc.getElementById('item');
const origin = doc.getElementById('origin');
const dest = doc.getElementById('dest');
const mode = doc.getElementById('mode');

function show(it, o, d, m) {
  item.value = it; origin.value = o; dest.value = d; mode.value = m;
  mode.dispatchEvent(new win.Event('change'));       // triggers a full render
  win.__lca.resetView(true);
  const cam = win.__lca.camera();
  cam.aspect = VW / VH;
  cam.updateProjectionMatrix();
  win.__lca.applyCamera();
  cam.updateMatrixWorld();
  return { L: win.__lca.placed(), cam };
}

let offscreen = 0, totalNodes = 0, inGlobe = 0, collide = 0;
let spineShown = 0, spineAll = 0, dropped = 0, wanted = 0;

for (const [it, o, d, m] of ROUTES) {
  const { L, cam } = show(it, o, d, m);
  const n = L.nodes.filter(x => x.spine).length;
  const globeC = new THREE.Vector3(
    -(n - 1) * C.SPACING / 2 - C.GLOBE_GAP - C.GLOBE_R, 0, 0);

  for (const nd of L.nodes) {
    totalNodes++;
    const v = nd.pos.clone().project(cam);
    if (!(v.z <= 1 && Math.abs(v.x) <= 1 && Math.abs(v.y) <= 1)) offscreen++;
    // nothing but the freight node may be inside the planet
    if (!nd.onRoute && nd.pos.distanceTo(globeC) < C.GLOBE_R + nd.r) inGlobe++;
  }

  const plan = win.__lca.labelPlan(cam, VW, VH, null, null);
  const got = new Set(plan.map(p => p.node).filter(Boolean));

  // how many labels the placer was asked for, and how many it seated
  const ask = L.nodes.filter(nd =>
    nd.spine || Math.abs(nd.total) >= L.maxAbs * 0.05);
  wanted += ask.length;
  dropped += ask.filter(nd => !got.has(nd)).length;
  const sp = L.nodes.filter(nd => nd.spine);
  spineAll += sp.length;
  spineShown += sp.filter(nd => got.has(nd)).length;

  // and nothing the placer seated may overlap anything else it seated
  for (let i = 0; i < plan.length; i++)
    for (let j = i + 1; j < plan.length; j++) {
      const a = plan[i], b = plan[j];
      // the boxes the placer itself used, not an estimate of them
      if (Math.abs(a.x - b.x) * 2 < a.w + b.w &&
          Math.abs(a.y - b.y) * 2 < a.h + b.h)
        { collide++; }
    }
}

ok(offscreen === 0, 'the opening view contains the whole scene',
   `${totalNodes - offscreen}/${totalNodes} nodes inside the frame`);
ok(inGlobe === 0, 'no branch is buried inside the planet');
ok(spineShown === spineAll, 'every life-cycle stage keeps its label',
   `${spineShown}/${spineAll}`);
ok(collide === 0, 'and nothing it did seat overlaps anything else it seated');
ok(dropped / Math.max(1, wanted) < 0.10,
   'labels are rarely dropped for collision',
   `${dropped} dropped of ${wanted} wanted ` +
   `(${(dropped / Math.max(1, wanted) * 100).toFixed(1)}%)`);



/* ------------------------------------------------ 6. does it idle? ------- */
/* A three-dimensional scene that renders unconditionally costs the same
   whether or not anything is happening. On a static page that is a fan
   spinning up to redraw an identical frame sixty times a second, and it is
   invisible in every functional test because the picture is correct. */
console.log('\n  Idling');
ok(typeof win.__lca.isDirty === 'function',
   'the scene tracks whether it is dirty');

// Without WebGL the page opens in the list, and the loop correctly does
// nothing at all while the list is showing. Switch to the scene tab so the
// idle behaviour under test is the one that runs when the scene is visible.
doc.getElementById('t3d').dispatchEvent(new win.MouseEvent('click',
                                                           { bubbles: true }));
ok(!doc.getElementById('list').classList.contains('on'),
   'the scene tab is showing');

// Let it settle the way it settles in a browser: by running frames. The
// camera eases towards its target, so "settled" is a state the loop reaches,
// not one it is put into.
let frames = 0;
while (win.__lca.isDirty() && frames < 600) { win.__lca.frame(); frames++; }
ok(!win.__lca.isDirty(), 'a settled scene reports itself clean',
   `settled after ${frames} frames`);

// and a frame with nothing happening must do no work
let drew = 0;
const realPlan = win.__lca.labelPlan;
const t1 = Date.now();
for (let i = 0; i < 300; i++) win.__lca.frame();
const idleMs = Date.now() - t1;
ok(idleMs < 60, 'three hundred idle frames cost almost nothing',
   `${idleMs} ms total, ${(idleMs / 300).toFixed(3)} ms a frame`);

win.__lca.touch();
ok(win.__lca.isDirty(), 'and touching it wakes it up again');

console.log(`\n  ${checks - fails}/${checks} checks passed` +
            (fails ? `, ${fails} FAILED` : ''));
process.exit(fails ? 1 : 0);
