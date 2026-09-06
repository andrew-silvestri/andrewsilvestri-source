"""
Write site/food.html from template.html and outputs/food_payload.json.

Every number on the page comes from the payload; the prose is in the
template. The page that ships also carries things other scripts own - the
nav (rebuild_nav.py), the citation markers and Sources list
(add_citations.py), the ?v= cache stamps (bust_cache.py) and the image
dimensions (sync_img_dims.py) - so this script keeps each of those as the
shipped page has it, and the drift check (tests/test_generators.py) can run
it on the shipped tree and expect no change.

Run:  python3 update_page.py            report only
      python3 update_page.py --apply
"""

import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "food.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "food_payload.json")
ITEMS = os.path.join(HERE, "outputs", "items.csv")
ZIP = os.path.join(SITE, "downloads", "food-code.zip")
sys.path.insert(0, ROOT)


def fmt(n):
    return f"{n:,}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}"


def join(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def values(P):
    n, o, m = P["n"], P["observed"], P["marginals"]
    nl = P["null_permutation"]
    lu = P["looked_up"]
    R = P["rules"]
    items = list(csv.DictReader(open(ITEMS, encoding="utf-8")))
    raw_beef = sum(1 for r in items if r["cls"] == "raw" and r["group"] == "Beef Products"
                   and float(r["kcal"]) >= P["kcal_floor"])
    groups = {g["group"]: g for g in P["groups"]}
    top = P["groups"][0]
    ts = {t["year"]: t for t in lu["time_series"]["value"]}
    fn = lu["fndds_2015_16"]["value"]
    dv = lu["derivation"]["value"]
    pairs = P["pairs"]
    moved = [p for p in pairs if not p["raw_HPF"] and p["prep_HPF"]]
    cooked = [p for p in pairs if p["prep"].startswith("cooked") and p not in moved]
    raw_fs = o["raw"]["FS"]
    null_raw = nl["raw"]["FS"]
    ratio = null_raw["mean"] / raw_fs if raw_fs else float("inf")
    exc = P["raw_hpf_items"]
    by_rule = {}
    for e in exc:
        by_rule.setdefault(e["rules"][0], []).append(e["name"].replace(", raw", "").replace("seaweed, ", ""))
    rule_words = {"FS": "on fat and sugar", "FSOD": "on fat and sodium", "CSOD": "on starch and sodium"}
    raw_exceptions = "; ".join(f"{join(v)} {rule_words[k]}" for k, v in by_rule.items())
    mass5_names = P["null_mass"]["raw_named"]["5"]
    fs_names = [e["name"].replace(", raw", "") for e in exc if e["above_floor"] and "FS" in e["rules"]]
    kinds = []
    for r in items:
        if r["cls"] == "raw" and float(r["kcal"]) >= P["kcal_floor"]                 and float(r["sodium_pct_wt"]) >= R["FSOD"]["sodium_pct_wt"]:
            head = r["description"].split(",")[0].lower()
            k = {"fish": "fish", "crustaceans": "shellfish", "mollusks": "shellfish",
                 "seaweed": "seaweed"}.get(head, head)
            if k not in kinds:
                kinds.append(k)
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0
    return {
        "n_raw": fmt(n["raw"]), "n_prepared": fmt(n["prepared"]),
        "n_raw_all": fmt(n["raw_all"]), "n_prepared_all": fmt(n["prepared_all"]),
        "n_loaded": fmt(n["loaded"] - n["dropped"]), "n_other": fmt(n["other"]),
        "n_excluded": fmt(n["excluded_from_raw"]), "n_fibre_missing": fmt(n["fibre_missing"]),
        "n_with_salt": fmt(n["with_salt_left_out"]),
        "raw_fs": fmt(raw_fs), "prep_fs": fmt(o["prepared"]["FS"]),
        "raw_fs_verb": "sits" if raw_fs == 1 else "sit", "raw_fs_word": "food" if raw_fs == 1 else "foods",
        "raw_fs_names": join(fs_names) or "none", "raw_salty_kinds": join(kinds) or "none",
        "prep_hpf_pct": pct(o["prepared"]["HPF"] / n["prepared"]),
        "raw_fat20_pct": pct(m["raw"]["fat_gt20"]), "raw_sugar20_pct": pct(m["raw"]["sugar_gt20"]),
        "prep_fat20_pct": pct(m["prepared"]["fat_gt20"]), "prep_sugar20_pct": pct(m["prepared"]["sugar_gt20"]),
        "raw_na30_pct": pct(m["raw"]["sodium_ge030"], 1), "prep_na30_pct": pct(m["prepared"]["sodium_ge030"]),
        "raw_indep_expected": fmt(round(m["raw"]["fat_gt20"] * m["raw"]["sugar_gt20"] * n["raw"])),
        "null_raw_mean": f"{null_raw['mean']:.0f}", "null_raw_min": fmt(null_raw["min"]),
        "null_raw_max": fmt(null_raw["max"]),
        "null_prep_mean": f"{nl['prepared']['FS']['mean']:.0f}",
        "null_prep_min": fmt(nl["prepared"]["FS"]["min"]), "null_prep_max": fmt(nl["prepared"]["FS"]["max"]),
        "null_ratio": f"{ratio:.0f}" if ratio != float("inf") else "many",
        "simplex_pct": pct(P["null_simplex_share"], 1),
        "mass10_raw": fmt(P["null_mass"]["counts"]["10"]["raw"]),
        "mass10_prep": fmt(P["null_mass"]["counts"]["10"]["prepared"]),
        "mass10_prep_pct": pct(P["null_mass"]["counts"]["10"]["prepared"] / n["prepared"]),
        "mass5_raw_names": join(mass5_names),
        "n_pairs": fmt(len(pairs)), "n_pairs_cooked": fmt(len(cooked)), "n_pairs_moved": fmt(len(moved)),
        "n_raw_hpf_all": fmt(len(exc)), "raw_exceptions": raw_exceptions,
        "raw_beef": fmt(raw_beef),
        "group_top_name": top["group"].replace(" Products", "").capitalize() if top["group"] != "Fast Foods" else "Fast foods",
        "group_top_pct": pct(top["share_hpf"]),
        "group_sweets_pct": pct(groups["Sweets"]["share_hpf"]),
        "group_beef_pct": pct(groups["Beef Products"]["share_hpf"]),
        "fs_fat": R["FS"]["fat_pct_kcal"], "fs_sugar": R["FS"]["sugar_pct_kcal"],
        "fsod_fat": R["FSOD"]["fat_pct_kcal"], "fsod_na": f"{R['FSOD']['sodium_pct_wt']:.2f}",
        "csod_carb": R["CSOD"]["carb_pct_kcal"], "csod_na": f"{R['CSOD']['sodium_pct_wt']:.2f}",
        "fndds_items": fmt(fn["items_analysed"]), "fndds_pct": pct(fn["share_hpf"]),
        "fndds_rawveg_pct": pct(fn["raw_vegetables_not_captured"]),
        "fndds_reduced": fmt(fn["reduced_items"]), "fndds_reduced_pct": pct(fn["reduced_share_hpf"]),
        "deriv_papers": dv["papers"], "deriv_foods": dv["foods"], "deriv_quote": dv["quote"],
        "ts_1988_items": fmt(ts[1988]["items"]), "ts_1988_pct": pct(ts[1988]["share_hpf"]),
        "ts_2001_items": fmt(ts[2001]["items"]), "ts_2001_pct": pct(ts[2001]["share_hpf"]),
        "ts_2018_items": fmt(ts[2018]["items"]), "ts_2018_pct": pct(ts[2018]["share_hpf"]),
        "reform_odds": lu["time_series"]["reformulation_odds_2018"],
        "shelf_pct": pct(lu["shelf_share"]["value"], 1), "purchase_pct": pct(lu["shelf_share"]["purchases_share"], 1),
        "kcal_floor": P["kcal_floor"], "seed": P["seed"], "n_perm": fmt(P["n_perm"]),
        "n_simplex": fmt(P["n_simplex"]), "zip_kb": fmt(zip_kb),
    }


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "heat.html"), encoding="utf-8").read()
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
    refs = add_citations.PAGES.get("food.html")
    if not refs:
        return text, ["food.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
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
        print("  food.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  food.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
