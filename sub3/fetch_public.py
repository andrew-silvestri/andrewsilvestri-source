"""The public files the sub-3 page reads, fetched into sub3/data/raw/ and recorded in data/fetched.json.

BMW Berlin Marathon Results 1999-2025 (Seffrin, Villiger, Andrade, Rosemann, Weiss, Ferreira, Knechtle;
Zenodo record 19342683, doi:10.5281/zenodo.19342683, published 31 March 2026, CC BY 4.0). One
semicolon-separated file: 880,779 official results with net finish time and splits at 5, 10, 15, 20 km,
halfway, 25, 30, 35 and 40 km, sex and age group. The record publishes the file's MD5; fetch() refuses a
download whose MD5 differs, and records the SHA-1 that build_sub3.py checks before it reads a byte.

Deutscher Wetterdienst hourly air temperature at Berlin-Tempelhof (station 433), for the morning of
each race.

The Berlin file holds runners' names. The build reads only the year, sex, age group and times, and nothing it
writes carries a name.

Run:  python fetch_public.py
"""
import datetime as dt
import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
MANIFEST = HERE / "data" / "fetched.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) andrewsilvestri.com sub3 fetch"
BLOCK = 1 << 20

FILES = {
    "berlin_1999_2025.csv": {
        "url": "https://zenodo.org/api/records/19342683/files/Dataset_Berlin_Marathon_1999-2025_original.csv/content",
        "md5": "7f6be8bb8f0f8d002ed952cf084e6bae",
        "record": "https://doi.org/10.5281/zenodo.19342683",
    },
    # Deutscher Wetterdienst, Climate Data Center: hourly air temperature and relative humidity at station
    # 433, Berlin-Tempelhof, 1951 to 2025 (DWD open data, free under the GeoNutzV / CC BY 4.0 terms). DWD
    # publishes no checksum, so the manifest's SHA-1 is the only pin. DWD renames the file when it adds a
    # year; a new name means a new edit here, not a silent change.
    "stundenwerte_TU_00433_19510101_20251231_hist.zip": {
        "url": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
               "air_temperature/historical/stundenwerte_TU_00433_19510101_20251231_hist.zip",
        "md5": None,
        "record": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/"
                  "air_temperature/historical/",
    },
}


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def record(name, via):
    p = RAW / name
    if FILES[name]["md5"] and digest(p, "md5") != FILES[name]["md5"]:
        raise SystemExit(f"{name}: MD5 differs from the Zenodo record's; not recorded")
    rows = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    rows[name] = {"url": FILES[name]["url"], "record": FILES[name]["record"], "fetched": dt.date.today().isoformat(),
                  "bytes": p.stat().st_size, "md5": FILES[name]["md5"], "sha1": digest(p, "sha1"), "via": via}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{name}: {p.stat().st_size:,} bytes" + (", MD5 matches the record" if FILES[name]["md5"] else "")
          + f" ({via})")


def fetch(name):
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / name
    tmp = out.with_suffix(".part")
    req = urllib.request.Request(FILES[name]["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        for b in iter(lambda: r.read(BLOCK), b""):
            f.write(b)
    tmp.replace(out)
    record(name, "urllib")


def verified(name):
    """The path of a raw file whose bytes match the manifest; the build calls this before reading."""
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    p = RAW / name
    if name not in rows or not p.exists() or digest(p, "sha1") != rows[name]["sha1"]:
        raise SystemExit(f"{name}: missing or not the recorded bytes; run python fetch_public.py")
    return p


if __name__ == "__main__":
    import sys
    for n in FILES:
        if (RAW / n).exists() and "--refetch" not in sys.argv:
            record(n, "already on disk")
        else:
            fetch(n)
