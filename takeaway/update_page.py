"""
Write site/takeaway.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from cited.py (parsed out of
a source's own words), or from a file this script measures (the archive's
size); the prose is in the template. The parts of the shipped page that
other scripts own - the nav (rebuild_nav.py), the citation markers and
Sources list (add_citations.py's table, applied here), the ?v= stamps
(bust_cache.py) and image dimensions - are kept as the shipped page has
them, so tests/test_generators.py can run this on the shipped tree and expect
no change. The idiom is meter/update_page.py's and beauty/update_page.py's.

claims() asserts every direction the template's words commit to. If a
rebuild moves one, the generator stops rather than ship prose the payload
contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "takeaway.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "takeaway-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import cited   # noqa: E402

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
WORDS = {12: "twelve", 6: "six", 3: "three"}
EXP_BY_YEAR = 2027      # "of it by the end of ..." - a reading point, not a forecast
NEAR_ZERO = 0.25        # Bcf/d: the alt text's "sits near zero"


def ym(key):
    y, m = key.split("-")
    return int(y), int(m)


def long(key):
    y, m = ym(key)
    return f"{MONTHS[m - 1]} {y}"


def short(key):
    y, m = ym(key)
    return f"{MONTHS[m - 1][:3]} {y}"


def f2(x):
    return f"{x:.2f}"


def signed(x):
    return f"{x:+.2f}".replace("-", "&minus;")


def month_list(keys):
    """'December 2025, July 2026 and August 2026', consecutive months in one year run together."""
    if not keys:
        return "none"
    parts, run = [], [keys[0]]
    for k in keys[1:]:
        (y0, m0), (y1, m1) = ym(run[-1]), ym(k)
        if y1 == y0 and m1 == m0 + 1:
            run.append(k)
        else:
            parts.append(run)
            run = [k]
    parts.append(run)

    def name(r):
        if len(r) == 1:
            return long(r[0])
        y = ym(r[0])[0]
        joint = " and " if len(r) == 2 else " to "
        return f"{MONTHS[ym(r[0])[1] - 1]}{joint}{MONTHS[ym(r[-1])[1] - 1]} {y}"
    names = [name(r) for r in parts]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def cap_rows(P):
    rows = []
    for e in P["entries"]:
        when = str(ym(e["month"])[0]) if e["year_only"] else short(e["month"])
        status = "In service" if e["status"] == "confirmed" else "Expected"
        if e["status"] == "confirmed" and e["disagrees"]:
            status += f" ({html.escape(e['disagrees'])})"
        name = html.escape(e["name"].replace(" (formerly Warrior Pipeline) Phase I & II", ""))
        rows.append(f'<tr><td>{name}</td><td class="n">{e["bcfd"]:.2f}</td><td>{when}</td>'
                    f'<td>{status}, per {html.escape(e["cite"])}</td></tr>')
    return "\n".join(rows)


def values(P):
    steo = P["steo"]["P"]
    last = P["steo"]["last_historical"]
    t0 = P["t0"]
    H = P["H"]
    lo, hi = P["H_band"]["k_lo"], P["H_band"]["k_hi"]
    k = P["k"]
    ent = P["entries"]
    conf = [e for e in ent if e["status"] == "confirmed"]
    exp = [e for e in ent if e["status"] == "expected"]
    mh = next(e for e in ent if e["name"] == "Matterhorn Express Pipeline")
    hb1 = next(e for e in ent if e["name"].endswith("Phase I & II Phase I"))
    cap = P["capacity"]
    cap_keys = sorted(cap)
    cap_t0 = sum(e["bcfd"] for e in conf if t0 < e["month"] <= last)
    dP = steo[last] - steo[t0]
    neg = [m for m in sorted(H) if H[m] < 0]
    neg_hi = [m for m in sorted(H) if min(lo[m], hi[m]) < 0]
    after_m = next(m for m in sorted(H) if m >= mh["month"])
    hmin = min(H, key=H.get)
    hpeak = max(H, key=H.get)
    fl = P["flaring"]
    share = fl["share"]
    vf_last = fl["last"]
    peak = max(share, key=share.get)
    c1, c2, c3 = [c for c in fl["clusters"] if "diff" in c][:3]
    names = {s["month"]: s["name"] for s in fl["starts"]}
    chk = fl["check"]
    exp_last = max(e["month"] for e in exp)
    eia_pct, eia_year = cited.eia_pct()
    rc = cited.reuters_counts()
    csgd = P["csgd"]
    v = {
        "last_short": short(last), "last_long": long(last), "t0_short": short(t0), "t0_long": long(t0),
        "P_last": f2(steo[last]), "P_anchor": f2(steo[P["anchor"]["month"]]),
        "cap_t0": f2(cap_t0), "dP_t0": f2(dP), "kdP_t0": f2(k["default"] * dP),
        "H_last": signed(H[last]), "H_after_m": signed(H[after_m]),
        "H_min": signed(H[hmin]), "H_min_month": long(hmin),
        "H_peak": signed(H[hpeak]), "H_peak_month": long(hpeak),
        "H_with_hb": signed(P["H_with_expected"][last]),
        "r_run": str(cited.reuters_run()),
        "band_max": f2(max(abs(lo[m] - hi[m]) for m in H)),
        "n_neg": str(len(neg)), "neg_months": month_list(neg), "n_neg_hi": str(len(neg_hi)),
        "k_def": f"{k['default']:.3f}", "k_year": str(k["year"]),
        "k_both_net": f"{k['by_state']['both']['net']:.3f}", "k_tx_net": f"{k['by_state']['TX']['net']:.3f}",
        "k_both_dry": f"{k['by_state']['both']['dry']:.3f}",
        "anchor_lo": f"{P['anchor']['lo']:g}", "anchor_hi": f"{P['anchor']['hi']:g}",
        "anchor_month": long(P["anchor"]["month"]), "anchor_width": f"{P['anchor']['hi'] - P['anchor']['lo']:g}",
        "n_conf": str(len(conf)), "conf_total": f2(sum(e["bcfd"] for e in conf)), "matterhorn": f"{mh['bcfd']:g}",
        "exp_total": f2(sum(e["bcfd"] for e in exp)), "exp_last": long(exp_last), "exp_last_year": str(ym(exp_last)[0]),
        "exp_by": f2(sum(e["bcfd"] for e in exp if ym(e["month"])[0] <= EXP_BY_YEAR)), "exp_by_year": str(EXP_BY_YEAR),
        # D-25 item 5: the expected total mixes lines being built with lines
        # not yet started; split it by the tracker's status.
        "exp_built": f2(sum(e["bcfd"] for e in exp if e["stage"] in BUILDING)),
        "exp_not": f2(sum(e["bcfd"] for e in exp if e["stage"] not in BUILDING)),
        "exp_not_names": and_list([short_name(e["name"]) for e in exp if e["stage"] not in BUILDING]),
        "event_min": f"{EVENT_MIN_BCFD:g}",
        "conf_lo_end": f2(cap[cap_keys[-1]]["lo_confirmed"]), "conf_hi_end": f2(cap[cap_keys[-1]]["hi_confirmed"]),
        "all_lo_end": f2(cap[cap_keys[-1]]["lo"]), "all_hi_end": f2(cap[cap_keys[-1]]["hi"]),
        "hb1": f"{hb1['bcfd']:g}",
        "pin_before": f2(P["pin"]["before"]), "pin_after": f2(P["pin"]["after"]),
        "fc_before": f2(100 * chk["before"]), "fc_after": f2(100 * chk["after"]),
        "fc_before_span": month_list(chk["before_months"]),
        "fc_after_span": month_list(chk["after_months"]),
        "c1_before": f2(100 * c1["before"]), "c1_after": f2(100 * c1["after"]), "c1_start": long(c1["first"]),
        "c2_before": f2(100 * c2["before"]), "c2_after": f2(100 * c2["after"]), "c2_year": str(ym(c2["first"])[0]),
        "c3_before": f2(100 * c3["before"]), "c3_after": f2(100 * c3["after"]),
        "c3_first_long": long(c3["first"]), "c3_last_long": long(c3["last"]),
        "c2_rank": str(c2["rank_below"]), "c3_rank": str(c3["rank_below"]),
        "pl_fall_year": str(fall_years(fl, c2)[0]),
        "c3_in_falling": str(sum(1 for m in c3["placebo_below"]
                                 if annual(share, ym(m)[0]) < annual(share, ym(m)[0] - 1))), "fc_diff": f2(100 * (chk["before"] - chk["after"])),
        "dbl_e": long(fl["double_e"]),
        "vf_extract": (lambda d: f"{d.day} {MONTHS[d.month - 1]} {d.year}")(
            __import__("datetime").datetime.strptime(fl["dump"]["gas_extract_date"], "%d-%b-%y")),
        "unsettled_word": WORDS[fl["unsettled_months"]],
        "placebo_n": str(fl["placebo_n"]),
        "pl_first": str(ym(fl["placebo_months"][0])[0]), "pl_last": str(ym(fl["placebo_months"][1])[0]), "window_word": WORDS[P["window"]],
        "vf_first_long": long(fl["first"]), "vf_last_long": long(vf_last), "vf_last_short": short(vf_last),
        "vf_peak": f2(100 * share[peak]), "vf_peak_month": long(peak), "vf_end": f2(100 * share[vf_last]),
        "csgd_year": str(csgd["year"]), "csgd_pct": f"{100 * csgd['share']:.0f}",
        "steo_release": P["steo"]["release"],
        "rec_n": str(P["reconcile"]["n"]), "rec_first": long(P["reconcile"]["first"]),
        "rec_last": long(P["reconcile"]["last"]), "rec_min": f"{P['reconcile']['min']:.2f}",
        "rec_max": f"{P['reconcile']['max']:.2f}", "rec_mean": f"{P['reconcile']['mean']:.2f}",
        "n_tx_counties": str(P["region"]["TX"]), "n_nm_counties": str(P["region"]["NM"]),
        "eia_pct": str(eia_pct), "eia_year": str(eia_year), "eia_t0_date": cited.EIA_T0["date"],
        "r_2024": str(rc[2024]), "r_2025": str(rc[2025]), "r_2026": str(rc[2026]), "r_date": cited.REUTERS["date"],
        "cap_rows": cap_rows(P),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    claims(P, H, lo, hi, mh, after_m, peak, c1, c2, chk, neg, conf)
    return v


def add(key, n):
    """'YYYY-MM' plus n months."""
    y, m = ym(key)
    i = y * 12 + m - 1 + n
    return f"{i // 12}-{i % 12 + 1:02d}"


def fall_years(fl, *groups):
    """The years of the placebo months whose fall exceeds any of these groups'."""
    return sorted({ym(m)[0] for c in groups for m in c["placebo_below"]})


# The tracker's statuses that mean a line is being built (D-25 item 5);
# "Applied", "Pre-applied" and "Approved" are not.
BUILDING = {"Construction", "Part Completed"}
# build_takeaway.EVENT_MIN_BCFD: an addition this size or larger counts as a
# start in the venting and flaring test (D-25 item 3). Imported so the page
# cannot state a threshold the build does not use.
from build_takeaway import EVENT_MIN_BCFD  # noqa: E402


def short_name(n):
    return n.replace(" Project", "").replace(" Pipeline", "").replace(" expansion project", "")


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def annual(share, y):
    v = [s for k, s in share.items() if ym(k)[0] == y]
    return sum(v) / len(v)


def claims(P, H, lo, hi, mh, after_m, peak, c1, c2, chk, neg, conf):
    c3 = [c for c in P["flaring"]["clusters"] if "diff" in c][2]
    names = {s["month"]: s["name"] for s in P["flaring"]["starts"]}
    near = [m for m in H if "2026-02" <= m <= "2026-05"]
    checks = [
        ("Matterhorn is the largest addition in service", mh["bcfd"] == max(e["bcfd"] for e in conf)),
        ("Matterhorn is in service", mh["status"] == "confirmed"),
        ("marketed production exceeded the anchor in its month",
         P["steo"]["P"][P["anchor"]["month"]] > P["anchor"]["hi"]),
        ("'production growth then ate it': headroom fell after Matterhorn",
         min(H[m] for m in H if m > after_m) < H[after_m]),
        ("'The path between was not steady': headroom went below zero at least once", len(neg) > 0),
        ("'less headroom than in' t0", H[P["steo"]["last_historical"]] < 0),
        ("the record counts no expected line", all(
            abs(H[m] - (sum(e["bcfd"] for e in conf if P["t0"] < e["month"] <= m)
                        - P["k"]["default"] * (P["steo"]["P"][m] - P["steo"]["P"][P["t0"]]))) < 1e-9 for m in H)),
        ("alt: near zero February to May 2026", near and all(abs(H[m]) < NEAR_ZERO for m in near)),
        ("'It was not': production did not grow faster after Matterhorn than before t0",
         P["pin"]["after"] <= P["pin"]["before"]),
        ("'They did': more venting and flaring before than after", chk["before"] > chk["after"]),
        ("every month of both PLAN 3.4 windows is in the series", not chk["missing"]),
        ("'fell after each of the three' tested groups", c1["diff"] < 0 and c2["diff"] < 0 and c3["diff"] < 0),
        ("'the 2019 fall is larger than every one' of the placebo differences", c1["rank_below"] == 0),
        ("'only the first stands out': placebo falls exceed the 2021 and Matterhorn groups'",
         c2["rank_below"] > 0 and c3["rank_below"] > 0),
        ("the third group runs from the Whistler expansion to Matterhorn",
         names[c3["starts"][0]].startswith("Whistler") and names[c3["starts"][-1]].startswith("Matterhorn")
         and c3["last"] == mh["month"]),
        ("'all come from' one year: the placebo falls beyond the 2021 group",
         len(fall_years(P["flaring"], c2)) == 1),
        ("'a year in which the share fell': its mean below the year before's",
         all(annual(P["flaring"]["share"], y) < annual(P["flaring"]["share"], y - 1)
             for y in fall_years(P["flaring"], c2))),
        ("Double E's completion falls inside the 2021 group's after-window",
         add(c2["last"], 1) <= P["flaring"]["double_e"] <= add(c2["last"], P["window"])),
        ("exactly three groups tested", len([c for c in P["flaring"]["clusters"] if "diff" in c]) == 3),
        ("the first tested start is Gulf Coast Express (2019)", c1["first"].startswith("2019")),
        ("the second tested group is 2021", c2["first"].startswith("2021")),
        ("alt: the venting and flaring peak comes before Gulf Coast Express", peak < c1["first"]),
        ("the placebo months lie before the first tested start", P["flaring"]["placebo_months"][1] < c1["first"]),
        ("'years when the share was rising': it ends the placebo span higher than it began",
         P["flaring"]["share"][P["flaring"]["placebo_months"][1]] > P["flaring"]["share"][P["flaring"]["placebo_months"][0]]),
        ("most gas in the three districts comes from oil wells", P["csgd"]["share"] > 0.5),
        ("the expected total splits into building and not yet building",
         abs(sum(e["bcfd"] for e in P["entries"] if e["status"] == "expected")
             - sum(e["bcfd"] for e in P["entries"] if e["status"] == "expected" and e["stage"] in BUILDING)
             - sum(e["bcfd"] for e in P["entries"] if e["status"] == "expected" and e["stage"] not in BUILDING)) < 1e-9),
        ("every expected line has a tracker status",
         all(e["stage"] for e in P["entries"] if e["status"] == "expected")),
    ]
    bad = [name for name, ok in checks if not ok]
    if bad:
        raise SystemExit("the payload contradicts the template: " + "; ".join(bad))


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "storage.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def image_dims(text):
    from PIL import Image

    def dims(m):
        attr, src, rest = m.group(1), m.group(2), m.group(3)
        w, h = Image.open(os.path.join(SITE, src)).size
        return f'{attr}="{src}{rest}" width="{w}" height="{h}"'
    text = re.sub(r'(srcset)="(assets/[^"?]+)([^"]*)" width="[^"]*" height="[^"]*"', dims, text)
    return re.sub(r'(src)="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"',
                  lambda m: dims(m).replace('" width', '" loading="lazy" width', 1), text)


def span(text):
    """The marginalia asides span the grid rows after them (beauty/update_page.py's rule)."""
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
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    t = keep_from_shipped(t, shipped)
    t = image_dims(t)
    t = t.replace("{{span}}", str(span(t)))
    return t


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("takeaway.html")
    if not refs:
        return text, ["takeaway.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
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
        old = open(PAGE, "rb").read().decode("utf-8")          # bytes: trap 32
        print("  takeaway.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  takeaway.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
