/* test_kit.js - the insight kit (R1, 2026-10-23), measured as it ships.
 *
 *   node tests/test_kit.js                 all checks; exit 1 on any failure
 *   node tests/test_kit.js --break <name>  reproduce a fault; must exit 1
 *
 * What each check asserts, and the fault its --break reproduces:
 *
 *   parity   charts.update() from any state lands exactly where render() of
 *            that state does - in node (jsdom) over a grid of states and
 *            widths, and in the browser on the live chart after scrolling.
 *            --break parity: update() skips the reveal clip, the fault that
 *            would leave the live chart and the static figures disagreeing.
 *   layout   every spec on the fixture renders strictly from 320px to 1140px;
 *            and a control spec that cannot fit (five full-word annotations
 *            at 320px) MUST be refused, or the gate is asleep.
 *   rail     no page that links scrolly.css carries aside.marginalia, and no
 *            page has more than three takeaways. --break rail: a fixture copy
 *            with a marginalia aside added.
 *   nojs     with JS off: no stage, one visible static figure per step, the
 *            clip's native controls, the counter's final value.
 *   motion   with reduced motion: nothing goes live, the clip does not play.
 *            --break motion: scrolly.js ignores the preference.
 *   live     with motion: every scrolly goes live; arriving at each step puts
 *            the chart in that step's state, and the state MOVES between
 *            steps; turning reduced motion on mid-page tears it down, off
 *            brings it back.
 *   font     chart text renders at the size charts.js laid it out for: the
 *            computed font-size, and each label's measured length against
 *            its predicted width (trap 31: assert the declaration applied).
 *            --break font: a stylesheet that sets chart text to 14px.
 *   served   no chart SVG on screen is scaled below the size it was drawn at.
 *   under    (R2) panels under a series: every bar's count is drawn whole,
 *            outside the reveal clip, at every width; the site's own kit
 *            specs (takeaway.html's hero) join the parity and layout sweeps.
 *            --break under: the panel labels go back inside the clip, the
 *            fault that showed "17" as "1" on the phone chart mid-reveal.
 *   counter  links to an existing source entry, animates, and ends on the
 *            exact text it shipped with.
 *   clip     files under 4 MB, captions load (3 cues), the play button
 *            replaces native controls, a loop of <= 10 s plays muted in view
 *            with motion and waits for a click without it.
 */
'use strict';
const path = require('path');
const fs = require('fs');
const http = require('http');
const { chromium } = require('playwright');
const { JSDOM } = require('jsdom');

const PUB = path.join(__dirname, '..');
const SITE = path.join(PUB, 'site');
const FIX = path.join(__dirname, 'fixtures');
const BREAKS = ['parity', 'font', 'rail', 'motion', 'under'];
const BREAK = (() => { const i = process.argv.indexOf('--break'); return i > 0 ? process.argv[i + 1] : null; })();
if (BREAK !== null && !BREAKS.includes(BREAK)) { console.error('  --break takes one of: ' + BREAKS.join(' | ')); process.exit(2); }

let failures = 0, checks = 0;
function say(ok, what) { checks++; if (!ok) failures++; console.log((ok ? '  ok   ' : '  FAIL ') + what); }

/* A mutation that does not mutate reads exactly like a test that works
   (site-sweep STATE, instrument 5): every one asserts it replaced once. */
function mutate(src, a, b, what) {
  const n = src.split(a).length - 1;
  if (n !== 1) { console.error('  mutation ' + what + ' matched ' + n + ' times, not 1'); process.exit(2); }
  return src.replace(a, b);
}
const CHARTS_SRC = fs.readFileSync(path.join(SITE, 'assets', 'charts.js'), 'utf8');
const SCROLLY_SRC = fs.readFileSync(path.join(SITE, 'assets', 'scrolly.js'), 'utf8');
let chartsSrc = BREAK === 'parity'
  ? mutate(CHARTS_SRC, "if (!el) continue;", "if (!el || key === 'clip') continue;", 'parity') : CHARTS_SRC;
if (BREAK === 'under') {
  chartsSrc = mutate(chartsSrc, "    s.push('</g>');\n    // panel frames", "    // panel frames", 'under 1');
  chartsSrc = mutate(chartsSrc, "    s.push('<text class=\"ch-now\"", "    s.push('</g>');\n    s.push('<text class=\"ch-now\"", 'under 2');
}
const scrollySrc = BREAK === 'motion'
  ? mutate(SCROLLY_SRC, "function motionOn() { return root.dataset.motion !== 'off'; }", 'function motionOn() { return true; }', 'motion') : SCROLLY_SRC;
function loadCharts(src) { const m = { exports: {} }; new Function('module', 'exports', src)(m, m.exports); return m.exports; }
const Charts = loadCharts(chartsSrc);

const KIT = fs.readFileSync(path.join(FIX, 'kit.html'), 'utf8');
const SPECS_FIX = [...KIT.matchAll(/<script type="application\/json" class="scrolly-spec">([\s\S]*?)<\/script>/g)]
  .map(m => JSON.parse(m[1].replace(/<\\\//g, '</')));
// R2: every site page's kit specs join the sweeps (takeaway.html's hero)
const SPECS = SPECS_FIX.concat(fs.readdirSync(SITE).filter(f => f.endsWith('.html')).flatMap(f =>
  [...fs.readFileSync(path.join(SITE, f), 'utf8').matchAll(/<script type="application\/json" class="scrolly-spec">([\s\S]*?)<\/script>/g)]
    .map(m => JSON.parse(m[1].replace(/<\\\//g, '</')))));

/* ------------------------------------------------------------ parity --- */
function canon(svgText) {
  const w = new JSDOM('<body>' + svgText + '</body>').window, out = w.document.body.innerHTML;
  w.close();
  return out;
}
{
  const grid = { series: [0, 0.07, 0.33, 0.5, 0.81, 1].map(t => ({ t })), split: [0, 0.2, 0.5, 0.75, 1].map(s => ({ s })),
                 // R3: strip states mix every key it reads (bars, lights, range, marks)
                 strip: [{ t: 0 }, { t: 0.4, med: 1 }, { t: 1, med: 1, neg: 1 }, { t: 1, band: 0.5 },
                         { t: 1, band: 1, inside: 1 }, { t: 1, band: 1, neg: 0.3, inside: 0.6, med: 0 }],
                 // R4: days states cross every key (reveal, lit, the blend between years, and the
                 // blend's midpoint where the lit set and the labels switch year)
                 days: [{ t: 0 }, { t: 0.37 }, { t: 1 }, { t: 1, lit: 1 }, { t: 1, lit: 0.5, mix: 0.49 },
                        { t: 1, lit: 0.5, mix: 0.51 }, { t: 1, mix: 1 }, { t: 1, mix: 1, lit: 1 }] };
  let pairs = 0, bad = [];
  // One document for the whole sweep, re-filled per pair. R4 found unclosed windows ran node out of memory
  // and closed them; closed windows are still retained: with ethane.html's spec (Q11, 2026-10-25) the heap
  // stood at 3.87 GB after this loop and the next section aborted (rc=134). Parsing into one body serializes
  // exactly as a fresh window's body does, which is what canon() is.
  const one = new JSDOM('<body></body>').window, body = one.document.body;
  for (const spec of SPECS) for (const w of [320, 517, 720, 1140]) {
    const sts = grid[spec.type];
    for (const a of sts) for (const b of sts) {
      if (a === b) continue;
      body.innerHTML = Charts.render(spec, a, { width: w });
      Charts.update(body.querySelector('svg'), spec, b);
      const got = body.innerHTML;
      body.innerHTML = Charts.render(spec, b, { width: w });
      const want = body.innerHTML;
      pairs++;
      if (got !== want && bad.length < 3) bad.push(spec.id + ' @' + w + ' ' + JSON.stringify(a) + '->' + JSON.stringify(b));
    }
  }
  one.close();
  say(bad.length === 0 && pairs > 0, 'parity (node): update() == render() over ' + pairs + ' state pairs' + (bad.length ? ': ' + bad.join('; ') : ''));
}

/* ------------------------------------------------------------ layout --- */
{
  const probs = SPECS.map(s => Charts.check(s)).flat();
  say(SPECS.length >= 2 && probs.length === 0, 'layout: ' + SPECS.length + ' specs (fixture and site) render strictly at every width 320-1140' + (probs.length ? ': ' + probs.slice(0, 3).join('; ') : ''));
  const ctl = JSON.parse(JSON.stringify(SPECS.find(s => s.type === 'series')));
  ctl.annotations.forEach(a => { delete a.short; });
  const refused = Charts.check(ctl);
  say(refused.length > 0, 'layout control: a spec whose labels cannot fit at 320px is refused (' + refused.length + ' widths refused)');
}

/* ------------------------------------------------------------- under --- */
{
  const withBars = SPECS.filter(s => (s.under || []).some(u => u.kind === 'bars'));
  const bad = [];
  let n = 0;
  for (const spec of withBars) for (let w = 320; w <= 1140; w += 10) for (const t of [0.1, 0.5, 1]) {
    // Q11, 2026-10-25: these windows were never closed; with ethane.html's spec added the run
    // reached node's 4 GB heap and aborted (rc=134), as the parity loop's did in R4. Close each one.
    const win = new JSDOM('<body>' + Charts.render(spec, { t }, { width: w }) + '</body>').window, d = win.document;
    const clipped = new Set([...d.querySelectorAll('g[clip-path] text')].map(e => e.textContent));
    const outside = [...d.querySelectorAll('svg > text')].map(e => e.textContent);
    win.close();
    for (const u of spec.under.filter(u => u.kind === 'bars')) for (const b of u.bars) {
      n++;
      if ((clipped.has(b.text) || !outside.includes(b.text)) && bad.length < 3) bad.push(spec.id + ' @' + w + ' t=' + t + ' "' + b.text + '"');
    }
  }
  say(withBars.length >= 1 && n > 0 && bad.length === 0, 'under: ' + n + ' bar labels over ' + withBars.length + ' spec(s) drawn whole, outside the reveal' + (bad.length ? ': ' + bad.join('; ') : ''));
}

/* -------------------------------------------------------------- rail --- */
{
  const pages = fs.readdirSync(SITE).filter(f => f.endsWith('.html')).map(f => [f, fs.readFileSync(path.join(SITE, f), 'utf8')]);
  let kit = KIT;
  if (BREAK === 'rail') kit = mutate(kit, '<h2>A series', '<aside class="marginalia"><ul><li><b>k</b><span class="v">0.8</span></li></ul></aside>\n<h2>A series', 'rail');
  pages.push(['_fixture/kit.html', kit]);
  const users = pages.filter(([, h]) => /assets\/scrolly\.css/.test(h));
  const both = users.filter(([, h]) => /<aside class="marginalia/.test(h)).map(([f]) => f);
  const many = pages.filter(([, h]) => (h.match(/<section class="takeaways"[\s\S]*?<\/section>/) || [''])[0].split('<li>').length - 1 > 3).map(([f]) => f);
  say(users.length >= 1 && both.length === 0, 'rail: ' + users.length + ' page(s) use the kit, none also carries aside.marginalia' + (both.length ? ': ' + both.join(', ') : ''));
  say(many.length === 0, 'rail: no page has more than three takeaways' + (many.length ? ': ' + many.join(', ') : ''));
}

/* ----------------------------------------------------------- browser --- */
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.webm': 'video/webm', '.mp4': 'video/mp4', '.vtt': 'text/vtt', '.json': 'application/json', '.ico': 'image/x-icon' };
function serve() {
  return new Promise(r => {
    const s = http.createServer((q, res) => {
      const u = decodeURIComponent(q.url.split('?')[0]);
      let body = null;
      if (u === '/assets/charts.js') body = chartsSrc;
      else if (u === '/assets/scrolly.js') body = scrollySrc;
      const f = u.startsWith('/_fixture/') ? path.join(FIX, u.slice(10)) : path.join(SITE, u);
      const send = d => { res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); res.end(d); };
      if (body !== null) return send(body);
      fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } send(d); });
    }).listen(0, '127.0.0.1', () => r(s));
  });
}

(async () => {
  const srv = await serve();
  const URL = `http://127.0.0.1:${srv.address().port}/_fixture/kit.html`;
  const browser = await chromium.launch();
  const fontCss = BREAK === 'font' ? '.chart text { font-size: 14px !important; }' : null;

  for (const [w, h] of [[1440, 900], [390, 844]]) {
    /* nojs */
    {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, javaScriptEnabled: false });
      const p = await ctx.newPage();
      await p.goto(URL, { waitUntil: 'load' });
      const r = await p.evaluate(() => ({
        stage: [...document.querySelectorAll('.scrolly-stage')].map(s => getComputedStyle(s).display),
        figs: [...document.querySelectorAll('.step')].map(st => [...st.querySelectorAll('.step-fig svg')].filter(s => s.getBoundingClientRect().width > 0).length),
        controls: [...document.querySelectorAll('figure.clip video')].map(v => v.hasAttribute('controls')),
        btn: [...document.querySelectorAll('.clip-play')].map(b => getComputedStyle(b).display),
      }));
      say(r.stage.every(d => d === 'none') && r.figs.length > 0 && r.figs.every(n => n === 1) && r.controls.every(Boolean) && r.btn.every(d => d === 'none'),
        `nojs @${w}: stages hidden, ${r.figs.length} steps each show exactly one figure, clip has native controls and no button`);
      await ctx.close();
    }
    /* motion off */
    {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: 'reduce' });
      const p = await ctx.newPage();
      await p.goto(URL, { waitUntil: 'load' });
      await p.evaluate(() => document.querySelector('figure.clip').scrollIntoView({ block: 'center' }));
      await p.waitForTimeout(700);
      const r = await p.evaluate(() => ({
        live: document.querySelectorAll('.scrolly.is-live').length,
        figs: [...document.querySelectorAll('.step')].map(st => [...st.querySelectorAll('.step-fig svg')].filter(s => s.getBoundingClientRect().width > 0).length),
        paused: document.querySelector('figure.clip video').paused,
        btn: !document.querySelector('.clip-play').hidden,
      }));
      say(r.live === 0 && r.figs.every(n => n === 1) && r.paused && r.btn,
        `motion @${w}: reduced motion -> ${r.live} live scrollies, stacked figures, clip paused with its play button`);
      if (w === 1440 && r.btn) {
        await p.click('.clip-play');
        await p.waitForTimeout(600);
        const pl = await p.evaluate(() => { const v = document.querySelector('figure.clip video'); return { paused: v.paused, t: v.currentTime, controls: v.hasAttribute('controls') }; });
        say(!pl.paused && pl.t > 0 && pl.controls, `clip @${w}: the play button starts it under reduced motion (t=${pl.t.toFixed(2)}s) and restores native controls`);
      }
      await ctx.close();
    }
    /* motion on */
    {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: 'no-preference' });
      const p = await ctx.newPage();
      const errs = []; p.on('pageerror', e => errs.push(e.message));
      if (fontCss) await p.addInitScript(css => { document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); }); }, fontCss);
      await p.goto(URL, { waitUntil: 'load' });
      await p.waitForTimeout(200);
      const nSec = await p.evaluate(() => document.querySelectorAll('section.scrolly').length);
      const nLive = await p.evaluate(() => document.querySelectorAll('section.scrolly.is-live').length);
      say(nSec >= 2 && nLive === nSec, `live @${w}: ${nLive} of ${nSec} scrollies live`);

      // arrive at each step: put its top a full span above the trigger
      const arrive = await p.evaluate(async () => {
        const out = [];
        for (const [si, S] of window.__scrolly.entries()) {
          for (let i = 0; i < S.steps.length; i++) {
            const sb = S.stage.getBoundingClientRect().height;
            const span = Math.max(80, 0.7 * (innerHeight - sb));
            const top = S.steps[i].getBoundingClientRect().top + scrollY;
            scrollTo(0, top - innerHeight + span + 2);
            await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
            await new Promise(r => setTimeout(r, 60));
            const want = S.states[i], got = S.state;
            const ok = Object.keys(want).every(k => Math.abs(got[k] - want[k]) < 1e-6);
            const svg = S.stage.querySelector('svg');
            const ser = new XMLSerializer();
            const canon = s => { const d = new DOMParser().parseFromString('<body>' + s + '</body>', 'text/html'); return d.body.innerHTML; };
            const same = canon(svg.outerHTML) === canon(Charts.render(S.spec, got, { width: S.width, suffix: '-live' }));
            out.push({ si, i, ok, same, got: JSON.stringify(got), want: JSON.stringify(want), active: S.steps[i].classList.contains('is-active') });
          }
        }
        return out;
      });
      const wrong = arrive.filter(a => !a.ok || !a.active);
      say(arrive.length > 0 && wrong.length === 0, `live @${w}: arriving at each of ${arrive.length} steps puts the chart in that step's state` + (wrong.length ? ': ' + wrong.slice(0, 2).map(a => `s${a.si}/${a.i} got ${a.got} want ${a.want} active=${a.active}`).join('; ') : ''));
      const moved = arrive.filter((a, k) => k > 0 && arrive[k - 1].si === a.si && arrive[k - 1].got === a.got);
      say(moved.length === 0, `live @${w}: the state moves between every pair of consecutive steps`);
      const drift = arrive.filter(a => !a.same);
      say(drift.length === 0, `parity (browser) @${w}: the live SVG equals render() of its state at all ${arrive.length} steps` + (drift.length ? ': ' + drift.length + ' differ, first s' + drift[0].si + '/' + drift[0].i : ''));

      // font: the declaration applied, and the widths charts.js predicted
      const f = await p.evaluate(({ CW, FS, FS_BIG }) => {
        const out = { sizes: new Set(), worst: 0, n: 0, label: '' };
        document.querySelectorAll('.scrolly-stage svg text').forEach(t => {
          const cs = getComputedStyle(t); out.sizes.add(cs.fontSize);
          if (!t.textContent.length) return;
          const want = t.textContent.length * 0.6 * (t.classList.contains('ch-now') ? FS_BIG : FS);
          const got = t.getComputedTextLength(), err = Math.abs(got - want) / want;
          out.n++; if (err > out.worst) { out.worst = err; out.label = t.textContent; }
        });
        out.sizes = [...out.sizes]; return out;
      }, { CW: Charts.CW, FS: Charts.FS, FS_BIG: Charts.FS_BIG });
      say(f.n > 20 && f.sizes.every(s => s === '12px' || s === '14.5px') && f.worst < 0.03,
        `font @${w}: ${f.n} chart labels at ${f.sizes.join('/')}, worst width error ${(100 * f.worst).toFixed(1)}% ("${f.label}")`);

      // served: nothing on screen drawn smaller than it was laid out
      const sc = await p.evaluate(() => {
        let worst = 9;
        document.querySelectorAll('svg.chart').forEach(s => {
          const r = s.getBoundingClientRect(); if (!r.width) return;
          worst = Math.min(worst, r.width / s.viewBox.baseVal.width);
        });
        return worst;
      });
      say(sc >= 0.999, `served @${w}: smallest chart scale ${sc.toFixed(3)} (text never below its laid-out size)`);

      // counter: animates, then ends on the shipped text, and its source exists
      const c = await p.evaluate(async () => {
        const a = document.querySelector('a.counter'), shipped = a.getAttribute('data-value') && a.textContent;
        const target = document.querySelector(a.getAttribute('href'));
        a.scrollIntoView({ block: 'center' });
        let seen = new Set();
        const t0 = performance.now();
        while (performance.now() - t0 < 1500) { seen.add(a.textContent); await new Promise(r => setTimeout(r, 30)); }
        return { shipped, final: a.textContent, distinct: seen.size, src: !!target && target.tagName };
      });
      say(c.src === 'LI' && c.final === c.shipped && c.distinct > 3,
        `counter @${w}: links to its source entry (${c.src}), showed ${c.distinct} values while counting, ended on "${c.final}"`);

      // clip: loop plays muted when in view with motion on
      const cl = await p.evaluate(async () => {
        const v = document.querySelector('figure.clip video');
        v.scrollIntoView({ block: 'center' });
        await new Promise(r => setTimeout(r, 1200));
        const tr = v.textTracks[0]; if (tr) tr.mode = 'hidden';
        await new Promise(r => setTimeout(r, 300));
        return { paused: v.paused, muted: v.muted, loop: v.loop, t: v.currentTime, cues: tr && tr.cues ? tr.cues.length : -1, btn: !document.querySelector('.clip-play').hidden };
      });
      say(!cl.paused && cl.muted && cl.loop && cl.t > 0 && !cl.btn, `clip @${w}: an 8 s loop plays muted in view (t=${cl.t.toFixed(2)}s), button hidden`);
      say(cl.cues === 3, `clip @${w}: captions load, ${cl.cues} cues`);

      // teardown and return on the preference changing mid-page
      await p.emulateMedia({ reducedMotion: 'reduce' });
      await p.waitForTimeout(150);
      const off = await p.evaluate(() => ({ live: document.querySelectorAll('.scrolly.is-live').length, stages: [...document.querySelectorAll('.scrolly-stage')].map(s => s.innerHTML.length) }));
      await p.emulateMedia({ reducedMotion: 'no-preference' });
      await p.waitForTimeout(150);
      const on = await p.evaluate(() => document.querySelectorAll('.scrolly.is-live').length);
      say(off.live === 0 && off.stages.every(n => n === 0) && on === nSec, `live @${w}: reduced motion mid-page tears down (${off.live} live, stages emptied), and back on restores ${on}`);
      say(errs.length === 0, `live @${w}: no page errors` + (errs.length ? ': ' + errs.slice(0, 2).join('; ') : ''));
      await ctx.close();
    }
  }

  // clip files
  const meta = JSON.parse(fs.readFileSync(path.join(FIX, 'clips', 'kit-test.json'), 'utf8'));
  const sizes = ['webm', 'mp4'].map(e => fs.statSync(path.join(FIX, 'clips', 'kit-test.' + e)).size);
  const vtt = fs.readFileSync(path.join(FIX, 'clips', 'kit-test.vtt'), 'utf8');
  say(sizes.every(s => s < 4 * 1024 * 1024) && sizes.every((s, i) => s === meta.files[['webm', 'mp4'][i]].bytes) && /^WEBVTT\n/.test(vtt) && meta.duration_s <= 10,
    `clip files: webm ${sizes[0]} B, mp4 ${sizes[1]} B (< 4 MB, = metadata), VTT header, ${meta.duration_s}s`);

  await browser.close(); srv.close();
  console.log(`\n${checks - failures}/${checks} passed${BREAK ? ' (--break ' + BREAK + ')' : ''}`);
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
