/* The width every figure is SERVED at, measured in a browser.
 *
 * Prints one JSON object on stdout:
 *   {config, rows:[{engine, viewport, page, file, cssWidth, naturalWidth}]}
 *
 * This exists because of trap 22: a figure is drawn at the width it is shown,
 * and the page decides the width. Nothing about a figure's source says what
 * that width is, so the floor cannot be checked anywhere but here.
 *
 * `file` is currentSrc, not the src attribute - a <picture> serves a different
 * file at a narrow viewport, and the served file is the one whose text the
 * reader is looking at. Rows are keyed on DOM position rather than on the
 * file, because keying on the file splits the one image that actually swaps
 * into two rows that never pair.
 *
 * loading="lazy" images below the fold never resolve currentSrc until they are
 * in view. An earlier version awaited img.decode(); in Chromium that never
 * settled for one of them and the run sat for twelve minutes with no output.
 * Loading is forced eager and img.complete is polled with a ceiling instead.
 *
 * Both engines are launched. They have agreed on every row so far - identical
 * CSS widths at both viewports on all 28 figures - and the check that consumes
 * this takes the SMALLEST width reported for a figure, so an engine that ever
 * disagrees makes the gate stricter rather than silently picking a winner.
 *
 *   node tests/fig_served_widths.js
 *   node tests/fig_served_widths.js --matrix   # D-01's nine configurations
 *
 * --matrix measures D-01's matrix instead (DECISIONS D-01): 360x780, 390x844,
 * 768x1024, 1024x768, 1440x900, and 150/200/250/400% zoom of a 1440x900 panel
 * as CSS viewports 960x600, 720x450, 576x360, 360x225 - in Chromium and
 * WebKit, the engines D-01 measured with. tests/test_fig_floor.py reads it for
 * rule 3; each row carries its viewport, so the configuration travels with the
 * number.
 */
const path = require('path');
const fs = require('fs');
const http = require('http');
const pw = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PAGES = ['index', 'about', 'code', 'heat', 'storage', 'climate-cost',
               'longevity', 'skyline', 'continents', 'beauty', 'meter'];
const MATRIX = process.argv.includes('--matrix');
const VIEWPORTS = MATRIX
  ? [[360, 780], [390, 844], [768, 1024], [1024, 768], [1440, 900],
     [960, 600], [720, 450], [576, 360], [360, 225]]
  : [[1440, 900], [390, 844]];
const ENGINES = MATRIX ? ['chromium', 'webkit'] : ['chromium', 'firefox'];
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
               '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml',
               '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.ico': 'image/x-icon',
               '.json': 'application/json' };

function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      fs.readFile(path.join(SITE, u), (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(u)] || 'application/octet-stream' });
        res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const rows = [];
  const engines = [];
  for (const eng of ENGINES) {
    const browser = await pw[eng].launch();
    engines.push(`${eng} ${browser.version()}`);
    for (const [w, h] of VIEWPORTS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      page.setDefaultTimeout(20000);
      for (const p of PAGES) {
        await page.goto(base + p + '.html', { waitUntil: 'load' });
        await page.evaluate(() => {
          for (const i of document.querySelectorAll('main img')) i.loading = 'eager';
          for (let y = 0; y < document.documentElement.scrollHeight; y += 400) window.scrollTo(0, y);
          window.scrollTo(0, 0);
        });
        let ready = false;
        for (let n = 0; n < 40 && !ready; n++) {
          ready = await page.evaluate(() => [...document.querySelectorAll('main img')].every(i => i.complete));
          if (!ready) await page.waitForTimeout(150);
        }
        await page.waitForTimeout(150);
        const got = await page.evaluate(() => [...document.querySelectorAll('main img')].map(i => {
          const r = i.getBoundingClientRect();
          return { file: (i.currentSrc || i.src).split('/').pop().split('?')[0],
                   cssWidth: +r.width.toFixed(2), naturalWidth: i.naturalWidth };
        }));
        for (const g of got) rows.push({ engine: eng, viewport: `${w}x${h}`, page: p, ...g });
      }
      await ctx.close();
    }
    await browser.close();
  }
  srv.close();
  process.stdout.write(JSON.stringify({
    config: { playwright: require('playwright/package.json').version,
              engines, deviceScaleFactor: 1,
              viewports: VIEWPORTS.map(v => v.join('x')) },
    rows }, null, 1));
})();
