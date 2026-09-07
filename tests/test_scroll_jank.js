/* Does the home page stay smooth while you scroll it?
 *
 *   node tests/test_scroll_jank.js            # the three pins, 1440 and 390
 *   node tests/test_scroll_jank.js --break    # trap 17: prove it sees jank
 *   node tests/test_scroll_jank.js --dsf 1    # override the device ratio
 *
 * WHY THIS EXISTS. _deslop/measure.js reports idle CPU on a page nobody is
 * touching, and every gate this project has was green while the live site was
 * visibly janky to scroll. Idle cost and scroll cost are different questions:
 * a fixed full-viewport canvas repainting under a scrolling opaque column
 * costs nothing extra when still and can miss every frame when moving. So this
 * drives a real wheel scroll and records what the frames actually did.
 *
 * AND IT RUNS AT THE DISPLAY'S DEVICE RATIO, WHICH IS THE OTHER HALF OF THE
 * SAME MISTAKE. Playwright defaults to deviceScaleFactor 1, and every earlier
 * measurement took that default - so hero.js's TRAIL_DPR, which is
 * Math.min(devicePixelRatio, 2), was clamped to 1 in the harness and could
 * never show a cost. The back canvas measured 1.3 megapixels there and is 5.18
 * on the 3840x2400 panel this was written on. A canvas benchmark at the wrong
 * device ratio is not a benchmark of the canvas.
 *
 * WHAT IT REPORTS, per pin and viewport:
 *   worst    the longest single frame during the scroll, in ms
 *   p95      the 95th-percentile frame, which is what "feels" janky
 *   dropped  frames longer than 25ms, i.e. more than 1.5 frames at 60Hz
 *   longtask total ms of main-thread tasks over 50ms, from PerformanceObserver
 *
 * A 60Hz frame is 16.7ms. Anything at or under ~20ms p95 reads as smooth.
 */

'use strict';
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PINS = ['pendulum', 'lorenz', 'threebody'];
/* 1920x1200 is this machine maximised: a 3840x2400 panel at 200% scaling. It
   is here because 1440x900 was the only desktop size ever measured and it
   understates the canvas by 78% - 5.18 megapixels against 9.22. The size a
   reader actually has is the size to measure. */
const VIEWPORTS = [[1920, 1200], [1440, 900], [390, 844]];
const FRAME_MS = 1000 / 60;
const DROP_MS = FRAME_MS * 1.5;          // >1.5 frames: a visible hitch
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const DSF = parseFloat(arg('--dsf', '2'));
/* --real drives the INSTALLED Chrome, headed, with the GPU. Headless Chromium
   composites in software, so a fixed canvas under a scrolling opaque layer
   costs something there that has little to do with what a reader's machine
   does - and this whole file exists because a measurement taken in the wrong
   configuration is worse than none. Use --real for any number you intend to
   act on; the headless default is for CI, where it is at least consistent. */
const REAL = process.argv.includes('--real');

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

/* Recording runs in the page: a rAF loop for cadence and a PerformanceObserver
   for long tasks. The rAF callback is one extra callback a frame and costs
   nothing measurable; it is also the only way to see the cadence the reader
   sees, because CDP's task durations do not tell you which frames were late. */
const START = () => {
  window.__j = { f: [], tasks: [], raf: 0 };
  try {
    new PerformanceObserver(l => { for (const e of l.getEntries()) window.__j.tasks.push(e.duration); })
      .observe({ entryTypes: ['longtask'] });
  } catch (e) { /* not every build exposes longtask */ }
  let last = performance.now();
  (function step() {
    const n = performance.now();
    window.__j.f.push(n - last);
    last = n;
    window.__j.raf = requestAnimationFrame(step);
  })();
};

const STOP = () => {
  cancelAnimationFrame(window.__j.raf);
  const f = window.__j.f.slice(1);          // the first delta spans the setup
  const sorted = [...f].sort((a, b) => a - b);
  const pct = q => sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * q))] : 0;
  return {
    n: f.length,
    worst: f.length ? Math.max(...f) : 0,
    p95: pct(0.95),
    median: pct(0.5),
    dropped: f.filter(d => d > 25).length,
    longtask: Math.round(window.__j.tasks.reduce((a, b) => a + b, 0)),
    docH: document.documentElement.scrollHeight,
    canvasPx: (() => { const c = document.querySelector('#hero canvas'); return c ? c.width * c.height : 0; })()
  };
};

async function measure(page, heavy) {
  await page.evaluate(START);
  if (heavy) {
    /* trap 17: a deliberately janky page, to prove the check can see jank.
       A 30ms synchronous block every frame cannot be hidden by any amount of
       compositing - if this does not show, the harness is not measuring. */
    await page.evaluate(() => {
      window.__heavy = setInterval(() => {
        const t = performance.now();
        while (performance.now() - t < 30) { /* burn */ }
      }, 16);
    });
  }
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  const vh = page.viewportSize().height;
  await page.mouse.move(page.viewportSize().width / 2, vh / 2);
  /* --flick delivers wheel events back to back, which is what a trackpad
     throw does; the metered default leaves 24ms of idle between them and that
     is enough for the browser to finish a frame it would otherwise miss. */
  const FLICK = process.argv.includes('--flick');
  const step = FLICK ? 300 : 120, gap = FLICK ? 0 : 24;
  for (let y = 0; y < Math.min(H - vh, vh * 6); y += step) {
    await page.mouse.wheel(0, step);
    if (gap) await page.waitForTimeout(gap);
  }
  const r = await page.evaluate(STOP);
  if (heavy) await page.evaluate(() => clearInterval(window.__heavy));
  return r;
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = REAL
    ? await chromium.launch({ channel: 'chrome', headless: false,
        args: ['--force-device-scale-factor=' + DSF, '--start-maximized'] })
    : await chromium.launch();
  const breaking = process.argv.includes('--break');
  let failures = 0;

  console.log(`\nScroll jank on index.html - deviceScaleFactor ${DSF}, ${FRAME_MS.toFixed(1)}ms budget\n`);
  console.log('  pin        viewport     frames  median    p95   worst  dropped  longtask  canvasMP');

  const rows = [];
  for (const [w, h] of VIEWPORTS) {
    for (const pin of (breaking ? ['pendulum'] : PINS)) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: DSF });
      const page = await ctx.newPage();
      await page.goto(base + 'index.html?hero=' + pin, { waitUntil: 'load' });
      await page.waitForTimeout(2000);
      const r = await measure(page, false);
      rows.push({ pin, w, h, r });
      console.log(`  ${pin.padEnd(10)} ${(w + 'x' + h).padEnd(11)} ${String(r.n).padStart(6)} ${r.median.toFixed(1).padStart(7)} ${r.p95.toFixed(1).padStart(6)} ${r.worst.toFixed(1).padStart(7)} ${String(r.dropped).padStart(8)} ${String(r.longtask).padStart(9)} ${(r.canvasPx / 1e6).toFixed(2).padStart(9)}`);

      if (breaking) {
        const bad = await measure(page, true);
        console.log(`  ${'(heavy)'.padEnd(10)} ${(w + 'x' + h).padEnd(11)} ${String(bad.n).padStart(6)} ${bad.median.toFixed(1).padStart(7)} ${bad.p95.toFixed(1).padStart(6)} ${bad.worst.toFixed(1).padStart(7)} ${String(bad.dropped).padStart(8)} ${String(bad.longtask).padStart(9)}`);
        const seen = bad.p95 > r.p95 * 1.5 && bad.dropped > r.dropped;
        if (!seen) failures++;
        console.log(`  ${seen ? 'ok  ' : 'FAIL'} the check separates a janky page from this one\n`);
      }
      await ctx.close();
    }
  }

  if (!breaking) {
    const worstP95 = Math.max(...rows.map(r => r.r.p95));
    const anyDropped = rows.reduce((a, r) => a + r.r.dropped, 0);
    console.log(`\n  worst p95 across all six runs: ${worstP95.toFixed(1)}ms; ${anyDropped} dropped frames in total`);
    console.log(`  (a 60Hz frame is ${FRAME_MS.toFixed(1)}ms; p95 at or under ~20ms reads as smooth)`);
  }

  await browser.close();
  srv.close();
  process.exit(failures ? 1 : 0);
})();
