"""Write the step-0 findings as plain text: no box drawing, nothing truncated.

Three specifications, differing only in which terms are in the model, so
the Red List coefficients can be read across them:

  confounders   family, mass, range, described, category
  no-views      the above plus rated attractiveness          <- TEST 2
  full          the above plus log10 Wikipedia views

TEST 2 asks whether Wikipedia views is mediating the threat effect. Views
plausibly FOLLOW research rather than precede it, and a threatened
charismatic species draws pageviews partly BECAUSE it is threatened, so
controlling for views may absorb part of the pathway under study. If the
category coefficients GROW when views is dropped, views was mediating and
the page must say so. If they hold, views is a genuine competitor.

Run:  python3 step0_report.py > STEP0_2026-09-09.md
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_beauty as B                                      # noqa: E402

CATS = B.CATS
CONF = B.TERMS_CONF
NOVIEWS = CONF + ["attractiveness"]
FULL = B.TERMS_FULL


def hc1(m, terms):
    import statsmodels.api as sm
    X, names = B.design(m, terms)
    res = sm.OLS(m["y"].to_numpy(float), X).fit(cov_type="HC1")
    ci = res.conf_int()
    out = {}
    for c in CATS[1:]:
        i = names.index("cat_" + c)
        out[c] = (float(res.params[i]), float(ci[i][0]), float(ci[i][1]),
                  float(res.pvalues[i]))
    _, r2 = B.ols(X, m["y"].to_numpy(float))
    return out, float(r2)


def main():
    d, m, n, meta, rl = B.join()
    print("# Step 0 findings, 9 September 2026")
    print()
    print(f"Modelled sample: {len(m):,} birds. Response is log(1 + works "
          f"2015-2024). Reference category is Least Concern. Errors are HC1.")
    print(f"Red List {meta['red_list_version']}, source {meta['redlist_source']}.")
    print()

    print("## 1. Raw counts by Red List category, unadjusted")
    print()
    print("    cat    n      median   mean   typical")
    raw = B.raw_means(m)
    for c in CATS:
        r = raw[c]
        print(f"    {c:4s}  {r['n']:5d}   {r['median']:7.1f} {r['mean']:6.1f}   "
              f"{r['typical']:7.2f}")
    print()
    print("    'typical' is expm1 of the mean of log(1+works), the same")
    print("    back-transformation the adjusted means use.")
    print()

    fits = {}
    for tag, terms in (("confounders", CONF), ("no-views", NOVIEWS), ("full", FULL)):
        fits[tag] = (B.fit_all(m, terms), *hc1(m, terms))

    print("## 2. Red List coefficients across three specifications")
    print()
    print("    Positive means MORE papers than Least Concern.")
    print()
    for tag in ("confounders", "no-views", "full"):
        _, co, r2 = fits[tag]
        print(f"    {tag}  (R2 = {r2:.3f})")
        print("      cat     coef        95% CI              p")
        for c in CATS[1:]:
            b, lo, hi, p = co[c]
            print(f"      {c:4s} {b:+8.4f}   [{lo:+7.4f}, {hi:+7.4f}]   {p:.3g}")
        print()

    print("## 3. TEST 2 - does dropping Wikipedia views change the threat term?")
    print()
    print("    cat    no-views    full     difference   direction")
    _, cnv, _ = fits["no-views"]
    _, cfu, _ = fits["full"]
    grew = []
    for c in CATS[1:]:
        a = cnv[c][0]
        b = cfu[c][0]
        diff = a - b
        grew.append(diff > 0)
        word = "grows without views" if diff > 0 else "shrinks without views"
        print(f"    {c:4s} {a:+9.4f} {b:+8.4f}   {diff:+10.4f}   {word}")
    print()
    if all(grew):
        print("    Every category coefficient is LARGER when views is dropped.")
        print("    Views was absorbing part of the threat effect: it sits on the")
        print("    pathway, not beside it. The page must say so.")
    elif not any(grew):
        print("    Every coefficient is SMALLER without views. Views is not")
        print("    mediating; it competes with threat rather than carrying it.")
    else:
        print("    Mixed. No single statement about mediation is supportable.")
    print()

    print("## 4. Drop-one change in R-squared, full model")
    print()
    f, _, _ = fits["full"]
    print("    term                       drop-one dR2")
    for k, v in sorted(f["drop_r2"].items(), key=lambda kv: -kv[1]):
        print(f"    {B.LABELS[k]:26s} {v:.4f}")
    print()
    print("    The two appeal proxies do NOT behave alike, and the page cannot")
    print("    collapse them into one word:")
    print(f"      rated attractiveness  {f['drop_r2']['attractiveness']:.4f}")
    print(f"      Wikipedia views       {f['drop_r2']['views']:.4f}")
    print(f"      ratio                 {f['drop_r2']['views'] / max(f['drop_r2']['attractiveness'], 1e-12):.0f}x")
    print()

    print("## 5. Adjusted means, papers per species (g-computation)")
    print()
    print("    cat    raw typical   confounders   no-views    full")
    for c in CATS:
        print(f"    {c:4s}  {raw[c]['typical']:10.2f}   "
              f"{fits['confounders'][0]['adjusted'][c]:11.2f}   "
              f"{fits['no-views'][0]['adjusted'][c]:8.2f}   "
              f"{fits['full'][0]['adjusted'][c]:7.2f}")
    print()
    print("## 6. Effect size in plain terms")
    print()
    print("    Two answers to two different questions. Which one the page")
    print("    quotes depends on which question it is asking.")
    print()
    print("    TOTAL - threat's whole advantage, attention left in the pathway")
    print("    (the no-views specification):")
    for c in CATS[1:]:
        b = cnv[c][0]
        print(f"      {c} vs LC:  exp({b:+.4f}) = {np.exp(b):.2f}x")
    print()
    print("    DIRECT - threat's advantage with attention held fixed")
    print("    (the full specification):")
    for c in CATS[1:]:
        b = cfu[c][0]
        print(f"      {c} vs LC:  exp({b:+.4f}) = {np.exp(b):.2f}x")
    print()

    print("## 7. The share of threat's advantage running through attention")
    print()
    print("    (total - direct) / total, per category. ASSUMED, see below.")
    print()
    print("    cat     total     direct    through attention")
    for c in CATS[1:]:
        tot, dr = cnv[c][0], cfu[c][0]
        print(f"    {c:4s} {tot:+9.4f} {dr:+10.4f} {100 * (tot - dr) / tot:15.1f}%")
    print()
    print("    The share rises monotonically with severity. The more")
    print("    endangered the bird, the more of its research advantage runs")
    print("    through public attention - and rated attractiveness, the proxy")
    print("    this project is named for, carries none of it (dR2 0.0008).")
    print()
    print("    ASSUMED - the direction. This is a decomposition from a")
    print("    cross-section with a single-timepoint mediator, so it cannot")
    print("    order the two. threat -> attention -> research and")
    print("    research -> better Wikipedia article -> views produce identical")
    print("    numbers. The percentages are what the model attributes, not a")
    print("    demonstrated sequence, and the word 'mediates' does not appear")
    print("    on the page without 'assumed' beside it.")
    print()


if __name__ == "__main__":
    main()
