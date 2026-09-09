"""
The failure modes particular to this project, plus the drift check every
generated page has.

  1. Nothing species-level with a Red List category leaves the machine: the
     payload names no species, and the shipped archive holds no file with a
     category column, no data/raw/, no birds_joined.csv.
  2. The page that ships was built from the Red List API, not from the
     labelled 2021 fallback.
  3. The category coefficients in the payload reproduce from birds_open.csv
     plus a Red List column (skipped, with a message, when there is none).
  4. site/beauty.html equals the template rendered from the payload.
  5. The three figures exist in site/assets.
  6. manifest.json ships, is current, and its digest of the withheld table
     matches the table the build actually used.
  7. The OpenAlex query is still the pinned one. See openalex_query() below:
     this is the check that catches an external API changing meaning under
     the code, which nothing else here does.

Run:  python3 test_beauty.py
"""

import csv
import io
import json
import os
import random
import re
import sys
import urllib.parse
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
PAYLOAD = os.path.join(HERE, "outputs", "beauty_payload.json")
MANIFEST = os.path.join(HERE, "manifest.json")
OPEN = os.path.join(HERE, "data", "birds_open.csv")
IUCN = os.path.join(HERE, "data", "iucn_aves.csv")
ZIP = os.path.join(ROOT, "site", "downloads", "beauty-code.zip")
PAGE = os.path.join(ROOT, "site", "beauty.html")
FIGS = ["beauty_fig1_gap.png", "beauty_fig2_category.png", "beauty_fig3_terms.png"]
CATCOL = re.compile(r"iucn|red_?list|categor", re.I)
PINNED = "title_and_abstract.search"


def model_maths(B=None):
    """Fit data whose coefficients are known, and check they come back.

    Takes the module under test so a mutated copy can be passed in: this
    check is only worth its lines if a broken estimator fails it, and the
    way to know that is to break one. See break_model.py beside this file.

    Check 3 in main() recomputes the coefficients from birds_open.csv and
    compares them to the payload. That is a drift check and nothing more:
    both sides call fit_all, so it passes whether or not fit_all is right.
    A sibling project on this site learned the sharper version of this the
    same night, where a test that reproduced a paper's published summary
    statistics passed while the model behind them was wrong, because the
    published values were ratios and errors in two terms cancelled. An
    aggregate can be right for compensating reasons; a coefficient cannot.

    So this fits synthetic data built from known coefficients and asserts
    the estimator recovers them, which catches the faults a drift check
    cannot see: a mis-coded dummy, a shifted reference category, a design
    matrix whose columns and names have come apart. Two exact invariants
    go with it, both independent of the numbers:

      * with category as the only term, the g-computed category means must
        equal the raw per-category means, because predicting every species
        under one category with nothing else in the model is that group's
        own mean;
      * dropping a term from an ordinary least-squares fit can never raise
        R-squared, so every drop-one value must be non-negative.

    And the coefficients are cross-checked against statsmodels, which is a
    second implementation of the same estimator rather than a second call
    to this one.

    What this does NOT cover, because the synthetic frame arrives already
    transformed: everything join() does to build it. A wrong log base, a
    reference year off by one, a filter that drops the wrong species, the
    name matching between AVONET and the Red List. Those are covered by
    checks 1 to 6 and by reading the counts the build prints, not here. Do
    not read a pass on this as a pass on the numbers.
    """
    import numpy as np
    import pandas as pd
    if B is None:
        import build_beauty as B
    fails = []
    rng = np.random.default_rng(7)
    n = 1200
    truth = {"log_mass": 0.42, "log_range": 0.31, "years_described": -0.006,
             "attractiveness": 0.18, "log_views": 0.55,
             "cat_NT": -0.20, "cat_VU": 0.35, "cat_EN": -0.45, "cat_CR": 0.60}
    fam_names = [f"Fam{i:02d}" for i in range(15)]
    fam_effect = dict(zip(fam_names, rng.normal(0, 0.4, len(fam_names))))
    df = pd.DataFrame({
        "family": rng.choice(fam_names, n),
        "log_mass": rng.normal(2, 0.8, n),
        "log_range": rng.normal(5, 1.2, n),
        "years_described": rng.integers(5, 260, n).astype(float),
        "attractiveness": rng.normal(6.5, 0.7, n),
        "log_views": rng.normal(2, 0.9, n),
        "category": pd.Categorical(rng.choice(B.CATS, n), B.CATS),
    })
    y = 1.5 + sum(truth[k] * df[k] for k in
                  ("log_mass", "log_range", "years_described", "attractiveness", "log_views"))
    y = y + df["family"].map(fam_effect).to_numpy()
    for c in B.CATS[1:]:
        y = y + truth["cat_" + c] * (df["category"] == c).to_numpy()
    df["y"] = y + rng.normal(0, 0.02, n)

    fit = B.fit_all(df, B.TERMS_FULL)
    for k, want in truth.items():
        got = fit["beta"].get(k)
        if got is None:
            fails.append(f"model: the full fit has no term {k}")
        elif abs(got - want) > 0.05:
            fails.append(f"model: {k} recovered as {got:+.3f}, built as {want:+.3f}")

    # statsmodels, as a second implementation of the same estimator
    rob = B.robust_se(df, B.TERMS_FULL)
    for k in truth:
        a, b = fit["beta"].get(k), rob.get(k, {}).get("coef")
        if a is not None and b is not None and abs(a - b) > 1e-8:
            fails.append(f"model: {k} is {a:+.6f} by lstsq and {b:+.6f} by statsmodels")

    # invariant: category alone, g-computed means are the raw means
    only = B.fit_all(df, ["category"])
    raw = {c: float(np.expm1(df.loc[df["category"] == c, "y"].mean())) for c in B.CATS}
    for c in B.CATS:
        if abs(only["adjusted"][c] - raw[c]) > 1e-6:
            fails.append(f"model: category-only adjusted mean for {c} is "
                         f"{only['adjusted'][c]:.4f}, the raw mean is {raw[c]:.4f}")

    # invariant: dropping a term cannot improve an OLS fit
    for t, v in fit["drop_r2"].items():
        if v < -1e-9:
            fails.append(f"model: dropping {t} raised R-squared by {-v:.5f}")

    # The manifest publishes a digest and a sentence describing how it was
    # made, and a reader with their own Red List fetch reimplements it from
    # that sentence. Comparing category_digest() against itself would prove
    # nothing, so the canonical form is built here a second time, straight
    # from the words the manifest carries: sorted 'species,category' lines,
    # LF endings, UTF-8, no header.
    import hashlib
    rl = pd.DataFrame({"species": ["Zosterops lateralis", "Abeillia abeillei", "Passer domesticus"],
                       "category": ["LC", "NT", "LC"]})
    blob = "species,category\n".replace("species,category\n", "")  # no header
    for s, c in sorted(zip(rl["species"], rl["category"])):
        blob += f"{s},{c}\n"
    want = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    got, rows = B.category_digest(rl)
    if got != want:
        fails.append("model: category_digest() does not match the canonical form the "
                     "manifest describes, so a reader reimplementing it from that "
                     "sentence would not reproduce the digest")
    if rows != 3:
        fails.append(f"model: category_digest() counted {rows} rows, not 3")
    return fails


def openalex_query():
    """OpenAlex redefined the bare `search=` parameter as full-text search in
    February 2026. `filter=title_and_abstract.search:` still means what
    `search=` used to mean, and the two now return different numbers for the
    same species: on 5 September 2026, "Panthera leo" gave 11,759 works
    through `search=` and 3,459 through the filter. Every count on this page
    is the second kind. An edit that reached for the shorter parameter would
    change what the whole page means while every other test kept passing,
    because the code would still be correct and the API would still answer.

    So: the URL the fetcher builds must carry the pinned filter and no bare
    search parameter, and the source must not grow a `search` key. This is a
    guard against a semantic change in someone else's API, which is the kind
    of drift the rest of the suite cannot see."""
    import fetch_openalex as O
    fails = []
    q = urllib.parse.parse_qs(urllib.parse.urlparse(O.url_for("Passer domesticus", "")).query)
    if "search" in q:
        fails.append("fetch_openalex.py builds a URL with a bare search= parameter; "
                     "since Feb 2026 that is full-text search, not title-and-abstract")
    if PINNED not in q.get("filter", [""])[0]:
        fails.append(f"fetch_openalex.py's filter= does not use {PINNED}:")
    if f"{PINNED}:" not in q.get("filter", [""])[0]:
        fails.append(f"fetch_openalex.py's filter= has {PINNED} without its colon")
    src = open(O.__file__, encoding="utf-8").read().replace(PINNED, "")
    for pat, why in ((r'["\']search["\']\s*:', 'a "search" key in the query parameters'),
                     (r'[?&]search=', 'a literal search= in a URL')):
        m = re.search(pat, src)
        if m:
            fails.append(f"fetch_openalex.py line {src[:m.start()].count(chr(10)) + 1}: "
                         f"{why}, outside {PINNED}")
    return fails


def settled_guard():
    """check_settled() must refuse a resumable table that does not say when
    its rows were fetched, and one that says something other than a date.

    The guard exists because a placeholder table sat in this folder on
    5 September 2026 while the archive was being rebuilt (HANDOFF trap 18).
    Its first version looked for a stamp column and checked the values it
    found, which meant a table with no stamp column passed in silence: on
    6 September wikipedia_views.csv had no such column and the guard had
    nothing to say about it. A guard that needs a column to exist before it
    can complain is trap 20 in a different coat.

    Three cases, each run against a private data directory holding two
    species and all three resumable tables, so no fetch running in the real
    one can touch the result:
      - a table with no `fetched` column, once per resumable table;
      - a table whose `fetched` values include a non-date, once per table;
      - all three stamped with a date, which must build.

    Proven against the guard as it stood on 6 September 2026 (trap 17):
    the three no-column cases all passed that guard, and this check
    reported all three; the three non-date cases were already refused; the
    clean case passed. After the guard was made total all seven agreed.
    """
    import contextlib
    import shutil
    import tempfile
    import build_beauty as B
    fails = []
    species = ["Passer domesticus", "Zosterops lateralis"]
    good = "2026-09-05"
    columns = {"description_years.csv": ["species", "matched_name", "authorship", "year", "source"],
               "wikipedia_views.csv": ["species", "article", "months", "views_total",
                                       "views_mean_monthly"],
               "openalex_counts.csv": ["species", "works_2015_2024", "cost_usd"]}
    filler = {"source": "gbif", "year": "1758", "months": "120", "views_total": "10",
              "views_mean_monthly": "0.08", "works_2015_2024": "3", "cost_usd": "0.0010"}

    def run(stamps):
        """stamps: table -> list of `fetched` values per species, or None for
        no column. Returns the refusal text, or '' when the guard passed."""
        tmp = tempfile.mkdtemp(prefix="beauty-guard-")
        data = os.path.join(tmp, "data")
        os.makedirs(data)
        with open(os.path.join(data, "avonet_slim.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["species", "family", "mass", "range"])
            for s in species:
                w.writerow([s, "F", "10", "100"])
        for name, cols in columns.items():
            st = stamps[name]
            hdr = cols + (["fetched"] if st is not None else [])
            with open(os.path.join(data, name), "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(hdr)
                for i, s in enumerate(species):
                    row = [s] + [filler.get(c, "") for c in cols[1:]]
                    w.writerow(row + ([st[i]] if st is not None else []))
        keep = B.HERE, B.DATA
        B.HERE, B.DATA = tmp, data
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                B.check_settled()
            return ""
        except SystemExit as e:
            return str(e)
        finally:
            B.HERE, B.DATA = keep
            shutil.rmtree(tmp, ignore_errors=True)

    clean = {n: [good, good] for n in columns}
    msg = run(clean)
    if msg:
        fails.append(f"guard: three correctly stamped tables were refused: {msg.strip()}")
    for name in columns:
        script = B.RESUMABLE[name]
        s = dict(clean)
        s[name] = None
        msg = run(s)
        if not msg:
            fails.append(f"guard: {name} with no fetched column was not refused")
        elif name not in msg or script not in msg or "fetched" not in msg:
            fails.append(f"guard: {name} with no fetched column was refused, but without "
                         f"naming the table, the column and {script}: {msg.strip()}")
        s[name] = [good, "placeholder"]
        msg = run(s)
        if not msg:
            fails.append(f"guard: {name} with a non-date fetched value was not refused")
        elif "placeholder" not in msg or script not in msg:
            fails.append(f"guard: {name} with a non-date fetched value was refused, but "
                         f"without naming the value and {script}: {msg.strip()}")
    return fails


def resume_repair():
    """netutil.trim_partial_row() must drop a trailing row cut short by a
    kill, keep every whole row, leave a clean file alone, and remove a
    file that is nothing but a partial header.

    The fetches are appends, and the OpenAlex one runs for days on a
    machine that reboots. A row cut mid-write would be read on the next
    start as a finished species with a truncated count, and the stamp
    guard would pass it if the cut fell after the date. Proven 6 September
    2026 two ways: against a trim that trims nothing, the cut-row and
    partial-header cases both reported and the clean case passed, as it
    should; against a netutil without the function, one report."""
    import tempfile
    import netutil
    fails = []
    fn = getattr(netutil, "trim_partial_row", None)
    if fn is None:
        return ["resume: netutil has no trim_partial_row()"]
    whole = "species,works_2015_2024,cost_usd,fetched\nAa bb,3,0.0010,2026-09-06\n"
    cases = [("cut row", whole + "Cc dd,12,0.00", whole, "Cc dd,12,0.00"),
             ("clean file", whole, whole, ""),
             ("partial header", "species,works_20", None, "species,works_20")]
    for label, before, after, dropped in cases:
        fd, p = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(p, "wb") as fh:
            fh.write(before.encode("utf-8"))
        got = fn(p)
        now = open(p, "rb").read().decode("utf-8") if os.path.exists(p) else None
        os.path.exists(p) and os.remove(p)
        if got != dropped:
            fails.append(f"resume: {label}: returned {got!r}, expected {dropped!r}")
        if now != after:
            fails.append(f"resume: {label}: file is {now!r} afterwards, expected {after!r}")
    return fails


def main():
    fails, skips = [], []
    if not os.path.exists(PAYLOAD) or not os.path.exists(OPEN):
        # The checks that do not need a build still run, so this is useful
        # before the first one: it is how the query guard was exercised
        # while the fetches were still going.
        print("  no build yet (outputs/beauty_payload.json); running what does not need one")
        fails = model_maths() + openalex_query() + settled_guard() + resume_repair()
        for f in fails:
            print("  FAIL: " + f)
        print(f"  {len(fails)} failure(s), the rest skipped until build_beauty.py has run")
        return 1 if fails else 0
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    species = [r["species"] for r in csv.DictReader(open(OPEN, encoding="utf-8"))]

    # 1a. no species named in the payload
    text = json.dumps(P)
    random.seed(1)
    sample = random.sample(species, min(300, len(species)))
    leaked = [s for s in sample if s in text]
    if leaked:
        fails.append(f"payload names species: {leaked[:3]}")

    # 1b. the archive
    if os.path.exists(ZIP):
        z = zipfile.ZipFile(ZIP)
        for name in z.namelist():
            base = name.rsplit("/", 1)[-1]
            if "data/raw/" in name or base in ("birds_joined.csv", "iucn_aves.csv"):
                fails.append(f"archive ships {name}")
                continue
            if base.endswith(".csv") and base != "iucn_table1a.csv":
                hdr = io.TextIOWrapper(z.open(name), encoding="utf-8").readline()
                bad = [c for c in hdr.strip().split(",") if CATCOL.search(c)]
                if bad:
                    fails.append(f"archive {name} has column(s) {bad}")
            if base.endswith(".json"):
                # EVERY species name, not a sample of fifty. The thing the
                # Red List's terms forbid is a species sitting beside its
                # category, so the operative question is whether any bird
                # this project models is named in a shipped JSON at all.
                text = z.read(name).decode("utf-8")
                named = [s for s in species if s in text]
                if named:
                    fails.append(f"archive {name} names species: {named[:3]}")
                # What was here until 2026-09-09, and why it went: a check
                # that failed when a file carried both a "species" key and a
                # "category" key. It fired the first time a real payload was
                # built - on looked_up.openalex_search_drift.species, which
                # is "Panthera leo" illustrating the OpenAlex query change,
                # and on the category COEFFICIENT dicts. Neither is a
                # species-to-category table and no bird was named. The key
                # heuristic was a way to catch a mapping without enumerating
                # names; enumerating all 9,113 names is strictly stronger and
                # does not misfire, so the heuristic adds only false
                # positives. If it is ever restored, it must test for a
                # binomial KEY with a category VALUE, not for two key names
                # co-occurring anywhere in a file.
    else:
        skips.append("no site/downloads/beauty-code.zip yet (rezip_downloads.py)")

    # 2. the shipped page's Red List source
    if P.get("redlist_source") != "api":
        fails.append(f"payload redlist_source is {P.get('redlist_source')!r}, not 'api' "
                     "(set IUCN_TOKEN, run fetch_iucn.py, rebuild)")

    # 3. coefficients reproduce
    if os.path.exists(IUCN):
        import build_beauty as B
        _, m, _, _, _ = B.join()
        f = B.fit_all(m, B.TERMS_CONF)
        for c in B.CATS[1:]:
            a, b = f["beta"]["cat_" + c], P["model_confounders"]["beta"]["cat_" + c]
            if abs(a - b) > 1e-6:
                fails.append(f"category {c} coefficient {a:.4f} != payload {b:.4f}")
        if f["n"] != P["n"]["modelled"]:
            fails.append(f"modelled n {f['n']} != payload {P['n']['modelled']}")
    else:
        skips.append("no data/iucn_aves.csv: coefficient recomputation skipped")

    # 4. page drift
    if os.path.exists(PAGE):
        import update_page
        rendered, probs = update_page.cite(update_page.render(P))
        if rendered != open(PAGE, encoding="utf-8").read():
            fails.append("site/beauty.html differs from the template rendered from the payload")
        fails += [f"citations: {p}" for p in probs]
    else:
        skips.append("no site/beauty.html yet")

    # 5. figures
    for f in FIGS:
        if not os.path.exists(os.path.join(ROOT, "site", "assets", f)):
            fails.append(f"missing site/assets/{f}")

    # 6. the manifest: present, shipped, current, and about the right table
    if not os.path.exists(MANIFEST):
        fails.append("no manifest.json; run build_beauty.py")
    else:
        M = json.load(open(MANIFEST, encoding="utf-8"))
        w = M.get("withheld", {})
        if w.get("ships") is not False or w.get("file") != "data/iucn_aves.csv":
            fails.append("manifest.json does not mark data/iucn_aves.csv as withheld")
        if len(w.get("sha256", "")) != 64:
            fails.append("manifest.json has no sha256 for the withheld table")
        if w.get("sha256") != P.get("categories_sha256"):
            fails.append("manifest.json and the payload disagree on the category digest; "
                         "one of them is stale")
        if M.get("red_list_version") != P.get("red_list_version"):
            fails.append("manifest.json and the payload disagree on the Red List version")
        for row in M.get("inputs", []):
            p = os.path.join(HERE, row["file"])
            if not os.path.exists(p):
                fails.append(f"manifest names {row['file']}, which is not there")
            else:
                import build_beauty as B
                h, size = B.file_digest(p)
                if h != row["sha256"]:
                    fails.append(f"{row['file']} has changed since the manifest was written")
        if os.path.exists(IUCN):
            import build_beauty as B
            rl, meta = B.redlist()
            digest, rows = B.category_digest(rl)
            if meta["redlist_source"] == "api" and digest != w.get("sha256"):
                fails.append(f"the Red List table here digests to {digest[:16]}..., the "
                             f"manifest says {w.get('sha256', '')[:16]}...; rebuild")
        else:
            skips.append("no data/iucn_aves.csv: manifest digest not re-derived")
        if os.path.exists(ZIP) and "manifest.json" not in zipfile.ZipFile(ZIP).namelist():
            fails.append("the archive does not ship manifest.json, so a reader cannot "
                         "check their own Red List fetch against it")

    # 7. the estimator recovers coefficients it was given, and the query
    #    still means what the page says it means
    fails += model_maths()
    fails += openalex_query()
    fails += settled_guard()
    fails += resume_repair()

    # 8. the build refuses to run on inputs that are still being written
    import build_beauty as B
    from netutil import Lock
    lk = Lock("test-guard", HERE)
    lk.__enter__()
    try:
        B.check_settled()
        fails.append("build_beauty.check_settled() did not refuse while a lock was live")
    except SystemExit as e:
        if "test-guard" not in str(e):
            fails.append(f"check_settled() refused, but not for the live lock: {e}")
    finally:
        lk.__exit__()

    for s in skips:
        print("  skip: " + s)
    for f in fails:
        print("  FAIL: " + f)
    print(f"  {len(fails)} failure(s), {len(skips)} skipped")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
