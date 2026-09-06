"""
Research effort per bird species: the number of OpenAlex works, 2015-2024,
whose title or abstract contains the scientific name as a phrase.

OpenAlex data are CC0. Since February 2026 the API is metered. Measured on
6 September 2026 from the response headers: a call that lists with a
filter costs 10 credits, $0.001, whatever per-page or select it carries;
a keyless client gets 1,000 credits a day ($0.10, 100 species) and a free
account key 10,000 ($1.00, 1,000 species), so the full run is eleven days
on a key. The key, if there is one, is read from the environment as
OPENALEX_KEY and never from disk; without it the script runs on the
keyless allowance and stops cleanly at 429, to be re-run the next day.
Every response's meta.cost_usd is written into its row, and the page sums
that column of the shipped table to say what a re-run costs; each run's
total also goes to data/openalex_run_log.txt when the run ends, as a
record, not as the source of the figure.

Writes data/openalex_counts.csv: species, works_2015_2024, cost_usd,
fetched. Resumable: species already in the file are skipped, a call that
returns nothing writes no row so it is retried next run, every row is
flushed as it is written, and a row cut short by a kill is dropped on the
next start. Proven on 6 September 2026 by killing the process twice mid-run
and restarting it: no species repeated, none blank, none lost.

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
from netutil import get_json, check_header, trim_partial_row, Budget, Lock  # noqa: E402

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
    cut = trim_partial_row(OUT)
    if cut:
        print(f"  dropped a row the last run did not finish writing: {cut[:60]!r}")
    check_header(OUT, COLS)
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    todo = [s for s in species if s not in done]
    print(f"  {len(species):,} species, {len(done):,} done, {len(todo):,} to fetch, "
          f"{'keyed ($1.00/day, 1,000 species)' if key else 'keyless ($0.10/day, 100 species)'}")
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
                fh.flush()      # paid for; a kill must not lose it
                n += 1
                cost += c
                lk.beat()
                if n % 200 == 0:
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
