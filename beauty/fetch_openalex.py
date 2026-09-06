"""
Research effort per bird species: the number of OpenAlex works, 2015-2024,
whose title or abstract contains the scientific name as a phrase.

OpenAlex data are CC0. Since February 2026 the API is metered: a call that
lists with a filter costs $0.0001, a keyless client gets $0.10 a day (about
1,000 species), a free account key gets $1.00 a day (about 10,000 species).
The key, if there is one, is read from the environment as OPENALEX_KEY and
never from disk; without it the script runs on the keyless allowance and
stops cleanly at 429, to be re-run the next day. Every response's
meta.cost_usd is summed into data/openalex_run_log.txt so the page can say
what a re-run costs from the record rather than from an estimate.

Writes data/openalex_counts.csv: species, works_2015_2024, cost_usd,
fetched. Resumable: species already in the file are skipped.

Run:  python3 fetch_openalex.py
"""

import csv
import datetime as dt
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from netutil import get_json, check_header, Budget, Lock  # noqa: E402

SPECIES = os.path.join(HERE, "data", "avonet_slim.csv")
OUT = os.path.join(HERE, "data", "openalex_counts.csv")
LOG = os.path.join(HERE, "data", "openalex_run_log.txt")
COLS = ["species", "works_2015_2024", "cost_usd", "fetched"]
YEARS = "2015-2024"
MAILTO = "dasilvestri@utexas.edu"


def url_for(name, key):
    flt = f'title_and_abstract.search:"{name}",publication_year:{YEARS}'
    q = {"filter": flt, "per-page": 1, "mailto": MAILTO}
    if key:
        q["api_key"] = key
    return "https://api.openalex.org/works?" + urllib.parse.urlencode(q)


def main():
    key = os.environ.get("OPENALEX_KEY", "").strip()
    species = [r["species"] for r in csv.DictReader(open(SPECIES, encoding="utf-8"))]
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    todo = [s for s in species if s not in done]
    print(f"  {len(species):,} species, {len(done):,} done, {len(todo):,} to fetch, "
          f"{'keyed' if key else 'keyless ($0.10/day)'}")
    check_header(OUT, COLS)
    new = not os.path.exists(OUT)
    n, cost, unanswered = 0, 0.0, 0
    today = dt.date.today().isoformat()
    stopped = ""
    with Lock("openalex", HERE) as lk, open(OUT, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLS)
        try:
            for s in todo:
                j = get_json(url_for(s, key))
                if j is None or "meta" not in j:
                    # No row: a species whose call failed is still to do, so
                    # the next run retries it instead of carrying a blank
                    # count as if it were an answer.
                    unanswered += 1
                    continue
                meta = j["meta"]
                c = float(meta.get("cost_usd", 0) or 0)
                w.writerow([s, meta.get("count", ""), f"{c:.4f}", today])
                n += 1
                cost += c
                lk.beat()
                if n % 200 == 0:
                    fh.flush()
                    print(f"  {n:,} fetched, ${cost:.2f}")
                time.sleep(0.05)
        except Budget as e:
            stopped = f"stopped at 429 ({e}); re-run tomorrow or with OPENALEX_KEY"
            print("  " + stopped)
    with open(LOG, "a", encoding="utf-8") as lg:
        lg.write(f"{today}\t{'keyed' if key else 'keyless'}\tspecies={n}\tcost_usd={cost:.4f}"
                 f"\t{stopped}\n")
    print(f"  {n:,} species fetched, ${cost:.4f} -> {os.path.relpath(OUT, HERE)}"
          + (f"; {unanswered} unanswered, left for the next run" if unanswered else ""))


if __name__ == "__main__":
    main()
