"""Fetch ERCOT's public historical settlement point prices, one zip per year.

Two reports on ERCOT's Market Information System, both public (no login):
  13060  Historical DAM Load Zone and Hub Prices   (NP4-180-ER), hourly
  13061  Historical RTM Load Zone and Hub Prices   (NP6-785-ER), 15-minute
The report listing is read each run, so the current year's file (which ERCOT
replaces in place as the year goes on) is fetched under the name ERCOT gives it.

ERCOT's website terms (https://www.ercot.com/help/terms, s.5): raw data in the
public portions of the site "may be used, reproduced, and redistributed in
compilations, charts, and analyses". Recorded in SOURCES Part 7.

    python storage/fetch_ercot.py            # every year listed, skipping files already recorded
    python storage/fetch_ercot.py 2024 2025  # just these years
"""
import json
import re
import sys
import urllib.request

import netfetch as N

LIST = "https://www.ercot.com/misapp/GetReports.do?reportTypeId={rt}"
DOC = "https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId={doc}"
REPORTS = {"DAM": 13060, "RTM": 13061}


def listing(rt):
    req = urllib.request.Request(LIST.format(rt=rt), headers={"User-Agent": N.UA})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    names = re.findall(r">([^<>]*?(?:DAM|RTM)LZHBSPP_(\d{4})\.zip)<", html)
    docs = re.findall(r"doclookupId=(\d+)", html)
    if len(names) != len(docs) or not names:
        raise RuntimeError(f"report {rt}: {len(names)} names and {len(docs)} links; the listing changed shape")
    return [(name, int(year), doc) for (name, year), doc in zip(names, docs)]


def main(years):
    have = json.loads(N.MANIFEST.read_text(encoding="utf-8")) if N.MANIFEST.exists() else {}
    for kind, rt in REPORTS.items():
        for name, year, doc in listing(rt):
            if years and year not in years:
                continue
            local = f"{kind}_{year}.zip"
            if local in have and have[local].get("ercot_name") == name:
                print(f"{local}: already have {name}")
                continue
            N.fetch(DOC.format(doc=doc), local)
            rows = json.loads(N.MANIFEST.read_text(encoding="utf-8"))
            rows[local]["ercot_name"] = name
            with open(N.MANIFEST, "w", encoding="utf-8", newline="\n") as f:
                json.dump(rows, f, indent=1, sort_keys=True)
                f.write("\n")


if __name__ == "__main__":
    main({int(a) for a in sys.argv[1:]})
