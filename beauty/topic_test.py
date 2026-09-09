"""The stratified topic test, run against PRESPEC_topics_2026-09-09.md.

The rule was committed before any topic data existed. This script does not
choose strata, thresholds or a primary comparison - it reads them from the
constants below, which are transcribed from that file, and reports every
stratum named there INCLUDING the ones that fail the cell-size floor.

The question: STEP0 finds threatened birds get MORE research. Is that made
of papers ABOUT the listing - status reviews, Red List updates, assessment
documents - or of research the listing may have prompted? Papers about the
listing are an instrument artefact. Papers prompted by it are the finding.

Each field is fitted with the same reduced specification selection_check.py
uses: family, mass, range, described, category; HC1 errors; response is
log(1 + works IN THAT FIELD).

Run:  python3 topic_test.py
"""

import collections
import csv
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_beauty as B                                      # noqa: E402

TOPICS = os.path.join(HERE, "data", "topic_counts.csv")
TERMS = B.TERMS_CONF
CATS = B.CATS

# ---- transcribed from PRESPEC_topics_2026-09-09.md, not chosen here ----
PRIMARY = "13"
SECONDARY = ["28", "24", "27", "19", "11"]      # pre-ordered in the file
CONTROL = "23"                                  # the artefact's own home
ARTEFACT_PRONE = {"23", "11"}
NAMES = {"11": "Agricultural and Biological Sciences",
         "13": "Biochemistry, Genetics and Molecular Biology",
         "19": "Earth and Planetary Sciences",
         "23": "Environmental Science",
         "24": "Immunology and Microbiology",
         "27": "Medicine",
         "28": "Neuroscience"}
MIN_CELL = 30            # per Red List category, species with >= 1 work
FAIL_BELOW = 0.20        # CR point estimate floor in the primary stratum
ALPHA = 0.05
# -----------------------------------------------------------------------


def load():
    _, m, _, _, _ = B.join()
    m = m.copy()
    t = pd.read_csv(TOPICS, dtype={"field_id": str})
    wide = (t[t["field_id"] != "_none"]
            .pivot_table(index="species", columns="field_id", values="works",
                         aggfunc="sum", fill_value=0))
    return m, wide


def cells(m, w):
    """Species per Red List category with >= 1 work in this field."""
    return {c: int(((m["category"] == c) & (w > 0)).sum()) for c in CATS}


def fit_field(m, w):
    import statsmodels.api as sm
    d = m.copy()
    d["y"] = np.log1p(w.to_numpy(float))
    X, names = B.design(d, TERMS)
    res = sm.OLS(d["y"].to_numpy(float), X).fit(cov_type="HC1")
    ci = res.conf_int()
    out = {}
    for c in CATS[1:]:
        i = names.index("cat_" + c)
        out[c] = (float(res.params[i]), float(ci[i][0]), float(ci[i][1]),
                  float(res.pvalues[i]))
    return out


def report(tag, fid, m, wide, results):
    w = wide[fid].reindex(m["species"]).fillna(0) if fid in wide.columns \
        else pd.Series(0.0, index=m["species"])
    w.index = m.index
    cl = cells(m, w)
    ok = all(cl[c] >= MIN_CELL for c in CATS)
    total = int(w.sum())
    print(f"\n  [{tag}] field {fid} - {NAMES.get(fid, '?')}")
    print(f"    works in field: {total:,}   species with >=1: {int((w > 0).sum()):,}")
    print("    cells (species with >=1 work): " +
          "  ".join(f"{c} {cl[c]}" for c in CATS))
    if not ok:
        short = [f"{c}={cl[c]}" for c in CATS if cl[c] < MIN_CELL]
        print(f"    BELOW THE FLOOR (min {MIN_CELL} per category): {', '.join(short)}")
        print(f"    NOT INTERPRETED, per the pre-spec.")
        results[fid] = {"reportable": False, "cells": cl}
        return
    f = fit_field(m, w)
    print("      cat     coef        95% CI              p")
    for c in CATS[1:]:
        b, lo, hi, p = f[c]
        print(f"      {c:4s} {b:+8.4f}   [{lo:+7.4f}, {hi:+7.4f}]   {p:.3g}")
    cr = f["CR"]
    passes = cr[0] >= FAIL_BELOW and cr[3] < ALPHA
    print(f"    CR: coef {cr[0]:+.4f} (floor {FAIL_BELOW:+.2f}), p {cr[3]:.3g} "
          f"-> {'meets' if passes else 'DOES NOT MEET'} the pre-spec threshold")
    results[fid] = {"reportable": True, "cells": cl, "fit": f, "cr_passes": passes}


def main():
    m, wide = load()
    print(f"  {len(m):,} modelled species; topic table covers "
          f"{wide.shape[0]:,} species across {wide.shape[1]} fields")
    print(f"  Rule from PRESPEC: min cell {MIN_CELL}/category, primary field "
          f"{PRIMARY}, CR floor {FAIL_BELOW:+.2f} at p<{ALPHA}")

    results = {}
    report("PRIMARY", PRIMARY, m, wide, results)
    for fid in SECONDARY:
        report("secondary", fid, m, wide, results)
    report("POSITIVE CONTROL", CONTROL, m, wide, results)

    print("\n" + "=" * 68)
    print("  THE CRUDE CONTRAST, predicted in advance to be worse")
    print("=" * 68)
    print("  Total works minus fields 23 and 11. The pre-spec says this")
    print("  understates the effect because it deletes genuine conservation")
    print("  biology, which IS research effort on the species.")
    keep = [c for c in wide.columns if c not in ARTEFACT_PRONE]
    w = wide[keep].sum(axis=1).reindex(m["species"]).fillna(0)
    w.index = m.index
    f = fit_field(m, w)
    print("      cat     coef        95% CI              p")
    for c in CATS[1:]:
        b, lo, hi, p = f[c]
        print(f"      {c:4s} {b:+8.4f}   [{lo:+7.4f}, {hi:+7.4f}]   {p:.3g}")

    print("\n" + "=" * 68)
    print("  VERDICT against the pre-spec")
    print("=" * 68)
    prim = results.get(PRIMARY, {})
    artefact_free = [f_ for f_ in [PRIMARY] + SECONDARY
                     if f_ not in ARTEFACT_PRONE and results.get(f_, {}).get("reportable")]
    print(f"  artefact-free strata meeting the cell floor: "
          f"{artefact_free or 'NONE'}")
    if not prim.get("reportable"):
        print("  PRIMARY stratum is below the cell floor.")
    if len(artefact_free) < 2:
        print("  INDETERMINATE: fewer than two artefact-free strata meet the")
        print("  floor. Reported as indeterminate; the threshold is NOT")
        print("  lowered. The page rests on the total effect with the")
        print("  artefact named as an unresolved limitation.")
        return
    others = [f_ for f_ in artefact_free if f_ != PRIMARY
              and results[f_].get("cr_passes")]
    if prim.get("cr_passes") and others:
        print(f"  SURVIVES: CR is positive at p<{ALPHA} with coef >= "
              f"{FAIL_BELOW:+.2f} in the primary stratum and in {others}.")
    elif not prim.get("cr_passes"):
        print(f"  FAILS: the primary stratum does not meet the threshold.")
        print(f"  A threat effect present only where status reviews can be")
        print(f"  published is an artefact.")
    else:
        print(f"  FAILS: primary meets the threshold but no secondary")
        print(f"  artefact-free stratum does.")


if __name__ == "__main__":
    main()
