"""
Write site/beauty.html from template.html, outputs/beauty_payload.json and
models.json.

Every number on the page comes from the payload; the prose is in the
template. The page that ships also carries things other scripts own - the
nav (rebuild_nav.py), the citation markers and Sources list
(add_citations.py), the ?v= cache stamps (bust_cache.py) and the image
dimensions (sync_img_dims.py) - so this script keeps each of those as the
shipped page has it, and the drift check (tests/test_generators.py) can run
it on the shipped tree and expect no change. The idiom is food/update_page.py's.

Run:  python3 update_page.py            report only
      python3 update_page.py --apply
"""

import argparse
import datetime as dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "beauty.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "beauty_payload.json")
MODELS = os.path.join(HERE, "models.json")
MANIFEST = os.path.join(HERE, "manifest.json")
COUNTS = os.path.join(HERE, "data", "openalex_counts.csv")
# A free OpenAlex key's daily allowance in dollars, measured from the
# X-RateLimit-Limit-USD header on 6 September 2026.
OPENALEX_DAILY_USD = 1.00
ZIP = os.path.join(SITE, "downloads", "beauty-code.zip")
sys.path.insert(0, ROOT)


WORDS = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def fmt(n):
    return f"{n:,}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}"


def openalex_cost():
    """What the per-species fetch actually cost: the cost_usd column of
    the table that ships, summed, and the rows it has. The run log is
    provenance for the same figure, but it is written when a run ends, so
    a run that was killed leaves rows in the table and no line in the log;
    the table is the artefact the page describes, so the table is what is
    summed (HANDOFF trap 20)."""
    import csv
    if not os.path.exists(COUNTS):
        return 0.0, 0
    rows = list(csv.DictReader(open(COUNTS, encoding="utf-8")))
    return sum(float(r["cost_usd"] or 0) for r in rows), len(rows)


def values(P):
    n = P["n"]
    raw = P["raw_by_category"]
    conf = P["model_confounders"]
    full = P["model_full"]
    B = P["bootstrap"]
    G = P["groups"]
    lu = P["looked_up"]
    M = json.load(open(MODELS, encoding="utf-8"))["models"]
    MAN = json.load(open(MANIFEST, encoding="utf-8"))
    dr = lu["openalex_search_drift"]
    nov = P["model_noviews"]
    st = P["strata"]
    dcat = P["data_deficient"]["by_category"]
    g = {r["group"]: r for r in G["rows"]}
    read = [m for m in M if m["read"] == "full text"]
    verdicts = {}
    for m in M:
        verdicts.setdefault(m["verdict"], []).append(m)
    n_null_or_neg = sum(1 for m in read if m["verdict"] in ("null", "negative"))
    n_null_or_neg_adj = sum(1 for m in read if m["verdict"] in ("null", "negative") and m["adjusted"])
    cost, cost_n = openalex_cost()
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0
    cr, lc = raw["CR"]["typical"], raw["LC"]["typical"]
    acr, alc = conf["adjusted"]["CR"], conf["adjusted"]["LC"]
    p_cr = conf["robust"]["cat_CR"]["p"]
    p_en = conf["robust"]["cat_EN"]["p"]
    drop = full["drop_r2"]
    rank = sorted(drop, key=lambda t: -drop[t])
    top = rank[0]
    ratio_top_cat = drop[top] / drop["category"] if drop["category"] > 0 else float("inf")
    v = {
        "n_avonet": fmt(n["avonet"]), "n_modelled": fmt(n["modelled"]),
        "n_attract": fmt(n["with_attractiveness"]), "n_article": fmt(n["with_article"]),
        "n_year": fmt(n["with_year"]), "n_works": fmt(n["with_works"]), "n_category": fmt(n["with_category"]),
        "n_dropped_dd": fmt(n["dropped_not_assessed_or_dd_ex"]),
        "n_no_article": fmt(n["avonet"] - n["with_article"]),
        "n_shared_views": fmt(n["views_shared_article"]),
        "n_shared_articles": fmt(n["shared_articles"]),
        "n_modelled_shared": fmt(n["modelled_shared_article"]),
        "sens_shared_cat_drop": f"{P['sensitivity']['unshared_article']['drop_r2']['category']:.3f}",
        "sens_article_cat_drop": f"{P['sensitivity']['has_article']['drop_r2']['category']:.3f}",
        "red_list_version": P["red_list_version"], "redlist_source_word":
            "the Red List API" if P["redlist_source"] == "api" else "the 2021 categories in the Santangeli deposit",
        "n_boot": fmt(P["n_boot"]), "seed": P["seed"], "ref_year": P["reference_year"],
        "r2_conf": f"{conf['r2']:.2f}", "r2_full": f"{full['r2']:.2f}",
        # figure 1
        "amph_share_thr": pct(g["Amphibians"]["share_threatened"]), "amph_share_works": pct(g["Amphibians"]["share_works"]),
        "amph_per": f"{g['Amphibians']['works_per_threatened']:.0f}",
        "rept_per": f"{g['Reptiles']['works_per_threatened']:.0f}",
        "birds_share_thr": pct(g["Birds"]["share_threatened"]), "birds_share_works": pct(g["Birds"]["share_works"]),
        "birds_per": f"{g['Birds']['works_per_threatened']:.0f}",
        "mamm_per": f"{g['Mammals']['works_per_threatened']:.0f}", "fish_per": f"{g['Fishes']['works_per_threatened']:.0f}",
        "birds_over_amph": f"{g['Birds']['works_per_threatened'] / g['Amphibians']['works_per_threatened']:.0f}",
        "amph_pct_thr": g["Amphibians"]["pct_threatened_best"], "birds_pct_thr": g["Birds"]["pct_threatened_best"],
        "amph_threatened": fmt(g["Amphibians"]["threatened"]), "birds_threatened": fmt(g["Birds"]["threatened"]),
        "total_threatened": fmt(G["total_threatened"]), "total_works": fmt(G["total_works"]),
        "works_years": G["works_years"],
        # figure 2
        "lc_raw": f"{lc:.1f}", "cr_raw": f"{cr:.1f}", "en_raw": f"{raw['EN']['typical']:.1f}",
        "lc_adj": f"{alc:.1f}", "cr_adj": f"{acr:.1f}", "en_adj": f"{conf['adjusted']['EN']:.1f}",
        "lc_n": fmt(raw["LC"]["n"]), "cr_n": fmt(raw["CR"]["n"]), "en_n": fmt(raw["EN"]["n"]),
        "vu_n": fmt(raw["VU"]["n"]), "nt_n": fmt(raw["NT"]["n"]),
        "lc_zero_pct": pct(raw["LC"]["share_zero"]), "cr_zero_pct": pct(raw["CR"]["share_zero"]),
        "cr_raw_ci": f"{B['raw']['CR'][0]:.1f} to {B['raw']['CR'][1]:.1f}",
        "cr_adj_ci": f"{B['conf_adj']['CR'][0]:.1f} to {B['conf_adj']['CR'][1]:.1f}",
        "raw_cr_vs_lc": "more" if cr > lc else "fewer",
        "raw_cr_vs_lc_pct": pct(abs(cr / lc - 1)),
        "adj_cr_vs_lc": "more" if acr > alc else "fewer",
        "adj_cr_vs_lc_pct": pct(abs(acr / alc - 1)),
        "cr_coef": f"{conf['beta']['cat_CR']:+.2f}", "cr_p": f"{p_cr:.2f}" if p_cr >= 0.01 else "under 0.01",
        "en_coef": f"{conf['beta']['cat_EN']:+.2f}", "en_p": f"{p_en:.2f}" if p_en >= 0.01 else "under 0.01",
        # figure 3
        "top_term": P["term_labels"][top].lower(), "top_drop": f"{drop[top]:.3f}",
        "second_term": P["term_labels"][rank[1]].lower(), "second_drop": f"{drop[rank[1]]:.3f}",
        "cat_drop": f"{drop['category']:.3f}", "cat_rank": str(rank.index("category") + 1),
        "attr_drop": f"{drop['attractiveness']:.3f}", "views_drop": f"{drop['views']:.3f}",
        "family_drop": f"{drop['family']:.3f}", "range_drop": f"{drop['range']:.3f}",
        "mass_drop": f"{drop['mass']:.3f}", "described_drop": f"{drop['described']:.3f}",
        "top_over_cat": f"{ratio_top_cat:.0f}" if ratio_top_cat != float("inf") else "many",
        "attr_coef": f"{full['robust']['attractiveness']['coef']:+.2f}",
        "attr_p": f"{full['robust']['attractiveness']['p']:.2f}" if full["robust"]["attractiveness"]["p"] >= 0.01 else "under 0.01",
        "views_coef": f"{full['robust']['log_views']['coef']:+.2f}",
        # the literature
        "n_models": str(len(M)), "n_read": str(len(read)),
        "n_null_or_neg": str(n_null_or_neg), "n_null_or_neg_adj": str(n_null_or_neg_adj),
        "n_null": str(len(verdicts.get("null", []))), "n_negative": str(len(verdicts.get("negative", []))),
        "n_unread": str(sum(1 for m in M if m["read"] != "full text")),
        "n_models_word": WORDS.get(len(M), str(len(M))).capitalize(),
        "n_abstract_word": (lambda k: f"{WORDS.get(k, str(k)).capitalize()} {'is' if k == 1 else 'are'}")(
            sum(1 for m in M if m["read"] == "abstract")),
        "n_none_word": WORDS.get(sum(1 for m in M if m["read"] == "none"), "some"),
        "models_rows": "".join(
            f"<tr><td>{m['label']}</td><td>{m['taxon']}, {fmt(m['n'])}</td>"
            f"<td>{m['verdict'].replace('-', ', ')}</td><td>{m['read']}</td></tr>"
            for m in M),
        # looked up
        "esa_top10": lu["esa_top10_share"]["value"], "life_pct": lu["life_birds_mammals_budget"]["value"],
        "global_funded_pct": lu["global_threatened_ever_funded"]["value"],
        "global_lc_pct": lu["global_funds_to_least_concern"]["value"],
        "dd_mammals": lu["dd_mammals_predicted_threatened"]["value"],
        "dd_amph": lu["dd_amphibians_predicted_threatened"]["value"],
        "extinct_est": lu["extinct_since_1500_estimate"]["value"], "extinct_rl": lu["extinct_since_1500_red_list"]["value"],
        # the code
        "openalex_cost": f"{cost:.2f}", "openalex_cost_n": fmt(cost_n),
        "openalex_days": fmt(max(1, int(-(-cost // OPENALEX_DAILY_USD)))), "zip_kb": fmt(zip_kb),
        "cat_sha_short": P["categories_sha256"][:16], "cat_rows": fmt(MAN["withheld"]["rows"]),
        "drift_date": (lambda d: f"{d.day} {d:%B %Y}")(dt.date.fromisoformat(dr["observed"])),
        "drift_common": dr["common"], "drift_fulltext": fmt(dr["fulltext"]),
        "drift_filter": fmt(dr["title_abstract"]),
        "drift_ratio": f"{dr['fulltext'] / dr['title_abstract']:.1f}",
        # the total effect, and the share of it running through attention
        "cr_tot": f"{nov['adjusted']['CR']:.1f}", "lc_tot": f"{nov['adjusted']['LC']:.1f}",
        "cr_tot_coef": f"{nov['beta']['cat_CR']:+.2f}",
        "cr_tot_x": f"{math.exp(nov['beta']['cat_CR']):.2f}",
        "cr_dir_coef": f"{full['beta']['cat_CR']:+.2f}",
        "cr_dir_x": f"{math.exp(full['beta']['cat_CR']):.2f}",
        "cr_tot_ci": f"{B['noviews_adj']['CR'][0]:.1f} to {B['noviews_adj']['CR'][1]:.1f}",
        "med_nt": pct(P["mediated_share"]["NT"]), "med_cr": pct(P["mediated_share"]["CR"]),
        "med_vu": pct(P["mediated_share"]["VU"]), "med_en": pct(P["mediated_share"]["EN"]),
        "views_over_attr": f"{drop['views'] / drop['attractiveness']:.0f}",
        # selection: what conditioning on a rated score does
        "sel_dropped": fmt(P["selection"]["dropped"]),
        "sel_n_a": fmt(P["selection"]["A_no_rating_required"]["n"]),
        "sel_cr_a": f"{P['selection']['A_no_rating_required']['category']['CR']['coef']:+.3f}",
        "sel_cr_b": f"{P['selection']['B_modelled']['category']['CR']['coef']:+.3f}",
        # the assessment-evidence confound
        # The DD table has its OWN frame: every bird with a Red List
        # category and a works count. The fits need an attractiveness
        # rating too, so they run on fewer. Two frames on one page, and
        # the page names which is which rather than letting a reader
        # assume one N covers both.
        "dd_frame": fmt(sum(v["n"] for v in dcat.values())),
        "dd_n": fmt(P["data_deficient"]["by_category"]["DD"]["n"]),
        "nt_median": f"{dcat['NT']['median']:.0f}",
        "en_median": f"{dcat['EN']['median']:.0f}",
        "cr_median": f"{dcat['CR']['median']:.0f}",
        "ew_n": fmt(dcat["EW"]["n"]), "ew_median": f"{dcat['EW']['median']:.0f}",
        "dd_median": f"{P['data_deficient']['by_category']['DD']['median']:.0f}",
        "lc_median": f"{P['data_deficient']['by_category']['LC']['median']:.0f}",
        # the pre-registered stratum test
        "strat_primary_cr": f"{st['fields']['13']['category']['CR']['coef']:+.3f}",
        "strat_primary_x": f"{math.exp(st['fields']['13']['category']['CR']['coef']):.2f}",
        "strat_control_cr": f"{st['fields']['23']['category']['CR']['coef']:+.3f}",
        "strat_earth_cr": f"{st['fields']['19']['category']['CR']['coef']:+.3f}",
        "strat_floor": f"{st['rule']['cr_floor']:+.2f}",
        "strat_min_cell": str(st["rule"]["min_cell_per_category"]),
        "strat_failed": fmt(sum(1 for f in st["fields"].values() if not f["reportable"])),
        "strat_crude_cr": f"{st['crude_exclusion']['category']['CR']:+.3f}",
        "strat_inflation": pct(1 - st["crude_exclusion"]["category"]["CR"]
                              / conf["beta"]["cat_CR"]),
        "conf_cr_coef": f"{conf['beta']['cat_CR']:+.3f}",
    }
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "food.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    text = re.sub(r'(href|src)="([^"?]+\.(?:css|js|png))"', stamp, text)
    return text


def image_dims(text):
    from PIL import Image

    def dims(m):
        src = m.group(1)
        w, h = Image.open(os.path.join(SITE, src)).size
        return f'src="assets/{src.split("/", 1)[1]}{m.group(2)}" loading="lazy" width="{w}" height="{h}"'
    return re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"', dims, text)


def span(text):
    """The marginalia asides span the grid rows that follow them: the count
    of top-level elements in <main> after the asides, plus one."""
    main = text[text.index("<main"):text.index("</main>")]
    body = re.sub(r"<aside.*?</aside>", "", main, flags=re.S)
    body = body[body.index(">") + 1:]
    depth, n = 0, 0
    for m in re.finditer(r"<(/?)(\w+)[^>]*?>", body):
        close, tag = m.group(1), m.group(2)
        if tag in ("img", "br", "hr", "meta", "link", "input"):
            n += depth == 0
            continue
        if close:
            depth -= 1
        else:
            n += depth == 0
            depth += 1
    return n + 1


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav", "span"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    t = keep_from_shipped(t, shipped)
    t = image_dims(t)
    t = t.replace("{{span}}", str(span(t)))
    return t


def cite(text):
    """Citation markers and the Sources list, from add_citations.py's table
    for this page, applied to the rendered text so a re-run reproduces the
    shipped page exactly."""
    import add_citations
    refs = add_citations.PAGES.get("beauty.html")
    if not refs:
        return text, ["beauty.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    # An explicit LF newline, and never newline="": .gitattributes stores
    # this tree as LF, and Python text mode on Windows writes CRLF
    # otherwise. HANDOFF trap 32, and the sweeps of 6, 7 and 9 September
    # could not reach this generator because it had never produced a page:
    # beauty.html was the only file in site/ with CRLF when it first ran.
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    t = render(P)
    t, probs = cite(t)
    for p in probs:
        print("  " + p)
    if os.path.exists(PAGE):
        old = open(PAGE, encoding="utf-8").read()
        print("  beauty.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  beauty.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
