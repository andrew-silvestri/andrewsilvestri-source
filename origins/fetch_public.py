"""
Download the two public databases origins/ reads into data/raw (gitignored), and check each file's SHA-1
against the copy the page was built from.

  ASHRAE Global Thermal Comfort Database II, v2.1.0, Zenodo record 4993952, CC BY 4.0
  MARHYS (MARine HYdrothermal Solutions) Database 3.0, PANGAEA 958978, CC BY 4.0

Then:  python analyse_ashrae.py
       python marhys_lostcity.py data/raw/MARHYS_DB_3_0.xlsx data/lost_city_marhys3.csv
       python build_origins.py
       python update_page.py --apply

Run:  python fetch_public.py
"""
import hashlib
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
FILES = [
    ("db_measurements_v2.1.0.csv.gz",
     "https://zenodo.org/records/4993952/files/db_measurements_v2.1.0.csv.gz?download=1",
     "81cdad28c1654679cabf9eb0dd8eb08df52b85d0"),
    ("db_metadata.csv",
     "https://zenodo.org/records/4993952/files/db_metadata.csv?download=1",
     "376981ac66b3e28c8252dd5b3f0ddfd651789972"),
    ("MARHYS_DB_3_0.xlsx",
     "https://download.pangaea.de/dataset/958978/files/MARHYS_DB_3_0.xlsx",
     "2fa82d915ddd46bf4b594c1aac7410352ee7e838"),
]


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(RAW, exist_ok=True)
    bad = 0
    for name, url, want in FILES:
        path = os.path.join(RAW, name)
        if not os.path.exists(path):
            req = urllib.request.Request(url, headers={"User-Agent": "origins-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
        got = sha1(path)
        ok = got == want
        bad += not ok
        print(f"  {name}: {'ok' if ok else 'SHA-1 differs: ' + got}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
