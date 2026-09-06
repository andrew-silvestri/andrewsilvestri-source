"""
The group-level inputs for the first figure: how many species each vertebrate
class has, how many are threatened, and how many papers name the class.

  1. IUCN Red List Table 1a (PDF; the summary-statistics page offers no
     other format) -> data/iucn_table1a.csv, one row per group with the
     described, evaluated and threatened counts and the Red List version.
     The table is a published aggregate and is cited, not redistributed.
  2. OpenAlex works 2015-2024 whose title or abstract names the class,
     restricted to works whose primary topic is in Agricultural and
     Biological Sciences or Environmental Science -> data/group_counts.csv.
     Five classes only: Stage 1 showed the name-based proxy fails outside
     vertebrates (papers on rice do not say "angiosperm"), so no other
     group is fetched or drawn.

Run:  python3 fetch_groups.py            (OPENALEX_KEY optional; 10 calls)
"""

import csv
import datetime as dt
import hashlib
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from netutil import get_json, Budget, UA  # noqa: E402

RAW = os.path.join(HERE, "data", "raw")
VERSION = "2026-1"
PDF_URL = f"https://nc.iucnredlist.org/redlist/content/attachment_files/{VERSION}_RL_Table1a.pdf"
PDF = os.path.join(RAW, f"iucn_table1a_{VERSION}.pdf")
PDF_SHA = "fefba9c933226cb5e9c8c616ee41d16cd339cfa00ebe3aadf842542f4540fc10"
TABLE_OUT = os.path.join(HERE, "data", "iucn_table1a.csv")
COUNTS_OUT = os.path.join(HERE, "data", "group_counts.csv")
MAILTO = "dasilvestri@utexas.edu"
TOPIC = "primary_topic.field.id:11|23"
YEARS = "2015-2024"

CLASSES = {
    "Mammals": "mammal OR mammals OR mammalia OR mammalian",
    "Birds": "bird OR birds OR aves OR avian",
    "Reptiles": "reptile OR reptiles OR reptilia OR squamata OR testudines OR crocodylia",
    "Amphibians": "amphibian OR amphibians OR amphibia OR anura OR caudata OR gymnophiona",
    "Fishes": "fish OR fishes OR teleost OR elasmobranch OR chondrichthyes OR actinopterygii",
}

# A row is "Name[ footnote] described evaluated x% threatened" then either
# three percentages or the words "Insufficient coverage" (groups under 80%
# evaluated, for which IUCN prints no % threatened).
ROW = re.compile(r"^([A-Za-z][A-Za-z &.,]+?)\s*\d{0,2}\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)%\s+([\d,]+)"
                 r"(?:\s+(\d+)%\s+(\d+)%\s+(\d+)%|\s+Insufficient coverage)?\s*$")


def fetch_pdf():
    os.makedirs(RAW, exist_ok=True)
    if not os.path.exists(PDF):
        print(f"  downloading {PDF_URL}")
        req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0 " + UA})
        with urllib.request.urlopen(req, timeout=120) as r, open(PDF, "wb") as fh:
            fh.write(r.read())
    h = hashlib.sha256(open(PDF, "rb").read()).hexdigest()
    if h != PDF_SHA:
        sys.exit(f"  SHA-256 mismatch for {os.path.basename(PDF)}\n    got      {h}\n    expected {PDF_SHA}\n"
                 f"  IUCN has re-issued the {VERSION} table; check it, re-pin, and re-run.")
    print(f"  {os.path.basename(PDF)} verified")
    return h


def parse_table():
    from pypdf import PdfReader
    txt = PdfReader(PDF).pages[0].extract_text(extraction_mode="layout")
    txt = "\n".join(re.sub(r"\s{2,}", " ", ln).strip() for ln in txt.splitlines())
    m = re.search(r"IUCN Red List version (\S+): Table 1a", txt)
    version = m.group(1) if m else VERSION
    upd = re.search(r"Last updated: ([^\n]+)", txt)
    updated = upd.group(1).strip() if upd else ""
    section, rows = None, []
    for line in txt.splitlines():
        head = line.strip().split(" ")[0].upper() if line.strip() else ""
        if head in ("VERTEBRATES", "INVERTEBRATES", "PLANTS", "FUNGI"):
            section = head.title()
            continue
        mm = ROW.match(line)
        if not mm:
            continue
        name = mm.group(1).strip()
        if name in ("Subtotal", "TOTAL"):
            continue

        def n(s):
            return int(s.replace(",", ""))
        rows.append({"group": name, "section": section, "described": n(mm.group(2)),
                     "evaluated": n(mm.group(3)), "pct_evaluated": float(mm.group(4)),
                     "threatened": n(mm.group(5)), "pct_threatened_low": mm.group(6) or "",
                     "pct_threatened_best": mm.group(7) or "", "pct_threatened_high": mm.group(8) or "",
                     "source": f"IUCN Red List {version} Table 1a (last updated {updated}), {PDF_URL}"})
    if len(rows) < 20 or not all(g in {r["group"] for r in rows} for g in CLASSES):
        sys.exit(f"  parsed {len(rows)} rows from {PDF}; expected 21 with the five vertebrate classes")
    with open(TABLE_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {len(rows)} groups, Red List {version} -> {os.path.relpath(TABLE_OUT, HERE)}")


def fetch_counts():
    key = os.environ.get("OPENALEX_KEY", "").strip()
    today = dt.date.today().isoformat()
    rows = []
    try:
        for g, q in CLASSES.items():
            flt = f"title_and_abstract.search:{q},{TOPIC},publication_year:{YEARS}"
            params = {"filter": flt, "per-page": 1, "mailto": MAILTO}
            if key:
                params["api_key"] = key
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            j = get_json(url)
            rows.append({"group": g, "search": q, "topic_filter": TOPIC, "years": YEARS,
                         "works": j["meta"]["count"], "cost_usd": j["meta"].get("cost_usd", ""),
                         "fetched": today, "url": url.replace(key, "OPENALEX_KEY") if key else url})
            print(f"  {g:12s} {j['meta']['count']:>9,}")
            time.sleep(0.3)
    except Budget as e:
        print(f"  stopped: {e}; group_counts.csv left as it was")
        return
    with open(COUNTS_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  -> {os.path.relpath(COUNTS_OUT, HERE)}")


if __name__ == "__main__":
    from netutil import Lock
    with Lock("groups", HERE):
        fetch_pdf()
        parse_table()
        fetch_counts()
