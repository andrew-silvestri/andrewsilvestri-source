"""
Write site/economy.html from template.html and outputs/economy_payload.json.

Every number on the page comes from the payload; the prose is in the template.
The page that ships also carries things other scripts own - the nav
(rebuild_nav.py), the citation markers and Sources list (add_citations.py), the
?v= cache stamps (bust_cache.py) and the image dimensions (sync_img_dims.py) -
so this script keeps each of those as the shipped page has it, and the drift
check (tests/test_generators.py) can run it on the shipped tree and expect no
change.

Run:  python3 update_page.py            report only
      python3 update_page.py --apply
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "economy.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "economy_payload.json")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import model as M                                              # noqa: E402


def hm(seconds):
    s = int(round(seconds))
    return f"{s // 3600}:{(s % 3600) // 60:02d}"


def pace_row(P, v):
    return next(r for r in P["paces"]["rows"] if abs(r["v_ms"] - v) < 1e-9)


def values(P):
    E, T = P["elasticity"], P["transfer"]
    key = f"{P['paces']['headline_saving']:.2f}"
    L, Z = P["lanferdini"], P["looked_up"]["zanini_2025"]["value"]
    S = P["looked_up"]["smyth_2020"]["value"]
    H = M.HOOGKAMER_2016
    shoe = P["looked_up"]["footwear_spread"]["value"]
    ref = P["reference_runner"]
    comp = P["compounding"]["value"]
    three = next(c for c in comp if abs(c["p"] - 0.03) < 1e-9)

    rows = []
    for c in comp:
        rows.append(
            f'<tr><td>{100 * c["p"]:.0f}%</td>'
            f'<td class="n">{100 * c["product"]:.2f}%</td>'
            f'<td class="n">{100 * c["sum"]:.0f}%</td>'
            f'<td class="n">{c["gap_s"]:.0f} s</td></tr>')

    v = {}
    for tag, speed in (("260", 2.60), ("400", 4.00), ("572", 5.72)):
        r = pace_row(P, speed)
        v[f"gain_{tag}_pct"] = f'{r["gain"][key]["speed_pct"]:.1f}'
        v[f"saved_{tag}"] = M.ms(r["gain"][key]["saved_s"])
        v[f"pace_{tag}_hm"] = hm(r["marathon_s"])
        v[f"drag_{tag}_pct"] = f'{100 * r["drag_share"]:.1f}'

    v.update({
        "headline_pct": f'{100 * P["paces"]["headline_saving"]:.0f}',
        "crossing_ms": f'{E["crossing_ms"]:.2f}',
        "crossing_hm": hm(E["crossing_marathon_s"]),
        "n_curves": len(E["curves"]),
        "transfer_measured": f'{T["measured"]["value"]:.2f}',
        "transfer_modelled": f'{T["modelled"]["value"]:.2f}',
        # three decimals: the two routes differ by 0.003, and .2f rendered
        # that as "0.00", which reads as a claim of exact equality
        "transfer_gap": f'{T["difference"]:.3f}',
        "hoogkamer_n": H["n"],
        "hoogkamer_mass": 100,
        "hoogkamer_metabolic": f'{H["metabolic_pct"]:.2f}',
        "hoogkamer_time": f'{H["time_pct"]:.2f}',
        "lan_n": L["n"],
        "r_ceiling": f'{L["correlations"]["ceiling"]["r"]:+.2f}',
        "r_fraction": f'{L["correlations"]["fraction"]["r"]:+.2f}',
        "r_economy": f'{L["correlations"]["economy"]["r"]:+.2f}',
        "r_product": f'{L["correlations"]["product_max"]["r"]:+.2f}',
        "comp_3_product": f'{100 * three["product"]:.2f}',
        "comp_3_sum": f'{100 * three["sum"]:.0f}',
        "comp_3_gap_s": f'{three["gap_s"]:.0f}',
        "compounding_rows": "\n".join(rows),
        "zanini_n": Z["n"],
        "zanini_econ_120": f'{Z["economy_worse_pct_at_120min"]:.1f}',
        "zanini_peak_120": f'{Z["vo2peak_fall_pct"][1]:.1f}',
        "zanini_thr_0": f'{Z["threshold_speed_kmh"][0]:.1f}',
        "zanini_thr_120": f'{Z["threshold_speed_kmh"][2]:.1f}',
        "vic_n_all": "2,303",
        "vic_n": f'{P["vickers"]["n_both"]:,}',
        "vic_ratio": f'{100 * P["vickers"]["ratio"]["median"]:.1f}',
        "vic_slow": f'{100 * P["vickers"]["terciles"][0]["median_ratio"]:.1f}',
        "vic_fast": f'{100 * P["vickers"]["terciles"][2]["median_ratio"]:.1f}',
        "smyth_150": f'{100 * S["at_150_min"]:.0f}',
        "smyth_360": f'{100 * S["at_360_min"]:.0f}',
        "shoe_min": f'{shoe["min_pct"]:.2f}',
        "shoe_max": f'{shoe["max_pct"]:.2f}',
        "shoe_ind_min": f'{shoe["individual_min_pct"]:+.1f}',
        "shoe_ind_max": f'{shoe["individual_max_pct"]:+.1f}',
        "ref_mass": ref["mass_kg"],
        "ref_height": f'{ref["height_m"]:.2f}',
        "ref_area": f'{ref["frontal_area_m2"]:.2f}',
        "coyle_lo": P["looked_up"]["coyle_1995"]["value"]
                     ["ceiling_explains_threshold_variance_pct"][0],
        "coyle_hi": P["looked_up"]["coyle_1995"]["value"]
                     ["ceiling_explains_threshold_variance_pct"][1],
        "paper_tol": "0.02",
        "paper_worst": f'{max(abs(c["diff_pp"]) for c in P["paper_check"]["value"]):.3f}',
    })
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
        return (f'src="assets/{src.split("/", 1)[1]}{m.group(2)}" loading="lazy" '
                f'width="{w}" height="{h}"')
    return re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" '
                  r'height="[^"]*"', dims, text)


def span(text):
    """The marginalia aside spans the grid rows that follow it: the count of
    top-level elements in <main> after the asides, plus one."""
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
    """Citation markers and the Sources list, from add_citations.py's table for
    this page, applied to the rendered text so a re-run reproduces the shipped
    page exactly."""
    import add_citations
    refs = add_citations.PAGES.get("economy.html")
    if not refs:
        return text, ["economy.html has no entry in add_citations.PAGES"]
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
        print("  economy.html: " + ("unchanged" if old == t
                                    else "would change" if not apply else "rewritten"))
    else:
        print("  economy.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
