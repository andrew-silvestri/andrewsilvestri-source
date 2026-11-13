"""Download one public file into nightshift/data/raw/ and record where it came from.

Every fetch goes through `fetch()`, which streams the file to disk and appends a row to
data/fetched.json: the URL, the date it ran, the byte count and the SHA-1. The build reads that
manifest through `verified()` and refuses a raw file it does not list or whose bytes have changed,
so a file put there by hand, or a placeholder, cannot reach a payload (HANDOFF trap 18), and the
check is recomputed from the file the build reads, not read back from the manifest (trap 20).
The idiom is lead/netfetch.py's.

www.bls.gov answers 403 to a request that does not look like a browser's navigation (a bare
User-Agent is not enough), so the request carries the headers a browser sends for a typed URL.
"""
import datetime as _dt
import gzip
import hashlib
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MANIFEST = HERE / "data" / "fetched.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Dest": "document",
    "Upgrade-Insecure-Requests": "1",
}
BLOCK = 1 << 20


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def record(name, url, via):
    p = RAW / name
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    rows[name] = {"url": url, "fetched": _dt.date.today().isoformat(), "bytes": p.stat().st_size,
                  "sha1": _sha1(p), "via": via}
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{name}: {p.stat().st_size:,} bytes via {via}")
    return p


def fetch(url, name, timeout=300, tries=3):
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    tmp = out.with_suffix(out.suffix + ".part")
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
            tmp.write_bytes(body)
            tmp.replace(out)
            return record(name, url, "urllib")
        except Exception as e:          # a 403 from a busy server is usually transient
            last = e
            time.sleep(10 * (k + 1))
    raise SystemExit(f"{name}: {last}")


def verified(name):
    """Path to a raw file and its manifest row, after re-hashing it. Raises if absent or changed."""
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = rows[name]
    if _sha1(RAW / name) != row["sha1"]:
        raise RuntimeError(f"{name} does not match data/fetched.json; re-run the fetch script that writes it")
    return RAW / name, row
