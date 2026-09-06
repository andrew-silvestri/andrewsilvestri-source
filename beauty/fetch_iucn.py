"""
Red List category per bird species, from the IUCN Red List API v4 with the
reader's own token.

The Red List's terms of use (v3.1, June 2024) forbid redistributing Red
List data, in whole or in part, by any means including web downloads, so no
file this script writes is in the code archive or in git: the raw pages go
to data/raw/iucn_aves/ and the slim table to data/iucn_aves.csv, both
ignored. The one thing the terms leave unrestricted is "use of the IUCN Red
List Categories associated with each named taxonomic entity", which is the
only field this project uses. The token is personal to the account that
requested it: get one at https://api.iucnredlist.org/ (a form; the key
arrives by email, usually within a day or two), then set IUCN_TOKEN in the
environment. Nothing is read from disk.

Calls /api/v4/taxa/class/Aves page by page (100 assessments a page, about
120 pages), half a second apart as the IUCN R client recommends, and keeps
the latest global assessment per scientific name.

Writes data/iucn_aves.csv: species, category, year_published,
assessment_id, red_list_version. Cite as: IUCN <year>. The IUCN Red List of
Threatened Species. Version <version>. https://www.iucnredlist.org.

Run:  python3 fetch_iucn.py
"""

import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from netutil import get_json, need_key, Budget, Lock  # noqa: E402

RAW = os.path.join(HERE, "data", "raw", "iucn_aves")
OUT = os.path.join(HERE, "data", "iucn_aves.csv")
API = "https://api.iucnredlist.org/api/v4"


def find(d, *names):
    """First of several possible field names, so a rename in the API shows
    up as a blank column rather than a crash."""
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return ""


def main():
    token = os.environ.get("IUCN_TOKEN", "").strip()
    if not token:
        need_key("IUCN_TOKEN", "https://api.iucnredlist.org/ (Register, then Generate a token)",
                 "sent by email, usually within one to two days")
    hdr = {"Authorization": token if token.lower().startswith("bearer") else f"Bearer {token}"}
    os.makedirs(RAW, exist_ok=True)
    ver = get_json(f"{API}/information/red_list_version", headers=hdr) or {}
    version = find(ver, "red_list_version", "version")
    print(f"  Red List version {version or '?'}")
    best = {}
    page, n = 1, 0
    complete = False
    lk = Lock("iucn", HERE)
    lk.__enter__()
    try:
        while True:
            cache = os.path.join(RAW, f"page_{page:04d}.json")
            if os.path.exists(cache):
                j = json.load(open(cache, encoding="utf-8"))
            else:
                j = get_json(f"{API}/taxa/class/Aves?page={page}&per_page=100&latest=true",
                             headers=hdr)
                if j is None:
                    complete = True
                    break
                json.dump(j, open(cache, "w", encoding="utf-8"))
                time.sleep(0.5)
            lk.beat()
            items = j.get("assessments") or j.get("result") or []
            if not items:
                complete = True
                break
            for a in items:
                scopes = a.get("scopes") or []
                codes = {str(s.get("code", "")) for s in scopes if isinstance(s, dict)}
                if scopes and "1" not in codes:
                    continue                       # regional assessment
                name = find(a, "taxon_scientific_name", "scientific_name")
                cat = find(a, "red_list_category_code", "category", "red_list_category")
                yr = str(find(a, "year_published", "assessment_year"))
                if not name:
                    continue
                if name not in best or yr > best[name][1]:
                    best[name] = (cat, yr, find(a, "assessment_id", "id"))
            n += len(items)
            print(f"  page {page}: {len(items)} assessments, {len(best):,} species so far")
            page += 1
    except Budget as e:
        print(f"  stopped: {e}")
    finally:
        lk.__exit__()
    # The table is written only by a run that reached the last page. A
    # half-fetched Red List is worse than none: the build would model a
    # sample of birds that stops at whatever page the token was throttled
    # on, and the manifest would publish a digest of it. The pages are
    # cached, so re-running costs only the pages still missing.
    if not complete:
        sys.exit(f"  incomplete: {page - 1} page(s) cached, {len(best):,} species so far, "
                 f"and the last page was not reached.\n  Nothing was written. Re-run to "
                 f"continue from the cache.")
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["species", "category", "year_published", "assessment_id", "red_list_version"])
        for name in sorted(best):
            cat, yr, aid = best[name]
            w.writerow([name, cat, yr, aid, version])
    print(f"  {len(best):,} species, {n:,} assessments -> {os.path.relpath(OUT, HERE)} (not in git, not in the archive)")


if __name__ == "__main__":
    main()
