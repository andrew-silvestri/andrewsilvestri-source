"""Works per species BY OpenAlex primary-topic field, 2015-2024.

One call per species, `group_by=primary_topic.field.id` over the same
pinned filter fetch_openalex.py uses, so the denominator is the same corpus
as data/openalex_counts.csv.

**A group_by costs $0.0001 per species** - a TENTH of the plain list call
in fetch_openalex.py, which is $0.001 because `.search` is full-text and
bills as a search. Same filter, same `.search`, different operation,
different price. **The rate belongs to the operation, not to the filter.**

How that was established, because two weaker attempts came first and the
difference matters:

  meta.cost_usd            returned 0.0001 on every call. This is the
                           API's own accounting of its own charge, and it
                           is what the row carries - but it is not an
                           independent check of what was billed.
  a two-call balance probe  UNSOUND, and recorded here so nobody repeats
                           it. One group_by call then one list call, a
                           minute apart, reading prepaid after each. The
                           balance LAGS - measured at $0.0350 for under an
                           hour on 8 September - so a one-minute window
                           cannot attribute a charge to either call. The
                           group_by call moved the balance by ZERO, which
                           is consistent with free or with lag and is NOT
                           evidence of one credit.
  the run itself           the identifying measurement. Prepaid $3.1668 ->
                           $3.0545 and daily $0.0002 -> $0 across ~1,293
                           calls: $0.1125 drawn. Ten credits would have
                           left ~$1.87 and free would have left $3.1668.
                           The hypotheses are a factor of ten apart, so
                           the lag cannot move the answer between them.
                           The residual IS the lag: $0.1125 / $0.0001 =
                           1,125 calls posted against 1,293 written.

An earlier version of this docstring said $0.001, by carrying the list
call's price to an operation nobody had priced; a later one said "1 credit"
on the strength of a reading that showed zero movement. Both were the
published rate table arriving as an inference. The number above is the one
the balance paid.

This exists to test one rival explanation for STEP0_2026-09-09.md's
finding. The rule it is tested against is committed, before any of this
data existed, in PRESPEC_topics_2026-09-09.md. Read that first; choosing
strata after seeing coefficients is the failure this table is designed not
to permit.

NOTHING HERE IS INHERITED. A new fetcher gets none of fetch_openalex.py's
protections unless they are written in again, which is why each is named:

  netutil.Lock        a heartbeat while appending, so check_settled() can
                      see a live fetch and refuse to build mid-write
  fetched stamp       the ISO date per row, so placeholder data cannot
                      reach a payload (HANDOFF trap 18)
  trim_partial_row    a row cut short by a kill is dropped on the next
                      start rather than read as a finished species
  check_header        refuses to append to a table with other columns
  pinned filter       title_and_abstract.search, never a bare search=
  try/finally         EVERY exit path writes the run log, with the
                      exception class in the line. Until 8 September
                      fetch_openalex.py caught only Budget, and the run
                      that fetched 9,832 species would have taken its whole
                      cost out of the file the page quotes.

break_topics.py proves the last of those over five exit paths, and was
itself proven to fail under mutation before being believed.

Writes data/topic_counts.csv: species, field_id, works, cost_usd, fetched.
One row per species per field with a non-zero count, plus a field_id="_none"
row for a species whose call returned no groups, so "asked and got nothing"
is distinguishable from "never asked".

Run:  python3 fetch_topics.py            # non-LC first, then matched LC
      python3 fetch_topics.py --which lc
"""

import argparse
import csv
import datetime as dt
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from netutil import get_json, check_header, trim_partial_row, Budget, Lock  # noqa: E402

DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "topic_counts.csv")
LOG = os.path.join(DATA, "topic_run_log.txt")
JOINED = os.path.join(DATA, "birds_joined.csv")
LC_MATCHED = os.path.join(DATA, "lc_matched.csv")
COLS = ["species", "field_id", "works", "cost_usd", "fetched"]
YEARS = "2015-2024"
MAILTO = "dasilvestri@utexas.edu"
NONE = "_none"


def url_for(name, key):
    flt = f'title_and_abstract.search:"{name}",publication_year:{YEARS}'
    q = {"filter": flt, "group_by": "primary_topic.field.id", "mailto": MAILTO}
    if key:
        q["api_key"] = key
    return "https://api.openalex.org/works?" + urllib.parse.urlencode(q)


def targets(which):
    """The species to fetch, in a fixed order, from tables already on disk.

    'population' is what PRESPEC amendment 1 selects: every modelled
    species, because 543 of 1,245 non-LC strata hold no LC bird and the
    matched design could not answer the primary comparison over them.

    Non-LC species come FIRST in every mode. The fetch walks its list in
    order, so a run cut short by a 429 or a kill keeps whatever it reached
    -- and the scarce categories are the ones a truncated run must not
    lose. Alphabetical order within each block correlates with genus and
    therefore with family, the strongest term in the model, so a truncated
    LC block is a biased LC sample; putting the 1,837 non-LC first means
    the categories that bind the cell-size rule are complete before any
    truncation can bite.
    """
    import build_beauty as B
    _, m, _, _, _ = B.join()
    non_lc = sorted(m.loc[m["category"] != "LC", "species"].astype(str))
    all_lc = sorted(m.loc[m["category"] == "LC", "species"].astype(str))
    lc = []
    if os.path.exists(LC_MATCHED):
        lc = [r["species"] for r in csv.DictReader(open(LC_MATCHED, encoding="utf-8"))]
    if which == "nonlc":
        return non_lc
    if which == "lc":
        if not lc:
            sys.exit("  data/lc_matched.csv is missing; run match_lc.py first. "
                     "Nothing was written.")
        return lc
    if which == "population":
        return non_lc + all_lc
    return non_lc + lc


def main(which, limit):
    key = os.environ.get("OPENALEX_KEY", "").strip()
    want = targets(which)
    cut = trim_partial_row(OUT)
    if cut:
        print(f"  dropped a row the last run did not finish writing: {cut[:60]!r}")
    check_header(OUT, COLS)
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    outstanding = [s for s in want if s not in done]
    todo = outstanding[:limit] if limit else outstanding
    print(f"  {len(want):,} species in scope, {len(want) - len(outstanding):,} done, "
          f"{len(todo):,} to fetch"
          + (f" (of {len(outstanding):,} outstanding, --limit {limit})" if limit else "")
          + ", "
          f"{'keyed ($1.00/day, 1,000 species)' if key else 'keyless ($0.10/day, 100 species)'}")
    new = not os.path.exists(OUT)
    n, cost, unanswered, rows = 0, 0.0, 0, 0
    today = dt.date.today().isoformat()
    stopped = ""
    try:
        with Lock("topics", HERE) as lk, open(OUT, "a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(COLS)
            try:
                for s in todo:
                    j = get_json(url_for(s, key))
                    if j is None or "meta" not in j:
                        # No row at all: the species is still to do, so the
                        # next run retries it rather than recording a blank
                        # as though it were an answer.
                        unanswered += 1
                        continue
                    c = float(j["meta"].get("cost_usd", 0) or 0)
                    groups = [g for g in (j.get("group_by") or [])
                              if int(g.get("count", 0) or 0) > 0]
                    if groups:
                        for g in groups:
                            # the bare numeric id: group_by returns a full
                            # URL and PRESPEC names fields as 11, 13, 23.
                            fid = str(g["key"]).rstrip("/").rsplit("/", 1)[-1]
                            w.writerow([s, fid, g["count"], f"{c:.4f}", today])
                            rows += 1
                            c = 0.0      # the call is charged once, on its first row
                    else:
                        w.writerow([s, NONE, 0, f"{c:.4f}", today])
                        rows += 1
                    fh.flush()           # paid for; a kill must not lose it
                    n += 1
                    cost += float(j["meta"].get("cost_usd", 0) or 0)
                    lk.beat()
                    if n % 200 == 0:
                        print(f"  {n:,} species, {rows:,} rows, ${cost:.2f}")
                    time.sleep(0.05)
            except Budget as e:
                stopped = f"stopped at 429 ({e}); re-run tomorrow or with OPENALEX_KEY"
                print("  " + stopped)
    except BaseException as e:                                   # noqa: BLE001
        stopped = f"stopped on {type(e).__name__}: {e}"
        print("  " + stopped)
        raise
    finally:
        with open(LOG, "a", encoding="utf-8") as lg:
            lg.write(f"{today}\t{'keyed' if key else 'keyless'}\twhich={which}"
                     f"\tspecies={n}\trows={rows}\tcost_usd={cost:.4f}\t{stopped}\n")
    print(f"  {n:,} species, {rows:,} rows, ${cost:.4f} -> {os.path.relpath(OUT, HERE)}"
          + (f"; {unanswered} unanswered, left for the next run" if unanswered else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["nonlc", "lc", "all", "population"], default="nonlc")
    ap.add_argument("--limit", type=int, default=0)
    main(ap.parse_args().which, ap.parse_args().limit)
