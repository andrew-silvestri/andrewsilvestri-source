/* kit_render.js - run the insight kit's chart code at build time (R1).
 *
 * insight.py pipes {spec, states} in as JSON and reads back the static SVG
 * each step shows when the page is not animating, at the two widths that
 * ship, plus Charts.check()'s sweep of every width in between. It requires
 * site/assets/charts.js itself, so the static figures are drawn by the same
 * code the browser runs - there is no second renderer to drift.
 */
'use strict';
const path = require('path');
const Charts = require(path.join(__dirname, 'site', 'assets', 'charts.js'));

let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => { buf += d; });
process.stdin.on('end', () => {
  const job = JSON.parse(buf), out = { wide: [], phone: [], problems: [] };
  try {
    job.states.forEach((st, i) => {
      out.wide.push(Charts.render(job.spec, st, { width: Charts.WIDE, strict: true, suffix: '-w' + i }));
      out.phone.push(Charts.render(job.spec, st, { width: Charts.PHONE, strict: true, suffix: '-p' + i }));
    });
    out.problems = Charts.check(job.spec);
  } catch (e) { out.problems.push(e.message); }
  process.stdout.write(JSON.stringify(out));
});
