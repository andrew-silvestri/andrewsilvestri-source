"""The public files the messaging page reads, fetched into messaging/data/raw/ and recorded in data/fetched.json.

- data63.xlsx: Vlasceanu et al. (2024), "Addressing climate change with behavioral science: A global
  intervention tournament in 63 countries", Science Advances 10, eadj5778. The participant-level data the
  authors posted on Zenodo (record 10345806), 59,440 participants.
- zenodo_10345806.json: the Zenodo API record of that deposit. fetch checks the downloaded file's MD5
  against the checksum Zenodo publishes there, so the file is the one the authors deposited.

The field effects the page charts (data/effects.csv), the replication pairs (data/shrink.csv) and the kit
(data/kit.csv) are transcribed from the papers, each row with the table or page it was read from; most of
those papers are behind publishers' terms that do not allow a copy here.

Run:  python fetch_public.py
"""
import hashlib
import json

from netfetch import RAW, fetch

RECORD = "https://zenodo.org/api/records/10345806"
FILES = {
    "zenodo_10345806.json": RECORD,
    "data63.xlsx": "https://zenodo.org/records/10345806/files/data63.xlsx?download=1",
}


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def zenodo_md5(name):
    rec = json.loads((RAW / "zenodo_10345806.json").read_text(encoding="utf-8"))
    for f in rec["files"]:
        if f["key"] == name:
            return f["checksum"].split(":", 1)[1]
    raise SystemExit(f"{name} is not in the Zenodo record")


if __name__ == "__main__":
    for name, url in FILES.items():
        fetch(url, name)
    want, got = zenodo_md5("data63.xlsx"), md5(RAW / "data63.xlsx")
    if want != got:
        raise SystemExit(f"data63.xlsx MD5 {got} differs from Zenodo's {want}")
    print(f"data63.xlsx MD5 {got} matches the Zenodo record")
