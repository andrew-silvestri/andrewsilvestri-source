/* THE CHROME INVARIANT.
 *
 *   A page's own chrome AT REST occupies no more than 25% of the viewport
 * height, at every width from 360 up and at every zoom from 100% to 400%.
 *
 * AT REST IS THE SCOPE THE NUMBER WAS ALWAYS DERIVED FROM, not an exemption
 * added later to fit a menu. 25% came from two at-rest measurements and no
 * others: the horizontal nav is 76px on index and 50px elsewhere, which is
 * 8.4% of a 900px viewport and 17% of the 450px a 200% zoom leaves on the same
 * panel. No open state existed when it was set. And the defect it was written
 * against was at-rest by its nature - 39-41% of the first screen at 390, 96%
 * at 250% zoom, 154% at 400% - what made that a defect is that it ARRIVED
 * UNASKED. A menu the reader tapped open is the thing they asked for, and is
 * governed by the open-state properties below rather than by a height cap: no
 * arrangement of seven 44px targets fits inside 56px, so a cap would forbid
 * every menu rather than constrain this one.
 *
 * Chrome is nav.top plus the navband that wraps it on the home page - the
 * furniture a page carries to be part of a site, as opposed to the page's own
 * content. Measured as the union of their border boxes at scrollY 0, so a
 * navband that contains its nav is counted once.
 *
 * WHY 25% AND WHY IT IS NOT TASTE. The horizontal nav the site already has is
 * 76px on index and 50px elsewhere: 8.4% of a 900px viewport at 100% zoom and
 * 17% of the 450px viewport that a 200% zoom leaves on the same panel. So 25%
 * passes the design the site has, at every configuration that design currently
 * works in, with room above the worst of them. It fails the COLUMN layout
 * everywhere - 41% at 390, 96% at 250% zoom, 154% at 400% - and a threshold
 * that passed the column layout at any configuration would have been a number
 * picked to avoid the work rather than measured.
 *
 * The measurement behind those figures is in the Phase 2 packet, section 3,
 * with its configuration: 200 rows, Chromium and Firefox agreeing on every one.
 *
 * WHY BOTH AXES. tests/test_layout.js steps 1024 -> 960 -> 390 and never visits
 * the band between, and style.css:158 puts nav.top into flex-direction:column
 * below 620 - so the widths where the column layout applies were measured at
 * one point out of sixteen. Nothing had measured zoom at all, and at 400% the
 * nav is TALLER THAN THE SCREEN: a reader scrolls past navigation to reach the
 * first word of any page. Zoom is how people with low vision read.
 *
 * HOW ZOOM IS MODELLED, stated because it is a choice. Browser zoom divides the
 * CSS viewport: a 1440x900 panel at 200% lays out as 720x450. Playwright has no
 * cross-engine zoom control, so a zoom of Z is a viewport of physical/Z. That
 * is layout-equivalent and layout is what this measures. It is not the browser
 * zoom UI and reproduces nothing zoom does to rasterisation.
 *
 * KNOWN RED, AND WHY, AS OF 2026-09-12. This gate FAILS 420 of 980 today. The
 * nav collapse that made it pass was reverted the same day: it was held open by
 * :not(:focus-within), and WebKit does not focus an anchor on activation - not
 * on tap and not on click - so the control never opened and every link below
 * 620px was behind it. Andrew found it on an iPhone. A nav that is 154% of the
 * viewport is a worse-looking page; a nav that cannot be opened is an unusable
 * one, so the revert is the right way round and this gate stays red until a
 * mechanism that opens on touch replaces it. The red is deliberate and has a
 * named cause; do not tune the threshold to clear it.
 *
 * AND ITS DENOMINATOR EXCLUDES THE DEVICE CLASS THE DEFECT LIVED IN. Nothing in
 * this file launches WebKit, and nothing emulates touch. The 196 open-state
 * checks used Tab and synthetic activation, both of which work where a real tap
 * does not, so this gate reported 980/980 and 196/196 on a nav that did not
 * work on a phone. It was right about every configuration it could reach, which
 * is the fifth instance of that pattern in this project and the largest. A
 * touch path - WebKit, hasTouch, page.tap() - is owed here and is not yet
 * written.
 *
 * THE OPEN STATE IS CONSTRAINED, JUST NOT BY A HEIGHT. Three properties, each
 * asserted below and each seen to fail:
 *
 *   1. closed is the default on load, on every page at every width and zoom;
 *   2. the reader can dismiss it - the summary toggles back, and Escape closes
 *      it (site/assets/nav.js, the one thing there that is script);
 *   3. it does not persist across navigation.
 *
 * THE NO-JS ARM. site/assets/nav.js's header claims that with the file absent
 * the feature degrades to a working menu: closed on load, the summary toggling
 * on tap and on click, Enter and Space, the announced expanded state - all the
 * platform's - with Escape the only loss. That was a claim in a comment about
 * behaviour nothing exercised, which is exactly what this project keeps finding
 * in other people's files. #nogl and #noaudio are the precedent and the reason:
 * this site's degradations are stated and visible, and a stated degradation
 * nobody has run is a claim like any other.
 *
 * So the arm blocks nav.js at the route, in all three engines, and asserts the
 * platform behaviours still hold AND that Escape does NOTHING. The second half
 * is what makes the first half mean anything: without it the arm would pass
 * identically whether nav.js were blocked or loaded, and would be testing the
 * fully-scripted page under a misleading name.
 *
 * THE TOUCH PATH, AND WHY IT EXISTS. The control this replaced was an
 * <a href="#"> held open by :not(:focus-within). WebKit does not focus an
 * anchor on activation - by tap OR by click, activeElement afterwards is BODY -
 * so it never opened and every link below 620px sat behind it. This file
 * reported 980/980 and 196/196 on that nav, and was right about every
 * configuration it could reach: it launched Chromium and Firefox, emulated no
 * touch, and drove the control with Tab and synthetic activation, all of which
 * work where a real tap does not. So the touch path launches WEBKIT with
 * hasTouch and drives the control with page.tap().
 *
 * Playwright's WebKit is not Safari on iOS. It is the closest instrument
 * available here; Andrew's own phone is ground truth and is where this was
 * confirmed.
 *
 * WHAT THE TOUCH PATH DELIBERATELY DOES NOT ASSERT, and this is not an
 * oversight. It does NOT check that the five dropdown GROUPS open on tap.
 * Those work through `.dd:hover > .ddmenu` at style.css:223 - outside the 620
 * block, written for a desktop pointer - combined with iOS Safari's first-tap
 * hover reveal, confirmed on a real iPhone 2026-09-13. Playwright's synthetic
 * tap leaves hover applied, so an assertion here would pass for the same
 * accidental reason the device does: green because of the very thing it is
 * supposed to be testing. It would read as coverage and be none. GROUP OPENING
 * ON TOUCH IS VERIFIED ON A REAL IPHONE ONLY, IS NOT COVERED BY THIS FILE, AND
 * CANNOT BE, because the instrument cannot separate hover from tap.
 *
 * CLOSED CONTENTS, BECAUSE A HEIGHT IS NOT A DESIGN. This file asserted that
 * the collapsed bar is 50px and 22.2% and was right about both, and the bar was
 * showing Home, Code, About AND the control - three of seven links that were
 * supposed to be behind it. `nav.top > a` is (0,1,2) and so is
 * `nav.top a { ... display: block }` later in style.css, so the hide rule lost
 * on source order. The height was correct because the items fitted on one row.
 * Andrew saw it on his phone; nothing here could.
 *
 * So below the breakpoint the closed bar must contain EXACTLY the control and
 * the link to index.html, and nothing else. Above it, the control must be the
 * one thing hidden. Stated as an exact set rather than a count, because a count
 * is satisfied by the wrong two items.
 *
 * WHAT THIS DOES NOT ASSERT. Only nav.top and .navband: a page that grew some
 * other fixed furniture would not be counted until it is named here. Only
 * scrollY 0 - a sticky band's behaviour further down the page is
 * test_layout.js's business and the sticky decision's own. Nothing about what
 * the chrome CONTAINS, whether its targets are big enough to hit, or whether
 * it is reachable; tests/test_nav_states.js and test_layout.js own those. And
 * nothing about the page's own words, which is a separate invariant and is not
 * set.
 *
 *   node tests/test_chrome.js
 *   node tests/test_chrome.js --break          # 0 caught, non-zero blind
 *   node tests/test_chrome.js --break notap    # the control never opens
 *   node tests/test_chrome.js --break nodefault  # it starts open
 *   node tests/test_chrome.js --break noescape   # Escape does not close it
 *   node tests/test_chrome.js --break persists   # it survives navigation
 *   node tests/test_chrome.js --break contents   # the closed bar shows too much
 *   node tests/test_chrome.js --break nojs       # the menu needs script to open
 *   node tests/test_chrome.js --break jsleak     # nav.js loads despite the block
 *   node tests/test_chrome.js --enforce          # D-01 WebKit rows gate too
 *   node tests/test_chrome.js --break d01        # column nav in the WebKit rows
 *
 * D-01 RULE 1 IN WEBKIT, REPORTED (Q1, 2026-10-20). D-01 adopted this file's
 * 25% as rule 1 (answer 1A) and measured it in Chromium AND WebKit at its own
 * matrix: 360x780, 390x844, 768x1024, 1024x768, 1440x900, and 150/200/250/400%
 * of a 1440x900 panel. The zoom rows were already here, in Chromium and
 * Firefox, gated since c85cb1e; what this file never launched for the height
 * sweep is WebKit, and the device rows at their own heights (the sweep holds
 * height at 844). So that block measures WebKit at the D-01 matrix and
 * REPORTS: it prints its rows and its failures and does not change the exit
 * status unless --enforce is given. Q5 turns enforcement on. A fixture runs
 * first - a 100px nav at 360x225 must read over the limit and a 40px one
 * under it - and a fixture failure exits 1 in every mode. --break d01 forces
 * the column nav (the layout this threshold was written against: 154% at
 * 400%) into the WebKit rows, counts only rows that pass unmutated, and
 * EXITS NON-ZERO WHEN IT IS CAUGHT, 0 when blind. That is the Q1 convention
 * for a new check and the opposite of this file's older modes above; the
 * difference is stated here rather than left for the reader to find.
 *
 * --break forces the column layout at every width and zoom - the exact fault
 * the threshold exists to refuse - and asserts only on the configurations the
 * UNMUTATED site passes, because 420 of 980 already fail and a break mode that
 * asked "did anything fail" would report caught with the mutation doing
 * nothing. A check nobody has seen fail is a claim (trap 17); a break mode
 * whose verdict is true before the fault is injected is decoration wearing the
 * right words (trap 26); read the exit status, not the output (trap 34).
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const pw = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PAGES = ['index', 'about', 'code', 'heat', 'storage', 'climate-cost',
               'longevity', 'skyline', 'continents', 'beauty', 'lostgas', 'takeaway', 'uri', 'ethane',
               '_fixture/kit'];
/* The insight kit's fixture (R1, 2026-10-23): tests/fixtures/kit.html, served
   from tests/ and never from site/, so the kit is measured by this gate as it
   ships before any page uses it (packet R1: the kit passes the existing gates
   on a fixture page). Built by tests/fixtures/build_kit_fixture.py. */
const FIX = path.join(__dirname, 'fixtures');
const LIMIT = 0.25;
const bi = process.argv.indexOf('--break');
const BREAK = bi >= 0;
/* --break with no mode is the column-layout mutation this file shipped with;
   the named modes mutate the touch path instead, one property each. */
const BREAK_MODE = BREAK && process.argv[bi + 1] && !process.argv[bi + 1].startsWith('--')
  ? process.argv[bi + 1] : null;
const TOUCH_BREAKS = ['notap', 'nodefault', 'noescape', 'persists', 'contents',
                      'nojs', 'jsleak'];
if (BREAK_MODE && !TOUCH_BREAKS.includes(BREAK_MODE) && BREAK_MODE !== 'd01') {
  console.error('  --break takes nothing, or one of: ' + TOUCH_BREAKS.concat(['d01']).join(' | '));
  process.exit(1);
}
const ENFORCE = process.argv.includes('--enforce');
/* D-01's matrix, verbatim (DECISIONS D-01, Options). */
const D01 = [
  { name: '360x780', w: 360, h: 780, zoom: 100 }, { name: '390x844', w: 390, h: 844, zoom: 100 },
  { name: '768x1024', w: 768, h: 1024, zoom: 100 }, { name: '1024x768', w: 1024, h: 768, zoom: 100 },
  { name: '1440x900', w: 1440, h: 900, zoom: 100 },
  { name: '960x600', w: 960, h: 600, zoom: 150 }, { name: '720x450', w: 720, h: 450, zoom: 200 },
  { name: '576x360', w: 576, h: 360, zoom: 250 }, { name: '360x225', w: 360, h: 225, zoom: 400 },
];

/* 360 is the floor the invariant names and the narrowest phone worth serving;
   the step is 20px to 1024, with every 4px through 596-644 so the 620
   breakpoint is crossed rather than jumped. */
const WIDTHS = [];
for (let w = 360; w <= 1024; w += 20) WIDTHS.push(w);
for (let w = 596; w <= 644; w += 4) if (!WIDTHS.includes(w)) WIDTHS.push(w);
WIDTHS.sort((a, b) => a - b);
const ZOOMS = [100, 150, 200, 250, 400];
const PANEL = [1440, 900];

const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
               '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
               '.ico': 'image/x-icon', '.json': 'application/json', '.webp': 'image/webp' };

function serve() {
  return new Promise(r => {
    const s = http.createServer((q, res) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      const f = u.startsWith('/_fixture/') ? path.join(FIX, u.slice('/_fixture/'.length)) : path.join(SITE, u);
      fs.readFile(f, (e, d) => {
        if (e) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(u)] || 'application/octet-stream' });
        res.end(d);
      });
    }).listen(0, '127.0.0.1', () => r(s));
  });
}

/* The mutation. Forcing the column layout above its breakpoint is the fault the
   threshold refuses, injected rather than imagined. */
const BREAK_CSS = 'nav.top{flex-direction:column!important}';

async function chromeShare(page) {
  return page.evaluate(() => {
    const parts = [document.querySelector('.navband'), document.querySelector('nav.top')]
      .filter(Boolean).map(el => el.getBoundingClientRect())
      .filter(r => r.height > 0);
    if (!parts.length) return { px: 0, share: 0, n: 0 };
    // union, so a navband containing its nav is counted once
    const top = Math.min(...parts.map(r => r.top));
    const bottom = Math.max(...parts.map(r => r.bottom));
    const px = +(bottom - top).toFixed(1);
    return { px, share: +(px / window.innerHeight).toFixed(4), n: parts.length };
  });
}

/* The second assertion. Reachability is measured by tabbing from the top of the
   document and collecting what actually takes focus, not by reading the DOM: a
   display:none link is in the markup and is reachable by nobody. */
async function openState(page) {
  /* TOP LEVEL, not every anchor in the bar. The first version counted
     nav.top a, which is 15 - it includes the links inside each dropdown, and
     those are display:none until their own .dd:focus-within opens them, a
     mechanism this change does not touch. Nine is what the collapsed bar owes
     the reader: Home, six groups or links, Code, About. */
  const declared = await page.evaluate(() =>
    document.querySelectorAll('nav.top > a:not(.navmore), nav.top > .dd > a').length);
  /* Destinations only. The control is excluded because above the breakpoint it
     is display:none and cannot be tabbed to - which is correct, there is
     nothing to open there, and counting it reported 14 of 15 reachable at
     every width above 620 as though a link had been lost. Whether the control
     itself is reachable is asserted separately, and only where it is shown. */
  const allLinks = await page.evaluate(() =>
    document.querySelectorAll('nav.top a:not(.navmore)').length);
  const controlShown = await page.evaluate(() => {
    const b = document.querySelector('nav.top > details.navmore > summary');
    return !!(b && b.getClientRects().length);
  });
  /* Open the control the way the platform does, not by focusing something.
     This used to focus an <a class="navmore"> because the old mechanism was
     held by :not(:focus-within); the control is a <details> now and its state
     is its open attribute. Left as it was, this reported 84 of 196 failures
     against a nav that works - a check still driving a mechanism that had been
     replaced. */
  await page.evaluate(() => {
    const d = document.querySelector('nav.top > details.navmore');
    if (d) d.open = true;
    for (const g of document.querySelectorAll('nav.top .dd > a')) g.focus();
  });
  await page.waitForTimeout(80);
  const shown = await page.evaluate(() =>
    [...document.querySelectorAll('nav.top > a:not(.navmore), nav.top > .dd > a')]
      .filter(a => a.getClientRects().length > 0).length);
  // tab from the very top and see what the keyboard can actually land on
  await page.evaluate(() => { document.body.setAttribute('tabindex', '-1'); document.body.focus(); });
  const seen = new Set();
  for (let i = 0; i < 60; i++) {
    await page.keyboard.press('Tab');
    const tag = await page.evaluate(() => {
      const a = document.activeElement;
      if (!a || !a.closest || !a.closest('nav.top')) return null;
      /* Identify the control by its class, not by matching its label text.
         The first version compared against '#|Menu ▾' and Firefox failed it
         at two widths out of forty-four while reporting all fourteen anchors
         reachable - the nav was fine and the probe was brittle. */
      return ((a.tagName === 'SUMMARY' || a.classList.contains('navmore')) ? 'CONTROL' : 'LINK') + '|' +
             (a.getAttribute('href') || '') + '|' + (a.textContent || '').trim().slice(0, 12);
    });
    if (tag) seen.add(tag);
  }
  return { declared, allLinks, shown, controlShown, control: [...seen].some(s => s.startsWith('CONTROL|')), tabbed: seen.size };
}

/* NO-JS ARM. nav.js blocked at the route; the platform's own behaviour is
   asserted, and Escape must do nothing. All three engines, because a native
   disclosure is exactly the sort of thing they differ on. */
async function noJsArm(base) {
  const fails = [];
  for (const eng of ['webkit', 'chromium', 'firefox']) {
    let browser;
    try { browser = await pw[eng].launch(); }
    catch (e) { fails.push(`${eng} would not launch: ${e.message.split('\n')[0]}`); continue; }
    const ctx = await browser.newContext({
      viewport: { width: 390, height: 664 }, hasTouch: true,
      isMobile: eng === 'webkit', deviceScaleFactor: 3 });
    const page = await ctx.newPage();
    page.setDefaultTimeout(15000);
    let served = false;
    /* --break jsleak lets the file through, so the arm should notice that
       Escape suddenly works and object. */
    if (BREAK_MODE !== 'jsleak') {
      await page.route('**/assets/nav.js*', r => { served = true; return r.abort(); });
    } else {
      await page.route('**/assets/nav.js*', r => { served = true; return r.continue(); });
    }
    await page.goto(base + 'heat.html', { waitUntil: 'load' });
    await page.waitForTimeout(200);

    const read = () => page.evaluate(() => {
      const d = document.querySelector('nav.top > details.navmore');
      const all = [...document.querySelectorAll('nav.top > a, nav.top > .dd > a')];
      return { present: !!d, open: !!(d && d.open),
               declared: all.length,
               shown: all.filter(a => a.getClientRects().length > 0).length };
    });
    const tag = `[${eng} no-js]`;

    if (!served) fails.push(`${tag} nav.js was never requested - the block proves nothing`);

    /* closed is still the default with no script at all */
    let s = await read();
    if (!s.present) { fails.push(`${tag} no collapse control in the markup`); await browser.close(); continue; }
    if (s.open) fails.push(`${tag} open on load without script - closed must be the default`);

    /* --break nojs: make the platform toggle unavailable, which is what a
       script-dependent menu would look like here. */
    if (BREAK_MODE === 'nojs') {
      await page.evaluate(() => {
        const d = document.querySelector('nav.top > details.navmore');
        if (d) d.addEventListener('click', e => { e.preventDefault(); }, true);
      });
    }

    /* tap opens, tap closes */
    try { await page.tap('nav.top > details.navmore > summary'); } catch (e) { /* below */ }
    await page.waitForTimeout(200);
    s = await read();
    if (!s.open) fails.push(`${tag} a tap did not open it without script`);
    else if (s.shown < s.declared) fails.push(`${tag} opened but ${s.shown} of ${s.declared} links visible`);
    if (s.open) {
      try { await page.tap('nav.top > details.navmore > summary'); } catch (e) { /* below */ }
      await page.waitForTimeout(200);
      if ((await read()).open) fails.push(`${tag} a second tap did not close it without script`);
    }

    /* Enter and Space, still the platform's */
    for (const key of ['Enter', 'Space']) {
      await page.evaluate(() => { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = false; });
      await page.focus('nav.top > details.navmore > summary');
      await page.keyboard.press(key);
      await page.waitForTimeout(180);
      if (!(await read()).open) fails.push(`${tag} ${key} did not toggle it without script`);
    }

    /* AND ESCAPE MUST DO NOTHING. Without this the arm passes identically
       whether nav.js was blocked or loaded. */
    await page.evaluate(() => { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = true; });
    await page.waitForTimeout(120);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    if (!(await read()).open)
      fails.push(`${tag} Escape closed it with nav.js blocked - either the file loaded anyway or something else is handling Escape, and this arm is not testing the degraded page`);

    await browser.close();
  }
  return fails;
}

/* TOUCH PATH. WebKit, hasTouch, page.tap(). Returns a list of failures. */
async function touchPath(base) {
  const fails = [];
  let browser;
  try { browser = await pw.webkit.launch(); }
  catch (e) { return [`webkit would not launch: ${e.message.split('\n')[0]}`]; }
  const ver = browser.version();
  const cases = [
    { label: '390x664 phone', w: 390, h: 664 },
    { label: '360x225 (400% zoom)', w: 360, h: 225 },
  ];
  for (const c of cases) {
    for (const name of ['heat', 'index']) {
      const ctx = await browser.newContext({
        viewport: { width: c.w, height: c.h }, hasTouch: true, isMobile: true,
        deviceScaleFactor: 3 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(15000);
      await page.goto(base + name + '.html', { waitUntil: 'load' });
      if (BREAK_MODE === 'nodefault') {
        await page.evaluate(() => { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = true; });
      }
      if (BREAK_MODE === 'notap') {
        /* the control stops responding: exactly the :focus-within failure */
        await page.evaluate(() => { const s = document.querySelector('nav.top > details.navmore > summary'); if (s) s.style.pointerEvents = 'none'; });
      }
      await page.waitForTimeout(150);

      const read = () => page.evaluate(() => {
        const d = document.querySelector('nav.top > details.navmore');
        const all = [...document.querySelectorAll('nav.top > a, nav.top > .dd > a')];
        return { present: !!d, open: !!(d && d.open),
                 declared: all.length,
                 shown: all.filter(a => a.getClientRects().length > 0).length };
      });

      /* Property 1: closed on load */
      const load = await read();
      if (!load.present) { fails.push(`${name} ${c.label}: no collapse control in the markup`); await ctx.close(); continue; }
      if (load.open) fails.push(`${name} ${c.label}: open on load - closed must be the default`);

      /* the tap opens it, and every declared link becomes visible */
      let tapErr = '';
      try { await page.tap('nav.top > details.navmore > summary'); }
      catch (e) { tapErr = e.message.split('\n')[0]; }
      await page.waitForTimeout(250);
      const opened = await read();
      if (!opened.open) fails.push(`${name} ${c.label}: a tap did not open the control${tapErr ? ' (' + tapErr + ')' : ''}`);
      else if (opened.shown < opened.declared)
        fails.push(`${name} ${c.label}: opened but only ${opened.shown} of ${opened.declared} links visible`);

      /* Property 2a: the summary toggles it back */
      if (opened.open) {
        try { await page.tap('nav.top > details.navmore > summary'); } catch (e) { /* reported below */ }
        await page.waitForTimeout(200);
        const shut = await read();
        if (shut.open) fails.push(`${name} ${c.label}: a second tap did not close it`);
      }

      /* Property 2b: Escape closes it */
      await page.evaluate(() => { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = true; });
      if (BREAK_MODE === 'noescape') {
        await page.evaluate(() => { const s = document.createElement('script'); s.textContent = 'window.__eatEsc=1;document.addEventListener("keydown",function(e){if(e.key==="Escape")e.stopImmediatePropagation()},true)'; document.head.appendChild(s); });
      }
      await page.waitForTimeout(120);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(200);
      const esc = await read();
      if (esc.open) fails.push(`${name} ${c.label}: Escape did not close it`);

      /* Property 3: it does not persist across navigation */
      await page.evaluate(() => { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = true; });
      await page.waitForTimeout(120);
      if (BREAK_MODE === 'persists') {
        await page.evaluate(() => { try { sessionStorage.setItem('navopen', '1'); } catch (e) {} });
      }
      await page.goto(base + (name === 'heat' ? 'storage' : 'about') + '.html', { waitUntil: 'load' });
      if (BREAK_MODE === 'persists') {
        await page.evaluate(() => { try { if (sessionStorage.getItem('navopen')) { const d = document.querySelector('nav.top > details.navmore'); if (d) d.open = true; } } catch (e) {} });
      }
      await page.waitForTimeout(180);
      const after = await read();
      if (after.open) fails.push(`${name} ${c.label}: still open after navigating - it must not persist`);

      await ctx.close();
    }
  }
  await browser.close();
  return fails.map(f => `[webkit ${ver}] ${f}`);
}

/* D-01 RULE 1 IN WEBKIT. Returns { ver, fixture: [..failures], rows: [..] }.
   mutate forces the column nav, for --break d01. */
async function d01WebKit(base, mutate) {
  const browser = await pw.webkit.launch();
  const ver = browser.version();
  const fixture = [];
  /* Fixture first: the instrument must read a tall nav as over and a short
     one as under, at the 400% row where the margin is thinnest. */
  {
    const ctx = await browser.newContext({ viewport: { width: 360, height: 225 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    for (const [px, over] of [[100, true], [40, false]]) {
      await page.setContent(`<body style="margin:0"><nav class="top" style="display:block;height:${px}px">n</nav><p>x</p></body>`);
      const r = await chromeShare(page);
      if ((r.share > LIMIT + 1e-9) !== over || Math.abs(r.px - px) > 0.5)
        fixture.push(`[webkit ${ver} fixture | 360x225 | dpr 1] a ${px}px nav read ${r.px}px, ${(r.share * 100).toFixed(1)}%; want ${over ? 'over' : 'under'} ${LIMIT * 100}%`);
    }
    await ctx.close();
  }
  const rows = [];
  if (!fixture.length) {
    for (const c of D01) {
      const ctx = await browser.newContext({ viewport: { width: c.w, height: c.h }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(20000);
      for (const name of PAGES) {
        await page.goto(base + name + '.html' + (name === 'index' ? '?hero=pendulum' : ''), { waitUntil: 'load' });
        if (mutate) await page.addStyleTag({ content: BREAK_CSS });
        await page.waitForTimeout(100);
        rows.push({ page: name, w: c.w, h: c.h, zoom: c.zoom, ...(await chromeShare(page)) });
      }
      await ctx.close();
    }
  }
  await browser.close();
  return { ver, fixture, rows };
}

function d01Label(ver, r) {
  return `[webkit ${ver} | ${r.w}x${r.h}` +
         `${r.zoom !== 100 ? ' = ' + r.zoom + '% of 1440x900' : ''} | dpr 1]`;
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;

  /* --break d01 runs only the WebKit block: unmutated, then with the column
     nav forced, and asks whether rows that passed now fail. */
  if (BREAK_MODE === 'd01') {
    const clean = await d01WebKit(base, false);
    const broken = clean.fixture.length ? clean : await d01WebKit(base, true);
    srv.close();
    if (clean.fixture.length) {
      for (const f of clean.fixture) console.log('  FIXTURE ' + f);
      console.log('  --break d01: caught by the fixture');
      process.exit(1);
    }
    const passed = new Set(clean.rows.filter(r => r.share <= LIMIT + 1e-9).map(r => r.page + '|' + r.w + 'x' + r.h));
    const caught = broken.rows.filter(r => r.share > LIMIT + 1e-9 && passed.has(r.page + '|' + r.w + 'x' + r.h));
    console.log(`  config: playwright ${require('playwright/package.json').version}, webkit ${clean.ver}, deviceScaleFactor 1`);
    console.log(`  --break d01: column nav forced; ${caught.length} of ${passed.size} WebKit rows that pass unmutated now exceed ${LIMIT * 100}%`);
    for (const r of caught.slice(0, 6))
      console.log(`    ${d01Label(clean.ver, r)} ${r.page}: ${r.px}px, ${(r.share * 100).toFixed(1)}%`);
    console.log(caught.length ? '  caught' : '  BLIND: the mutation changed nothing the threshold refuses');
    process.exit(caught.length ? 1 : 0);
  }

  const engines = [];
  const fails = [];
  const openFails = [];
  const contentFails = [];
  let checks = 0, openChecks = 0, worst = { share: -1 };

  for (const eng of ['chromium', 'firefox']) {
    const browser = await pw[eng].launch();
    engines.push(`${eng} ${browser.version()}`);
    const cases = [
      ...WIDTHS.map(w => ({ kind: 'width', w, h: 844, zoom: 100 })),
      ...ZOOMS.map(z => ({ kind: 'zoom', w: Math.round(PANEL[0] / (z / 100)),
                           h: Math.round(PANEL[1] / (z / 100)), zoom: z })),
    ];
    for (const c of cases) {
      const ctx = await browser.newContext({ viewport: { width: c.w, height: c.h }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(20000);
      for (const name of PAGES) {
        await page.goto(base + name + '.html', { waitUntil: 'load' });
        if (BREAK) await page.addStyleTag({ content: BREAK_CSS });
        await page.waitForTimeout(100);
        const r = await chromeShare(page);
        checks++;
        /* CLOSED CONTENTS. The collapsed bar's visible children, as an exact
           set. BREAK_MODE 'contents' un-hides one to prove this fires. */
        if (BREAK_MODE === 'contents') {
          await page.evaluate(() => {
            const a = document.querySelector('nav.top > a[href="code.html"]');
            if (a) a.style.setProperty('display', 'block', 'important');
          });
          await page.waitForTimeout(40);
        }
        const shownSet = await page.evaluate(() => {
          const nav = document.querySelector('nav.top');
          if (!nav) return null;
          return [...nav.children]
            .filter(c => c.getClientRects().length > 0)
            .map(c => c.tagName === 'DETAILS' ? 'CONTROL'
                    : (c.getAttribute && c.getAttribute('href')) || c.className || c.tagName)
            .sort();
        });
        if (shownSet) {
          const collapsed = c.kind === 'width' ? c.w <= 620 : c.w <= 620;
          const want = collapsed ? ['CONTROL', 'index.html'] : null;
          if (collapsed && (shownSet.length !== 2 || shownSet.join('|') !== want.join('|'))) {
            contentFails.push(`${name} ${c.kind === 'zoom' ? c.zoom + '% zoom' : c.w + 'px'} ` +
                              `${eng}: closed bar shows [${shownSet.join(', ')}], want [${want.join(', ')}]`);
          }
          if (!collapsed && shownSet.includes('CONTROL')) {
            contentFails.push(`${name} ${c.w}px ${eng}: the control is visible above the breakpoint`);
          }
        }
        if (r.share > worst.share) worst = { ...r, eng, name, ...c };
        if (r.share > LIMIT + 1e-9) {
          fails.push({ eng, name, ...c, ...r });
        }
        /* The open state, on one page per configuration - the bar is the same
           on all ten and the height sweep already covers every page. */
        if (name === 'heat' || name === 'index') {
          const o = await openState(page);
          openChecks++;
          /* Every top-level entry visible once the bar is opened, and every
             anchor in the bar - dropdown contents included - reachable by Tab.
             The second is the stronger one and is what keeps the collapse from
             costing anybody a link. */
          if (o.shown < o.declared || o.tabbed < o.allLinks ||
              (o.controlShown && !o.control)) {
            openFails.push({ eng, name, ...c, ...o });
          }
        }
      }
      await ctx.close();
    }
    await browser.close();
  }
  if (contentFails.length) {
    console.log(`\n  ${contentFails.length} closed-contents failure(s) - a correct height ` +
                `with the wrong items in it:`);
    for (const f of contentFails.slice(0, 8)) console.log('    ' + f);
  } else {
    console.log('  closed contents: below 620 the bar is exactly the control and Home; ' +
                'above it the control is hidden');
  }

  const touchFails = (await touchPath(base)).concat(await noJsArm(base));
  const d01 = await d01WebKit(base, false);
  srv.close();

  console.log(`  config: playwright ${require('playwright/package.json').version}, ` +
              `${engines.join(', ')}, deviceScaleFactor 1`);
  console.log(`  ${WIDTHS.length} widths 360-1024 at height 844, ${ZOOMS.length} zooms on a ` +
              `${PANEL.join('x')} panel (CSS viewport = physical / zoom), ${PAGES.length} pages, 2 engines`);
  console.log(`  limit ${(LIMIT * 100).toFixed(0)}% of viewport height`);
  console.log(`  worst: ${worst.name} ${worst.eng} ${worst.kind === 'zoom' ? worst.zoom + '% zoom' : worst.w + 'px'} ` +
              `viewport ${worst.w}x${worst.h} -> ${worst.px}px, ${(worst.share * 100).toFixed(1)}%`);

  if (fails.length) {
    const byPage = {};
    for (const f of fails) (byPage[f.name] = byPage[f.name] || []).push(f);
    console.log(`\n  ${fails.length} of ${checks} page-configuration pairs over the limit:`);
    for (const [name, list] of Object.entries(byPage)) {
      const mx = list.reduce((a, b) => (b.share > a.share ? b : a));
      console.log(`    ${name.padEnd(14)} ${String(list.length).padStart(4)} over, worst ` +
                  `${(mx.share * 100).toFixed(1)}% at ${mx.kind === 'zoom' ? mx.zoom + '% zoom' : mx.w + 'px'} ` +
                  `(${mx.px}px of ${mx.h})`);
    }
  } else {
    console.log(`\n  ${checks} page-configuration pairs, all at or under ${(LIMIT * 100).toFixed(0)}%`);
  }

  if (touchFails.length) {
    console.log(`\n  ${touchFails.length} touch-path failure(s) - WebKit, hasTouch, page.tap():`);
    for (const f of touchFails.slice(0, 10)) console.log('    ' + f);
  } else {
    console.log('  touch path: WebKit tap opens the control, every link shown, ' +
                'summary and Escape close it, closed on load, no persistence');
    console.log('  no-js arm: nav.js blocked in all three engines - closed on load, ' +
                'tap and Enter and Space toggle, Escape correctly does nothing');
  }

  if (openFails.length) {
    console.log(`\n  ${openFails.length} of ${openChecks} open-state checks failed ` +
                `(a bar that collapses and never opens passes the height limit perfectly):`);
    for (const f of openFails.slice(0, 8)) {
      console.log(`    ${f.name} ${f.eng} ${f.kind === 'zoom' ? f.zoom + '% zoom' : f.w + 'px'}: ` +
                  `${f.declared} top-level declared, ${f.shown} visible when opened; ${f.allLinks} anchors, ${f.tabbed} reachable by Tab`);
    }
  } else {
    console.log(`  ${openChecks} open-state checks: every declared link visible when opened and reachable by Tab`);
  }

  /* D-01 rule 1 in WebKit: reported; gating only under --enforce. */
  const d01Over = d01.rows.filter(r => r.share > LIMIT + 1e-9);
  if (d01.fixture.length) {
    console.log('\n  D-01 RULE 1 IN WEBKIT: FIXTURE FAILED - no verdict reported:');
    for (const f of d01.fixture) console.log('    ' + f);
  } else {
    const w = d01.rows.reduce((a, b) => (b.share > a.share ? b : a));
    console.log(`\n  D-01 RULE 1 IN WEBKIT (${ENFORCE ? 'enforced' : 'reported, not enforced'}): ` +
                `${d01Over.length} of ${d01.rows.length} page-configuration pairs over ${(LIMIT * 100).toFixed(0)}%; ` +
                `worst ${w.page} ${d01Label(d01.ver, w)} ${w.px}px of ${w.h}, ${(w.share * 100).toFixed(1)}%`);
    for (const r of d01Over)
      console.log(`    ${d01Label(d01.ver, r)} ${r.page}: ${r.px}px of ${r.h}, ${(r.share * 100).toFixed(1)}%`);
  }
  if (d01.fixture.length) process.exit(1);

  if (BREAK_MODE) {
    const caught = touchFails.length > 0 || contentFails.length > 0;
    console.log(`\n  --break ${BREAK_MODE}: ${caught ? 'caught' : 'BLIND - the touch path noticed nothing'}`);
    process.exit(caught ? 0 : 1);
  }

  if (BREAK) {
    /* Only the configurations the UNMUTATED site passes count here. 420 of 980
       already fail, so a break mode that asked "did anything fail" would have
       reported caught with the mutation doing nothing - trap 26 with the
       verdict true before the fault is injected. PASSING_TODAY is the set the
       horizontal nav is comfortably inside: above the 620 breakpoint, and at
       zooms of 200% and under. */
    const PASSING_TODAY = f => (f.kind === 'width' ? f.w > 620 : f.zoom <= 200);
    const caught = fails.filter(PASSING_TODAY);
    console.log(`\n  --break: the column layout forced at every width and zoom.`);
    console.log(`  of the configurations that pass unmutated, ${caught.length} now fail` +
                (caught.length ? `, worst ${(Math.max(...caught.map(c => c.share)) * 100).toFixed(1)}%` : ''));
    if (!caught.length) {
      console.log('  BLIND: the mutation changed nothing the threshold refuses');
      process.exit(1);
    }
    console.log('  caught');
    process.exit(0);
  }
  process.exit(fails.length || openFails.length || touchFails.length
               || contentFails.length || (ENFORCE && d01Over.length) ? 1 : 0);
})();
