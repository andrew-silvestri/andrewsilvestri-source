/* Does the visualiser stay snappy at eight thousand species?
 *
 * "Feels slow" is not a measurement and cannot be regressed against, so the
 * things that actually make it feel slow are timed: the cost of getting the
 * page to first paint, the cost of a keystroke in the search box, the cost of
 * changing the sort, and whether the DOM grows without bound as somebody
 * browses. jsdom is a good deal slower than a browser at DOM work, so these
 * numbers are pessimistic - which is the right direction for a budget.
 *
 * A caveat on the budgets. jsdom's CSSOM is far slower than a browser's - a
 * single element.style.width assignment costs it a few tenths of a
 * millisecond, against a few microseconds in Chrome - so re-sorting four
 * hundred rows, which rewrites a couple of thousand style properties, is
 * dominated by that and cannot be optimised below it here. The budgets are
 * therefore set as regression guards a little above what the current code
 * achieves, not as targets for what the page feels like. What they do catch is
 * the thing that actually went wrong: work that scales with the size of the
 * table rather than with the size of the view.
 *
 * Run:  node test_perf.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const PAGE = path.join(__dirname, 'longevity.html');
const html = fs.readFileSync(PAGE, 'utf8');

let fails = 0, checks = 0;
function ok(cond, label, detail) {
  checks++;
  console.log((cond ? '  ok    ' : '  FAIL  ') + label +
              (detail ? '   ' + detail : ''));
  if (!cond) fails++;
}
function budget(ms, limit, label) {
  ok(ms <= limit, label, `${ms.toFixed(0)} ms (budget ${limit})`);
}

console.log('\n  Payload');
const kb = Buffer.byteLength(html) / 1024;
ok(kb < 1100, 'the page is under a megabyte and a bit', `${kb.toFixed(0)} kB`);
ok(html.includes('JSON.parse'),
   'the data is parsed as JSON, not as a JavaScript object literal');

const t0 = Date.now();
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true,
  beforeParse(w) {
    w.requestAnimationFrame = (f) => { f(0); return 0; };
    w.matchMedia = () => ({ matches: false, addEventListener() {} });
  }
});
const boot = Date.now() - t0;
const win = dom.window, doc = win.document;

console.log('\n  Startup');
const RAW = win.__lq ? win.__lq.RAW : null;
ok(!!RAW && RAW.length > 7000, 'the table rehydrates',
   `${RAW ? RAW.length.toLocaleString() : 0} species`);
budget(boot, 2500, 'parse, rehydrate and first render');

// the rehydrated rows must be complete: a dropped field in the transport
// encoding would show as blank taxonomy rather than as an error
const r = RAW[0];
ok(['n', 's', 'm', 'c', 'q', 'cl', 'or', 'fa', 'ge']
     .every(k => r[k] !== undefined),
   'every field survives the encoding', Object.keys(r).length + ' fields');
const blank = RAW.filter(d => !d.cl || !d.or || !d.fa).length;
ok(blank === 0, 'no row lost its taxonomy in transport');

console.log('\n  Interaction');
function time(fn, n) {
  const t = Date.now();
  for (let i = 0; i < n; i++) fn(i);
  return (Date.now() - t) / n;
}

const q = doc.getElementById('q');
const typed = time((i) => {
  q.value = 'shar'.slice(0, (i % 4) + 1);
  q.dispatchEvent(new win.Event('input'));
}, 8);
budget(typed, 260, 'a keystroke in the search box');

q.value = '';
q.dispatchEvent(new win.Event('input'));

// The controls are segmented buttons, not selects, so they are driven the way
// a person drives them: by clicking a segment.
function segKeys(id) {
  return [...doc.querySelectorAll('#' + id + ' button')]
    .map(b => b.dataset.k);
}
function press(id, k) {
  const b = [...doc.querySelectorAll('#' + id + ' button')]
    .find(x => x.dataset.k === k);
  if (!b) throw new Error('no segment ' + k + ' in ' + id);
  b.dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
}

const sortKeys = segKeys('sortSeg');
const sorted = time((i) => press('sortSeg', sortKeys[i % sortKeys.length]), 6);
budget(sorted, 520, 'changing the sort, every row moving');

press('viewSeg', 'gr');
const rankKeys = segKeys('rankSeg');
const grouped = time((i) => press('rankSeg', rankKeys[i % rankKeys.length]), 6);
budget(grouped, 420, 'regrouping every species by a new rank');

// repeating a render must be nearly free, or the cache is not working
press('rankSeg', rankKeys[0]);
const cached = time(() => press('rankSeg', rankKeys[0]), 6);
ok(cached < grouped, 'repeating a render hits the cache',
   `${cached.toFixed(0)} ms against ${grouped.toFixed(0)} ms cold`);

press('viewSeg', 'sp');

console.log('\n  The DOM does not grow without bound');
const filtRank = doc.getElementById('filtRank');
const filtVal = doc.getElementById('filtVal');
filtRank.value = 'or';
filtRank.dispatchEvent(new win.Event('change'));
const before = doc.querySelectorAll('#chart .row').length;
for (let i = 0; i < 25; i++) {
  const o = filtVal.options[i % Math.max(1, filtVal.options.length)];
  if (!o) break;
  filtVal.value = o.value;
  filtVal.dispatchEvent(new win.Event('change'));
}
const after = doc.querySelectorAll('#chart .row').length;
ok(after < 3000, 'browsing twenty-five taxa does not leave the DOM littered',
   `${before} rows to start, ${after} after`);

// The check that matters most: a redraw with nothing changed must be nearly
// free. If it is not, the page is doing work proportional to the table on
// every interaction, which is exactly what made it heavy at eight thousand
// species.
const idem = time(() => win.__lq.render(), 12);
ok(idem < sorted / 3, 'a redraw with nothing changed is nearly free',
   `${idem.toFixed(0)} ms against ${sorted.toFixed(0)} ms for a real change`);

console.log(`\n  ${checks - fails}/${checks} checks passed` +
            (fails ? `, ${fails} FAILED` : ''));
process.exit(fails ? 1 : 0);
