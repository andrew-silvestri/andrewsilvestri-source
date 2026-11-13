"""Build outputs/payload.json for the armchair page from the files in data/.

Two inputs:
- The Placita, opinion by opinion (data/opinions_book1..5.csv: one row per attributed answer to a chapter's
  question, paraphrased from John Dowel's translation, Gutenberg #78851, with Gutenberg line numbers), and two
  independent gradings of every row against present science (data/ratings_A_part*.csv, ratings_B_part*.csv).
  The grades: STRONG, PARTIAL, LOOSE, WRONG, UNSCORABLE (no physical answer to check).
- The case table (data/cases_*.csv): famous anticipations, misses and reverse cases, each with the year of the
  idea, a named confirming or refuting event fixed before the gap was computed, and a grade.

Rules fixed before computing:
- A Placita row is scorable when both raters scored it (neither said UNSCORABLE).
- Consensus grade: where the raters differ, the lower of the two grades (STRONG > PARTIAL > LOOSE > WRONG).
  The upper of the two is reported too, so the page can give a range.
- Agreement: Cohen's kappa on all five codes, and on the binary "right in its core claim" (STRONG or PARTIAL)
  for rows both raters scored.
- Gap: confirm_year - idea_year, less one when the idea is BCE and the event CE (there is no year 0). Every
  case row's gap is recomputed here and must equal the one in the file.

Run:  python analysis.py
"""
import csv
import glob
import json
import os
import statistics
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs", "payload.json")
ORDER = {"STRONG": 3, "PARTIAL": 2, "LOOSE": 1, "WRONG": 0}
CODES = ["STRONG", "PARTIAL", "LOOSE", "WRONG", "UNSCORABLE"]


def rows(pattern):
    out = []
    for p in sorted(glob.glob(os.path.join(DATA, pattern))):
        with open(p, encoding="utf-8", newline="") as f:
            out += list(csv.DictReader(f))
    return out


def kappa(a, b, cats):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / n / n
    return (po - pe) / (1 - pe), po


def placita():
    ops = rows("opinions_book?.csv")
    ids = [o["id"] for o in ops]
    assert len(ids) == len(set(ids)), "duplicate opinion ids"
    ra = {r["id"]: r for r in rows("ratings_A_part?.csv")}
    rb = {r["id"]: r for r in rows("ratings_B_part?.csv")}
    assert set(ra) == set(ids) == set(rb), "every opinion must carry both ratings"
    for r in list(ra.values()) + list(rb.values()):
        assert r["grade"] in CODES, r
    ga = [ra[i]["grade"] for i in ids]
    gb = [rb[i]["grade"] for i in ids]
    k5, po5 = kappa(ga, gb, CODES)

    scor = [o for o in ops if ra[o["id"]]["grade"] != "UNSCORABLE" and rb[o["id"]]["grade"] != "UNSCORABLE"]
    ba = ["R" if ra[o["id"]]["grade"] in ("STRONG", "PARTIAL") else "N" for o in scor]
    bb = ["R" if rb[o["id"]]["grade"] in ("STRONG", "PARTIAL") else "N" for o in scor]
    k2, po2 = kappa(ba, bb, ["R", "N"])

    low, high = Counter(), Counter()
    per_q = defaultdict(list)
    table = []
    for o in ops:
        a, b = ra[o["id"]]["grade"], rb[o["id"]]["grade"]
        if "UNSCORABLE" in (a, b):
            g_lo = g_hi = None
        else:
            g_lo = min(a, b, key=ORDER.get)
            g_hi = max(a, b, key=ORDER.get)
            low[g_lo] += 1
            high[g_hi] += 1
        key = (int(o["book"]), int(o["chapter"]))
        per_q[key].append(g_lo)
        table.append({"id": o["id"], "book": int(o["book"]), "chapter": int(o["chapter"]),
                      "question": o["question"], "holders": o["holders"], "opinion": o["opinion"],
                      "line_start": int(o["line_start"]), "line_end": int(o["line_end"]), "grade_A": a, "grade_B": b,
                      "consensus": g_lo, "upper": g_hi})
    n = len(scor)
    assert sum(low.values()) == n == sum(high.values())

    # Questions (chapters) with at least one scorable answer, and those whose answers include a STRONG one.
    q_scor = {k: [g for g in v if g] for k, v in per_q.items()}
    q_scor = {k: v for k, v in q_scor.items() if v}
    q_hit = {k: v for k, v in q_scor.items() if "STRONG" in v}
    q_none = {k: v for k, v in q_scor.items() if all(g == "WRONG" for g in v)}
    rivals = [len(v) - v.count("STRONG") for v in q_hit.values()]

    by_book = {}
    for bk in range(1, 6):
        sub = [t for t in table if t["book"] == bk and t["consensus"]]
        c = Counter(t["consensus"] for t in sub)
        by_book[str(bk)] = {"n_all": sum(1 for t in table if t["book"] == bk), "n": len(sub),
                            **{g: c[g] for g in ORDER}}

    holders = Counter()
    for t in table:
        if t["consensus"] == "STRONG":
            for h in t["holders"].split("; "):
                holders[h] += 1

    record = {}
    for name in ("Democritus", "Thales", "Anaxagoras", "Empedocles", "Plato", "Aristotle", "the Stoics",
                 "Epicurus", "Pythagoras", "Anaximander"):
        mine = [t["consensus"] for t in table if t["consensus"] and name in t["holders"].split("; ")]
        record[name] = {"n": len(mine), **{g: mine.count(g) for g in ORDER}}

    return {
        "record": record,
        "n_opinions": len(ops), "n_chapters": len(per_q), "n_scorable": n,
        "n_unscorable": len(ops) - n,
        "low": dict(low), "high": dict(high),
        "kappa5": round(k5, 3), "agree5": round(po5, 3), "kappa2": round(k2, 3), "agree2": round(po2, 3),
        "q_scorable": len(q_scor), "q_with_strong": len(q_hit), "q_all_wrong": len(q_none),
        "rivals_median": statistics.median(rivals) if rivals else 0,
        "rivals_mean": round(statistics.mean(rivals), 2) if rivals else 0,
        "by_book": by_book,
        "strong_holders": holders.most_common(),
        "table": table,
    }


def cases():
    cs = rows("cases_*.csv")
    ids = [c["id"] for c in cs]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    out = []
    for c in cs:
        iy, cy = int(c["idea_year"]), int(c["confirm_year"])
        gap = cy - iy - (1 if iy < 0 < cy else 0)
        assert gap == int(c["gap_years"]), (c["id"], gap, c["gap_years"])
        g = c["grade"].split(",")[0].strip().upper()
        assert g in ORDER, (c["id"], c["grade"])
        out.append({"id": c["id"], "side": c["side"].strip().upper(), "thinker": c["thinker"],
                    "work": c["work"], "locator": c["locator"], "idea_year": iy,
                    "idea_year_note": c["idea_year_note"], "claim": c["claim"],
                    "later_result": c["later_result"], "confirm_event": c["confirm_event"],
                    "confirm_year": cy, "gap": gap, "grade": g, "grade_note": c["grade"],
                    "causal_line": c["causal_line"], "same_passage_wrong": c["same_passage_wrong"],
                    "instrument": c["instrument"], "instrument_year": c["instrument_year"],
                    "sources": c["sources"], "verified": c["verified"]})
    out.sort(key=lambda r: (r["idea_year"], r["id"]))
    tally = Counter(r["grade"] for r in out)
    ancient = [r for r in out if r["idea_year"] < 500]
    modern = [r for r in out if r["idea_year"] >= 1400]
    def med(rs, grades):
        v = [r["gap"] for r in rs if r["grade"] in grades]
        return statistics.median(v) if v else None
    return {"n": len(out), "tally": dict(tally),
            "gap_med_ancient_hit": med(ancient, ("STRONG", "PARTIAL")),
            "gap_med_modern_hit": med(modern, ("STRONG", "PARTIAL")),
            "gap_med_ancient_miss": med(ancient, ("WRONG",)),
            "gap_med_modern_miss": med(modern, ("WRONG",)),
            "n_ancient": len(ancient), "n_modern": len(modern),
            "rows": out}


if __name__ == "__main__":
    P = {"placita": placita(), "cases": cases(),
         "source": {"gutenberg": 78851, "fetched": json.load(open(os.path.join(DATA, "fetched.json")))}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, ensure_ascii=False, indent=1)
    p, c = P["placita"], P["cases"]
    print(f"Placita: {p['n_opinions']} opinions in {p['n_chapters']} chapters; scorable {p['n_scorable']}")
    print(f"  consensus (lower) {p['low']}  upper {p['high']}")
    print(f"  kappa5 {p['kappa5']} (agree {p['agree5']}); kappa right/not {p['kappa2']} (agree {p['agree2']})")
    print(f"  chapters scorable {p['q_scorable']}, with a STRONG answer {p['q_with_strong']}, all WRONG {p['q_all_wrong']}; "
          f"rivals beside a STRONG answer median {p['rivals_median']} mean {p['rivals_mean']}")
    print(f"  by book {p['by_book']}")
    print(f"  STRONG holders {p['strong_holders'][:12]}")
    print(f"Cases: {c['n']} {c['tally']}; median gap hits ancient {c['gap_med_ancient_hit']} modern {c['gap_med_modern_hit']}; "
          f"misses ancient {c['gap_med_ancient_miss']} modern {c['gap_med_modern_miss']}")
