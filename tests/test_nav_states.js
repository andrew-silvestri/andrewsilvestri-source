/* Does every nav state RENDER what its own rule DECLARES, and does it clear AA?
 *
 *   node tests/test_nav_states.js
 *   node tests/test_nav_states.js --break indent    # trap 17: prove it fires
 *   node tests/test_nav_states.js --break on
 *   node tests/test_nav_states.js --break hover
 *   node tests/test_nav_states.js --break override
 *
 * Every --break run must exit NON-ZERO if the mutation goes unnoticed (trap 26:
 * a break mode that prints instead of failing is a check on the reader). All
 * four were run on 2026-09-08 and all four fire:
 *
 *   indent    2 states, on rendered-vs-declared; AA stays green
 *   on        3 states, on BOTH assertions
 *   hover     1 state,  on rendered-vs-declared ALONE - AA reports 5.30:1 `ok`
 *   override  3 states, on BOTH, with the rule PRESENT and losing
 *
 * The `hover` row is the reason this file exists: no contrast gate anywhere can
 * fail there, because the broken value is inside the passing range.
 *
 * TWO ASSERTIONS PER STATE, AND THE SECOND IS THE ONE THAT MATTERS.
 *
 *   (a) the contrast pair clears AA at 4.5:1
 *   (b) the rendered value EQUALS the value the named rule declares
 *
 * (b) exists because of trap 31. Three declarations in `nav.top`'s dropdown
 * have now been found never to have applied, all to specificity. Two failed
 * visibly. The third - `.ddmenu a:hover { color: var(--acc) }` - fell back to
 * --dim on --bg-lift, which measures 5.30:1 and PASSES AA; working it gives
 * --acc on --bg-lift at 5.71:1, which also passes. So assertion (a) was green
 * either way and green BECAUSE the rule was dead. A gate defines a floor, and a
 * declaration that fails silently INTO the acceptable region is invisible to
 * it. Only (b) can see that, and nothing in this repository had ever made it.
 *
 * (b) is not tautological. It does not ask "what won" - the winner always
 * equals the computed value. It NAMES the rule that is supposed to win, reads
 * the value out of the stylesheet at run time, and asserts the page agrees. So
 * it fails when a more specific selector elsewhere quietly takes over, which is
 * exactly what happened three times.
 *
 * WHY `_deslop/measure.js` COULD NOT HAVE CAUGHT ANY OF THIS, and it is not the
 * AA arithmetic - that rig resolves backgrounds through CSS and computes the
 * same ratios this file does. The gap is enumeration:
 *
 *   - a dropdown menu is `display: none` until hovered or focused, so an
 *     unattended crawl opens no menu and measures no item inside one;
 *   - `.ddmenu a.on` exists on ONE PAGE PER MENU - the page that item links to -
 *     so even a crawl that opened every menu would find the current-item state
 *     on 1 of 21 pages and only if it happened to be that page;
 *   - `:hover` states are not present in a static walk at all.
 *
 * This file forces the menus open, drives the hovers, and picks pages chosen so
 * each state exists. That is the whole of what it adds.
 *
 * BOTH VIEWPORTS. 390 is not a smaller copy of 1728: the 620px block gives the
 * menu its own `nav.top .ddmenu a` with a different indent, makes `.ddmenu`
 * `background: transparent` so the effective background behind an item is the
 * nav band rather than --card, and opens menus on `:focus-within` alone.
 * Different rules, different backgrounds, different ratios - so it is measured
 * rather than assumed to follow.
 */
'use strict';
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };
const AA = 4.5;

const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : null; };
const BREAK = arg('--break');

/* Each mutation reverts one historical defect, by name. The point of --break is
   not that the file changes; it is that the run FAILS (trap 26). */
const MUTATIONS = {
  // the 26px indent that never applied: drop `nav.top ` from the padding rule
  indent: ['nav.top .ddmenu a {\n  display: block;', '.ddmenu a {\n  display: block;'],
  // the current item at 1.08:1
  on: ['nav.top .ddmenu a.on,\nnav.top .ddmenu a.on:hover {', '.ddmenu a.on, .ddmenu a.on:hover {'],
  // the hover colour that failed INSIDE the passing range
  hover: ['nav.top .ddmenu a:hover {', '.ddmenu a:hover {'],
  /* THE THREE ABOVE ALL DELETE THE NAMED RULE, and a check that only notices
     "the rule is gone" is weaker than one that notices "the rule is there and
     losing" - which is the shape all three real defects had. This one leaves
     `nav.top .ddmenu a.on` exactly where it is and adds a more specific
     selector after it, so the declaration is present, correct, and overridden.
     If the run below reports "declares ... renders ..." rather than "declares
     nothing", the check is reading the cascade and not just the sheet. */
  override: ['/* --------------------------------------------------------------- text --- */',
             'nav.top .dd .ddmenu a.on { color: var(--dim); }\n'
             + '/* --------------------------------------------------------------- text --- */'],
};

function css() {
  let t = fs.readFileSync(path.join(SITE, 'style.css'), 'utf8');
  if (!BREAK) return t;
  const m = MUTATIONS[BREAK];
  if (!m) { console.error('  unknown --break: ' + BREAK + ' (indent|on|hover|override)'); process.exit(2); }
  const n = t.split(m[0]).length - 1;
  if (n !== 1) { console.error('  MUTATION MATCHED %d TIMES, WANTED 1: %s', n, BREAK); process.exit(2); }
  return t.replace(m[0], m[1]);
}

function serve(sheet) {
  return new Promise(r => {
    const s = http.createServer((q, res) => {
      const url = decodeURIComponent(q.url.split('?')[0]);
      if (url === '/style.css') { res.writeHead(200, { 'Content-Type': 'text/css' }); res.end(sheet); return; }
      const f = path.join(SITE, url);
      fs.readFile(f, (e, d) => {
        if (e) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
        res.end(d);
      });
    }).listen(0, '127.0.0.1', () => r(s));
  });
}

/* page, viewport, a selector for the element, whether to hover it, the rule
   that must govern it, and which properties that rule must actually deliver.
   `meter.html` is inside Gas and `code.html` is a top-level item, so
   between them every state exists.

   This was `food.html` until 2026-09-09, when food.html was unpublished and
   seven of the nine states reported ELEMENT NOT FOUND. The page here is not
   arbitrary and must not be changed to just any page: DD resolves to
   `.dd:has(.ddmenu a.on)`, the dropdown holding the current item, so the page
   has to sit in a menu that ALSO has at least one other item - otherwise
   `.ddmenu a:not(.on)` matches nothing and four states vanish. beauty.html
   would not do: Mind holds it alone. Misc holds three.

   The constraint is about the NAV'S SHAPE, not about this page: if Mind
   ever gains a second entry, beauty.html becomes eligible and so does the
   other one. Any page in a menu of two or more works.

   It was `continents.html` until 2026-10-22, when R0 unlisted longevity,
   beauty and skyline (D-39) and Other was left holding continents alone:
   four states reported ELEMENT NOT FOUND against a nav that worked (trap
   35). `meter.html` is in Gas with takeaway. If Gas ever drops to one item,
   pick another menu of two or more. */
const STATES = [
  { name: 'top bar, current page',   page: 'code.html', vp: 1728, sel: 'nav.top > a.on', hover: false,
    rule: 'nav.top a.on', props: ['color'] },
  { name: 'menu item',               page: 'meter.html', vp: 1728, sel: 'DD .ddmenu a:not(.on)', hover: false,
    rule: 'nav.top .ddmenu a', props: ['color', 'padding-left'] },
  { name: 'menu item, hovered',      page: 'meter.html', vp: 1728, sel: 'DD .ddmenu a:not(.on)', hover: true,
    rule: 'nav.top .ddmenu a:hover', props: ['color'] },
  { name: 'menu item, current',      page: 'meter.html', vp: 1728, sel: 'DD .ddmenu a.on', hover: false,
    rule: 'nav.top .ddmenu a.on', props: ['color'] },
  { name: 'menu item, current+hover', page: 'meter.html', vp: 1728, sel: 'DD .ddmenu a.on', hover: true,
    rule: 'nav.top .ddmenu a.on', props: ['color'] },
  /* TWO ENTRIES, NOT ONE, AND THE FIRST DRAFT HAD IT WRONG. At 390 the colour
     and the indent come from DIFFERENT rules: the 620px block's
     `nav.top .ddmenu a` sets only `padding` and `font-size`, so the colour
     still falls through to the base rule outside the media query. Asking one
     entry for both made the check report the base rule as declaring nothing,
     which was the check being right about a mistake in this table. */
  { name: 'phone menu item',         page: 'meter.html', vp: 390, sel: 'DD .ddmenu a:not(.on)', hover: false,
    rule: 'nav.top .ddmenu a', props: ['color'] },
  { name: 'phone menu item, indent', page: 'meter.html', vp: 390, sel: 'DD .ddmenu a:not(.on)', hover: false,
    rule: 'nav.top .ddmenu a', props: ['padding-left'], media: 620 },
  { name: 'phone menu item, current', page: 'meter.html', vp: 390, sel: 'DD .ddmenu a.on', hover: false,
    rule: 'nav.top .ddmenu a.on', props: ['color'] },
  { name: 'phone top bar, current',  page: 'code.html', vp: 390, sel: 'nav.top > a.on', hover: false,
    rule: 'nav.top a.on', props: ['color'] },
  /* THE COLLAPSE CONTROL IS A NAV STATE, and it was introduced into a nav whose
     entire rule set names anchors. A <summary> is not an anchor, so it matched
     NONE of them and fell back to inherited ink - visibly darker than Home and
     Code, which is what Andrew reported from his phone on 2026-09-13. Not
     specificity, which at least leaves a cascade to inspect: NON-MATCHING,
     which produces no cascade and warns nowhere.
     Enumerated against `nav.top > a` rather than guessed: of twenty computed
     properties, four differed - color, padding, outlineColor (which follows
     color), and display. The first three must match and are asserted here.
     `display` differs ON PURPOSE and is not asserted: the anchors are
     full-width rows when the bar is open, the control is an inline item in the
     closed bar, and inline-flex is also what suppresses the disclosure marker.
     ONLY color AND padding-left ARE ASSERTED HERE, and that is the probe's
     limit rather than a judgement: resolve() above knows how to compute a
     declared value for those two properties and no others. padding-top is
     equally wrong when it is wrong and equally unassertable here; the full
     twenty-property comparison lives in the commit that fixed this. */
  { name: 'phone control',           page: 'code.html', vp: 390, sel: 'nav.top > details.navmore > summary', hover: false,
    rule: 'nav.top > .navmore > summary', props: ['color', 'padding-left'], media: 620 },
  { name: 'phone control, hovered',  page: 'code.html', vp: 390, sel: 'nav.top > details.navmore > summary', hover: true,
    rule: 'nav.top > .navmore > summary:hover', props: ['color'], media: 620 },
];

const PROBE = ({ sel, rule, props, media }) => {
  const q = sel.startsWith('DD ')
    ? (() => { const dd = [...document.querySelectorAll('.dd')].find(d => d.querySelector('.ddmenu a.on'));
               return dd ? dd.querySelector(sel.slice(3)) : null; })()
    : document.querySelector(sel);
  if (!q) return { missing: true };

  const rgb = s => (s.match(/[\d.]+/g) || []).slice(0, 4).map(Number);
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                     return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const hex = c => '#' + c.map(v => Math.round(v).toString(16).padStart(2, '0').toUpperCase()).join('');
  const effBg = el => { for (let n = el; n; n = n.parentElement) {
      const c = rgb(getComputedStyle(n).backgroundColor); if (c.length < 4 || c[3] !== 0) return c.slice(0, 3); }
    return [255, 255, 255]; };

  // resolve a declared value (which may be `var(--x)`) to what it computes to
  const resolve = v => {
    const probe = document.createElement('span');
    probe.style.color = v; probe.style.paddingLeft = v;
    document.body.appendChild(probe);
    const cs = getComputedStyle(probe);
    const out = { color: cs.color, 'padding-left': cs.paddingLeft };
    probe.remove();
    return out;
  };

  /* Find the DECLARED value by walking the stylesheet for the named rule. The
     rule is matched by its selector text, inside the right media context, so
     the desktop and 620px versions of `nav.top .ddmenu a` are told apart. */
  const declared = {};
  const want = rule.replace(/\s+/g, ' ').trim();
  const scan = (rules, inMedia) => {
    for (const r of rules) {
      if (r.media) { const mq = r.conditionText || r.media.mediaText;
                     const px = (mq.match(/(\d+)px/) || [])[1];
                     scan(r.cssRules, px ? Number(px) : inMedia); continue; }
      if (!r.selectorText) continue;
      const sels = r.selectorText.split(',').map(s => s.replace(/\s+/g, ' ').trim());
      if (!sels.includes(want)) continue;
      if ((inMedia || null) !== (media || null)) continue;
      for (const p of props) { const v = r.style.getPropertyValue(p); if (v) declared[p] = v; }
    }
  };
  for (const sheet of document.styleSheets) { let l; try { l = sheet.cssRules; } catch (e) { continue; } scan(l, null); }

  const cs = getComputedStyle(q);
  const fg = rgb(cs.color).slice(0, 3), bg = effBg(q);
  const [x, y] = [lum(fg), lum(bg)].sort((a, b) => b - a);
  const mismatches = [];
  for (const p of props) {
    if (!(p in declared)) { mismatches.push(p + ': the rule `' + rule + '` declares nothing'); continue; }
    const wantV = resolve(declared[p])[p];
    const gotV = p === 'color' ? cs.color : cs.getPropertyValue(p);
    if (wantV !== gotV) mismatches.push(p + ': declares ' + declared[p] + ' -> ' + wantV + ', renders ' + gotV);
  }
  return { fg: hex(fg), bg: hex(bg), ratio: +((x + 0.05) / (y + 0.05)).toFixed(2),
           text: (q.textContent || '').trim().slice(0, 20), mismatches };
};

(async () => {
  const sheet = css();
  const srv = await serve(sheet);
  const base = 'http://127.0.0.1:' + srv.address().port + '/';
  const browser = await chromium.launch();
  let checks = 0, fails = 0;

  console.log('\n  nav states: AA at %s:1, and rendered == declared%s\n',
    AA, BREAK ? '   [--break ' + BREAK + ']' : '');
  console.log('  state                      vp    text                 fg        bg        ratio  AA    declared');

  for (const st of STATES) {
    const ctx = await browser.newContext({ viewport: { width: st.vp, height: st.vp === 390 ? 844 : 1080 } });
    const page = await ctx.newPage();
    await page.goto(base + st.page, { waitUntil: 'load' });
    // menus are display:none until hovered or focused; force them so the
    // states exist to read at all. This is the enumeration _deslop/ lacks.
    // Only the menu holding the current item: with every menu forced open,
    // Power's sits over Gas's and a hover on a Gas item is intercepted
    // (2026-10-22, when the fixture moved from the last menu to the first).
    await page.addStyleTag({ content: '.dd:has(.ddmenu a.on) .ddmenu { display: block !important; }' });
    if (st.hover) {
      const el = await page.$(st.sel.startsWith('DD ') ? '.dd:has(.ddmenu a.on) ' + st.sel.slice(3) : st.sel);
      if (el) { await el.hover(); await page.waitForTimeout(200); }
    }
    const r = await page.evaluate(PROBE, { sel: st.sel, rule: st.rule, props: st.props, media: st.media });
    checks++;
    if (r.missing) {
      fails++;
      console.log('  ' + st.name.padEnd(27) + String(st.vp).padEnd(6) + 'ELEMENT NOT FOUND on ' + st.page);
    } else {
      const aaOk = r.ratio >= AA;
      const decOk = r.mismatches.length === 0;
      if (!aaOk || !decOk) fails++;
      console.log('  ' + st.name.padEnd(27) + String(st.vp).padEnd(6) + r.text.padEnd(21)
        + r.fg.padEnd(10) + r.bg.padEnd(10) + String(r.ratio).padStart(5) + '  '
        + (aaOk ? 'ok  ' : 'FAIL').padEnd(6) + (decOk ? 'ok' : 'FAIL'));
      for (const m of r.mismatches) console.log('      ' + st.rule + '  ' + m);
    }
    await ctx.close();
  }

  await browser.close();
  srv.close();
  console.log('\n  %d/%d nav states render what their rule declares and clear AA', checks - fails, checks);
  if (BREAK && fails === 0) {
    console.log('\n  BREAK MODE NOTICED NOTHING - the mutation "%s" changed the page and no', BREAK);
    console.log('  assertion fired. That makes this file decoration, whatever else it prints.');
    process.exit(1);
  }
  if (BREAK) console.log('  --break %s: %d state(s) failed, as they must.', BREAK, fails);
  process.exit(BREAK ? (fails ? 0 : 1) : (fails ? 1 : 0));
})();
