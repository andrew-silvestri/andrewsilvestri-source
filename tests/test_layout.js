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
const PAGES = ['index', 'about', 'atlas', 'model', 'library', 'code', 'heat', 'storage', 'climate-cost', 'longevity', 'skyline', 'food', 'neuron', 'economy', 'shoes', 'continents'];   // desktop retired 2026-09-05; about added 2026-09-07
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
const VIEWPORTS = [[1920, 1080], [1440, 900], [1366, 768], [1280, 800], [1024, 768], [960, 720], [390, 844]];
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.ico': 'image/x-icon' };

function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const f = path.join(SITE, decodeURIComponent(req.url.split('?')[0]));
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
    for (const p of PAGES) {
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
      const fits = await page.evaluate(() => {
        const out = [];
        for (const el of document.querySelectorAll('body *')) {
          if (getComputedStyle(el).position !== 'fixed') continue;
          const r = el.getBoundingClientRect();
          if (!r.width || !r.height) continue;
          const name = el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '');
          for (const n of [el, ...el.querySelectorAll('*')]) {
            if (n.scrollWidth > n.clientWidth + 1 && n.clientWidth > 0) {
              out.push(`fixed block ${name} is too narrow for its text: `
                + `${n.tagName.toLowerCase()} needs ${n.scrollWidth}px in ${n.clientWidth}px `
                + `"${(n.textContent || '').trim().slice(0, 30)}"`);
              break;
            }
          }
        }
        return out;
      });
      for (const f of fits) if (!hits.includes(f)) hits.push(f);
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
      checks++;
      if (hits.length) { failures++; console.log(`  FAIL ${p}.html @${w}: ${hits.slice(0, 6).join('; ')}${hits.length > 6 ? ' …' : ''}`); }
      else console.log(`  ok   ${p}.html @${w}`);
    }
    await ctx.close();
  }
  await browser.close();
  srv.close();
  console.log(`\n  ${checks - failures}/${checks} page-viewport combinations free of marginalia collisions, with one left edge, the index to spec`);
  process.exit(failures ? 1 : 0);
})();
