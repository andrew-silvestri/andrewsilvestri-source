"""
Write site/skyline.html from page.html, data/skylines.json and
data/filter_report.json (build_skylines.py).

Every number on the page comes from the payload, the filter report, the
archived Wikidata pull (one demolition year), build_skylines.py's constants
or a file this script measures (the archive's size); the prose is in
page.html. The nav (rebuild_nav.py) and the ?v= stamps (bust_cache.py) are
kept as the shipped page has them, so tests/test_generators.py can run this
on the shipped tree and expect no change. The idiom is heat/update_page.py's.

claims() asserts what the template's words say about the data ("about one in
twenty", the funnel adding up, "about ten decibels", the examples it names);
if a fresh pull moves one, the generator stops rather than ship prose the
data contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "skyline.html")
TEMPLATE = os.path.join(HERE, "page.html")
PAYLOAD = os.path.join(HERE, "data", "skylines.json")
REPORT = os.path.join(HERE, "data", "filter_report.json")
ZIP = os.path.join(SITE, "downloads", "skyline-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import build_skylines as B      # noqa: E402
import fetch_osm                # noqa: E402
import fetch_wikidata           # noqa: E402

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten"}
GONE = ("destroyed", "demolished", "demolition", "former", "end date")


def day(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def tally(R):
    t = {}
    for v in R.values():
        for k, n in v["count"].items():
            t[k] = t.get(k, 0) + n
    gone = unbuilt = 0
    for v in R.values():
        for _, _, why in v["dropped"]:
            if why in ("tower structure", "outside city", "not in OSM") or \
                    why.startswith(("duplicate", "height")):
                continue
            if any(g in why for g in GONE):
                gone += 1
            else:
                unbuilt += 1
    t["gone"], t["unbuilt"] = gone, unbuilt
    t["cand"] = (t["not standing (Wikidata)"] + t["not in OSM"] +
                 t["duplicate"] + t["kept"])
    return t


def park_year():
    wd = json.load(open(B.latest("wikidata_*.json"), encoding="utf-8"))
    ys = {f["dem"]["value"][:4] for f in wd["cities"]["New York"]["facts"]
          if f.get("bLabel", {}).get("value") == "270 Park Avenue"
          and "dem" in f}
    if len(ys) != 1:
        raise SystemExit(f"270 Park Avenue demolition years: {ys}")
    return ys.pop()


VOICE = {  # app.js VOICING, in words; test: every mode on the page is here
    "major": ("root, third, fifth", "the same"),
    "minor": ("root, minor third, fifth", "the same"),
    "hijaz": ("root, third, fifth", "flattened second, third, fifth"),
    "pent_major": ("root, third, sixth", "the same"),
    "yo": ("root, fourth, sixth", "the same"),
    "pent_minor": ("root, minor third, fifth, flattened seventh",
                   "minor third, fifth, flattened seventh"),
    "blues": ("root, minor third, fifth, flattened seventh",
              "minor third, flattened fifth, flattened seventh"),
    "insen": ("root, fourth, flattened seventh",
              "flattened second, fourth, flattened seventh"),
}
MODE_NAME = {"pent_major": "pentatonic major", "pent_minor": "pentatonic minor"}


def claims(P, R, T, v):
    bad = []
    share = T["not standing (Wikidata)"] / T["cand"]
    if not 0.04 <= share <= 0.06:
        bad.append(f"'about one in twenty' is {share:.3f}")
    if T["gone"] + T["unbuilt"] != T["not standing (Wikidata)"]:
        bad.append("demolished + unbuilt != Wikidata's not-standing count")
    total = sum(T[k] for k in ("not building", "tower structure",
                               "outside city", "no usable height",
                               "below floor", "implausible height",
                               "not standing (Wikidata)", "not in OSM",
                               "duplicate", "kept"))
    if total != T["items"]:
        bad.append(f"the funnel does not add up: {total} != {T['items']}")
    if abs(20 * math.log10(0.5 ** 1.6) + 10) > 0.6:
        bad.append("'about ten decibels quieter' at half height fails")
    for c, name in (("Paris", "Eiffel Tower"), ("Toronto", "CN Tower"),
                    ("Tokyo", "Tokyo Skytree")):
        if not any(l == name and w == "tower structure"
                   for _, l, w in R[c]["dropped"]):
            bad.append(f"{name} is not dropped as a tower structure")
    out = {c: [l for _, l, w in R[c]["dropped"] if w == "outside city"]
           for c in ("Paris", "Tel Aviv", "Tokyo")}
    if "Tour First" not in out["Paris"]:
        bad.append("La Defense (Tour First) is not dropped from Paris")
    if "Exchange Ramat Gan" not in out["Tel Aviv"]:
        bad.append("Ramat Gan is not dropped from Tel Aviv")
    if "Yokohama Landmark Tower" not in out["Tokyo"]:
        bad.append("Yokohama is not dropped from Tokyo")
    if not any(l == "Meiji University Liberty Tower" and w == "not in OSM"
               for _, l, w in R["Tokyo"]["dropped"]):
        bad.append("Limits names Meiji University Liberty Tower as left "
                   "out by OSM; it is not")
    C = {c["city"]: c for c in P["cities"]}
    ny = C["New York"]
    if not any(r[4] == "Empire State Building" and r[3] == 453.0
               for r in ny["ring"]):
        bad.append("the Empire State is not 453 m on the wheel")
    if ny["tallest"] == 453.0:
        bad.append("Limits says the Empire State is not New York's tallest")
    if not any(l == "270 Park Avenue" and "demolition" in w
               for _, l, w in R["New York"]["dropped"]):
        bad.append("the old 270 Park Avenue is not dropped as demolished")
    if not any(r[4] == "270 Park Avenue" for r in ny["ring"]):
        bad.append("the new 270 Park Avenue is not on the wheel")
    for c in THIN:
        if C[c]["n"] > 25:
            bad.append(f"{c} is named as thin but has {C[c]['n']} towers")
    return bad


THIN = ("Hong Kong", "Seoul")


def half_arcs(P):
    """For each city, the narrowest arc of true bearing holding half its
    wheel's towers."""
    out = []
    for c in P["cities"]:
        az = sorted(r[6] for r in c["ring"])
        n, k = len(az), (len(az) + 1) // 2
        best = min((az[(i + k - 1) % n] - az[i] + (360 if i + k - 1 >= n
                                                   else 0))
                   for i in range(n))
        out.append((best, c["city"]))
    return sorted(out)


def funnel(T, P):
    thin = sum(d["ring"] for d in P["dropped"])
    on = sum(len(c["ring"]) for c in P["cities"])
    rows = [
        ("Records the search returned", T["items"], False),
        ("not a building", -T["not building"], False),
        ("a tower or mast, not a building", -T["tower structure"], False),
        ("not in the city", -T["outside city"], False),
        ("no usable height", -T["no usable height"], False),
        (f"under {B.RING_FLOOR:.0f} meters", -T["below floor"], False),
        ("a height no building has (over 830 meters)",
         -T["implausible height"], False),
        (f"Buildings of {B.RING_FLOOR:.0f} meters or more in the cities",
         T["cand"], True),
        ("gone or unbuilt, by Wikidata's own record",
         -T["not standing (Wikidata)"], False),
        ("not matched in OpenStreetMap", -T["not in OSM"], False),
        ("the same building twice", -T["duplicate"], False),
        ("Towers confirmed standing", T["kept"], True),
        ("in the cities too thin for a wheel", -thin, False),
        ("beyond New York's tallest " + str(B.RING_MAX),
         -(T["kept"] - thin - on), False),
        ("Towers on the wheels", on, True),
    ]
    run = 0
    html_rows = []
    for label, n, total in rows:
        if total:
            if run != n:
                raise SystemExit(f"funnel: {label} is {n}, the steps give {run}")
            html_rows.append(f"<tr><th>{label}</th><th>{n:,}</th></tr>")
        else:
            run += n
            cell = f"{n:,}" if n >= 0 else f"&minus;{-n:,}"
            html_rows.append(f"<tr><td>{label}</td><td>{cell}</td></tr>")
        if label.startswith("Records"):
            run = n
    return "\n".join(html_rows)


def values(P, R):
    T = tally(R)
    C = sorted(P["cities"], key=lambda c: (-c["n"], c["city"]))
    by_h = sorted(P["cities"], key=lambda c: c["tallest"])
    rows = "\n".join(
        f"<tr><td>{html.escape(c['city'])}</td><td>{c['n']}</td>"
        f"<td>{len(c['ring'])}</td><td>{html.escape(c['tallestName'])}, "
        f"{c['tallest']:.0f} m</td></tr>" for c in C)
    keys = "\n".join(
        f"<tr><td>{html.escape(c['city'])}</td><td>{html.escape(c['key']['label'].replace('pent ', 'pentatonic '))}</td>"
        f"<td class=\"dim\">{html.escape(c['key']['why'])}</td></tr>"
        for c in P["cities"])
    modes = []
    for m in VOICE:
        cs = [c["city"] for c in P["cities"] if c["key"]["mode"] == m]
        if cs:
            modes.append(f"<tr><td>{MODE_NAME.get(m, m)}</td><td class=\"dim\">"
                         f"{VOICE[m][0]}</td><td class=\"dim\">{VOICE[m][1]}"
                         f"</td><td class=\"dim\">{html.escape(', '.join(cs))}"
                         f"</td></tr>")
    unvoiced = {c["key"]["mode"] for c in P["cities"]} - set(VOICE)
    if unvoiced:
        raise SystemExit(f"modes with no voicing on the page: {unvoiced}")
    ny = next(c for c in P["cities"] if c["city"] == "New York")
    top8 = sorted(ny["ring"], key=lambda r: -r[3])[:8]
    park = [r for r in ny["ring"] if r[4] == "270 Park Avenue"]
    arcs = half_arcs(P)
    share = T["not standing (Wikidata)"] / T["cand"]
    if abs(share - 0.05) > 0.01:
        raise SystemExit(f"'about one in twenty' is {share:.3f}")
    n_all = len(fetch_wikidata.CITIES)
    import insight
    v = {
        "h1": ("One in twenty of an open database's tall buildings in "
               f"{n_all} cities is not there"),
        "meta": (f"Wikidata lists {T['cand']:,} buildings of "
                 f"{B.RING_FLOOR:.0f} m or more for {n_all} cities. By its own records, "
                 f"{T['not standing (Wikidata)']} of them are demolished or unbuilt. "
                 "The towers that stand are played as "
                 "sound."),
        "stamp": insight.stamp(live=False),
        "floor": f"{B.RING_FLOOR:.0f}", "n_all": str(n_all),
        "cand": f"{T['cand']:,}", "gone": str(T["gone"]),
        "unbuilt": str(T["unbuilt"]), "noosm": str(T["not in OSM"]),
        "wd_out": str(T["not standing (Wikidata)"]),
        "n_city": str(len(P["cities"])), "ring_max": str(B.RING_MAX),
        "park_year": park_year(),
        "park_new": str(park[0][5]) if park and park[0][5] else "undated",
        "fig_alt": html.escape(
            "New York's eight tallest towers on the wheel as bars, by height "
            f"in meters, from {top8[0][4]} at {top8[0][3]:.0f} m to "
            f"{top8[-1][4]} at {top8[-1][3]:.0f} m."),
        "radius": f"{fetch_wikidata.RADIUS_KM:.0f}",
        "pull_floor": f"{fetch_wikidata.FLOOR_M:.0f}",
        "items": f"{T['items']:,}",
        "funnel_rows": funnel(T, P),
        "n_notb": str(T["not building"]),
        "n_tower": str(T["tower structure"]),
        "n_outside": str(T["outside city"]),
        "core_km": f"{B.CORE_KM:.0f}",
        "near_m": f"{B.NEAR_KEEP_M:.0f}", "n_dup": str(T["duplicate"]),
        "min_tall": str(B.MIN_TALL), "min_h": f"{B.MIN_HEIGHT:.0f}",
        "min_ring": str(B.MIN_RING),
        "n_dropped_word": WORDS.get(len(P["dropped"]),
                                    str(len(P["dropped"]))).capitalize(),
        "dropped": and_list([d["city"] for d in P["dropped"]]),
        "thin": and_list(list(THIN)),
        "city_rows": rows,
        "osm_h": str(sum(c["osmHeights"] for c in P["cities"])),
        "osm_off": str(sum(c["osmHeights"] - c["osmWithin10"]
                           for c in P["cities"])),
        "arc_lo": f"{arcs[0][0]:.0f}", "arc_lo_city": arcs[0][1],
        "arc_hi": f"{arcs[-1][0]:.0f}", "arc_hi_city": arcs[-1][1],
        "shortest_city": by_h[0]["city"], "tallest_city": by_h[-1]["city"],
        "key_rows": keys,
        "n_keys": str(len({c["key"]["label"] for c in P["cities"]})),
        "n_modes": WORDS.get(len({c["key"]["mode"] for c in P["cities"]}),
                             str(len({c["key"]["mode"] for c in P["cities"]}))),
        "mode_rows": "\n".join(modes),
        "fetched": day(P["sources"]["wikidataFetched"]),
        "osm_fetched": day(P["sources"]["osmFetched"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    return v, T


def keep_from_shipped(text, shipped):
    stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"',
                             shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return (f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps
                else m.group(0))
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render(P, R):
    t = open(TEMPLATE, encoding="utf-8").read()
    v, T = values(P, R)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    return keep_from_shipped(t, open(PAGE, encoding="utf-8").read()), T


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    R = json.load(open(REPORT, encoding="utf-8"))
    t, T = render(P, R)
    bad = claims(P, R, T, None)
    for b in bad:
        print("  CLAIM FAILS: " + b)
    old = open(PAGE, "rb").read().decode("utf-8")   # bytes: trap 32
    print("  skyline.html: " + ("unchanged" if old == t else
                                "would change" if not apply else "rewritten"))
    if apply and not bad:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
