"""
The same OpenAlex query fetch_openalex.py counts, split by record type.

D-32 (QA, 2026-10-22): most of what the page counted as "papers" are not
research. For a Critically Endangered bird the works whose title or abstract
names it are mostly GBIF occurrence downloads (OpenAlex type `dataset`) and
IUCN Red List assessments and Birds of the World accounts (type
`reference-entry`). Geospiza heliobates, 9 works: dataset 6,
reference-entry 3, no research at all. This script asks OpenAlex for the
same filter as fetch_openalex.py with group_by=type, so the total of each
row is the count the page used to carry and the split says what it was.

One call per species, 10 credits ($0.001), measured 2026-10-24 from
X-RateLimit-Credits-Used: group_by does not change the price of the search.
Two tiers, each in a fixed shuffled order (seed 32) so a run that stops at
the day's budget leaves a random sample, not the first letters of the
alphabet: first the 9,113 birds the model fits (data/birds_open.csv, which
ships), then every other AVONET species with a row in the reader's own Red
List table (data/iucn_aves.csv, 1,556 on 2026-10-24), which the page's
selection check and its Data Deficient comparison read. A reader without the
Red List table fetches tier 1 only.

Writes data/openalex_types.csv: species, works_total, by_type, cost_usd,
fetched. by_type is "type:count;type:count" in OpenAlex's own type names.
Every row carries the date it was fetched (trap 18: build_beauty refuses a
table with a row that does not). Resumable on the same terms as
fetch_openalex.py: done species are skipped, an unanswered call writes no
row, every row is flushed, a row cut short by a kill is dropped next start.

The key is read by name (OPENALEX_KEY) through envfile.py, never printed.
Run:  python fetch_types.py
"""

import csv
import datetime as dt
import os
import random
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from netutil import get_json, check_header, trim_partial_row, Budget, Lock, polite  # noqa: E402
import envfile  # noqa: E402

SPECIES = os.path.join(HERE, "data", "birds_open.csv")
AVONET = os.path.join(HERE, "data", "avonet_slim.csv")
REDLIST = os.path.join(HERE, "data", "iucn_aves.csv")
OUT = os.path.join(HERE, "data", "openalex_types.csv")
LOG = os.path.join(HERE, "data", "types_run_log.txt")
COLS = ["species", "works_total", "by_type", "cost_usd", "fetched"]
YEARS = "2015-2024"
SEED = 32
WORKERS = 4


def url_for(name, key):
    # The filter is fetch_openalex.url_for's, character for character; the
    # build checks each row's works_total against that script's count.
    flt = f'title_and_abstract.search:"{name}",publication_year:{YEARS}'
    q = polite({"filter": flt, "group_by": "type"})
    if key:
        q["api_key"] = key
    return "https://api.openalex.org/works?" + urllib.parse.urlencode(q)


def order():
    names = lambda p: [r["species"] for r in csv.DictReader(open(p, encoding="utf-8"))]  # noqa: E731
    sp = names(SPECIES)
    random.Random(SEED).shuffle(sp)
    if os.path.exists(REDLIST):
        have, listed = set(sp), set(names(REDLIST))
        rest = [s for s in names(AVONET) if s in listed and s not in have]
        random.Random(SEED).shuffle(rest)
        sp += rest
    return sp


def main():
    key = envfile.get("OPENALEX_KEY")
    species = order()
    cut = trim_partial_row(OUT)
    if cut:
        print(f"  dropped a row the last run did not finish writing: {cut[:60]!r}")
    check_header(OUT, COLS)
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    todo = [s for s in species if s not in done]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(todo)
    todo = todo[:limit]
    print(f"  {len(species):,} species (both tiers), {len(done):,} done, {len(todo):,} to fetch this run, "
          f"{'keyed' if key else 'keyless'}")
    new = not os.path.exists(OUT)
    n, cost, unanswered = 0, 0.0, 0
    today = dt.date.today().isoformat()
    stopped = ""
    try:
        with Lock("types", HERE) as lk, open(OUT, "a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            if new:
                w.writerow(COLS)
            # Four requests in flight, one writer. Sequentially the first run
            # managed 45 species a minute against 0.2 s calls (2026-10-24):
            # an occasional request hung for the whole 60 s timeout, four
            # times over. A 20 s timeout and four workers keep a hang from
            # stalling the rest; rows are still written, and flushed, one at
            # a time from this thread, in the order the calls return.
            from concurrent.futures import ThreadPoolExecutor
            pool = ThreadPoolExecutor(WORKERS)
            # Submitted up front (a list, not a generator: a generator would
            # submit each call only as the loop reached it, which is serial).
            jobs = [(s, pool.submit(get_json, url_for(s, key), None, 4, 20)) for s in todo]
            try:
                for s, fut in jobs:
                    j = fut.result()
                    if j is None or "meta" not in j or "group_by" not in j:
                        unanswered += 1
                        continue
                    meta = j["meta"]
                    groups = sorted((g["key_display_name"] or g["key"], int(g["count"]))
                                    for g in j["group_by"])
                    if sum(c for _, c in groups) != int(meta["count"]):
                        # group_by over a field every work has must add up to
                        # the total; a short sum means a type went missing.
                        unanswered += 1
                        print(f"  {s}: groups sum {sum(c for _, c in groups)} != count {meta['count']}; not written")
                        continue
                    c = float(meta.get("cost_usd", 0) or 0)
                    w.writerow([s, meta["count"], ";".join(f"{t}:{k}" for t, k in groups),
                                f"{c:.4f}", today])
                    fh.flush()
                    n += 1
                    cost += c
                    lk.beat()
                    if n % 250 == 0:
                        print(f"  {n:,} fetched, ${cost:.2f}", flush=True)
                    time.sleep(0.05)
            except Budget as e:
                stopped = f"stopped at 429 ({e}); re-run after the daily reset"
                print("  " + stopped)
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
    except BaseException as e:                                   # noqa: BLE001
        stopped = f"stopped on {type(e).__name__}: {e}"
        print("  " + stopped)
        raise
    finally:
        with open(LOG, "a", encoding="utf-8", newline="\n") as lg:
            lg.write(f"{today}\t{'keyed' if key else 'keyless'}\tspecies={n}\tcost_usd={cost:.4f}"
                     f"\t{stopped}\n")
    print(f"  {n:,} species fetched, ${cost:.4f} -> {os.path.relpath(OUT, HERE)}"
          + (f"; {unanswered} unanswered, left for the next run" if unanswered else ""))


if __name__ == "__main__":
    main()
