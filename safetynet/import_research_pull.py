"""Record the three BLS LAUS responses that the research step pulled on 2026-11-07, under the names
fetch_public.py uses, when the keyless BLS API quota for the day is spent. The bytes are the API's
own JSON response, unchanged; the manifest row says where they came from and how.

Run:  python import_research_pull.py <folder holding bls-api-v1-laus-*-2016-2025.json>
"""
import json
import shutil
import sys
from pathlib import Path

import fetch_public as F
import netfetch

NAMES = ["bls-api-v1-laus-AL-MS-2016-2025.json", "bls-api-v1-laus-MO-WI-2016-2025.json",
         "bls-api-v1-laus-WY-PR-2016-2025.json"]

if __name__ == "__main__":
    src = Path(sys.argv[1])
    netfetch.RAW.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(NAMES):
        d = json.loads((src / f).read_text(encoding="utf-8"))
        if d.get("status") != "REQUEST_SUCCEEDED":
            raise SystemExit(f"{f}: not a successful BLS response")
        ids = [s["seriesID"] for s in d["Results"]["series"]]
        shutil.copy(src / f, netfetch.RAW / f"bls_laus_{i}.json")
        body = json.dumps({"seriesid": ids, "startyear": "2016", "endyear": "2025"})
        netfetch.record(f"bls_laus_{i}.json", F.BLS,
                        "urllib POST, 2026-11-07, by the research pull; copied (keyless daily quota spent)", body)
