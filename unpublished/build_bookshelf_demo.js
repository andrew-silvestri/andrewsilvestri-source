/* The bookshelf's demo wallpaper, rendered by the app itself.
 *
 * The home-page card for the bookshelf showed a screenshot of the tool - its
 * control panel legible down the left edge - rather than the wallpaper the
 * tool produces (Phase 4, A2, 2026-09-04). A card should show the thing that
 * is made, not the thing that makes it. This opens site/bookshelf-app.html
 * headless at a 1920x1080 screen, lets it draw its built-in demo shelf (44
 * public books), and saves the canvas as bookshelf/demo-wallpaper.png, which
 * build_thumbnails.py then thumbnails for the card. The wallpaper itself is
 * not shipped; only the 542px thumbnail is.
 *
 *   node build_bookshelf_demo.js
 *
 * Needs the playwright under tests/node_modules (npm install in tests/).
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require(path.join(__dirname, '..', 'tests', 'node_modules', 'playwright'));

const SITE = __dirname;   // retired 2026-09-05: serves unpublished/, where the app now lives
const OUT = path.join(__dirname, '..', 'bookshelf', 'demo-wallpaper.png');
const W = 1920, H = 1080;   // the commonest screen; the app sizes the canvas to the screen
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.otf': 'font/otf' };

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
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(base + 'bookshelf-app.html', { waitUntil: 'load' });
  await page.waitForFunction(() => document.fonts.status === 'loaded');
  await page.waitForTimeout(800);   // the shelf draws after the fonts arrive
  const info = await page.evaluate(() => {
    const c = document.getElementById('cv');
    return { w: c.width, h: c.height, stats: document.getElementById('stats').textContent };
  });
  if (errors.length) { console.error('page errors:', errors.join('; ')); process.exit(1); }
  if (info.w !== W || info.h !== H) { console.error(`canvas is ${info.w}x${info.h}, expected ${W}x${H}`); process.exit(1); }
  if (!/demo shelf/.test(info.stats)) { console.error('the app is not showing the demo shelf: ' + info.stats); process.exit(1); }
  const data = await page.evaluate(() => document.getElementById('cv').toDataURL('image/png'));
  fs.writeFileSync(OUT, Buffer.from(data.split(',')[1], 'base64'));
  console.log(`  wrote ${path.relative(__dirname, OUT)}  ${info.w}x${info.h}  ${(fs.statSync(OUT).size / 1024) | 0} KB  (${info.stats.trim()})`);
  await browser.close();
  srv.close();
})();
