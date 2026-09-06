"""
Write site/continents.html from template.html and the payload.

Every number on the page comes from outputs/continents_payload.json; the
prose is in the template. The page that ships also carries things other
scripts own - the nav (rebuild_nav.py), the citation markers and Sources list
(add_citations.py), the ?v= cache stamps (bust_cache.py) and the image
dimensions (sync_img_dims.py) - so this script keeps each of those as the
shipped page has it, and the drift check (tests/test_generators.py) can run
it on the shipped tree and expect no change.

Tables are generated a whole tbody at a time, never a placeholder per cell.
Four tables at a cell each would be a couple of hundred placeholders and the
page-equals-payload check would then be comparing strings rather than tables.

Every list that reaches the page has an order written down in the payload or
in build_continents.py. Nothing here iterates a set or a directory.

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
PAGE = os.path.join(SITE, "continents.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "continents_payload.json")
sys.path.insert(0, ROOT)


def fmt(n):
    return f"{n:,}"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def band_rows(P):
    out = []
    for b in P["present"]["distance_bands"]:
        lo, hi = b["lo_km"], b["hi_km"]
        lab = (f"more than {fmt(lo)} km" if hi is None
               else f"{fmt(lo)} to {fmt(hi)} km")
        out.append(f"<tr><td>{lab}</td><td class=\"n\">{fmt(b['n'])}</td>"
                   f"<td class=\"n\">{b['median_mm_yr']:.2f} mm/yr</td>"
                   f"<td class=\"n\">{b['p90_mm_yr']:.2f}</td></tr>")
    return "\n".join(out)


def anchor_rows(P):
    out = []
    for a in P["anchors"]:
        out.append(f"<tr><td>{esc(a['what'])}</td>"
                   f"<td>{esc(str(a['threshold']))}</td>"
                   f"<td class=\"n\">{esc(str(a['measured']))}</td></tr>")
    return "\n".join(out)


def sydney_line(P):
    """The page's best fact, generated from the cache rather than recalled."""
    ages = P["past"]["ages"]
    models = P["past"]["models"]
    rows = {r["age"]: r for r in P["past"]["spread"]}
    best = None
    for age in sorted(ages, reverse=True):
        row = rows.get(age)
        if not row:
            continue
        for pl in row["places"]:
            if pl["place"] == "Sydney" and pl["no_crust"]:
                best = (age, pl, row["n_models_in_range"])
                break
        if best:
            break
    if not best:
        return ("Every model that reaches an age places crust under every "
                "place asked about, so the no-crust case does not arise in "
                "this set.")
    age, pl, in_range = best
    return (f"At {fmt(age)} million years, {in_range} of the "
            f"{len(models)} models still reach that far back, and "
            f"{pl['no_crust']} of those {in_range} place no crust under "
            f"Sydney at all. The disagreement there is not about where the "
            f"ground was. It is about whether it existed.")


def values(P):
    pres, fut, past = P["present"], P["future"], P["past"]
    bands = pres["distance_bands"]
    pa = pres["pacific"]
    g = {r["pair"]: r for r in P["geologic_vs_geodetic"]}
    ex = {r["site"]: r for r in P["extrapolation"]}
    anch = {a["id"]: a for a in P["anchors"]}
    br = P["b1_break"]
    plates = {r["plate"]: r for r in pres["plates"]}
    ilsg = next((r for r in pres["excluded"] if r["sta"] == "ILSG"), None)

    # the first age at which any pair of futures differs by more than 5 %
    agree_until = 0
    for d in fut["disagreement"]:
        if d["max"] <= 5.0:
            agree_until = d["age"]
        else:
            break
    future_max = max(d["max"] for d in fut["disagreement"])

    sp = [r for r in past["spread"] if r["max_km"] is not None]
    near = min(sp, key=lambda r: r["age"] if r["age"] > 0 else 1e9)
    far = max(sp, key=lambda r: r["age"])
    hawaii_max = max((r["residual_mm_yr"] for r in pres["excluded"]
                      if r["plate"] == "PA" and 18.8 <= r["lat"] <= 20.4
                      and -156.2 <= r["lon"] <= -154.7), default=0)
    oldest = max(m["oldest_ma"] for m in past["models"])
    last_age = max(a for a in past["ages"])

    return {
        "n_all": fmt(pres["n_all"]),
        "n_after_cuts": fmt(pres["n_after_cuts"]),
        "n_with_plate": fmt(pres["n_with_plate"]),
        "n_plates": pres["n_plates_fitted"],
        "n_plotted": fmt(pres["n_plotted"]),
        "n_na": fmt(plates["NA"]["n_far"]),
        "n_af": fmt(plates["AF"]["n_far"]),
        "denver_speed": f"{ex['Denver']['speed_mm_yr']:.0f}",
        "band_far": f"{bands[4]['median_mm_yr']:.2f}",
        "band_near": f"{bands[0]['median_mm_yr']:.1f}",
        "near_km": fmt(bands[0]["hi_km"]),
        "far_km": fmt(int(P["cuts"]["far_km"])),
        "min_years": f"{P['cuts']['min_years']:.0f}",
        "max_sigma": f"{P['cuts']['max_sigma_mm_yr']:.1f}",
        "mad_k": f"{P['cuts']['mad_k']:.0f}",
        "polar_cut": f"{P['cuts']['polar_cut_deg']:.0f}",
        "big_island_n": pres["big_island_excluded"],
        "hawaii_max": f"{hawaii_max:.0f}",
        "ilsg_resid": f"{ilsg['residual_mm_yr']:.0f}" if ilsg else "n/a",
        "pa_before_n": pa["before"]["n"],
        "pa_before_rms": f"{pa['before']['rms_mm_yr']:.1f}",
        "pa_before_itrf": f"{pa['before']['itrf_diff_mm_yr']:.1f} mm/yr",
        "pa_after_rms": f"{pa['after']['rms_mm_yr']:.2f}",
        "pa_dropped": pa["before"]["n"] - pa["after"]["n"],
        "band_rows": band_rows(P),
        "anchor_rows": anchor_rows(P),
        "n_gates": len(P["anchors"]),
        "n_probes": 12,
        "morvel_interval": "0.78 to 3.16",
        "morvel_interval_detail": ("0.78 million years for ten spreading "
                                   "centres, 3.16 for seven, and decades for "
                                   "the five or six plates it carries on GPS"),
        "ie_morvel": f"{g['IN-EU']['morvel']:.1f}",
        "ie_itrf": f"{g['IN-EU']['itrf']:.1f}",
        "ie_gap": f"{abs(g['IN-EU']['speed_change_mm_yr']):.1f}",
        "ar_gap": f"{abs(g['AR-EU']['speed_change_mm_yr']):.1f}",
        "nz_gap": f"{abs(g['NZ-SA']['speed_change_mm_yr']):.1f}",
        "n_slower": sum(1 for r in P["geologic_vs_geodetic"]
                        if (r.get("speed_change_mm_yr") or 0) <= -5),
        "sped_up": next(r["boundary"] for r in P["geologic_vs_geodetic"]
                        if (r.get("speed_change_mm_yr") or 0) > 0),
        "sped_up_by": f"{max(r['speed_change_mm_yr'] for r in P['geologic_vs_geodetic'] if r.get('speed_change_mm_yr') is not None):.1f}",
        "n_models": len(past["models"]),
        "n_models_500": sum(1 for m in past["models"]
                            if m["oldest_ma"] >= last_age),
        "n_places": len(past["places"]),
        "age_step": past["ages"][1] - past["ages"][0],
        "past_oldest": fmt(last_age),
        "past_near_age": fmt(near["age"]),
        "past_far_age": fmt(far["age"]),
        "past_far_km": fmt(int(far["max_km"])),
        "sydney_line": sydney_line(P),
        "common_age": fmt(fut["common_age"]),
        "agree_until": agree_until,
        "future_max": f"{future_max:.0f}",
        "land_today": f"{[r for r in fut['land_distribution'] if r['scenario'] == 'today'][0]['land_pct']:.0f}",
        "naive_pct": f"{fut['naive_max_disagreement_pct']:.0f}",
        "t0_pct": f"{fut['t0_agreement_pct']:.1f}",
        "antipodal": fmt(int(P["antipodal_km"])),
        "break_deg": f"{br['movable_deg_myr']:.3f}",
        "break_pct": f"{br['share_of_rate_pct']:.0f}",
        "b1c_tol": f"{br['station_check_mm_yr']:.1f}",
        "stations_mb": f"{os.path.getsize(os.path.join(HERE, 'data', 'stations.csv')) / 1048576:.1f} MB",
        "masks_kb": f"{os.path.getsize(os.path.join(HERE, 'data', 'future_masks.npz')) / 1024:.0f} KB",
        "land_mb": f"{os.path.getsize(os.path.join(HERE, 'data', 'land.json')) / 1048576:.1f} MB",
    }


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "food.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"',
                                 shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return (f'{m.group(1)}="{path}?v={stamps[path]}"'
                if path in stamps else m.group(0))
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def image_dims(text):
    from PIL import Image

    def dims(m):
        src = m.group(1)
        w, h = Image.open(os.path.join(SITE, src)).size
        return (f'src="assets/{src.split("/", 1)[1]}{m.group(2)}" '
                f'loading="lazy" width="{w}" height="{h}"')
    return re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" '
                  r'width="[^"]*" height="[^"]*"', dims, text)


def span(text):
    """The marginalia asides span the grid rows that follow them: the count
    of top-level elements in <main> after the asides, plus one."""
    main = text[text.index("<main"):text.index("</main>")]
    body = re.sub(r"<aside.*?</aside>", "", main, flags=re.S)
    body = body[body.index(">") + 1:]
    depth, n = 0, 0
    for m in re.finditer(r"<(/?)(\w+)[^>]*?>", body):
        close, tag = m.group(1), m.group(2)
        if tag in ("img", "br", "hr", "meta", "link", "input", "source"):
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        print(f"  values with no placeholder: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = (open(PAGE, encoding="utf-8").read()
               if os.path.exists(PAGE) else None)
    t = keep_from_shipped(t, shipped)
    t = image_dims(t)
    return t.replace("{{span}}", str(span(t)))


def cite(text):
    """Citation markers and the Sources list, from add_citations.py's table
    for this page, applied to the rendered text so a re-run reproduces the
    shipped page exactly."""
    import add_citations
    refs = add_citations.PAGES.get("continents.html")
    if not refs:
        return text, ["continents.html has no entry in add_citations.PAGES"]
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
        print("  continents.html: " + ("unchanged" if old == t else
                                       "would change" if not apply
                                       else "rewritten"))
    else:
        print("  continents.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
