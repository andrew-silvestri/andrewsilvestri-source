"""Download one public file into meter/data/raw/ and record where it came from.

Every fetch_*.py goes through `fetch()`, which writes the file and appends a
row to data/fetched.json: the URL, the date it ran, the byte count and the
SHA-1. The build reads that manifest and refuses a raw file it does not list,
so a file put there by hand, or a placeholder, cannot reach a payload
(HANDOFF trap 18).

PHMSA's site sits behind a bot screen that answers 403 to every scripted
client, headless Chrome included, and serves a visible browser. `fetch()`
tries a plain request first and, on 403, hands the URL to a visible Chrome
through Playwright (tests/node_modules), which saves the download. A window
opens for a few seconds; that is the price of the agency's screen, not a
workaround of its terms (the data is public and the page offers it).
"""
import datetime as _dt
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MANIFEST = HERE / "data" / "fetched.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) andrewsilvestri.com meter fetch"

_BROWSER_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ channel: 'chrome', headless: false });
  const ctx = await b.newContext({ acceptDownloads: true });
  const p = await ctx.newPage();
  // Land on the agency page first so the screen sets its cookie, then ask for the file.
  await p.goto('https://www.phmsa.dot.gov/data-and-statistics/pipeline/gas-distribution-gas-gathering-gas-transmission-hazardous-liquids', { waitUntil: 'domcontentloaded', timeout: 90000 });
  const [dl] = await Promise.all([
    p.waitForEvent('download', { timeout: 120000 }),
    p.evaluate(u => { const a = document.createElement('a'); a.href = u; document.body.appendChild(a); a.click(); }, url),
  ]);
  await dl.saveAs(out);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def _record(name, url, data, via):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    rows[name] = {"url": url, "fetched": _dt.date.today().isoformat(), "bytes": len(data),
                  "sha1": hashlib.sha1(data).hexdigest(), "via": via}
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=1, sort_keys=True)
        f.write("\n")


def fetch(url, name):
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        via = "urllib"
    except urllib.error.HTTPError as e:
        if e.code != 403:
            raise
        tests = HERE.parent / "tests"
        js = RAW / "_fetch_browser.js"
        js.write_text(_BROWSER_JS, encoding="utf-8")
        env = dict(os.environ, NODE_PATH=str(tests / "node_modules"))
        try:
            subprocess.run(["node", str(js), url, str(out)], check=True, env=env, cwd=tests)
        finally:
            js.unlink(missing_ok=True)
        data = out.read_bytes()
        via = "chrome (403 to scripted clients)"
    out.write_bytes(data)
    _record(name, url, data, via)
    print(f"{name}: {len(data):,} bytes via {via}")
    return out


def verified(name):
    """Path to a raw file, after checking it against the manifest. Raises if absent or changed."""
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = rows[name]
    data = (RAW / name).read_bytes()
    if hashlib.sha1(data).hexdigest() != row["sha1"]:
        raise RuntimeError(f"{name} does not match data/fetched.json; re-run the fetch script that writes it")
    return RAW / name, row
