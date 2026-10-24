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
COUNTS = os.path.join(HERE, "data", "openalex_types.csv")
LC_MATCHED = os.path.join(HERE, "data", "lc_matched.csv")
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
    """What the per-species record-type fetch (fetch_types.py) actually
    cost: the cost_usd column of the table that ships, summed, and the rows
    it has. The run log is
    provenance for the same figure, but it is written when a run ends, so
    a run that was killed leaves rows in the table and no line in the log;
    the table is the artefact the page describes, so the table is what is
    summed (HANDOFF trap 20)."""
    import csv
    if not os.path.exists(COUNTS):
        return 0.0, 0
    rows = list(csv.DictReader(open(COUNTS, encoding="utf-8")))
    return sum(float(r["cost_usd"] or 0) for r in rows), len(rows)


ORDINAL = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
           7: "seventh"}


def values(P):
    """Every number on the page, from the payload.

    One definition of "times" throughout (R5, 2026-10-24): the adjusted
    typical count under a category over the same under Least Concern, from
    the g-computed means. exp(coef) is not printed as a multiple, because on
    log(1 + x) it is the ratio of (1 + count) and disagrees with the two
    typical values printed beside it. The count model's exp(coef) is a ratio
    of mean counts and is labelled as that.
    """
    n = P["n"]
    raw = P["raw_by_category"]
    full = P["model_full"]
    nov = P["model_noviews"]
    B = P["bootstrap"]
    G = P["groups"]
    lu = P["looked_up"]
    RT = P["record_types"]
    M = json.load(open(MODELS, encoding="utf-8"))["models"]
    MAN = json.load(open(MANIFEST, encoding="utf-8"))
    dr = lu["openalex_search_drift"]
    dcat = P["data_deficient"]["by_category"]
    g = {r["group"]: r for r in G["rows"]}
    read = [m for m in M if m["read"] == "full text"]
    cost, cost_n = openalex_cost()
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0
    drop = full["drop_r2"]
    rank = sorted(drop, key=lambda t: -drop[t])
    adj, adjf = nov["adjusted"], full["adjusted"]
    ratio = adj["CR"] / adj["LC"]
    sh = RT["shares"]
    allw = sum(sh[c]["works_typed"] for c in sh)
    share = {k: sum(sh[c][k] * sh[c]["works_typed"] for c in sh) / allw
             for k in ("research", "dataset", "reference")}
    fits = RT["fits"]
    x = lambda f: f["adjusted"]["CR"] / f["adjusted"]["LC"]          # noqa: E731
    cm = P["count_model"]["CR"]
    ts = P["type_sources"]
    fetched = P["types_fetched"]
    lc_matched_n = sum(1 for _ in open(LC_MATCHED, encoding="utf-8")) - 1
    dmy = lambda d: f"{d.day} {d:%B %Y}"                              # noqa: E731
    # The prose of "What else goes with being studied" names the order of
    # the terms in words. It is checked here so a refit that reorders them
    # stops the render instead of shipping a sentence the figure contradicts.
    if rank[:2] != ["views", "family"] or rank.index("category") < rank.index("range"):
        raise SystemExit(f"term order changed ({rank}); rewrite the template's terms paragraph")
    if not (adj["LC"] < adj["NT"] < adj["VU"] < adj["EN"] < adj["CR"]):
        raise SystemExit("adjusted means are not monotone; the template says the rise runs through every category")
    cmod = P["count_model"]
    if not (math.exp(cmod["CR"]["lo"]) < 1.2 and cmod["VU"]["coef"] < cmod["NT"]["coef"]):
        raise SystemExit("count model no longer 'only just distinguishable' with VU below NT; "
                         "rewrite that paragraph")
    pv = full["robust"]["attractiveness"]["p"]
    v = {
        "attr_p": f"{pv:.2f}" if pv >= 0.01 else "under 0.01",
        "n_avonet": fmt(n["avonet"]), "n_modelled": fmt(n["modelled"]),
        "n_attract": fmt(n["with_attractiveness"]), "n_article": fmt(n["with_article"]),
        "n_category": fmt(n["with_category"]),
        "n_dropped_dd": fmt(n["dropped_not_assessed_or_dd_ex"]),
        "n_no_article": fmt(n["avonet"] - n["with_article"]),
        "n_shared_views": fmt(n["views_shared_article"]),
        "n_shared_articles": fmt(n["shared_articles"]),
        "sens_article_cr": f"{P['sensitivity']['has_article']['cat_beta']['CR']:+.2f}",
        "red_list_version": P["red_list_version"], "redlist_source_word":
            "the Red List API" if P["redlist_source"] == "api" else "the 2022-1 categories in the Santangeli deposit",
        "n_boot": fmt(P["n_boot"]), "seed": P["seed"], "ref_year": P["reference_year"],
        "r2_full": f"{full['r2']:.2f}", "r2_noviews": f"{nov['r2']:.2f}",
        "types_fetched": " and ".join(dmy(dt.date.fromisoformat(d)) for d in fetched),
        # the hero: what the count was made of
        "share_research_all": pct(share["research"]), "share_dataset_all": pct(share["dataset"]),
        "share_reference_all": pct(share["reference"]),
        "share_other_all": f"{100 * (1 - share['research'] - share['dataset'] - share['reference']):.1f}",
        "n_famous_lc": str(int(round(RT["famous_lc"], -1))),
        "n_year_col": fmt(n["year_from_col"]),
        "n_read_word": WORDS[len(read)],
        "n_null_word": WORDS[sum(1 for m in read if m["verdict"] == "null")],
        "n_negative_word": WORDS[sum(1 for m in read if m["verdict"] == "negative")],
        "cr_tot_coef": f"{nov['beta']['cat_CR']:+.2f}",
        "types_cost_round": f"{cost:.0f}",
        "cr_mean_research": f"{sh['CR']['mean_research']:.0f}", "lc_mean_research": f"{sh['LC']['mean_research']:.0f}",
        "lc_typed_tot": f"{fits['works_typed']['adjusted']['LC']:.0f}",
        "cr_typed_tot": f"{fits['works_typed']['adjusted']['CR']:.0f}",
        "zero_all_pct": pct(RT["zero_research"]["all"]),
        "ds_cr_x": f"{x(fits['dataset']):.1f}", "ref_cr_x": f"{x(fits['reference']):.1f}",
        "old_cr_x": f"{x(fits['works_typed']):.1f}",
        "probe_n": str(ts["species_sampled"]), "probe_gbif_pct": pct(ts["gbif_share_of_datasets"]),
        "probe_ref_pct": pct(ts["iucn_bow_share_of_reference"]),
        # threat and research
        "lc_raw": f"{raw['LC']['typical']:.1f}", "cr_raw": f"{raw['CR']['typical']:.1f}",
        "lc_tot": f"{adj['LC']:.1f}", "cr_tot": f"{adj['CR']:.1f}", "nt_tot": f"{adj['NT']:.1f}",
        "vu_tot": f"{adj['VU']:.1f}", "en_tot": f"{adj['EN']:.1f}",
        "cr_tot_ci": f"{B['noviews_adj']['CR'][0]:.1f} to {B['noviews_adj']['CR'][1]:.1f}",
        "cr_tot_x": f"{ratio:.1f}", "cr_tot_x1": f"{ratio:.0f}" if ratio >= 3 else f"{ratio:.1f}",
        "cr_x_lo": f"{B['noviews_ratio']['CR'][0]:.1f}", "cr_x_hi": f"{B['noviews_ratio']['CR'][1]:.1f}",
        "ppml_x": f"{math.exp(cm['coef']):.1f}", "ppml_lo": f"{math.exp(cm['lo']):.1f}",
        "ppml_hi": f"{math.exp(cm['hi']):.1f}",
        "journal_cr_x": f"{P['sensitivity']['journal_only']['adjusted']['CR'] / P['sensitivity']['journal_only']['adjusted']['LC']:.1f}",
        "cr_dir_x": f"{adjf['CR'] / adjf['LC']:.1f}", "cr_dir_coef": f"{full['beta']['cat_CR']:+.2f}",
        "med_nt": pct(P["mediated_share"]["NT"]), "med_cr": pct(P["mediated_share"]["CR"]),
        # the terms
        "family_drop": f"{drop['family']:.3f}", "cat_drop": f"{drop['category']:.3f}",
        "cat_rank_word": ORDINAL[rank.index("category") + 1],
        "second_term_cap": P["term_labels"][rank[1]], "second_drop": f"{drop[rank[1]]:.3f}",
        "attr_drop": f"{drop['attractiveness']:.3f}", "views_drop": f"{drop['views']:.3f}",
        # the literature
        "n_read": str(len(read)),
        "n_null": str(sum(1 for m in read if m["verdict"] == "null")),
        "n_negative": str(sum(1 for m in read if m["verdict"] == "negative")),
        "n_assessed_word": WORDS[sum(1 for m in read if m["verdict"] == "assessed-positive")],
        # A threat term in a MODEL: not Adamo (no term) and not Ducatez &
        # Lefebvre 2014, a bivariate comparison (models.json adjusted=false).
        "n_threat_word": WORDS.get(sum(1 for m in M if m["verdict"] != "no threat term"
                                       and m["adjusted"]), "some"),
        "n_models_word": WORDS.get(len(M), str(len(M))).capitalize(),
        "models_rows": "".join(
            f"<tr><td>{m['label']}</td><td>{m['taxon']}, {fmt(m['n'])}</td>"
            f"<td>{m['verdict'].replace('-', ', ')}{'' if m['adjusted'] else ', unadjusted'}</td>"
            f"<td>{m['read']}</td></tr>"
            for m in M),
        # the classes
        "amph_share_thr": pct(g["Amphibians"]["share_threatened"]),
        "amph_share_works": pct(g["Amphibians"]["share_works"]),
        "amph_per": f"{g['Amphibians']['works_per_threatened']:.0f}",
        "birds_per": f"{g['Birds']['works_per_threatened']:.0f}",
        "amph_pct_thr": g["Amphibians"]["pct_threatened_best"],
        "eval_lo": f"{min(r['pct_evaluated'] for r in G['rows']):.0f}",
        "eval_hi": f"{max(r['pct_evaluated'] for r in G['rows']):.0f}",
        "works_years": G["works_years"],
        # looked up
        "esa_top10": lu["esa_top10_share"]["value"], "life_pct": lu["life_birds_mammals_budget"]["value"],
        "global_funded_pct": lu["global_threatened_ever_funded"]["value"],
        "global_lc_pct": lu["global_funds_to_least_concern"]["value"],
        "dd_mammals": lu["dd_mammals_predicted_threatened"]["value"],
        "dd_amph": lu["dd_amphibians_predicted_threatened"]["value"],
        "extinct_est": lu["extinct_since_1500_estimate"]["value"], "extinct_rl": lu["extinct_since_1500_red_list"]["value"],
        "drift_date": dmy(dt.date.fromisoformat(dr["observed"])),
        "drift_common": dr["common"], "drift_fulltext": fmt(dr["fulltext"]),
        "drift_filter": fmt(dr["title_abstract"]),
        "drift_ratio": f"{dr['fulltext'] / dr['title_abstract']:.1f}",
        # limits
        "dd_frame": fmt(P["data_deficient"]["frame"]),
        "dd_n": fmt(dcat["DD"]["n"]), "dd_median": f"{dcat['DD']['median']:.0f}",
        "lc_median": f"{dcat['LC']['median']:.0f}",
        "sel_dropped": fmt(P["selection"]["dropped"]),
        "sel_n_a": fmt(P["selection"]["A_no_rating_required"]["n"]),
        "sel_cr_a": f"{P['selection']['A_no_rating_required']['category']['CR']['coef']:+.2f}",
        "sel_cr_b": f"{P['selection']['B_modelled']['category']['CR']['coef']:+.2f}",
        # the code
        "types_cost": f"{cost:.2f}", "types_cost_n": fmt(cost_n),
        "types_days": fmt(max(1, int(-(-cost // OPENALEX_DAILY_USD)))), "zip_kb": fmt(zip_kb),
        "cat_sha_short": P["categories_sha256"][:16], "cat_rows": fmt(MAN["withheld"]["rows"]),
        "lc_matched_n": fmt(lc_matched_n),
    }
    v["meta_description"] = (
        f"Across {v['n_modelled']} bird species, only {v['share_research_all']}% of what a search of "
        f"OpenAlex returns for a bird's name is research. On research alone, a Critically Endangered "
        f"bird has about {v['cr_tot_x']} times the work of a Least Concern one, with family, size, "
        f"range, description date and rated attractiveness held equal.")
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "food.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    text = re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)
    return text


def image_dims(text):
    from PIL import Image

    def dims(m):
        src = m.group(1)
        w, h = Image.open(os.path.join(SITE, src)).size
        return f'src="assets/{src.split("/", 1)[1]}{m.group(2)}" loading="lazy" width="{w}" height="{h}"'
    text = re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"', dims, text)

    def sdims(m):
        w, h = Image.open(os.path.join(SITE, m.group(1))).size
        return f'srcset="{m.group(1)}{m.group(2)}" width="{w}" height="{h}"'
    return re.sub(r'srcset="(assets/[^"?]+)([^"]*)" width="[^"]*" height="[^"]*"', sdims, text)


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
