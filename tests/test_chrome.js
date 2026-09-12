/* THE CHROME INVARIANT.
 *
 *   A page's own chrome occupies no more than 25% of the viewport height, at
 *   every width from 360 up and at every zoom from 100% to 400%.
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
 *   node tests/test_chrome.js --break    # 0 caught, non-zero blind
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
               'longevity', 'skyline', 'continents', 'beauty'];
const LIMIT = 0.25;
const BREAK = process.argv.includes('--break');

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
      fs.readFile(path.join(SITE, u), (e, d) => {
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
    const b = document.querySelector('nav.top .navmore');
    return !!(b && b.getClientRects().length);
  });
  await page.evaluate(() => {
    const b = document.querySelector('nav.top .navmore') ||
              document.querySelector('nav.top a');
    if (b) b.focus();
    for (const d of document.querySelectorAll('nav.top .dd > a')) d.focus();
    if (b) b.focus();
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
      return (a.classList.contains('navmore') ? 'CONTROL' : 'LINK') + '|' +
             (a.getAttribute('href') || '') + '|' + (a.textContent || '').trim().slice(0, 12);
    });
    if (tag) seen.add(tag);
  }
  return { declared, allLinks, shown, controlShown, control: [...seen].some(s => s.startsWith('CONTROL|')), tabbed: seen.size };
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const engines = [];
  const fails = [];
  const openFails = [];
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
  process.exit(fails.length || openFails.length ? 1 : 0);
})();
