/* Is the caption/footer panel's ground actually opaque?
 *
 *   node tests/test_panel.js            # serve is built in
 *   node tests/test_panel.js --break    # trap 17: with the background removed
 *
 * It replaces tests/test_exclusion.js, which asked the same question of a
 * different mechanism. Until 2026-09-07 the block had no background of its own
 * and hero.js cleared its rectangle out of both canvases every frame; the
 * check that could see that was one that sampled the canvases directly. The
 * block now carries background: var(--bg) and the clearRect is gone, so the
 * thing to verify is not "is the canvas empty there" but "does the canvas
 * reach the reader there at all".
 *
 * WHY _deslop/measure.js STILL CANNOT DO THIS. That rig builds its contrast
 * pairs by walking getComputedStyle(el).backgroundColor up the DOM - CSS
 * colours, not rendered pixels. It reported 0 AA failures for this block when
 * the block had no background and the text sat over a live canvas, and it will
 * report 0 AA failures if the background declaration is deleted tomorrow. The
 * declaration being present in the cascade is exactly what that rig assumes
 * rather than checks.
 *
 * WHAT IT ASSERTS, at 1728x1080 dpr 2.2222 where the block is fixed in the
 * left margin:
 *
 *   opaque   the panel's rendered pixels are IDENTICAL with the hero canvases
 *            showing and with them hidden. An opaque ground cannot let what is
 *            behind it change what is in front of it. This needs no colour
 *            constant and no tolerance: it is an identity, not a threshold.
 *   control  a band immediately above the panel is NOT identical between those
 *            two states. Without it the opacity check passes on any frame
 *            where the animation happened to be elsewhere, which is most of
 *            them for a system that sweeps.
 *   seam     scrolled past the fold, the panel's right border and .paper's
 *            border-left land on the same pixel column and paint ONE hairline.
 *            They are one CSS pixel apart by default and paint two.
 *
 * The panel is opaque, so the images are compared after decoding rather than
 * by hashing the PNG bytes: an encoder that is not bit-deterministic would
 * fail a test about pixels for a reason that has nothing to do with pixels.
 * Decoding happens in the page, because no image library is guaranteed here.
 */

'use strict';
const path = require('path');
const fs = require('fs');
const http = require('http');
const { firefox } = require('playwright');   // tests/node_modules

const SITE = path.join(__dirname, '..', 'site');
const PINS = ['pendulum', 'lorenz', 'threebody'];
const BREAK = process.argv.includes('--break');
const DSF = 2.2222;
const VW = 1728, VH = 1080;
/* Long enough that the trails have spread across the canvas - at t=0 the
   systems are compact and the margin may be empty for reasons that have
   nothing to do with the panel. Same 25s tests/test_exclusion.js used. */
const SETTLE = 25000;
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

let failures = 0;
let detected = 0;
const say = (ok, msg) => { if (!ok) failures++; console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${msg}`); };

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

/* Both PNGs are handed to the page as data URLs and diffed on a canvas there.
   Returns the count of pixels differing by more than 2 in any channel - 2
   rather than 0 because a screenshot of a composited page is not obliged to
   round subpixel coverage the same way twice, and one stray unit of blue is
   not the animation showing through. */
const DIFF = async ([a, b]) => {
  const load = s => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = s; });
  const [ia, ib] = await Promise.all([load(a), load(b)]);
  if (ia.width !== ib.width || ia.height !== ib.height) return { n: -1, total: 0 };
  const c = document.createElement('canvas');
  c.width = ia.width; c.height = ia.height;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(ia, 0, 0);
  const da = g.getImageData(0, 0, c.width, c.height).data;
  g.clearRect(0, 0, c.width, c.height);
  g.drawImage(ib, 0, 0);
  const db = g.getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 0; i < da.length; i += 4) {
    if (Math.abs(da[i] - db[i]) > 2 || Math.abs(da[i + 1] - db[i + 1]) > 2 || Math.abs(da[i + 2] - db[i + 2]) > 2) n++;
  }
  return { n, total: da.length / 4 };
};

const b64 = buf => 'data:image/png;base64,' + buf.toString('base64');

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/index.html?hero=`;
  const browser = await firefox.launch();

  console.log(`\n  The caption/footer panel's ground, from rendered pixels`
            + `${BREAK ? '  [--break: background removed]' : ''}`);
  console.log(`  Playwright Firefox ${browser.version()}, ${VW}x${VH}, deviceScaleFactor ${DSF}\n`);

  for (const pin of PINS) {
    const ctx = await browser.newContext({ viewport: { width: VW, height: VH }, deviceScaleFactor: DSF });
    const page = await ctx.newPage();
    await page.goto(base + pin, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    if (BREAK) await page.evaluate(() => {   /* neuter the panel the way deleting the declaration would */
      document.querySelector('.herofoot').style.background = 'transparent';
    });
    await page.waitForTimeout(SETTLE);

    const r = await page.evaluate(() => {
      const el = document.querySelector('.herofoot');
      const q = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return { x: q.x, y: q.y, w: q.width, h: q.height, fixed: cs.position === 'fixed',
               bg: cs.backgroundColor, bt: cs.borderTopWidth, br: cs.borderRightWidth };
    });
    say(r.fixed && r.w > 0,
      `block is fixed, ${Math.round(r.w)}x${Math.round(r.h)} at (${Math.round(r.x)}, ${Math.round(r.y)}), `
      + `background ${r.bg}, borders ${r.bt}/${r.br}`);

    /* INSET BY 1 CSS PIXEL FOR THE ASSERTION, and the full rect reported beside
       it. The block is bottom-anchored and its height is fractional (219.5px at
       1728, because the line boxes are), so its top edge lands at y = 860.5 and
       at deviceScaleFactor 2.2222 that is device row 1912.2 - the clip's first
       row is about four fifths of the panel's top border and one fifth of
       whatever is above it. Measured 2026-09-07: the un-inset rect differs in
       106 of 512811 pixels, ALL of them on row 0, over the x range the pendulum
       sweeps. That is the boundary blend, not the animation reaching the
       reader, and the two are worth telling apart - so the assertion is on the
       inset and the edge figure is printed. */
    const panel = { x: r.x, y: r.y, width: r.w, height: r.h };
    const inner = { x: r.x, y: r.y + 1, width: r.w - 1, height: r.h - 2 };
    /* The control is the LEFT MARGIN ABOVE the block - the region every system
       actually sweeps. A band beside the block at the foot of the screen is
       where the Lorenz never goes, so a control there reports "no change" for
       reasons that have nothing to do with the panel. */
    const control = { x: 0, y: 40, width: Math.max(8, r.x + r.w), height: Math.max(8, r.y - 60) };

    const withCanvas = { panel: await page.screenshot({ clip: inner }),
                         edge: await page.screenshot({ clip: panel }),
                         control: await page.screenshot({ clip: control }) };
    await page.evaluate(() => { document.querySelector('#hero').style.display = 'none'; });
    await page.waitForTimeout(120);
    const without = { panel: await page.screenshot({ clip: inner }),
                      edge: await page.screenshot({ clip: panel }),
                      control: await page.screenshot({ clip: control }) };
    await page.evaluate(() => { document.querySelector('#hero').style.display = ''; });

    const dPanel = await page.evaluate(DIFF, [b64(withCanvas.panel), b64(without.panel)]);
    const dEdge = await page.evaluate(DIFF, [b64(withCanvas.edge), b64(without.edge)]);
    const dCtl = await page.evaluate(DIFF, [b64(withCanvas.control), b64(without.control)]);

    if (BREAK) {
      /* Inverted, and NOT asserted per pin. Only a system that actually sweeps
         the bottom-left corner can exercise this check at all: with the
         background removed the pendulum shows through, while the Lorenz and
         the three-body may not go near it. A per-pin assertion would "pass" on
         two pins that prove nothing. So the run requires that AT LEAST ONE pin
         notices, and names which. */
      detected += dPanel.n > 0 ? 1 : 0;
      console.log(`  ${dPanel.n > 0 ? 'sees it ' : 'blind   '} ${pin}: ${dPanel.n} of ${dPanel.total} panel pixels change when the canvas is hidden`);
    } else {
      say(dPanel.n === 0, `panel is opaque: ${dPanel.n} of ${dPanel.total} pixels change when the canvas is hidden`
          + (dEdge.n ? `  (${dEdge.n} on the un-inset rect - the fractional top edge, see the note above)` : ''));
    }
    say(dCtl.n > 0, `control region above it does change: ${dCtl.n} of ${dCtl.total} pixels`);

    /* The seam, checked only once - it is a property of the stylesheet, not of
       the system on screen. Scrolled past the fold so .paper spans the panel's
       rows; at scrollY 0 the paper column starts below the hero band and there
       is no border there to double.
       NOT under --break. With the ground removed the canvas shows through the
       sample strip and every inked column counts as a rule, so the check
       reports 10 ruled columns of 19 and fails for a reason that has nothing to
       do with the seam. A check that cannot be read in a mode is not run in it. */
    if (pin === PINS[0] && !BREAK) {
      await page.evaluate(() => scrollTo(0, 600));
      await page.waitForTimeout(200);
      const seam = await page.evaluate(() => {
        const p = document.querySelector('.paper').getBoundingClientRect();
        const f = document.querySelector('.herofoot').getBoundingClientRect();
        return { paperLeft: p.left, footRight: f.right,
                 covers: p.top <= f.top && p.bottom >= f.bottom - 1,
                 y: Math.round(f.top + f.height / 2) };
      });
      const strip = await page.screenshot({ clip: { x: seam.paperLeft - 4, y: seam.y - 8, width: 9, height: 16 } });
      const cols = await page.evaluate(async src => {
        const img = await new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; });
        const c = document.createElement('canvas');
        c.width = img.width; c.height = img.height;
        const g = c.getContext('2d', { willReadFrequently: true });
        g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, c.width, c.height).data;
        /* --bg is #F2F0EF. A column counts as ruled if its middle row is more
           than 8 units off the ground in any channel. */
        const row = Math.floor(c.height / 2), out = [];
        for (let x = 0; x < c.width; x++) {
          const i = (row * c.width + x) * 4;
          out.push(Math.abs(d[i] - 242) > 8 || Math.abs(d[i + 1] - 240) > 8 || Math.abs(d[i + 2] - 239) > 8);
        }
        return { ruled: out.filter(Boolean).length, width: c.width, pattern: out.map(v => v ? '|' : '.').join('') };
      }, b64(strip));
      /* One CSS pixel of rule at deviceScaleFactor 2.2222 is 2 or 3 device
         columns; two adjacent CSS rules would be 4 to 6. The assertion is on
         device columns because that is what the reader sees. */
      say(seam.covers && cols.ruled > 0 && cols.ruled <= 3,
        `.paper seam is one hairline: ${cols.ruled} ruled device columns of ${cols.width} `
        + `at x=${Math.round(seam.paperLeft)} (${cols.pattern}), paper.left ${Math.round(seam.paperLeft)} `
        + `vs foot.right ${Math.round(seam.footRight)}`);
    }

    console.log('');
    await ctx.close();
  }

  await browser.close();
  srv.close();
  if (BREAK) {
    say(detected > 0, `${detected} of ${PINS.length} pins noticed the background being removed`);
  }
  console.log(`  ${failures ? failures + ' FAILED' : 'all checks passed'}\n`);
  process.exit(failures ? 1 : 0);
})();
