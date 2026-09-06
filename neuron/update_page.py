"""
Write site/neuron.html from template.html and outputs/neuron_payload.json.

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
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "neuron.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "neuron_payload.json")
ZIP = os.path.join(SITE, "downloads", "neuron-code.zip")
sys.path.insert(0, ROOT)


def fmt(n):
    return f"{n:,}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}"


def um(v):
    """A length the way the page says it: mm past a millimetre, else um."""
    if v >= 1000:
        return f"{v / 1000:.1f} mm"
    if v >= 1:
        return f"{v:.0f} &micro;m"
    return f"{v:.2f} &micro;m"


def values(P):
    c, k, g, l = P["cascade"], P["the_complete"], P["gradient"], P["ladder"]
    tm, tf = P["tradeoff_metadata"], P["tradeoff_files"]
    un = P["units"]
    steps = {s["key"]: s for s in c["steps"]}
    alone = {a["key"]: a for a in c["alone"]}
    pair = P["pair"]
    al, ml = pair.get("allen", {}), pair.get("mouselight", {})
    lu = P["looked_up"]

    v = {
        "retrieved": P["retrieved"],
        "n_total": fmt(c["n_total"]),
        # the cascade
        "n_parts": fmt(steps["parts"]["n"]),
        "pc_parts": pct(steps["parts"]["share"], 1),
        "n_diam_alone": fmt(alone["diameter"]["n"]),
        "pc_nodiam": pct(1 - alone["diameter"]["share"], 1),
        "pc_2d": pct(1 - alone["three_d"]["share"], 1),
        "n_shrink_alone": fmt(alone["shrinkage"]["n"]),
        "pc_shrink": pct(alone["shrinkage"]["share"], 1),
        "n_axoncomplete": fmt(alone["axon_complete"]["n"]),
        "n_after_diam": fmt(steps["diameter"]["n"]),
        "n_after_3d": fmt(steps["three_d"]["n"]),
        "n_after_axon": fmt(steps["axon_complete"]["n"]),
        "n_complete": fmt(c["n_complete"]),
        "pc_complete": f'{100 * c["n_complete"] / c["n_total"]:.2f}',
        # the trade-off, from metadata and from files
        "n_ac": fmt(tm["axon_complete"]),
        "n_ac_measured": fmt(tm["and_measured_diameter"]),
        "pc_ac_measured": pct(tm["share"], 1),
        "wb_n": fmt(tf["whole_brain"]["n"]),
        "wb_reach": um(tf["whole_brain"]["reach_median_um"]),
        "wb_distinct": fmt(tf["whole_brain"]["distinct_diam_median"]),
        "sl_n": fmt(tf["slice"]["n"]),
        "sl_reach": um(tf["slice"]["reach_median_um"]),
        "sl_distinct": fmt(tf["slice"]["distinct_diam_median"]),
        # the complete set
        "n_labs": str(k["n_labs"]),
        "top_doi": k["top_doi"],
        "top_doi_n": str(k["top_doi_n"]),
        "top_doi_pc": pct(k["top_doi_share"], 0),
        "complete_species": ", ".join("%s %s" % (fmt(s["n"]), s["species"])
                                      for s in k["species"]),
        "complete_top_region": k["regions"][0]["region"] if k["regions"] else "",
        "complete_top_region_n": str(k["regions"][0]["n"]) if k["regions"] else "",
        # the span
        "span_extent": um(l["extent_um"]),
        "span_thinnest": um(l["thinnest_um"]),
        "span_range": fmt(l["dynamic_range"]),
        "span_orders": f'{l["orders"]:.1f}',
        "span_px": f'{l["px_at_1000"]:.3f}',
        "span_px_needed": fmt(l["px_for_one_px_neurite"]),
        # the pair
        "allen_archive": al.get("archive", ""),
        "allen_axon": um(al.get("axon_um", 0)),
        "allen_dend": um(al.get("dend_um", 0)),
        "allen_reach": um(al.get("reach_um", 0)),
        "allen_distinct": fmt(al.get("n_distinct_diam", 0)),
        "ml_archive": ml.get("archive", ""),
        "ml_axon": um(ml.get("axon_um", 0)),
        "ml_dend": um(ml.get("dend_um", 0)),
        "ml_reach": um(ml.get("reach_um", 0)),
        "ml_distinct": fmt(ml.get("n_distinct_diam", 0)),
        # the gradient
        "grad_verdict": g["verdict"],
        "grad_pooled": f'{g["pooled_rho"]:.2f}',
        "grad_within": f'{g["median_within_rho"]:.2f}' if g["median_within_rho"] is not None else "n/a",
        "grad_archives": str(g["n_qualifying_archives"]),
        "grad_all_archives": str(g["n_archives"]),
        "grad_cells": fmt(g["n_cells"]),
        "grad_rho_rule": f'{g["rule"]["rho_threshold"]:.2f}',
        "grad_share_rule": pct(g["rule"]["share_threshold"], 0),
        "grad_min_cells": str(g["rule"]["min_cells"]),
        "grad_spread": f'{g["rule"]["min_reach_spread"]:.0f}',
        # units
        "units_ok": str(un["n_micrometres"]),
        "units_total": str(un["n_archives"]),
        "units_rejected_n": str(un["n_rejected"]),
        "units_rejected": " and ".join(un["rejected"]),
        "units_kept": fmt(un["n_cells_kept"]),
        "units_dropped": fmt(un["n_cells_dropped"]),
        "units_worst": fmt(int(max(u["max_reach_um"] for u in un["per_archive"]
                                   if not u["micrometres"]))),
        "units_soma_min": "%.0f" % un["rule"]["soma_min_um"],
        "units_soma_max": "%.0f" % un["rule"]["soma_max_um"],
        # sample
        "sample_n": fmt(P["sample"]["n"]),
        "sample_archives": str(len(P["sample"]["archives"])),
        # looked-up values quoted in prose
        "truncation": lu["axon_truncation"]["value"],
        "zshrink": "63 &plusmn; 10%",
        "spine_f": "1.78 to 2.39",
        "katz_min": "0.4 to 0.5 ms",
        "katz_modal": "about 0.75 ms",
        "diam_pipelines": "1.80 &plusmn; 0.15 &micro;m against 0.91 &plusmn; 0.09 &micro;m",
        "iou": "0.470 &plusmn; 0.071",
        "zipsize": zipsize(),
    }
    return v


def zipsize():
    if not os.path.exists(ZIP):
        return "&mdash;"
    kb = os.path.getsize(ZIP) / 1024
    return f"{kb / 1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"


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
    return re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"',
                  dims, text)


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
    refs = add_citations.PAGES.get("neuron.html")
    if not refs:
        return text, ["neuron.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8").write(text)
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
        print("  neuron.html: " + ("unchanged" if old == t
                                   else "would change" if not apply else "rewritten"))
    else:
        print("  neuron.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
