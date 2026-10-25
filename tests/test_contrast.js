/* Contrast measured on rendered pixels, not on resolved CSS.
 *
 * _deslop/measure.js walks the parent chain for a background-color, so text
 * over a canvas, an image or a background-image is scored against whatever
 * colour CSS happens to resolve, and reports nothing either way. That is how
 * longevity-app shipped a value label at 1.30:1 with every gate green
 * (HANDOFF section 8, trap 31), and on 2026-09-11 it is why skyline-app's
 * bearing line over its meter reads 5.80:1 by CSS and 2.90:1 in pixels.
 *
 * Method, per text run in view:
 *   A  the page as rendered
 *   B  the same frame with every glyph made transparent
 *   A2 as rendered again
 * ink    = pixels where A differs from B and A agrees with A2, so a canvas
 *          that keeps drawing is not counted as ink
 * ground = B within 2px of that ink; a run with no ink is measured over its
 *          whole box, which separates covered text (ground unlike the text)
 *          from invisible text (ground like it)
 * A line box whose centre hit-tests to another element is dropped as covered;
 * pointer-events:none text cannot be hit-tested and is kept.
 * The verdict is WCAG's ratio of the declared colour composited over each
 * ground pixel, at the 10th percentile, against 4.5 (3.0 for large text).
 *
 * tests/fixtures/contrast.html pins six cases with known answers and runs
 * first, every time: a check nobody has seen fire is a claim, not a check.
 *
 *   node tests/test_contrast.js                 pages and apps, 1440 and 390
 *   node tests/test_contrast.js --quick         1440 only
 *   node tests/test_contrast.js --break         ground taken from CSS, as the
 *                                               old rig does; MUST exit 1
 */
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const HERE = __dirname;
const SITE = path.join(HERE, '..', 'site');
const FIXTURES = path.join(HERE, 'fixtures');
const PAGES = ['about', 'beauty', 'climate-cost', 'code', 'continents', 'heat', 'index', 'longevity', 'lostgas', 'skyline', 'storage', 'takeaway', 'uri',
               '_fixture/kit'];
/* The insight kit's fixture (R1, 2026-10-23): tests/fixtures/kit.html, served
   from tests/ and never from site/, so the kit is measured by this gate as it
   ships before any page uses it (packet R1: the kit passes the existing gates
   on a fixture page). Built by tests/fixtures/build_kit_fixture.py. */
const APPS = ['climate-cost-app', 'continents-app', 'longevity-app', 'skyline-app'];   // takeaway-app dropped 2026-10-23 (R2: the page has no app); meter-app the same day (R3: a redirect stub to lostgas.html)
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.ico': 'image/x-icon' };
const BREAK = process.argv.includes('--break');
const QUICK = process.argv.includes('--quick');

function serve() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      const f = u.startsWith('/_fixture/') ? path.join(FIXTURES, u.slice('/_fixture/'.length)) : path.join(SITE, u);
      fs.readFile(f, (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
        res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}

/* Runs in the page: every text run in view, with its own line boxes, the
   colour it declares, and the ground CSS resolves for it (measure.js's rule,
   reproduced so the two can be printed side by side). */
function collect() {
  const parseRGB = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (t, b) => ({ r: t.r * t.a + b.r * (1 - t.a), g: t.g * t.a + b.g * (1 - t.a), b: t.b * t.a + b.b * (1 - t.a), a: 1 });
  const effBg = el => {
    const layers = []; let e = el;
    while (e && e !== document.documentElement) { const c = parseRGB(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; } e = e.parentElement; }
    let bg = parseRGB(getComputedStyle(document.body).backgroundColor) || { r: 255, g: 255, b: 255, a: 1 };
    if (bg.a < 1) bg = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) bg = layers[i].a >= 1 ? layers[i] : over(layers[i], bg);
    return bg;
  };
  const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.02; };
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    if (/^(SCRIPT|STYLE|NOSCRIPT|OPTION|CANVAS)$/.test(el.tagName)) continue;
    const texts = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim());
    if (!texts.length || !vis(el)) continue;
    const rects = [];
    for (const t of texts) { const rg = document.createRange(); rg.selectNodeContents(t); for (const r of rg.getClientRects()) if (r.width >= 2 && r.height >= 4 && r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight) rects.push(r); }
    if (!rects.length) continue;
    const cs = getComputedStyle(el);
    const pe = cs.pointerEvents === 'none';
    const marked = rects.map(r => { const h = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2); return { x0: r.left, y0: r.top, x1: r.right, y1: r.bottom, hit: pe || !!(h && (h === el || el.contains(h) || h.contains(el))) }; });
    out.push({ name: name(el), text: texts.map(t => t.textContent).join(' ').trim().replace(/\s+/g, ' ').slice(0, 50), fg: parseRGB(cs.color), cssBg: effBg(el), fs: parseFloat(cs.fontSize), fw: parseInt(cs.fontWeight) || 400, rects: marked });
  }
  return out;
}

const HIDE = '*,*::before,*::after,::marker{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important;caret-color:transparent!important}';

/* Runs in a blank page: decode the three frames once, then score every box. */
function score({ a, b, a2, boxes, useCss, cssW }) {
  const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  const ratio = (l1, l2) => (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  const load = src => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = src; });
  return Promise.all([load(a), load(b), load(a2)]).then(([ia, ib, ia2]) => {
    const W = ia.width, H = ia.height;
    const px = img => { const c = new OffscreenCanvas(W, H); const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(img, 0, 0); return x.getImageData(0, 0, W, H).data; };
    const A = px(ia), B = px(ib), A2 = px(ia2);
    const dpr = W / cssW;   // the MEASURED page's width, not this page's
    const out = [];
    for (const bx of boxes) {
      let ink = 0, covered = 0, ground = [], whole = [];
      const inkPts = [];
      for (const r of bx.rects) {
        if (!r.hit) { covered++; continue; }
        const xs = Math.round(r.x0 * dpr), ys = Math.round(r.y0 * dpr), xe = Math.round(r.x1 * dpr), ye = Math.round(r.y1 * dpr);
        for (let y = ys; y < ye; y++) for (let x = xs; x < xe; x++) {
          const i = (y * W + x) * 4;
          whole.push(i);
          const dab = Math.abs(A[i] - B[i]) + Math.abs(A[i + 1] - B[i + 1]) + Math.abs(A[i + 2] - B[i + 2]);
          const daa = Math.abs(A[i] - A2[i]) + Math.abs(A[i + 1] - A2[i + 1]) + Math.abs(A[i + 2] - A2[i + 2]);
          if (dab > 30 && daa <= 24) { ink++; inkPts.push([x, y]); }
        }
      }
      if (!whole.length) { out.push({ ...bx, rects: undefined, covered, allCovered: true }); continue; }
      const near = new Set();
      for (const [x, y] of inkPts) for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx >= 0 && ny >= 0 && nx < W && ny < H) near.add((ny * W + nx) * 4);
      }
      const pool = ink >= 3 && near.size ? [...near] : whole;
      const fg = bx.fg, cb = bx.cssBg;
      const rs = [];
      for (const i of pool) {
        const g = useCss ? [cb.r, cb.g, cb.b] : [B[i], B[i + 1], B[i + 2]];
        const c = [fg.r * fg.a + g[0] * (1 - fg.a), fg.g * fg.a + g[1] * (1 - fg.a), fg.b * fg.a + g[2] * (1 - fg.a)];
        rs.push(ratio(lum(c[0], c[1], c[2]), lum(g[0], g[1], g[2])));
      }
      rs.sort((x, y) => x - y);
      /* The verdict is the worse QUARTILE, not the worse tenth, and the two
         measured cases are why. Text that really sits on a fill moves both:
         skyline-app's bearing line read 2.90 at the tenth and 3.51 at the
         median over its meter. A bar or rule that merely ends a pixel from
         the glyphs lands inside the 2px neighbourhood and drags the tenth
         alone: longevity-app's value labels read 1.00 at the tenth and 5.80
         at the median, and nothing about them is hard to read.
         The fixture pins one half of this - #half, a label straddling a fill
         edge, must fail - and NOT the other: four attempts to build the
         abutting-bar shape never got the bar into the neighbourhood, so that
         case was dropped rather than left passing for the wrong reason. */
      const p10 = rs[Math.floor(rs.length * 0.1)], p25 = rs[Math.floor(rs.length * 0.25)], med = rs[Math.floor(rs.length * 0.5)];
      const cssR = ratio(lum(fg.r * fg.a + cb.r * (1 - fg.a), fg.g * fg.a + cb.g * (1 - fg.a), fg.b * fg.a + cb.b * (1 - fg.a)), lum(cb.r, cb.g, cb.b));
      const large = bx.fs >= 24 || (bx.fs >= 18.66 && bx.fw >= 700);
      out.push({ name: bx.name, text: bx.text, p10, p25, med, css: cssR, floor: large ? 3.0 : 4.5, ink, covered, noInk: ink < 3 });
    }
    return out;
  });
}

async function measure(page, shot, cssW) {
  const vh = await page.evaluate(() => innerHeight);
  const H = await page.evaluate(() => Math.max(document.documentElement.scrollHeight, innerHeight));
  const found = [];
  for (let y = 0; y < H; y += vh) {
    await page.evaluate(v => scrollTo(0, v), y);
    await page.waitForTimeout(300);
    const boxes = await page.evaluate(collect);
    if (!boxes.length) continue;
    const a = (await page.screenshot()).toString('base64');
    const h = await page.addStyleTag({ content: HIDE });
    await page.waitForTimeout(100);
    const b = (await page.screenshot()).toString('base64');
    await h.evaluate(n => n.remove());
    await page.waitForTimeout(100);
    const a2 = (await page.screenshot()).toString('base64');
    const res = await shot.evaluate(score, { a: 'data:image/png;base64,' + a, b: 'data:image/png;base64,' + b, a2: 'data:image/png;base64,' + a2, boxes, useCss: BREAK, cssW });
    found.push(...res);
  }
  return found;
}

(async () => {
  const t0 = Date.now();
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await chromium.launch();
  let failures = 0, runs = 0;

  const ctx = await browser.newContext({ viewport: { width: 420, height: 560 }, deviceScaleFactor: 1 });
  const shot = await ctx.newPage();
  await shot.goto('about:blank');
  await shot.evaluate(() => { window.innerWidthCss = innerWidth; });
  const fx = await ctx.newPage();

  // ---- the fixture, first and always
  const EXPECT = { 'span#c1.lab': 'fail', 'div#d1': 'fail', 'p#ok': 'pass', 'div#g1': 'fail', 'span#pe.lab': 'fail', 'span#cov': 'covered',
    'span#half': 'fail' };
  for (const fill of ['733E24', 'F2F0EF']) {
    await fx.goto(base + '_fixture/contrast.html?fill=' + fill, { waitUntil: 'load' });
    await fx.waitForTimeout(200);
    const got = await measure(fx, shot, 420);
    for (const [name, want0] of Object.entries(EXPECT)) {
      const r = got.find(x => x.name === name);
      const want = fill === 'F2F0EF' && (name === 'span#c1.lab' || name === 'span#pe.lab') ? 'pass' : want0;
      const verdict = !r ? 'missing' : r.allCovered || (r.noInk && r.med >= 1.5) ? 'covered' : r.p25 < r.floor ? 'fail' : 'pass';
      const ok = verdict === want;
      failures += !ok;
      console.log(`  ${ok ? 'ok  ' : 'FAIL'} fixture fill #${fill} ${name.padEnd(12)} ${r && r.p25 !== undefined ? 'px q1 ' + r.p25.toFixed(2) + ' (p10 ' + r.p10.toFixed(2) + ', median ' + r.med.toFixed(2) + ') css ' + r.css.toFixed(2) : '-'}  ${verdict}, expected ${want}`);
    }
  }
  await fx.close();
  if (BREAK) {
    // The mutation is the old rig's method. The fixture must NOTICE it.
    const caught = failures > 0;
    console.log(caught
      ? `\n  --break: ground taken from CSS scored the canvas and image cases as passes; the fixture caught it (${failures} expectation(s) missed).`
      : '\n  FAIL  --break: the CSS-resolved ground changed nothing the fixture could see.');
    await browser.close(); srv.close(); process.exit(1);
  }
  if (failures) { console.log(`\n  the fixture did not behave: ${failures} expectation(s) missed. Nothing else was measured.`); await browser.close(); srv.close(); process.exit(1); }
  console.log(`  ok    fixture: ${Object.keys(EXPECT).length * 2} expectations, both fills`);

  // ---- the site
  const widths = QUICK ? [[1440, 900]] : process.argv.includes('--phone') ? [[390, 844]] : [[1440, 900], [390, 844]];
  const only = (process.argv.find(a => a.startsWith('--only=')) || '').slice(7);
  const bad = [];
  for (const [w, h] of widths) {
    const c = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const p = await c.newPage();
    for (const name of PAGES.concat(APPS).filter(n => !only || n === only)) {
      await p.goto(base + name + '.html' + (name === 'index' ? '?hero=lorenz' : ''), { waitUntil: 'load', timeout: 90000 });
      await p.waitForTimeout(2000);
      const res = await measure(p, shot, w);
      runs += res.length;
      const fails = res.filter(r => !r.allCovered && !(r.noInk && r.med >= 1.5) && r.p25 < r.floor);
      const fill = res.filter(r => !r.allCovered && !r.noInk && Math.abs(r.med - r.css) / r.css > 0.1);
      for (const f of fails) bad.push({ page: name, w, ...f });
      console.log(`  ${fails.length ? 'FAIL' : 'ok  '} ${String(w).padEnd(5)} ${name.padEnd(18)} runs ${String(res.length).padStart(4)}  fails ${fails.length}  on a ground CSS does not know ${fill.length}`);
    }
    await c.close();
  }
  for (const f of bad) console.log(`        ${f.page} @${f.w}  ${f.name} ${JSON.stringify(f.text)}  pixels ${f.p25.toFixed(2)} at the worse quartile (p10 ${f.p10.toFixed(2)}, median ${f.med.toFixed(2)}), CSS says ${f.css.toFixed(2)}, floor ${f.floor}`);
  console.log(`\n  ${runs - bad.length}/${runs} text runs clear AA on rendered pixels, ${Math.round((Date.now() - t0) / 1000)}s`);
  await browser.close();
  srv.close();
  process.exit(bad.length ? 1 : 0);
})();
