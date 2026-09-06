"""
English Wikipedia pageviews per bird species, the public-attention proxy
Roll et al. (2016) and Mittermeier et al. (2019, 2021) used.

Two free endpoints, no key, data CC0 1.0 (Wikimedia Analytics API access
policy):

  1. The MediaWiki query API resolves each scientific name to the article it
     redirects to (most species pages sit under the common name), fifty
     names per call. A name that resolves to a one-word title (a genus page)
     or to nothing is recorded with no article.
  2. The pageviews API returns the monthly user-agent-filtered view count
     for that article, January 2016 to December 2025.

Writes data/wikipedia_views.csv: species, article, months, views_total,
views_mean_monthly, fetched (the date this script wrote the row; the
build refuses a table without it). Resumable: species already in the file
are skipped. Requests are sequential, as the policy asks.

Run:  python3 fetch_wikipedia.py
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
OUT = os.path.join(HERE, "data", "wikipedia_views.csv")
START, END = "20160101", "20251231"
QUERY = "https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&titles="
VIEWS = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
         "en.wikipedia/all-access/user/{title}/monthly/" + START + "/" + END)
COLS = ["species", "article", "months", "views_total", "views_mean_monthly", "fetched"]


def resolve(names):
    """scientific name -> article title, or '' when there is none."""
    out = {}
    for i in range(0, len(names), 50):
        chunk = names[i:i + 50]
        j = get_json(QUERY + urllib.parse.quote("|".join(chunk)))
        q = j.get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
        missing = {p["title"] for p in q.get("pages", {}).values() if "missing" in p}
        for n in chunk:
            t = norm.get(n, n)
            t = redir.get(t, t)
            if t in missing or len(t.split()) < 2 and t != n:
                out[n] = ""
            else:
                out[n] = t
        time.sleep(0.2)
    return out


def main():
    species = [r["species"] for r in csv.DictReader(open(SPECIES, encoding="utf-8"))]
    trim_partial_row(OUT)
    check_header(OUT, COLS)
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    todo = [s for s in species if s not in done]
    print(f"  {len(species):,} species, {len(done):,} done, {len(todo):,} to fetch")
    if not todo:
        return
    titles = resolve(todo)
    new = not os.path.exists(OUT)
    n = 0
    today = dt.date.today().isoformat()
    with Lock("wikipedia", HERE) as lk, open(OUT, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLS)
        try:
            for s in todo:
                art = titles.get(s, "")
                if not art:
                    w.writerow([s, "", 0, "", "", today])
                    continue
                j = get_json(VIEWS.format(title=urllib.parse.quote(art.replace(" ", "_"), safe="")),
                             retries=6, wait_429=30)
                items = (j or {}).get("items", [])
                time.sleep(0.25)
                tot = sum(it["views"] for it in items)
                w.writerow([s, art, len(items), tot,
                            f"{tot / len(items):.2f}" if items else "", today])
                n += 1
                lk.beat()
                if n % 500 == 0:
                    fh.flush()
                    print(f"  {n:,} fetched")
        except Budget as e:
            print(f"  stopped: {e}; re-run to continue")
    print(f"  {n:,} articles fetched -> {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
