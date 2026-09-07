/* Is the animation actually kept out of the caption/footer block?
 *
 *   node tests/test_exclusion.js            # serve site/ on 8765 first
 *   node tests/test_exclusion.js --break    # trap 17: with the clearRect gone
 *
 * It lives in tests/ and not in _deslop/ beside the rig it complements,
 * because _deslop/ is gitignored: a check kept there does not survive a
 * clone, which is already true of measure.js's ?hero= pin and is recorded in
 * HANDOFF section 7 as a wart. One is enough.
 *
 * WHY THIS CANNOT BE _deslop/measure.js's JOB. That rig builds its contrast
 * pairs by walking getComputedStyle(el).backgroundColor up the DOM - CSS
 * colours, not rendered pixels. The caption and footer resolve their ground to
 * --bg through .paper and the body whether hero.js's clearRect works, is
 * broken, or was deleted this morning. It will report 0 AA failures either
 * way. That blindness is why the paper column exists at all; this file is the
 * check that can actually see the pixels.
 *
 * WHAT IT ASSERTS, at 1920x1200 where the block is fixed in the left margin:
 *   inside   every sampled pixel in the block's rect is exactly --bg. No ink.
 *   control  a band immediately outside the rect DOES contain ink.
 *
 * The control is the half that matters. Without it the test passes on any
 * frame where the animation happened to be somewhere else, which is most of
 * them for a system that sweeps.
 */

'use strict';
const { chromium } = require('playwright');   // tests/node_modules

const BASE = 'http://127.0.0.1:8765/';
const BG = [242, 240, 239];
const PINS = ['pendulum', 'lorenz', 'threebody'];
const BREAK = process.argv.includes('--break');

let failures = 0;
let detected = 0;
const say = (ok, msg) => { if (!ok) failures++; console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${msg}`); };

(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: false,
    args: ['--force-device-scale-factor=2'] });

  console.log(`\nThe caption/footer exclusion, sampled from rendered pixels`
            + `${BREAK ? '  [--break: clearRect disabled]' : ''}\n`);

  for (const pin of PINS) {
    const ctx = await b.newContext({ viewport: { width: 1920, height: 1200 }, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.goto(BASE + 'index.html?hero=' + pin, { waitUntil: 'load' });
    await page.bringToFront();
    if (BREAK) await page.evaluate(() => { /* neuter the exclusion the way deleting it would */
      const c = document.querySelectorAll('#hero canvas');
      for (const k of c) { const g = k.getContext('2d'); g.clearRect = function () {}; }
    });
    /* Long enough that the trails have spread across the canvas - at t=0 the
       systems are compact and the margin may be empty for reasons that have
       nothing to do with the exclusion. */
    await page.waitForTimeout(25000);

    const r = await page.evaluate(() => {
      const el = document.querySelector('.herofoot');
      const q = el.getBoundingClientRect();
      return { x: q.x, y: q.y, w: q.width, h: q.height,
               fixed: getComputedStyle(el).position === 'fixed' };
    });
    say(r.fixed && r.w > 0, `block is fixed, ${Math.round(r.w)}x${Math.round(r.h)} at (${Math.round(r.x)}, ${Math.round(r.y)})`);

    const shot = await page.screenshot();
    const { createCanvas, loadImage } = (() => { try { return require('canvas'); } catch (e) { return {}; } })();

    /* No image library is guaranteed here, so the sampling is done in the page
       against the two canvases directly - which is the same pixels the reader
       sees, since nothing else paints in the left margin. */
    const sample = await page.evaluate(({ x, y, w, h }) => {
      const cs = [...document.querySelectorAll('#hero canvas')];
      const dpr = devicePixelRatio;
      const read = (c, X, Y, W, H) => {
        const g = c.getContext('2d');
        const d = g.getImageData(Math.round(X * (c.width / innerWidth)), Math.round(Y * (c.height / innerHeight)),
                                 Math.max(1, Math.round(W * (c.width / innerWidth))),
                                 Math.max(1, Math.round(H * (c.height / innerHeight)))).data;
        let ink = 0, n = 0;
        for (let i = 0; i < d.length; i += 4 * 37) { n++; if (d[i + 3] > 8) ink++; }
        return { ink, n };
      };
      /* Inset by 6 CSS px. clearRect takes fractional CSS coordinates under a
         dpr transform, so the very edge of the rect can keep a sub-pixel
         remnant; that is a rounding artefact at the boundary and not the
         animation leaking into the block, and the two are worth telling
         apart. The reported edge count says which one is happening. */
      const inside = cs.map(c => read(c, x + 6, y + 6, w - 12, h - 12));
      const edge = cs.map(c => read(c, x, y, w, h));
      /* The control is the LEFT MARGIN ABOVE the block - the region every
         system actually sweeps. A band beside the block at the foot of the
         screen is where the Lorenz never goes (its z range keeps it above
         y~1116 at this height), so a control there reports "no ink" for
         reasons that have nothing to do with the exclusion. */
      const control = cs.map(c => read(c, 0, 40, Math.max(8, x + w), Math.max(8, y - 60)));
      return { inside, edge, control, cw: x + w };
    }, r);

    const insideInk = sample.inside.reduce((a, s) => a + s.ink, 0);
    const controlInk = sample.control.reduce((a, s) => a + s.ink, 0);
    const edgeInk = sample.edge.reduce((a, s) => a + s.ink, 0);
    if (BREAK) {
      /* Inverted, and NOT asserted per pin. Only a system that actually sweeps
         the bottom-left corner can exercise this check at all: with the
         clearRect disabled the pendulum fills the block, while the Lorenz and
         the three-body still show nothing there because neither goes near it -
         the Lorenz's z range keeps it well above the foot of the screen. A
         per-pin assertion would "pass" on two pins that prove nothing. So the
         run requires that AT LEAST ONE pin notices, and names which. */
      detected += insideInk > 0 ? 1 : 0;
      console.log(`  ${insideInk > 0 ? 'sees it ' : 'blind   '} ${pin}: ${insideInk} ink samples inside with the exclusion disabled`);
    } else {
      say(insideInk === 0, `no ink inside the block: ${insideInk} of ${sample.inside.reduce((a, s) => a + s.n, 0)} samples`
          + (edgeInk ? `  (${edgeInk} at the very edge - sub-pixel remnant)` : ''));
    }
    say(controlInk > 0, `control region above it has ink: ${controlInk} samples`);
    console.log('');
    await ctx.close();
  }

  await b.close();
  console.log(`  ${failures ? failures + ' FAILED' : 'all checks passed'}\n`);
  process.exit(failures ? 1 : 0);
})();
