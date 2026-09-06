"""
Join the bird tables, fit the models, write the payload.

Reads, from data/:
  avonet_slim.csv          mass, range, family (AVONET, CC BY 4.0)
  attractiveness_slim.csv  rated attractiveness (Santangeli et al. 2023, CC BY 4.0)
  description_years.csv            year of description (Catalogue of Life, CC BY)
  wikipedia_views.csv      monthly English Wikipedia views 2016-2025 (CC0)
  openalex_counts.csv      works 2015-2024 naming the species (CC0)
  iucn_aves.csv            Red List category, from the reader's own token
                           (fetch_iucn.py); not in git, not in the archive
  iucn_table1a.csv, group_counts.csv   the five-class inputs for figure 1

If iucn_aves.csv is absent, the category column is taken from the
Santangeli deposit in data/raw/, which carries the Red List as the authors
had it in 2021, and the payload says so in redlist_source. The page that
ships is built from the API column; test_beauty.py checks that.

The response is log(1 + works). Two ordinary-least-squares fits with
family fixed effects and heteroskedasticity-robust errors:
  confounders   log mass, log range, years since description, category
  full          the same plus attractiveness and log views
From each: category means adjusted by g-computation (every species
predicted under each category, averaged, back-transformed), the drop-one
change in R-squared per term, and bootstrap intervals over species.

Writes outputs/beauty_payload.json; manifest.json, which carries a SHA-256
of the Red List table the build used so a reader can check their own fetch
against it; data/birds_joined.csv (with the category column; ignored by git
and the archive) and data/birds_open.csv (the same rows without it; ships).

Run:  python3 build_beauty.py [--boot N]
      python3 build_beauty.py --verify-categories
"""

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs", "beauty_payload.json")
MANIFEST = os.path.join(HERE, "manifest.json")
JOINED = os.path.join(DATA, "birds_joined.csv")
OPEN = os.path.join(DATA, "birds_open.csv")
SHIPPED_INPUTS = ["avonet_slim.csv", "attractiveness_slim.csv", "description_years.csv",
                  "wikipedia_views.csv", "openalex_counts.csv", "iucn_table1a.csv",
                  "group_counts.csv"]
# The per-species tables, which are appended to as their fetch runs and so
# must cover every AVONET species before the build will touch them.
RESUMABLE = {"description_years.csv": "fetch_years.py",
             "wikipedia_views.csv": "fetch_wikipedia.py",
             "openalex_counts.csv": "fetch_openalex.py"}
# Every resumable table carries this column, the ISO date the fetch that
# wrote the row ran. The build refuses a table without it, and one with
# any other kind of value in it. description_years.csv and
# wikipedia_views.csv were fetched on 2026-09-05 without the column and
# stamped with that date, from the files' modification times, when it was
# added on 2026-09-06.
STAMP = "fetched"
FETCH_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# description_years.csv also records which register answered.
REGISTERS = {"gbif", "col", "none"}
SANT_ZIP = os.path.join(DATA, "raw", "santangeli_2023.zip")
SANT_CSV = "Santangeli_et_al_data_and_scripts/monsterALL2_2_2023.csv"

SEED = 20260905
CATS = ["LC", "NT", "VU", "EN", "CR"]
CAT_NAMES = {"LC": "Least Concern", "NT": "Near Threatened", "VU": "Vulnerable",
             "EN": "Endangered", "CR": "Critically Endangered"}
FROM_NAME = {v: k for k, v in CAT_NAMES.items()}
REF_YEAR = 2024
TERMS_CONF = ["family", "mass", "range", "described", "category"]
TERMS_FULL = TERMS_CONF + ["attractiveness", "views"]
LABELS = {"family": "Family", "mass": "Body mass", "range": "Range size",
          "described": "Years since description", "category": "Red List category",
          "attractiveness": "Rated attractiveness", "views": "Wikipedia views"}
VERTEBRATES = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fishes"]


def check_settled():
    """Refuse to build while an input is still being written or is short.

    The manifest is a claim about files as they are at this instant, so a
    table that is still growing would be published as a digest of something
    that stops existing a second later, and the model would be fit on
    whatever fraction had arrived. Two checks, because they catch different
    things: a live lock means a fetch is running now, and a short table
    means one was interrupted, throttled or never finished. The second is
    the one that matters, and it holds even for a fetch started before this
    check existed.

    Fetch order was a line in the README until 5 September 2026, when a
    test run hashed two tables that background fetches were appending to
    mid-check. It reported them as changed, correctly, which is how the
    documented order became an enforced one.
    """
    from netutil import Lock, locks
    problems = []
    live = [(n, a) for n, a, is_live in locks(HERE) if is_live]
    stale = [(n, a) for n, a, is_live in locks(HERE) if not is_live]
    for n, a in live:
        problems.append(f"fetch_{n}.py is running (heartbeat {a:.0f}s ago). Wait for it.")
    for n, a in stale:
        problems.append(f"a {n} lock has not beaten for {a / 60:.0f} min, so that fetch died. "
                        f"Re-run fetch_{n}.py, or delete data/raw/.locks/{n}.lock if it finished.")
    want = {r["species"] for r in csv.DictReader(open(os.path.join(DATA, "avonet_slim.csv"),
                                                      encoding="utf-8"))}
    for name, script in RESUMABLE.items():
        p = os.path.join(DATA, name)
        if not os.path.exists(p):
            problems.append(f"data/{name} is missing; run {script}")
            continue
        reader = csv.DictReader(open(p, encoding="utf-8"))
        rows = list(reader)
        have = {r["species"] for r in rows}
        short = want - have
        if short:
            problems.append(f"data/{name} covers {len(have):,} of {len(want):,} species, "
                            f"{len(short):,} short; {script} has not finished")
        # Every fetch stamps each row with the date it ran. A table without
        # the column was written by something other than its fetch script,
        # and a value that is not a date is a table somebody generated to
        # exercise the code; neither may reach a payload, a figure or an
        # archive. On 5 September 2026 a placeholder openalex_counts.csv sat
        # in this folder while another session's rezip_downloads.py walked
        # it; the archive missed it by timing alone. The column is required,
        # not looked for: until 6 September the check only ran when it found
        # one, so a table with none passed in silence (test_beauty.py's
        # settled_guard() is the proof).
        if STAMP not in (reader.fieldnames or []):
            problems.append(f"data/{name} has no '{STAMP}' column, so nothing says when its "
                            f"rows were fetched, or whether they were. {script} writes one; "
                            f"delete this table and run {script}.")
        else:
            bad = sorted({r[STAMP] or "(blank)" for r in rows
                          if not FETCH_STAMP.match(r[STAMP] or "")})
            if bad:
                problems.append(f"data/{name} has '{STAMP}' value(s) that are not dates: "
                                f"{', '.join(bad[:3])}. That is placeholder data; delete it "
                                f"and run {script}.")
        if "source" in (reader.fieldnames or []):
            odd = sorted({r["source"] for r in rows} - REGISTERS)
            if odd:
                problems.append(f"data/{name} has 'source' value(s) outside "
                                f"{sorted(REGISTERS)}: {', '.join(odd[:3])}; {script} does not "
                                f"write those.")
    if problems:
        sys.exit("  the inputs are not settled, so nothing was built:\n" +
                 "".join(f"    - {p}\n" for p in problems) +
                 "  Every fetch script is resumable: re-run it and it continues.")
    print(f"  inputs settled: {len(want):,} species in every table, no fetch running")


def category_digest(rl):
    """SHA-256 of the Red List table the build used, in a canonical form:
    'species,category' lines, sorted by species, LF endings, UTF-8, no
    header. This is what lets a reader who fetches the categories with
    their own token check they got the table this page was built from,
    which matters here more than elsewhere on the site because that table
    is the one input the archive is not allowed to carry.

    A digest is not the data. It is 64 characters for eleven thousand
    species and cannot be inverted to recover a single category, so it
    travels where the table may not."""
    pairs = sorted(zip(rl["species"].astype(str), rl["category"].astype(str)))
    blob = "".join(f"{s},{c}\n" for s, c in pairs)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest(), len(pairs)


def file_digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest(), os.path.getsize(path)


def write_manifest(rl, rl_meta, n):
    digest, rows = category_digest(rl)
    inputs = []
    for name in SHIPPED_INPUTS:
        p = os.path.join(DATA, name)
        if os.path.exists(p):
            h, size = file_digest(p)
            inputs.append({"file": f"data/{name}", "sha256": h, "bytes": size, "ships": True})
    M = {
        "generated": dt.date.today().isoformat(),
        "red_list_version": rl_meta["red_list_version"],
        "redlist_source": rl_meta["redlist_source"],
        "withheld": {
            "file": "data/iucn_aves.csv",
            "ships": False,
            "why": "The IUCN Red List terms of use (v3.1, June 2024, section 4) prohibit "
                   "redistributing Red List data in any form, so this table is not in the "
                   "archive and not in git. Fetch it with your own free token: "
                   "python3 fetch_iucn.py, with IUCN_TOKEN set.",
            "canonical_form": "sorted 'species,category' lines, LF endings, UTF-8, no header",
            "verify": "python3 build_beauty.py --verify-categories",
            "sha256": digest,
            "rows": rows,
        },
        "inputs": inputs,
        "modelled_species": n["modelled"],
    }
    json.dump(M, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    print(f"  categories sha256 {digest[:16]}... ({rows:,} species) -> manifest.json")
    return M


def verify_categories():
    """Check the Red List table on this machine against the manifest the
    archive shipped: same species, same categories, same Red List version."""
    if not os.path.exists(MANIFEST):
        sys.exit("  no manifest.json")
    M = json.load(open(MANIFEST, encoding="utf-8"))
    rl, meta = redlist()
    digest, rows = category_digest(rl)
    want = M["withheld"]
    print(f"  manifest: {want['rows']:,} species, Red List {M['red_list_version']}, "
          f"sha256 {want['sha256'][:16]}...")
    print(f"  yours:    {rows:,} species, Red List {meta['red_list_version']}, "
          f"sha256 {digest[:16]}...")
    if digest == want["sha256"]:
        print("  identical: your fetch matches the table this page was built from.")
        return 0
    if meta["red_list_version"] != M["red_list_version"]:
        print(f"  different, and so are the Red List versions. The Red List has been "
              f"reassessed since this page was built; that is the expected reason.")
    else:
        print("  DIFFERENT at the same Red List version. Check the name matching before "
              "trusting a rebuild.")
    return 1


def read(name, **kw):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        sys.exit(f"  missing {os.path.relpath(p, HERE)}; run the fetch script that writes it")
    return pd.read_csv(p, **kw)


def redlist():
    p = os.path.join(DATA, "iucn_aves.csv")
    if os.path.exists(p):
        r = pd.read_csv(p, dtype=str)
        ver = r["red_list_version"].dropna().iloc[0] if r["red_list_version"].notna().any() else ""
        r = r[["species", "category"]]
        return r, {"redlist_source": "api", "red_list_version": ver,
                   "citation": f"IUCN {ver[:4] if ver else '2026'}. The IUCN Red List of Threatened "
                               f"Species. Version {ver or '?'}. https://www.iucnredlist.org"}
    if not os.path.exists(SANT_ZIP):
        sys.exit("  no data/iucn_aves.csv (fetch_iucn.py, needs IUCN_TOKEN) and no raw Santangeli zip "
                 "(fetch_traits.py) for the labelled fallback")
    z = zipfile.ZipFile(SANT_ZIP)
    rows = csv.DictReader(io.TextIOWrapper(z.open(SANT_CSV), encoding="utf-8"))
    seen = {}
    for row in rows:
        n, c = row["sciName_HBWBLv5"], row["redlistCategory"]
        if n and n != "NA" and c in FROM_NAME and n not in seen:
            seen[n] = FROM_NAME[c]
    r = pd.DataFrame({"species": list(seen), "category": list(seen.values())})
    print("  NOTE: Red List category taken from the Santangeli 2023 deposit (2021 categories); "
          "set IUCN_TOKEN and run fetch_iucn.py for the current Red List")
    return r, {"redlist_source": "santangeli_2021_fallback", "red_list_version": "2021 (via Santangeli et al. 2023)",
               "citation": "Red List categories as carried in Santangeli et al. 2023, npj Biodiversity 2:20, "
                           "data deposit 10.6084/m9.figshare.22231504 (CC BY 4.0)"}


def join():
    av = read("avonet_slim.csv")
    at = read("attractiveness_slim.csv")
    yr = read("description_years.csv", dtype={"year": "Int64"})[["species", "year", "source"]].rename(
        columns={"source": "year_source"})
    wk = read("wikipedia_views.csv")[["species", "article", "views_mean_monthly"]]
    oa = read("openalex_counts.csv")[["species", "works_2015_2024"]]
    rl, rl_meta = redlist()
    n = {"avonet": len(av)}
    d = av.merge(at, on="species", how="left").merge(yr, on="species", how="left") \
          .merge(wk, on="species", how="left").merge(oa, on="species", how="left") \
          .merge(rl, on="species", how="left")
    n["with_attractiveness"] = int(d["attractiveness"].notna().sum())
    n["with_year"] = int(d["year"].notna().sum())
    n["with_article"] = int(d["article"].notna().sum() - (d["article"] == "").sum())
    n["with_works"] = int(d["works_2015_2024"].notna().sum())
    n["with_category"] = int(d["category"].notna().sum())
    n["category_counts_all"] = d["category"].value_counts(dropna=False).rename(index=str).to_dict()
    d["views"] = pd.to_numeric(d["views_mean_monthly"], errors="coerce").fillna(0.0)
    d["has_article"] = d["article"].fillna("").ne("").astype(int)
    # AVONET is on the BirdLife taxonomy, which splits species English
    # Wikipedia still covers in one article: the four Otidiphaps all resolve
    # to "Pheasant pigeon". Each of them is then credited with the whole
    # article's views, so the attention term is over-counted for exactly the
    # kind of species a recent split produces. The count is carried here and
    # the fit is repeated without them rather than the number being quietly
    # divided, which would assume attention splits evenly between forms.
    art = d["article"].fillna("")
    shares = art[art != ""].value_counts()
    d["article_shared_by"] = art.map(shares).fillna(0).astype(int)
    n["views_shared_article"] = int((d["article_shared_by"] > 1).sum())
    n["shared_articles"] = int((shares > 1).sum())
    keep = d["works_2015_2024"].notna() & d["attractiveness"].notna() & d["year"].notna() \
        & d["mass_g"].notna() & d["range_km2"].notna() & (d["range_km2"] > 0) \
        & d["category"].isin(CATS)
    m = d[keep].copy()
    n["modelled"] = int(len(m))
    n["dropped_not_assessed_or_dd_ex"] = int((~d["category"].isin(CATS) & d["works_2015_2024"].notna()
                                              & d["attractiveness"].notna() & d["year"].notna()).sum())
    m["works"] = m["works_2015_2024"].astype(int)
    m["y"] = np.log1p(m["works"])
    m["log_mass"] = np.log10(m["mass_g"])
    m["log_range"] = np.log10(m["range_km2"])
    m["years_described"] = REF_YEAR - m["year"].astype(int)
    m["log_views"] = np.log10(1 + m["views"])
    m["category"] = pd.Categorical(m["category"], CATS)
    n["modelled_shared_article"] = int((m["article_shared_by"] > 1).sum())
    return d, m, n, rl_meta, rl


def design(m, terms):
    cols, names = [np.ones(len(m))], ["intercept"]
    num = {"mass": "log_mass", "range": "log_range", "described": "years_described",
           "attractiveness": "attractiveness", "views": "log_views"}
    for t in terms:
        if t in num:
            cols.append(m[num[t]].to_numpy(float))
            names.append(num[t])
        elif t == "category":
            for c in CATS[1:]:
                cols.append((m["category"] == c).to_numpy(float))
                names.append("cat_" + c)
        elif t == "family":
            fam = pd.get_dummies(m["family"], drop_first=True, dtype=float)
            cols.extend(fam[c].to_numpy() for c in fam.columns)
            names.extend("fam_" + c for c in fam.columns)
    return np.column_stack(cols), names


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return beta, r2


def category_means(m, X, names, beta):
    """Every species predicted under each category, averaged, back-transformed."""
    idx = {n: i for i, n in enumerate(names)}
    base = X.copy()
    for c in CATS[1:]:
        base[:, idx["cat_" + c]] = 0
    out = {}
    for c in CATS:
        Xc = base.copy()
        if c != "LC":
            Xc[:, idx["cat_" + c]] = 1
        out[c] = float(np.expm1((Xc @ beta).mean()))
    return out


def fit_all(m, terms):
    X, names = design(m, terms)
    y = m["y"].to_numpy(float)
    beta, r2 = ols(X, y)
    drop = {}
    for t in terms:
        Xt, _ = design(m, [u for u in terms if u != t])
        _, r2t = ols(Xt, y)
        drop[t] = r2 - r2t
    return {"beta": dict(zip(names, beta.tolist())), "r2": float(r2), "drop_r2": drop,
            "adjusted": category_means(m, X, names, beta), "n": int(len(m))}


def raw_means(m):
    out = {}
    for c in CATS:
        s = m[m["category"] == c]
        out[c] = {"n": int(len(s)), "typical": float(np.expm1(s["y"].mean())) if len(s) else None,
                  "median": float(s["works"].median()) if len(s) else None,
                  "mean": float(s["works"].mean()) if len(s) else None,
                  "share_zero": float((s["works"] == 0).mean()) if len(s) else None}
    return out


def bootstrap(m, n_boot, rng):
    keys = {"raw": {c: [] for c in CATS}, "conf_adj": {c: [] for c in CATS},
            "full_adj": {c: [] for c in CATS}, "conf_drop": {t: [] for t in TERMS_CONF},
            "full_drop": {t: [] for t in TERMS_FULL},
            "conf_cat": {c: [] for c in CATS[1:]}, "full_cat": {c: [] for c in CATS[1:]}}
    for b in range(n_boot):
        s = m.iloc[rng.integers(0, len(m), len(m))]
        for c in CATS:
            sub = s[s["category"] == c]
            keys["raw"][c].append(float(np.expm1(sub["y"].mean())) if len(sub) else np.nan)
        for tag, terms in (("conf", TERMS_CONF), ("full", TERMS_FULL)):
            f = fit_all(s, terms)
            for c in CATS:
                keys[tag + "_adj"][c].append(f["adjusted"][c])
            for t in terms:
                keys[tag + "_drop"][t].append(f["drop_r2"][t])
            for c in CATS[1:]:
                keys[tag + "_cat"][c].append(f["beta"]["cat_" + c])
        if (b + 1) % 50 == 0:
            print(f"  bootstrap {b + 1}/{n_boot}")

    def ci(v):
        v = np.array(v, float)
        v = v[~np.isnan(v)]
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [None, None]
    return {k: {kk: ci(vv) for kk, vv in d.items()} for k, d in keys.items()}


def robust_se(m, terms):
    import statsmodels.api as sm
    X, names = design(m, terms)
    res = sm.OLS(m["y"].to_numpy(float), X).fit(cov_type="HC1")
    return {n: {"coef": float(res.params[i]), "se": float(res.bse[i]), "p": float(res.pvalues[i])}
            for i, n in enumerate(names) if not n.startswith("fam_")}


def groups():
    t = read("iucn_table1a.csv")
    g = read("group_counts.csv")
    t = t[t["group"].isin(VERTEBRATES)].merge(g[["group", "works", "fetched", "years"]], on="group")
    tot_thr, tot_w = t["threatened"].sum(), t["works"].sum()
    rows = []
    for _, r in t.iterrows():
        rows.append({"group": r["group"], "described": int(r["described"]), "evaluated": int(r["evaluated"]),
                     "pct_evaluated": float(r["pct_evaluated"]), "threatened": int(r["threatened"]),
                     "pct_threatened_best": (int(r["pct_threatened_best"]) if str(r["pct_threatened_best"]) not in ("", "nan") else None),
                     "works": int(r["works"]), "share_threatened": float(r["threatened"] / tot_thr),
                     "share_works": float(r["works"] / tot_w),
                     "works_per_threatened": float(r["works"] / r["threatened"])})
    return {"rows": rows, "total_threatened": int(tot_thr), "total_works": int(tot_w),
            "source_table": t["source"].iloc[0], "works_fetched": str(g["fetched"].iloc[0]),
            "works_years": str(g["years"].iloc[0])}


def looked_up():
    return {
        "esa_top10_share": {"value": "over half", "source": "Metrick & Weitzman 1996, Land Economics 72:1-16",
                            "what": "share of identifiable ESA spending FY1989-91 that went to ten species"},
        "life_birds_mammals_budget": {"value": 75, "unit": "% of LIFE species-project budget",
                                      "source": "Mammides 2019, Biodiversity and Conservation 28:1291-1296"},
        "global_threatened_ever_funded": {"value": 6, "unit": "% of threatened species",
                                          "source": "Guenard et al. 2025, PNAS 122:e2412479122"},
        "global_funds_to_least_concern": {"value": 29, "unit": "% of funds",
                                          "source": "Guenard et al. 2025, PNAS 122:e2412479122"},
        "dd_mammals_predicted_threatened": {"value": 64, "unit": "%",
                                            "source": "Bland et al. 2015, Conservation Biology 29:250-259"},
        "dd_amphibians_predicted_threatened": {"value": 85, "unit": "%",
                                               "source": "Borgelt et al. 2022, Communications Biology 5:679"},
        "extinct_since_1500_estimate": {"value": "7.5-13", "unit": "% of ~2 million known species",
                                        "source": "Cowie, Bouchet & Fontaine 2022, Biological Reviews 97:640-663"},
        "extinct_since_1500_red_list": {"value": 0.04, "unit": "%",
                                        "source": "Cowie, Bouchet & Fontaine 2022, Biological Reviews 97:640-663"},
        "published_models": {"value": None, "source": "see models.json once read from full text",
                             "what": "the ten species-level models and the sign of their threat term"},
        # Measured against the live API on the date shown, not quoted from
        # anyone: the same species asked for two ways that were the same
        # question until February 2026 and are not any more.
        "openalex_search_drift": {
            "species": "Panthera leo", "common": "the lion",
            "fulltext": 11759, "title_abstract": 3459, "observed": "2026-09-05",
            "source": "OpenAlex API, https://api.openalex.org/works, queried 5 September 2026",
            "what": "works returned for one species through the bare search= parameter, which "
                    "has meant full text since February 2026, against "
                    "filter=title_and_abstract.search:, which still means what search= used to"},
    }


def assumed():
    return [
        {"key": "paper_definition", "text": "A paper about a species is an OpenAlex work of 2015-2024 whose "
                                            "title or abstract contains the scientific name as a phrase."},
        {"key": "attention_proxy", "text": "Public attention is the mean monthly view count of the species' "
                                           "English Wikipedia article, 2016-2025; a species with no article "
                                           "is given zero, and a species sharing an article with another "
                                           "species is credited with the whole of it."},
        {"key": "phylogeny", "text": "Family fixed effects stand in for phylogeny; the published models use "
                                     "trees."},
        {"key": "response", "text": "The response is log(1 + papers); category means are back-transformed "
                                    "means of that, which reads as a typical rather than an average count."},
        {"key": "reference_year", "text": f"Years since description are counted to {REF_YEAR}."},
    ]


def main(n_boot):
    rng = np.random.default_rng(SEED)
    check_settled()
    d, m, n, rl_meta, rl = join()
    print(f"  {n['avonet']:,} AVONET species, {n['modelled']:,} modelled")
    conf = fit_all(m, TERMS_CONF)
    full = fit_all(m, TERMS_FULL)
    conf["robust"] = robust_se(m, TERMS_CONF)
    full["robust"] = robust_se(m, TERMS_FULL)
    for f in (conf, full):
        f["beta"] = {k: v for k, v in f["beta"].items() if not k.startswith("fam_")}
    print(f"  R2 confounders {conf['r2']:.3f}, full {full['r2']:.3f}")
    print("  drop-one R2, full:", {LABELS[k]: round(v, 4) for k, v in full["drop_r2"].items()})
    # Does the answer survive dropping the species whose Wikipedia article
    # is shared with another species, and the ones with no article at all?
    # Both are places where the attention term is measured badly.
    sens = {}
    for key, sub in (("unshared_article", m[m["article_shared_by"] <= 1]),
                     ("has_article", m[m["has_article"] == 1])):
        f = fit_all(sub, TERMS_FULL)
        sens[key] = {"n": f["n"], "dropped": int(len(m) - len(sub)), "r2": f["r2"],
                     "adjusted": f["adjusted"], "drop_r2": f["drop_r2"],
                     "cat_beta": {c: f["beta"]["cat_" + c] for c in CATS[1:]}}
        print(f"  sensitivity, {key}: n = {f['n']:,}, category drop-one R2 "
              f"{f['drop_r2']['category']:.4f} against {full['drop_r2']['category']:.4f}")
    boot = bootstrap(m, n_boot, rng)
    man = write_manifest(rl, rl_meta, n)
    P = {
        "categories_sha256": man["withheld"]["sha256"],
        "generated_from": ["fetch_traits.py", "fetch_years.py", "fetch_wikipedia.py", "fetch_openalex.py",
                           "fetch_iucn.py", "fetch_groups.py", "build_beauty.py"],
        "seed": SEED, "n_boot": n_boot, "reference_year": REF_YEAR,
        "categories": CATS, "category_names": CAT_NAMES, "term_labels": LABELS,
        "n": n, **rl_meta,
        "raw_by_category": raw_means(m),
        "model_confounders": {"terms": TERMS_CONF, **conf},
        "model_full": {"terms": TERMS_FULL, **full},
        "sensitivity": sens,
        "bootstrap": boot,
        "groups": groups(),
        "looked_up": looked_up(),
        "assumed": assumed(),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(P, open(OUT, "w", encoding="utf-8"), indent=1)
    cols = ["species", "family", "order", "mass_g", "range_km2", "year", "attractiveness",
            "article", "views_mean_monthly", "works_2015_2024"]
    m.sort_values("species")[cols + ["category"]].to_csv(JOINED, index=False)
    m.sort_values("species")[cols].to_csv(OPEN, index=False)
    print(f"  -> {os.path.relpath(OUT, HERE)}; {os.path.relpath(JOINED, HERE)} (not shipped); "
          f"{os.path.relpath(OPEN, HERE)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=300)
    ap.add_argument("--verify-categories", action="store_true",
                    help="check your Red List fetch against the manifest, and stop")
    a = ap.parse_args()
    if a.verify_categories:
        sys.exit(verify_categories())
    main(a.boot)
