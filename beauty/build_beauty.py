"""
Join the bird tables, fit the models, write the payload.

Reads, from data/:
  avonet_slim.csv          mass, range, family (AVONET, CC BY 4.0)
  attractiveness_slim.csv  rated attractiveness (Santangeli et al. 2023, CC BY 4.0)
  description_years.csv            year of description (Catalogue of Life, CC BY)
  wikipedia_views.csv      monthly English Wikipedia views 2016-2025 (CC0)
  openalex_counts.csv      works 2015-2024 naming the species (CC0), September 2026
  openalex_types.csv       the same query split by OpenAlex record type (CC0),
                           from which the response, research works, is taken
  iucn_aves.csv            Red List category, from the reader's own token
                           (fetch_iucn.py); not in git, not in the archive
  iucn_table1a.csv, group_counts.csv   the five-class inputs for figure 1

If iucn_aves.csv is absent, the category column is taken from the
Santangeli deposit in data/raw/, which carries the Red List as the authors
had it (version 2022-1), and the payload says so in redlist_source. The page that
ships is built from the API column; test_beauty.py checks that.

The response is log(1 + research works): the works naming the species whose
OpenAlex type is research (record_types.RESEARCH), not the GBIF downloads and
Red List and Birds of the World entries that made up most of the old count
(D-32, R5 2026-10-24). Ordinary-least-squares fits with family fixed effects
and standard errors clustered by family:
  confounders   log mass, log range, years since description, category
  full          the same plus attractiveness and log views
From each: category means adjusted by g-computation (every species
predicted under each category, averaged, back-transformed), the drop-one
change in R-squared per term, and bootstrap intervals over families.

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
                  "wikipedia_views.csv", "openalex_counts.csv", "openalex_types.csv",
                  "iucn_table1a.csv", "group_counts.csv", "type_sources.csv"]
# Fetched for the species the build needs, not for all of AVONET, so it is
# checked against the join (join()) rather than in RESUMABLE.
TYPED = ("openalex_types.csv", "fetch_types.py")
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
# The TOTAL effect of category: attractiveness is in, Wikipedia views is out.
# Views is not a competitor sitting beside threat, it is on the pathway -
# dropping it raises every category coefficient, by 16% at Near Threatened
# rising to 34% at Critically Endangered - so a specification that controls
# for it answers a different question (the shares quoted here were measured
# on the September counts; on research works, R5 2026-10-24, the share of the
# CR term moving with views is 34%). The page quotes both multiples:
# TERMS_NOVIEWS is the total, TERMS_FULL is the direct.
TERMS_NOVIEWS = TERMS_CONF + ["attractiveness"]
TERMS_FULL = TERMS_NOVIEWS + ["views"]
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
    tp = os.path.join(DATA, TYPED[0])
    if not os.path.exists(tp):
        problems.append(f"data/{TYPED[0]} is missing; run {TYPED[1]}")
    else:
        rows = list(csv.DictReader(open(tp, encoding="utf-8")))
        bad = sorted({r.get(STAMP) or "(blank)" for r in rows
                      if not FETCH_STAMP.match(r.get(STAMP) or "")})
        if bad:
            problems.append(f"data/{TYPED[0]} has '{STAMP}' value(s) that are not dates: "
                            f"{', '.join(bad[:3])}; delete it and run {TYPED[1]}.")
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
            # D-33: section 4 bars redistribution "in their original format",
            # not "in any form"; section 3 leaves the categories' use free.
            "why": "The IUCN Red List terms of use (v3.1, June 2024, section 4) bar "
                   "redistributing Red List data in their original format, so this table is not in the "
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
    json.dump(M, open(MANIFEST, "w", encoding="utf-8", newline="\n"), indent=1)
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
    print("  NOTE: Red List category taken from the Santangeli 2023 deposit (Red List 2022-1 categories); "
          "set IUCN_TOKEN and run fetch_iucn.py for the current Red List")
    return r, {"redlist_source": "santangeli_2021_fallback", "red_list_version": "2022-1 (via Santangeli et al. 2023)",
               "citation": "Red List categories as carried in Santangeli et al. 2023, npj Biodiversity 2:20, "
                           "data deposit 10.6084/m9.figshare.22231504 (CC BY 4.0)"}


def typed():
    """data/openalex_types.csv -> one row per species with the record-type
    totals. works_typed is the whole count on the fetch date; research,
    journal, dataset and reference are its parts (record_types.py)."""
    import record_types as RT
    t = read(TYPED[0], dtype={"by_type": str})
    rows = []
    for sp, tot, by in zip(t["species"], t["works_total"], t["by_type"].fillna("")):
        c = RT.parse(by)
        if sum(c.values()) != int(tot):
            sys.exit(f"  {TYPED[0]}: {sp} types sum to {sum(c.values())}, total {tot}")
        rows.append({"species": sp, "works_typed": int(tot),
                     "research": RT.total(c, RT.RESEARCH), "journal": RT.total(c, RT.JOURNAL),
                     "dataset": RT.total(c, RT.DATASET), "reference": RT.total(c, RT.REFERENCE)})
    out = pd.DataFrame(rows)
    if out["species"].duplicated().any():
        sys.exit(f"  {TYPED[0]} has a species twice")
    return out


def join():
    av = read("avonet_slim.csv")
    at = read("attractiveness_slim.csv")
    yr = read("description_years.csv", dtype={"year": "Int64"})[["species", "year", "source"]].rename(
        columns={"source": "year_source"})
    wk = read("wikipedia_views.csv")[["species", "article", "views_mean_monthly"]]
    oa = read("openalex_counts.csv")[["species", "works_2015_2024"]]
    ty = typed()
    rl, rl_meta = redlist()
    n = {"avonet": len(av)}
    d = av.merge(at, on="species", how="left").merge(yr, on="species", how="left") \
          .merge(wk, on="species", how="left").merge(oa, on="species", how="left") \
          .merge(ty, on="species", how="left").merge(rl, on="species", how="left")
    # Every species with a Red List row must have its typed count: the model
    # frame, the selection check and the Data Deficient comparison all read
    # it, and a species missing here would drop out of all three silently.
    short = d["category"].notna() & d["research"].isna()
    if short.any():
        sys.exit(f"  data/{TYPED[0]} lacks {int(short.sum()):,} species with a Red List category; "
                 f"{TYPED[1]} has not finished. Nothing was built.")
    n["with_typed"] = int(d["research"].notna().sum())
    n["with_attractiveness"] = int(d["attractiveness"].notna().sum())
    n["with_year"] = int(d["year"].notna().sum())
    n["year_from_col"] = 0      # set on the model frame below
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
    keep = d["research"].notna() & d["attractiveness"].notna() & d["year"].notna() \
        & d["mass_g"].notna() & d["range_km2"].notna() & (d["range_km2"] > 0) \
        & d["category"].isin(CATS)
    m = d[keep].copy()
    n["modelled"] = int(len(m))
    n["dropped_not_assessed_or_dd_ex"] = int((~d["category"].isin(CATS) & d["research"].notna()
                                              & d["attractiveness"].notna() & d["year"].notna()).sum())
    m["works"] = m["research"].astype(int)
    m["y"] = np.log1p(m["works"])
    m["log_mass"] = np.log10(m["mass_g"])
    m["log_range"] = np.log10(m["range_km2"])
    m["years_described"] = REF_YEAR - m["year"].astype(int)
    m["log_views"] = np.log10(1 + m["views"])
    m["category"] = pd.Categorical(m["category"], CATS)
    n["modelled_shared_article"] = int((m["article_shared_by"] > 1).sum())
    n["year_from_col"] = int((m["year_source"] == "col").sum())
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
            "noviews_adj": {c: [] for c in CATS},
            "full_adj": {c: [] for c in CATS}, "conf_drop": {t: [] for t in TERMS_CONF},
            "full_drop": {t: [] for t in TERMS_FULL},
            "conf_cat": {c: [] for c in CATS[1:]}, "full_cat": {c: [] for c in CATS[1:]},
            # The multiple the page prints: adjusted typical count under a
            # category over the same under Least Concern. Not exp(coef): on
            # log(1 + x) that is the ratio of (1 + count), which put "x3.8"
            # beside typical values of 1.9 and 10.1 in the R5 interim fit.
            "noviews_ratio": {c: [] for c in CATS[1:]}, "full_ratio": {c: [] for c in CATS[1:]}}
    # Families, not species, are resampled: species in one family are not
    # independent draws (QA, D-32), and a species bootstrap gave intervals
    # as narrow as the HC1 errors. A family drawn twice keeps one fixed
    # effect, which is what its identical rows estimate anyway.
    fams = m["family"].unique()
    rows_of = {f: np.flatnonzero(m["family"].to_numpy() == f) for f in fams}
    for b in range(n_boot):
        pick = rng.choice(fams, len(fams), replace=True)
        s = m.iloc[np.concatenate([rows_of[f] for f in pick])]
        for c in CATS:
            sub = s[s["category"] == c]
            keys["raw"][c].append(float(np.expm1(sub["y"].mean())) if len(sub) else np.nan)
        for tag, terms in (("conf", TERMS_CONF), ("noviews", TERMS_NOVIEWS),
                           ("full", TERMS_FULL)):
            f = fit_all(s, terms)
            for c in CATS:
                keys[tag + "_adj"][c].append(f["adjusted"][c])
            if tag + "_drop" in keys:
                for t in terms:
                    keys[tag + "_drop"][t].append(f["drop_r2"][t])
            if tag + "_ratio" in keys:
                for c in CATS[1:]:
                    keys[tag + "_ratio"][c].append(f["adjusted"][c] / f["adjusted"]["LC"])
            if tag + "_cat" in keys:
                for c in CATS[1:]:
                    keys[tag + "_cat"][c].append(f["beta"]["cat_" + c])
        if (b + 1) % 50 == 0:
            print(f"  bootstrap {b + 1}/{n_boot}")

    def ci(v):
        v = np.array(v, float)
        v = v[~np.isnan(v)]
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [None, None]
    return {k: {kk: ci(vv) for kk, vv in d.items()} for k, d in keys.items()}


def clustered(m, X, y=None):
    """OLS with errors clustered by family. Species in one family share more
    than the fixed effect takes out; QA found the HC1 errors this replaced
    understated the Critically Endangered term's (0.060 against 0.084)."""
    import statsmodels.api as sm
    y = m["y"].to_numpy(float) if y is None else y
    return sm.OLS(y, X).fit(cov_type="cluster",
                            cov_kwds={"groups": pd.factorize(m["family"])[0]})


def robust_se(m, terms):
    X, names = design(m, terms)
    res = clustered(m, X)
    return {n: {"coef": float(res.params[i]), "se": float(res.bse[i]), "p": float(res.pvalues[i])}
            for i, n in enumerate(names) if not n.startswith("fam_")}


def selection(d):
    """What conditioning the sample on a rated attractiveness score does.

    The model needs an attractiveness score, which 1,472 species in an
    otherwise-complete frame do not have. Marginally those species are
    less-studied, smaller-ranged and later-described, and Critically
    Endangered species are missing at nearly twice the base rate - but the
    page's claim is a CONDITIONAL coefficient, and the dropped species
    differ on covariates the model already adjusts for, so an unknown share
    of the marginal gap is absorbed by the specification. A median
    difference cannot fix the sign of a multivariate term.

    So this fits the same reduced specification on both samples, with
    attractiveness out of the model entirely, and the difference between
    the two sets of category coefficients IS the selection effect.
    selection_check.py is the same computation standing alone, and gates
    itself on reproducing join()'s sample before reading anything from it.
    """
    import statsmodels.api as sm
    out = {}
    for tag, need in (("A_no_rating_required", False), ("B_modelled", True)):
        keep = (d["research"].notna() & d["year"].notna()
                & d["mass_g"].notna() & d["range_km2"].notna() & (d["range_km2"] > 0)
                & d["category"].isin(CATS))
        if need:
            keep = keep & d["attractiveness"].notna()
        s = d[keep].copy()
        s["y"] = np.log1p(s["research"].astype(int))
        s["log_mass"] = np.log10(s["mass_g"])
        s["log_range"] = np.log10(s["range_km2"])
        s["years_described"] = REF_YEAR - s["year"].astype(int)
        s["category"] = pd.Categorical(s["category"], CATS)
        X, names = design(s, TERMS_CONF)
        res = clustered(s, X)
        ci = res.conf_int()
        cats = {}
        for c in CATS[1:]:
            i = names.index("cat_" + c)
            cats[c] = {"coef": float(res.params[i]), "lo": float(ci[i][0]),
                       "hi": float(ci[i][1]), "p": float(res.pvalues[i])}
        out[tag] = {"n": int(len(s)), "category": cats}
    a, b = out["A_no_rating_required"]["category"], out["B_modelled"]["category"]
    out["difference"] = {c: {"B_minus_A": b[c]["coef"] - a[c]["coef"],
                             "intervals_overlap": not (b[c]["lo"] > a[c]["hi"]
                                                       or a[c]["lo"] > b[c]["hi"])}
                         for c in CATS[1:]}
    out["dropped"] = out["A_no_rating_required"]["n"] - out["B_modelled"]["n"]
    return out


def data_deficient(d):
    """Works for Data Deficient birds, descriptive, alongside every category.

    A bird cannot be listed Critically Endangered without evidence, and
    that evidence is research: the arrow may run research -> listing rather
    than listing -> research, which would produce the same monotone
    gradient from a completely different mechanism. Data Deficient is the
    category meaning nobody has enough data, so where it falls is the
    cheapest available check on that story.

    DESCRIPTIVE ONLY. 34 species does not support a fitted coefficient and
    must not be given one, and nothing here appears as a point in a figure.
    """
    out = {}
    sub = d[d["research"].notna() & d["category"].notna()]
    for c in ["DD"] + CATS + ["EW", "EX"]:
        v = sub.loc[sub["category"] == c, "research"].to_numpy(float)
        if not len(v):
            continue
        out[c] = {"n": int(len(v)), "p25": float(np.percentile(v, 25)),
                  "median": float(np.median(v)), "p75": float(np.percentile(v, 75)),
                  "mean": float(v.mean())}
    return {"by_category": out, "frame": int(len(sub)),
            "note": "Descriptive only, on research works. Data Deficient is too few "
                    "species for a coefficient; it appears in no figure."}


def record_types(m):
    """What the old count was made of, and whether the effect is the paperwork.

    Replaces the topic-field strata test (D-32): QA found GBIF downloads and
    Red List entries are filed under every topic field, molecular biology
    included, so a field could not separate paperwork from research. The
    record type can. For each category: the raw shares of the typed total;
    and the total-effect model refitted on each part separately, so the page
    can say how much of the old Critically Endangered gap was each kind of
    record.
    """
    out = {"shares": {}, "fits": {}, "zero_research": {}}
    for c in CATS:
        s = m[m["category"] == c]
        tot = float(s["works_typed"].sum())
        out["shares"][c] = {"n": int(len(s)), "works_typed": int(tot),
                            "research": float(s["research"].sum() / tot),
                            "dataset": float(s["dataset"].sum() / tot),
                            "reference": float(s["reference"].sum() / tot),
                            "other": float(1 - (s["research"].sum() + s["dataset"].sum()
                                                + s["reference"].sum()) / tot),
                            "mean_typed": float(s["works_typed"].mean()),
                            "mean_research": float(s["research"].mean()),
                            "mean_dataset": float(s["dataset"].mean()),
                            "mean_reference": float(s["reference"].mean())}
        out["zero_research"][c] = float((s["research"] == 0).mean())
    out["zero_research"]["all"] = float((m["research"] == 0).mean())
    # The page names the well-known common birds that pull the Least
    # Concern average up; this is how many have 100 research works or more.
    out["famous_lc"] = int(((m["category"] == "LC") & (m["research"] >= 100)).sum())
    out["zero_typed_all"] = float((m["works_typed"] == 0).mean())
    X, names = design(m, TERMS_NOVIEWS)
    for col in ("works_typed", "works_2015_2024", "research", "journal", "dataset", "reference"):
        y = np.log1p(m[col].to_numpy(float))
        res = clustered(m, X, y)
        ci = res.conf_int()
        beta = res.params
        s = m.copy()
        s["y"] = y
        adj = category_means(s, X, names, beta)
        out["fits"][col] = {c: {"coef": float(beta[names.index("cat_" + c)]),
                                "lo": float(ci[names.index("cat_" + c)][0]),
                                "hi": float(ci[names.index("cat_" + c)][1]),
                                "p": float(res.pvalues[names.index("cat_" + c)])}
                            for c in CATS[1:]}
        out["fits"][col]["adjusted"] = adj
    return out


def type_sources():
    """fetch_type_sources.py's spot check: what share of the sampled
    species' datasets are GBIF's, and of their reference entries the Red
    List's or Birds of the World's."""
    t = read("type_sources.csv")
    def share(typ, names):
        s = t[t["type"] == typ]
        return float(s[s["source"].isin(names)]["works"].sum() / s["of_type"].iloc[0])
    return {"species_sampled": int(t["species_sampled"].iloc[0]), "fetched": str(t["fetched"].iloc[0]),
            "gbif_share_of_datasets": share("dataset", ["Global Biodiversity Information Facility"]),
            "iucn_bow_share_of_reference": share("reference-entry", ["IUCN Red List of Threatened Species",
                                                                      "Birds of the World"])}


def count_model(m):
    """Poisson (PPML) on research works, same design, family-clustered.

    A check, not the headline. It estimates the ratio of MEAN counts, which
    heavily studied birds dominate; the log(1 + x) fit estimates the ratio
    of typical counts. QA's count model on its interim cleaned counts gave
    x1.84 with an interval from about x0.76 to x4.4, so the page has to say
    what this one gives whichever way it falls."""
    import statsmodels.api as sm
    X, names = design(m, TERMS_NOVIEWS)
    res = sm.GLM(m["research"].to_numpy(float), X, family=sm.families.Poisson()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(m["family"])[0]}, maxiter=300)
    ci = res.conf_int()
    return {c: {"coef": float(res.params[names.index("cat_" + c)]),
                "lo": float(ci[names.index("cat_" + c)][0]),
                "hi": float(ci[names.index("cat_" + c)][1]),
                "p": float(res.pvalues[names.index("cat_" + c)])} for c in CATS[1:]}


def groups():
    t = read("iucn_table1a.csv")
    g = read("group_counts.csv")
    # research, not works: the class counts carried GBIF downloads and
    # reference entries too (8,042 of them for amphibians), D-32.
    g = g.drop(columns=["works"]).rename(columns={"research": "works"})
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
        {"key": "paper_definition", "text": "A research work about a species is an OpenAlex work of 2015-2024 "
                                            "whose title or abstract contains the scientific name as a phrase "
                                            "and whose OpenAlex type is a research type (record_types.py)."},
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
    noviews = fit_all(m, TERMS_NOVIEWS)
    full = fit_all(m, TERMS_FULL)
    conf["robust"] = robust_se(m, TERMS_CONF)
    noviews["robust"] = robust_se(m, TERMS_NOVIEWS)
    full["robust"] = robust_se(m, TERMS_FULL)
    for f in (conf, noviews, full):
        f["beta"] = {k: v for k, v in f["beta"].items() if not k.startswith("fam_")}
    print(f"  R2 confounders {conf['r2']:.3f}, full {full['r2']:.3f}")
    print("  drop-one R2, full:", {LABELS[k]: round(v, 4) for k, v in full["drop_r2"].items()})
    # Does the answer survive dropping the species whose Wikipedia article
    # is shared with another species, and the ones with no article at all?
    # Both are places where the attention term is measured badly.
    sens = {}
    j = m.copy()
    j["y"] = np.log1p(j["journal"].astype(float))
    fj = fit_all(j, TERMS_NOVIEWS)
    sens["journal_only"] = {"n": fj["n"], "adjusted": fj["adjusted"],
                            "cat_beta": {c: fj["beta"]["cat_" + c] for c in CATS[1:]}}
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
                           "fetch_types.py", "fetch_iucn.py", "fetch_groups.py", "build_beauty.py"],
        "seed": SEED, "n_boot": n_boot, "reference_year": REF_YEAR,
        "categories": CATS, "category_names": CAT_NAMES, "term_labels": LABELS,
        "n": n, **rl_meta,
        "raw_by_category": raw_means(m),
        "model_confounders": {"terms": TERMS_CONF, **conf},
        "model_noviews": {"terms": TERMS_NOVIEWS, **noviews},
        "model_full": {"terms": TERMS_FULL, **full},
        "mediated_share": {c: (noviews["beta"]["cat_" + c] - full["beta"]["cat_" + c])
                              / noviews["beta"]["cat_" + c] for c in CATS[1:]},
        "selection": selection(d),
        "data_deficient": data_deficient(d),
        "record_types": record_types(m),
        "count_model": count_model(m),
        "type_sources": type_sources(),
        "types_fetched": sorted(set(read(TYPED[0])["fetched"].astype(str))),
        "sensitivity": sens,
        "bootstrap": boot,
        "groups": groups(),
        "looked_up": looked_up(),
        "assumed": assumed(),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(P, open(OUT, "w", encoding="utf-8", newline="\n"), indent=1)
    cols = ["species", "family", "order", "mass_g", "range_km2", "year", "attractiveness",
            "article", "views_mean_monthly", "works_2015_2024", "works_typed", "research",
            "dataset", "reference"]
    m.sort_values("species")[cols + ["category"]].to_csv(JOINED, index=False, lineterminator="\n")
    m.sort_values("species")[cols].to_csv(OPEN, index=False, lineterminator="\n")
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
