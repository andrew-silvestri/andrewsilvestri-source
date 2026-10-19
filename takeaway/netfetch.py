"""Download one public file into takeaway/data/raw/ and record where it came from.

Every fetch_*.py goes through `fetch()`, which streams the file to disk and
appends a row to data/fetched.json: the URL, the date it ran, the byte count
and the SHA-1. The build reads that manifest through `verified()` and refuses
a raw file it does not list or whose bytes have changed, so a file put there
by hand, or a placeholder, cannot reach a payload (HANDOFF trap 18), and the
check is recomputed from the file the build reads, not read back from the
manifest (trap 20).

Streams in 1 MB blocks because the RRC production dump is several gigabytes
and meter/netfetch.py, which this is adapted from, reads a whole file into
memory.
"""
import datetime as _dt
import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MANIFEST = HERE / "data" / "fetched.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) andrewsilvestri.com takeaway fetch"
BLOCK = 1 << 20


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def record(name, url, via):
    """Add a manifest row for a file already in RAW (used when a browser saved it)."""
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


def fetch(url, name, timeout=300):
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    tmp = out.with_suffix(out.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
        for b in iter(lambda: r.read(BLOCK), b""):
            f.write(b)
    tmp.replace(out)
    return record(name, url, "urllib")


def verified(name):
    """Path to a raw file and its manifest row, after re-hashing it. Raises if absent or changed."""
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    row = rows[name]
    if _sha1(RAW / name) != row["sha1"]:
        raise RuntimeError(f"{name} does not match data/fetched.json; re-run the fetch script that writes it")
    return RAW / name, row
