"""Download one public file into safetynet/data/raw/ and record where it came from.

Every fetch goes through `fetch()`, which streams the file to disk and appends a row to
data/fetched.json: the URL, the request body if the source is a form or an API (POST), the date it
ran, the byte count and the SHA-1. The build reads that manifest through `verified()` and refuses a
raw file it does not list or whose bytes have changed, so a file put there by hand, or a placeholder,
cannot reach a payload (HANDOFF trap 18), and the check is recomputed from the file the build reads,
not read back from the manifest (trap 20). The idiom is ethane/netfetch.py's.
"""
import datetime as _dt
import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MANIFEST = HERE / "data" / "fetched.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) andrewsilvestri.com safetynet fetch"
BLOCK = 1 << 20


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def record(name, url, via, body=None):
    p = RAW / name
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    row = {"url": url, "fetched": _dt.date.today().isoformat(), "bytes": p.stat().st_size,
           "sha1": _sha1(p), "via": via}
    if body is not None:
        row["post"] = body
    rows[name] = row
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{name}: {p.stat().st_size:,} bytes via {via}")
    return p


def fetch(url, name, body=None, content_type=None, accept=None, timeout=300):
    """GET, or POST `body` (a str) when given. `accept` sets the Accept header (OECD SDMX)."""
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    tmp = out.with_suffix(out.suffix + ".part")
    headers = {"User-Agent": UA}
    if content_type:
        headers["Content-Type"] = content_type
    if accept:
        headers["Accept"] = accept
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
        for b in iter(lambda: r.read(BLOCK), b""):
            f.write(b)
    tmp.replace(out)
    return record(name, url, "urllib POST" if body is not None else "urllib", body)


def verified(name):
    """Path to a raw file and its manifest row, after re-hashing it. Raises if absent or changed."""
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = rows[name]
    if _sha1(RAW / name) != row["sha1"]:
        raise RuntimeError(f"{name} does not match data/fetched.json; re-run the fetch script that writes it")
    return RAW / name, row
