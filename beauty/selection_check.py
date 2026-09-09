"""Measure the selection effect on the CONDITIONAL Red List coefficients.

The fitted model needs a rated attractiveness score, which 1,472 species in
an otherwise-complete frame do not have. Those species are marginally
less-studied, smaller-ranged and later-described, and Critically Endangered
species are missing at nearly twice the base rate. It is tempting to argue
from those marginal differences to the direction of the bias on the Red
List term.

That argument does not follow. The page's claim is a CONDITIONAL
coefficient - category after family, mass, range and description year are
held fixed - and the dropped species differ on range and description year,
which are among the covariates being adjusted for. An unknown share of the
marginal works gap is therefore already absorbed by the specification. A
median difference cannot fix the sign of a multivariate term.

So measure it instead. Fit the SAME reduced specification twice, with
attractiveness out of the model entirely, so the only difference between
the two fits is which species are in the sample:

  sample A   every species clearing the Red List step, rating not required
  sample B   those of A that also carry a rating - the modelled sample

Same terms, same family fixed effects, same HC1 errors. The difference
between the two sets of category coefficients IS the selection effect.

The reconstruction of sample B is checked against build_beauty.join()'s own
output before anything is read from it: if this file's transformations have
drifted from the build's, B's coefficients will not match and the run
fails, because a selection effect measured with a different transform than
the page uses would be a number about nothing.

Run:  python3 selection_check.py [--json outputs/selection.json]
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_beauty as B                                      # noqa: E402

TERMS = B.TERMS_CONF          # family, mass, range, described, category
CATS = B.CATS


def transform(d, need_rating):
    """The rows the model would use, transformed exactly as join() does.

    need_rating=False is sample A. The mask below is join()'s `keep` with
    the attractiveness clause removed, and nothing else changed.
    """
    keep = (d["works_2015_2024"].notna() & d["year"].notna()
            & d["mass_g"].notna() & d["range_km2"].notna() & (d["range_km2"] > 0)
            & d["category"].isin(CATS))
    if need_rating:
        keep = keep & d["attractiveness"].notna()
    m = d[keep].copy()
    m["works"] = m["works_2015_2024"].astype(int)
    m["y"] = np.log1p(m["works"])
    m["log_mass"] = np.log10(m["mass_g"])
    m["log_range"] = np.log10(m["range_km2"])
    m["years_described"] = B.REF_YEAR - m["year"].astype(int)
    m["category"] = pd.Categorical(m["category"], CATS)
    return m


def fit(m):
    """Coefficients and HC1 95% intervals for the category dummies."""
    import statsmodels.api as sm
    X, names = B.design(m, TERMS)
    res = sm.OLS(m["y"].to_numpy(float), X).fit(cov_type="HC1")
    out = {}
    for c in CATS[1:]:
        i = names.index("cat_" + c)
        lo, hi = res.conf_int()[i]
        out[c] = {"coef": float(res.params[i]), "se": float(res.bse[i]),
                  "p": float(res.pvalues[i]), "lo": float(lo), "hi": float(hi)}
    _, r2 = B.ols(X, m["y"].to_numpy(float))
    return out, float(r2), int(len(m))


def main(js):
    d, m_build, n, _, _ = B.join()
    A = transform(d, need_rating=False)
    Bs = transform(d, need_rating=True)

    # Guard: the reconstruction must BE the build's sample, or the
    # comparison is between this file's idea of the model and the page's.
    if len(Bs) != len(m_build):
        sys.exit(f"  reconstruction mismatch: B has {len(Bs):,} rows, "
                 f"build_beauty.join() gives {len(m_build):,}. Nothing reported.")
    ref = B.fit_all(m_build, TERMS)
    chk, _, _ = fit(Bs)
    drift = [c for c in CATS[1:]
             if abs(chk[c]["coef"] - ref["beta"]["cat_" + c]) > 1e-8]
    if drift:
        sys.exit(f"  reconstruction drifts from build_beauty on {drift}. "
                 f"Nothing reported.")
    print(f"  reconstruction check: sample B reproduces build_beauty's "
          f"coefficients exactly ({len(Bs):,} species)")

    fa, r2a, na = fit(A)
    fb, r2b, nb = fit(Bs)
    print(f"\n  sample A  {na:,} species, rating NOT required, R2 {r2a:.3f}")
    print(f"  sample B  {nb:,} species, rating required,     R2 {r2b:.3f}")
    print(f"  selection drops {na - nb:,} species ({100 * (na - nb) / na:.1f}%)\n")

    print(f"  Red List coefficients, log(1+works), reference = Least Concern")
    print(f"  {'cat':4s} {'A coef':>8s} {'A 95% CI':>18s} "
          f"{'B coef':>8s} {'B 95% CI':>18s} {'B-A':>7s}  overlap?")
    rows = {}
    for c in CATS[1:]:
        a, b = fa[c], fb[c]
        diff = b["coef"] - a["coef"]
        ov = not (b["lo"] > a["hi"] or a["lo"] > b["hi"])
        rows[c] = {"A": a, "B": b, "diff": diff, "intervals_overlap": ov}
        print(f"  {c:4s} {a['coef']:>8.4f} [{a['lo']:>7.3f},{a['hi']:>7.3f}] "
              f"{b['coef']:>8.4f} [{b['lo']:>7.3f},{b['hi']:>7.3f}] "
              f"{diff:>+7.4f}  {'yes' if ov else 'NO'}")

    higher = [c for c in CATS[1:] if rows[c]["diff"] > 0]
    lower = [c for c in CATS[1:] if rows[c]["diff"] < 0]
    allov = all(rows[c]["intervals_overlap"] for c in CATS[1:])
    print()
    print(f"  B higher (less negative) than A: {higher or 'none'}")
    print(f"  B lower  (more negative) than A: {lower or 'none'}")
    print(f"  every interval overlaps: {allov}")
    print()
    if allov:
        print("  VERDICT: no category coefficient moves outside the other")
        print("  sample's interval. Selection does not bite at the level the")
        print("  page's claim is made. Quote these numbers, not the argument.")
    if len(higher) == len(CATS) - 1:
        print("  All four move UP under selection: the modelled sample")
        print("  understates how negative the threat term is, so the finding")
        print("  is conservative by the amounts in the B-A column.")
    elif len(lower) == len(CATS) - 1:
        print("  All four move DOWN under selection: the predicted direction")
        print("  is WRONG. The page may NOT claim the bias runs against it.")
    else:
        print("  Mixed directions: no single statement about the sign of the")
        print("  selection effect is supportable. The page reports the table.")

    if js:
        p = os.path.join(HERE, js)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({"terms": TERMS, "n_A": na, "n_B": nb, "r2_A": r2a, "r2_B": r2b,
                   "categories": rows}, open(p, "w", encoding="utf-8"), indent=1)
        print(f"\n  -> {os.path.relpath(p, HERE)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    main(ap.parse_args().json)
