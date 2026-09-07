/* Does the home page stay smooth while you scroll it, AND DOES THAT CHANGE AS
 * THE ANIMATION RUNS?
 *
 *   node tests/test_scroll_jank.js                  # the curve, both viewports
 *   node tests/test_scroll_jank.js --vp 1920        # one viewport
 *   node tests/test_scroll_jank.js --long           # the three-body's late phases
 *   node tests/test_scroll_jank.js --break          # trap 17: prove it sees jank
 *   node tests/test_scroll_jank.js --real           # installed Chrome, GPU
 *   node tests/test_scroll_jank.js --dsf 1          # override the device ratio
 *
 * WHY THIS EXISTS. _deslop/measure.js reports idle CPU on a page nobody is
 * touching, and every gate this project had was green while the live site was
 * visibly janky to scroll.
 *
 * WHY IT MEASURES A CURVE. The first version of this file scrolled immediately
 * after load, so it measured the animation at t=0 and reported "smooth". Cost
 * here is TIME-DEPENDENT and t=0 is its cheapest point:
 *
 *   - The three pendulums are released 0.001 rad apart. For about five seconds
 *     they are superimposed: three short near-identical arcs in one small
 *     region. By thirty seconds they are 17 rad apart, sweeping three separate
 *     trajectories across the whole canvas. The stroke COUNT is unchanged -
 *     and stroke count is the cost driver established on 2026-09-07 - but the
 *     strokes are far longer and the locality is far worse.
 *   - The three-body's adaptive stepper subdivides hardest at close approaches,
 *     and the binary forms late: t = 61.4 system time, about 205s of wall clock
 *     at RATE 0.30. An early scroll sees the easy opening geometry and never
 *     the step-count peak.
 *   - The reseed ramp is 1.6s roughly every 205s, and had never been measured.
 *
 * So: a settle before each scroll, buckets across elapsed time, and the
 * elapsed time printed beside every row. That is trap 24 one step along - the
 * measurement inherited a default nobody chose, and that time the default was
 * WHEN. Print the configuration beside the number, and the clock is part of
 * the configuration.
 *
 * DEVICE RATIO. Playwright defaults to deviceScaleFactor 1; every measurement
 * in this project took that default until 2026-09-07, so hero.js's TRAIL_DPR,
 * Math.min(devicePixelRatio, 2), was clamped to 1 in the very runs meant to
 * test it. The default here is 2. HANDOFF section 8, trap 24.
 *
 * REPORTED per pin, viewport and bucket: median, p95, worst frame, and frames
 * over 25ms. A 60Hz frame is 16.7ms; p95 at or under ~20ms reads as smooth.
 */

'use strict';
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');

const SITE = path.join(__dirname, '..', 'site');
const PINS = ['pendulum', 'lorenz', 'threebody'];
const FRAME_MS = 1000 / 60;
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const has = k => process.argv.includes(k);
const DSF = parseFloat(arg('--dsf', '2'));
const REAL = has('--real');
const LONG = has('--long');
const BREAK = has('--break');
const ONLY_VP = arg('--vp', null);
const ONLY_PIN = arg('--pin', null);
const ONLY_B = arg('--buckets', null);

/* Seconds of elapsed animation. 0 is the superimposed pendulums and the easy
   opening three-body geometry; 30 is well past the divergence; 60 is steady. */
const BUCKETS = BREAK ? [0] : (ONLY_B ? ONLY_B.split(",").map(Number) : [0, 10, 30, 60]);
/* 150 and 195 straddle the tightening binary, where the adaptive stepper
   subdivides hardest; 206 lands on the reseed ramp. */
const LONG_BUCKETS = [150, 195, 206];

/* 1920x1200 is this machine maximised: a 3840x2400 panel at 200% scaling.
   1440x900 was the only desktop size measured before 2026-09-07 and it
   understates the canvas by 78% - 5.18 megapixels against 9.22. */
let VIEWPORTS = [[1920, 1200], [390, 844]];
if (ONLY_VP) VIEWPORTS = VIEWPORTS.filter(v => String(v[0]) === ONLY_VP);

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
  const f = window.__j.f.slice(1);
  const sorted = [...f].sort((a, b) => a - b);
  const pct = q => sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * q))] : 0;
  return {
    n: f.length,
    worst: f.length ? Math.max(...f) : 0,
    p95: pct(0.95), median: pct(0.5),
    dropped: f.filter(d => d > 25).length,
    longtask: Math.round(window.__j.tasks.reduce((a, b) => a + b, 0))
  };
};

async function scrollMeasure(page, heavy) {
  /* Chrome throttles requestAnimationFrame to 1Hz in a window that is not
     frontmost, and --real opens a headed window per context, so whichever one
     is behind reports a ~1000ms median and 40-odd "dropped" frames that have
     nothing to do with the page. It is intermittent, which is worse than
     consistent - it contaminated a run on 2026-09-07 and would have been read
     as a catastrophic regression. Raise the window, then assert the cadence is
     sane before believing anything the run says. */
  await page.bringToFront();
  await page.waitForTimeout(150);
  await page.evaluate(START);
  if (heavy) {
    /* trap 17: a deliberately janky page, to prove the check can see jank. A
       30ms synchronous block every frame cannot be hidden by any amount of
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
  for (let y = 0; y < Math.min(H - vh, vh * 5); y += 120) {
    await page.mouse.wheel(0, 120);
    await page.waitForTimeout(20);
  }
  const r = await page.evaluate(STOP);
  if (heavy) await page.evaluate(() => clearInterval(window.__heavy));
  /* A median anywhere near 1000ms is the throttle above, not the page. Fail
     loudly rather than reporting it as a measurement. */
  r.throttled = !heavy && r.median > 100;
  /* Back to the top between buckets, and not only for a consistent start:
     below the 960 breakpoint hero.js pauses the loop once the band is off
     screen, so a page left scrolled down is a page whose animation clock has
     stopped. The buckets are elapsed ANIMATION time, so it has to be running. */
  await page.evaluate(() => scrollTo(0, 0));
  await page.waitForTimeout(400);
  return r;
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = REAL
    ? await chromium.launch({ channel: 'chrome', headless: false,
        args: ['--force-device-scale-factor=' + DSF] })
    : await chromium.launch();
  let failures = 0;

  console.log(`\nScroll jank across elapsed time - ${REAL ? 'INSTALLED Chrome, GPU' : 'headless Chromium, software'}, `
            + `deviceScaleFactor ${DSF}, ${FRAME_MS.toFixed(1)}ms budget`);
  console.log('  pin        viewport      t=s  frames  median    p95   worst  >25ms  canvasMP\n');

  const jobs = [];
  for (const [w, h] of VIEWPORTS)
    for (const pin of (BREAK ? ['pendulum'] : (ONLY_PIN ? [ONLY_PIN] : PINS)))
      jobs.push({ w, h, pin, buckets: BUCKETS });
  if (LONG) jobs.push({ w: 1920, h: 1200, pin: 'threebody', buckets: LONG_BUCKETS });

  const rows = [];
  for (const job of jobs) {
    const ctx = await browser.newContext({ viewport: { width: job.w, height: job.h }, deviceScaleFactor: DSF });
    const page = await ctx.newPage();
    await page.goto(base + 'index.html?hero=' + job.pin, { waitUntil: 'load' });
    await page.waitForFunction(() => document.body.classList.contains('hero-live'));
    const t0 = Date.now();
    const mp = await page.evaluate(() => { const c = document.querySelector('#hero canvas'); return c ? c.width * c.height / 1e6 : 0; });

    for (const b of job.buckets) {
      const wait = t0 + b * 1000 - Date.now();
      if (wait > 0) await page.waitForTimeout(wait);
      const elapsed = Math.round((Date.now() - t0) / 1000);
      const r = await scrollMeasure(page, false);
      rows.push({ pin: job.pin, w: job.w, b, r });
      console.log(`  ${job.pin.padEnd(10)} ${(job.w + 'x' + job.h).padEnd(11)} ${String(elapsed).padStart(4)} ${String(r.n).padStart(7)} ${r.median.toFixed(1).padStart(7)} ${r.p95.toFixed(1).padStart(6)} ${r.worst.toFixed(1).padStart(7)} ${String(r.dropped).padStart(6)} ${mp.toFixed(2).padStart(9)}`);
      if (r.throttled) { failures++; console.log('  FAIL  that row is a throttled window, not a measurement - rerun'); }

      if (BREAK) {
        const bad = await scrollMeasure(page, true);
        console.log(`  ${'(heavy)'.padEnd(10)} ${(job.w + 'x' + job.h).padEnd(11)} ${String(elapsed).padStart(4)} ${String(bad.n).padStart(7)} ${bad.median.toFixed(1).padStart(7)} ${bad.p95.toFixed(1).padStart(6)} ${bad.worst.toFixed(1).padStart(7)} ${String(bad.dropped).padStart(6)}`);
        const seen = bad.p95 > r.p95 * 1.5 && bad.dropped > r.dropped;
        if (!seen) failures++;
        console.log(`  ${seen ? 'ok  ' : 'FAIL'} the check separates a janky page from this one`);
      }
    }
    console.log('');
    await ctx.close();
  }

  if (!BREAK) {
    console.log('  worst p95 per elapsed bucket, across pins and viewports:');
    const byB = {};
    for (const r of rows) byB[r.b] = Math.max(byB[r.b] || 0, r.r.p95);
    for (const b of Object.keys(byB).sort((a, c) => a - c))
      console.log(`    t = ${String(b).padStart(3)}s   ${byB[b].toFixed(1)}ms`);
    console.log(`\n  total frames over 25ms: ${rows.reduce((a, r) => a + r.r.dropped, 0)}`);
  }

  await browser.close();
  srv.close();
  process.exit(failures ? 1 : 0);
})();
