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
 * Needs playwright (npm install in tests/), and the Chromium it installs.
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PAGES = ['index', 'atlas', 'model', 'library', 'code', 'heat', 'storage', 'climate-cost', 'longevity', 'skyline', 'desktop'];
// 1920 is here because "New York" wrapping to a line of its own in a 192px
// gutter was read as clipping (2026-09-04); the test now also fails on real
// clipping - any marginalia element wider than its box - so the two cannot
// be confused again.
const VIEWPORTS = [[1920, 1080], [1440, 900], [1024, 768], [390, 844]];
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
      checks++;
      if (hits.length) { failures++; console.log(`  FAIL ${p}.html @${w}: ${hits.slice(0, 6).join('; ')}${hits.length > 6 ? ' …' : ''}`); }
      else console.log(`  ok   ${p}.html @${w}`);
    }
    await ctx.close();
  }
  await browser.close();
  srv.close();
  console.log(`\n  ${checks - failures}/${checks} page-viewport combinations free of marginalia collisions`);
  process.exit(failures ? 1 : 0);
})();
