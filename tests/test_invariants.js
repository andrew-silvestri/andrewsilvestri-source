/* THREE OF THE FIVE LAYOUT INVARIANTS ADOPTED IN D-01 (2026-10-19).
 *
 *   Rule 2, OWN WORDS. At least 20 words of the page's own text in the first
 *     viewport, at every D-01 configuration, zoom included. index is exempt
 *     (settled in D-01). Chrome (nav.top, .navband) is not the page's own text.
 *   Rule 4, SCROLL CUE. No box hides more than 16px of content sideways
 *     without a visible cue OUTSIDE it - the apps' data-scroll-affordance
 *     contract (site/climate-cost-app.html:76). A few px is border and
 *     rounding, not a hidden column; that is why 16 and not 0.
 *   Rule 5, KEYBOARD. Every sideways scroller reachable by Tab, and no visible
 *     interactive element taken out of the tab order, in Chromium, Firefox
 *     AND WebKit. September's "0 unreachable" was Chromium and Firefox only;
 *     WebKit does not make a scroller focusable on its own, so 9 of 11 tables
 *     were unreachable there (D-01, measured 2026-10-18).
 *
 * Rules 1 and 3 live where their instruments already were: chrome share in
 * tests/test_chrome.js, figure text in tests/test_fig_floor.py.
 *
 * REPORTED, NOT ENFORCED. The pages fail all three today (D-01 counted 8, 6
 * and 5 pages). Q5 makes them pass and then turns enforcement on.
 *
 *   node tests/test_invariants.js               # --report: print failures, exit 0
 *   node tests/test_invariants.js --enforce     # exit 1 on any failure
 *   node tests/test_invariants.js --break words    # chrome counted as own words
 *   node tests/test_invariants.js --break cue      # a cue inside its box accepted
 *   node tests/test_invariants.js --break webkit   # the September engine set
 *
 * FIXTURES RUN FIRST, in every engine, before any page: tests/fixtures/
 * invariants-few.html (30 nav words, 5 own words: must read 5 and fail) and
 * invariants-boxes.html (one box per verdict, checkFixtures() below). If a fixture gets
 * the wrong verdict the instrument is broken and the run exits 1 whatever the
 * mode, because a page verdict from a broken instrument is not a verdict.
 *
 * EACH --break REPRODUCES THE FAULT MOST LIKELY TO HAPPEN TO ITS RULE, and
 * must exit NON-ZERO (trap 26: a break run you have to read is a check on the
 * reader). Exit 1 means the gate caught it; exit 0 under --break means BLIND.
 *   words   the counter stops excluding the nav: the few-words fixture then
 *           reads 35 and passes, and the fixture check refuses it.
 *   cue     a cue inside the box is accepted: it scrolls away with the content
 *           it announces, which is why the contract says outside. The fixture
 *           box #f-inside then passes and the fixture check refuses it.
 *   webkit  the keyboard rule runs in Chromium and Firefox only, as the
 *           September "0 unreachable" did; the engine-coverage assertion
 *           refuses a keyboard verdict that never asked WebKit.
 *
 * THE CONFIGURATION IS PRINTED BESIDE EVERY NUMBER (trap 24): engine and
 * version, CSS viewport, the zoom it stands for, deviceScaleFactor.
 * Zoom is modelled as tests/test_chrome.js models it: a Z% zoom of a 1440x900
 * panel is a CSS viewport of 1440/Z x 900/Z. Layout-equivalent, nothing more.
 *
 * WHAT THIS DOES NOT ASSERT. Own words counts words drawn in the first
 * viewport at scrollY 0 after load, by Range rects; it does not judge whether
 * they are legible (test_contrast.js) or large enough (test_fig_floor.py).
 * The cue rule reads the declared contract and checks the cue is visible and
 * outside the box; it does not judge whether a reader understands the cue.
 * Firefox is not used for rules 2 and 4, as in D-01: it reports inline <code>
 * with clientWidth 0 as an overflowing box. The keyboard rule presses Tab from
 * the top until 100 presses find nothing new (ceiling 1500) at 360x780; it does not test
 * arrow-key scrolling once a box has focus, and its interactive-element half
 * is structural (visible, tabindex < 0), because WebKit's Tab skips links by
 * platform setting and a Tab walk would report every link as lost there.
 * The four viewers are not measured: their own panels own their layout.
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const pw = require('playwright');

const ROOT = path.join(__dirname, '..');
const SITE = path.join(ROOT, 'site');
const FIX = path.join(__dirname, 'fixtures');
const PAGES = ['index', 'about', 'code', 'heat', 'storage', 'climate-cost',
               'longevity', 'skyline', 'continents', 'beauty', 'meter'];
const WORDS_EXEMPT = ['index'];
const MIN_WORDS = 20;
const CUE_PX = 16;
/* D-01's matrix, verbatim: five devices and four zooms of a 1440x900 panel. */
const CONFIGS = [
  { name: '360x780', w: 360, h: 780, zoom: 100 }, { name: '390x844', w: 390, h: 844, zoom: 100 },
  { name: '768x1024', w: 768, h: 1024, zoom: 100 }, { name: '1024x768', w: 1024, h: 768, zoom: 100 },
  { name: '1440x900', w: 1440, h: 900, zoom: 100 },
  { name: '960x600', w: 960, h: 600, zoom: 150 }, { name: '720x450', w: 720, h: 450, zoom: 200 },
  { name: '576x360', w: 576, h: 360, zoom: 250 }, { name: '360x225', w: 360, h: 225, zoom: 400 },
];
const LAYOUT_ENGINES = ['chromium', 'webkit'];
const KBD_ENGINES_REQUIRED = ['chromium', 'firefox', 'webkit'];
const KBD_VIEWPORT = { width: 360, height: 780 };
const TAB_CEILING = 1500;

const args = process.argv.slice(2);
const ENFORCE = args.includes('--enforce');
const bi = args.indexOf('--break');
const BREAK = bi >= 0 ? (args[bi + 1] || '') : null;
const BREAKS = ['words', 'cue', 'webkit'];
if (BREAK !== null && !BREAKS.includes(BREAK)) {
  console.error('  --break takes one of: ' + BREAKS.join(' | '));
  process.exit(2);
}
const KBD_ENGINES = BREAK === 'webkit' ? ['chromium', 'firefox'] : KBD_ENGINES_REQUIRED;

const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.ico': 'image/x-icon', '.json': 'application/json', '.webp': 'image/webp' };

function serve() {
  return new Promise(r => {
    const s = http.createServer((q, res) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      const file = u.startsWith('/__fixtures/') ? path.join(FIX, u.slice(12)) : path.join(SITE, u);
      fs.readFile(file, (e, d) => {
        if (e) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(u)] || 'application/octet-stream' });
        res.end(d);
      });
    }).listen(0, '127.0.0.1', () => r(s));
  });
}

/* Rules 2 and 4 in one pass over the page as loaded, at scrollY 0. */
function layoutProbe(page, brk) {
  return page.evaluate(async (brk) => {
    const imgs = [...document.querySelectorAll('img')];
    imgs.forEach(i => { i.loading = 'eager'; });
    for (let k = 0; k < 60 && imgs.some(i => !i.complete); k++)
      await new Promise(r => setTimeout(r, 100));
    window.scrollTo(0, 0);
    const H = window.innerHeight, W = window.innerWidth;
    const chrome = [document.querySelector('.navband'), document.querySelector('nav.top')].filter(Boolean);
    const inChrome = n => brk !== 'words' && chrome.some(c => c.contains(n));
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let words = 0;
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim()) continue;
      const p = n.parentElement;
      if (!p || inChrome(n) || p.closest('script,style,noscript,template')) continue;
      const cs = getComputedStyle(p);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      const re = /\S+/g; let m;
      while ((m = re.exec(n.textContent))) {
        range.setStart(n, m.index); range.setEnd(n, m.index + m[0].length);
        const r = range.getBoundingClientRect();
        if (r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < H && r.right > 0 && r.left < W) words++;
      }
    }
    const boxes = [];
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      if (!['auto', 'scroll', 'hidden'].includes(cs.overflowX)) continue;
      if (el.clientWidth === 0) continue;
      const hidden = el.scrollWidth - el.clientWidth;
      if (hidden <= 1 || el.closest('nav.top,.navband')) continue;
      let cue = false;
      const sel = el.getAttribute('data-scroll-affordance');
      if (sel) {
        let c = null;
        try { c = document.querySelector(sel); } catch (e) { c = null; }
        if (c && (brk === 'cue' || !el.contains(c))) {
          const cr = c.getBoundingClientRect(), ccs = getComputedStyle(c);
          cue = cr.width > 0 && cr.height > 0 && ccs.visibility !== 'hidden' && ccs.display !== 'none';
        }
      }
      boxes.push({ id: el.id || '', what: el.tagName.toLowerCase() + (el.id ? '#' + el.id : el.className ? '.' + String(el.className).split(' ')[0] : ''),
                   hidden, cue, ok: hidden <= 16 || cue });
    }
    return { H, W, words, boxes };
  }, brk);
}

/* Rule 5. Tab from the top until focus comes back round; record which scroll
   boxes, or anything inside them, ever held focus (the scratch tab_probe.js,
   with a cycle stop instead of a fixed 400). Plus the structural half. */
async function kbdProbe(page) {
  const n = await page.evaluate(() => {
    const boxes = [...document.querySelectorAll('body *')].filter(el => {
      const cs = getComputedStyle(el);
      return ['auto', 'scroll'].includes(cs.overflowX) && el.clientWidth > 0
        && el.scrollWidth - el.clientWidth > 1 && !el.closest('nav.top,.navband');
    });
    boxes.forEach((el, i) => { el.dataset.kbdprobe = i; });
    window.__reached = new Set();
    window.__seen = new Set();
    document.addEventListener('focusin', e => {
      window.__seen.add(e.target);
      const box = e.target.closest && e.target.closest('[data-kbdprobe]');
      if (box) window.__reached.add(box.dataset.kbdprobe);
    });
    return boxes.length;
  });
  await page.locator('body').click({ position: { x: 1, y: 1 } });
  /* Stop once 100 presses have found nothing new. Not "focus came back to the
     first element": Firefox hands focus to its own chrome after the last
     element and the first one never takes it again, so a cycle test there
     ran to the ceiling. */
  let presses = 0, seen = -1, still = 0, cycled = false;
  for (; presses < TAB_CEILING; presses++) {
    await page.keyboard.press('Tab');
    if (presses % 25 === 24) {
      const n = await page.evaluate(() => window.__seen.size);
      still = n === seen ? still + 25 : 0; seen = n;
      if (still >= 100) { cycled = true; break; }
    }
  }
  return page.evaluate(([presses, cycled]) => {
    const unreached = [...document.querySelectorAll('[data-kbdprobe]')]
      .filter(b => !window.__reached.has(b.dataset.kbdprobe))
      .map(b => b.tagName.toLowerCase() + (b.id ? '#' + b.id : b.className ? '.' + String(b.className).split(' ')[0] : ''));
    const negative = [...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')]
      .filter(el => { const r = el.getBoundingClientRect(); return (r.width || r.height)
        && el.getAttribute('tabindex') !== null && +el.getAttribute('tabindex') < 0
        && !el.hasAttribute('data-kbdprobe'); })
      .map(el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''));
    const negBoxes = [...document.querySelectorAll('[data-kbdprobe]')]
      .filter(b => b.getAttribute('tabindex') !== null && +b.getAttribute('tabindex') < 0)
      .map(b => b.tagName.toLowerCase() + (b.id ? '#' + b.id : ''));
    return { boxes: document.querySelectorAll('[data-kbdprobe]').length, unreached, negative,
             negBoxes, presses, cycled, focused: window.__seen.size };
  }, [presses, cycled]);
}

/* What each fixture must read. A disagreement is an instrument fault. */
function checkFixtures(eng, few, boxes, kbd) {
  const bad = [];
  if (few) {
    if (few.words !== 5) bad.push(`few-words fixture read ${few.words} own words, want exactly 5`);
    if (few.words >= MIN_WORDS) bad.push(`few-words fixture PASSES the ${MIN_WORDS}-word rule; it must fail`);
  }
  if (boxes) {
    if (boxes.words < MIN_WORDS) bad.push(`boxes fixture read ${boxes.words} own words, want >= ${MIN_WORDS}`);
    const want = { 'f-nocue': false, 'f-good': true, 'f-inside': false, 'f-small': true, 'f-neg': true };
    for (const [id, ok] of Object.entries(want)) {
      const b = boxes.boxes.find(x => x.id === id);
      if (!b) { bad.push(`cue fixture: #${id} not seen as a scroll box`); continue; }
      if (b.ok !== ok) bad.push(`cue fixture: #${id} judged ${b.ok ? 'ok' : 'failing'} (hidden ${b.hidden}px, cue ${b.cue}), want ${ok ? 'ok' : 'failing'}`);
    }
    if (boxes.boxes.length !== 5) bad.push(`cue fixture: ${boxes.boxes.length} scroll boxes seen, want 5`);
  }
  if (kbd) {
    for (const id of ['div#f-good', 'div#f-inside'])
      if (kbd.unreached.includes(id)) bad.push(`keyboard fixture: ${id} has tabindex 0 and was not reached`);
    if (!kbd.unreached.includes('div#f-neg')) bad.push('keyboard fixture: div#f-neg has tabindex -1 and was reached');
    if (!kbd.negative.includes('button#f-btn')) bad.push('keyboard fixture: button#f-btn (tabindex -1) not flagged');
    if (!kbd.cycled) bad.push(`keyboard fixture: focus still finding new targets after ${kbd.presses} presses`);
  }
  return bad.map(b => `[${eng} fixture] ${b}`);
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const versions = {};
  const fixtureFails = [];
  const wordsRows = [], cueRows = [], kbdRows = [];
  const label = (eng, c) => `[${eng} ${versions[eng]} | ${c.name}${c.zoom !== 100 ? ' = ' + c.zoom + '% of 1440x900' : ''} | dpr 1]`;

  /* RULES 2 AND 4: Chromium and WebKit at every D-01 configuration. */
  for (const eng of LAYOUT_ENGINES) {
    const browser = await pw[eng].launch();
    versions[eng] = browser.version();
    const fctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const fp = await fctx.newPage();
    await fp.goto(base + '__fixtures/invariants-few.html', { waitUntil: 'load' });
    const few = await layoutProbe(fp, BREAK);
    await fp.goto(base + '__fixtures/invariants-boxes.html', { waitUntil: 'load' });
    const bx = await layoutProbe(fp, BREAK);
    await fctx.close();
    fixtureFails.push(...checkFixtures(eng, few, bx, null));
    if (fixtureFails.length) { await browser.close(); break; }
    for (const c of CONFIGS) {
      const ctx = await browser.newContext({ viewport: { width: c.w, height: c.h }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(30000);
      for (const p of PAGES) {
        await page.goto(base + p + '.html' + (p === 'index' ? '?hero=pendulum' : ''), { waitUntil: 'load' });
        await page.waitForTimeout(150);
        const m = await layoutProbe(page, BREAK);
        if (!WORDS_EXEMPT.includes(p))
          wordsRows.push({ eng, c, p, words: m.words, ok: m.words >= MIN_WORDS });
        for (const b of m.boxes) cueRows.push({ eng, c, p, ...b });
      }
      await ctx.close();
    }
    await browser.close();
  }

  /* RULE 5: every engine D-01 names, 360x780. */
  const kbdEnginesRun = [];
  if (!fixtureFails.length) {
    for (const eng of KBD_ENGINES) {
      const browser = await pw[eng].launch();
      versions[eng] = browser.version();
      kbdEnginesRun.push(eng);
      const ctx = await browser.newContext({ viewport: KBD_VIEWPORT, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(30000);
      await page.goto(base + '__fixtures/invariants-boxes.html', { waitUntil: 'load' });
      fixtureFails.push(...checkFixtures(eng, null, null, await kbdProbe(page)));
      if (fixtureFails.length) { await browser.close(); break; }
      for (const p of PAGES) {
        await page.goto(base + p + '.html' + (p === 'index' ? '?hero=pendulum' : ''), { waitUntil: 'load' });
        const k = await kbdProbe(page);
        kbdRows.push({ eng, p, ...k });
      }
      await browser.close();
    }
  }
  srv.close();

  console.log(`  config: playwright ${require('playwright/package.json').version}, ` +
              Object.entries(versions).map(([e, v]) => `${e} ${v}`).join(', ') + ', deviceScaleFactor 1');
  console.log(`  mode: ${BREAK !== null ? '--break ' + BREAK : ENFORCE ? '--enforce' : '--report (exit 0 on page failures)'}`);

  if (fixtureFails.length) {
    console.log(`\n  FIXTURE FAILED - the instrument is wrong, no page verdict is reported:`);
    for (const f of fixtureFails) console.log('    ' + f);
    if (BREAK !== null) console.log(`\n  --break ${BREAK}: caught by the fixtures`);
    process.exit(1);
  }
  console.log(`  fixtures: ${LAYOUT_ENGINES.length + kbdEnginesRun.length} engine passes, every verdict as expected`);

  /* Engine coverage for rule 5. --break webkit lands here. */
  const missing = KBD_ENGINES_REQUIRED.filter(e => !kbdEnginesRun.includes(e));
  const coverageFails = missing.map(e => `keyboard rule never ran in ${e}; D-01 5A requires all three engines`);

  const pagesOf = rows => [...new Set(rows.map(r => r.p))];
  const wFail = wordsRows.filter(r => !r.ok);
  const cFail = cueRows.filter(r => !r.ok);
  const kFail = kbdRows.filter(r => r.unreached.length || r.negative.length);

  console.log(`\n  RULE 2 own words >= ${MIN_WORDS} in the first viewport (index exempt): ` +
              `${wFail.length} of ${wordsRows.length} page-configuration pairs fail, on ` +
              `${pagesOf(wFail).length} page(s)${wFail.length ? ': ' + pagesOf(wFail).join(', ') : ''}`);
  for (const r of wFail) console.log(`    ${label(r.eng, r.c)} ${r.p}: ${r.words} own words`);

  console.log(`\n  RULE 4 no box hides > ${CUE_PX}px without a cue outside it: ` +
              `${cFail.length} of ${cueRows.length} box-configuration rows fail, on ` +
              `${pagesOf(cFail).length} page(s)${cFail.length ? ': ' + pagesOf(cFail).join(', ') : ''}`);
  for (const r of cFail) console.log(`    ${label(r.eng, r.c)} ${r.p}: ${r.what} hides ${r.hidden}px, no cue`);

  console.log(`\n  RULE 5 every scroller reachable by Tab, no interactive element at tabindex < 0 ` +
              `(${KBD_VIEWPORT.width}x${KBD_VIEWPORT.height}, dpr 1, Tab until nothing new for 100 presses): ` +
              `${kFail.length} of ${kbdRows.length} page-engine rows fail, on ` +
              `${pagesOf(kFail).length} page(s)${kFail.length ? ': ' + pagesOf(kFail).join(', ') : ''}`);
  for (const r of kbdRows) {
    const tag = `[${r.eng} ${versions[r.eng]} | 360x780 | dpr 1]`;
    if (!r.cycled) console.log(`    ${tag} ${r.p}: NOTE still finding new focus targets at the ${r.presses}-press ceiling`);
    if (r.unreached.length || r.negative.length)
      console.log(`    ${tag} ${r.p}: ${r.unreached.length} of ${r.boxes} scroller(s) unreached` +
                  (r.unreached.length ? ' (' + r.unreached.join(', ') + ')' : '') +
                  (r.negative.length ? `; tabindex < 0: ${r.negative.join(', ')}` : ''));
  }
  for (const f of coverageFails) console.log('    COVERAGE: ' + f);

  const total = wFail.length + cFail.length + kFail.length;
  console.log(`\n  INVARIANTS (D-01 rules 2, 4, 5): ${total} failure(s) - rule 2 ${wFail.length}, ` +
              `rule 4 ${cFail.length}, rule 5 ${kFail.length}` + (coverageFails.length ? `; ${coverageFails.length} coverage failure(s)` : ''));
  if (coverageFails.length) {
    if (BREAK !== null) console.log(`  --break ${BREAK}: caught by the engine-coverage assertion`);
    process.exit(1);
  }
  if (BREAK !== null) {
    console.log(`  --break ${BREAK}: BLIND - nothing refused the fault`);
    process.exit(0);
  }
  process.exit(ENFORCE && total ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
