/*
 * The reconstruction viewer's own failure modes.
 *
 * 1. The sentinel never becomes a coordinate. GPlates returns
 *    [999.99, 999.99] where a model places no crust. It is a valid-looking
 *    float pair, so it would plot off the map or average into a mean and
 *    nothing would throw.
 * 2. The three states are exhaustive and disjoint. Every model is in exactly
 *    one of: answers, places no crust, does not reach this age.
 * 3. No-crust and out-of-range are not conflated. Coverage is a fact about a
 *    model's scope; no crust is a disagreement about the Earth.
 * 4. Nothing is interpolated. Every drawn coordinate is a payload entry.
 * 5. The distance readout matches a great-circle recomputed here from the
 *    shipped coordinates - parity without shipping a second engine.
 * 6. Longitudes are in range and latitudes are in range.
 * 7. Models are pinned. No "default" appears anywhere in the payload.
 * 8. The empty stage appears when, and only when, nothing is drawn.
 * 9. The land is reconstructed, present at every age, and decodes to real
 *    coordinates. A delta-encoded ring that accumulates wrong drifts off the
 *    map slowly rather than failing, so the decoded extent is checked.
 *10. The land agrees with the Earth: about 29 per cent of the surface at
 *    0 Ma, and a plausible fraction at every age. A delta-encoded ring that
 *    accumulates wrong drifts slowly rather than failing.
 *11. Switching the land model changes the land. If it did not, the selector
 *    would be telling the reader the models agree.
 *
 * Run:  node test_app.js        (from continents/, with tests/node_modules)
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const APP = path.join(ROOT, "site", "continents-app.html");
const LANDJS = path.join(ROOT, "site", "assets", "continents-land.js");
const { JSDOM } = require(path.join(ROOT, "tests", "node_modules", "jsdom"));

/* jsdom runs the page's script the moment the document is constructed, so
   the canvas stub has to be in place before that, not after. That is what
   beforeParse is for. Drawing something and drawing something visible are
   different claims, so this records the calls rather than pretending. */
function stubCanvas(window) {
  const ctx = new Proxy({}, {
    get(_t, k) {
      if (k === "canvas") return { width: 800, height: 400 };
      if (k === "globalAlpha" || k === "lineWidth") return 1;
      return (...a) => a;
    },
    set() { return true; },
  });
  window.HTMLCanvasElement.prototype.getContext = () => ctx;
  window.HTMLCanvasElement.prototype.getBoundingClientRect =
    () => ({ width: 800, height: 400, top: 0, left: 0 });
}

function main() {
  if (!fs.existsSync(APP)) {
    console.log("run build_app.py --apply first");
    return 1;
  }
  /* jsdom does not fetch the external land asset, so it is inlined here.
     The app HTML is otherwise exactly what ships. */
  let html = fs.readFileSync(APP, "utf8");
  if (fs.existsSync(LANDJS)) {
    html = html.replace(/<script src="assets\/continents-land\.js[^"]*"><\/script>/,
      "<script>" + fs.readFileSync(LANDJS, "utf8") + "</script>");
  }
  const dom = new JSDOM(html, {
    runScripts: "dangerously", pretendToBeVisual: true,
    beforeParse: stubCanvas,
  });
  const W = dom.window;
  const app = W.__app;
  if (!app) { console.log("the app did not expose __app"); return 1; }
  const D = app.DATA;
  const fails = [];
  const SENT = 999.99;

  // 1, 6 --------------------------------------------------------------
  let sentinel = 0, bad = 0, nulls = 0, total = 0;
  for (const t of D.tracks) {
    for (const m of D.models) {
      const tr = t.models[m.name];
      for (let i = 0; i < D.ages.length; i++) {
        total++;
        const la = tr.lat[i], lo = tr.lon[i];
        if (la === null || lo === null) { nulls++; continue; }
        if (Math.abs(Math.abs(lo) - SENT) < 0.02 ||
            Math.abs(Math.abs(la) - SENT) < 0.02) sentinel++;
        if (!(la >= -90 && la <= 90) || !(lo >= -180 && lo <= 180)) bad++;
      }
    }
  }
  if (sentinel || bad) fails.push(
    `1. ${sentinel} sentinel values and ${bad} out-of-range coordinates`);
  console.log(`  1. ${total} entries, ${sentinel} sentinels, ${bad} out of `
    + `range, ${nulls} recorded as no-crust or out-of-range`);

  // 2, 3 --------------------------------------------------------------
  let stateBad = 0, ncTotal = 0, outTotal = 0;
  for (let p = 0; p < D.tracks.length; p++) {
    for (let a = 0; a < D.ages.length; a++) {
      app.set(p, a);
      const c = app.counts();
      if (c.here + c.nocrust + c.out !== D.models.length) stateBad++;
      ncTotal += c.nocrust; outTotal += c.out;
      for (const m of D.models) {
        const st = app.state(m);
        const inRange = D.ages[a] <= m.oldest_ma;
        const isNull = D.tracks[p].models[m.name].lat[a] === null;
        const want = !inRange ? "out" : (isNull ? "nocrust" : "here");
        if (st !== want) stateBad++;
      }
    }
  }
  if (stateBad) fails.push(`2/3. ${stateBad} states wrong or not exhaustive`);
  console.log(`  2. states exhaustive and disjoint over `
    + `${D.tracks.length * D.ages.length} views, ${stateBad} faults`);
  console.log(`  3. ${ncTotal} no-crust and ${outTotal} out-of-range cases, `
    + "counted separately");

  // 4 ------------------------------------------------------------------
  app.set(0, 7);
  let interp = 0;
  for (const m of D.models) {
    if (app.state(m) !== "here") continue;
    const p = app.pos(m), tr = D.tracks[0].models[m.name];
    if (p[0] !== tr.lon[7] || p[1] !== tr.lat[7]) interp++;
  }
  if (interp) fails.push(`4. ${interp} drawn positions are not payload entries`);
  console.log(`  4. drawn positions are payload entries, ${interp} interpolated`);

  // 5 ------------------------------------------------------------------
  let worstDiff = 0;
  for (let p = 0; p < D.tracks.length; p += 3) {
    for (let a = 0; a < D.ages.length; a += 7) {
      app.set(p, a);
      const shown = D.models.filter((m) => app.state(m) === "here");
      for (let i = 0; i < shown.length; i++) {
        for (let j = i + 1; j < shown.length; j++) {
          const A = app.pos(shown[i]), B = app.pos(shown[j]);
          const mine = 2 * 6371.0088 * Math.asin(Math.min(1, Math.sqrt(
            Math.sin(((B[1] - A[1]) * Math.PI / 180) / 2) ** 2
            + Math.cos(A[1] * Math.PI / 180) * Math.cos(B[1] * Math.PI / 180)
            * Math.sin(((B[0] - A[0]) * Math.PI / 180) / 2) ** 2)));
          worstDiff = Math.max(worstDiff, Math.abs(mine - app.gc(A, B)));
        }
      }
    }
  }
  if (worstDiff > 1e-6) fails.push(`5. distances differ by ${worstDiff}`);
  console.log(`  5. great-circle parity, worst difference `
    + `${worstDiff.toExponential(1)} km`);

  // 7 ------------------------------------------------------------------
  const blob = JSON.stringify(D).toLowerCase();
  const pinned = D.models.length === 8 && !blob.includes("default");
  if (!pinned) fails.push("7. the payload is not eight explicitly named models");
  console.log(`  7. ${D.models.length} models named, fetched ${D.fetched}, `
    + "no default referenced");

  // 8 ------------------------------------------------------------------
  const empty = W.document.getElementById("empty");
  let emptyBad = 0;
  for (let p = 0; p < D.tracks.length; p++) {
    for (let a = 0; a < D.ages.length; a += 5) {
      app.set(p, a);
      const c = app.counts();
      const shows = empty.style.display === "flex";
      if (shows !== (c.here === 0)) emptyBad++;
    }
  }
  if (emptyBad) fails.push(`8. the empty message is wrong in ${emptyBad} views`);
  console.log(`  8. empty stage shown exactly when nothing is drawn, `
    + `${emptyBad} faults`);

  // 9, 10 --------------------------------------------------------------
  const LAND = W.LAND;
  if (!LAND) {
    fails.push("9. the land asset did not load; the viewer draws no continents");
    console.log("  9. LAND missing");
  } else {
    let missing = 0, badpt = 0, rings = 0, pts = 0;
    for (const m of LAND.models) {
      for (const a of D.ages) {
        const r = app.landRings(m, a);
        if (!r || !r.length) { missing++; continue; }
        rings += r.length;
        for (const ring of r) {
          pts += ring.length;
          for (const [lo, la] of ring) {
            if (!(lo >= -181 && lo <= 181) || !(la >= -91 && la <= 91)) badpt++;
          }
        }
      }
    }
    if (missing || badpt) fails.push(
      `9. ${missing} ages with no land and ${badpt} decoded points off the globe`);
    console.log(`  9. ${LAND.models.length} land models x ${D.ages.length} ages, `
      + `${missing} missing, ${rings.toLocaleString()} rings, `
      + `${pts.toLocaleString()} points, ${badpt} off the globe`);

    /* The models do not share a coastline dataset, so at 0 Ma they are not
       byte-identical - PALEOMAP is not EarthByte's outline. What they must
       agree with is the Earth: land is about 29 per cent of the surface, and
       every model at every age has to stay in a plausible band, which is
       also what catches a delta-encoded ring that accumulates wrong and
       drifts. And at older ages they must actually differ, or the selector
       is telling the reader the models agree. */
    const areaPct = (rings) => {
      let tot = 0;
      for (const pts of rings) {
        let s = 0;
        for (let i = 0; i < pts.length - 1; i++) {
          const x1 = pts[i][0] * Math.PI / 180, y1 = Math.sin(pts[i][1] * Math.PI / 180);
          const x2 = pts[i + 1][0] * Math.PI / 180, y2 = Math.sin(pts[i + 1][1] * Math.PI / 180);
          s += x1 * y2 - x2 * y1;
        }
        tot += Math.abs(s) / 2;
      }
      return tot / (4 * Math.PI) * 100;
    };
    const EARTH_LAND = 29.2;
    let a0 = [], worstBand = null;
    for (const m of LAND.models) {
      a0.push(areaPct(app.landRings(m, 0)));
      for (const a of D.ages) {
        const r = app.landRings(m, a);
        if (!r) continue;
        const pc = areaPct(r);
        if (pc < 15 || pc > 40) worstBand = `${m}@${a} = ${pc.toFixed(1)}%`;
      }
    }
    const off = a0.filter((p) => Math.abs(p - EARTH_LAND) > 3).length;
    if (off) fails.push(
      `10. ${off} land models disagree with Earth's land fraction at 0 Ma`);
    if (worstBand) fails.push(`10. implausible land area at ${worstBand}`);
    console.log(`  10. land at 0 Ma: ${a0.map((p) => p.toFixed(1) + "%").join(", ")} `
      + `against Earth's ${EARTH_LAND}%; every age inside 15-40%`);

    let sameOld = 0, cmpOld = 0;
    for (let i = 1; i < LAND.models.length; i++) {
      for (const a of [100, 200, 300, 400]) {
        cmpOld++;
        if (JSON.stringify(app.landRings(LAND.models[0], a))
            === JSON.stringify(app.landRings(LAND.models[i], a))) sameOld++;
      }
    }
    if (sameOld) fails.push(
      `11. ${sameOld} of ${cmpOld} land-model pairs are identical at older ages`);
    console.log(`  11. the models draw different worlds in ${cmpOld - sameOld} `
      + `of ${cmpOld} comparisons at 100 to 400 Ma`);
  }

  console.log("");
  if (fails.length) {
    console.log("FAIL");
    for (const f of fails) console.log("  - " + f);
    return 1;
  }
  console.log("ok");
  return 0;
}

process.exit(main());
