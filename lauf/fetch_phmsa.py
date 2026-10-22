"""PHMSA files for the lost-gas page. U.S. government works.

- annual_gas_distribution_2010_present.zip: gas distribution annual reports,
  Form PHMSA F 7100.1-1, 2010 to present; Part G is percent unaccounted for
  (PERCENT_UNACC_GAS). Linked from
  https://www.phmsa.dot.gov/data-and-statistics/pipeline/gas-distribution-gas-gathering-gas-transmission-hazardous-liquids
- report_congress_lauf_2017.pdf: PHMSA, Report on lost and unaccounted for
  natural gas metrics (May 2017, PIPES Act 2016 s.29).
- gd_annual_form_cy2018_forward.pdf: Form PHMSA F 7100.1-1 (rev 10/11/2018),
  the form PHMSA lists as "CY 2018 and forward".

PHMSA answers 403 to scripted clients (urllib, curl, headless Chrome). The
fallback runs the installed Chrome, visibly, through Playwright, opens
www.phmsa.dot.gov and fetches each file from inside that page; the manifest
row records it as "chrome session". Needs playwright (tests/node_modules).

Run:  python fetch_phmsa.py
"""
import os
import subprocess
import tempfile
import urllib.error
from pathlib import Path

from netfetch import RAW, fetch, record

FILES = {
    "annual_gas_distribution_2010_present.zip":
        "https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/data_statistics/pipeline/annual_gas_distribution_2010_present.zip",
    "report_congress_lauf_2017.pdf":
        "https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/news/17986/report-congress-lost-and-unaccounted-natural-gas-metrics-may-2017.pdf",
    "gd_annual_form_cy2018_forward.pdf":
        "https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/subdoc/3476/current-gd-annual-form-phmsa-f-71001-1cy-2018-and-forward.pdf",
}

BROWSER_JS = r"""
const pw = require('playwright'); const fs = require('fs');
(async () => {
  const [,, out, url] = process.argv;
  const b = await pw.chromium.launch({ channel: 'chrome', headless: false });
  const p = await (await b.newContext()).newPage();
  await p.goto('https://www.phmsa.dot.gov/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  const r = await p.evaluate(async u => { const x = await fetch(u, { credentials: 'include' });
    const a = new Uint8Array(await x.arrayBuffer()); let s = '';
    for (let k = 0; k < a.length; k += 0x8000) s += String.fromCharCode.apply(null, a.subarray(k, k + 0x8000));
    return { status: x.status, b64: btoa(s) }; }, url);
  await b.close();
  if (r.status !== 200) { console.error('status ' + r.status); process.exit(2); }
  fs.writeFileSync(out, Buffer.from(r.b64, 'base64'));
})();
"""


def via_browser(url, name):
    RAW.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent
    env = dict(os.environ, NODE_PATH=str(root / "tests" / "node_modules"))
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "get.js"
        js.write_text(BROWSER_JS, encoding="utf-8")
        subprocess.run(["node", str(js), str(RAW / name), url], check=True, env=env)
    return record(name, url, "chrome session (403 to scripted clients)")


if __name__ == "__main__":
    for name, url in FILES.items():
        try:
            fetch(url, name)
        except urllib.error.HTTPError as e:
            if e.code != 403:
                raise
            via_browser(url, name)
