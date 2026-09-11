/* Layout collision test.
 *
 * Serves site/ itself, opens every content page at 1440, 1024 and 390 px,
 * scrolls it through, and fails if any aside.marginalia's box intersects the
 * box of any other element in <main> (marginalia against marginalia included).
 * This bug has shipped twice - once as a canvas painting under a table
 * (2026-08-30, fixed in a script that was later deleted) and once as HTML
 * marginalia painting over breakout figures (2026-09-04). It is cheaper to
 * catch here than by looking at a screenshot.
 *
 *   node tests/test_layout.js
 *
 * Since 2026-09-04 (Phase 4, A4) it also checks that every page has one left
 * edge: every direct child of <main> that carries text starts at the same x.
 * A picture - img, picture, video, figure, the home page's mosaic - may be
 * wider than the measure, but only centred on it; a text block may not.
 * Asides are the gutters' own and are excluded. The home page shipped with
 * three left edges (masthead 342, hero 360, cards 150 at 1440) and nobody
 * measured it.
 *
 * Since 2026-09-07 it also checks that a position:fixed block is wide enough
 * for its own text. The home page's caption/footer block sits in the margin
 * beside .paper, and that margin is (viewport - 782) / 2 - so it narrows as the
 * window does while the text inside it does not. It shipped staying fixed down
 * to 961px, where the usable width is about two characters; at 1280, a common
 * laptop width, it is 181px against the 209px its longest line needs. This
 * test ran at 1024 and saw none of it, because nothing asserted that the text
 * fit. Overflow is measured as scrollWidth > clientWidth, the same way the
 * marginalia clipping check does it.
 *
 * And the index spec (style.css, "THE INDEX SPEC", 2026-09-05): on any page
 * with an .index, every .entry is a kicker, a linked title and exactly one
 * sentence, carries no figure, does not open by repeating its title, and
 * every entry has the same padding. It succeeded the card assertions, which
 * had held a format that was itself the mistake.
 *
 * Needs playwright (npm install in tests/), and the Chromium it installs.
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PAGES = ['index', 'about', 'code', 'heat', 'storage', 'climate-cost', 'longevity', 'skyline', 'continents', 'beauty',
               'manim'];   // manim added 2026-09-11: twelve <video class="fig"> children, the first page with video since 2026-09-04
/* The four full-screen apps. They carry no nav.top, no <main> and no
   .index, so most of the checks above them no-op; what they are here for is
   the fixed-block and sideways-scroll checks, at the two widths nothing has
   ever measured them at. They were never in PAGES - the list has only ever
   held document pages - which is how four pages with one @media breakpoint
   each shipped untested at 390 and 960. Added 2026-09-10. */
const APPS = ['climate-cost-app', 'longevity-app', 'skyline-app',
              'continents-app'];   // desktop retired 2026-09-05; about added 2026-09-07; beauty added, food+neuron and the whole atlas group unpublished 2026-09-09; Running retired 2026-09-09
// 1920 is here because "New York" wrapping to a line of its own in a 192px
// gutter was read as clipping (2026-09-04); the test now also fails on real
// clipping - any marginalia element wider than its box - so the two cannot
// be confused again.
// 960 is the home page's paper-column breakpoint (style.css, body.home .paper):
// above it the hero canvas shows in the margins either side of the column,
// below it the column is full-bleed. The list used to step 1024 -> 390, so the
// width where that rule changes - and the band of useless 9-121px margins just
// under it - was never measured. Added 2026-09-06, and run green on the tree
// before the hero landed, so a failure here is this test's news and not the
// hero's.
/* 1366 and 1280 straddle the caption/footer block's 1340 breakpoint, and 1280
   is the one that discriminates. At 1366 the block is fixed with 224px of
   usable text against the 209px its longest line needs - it fits, so it would
   pass even against a wrong breakpoint. At 1280 the margin is 181px and the
   text does NOT fit, so that width fails the moment the breakpoint is set too
   low. Both are common laptop widths, and without them nothing between 1024
   and 1440 was ever measured - which is how the block shipped staying fixed
   down to 961px. */
/* trap 17 and 26: the exemption below is a loosening, so it ships with a
   control that runs on every pass. tests/fixtures/clipping.html holds four
   fixed blocks that all overflow the same 100px and differ only in what they
   declare; exactly three must be reported. --break ellipsis disables the
   exemption and the fourth must then be reported too, or this exits 1. */
const BREAK = (() => { const i = process.argv.indexOf('--break');
  return i > 0 ? process.argv[i + 1] : null; })();
if (BREAK && BREAK !== 'ellipsis') {
  console.error('  unknown --break: ' + BREAK + ' (ellipsis)'); process.exit(2);
}
const FIXTURES = { 'clipping': ['silent', 'ellipsis-no-clip', 'wraps'] };
const FIXTURE_DIR = path.join(__dirname, 'fixtures');

const VIEWPORTS = [[1920, 1080], [1440, 900], [1366, 768], [1280, 800], [1024, 768], [960, 720], [390, 844]];
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.ico': 'image/x-icon' };

function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      // Fixtures live in tests/, never in site/ - a control page that shipped
      // would be a published page nobody meant to publish.
      const f = u.startsWith('/_fixture/')
        ? path.join(FIXTURE_DIR, u.slice('/_fixture/'.length))
        : path.join(SITE, u);
      fs.readFile(f, (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
        res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await chromium.launch();
  let failures = 0, checks = 0;
  for (const [w, h] of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    for (const p of PAGES.concat(APPS)) {
      await page.goto(base + p + '.html', { waitUntil: 'load' });
      await page.waitForTimeout(300);
      const H = await page.evaluate(() => document.documentElement.scrollHeight);
      const hits = [];
      // sticky asides move with the scroll, so test at every viewport-height step
      for (let y = 0; y < H; y += h) {
        await page.evaluate(v => scrollTo(0, v), y);
        await page.waitForTimeout(30);
        const found = await page.evaluate(() => {
          const asides = [...document.querySelectorAll('aside.marginalia')];
          if (!asides.length) return [];
          const box = el => el.getBoundingClientRect();
          const hit = (a, b) => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;
          const out = [];
          const others = [...document.querySelectorAll('main *')].filter(el => !el.closest('aside.marginalia') && el.getClientRects().length && !/^(SCRIPT|STYLE)$/.test(el.tagName));
          for (const a of asides) {
            const ab = box(a); if (ab.width === 0 || ab.height === 0) continue;
            for (const el of others) {
              const eb = box(el); if (eb.width === 0 || eb.height === 0) continue;
              if (hit(ab, eb)) out.push((a.className) + ' x ' + el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '') + ' @' + Math.round(eb.top + scrollY));
            }
            for (const b of asides) if (b !== a && hit(ab, box(b))) out.push(a.className + ' x ' + b.className);
            // clipping: text wider than the box that holds it is cut off, not wrapped
            for (const el of [a, ...a.querySelectorAll('*')]) {
              if (el.scrollWidth > el.clientWidth + 1) out.push(a.className + ' clips ' + el.tagName.toLowerCase() + ' "' + (el.textContent || '').trim().slice(0, 28) + '"');
            }
          }
          return out;
        });
        for (const f of found) if (!hits.includes(f)) hits.push(f);
      }
      // one left edge, measured at the top of the page
      await page.evaluate(() => scrollTo(0, 0));
      const edges = await page.evaluate(() => {
        const main = document.querySelector('main');
        // An app has no <main>: it is a control panel beside a stage, two
        // left edges on purpose, and the one-measure rule is a rule about
        // prose. Returning early is the rule not applying, not the rule
        // passing - the apps are held to the two checks below instead.
        if (!main) return [];
        const text = new Map(), pics = [];
        const name = el => el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : '');
        for (const el of main.children) {
          if (/^(ASIDE|SCRIPT|STYLE|FOOTER)$/.test(el.tagName)) continue;
          const b = el.getBoundingClientRect(); if (!b.width || !b.height) continue;
          const pic = /^(IMG|PICTURE|VIDEO|FIGURE)$/.test(el.tagName) || el.classList.contains('mosaic');
          if (pic) pics.push({ n: name(el), l: b.left, r: b.right });
          else { const k = Math.round(b.left); if (!text.has(k)) text.set(k, { names: [], right: 0 }); text.get(k).names.push(name(el)); text.get(k).right = Math.max(text.get(k).right, b.right); }
        }
        const out = [];
        if (text.size > 1) out.push('left edges: ' + [...text].map(([k, v]) => k + 'px (' + v.names.slice(0, 3).join(', ') + (v.names.length > 3 ? ' +' + (v.names.length - 3) : '') + ')').join(' vs '));
        if (text.size) {
          const [tl, tv] = [...text].sort((a, b) => b[1].names.length - a[1].names.length)[0];
          const mid = (tl + tv.right) / 2;
          for (const p of pics) {
            if (Math.abs(p.l - tl) <= 1) continue;
            if (Math.abs((p.l + p.r) / 2 - mid) > 2) out.push('picture off the measure: ' + p.n + ' left ' + Math.round(p.l) + ' vs text ' + tl);
          }
        }
        return out;
      });
      for (const f of edges) if (!hits.includes(f)) hits.push(f);
      // a fixed block's text must fit inside it
      const fits = await page.evaluate((noExempt) => {
        const out = [];
        for (const el of document.querySelectorAll('body *')) {
          if (getComputedStyle(el).position !== 'fixed') continue;
          const r = el.getBoundingClientRect();
          if (!r.width || !r.height) continue;
          const name = el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '');
          for (const n of [el, ...el.querySelectorAll('*')]) {
            // An element that declares text-overflow:ellipsis with hidden
            // overflow has SAID it truncates, and truncation is what
            // scrollWidth > clientWidth measures - so the raw comparison
            // cannot tell a designed ellipsis from text falling off the
            // end. skyline-app's #hint and #notes are the designed case and
            // failed this at three widths for doing what they declare.
            // What is still caught: an element with no ellipsis whose text
            // is simply cut, which is the defect this check exists for.
            const cs = getComputedStyle(n);
            // All three, together. text-overflow does nothing without a
            // clipping overflow, and nothing without nowrap either, so a
            // block declaring an ellipsis it cannot draw is still losing
            // text and must not be exempt. tests/fixtures/clipping.html
            // pins each term.
            if (!noExempt && cs.whiteSpace === 'nowrap'
                && cs.overflowX === 'hidden'
                && cs.textOverflow === 'ellipsis') continue;
            if (n.scrollWidth > n.clientWidth + 1 && n.clientWidth > 0) {
              out.push(`fixed block ${name} is too narrow for its text: `
                + `${n.tagName.toLowerCase()} needs ${n.scrollWidth}px in ${n.clientWidth}px `
                + `"${(n.textContent || '').trim().slice(0, 30)}"`);
              break;
            }
          }
        }
        return out;
      }, BREAK === 'ellipsis');
      for (const f of fits) if (!hits.includes(f)) hits.push(f);
      // Nothing scrolls sideways. A full-bleed canvas beside a fixed panel
      // is the layout that breaks this way, and a reader on a phone gets a
      // page that slides under their thumb with no way to see the right of
      // it. Measured on the document, which is where the overflow lands
      // however deep the element that caused it.
      const hscroll = await page.evaluate(() => {
        const d = document.documentElement;
        if (d.scrollWidth <= d.clientWidth + 1) return [];
        const wide = [...document.querySelectorAll('body *')]
          .filter(el => el.getBoundingClientRect().right > d.clientWidth + 1
                     && el.getClientRects().length)
          .slice(0, 3)
          .map(el => el.tagName.toLowerCase()
               + (typeof el.className === 'string' && el.className
                  ? '.' + el.className.trim().split(/\s+/)[0] : '')
               + ' to ' + Math.round(el.getBoundingClientRect().right));
        return ['scrolls sideways: ' + d.scrollWidth + 'px of content in '
                + d.clientWidth + 'px' + (wide.length ? ' (' + wide.join(', ')
                + ')' : '')];
      });
      for (const f of hscroll) if (!hits.includes(f)) hits.push(f);
      // the nav stays on one row above 620
      const navrow = await page.evaluate(() => {
        const nav = document.querySelector('nav.top');
        if (!nav || getComputedStyle(nav).flexDirection === 'column') return [];
        const kids = [...nav.children].filter(k => k.getClientRects().length);
        if (!kids.length) return [];
        const tops = [...new Set(kids.map(k => Math.round(k.getBoundingClientRect().top)))];
        // Items are centred on the row, and a .dd span is a different height
        // from a bare <a>, so their tops differ by a pixel or two on the SAME
        // row. Rows are found by clustering tops, not by counting distinct
        // ones - the naive version reports two rows on a bar that has one.
        tops.sort((a, b) => a - b);
        const rows = [tops[0]];
        for (const t of tops) if (t - rows[rows.length - 1] > 12) rows.push(t);
        if (rows.length === 1) return [];
        const names = kids.map(k => (k.textContent || '').trim().split(/\s+/)[0]).join(', ');
        return [`nav.top wrapped to ${rows.length} rows at this width (${kids.length} items: ${names})`];
      });
      for (const f of navrow) if (!hits.includes(f)) hits.push(f);
      // the index spec
      const entries = await page.evaluate(() => {
        const es = [...document.querySelectorAll('.index .entry')];
        if (!es.length) return [];
        const out = [], pads = new Set();
        for (const e of es) {
          const h3 = e.querySelector('h3'), name = h3 ? h3.textContent.trim() : '(untitled)';
          const ps = e.querySelectorAll(':scope > p'), tags = e.querySelectorAll('.tag');
          if (!h3 || !h3.querySelector('a')) out.push(`entry "${name}": no linked title`);
          if (tags.length !== 1) out.push(`entry "${name}": ${tags.length} kickers`);
          if (e.querySelector('img, picture, video, canvas')) out.push(`entry "${name}": carries a figure; the index spec has none`);
          if (ps.length !== 1) out.push(`entry "${name}": ${ps.length} paragraphs, wants one sentence`);
          else {
            const t = ps[0].textContent.trim();
            const n = (t.match(/[.!?]["')\u2019]*(\s|$)/g) || []).length;
            if (n !== 1) out.push(`entry "${name}": this entry's hook is over budget: ${n} sentences, wants one (spec item 2)`);
            if (t.toLowerCase().replace(/^the /, '').startsWith(name.toLowerCase().replace(/^the /, ''))) out.push(`entry "${name}": the sentence opens by repeating the title`);
          }
          const cs = getComputedStyle(e); pads.add(cs.paddingTop + '/' + cs.paddingBottom + '/' + cs.borderTopWidth);
        }
        if (pads.size > 1) out.push('entries differ in shape: ' + [...pads].join(', '));
        return out;
      });
      for (const f of entries) if (!hits.includes(f)) hits.push(f);
      /* An inner scroll region on a page that does not itself scroll hides
         content with nothing to say it is there. Both halves matter: an
         inner scroller on a scrolling page is ordinary, and a page that
         scrolls can be read to its end. continents-app failed exactly this
         until 2026-09-10 and the suite reported 108/108, because vertical
         clipping inside a scroll container was not measured anywhere. */
      const trapped = await page.evaluate(() => {
        const d = document.documentElement;
        if (d.scrollHeight > d.clientHeight + 1) return [];
        const nm = el => el.tagName.toLowerCase()
          + (el.id ? '#' + el.id : (typeof el.className === 'string' && el.className
             ? '.' + el.className.trim().split(/\s+/)[0] : ''));
        const out = [];
        for (const el of document.querySelectorAll('body *')) {
          const cs = getComputedStyle(el);
          if (!/(auto|scroll)/.test(cs.overflowY)) continue;
          if (el.scrollHeight <= el.clientHeight + 1) continue;
          /* A panel may carry its own affordance instead. The exemption is
             DECLARED, not inferred: the check cannot tell a cue from any
             other div, and guessing is how two earlier metrics in this file
             ended up measuring the design.

             data-scroll-affordance is a SELECTOR now, not a class name,
             because as of 2026-09-11 the cue is a sibling of the scroller
             rather than a child - a sticky cue inside a scrollport lands on
             whatever is at the bottom of it, which was prose in skyline and
             a form control in climate-cost at 390.

             Three things are required and the third is the new one: the cue
             must exist, it must be visible at this width, and IT MUST NOT BE
             INSIDE THE BOX IT DESCRIBES. Without the third, re-parenting it
             back into the scrollport would pass silently and bring the
             overlap back. */
          const decl = el.dataset && el.dataset.scrollAffordance;
          if (decl) {
            const cue = document.querySelector(decl);
            const shown = cue && cue.getBoundingClientRect().height > 0
              && getComputedStyle(cue).visibility !== 'hidden';
            if (shown && !el.contains(cue)) continue;
            out.push(nm(el) + ' declares "' + decl + '" and it is '
              + (!cue ? 'not there'
                 : !shown ? 'not visible at this width'
                 : 'inside the scrollport it describes')
              + ', while hiding ' + (el.scrollHeight - el.clientHeight) + 'px');
            continue;
          }
          out.push(nm(el) + ' hides ' + (el.scrollHeight - el.clientHeight)
            + 'px inside a page that does not scroll');
        }
        return out;
      });
      for (const f of trapped) if (!hits.includes(f)) hits.push(f);
      /* A canvas is a picture with no text in it, and on these four apps it
         is often the only place some of the content exists. */
      /* Is each control actually reachable where it is drawn? Asked with
         elementFromPoint at the control's own centre, which is the only
         question that matters and the only one that survives clipping.
         A rect comparison does NOT: getBoundingClientRect returns unclipped
         geometry, so a control scrolled half out of a panel reports a box
         overlapping whatever is below the panel, and the first version of
         this check duly reported climate-cost's tabs as covered by its own
         canvas. The same mistake was made measuring the scroll cues an hour
         earlier; an unclipped API cannot answer a question about a clipped
         box.

         The defect it exists for: longevity-app's #detail was position:fixed
         bottom-right at 70vh and covered two controls at 1440, four at 1280
         and NINE at 1024 - including the baseline switch, the one control
         that page's own prose singles out. Nothing here could see it. */
      const covering = await page.evaluate(() => {
        const nm = el => el.tagName.toLowerCase()
          + (el.id ? '#' + el.id : (typeof el.className === 'string' && el.className
             ? '.' + el.className.trim().split(/\s+/)[0] : ''));
        const out = [];
        for (const c of document.querySelectorAll(
              'a[href],button,select,input,textarea,[tabindex]')) {
          if (c.tabIndex < 0) continue;
          const b = c.getBoundingClientRect();
          if (!b.width || !b.height) continue;
          const x = b.left + b.width / 2, y = b.top + b.height / 2;
          if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) continue;
          /* A control scrolled out of a panel is not covered, it is simply
             not on screen - and its rect still says where it WOULD be, so
             elementFromPoint there returns whatever is at that spot instead.
             That is the third form this clipping problem has taken in this
             file. Only ask about a control that is actually inside every
             scrolling ancestor it has. */
          let clipped = false;
          for (let a = c.parentElement; a && a !== document.body; a = a.parentElement) {
            const cs = getComputedStyle(a);
            if (!/(auto|scroll|hidden)/.test(cs.overflowY + cs.overflowX)) continue;
            const ab = a.getBoundingClientRect();
            if (y < ab.top || y > ab.bottom || x < ab.left || x > ab.right) {
              clipped = true; break;
            }
          }
          if (clipped) continue;
          const top = document.elementFromPoint(x, y);
          if (!top || top === c || c.contains(top) || top.contains(c)) continue;
          out.push(nm(top) + ' covers the control "'
            + (c.textContent || c.id || c.type).trim().slice(0, 16) + '"');
        }
        return [...new Set(out)];
      });
      for (const f of covering) if (!hits.includes(f)) hits.push(f);

      const mute = await page.evaluate(() => [...document.querySelectorAll('canvas')]
        .filter(c => c.getBoundingClientRect().width > 0)
        // aria-hidden is a declaration that this canvas is not for the
        // accessibility tree - the home page draws its trails and its bodies
        // on two layers that are one picture, and only one of them is the
        // picture. Demanding a label on a hidden layer would be demanding a
        // second description of the same thing.
        .filter(c => c.getAttribute('aria-hidden') !== 'true')
        .filter(c => !c.getAttribute('role')
                  || !(c.getAttribute('aria-label') || '').trim())
        .map(c => (c.id ? 'canvas#' + c.id : 'canvas') + ' has no role or no label'));
      for (const f of mute) if (!hits.includes(f)) hits.push(f);
      checks++;
      if (hits.length) { failures++; console.log(`  FAIL ${p}.html @${w}: ${hits.slice(0, 6).join('; ')}${hits.length > 6 ? ' …' : ''}`); }
      else console.log(`  ok   ${p}.html @${w}`);
    }
    /* longevity's label rule. A value label is never drawn over its own
       bar: the bar's end is where the value is encoded, and --dim on --moss
       measures 1.30:1, so a number laid across it is simply gone. The
       plotting area reserves a measured gutter (--gut, from setGutter) so
       the label always has room beside the bar rather than on it.

       This is deliberately NOT "no .val overflows its track". That check
       existed, it passed 101/101, and the page was wrong in exactly the way
       it was named for - the label was inside the track and unreadable. A
       label in the gutter is outside the track and correct. Assert the
       thing that broke. */
    {
      await page.goto(base + 'longevity-app.html', { waitUntil: 'load' });
      await page.waitForTimeout(1800);
      const bad = await page.evaluate(() => {
        const out = [];
        const rows = [...document.querySelectorAll('#chart .row')]
          .filter(r => !r.classList.contains('hide'));
        for (const r of rows) {
          const v = r.querySelector('.val');
          if (!v || !v.textContent.trim()) continue;
          const bar = [...r.querySelectorAll('.bar,.bu,.bc,.bg1')]
            .map(e => e.getBoundingClientRect()).filter(b => b.width > 0)
            .sort((a, z) => z.right - a.right)[0];
          if (!bar) continue;
          const vb = v.getBoundingClientRect();
          if (vb.left < bar.right - 1 && vb.right > bar.left + 1)
            out.push('"' + (r.querySelector('.nm') || r).textContent.trim().slice(0, 24)
              + '" value ' + v.textContent.trim() + ' is drawn over its own bar ('
              + Math.round(bar.right - vb.left) + 'px of overlap)');
        }
        if (!rows.length) out.push('no rows rendered: the app did not boot');
        return out.slice(0, 3);
      });
      checks++;
      if (bad.length) { failures++; console.log('  FAIL longevity values @' + w + ': ' + bad.join('; ')); }
      else console.log('  ok   longevity values @' + w + ': no value drawn over its own bar');
    }

    /* climate-cost's label rule, asserted where it can be measured. The app
       nudges a near-edge label inward instead of dropping it, bounded so its
       box still covers its own node's x - position is what says which node a
       label is for, so a label that has left its node's column is wrong
       rather than displaced.

       NOT asserted here, deliberately: "no label is nearer a neighbouring
       node than its own." That was the first metric tried and it reported
       seven offenders; run against the shipped build as a control it
       reported the same for UNNUDGED labels - five of them stages at 390,
       one 5px from a neighbour - because .lab is deliberately lifted off its
       node by nd.r * 46 + 20 and the chain is dense. It measures the design.
       The invariant below is what the code actually promises. */
    if (w === 960 || w === 390) {
      await page.goto(base + 'climate-cost-app.html', { waitUntil: 'load' });
      await page.waitForTimeout(2600);
      const bad = await page.evaluate(() => {
        const L = window.__lca;
        if (!L) return ['__lca missing: the app did not boot'];
        const cv = document.getElementById('gl').getBoundingClientRect();
        const cam = L.camera();
        const out = [];
        for (const l of L.labelPlan(cam, cv.width, cv.height, null, null)) {
          if (!l.node || !l.node.pos) continue;
          const v = l.node.pos.clone().project(cam);
          const sx = (v.x * 0.5 + 0.5) * cv.width;
          if (Math.abs(l.x - sx) > l.w / 2 + 1)
            out.push('label "' + l.text.replace(/<[^>]*>/g, '').trim()
              + '" is ' + Math.round(Math.abs(l.x - sx)) + 'px off its node "'
              + l.node.name + '", past half its ' + Math.round(l.w) + 'px box');
        }
        return out;
      });
      checks++;
      if (bad.length) { failures++; console.log('  FAIL climate-cost labels @' + w + ': ' + bad.join('; ')); }
      else console.log('  ok   climate-cost labels @' + w + ': every label covers its own node');
    }

    // The clipping control. One viewport is enough: the predicate reads
    // declarations, not widths.
    if (w === 1440) {
      for (const [name, expect] of Object.entries(FIXTURES)) {
        await page.goto(base + '_fixture/' + name + '.html', { waitUntil: 'load' });
        await page.waitForTimeout(120);
        const got = await page.evaluate((noExempt) => {
          const out = [];
          for (const el of document.querySelectorAll('body *')) {
            if (getComputedStyle(el).position !== 'fixed') continue;
            const cs = getComputedStyle(el);
            if (!noExempt && cs.whiteSpace === 'nowrap'
                && cs.overflowX === 'hidden'
                && cs.textOverflow === 'ellipsis') continue;
            if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0)
              out.push(el.className);
          }
          return out.sort();
        }, BREAK === 'ellipsis');
        // The expectation does NOT move under --break. That is the whole
        // signal: with the exemption off, .declared joins the reported set,
        // the comparison fails, and the run exits non-zero as a break run
        // must. Widening `want` to match the mutation would make the check
        // pass whether or not the mutation took effect.
        const want = expect.slice().sort();
        checks++;
        if (got.join(',') !== want.join(',')) {
          failures++;
          console.log(`  FAIL fixture ${name}: reported [${got}], wanted [${want}]`);
        } else console.log(`  ok   fixture ${name}: [${got}]`);
      }
    }
    await ctx.close();
  }
  await browser.close();
  srv.close();
  console.log(`\n  ${checks - failures}/${checks} page-viewport combinations free of marginalia collisions, with one left edge, the index to spec, and nothing scrolling sideways`);
  if (BREAK) {
    // trap 26: a break run must FAIL, not print. The mutation here is the
    // exemption being switched off, and the fixture's .declared block is
    // what must start being reported.
    if (failures) console.log('  --break %s: %d check(s) failed, as they must.', BREAK, failures);
    else console.log('  BREAK MODE NOTICED NOTHING - the exemption was disabled and every check still passed.');
    process.exit(failures ? 0 : 1);
  }
  process.exit(failures ? 1 : 0);
})();
