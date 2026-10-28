"""
Write site/climate-cost.html from page.html and the model (lca.py).

Every number on the page is computed here from lca.Model, from
build_allocation_figure.py's bases, or from a file this script measures (the
archive's size); the prose is in page.html. The page had no generator until
2026-10-24 (R5): its table and prose figures were typed, which is how a
corrected model could have left a stale page behind (HANDOFF trap 12).

The corrections section is computed too. legacy() puts the three inputs D-26
and D-27 corrected back as they stood, in memory, reruns every item, and
checks the result against the totals the page published before (BEFORE,
copied from `python lca.py --all` on master 4dd30c2, 2026-10-24); then it
applies the corrections one at a time, so each item's move is credited to
the correction that made it.

claims() asserts what page.html's words say about the numbers ("most of it
is the animal", "under 2%", "nearly ten times"); if the model moves one, the
generator stops rather than ship prose the model contradicts.

The nav (rebuild_nav.py) and the ?v= stamps (bust_cache.py) are kept as the
shipped page has them, so tests/test_generators.py can run this on the
shipped tree and expect no change. The idiom is heat/update_page.py's; the
citation markers and Sources come from add_citations.PAGES, applied here.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import contextlib
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "climate-cost.html")
TEMPLATE = os.path.join(HERE, "page.html")
ZIP = os.path.join(SITE, "downloads", "climate-cost-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "data"))

import lca                            # noqa: E402  the model of record
import processes as D                 # noqa: E402  the module lca imported
from processes import PRODUCTS        # noqa: E402

# The totals the page published before the corrections, at each item's
# default route (lca.py --all on master 4dd30c2). legacy() must reproduce
# every one to the cent, or the "before" column would be a guess.
BEFORE = {
    "beef": 75.49, "car_petrol": 23.57, "flight_short": 21.40,
    "flight_long": 15.81, "jeans": 14.85, "cheese": 13.18, "car_ev": 12.81,
    "sneakers": 10.09, "bus_city": 9.52, "tshirt_cotton": 7.09,
    "chicken": 5.02, "tshirt_poly": 4.69, "leather_shoes": 3.66,
    "rice": 3.39, "coffee": 3.05, "tomato_greenhouse": 2.99, "almond": 1.74,
    "rail_intercity": 1.00, "banana": 0.89, "tomato_field": 0.67,
}
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
         13: "thirteen", 14: "fourteen", 15: "fifteen", 20: "twenty"}


def run(key, origin=None, dest=None, mode=None, life=None):
    p = PRODUCTS[key]
    return lca.Model(key, origin or p["default_origin"],
                     dest or p["default_dest"], mode, life).run()


def total(key, **kw):
    return run(key, **kw)["total"]


def stage(res, sid):
    return sum(s["total"] for s in res["spine"] if s["id"] == sid)


# ------------------------------------------------------------ corrections --
@contextlib.contextmanager
def reverted(which):
    """Put the named corrections back as they stood, in memory, and restore
    them afterwards. which: a subset of {"tanning", "gwp", "milk"}."""
    saved = []

    def put(obj, key, value):
        saved.append((obj, key, obj[key]))
        obj[key] = value
    shoes = PRODUCTS["leather_shoes"]["stages"]
    try:
        if "tanning" in which:
            st = {x["id"]: x for x in shoes}
            put(st["hide"], "inputs", st["tanning"]["inputs"])
            put(PRODUCTS["leather_shoes"], "stages",
                [x for x in shoes if x["id"] != "tanning"])
        if "gwp" in which:
            for obj, key, kind in GAS_TERMS():
                put(obj, key, obj[key] * D.WRITTEN_AT[kind] / D.GWP[kind])
            put(D.PROCESSES["field_n2o"], "direct", 4.4)
        if "milk" in which:
            for x in PRODUCTS["cheese"]["stages"]:
                if x.get("share") == D.MILK_SHARE:
                    put(x, "share", 0.85)
        yield
    finally:
        for obj, key, value in reversed(saved):
            obj[key] = value


def GAS_TERMS():
    """Every single-gas term processes.py restates through gas(), with the
    figure it was written at. Each is checked against gas() here, so a term
    whose value changes stops the build rather than reverting wrongly. A NEW
    term in processes.py must be added to this list by hand."""
    P = D.PROCESSES
    st = {k: {x["id"]: x for x in PRODUCTS[k]["stages"]} for k in PRODUCTS}
    terms = [(P["natgas_extraction"], "direct", "ch4_fossil", 0.42),
             (P["nitrate_fert"], "direct", "n2o", 1.4),
             (P["landfill"], "direct", "ch4_bio", 0.55),
             (st["beef"]["enteric"], "direct", "ch4_bio", 38.0),
             (st["cheese"]["enteric"], "direct", "ch4_bio", 8.4),
             (st["rice"]["paddy"], "direct", "ch4_bio", 1.85),
             (st["coffee"]["wet_mill"], "direct", "ch4_bio", 0.62)]
    for obj, key, kind, x in terms:
        if abs(obj[key] - D.gas(x, kind)) > 1e-12:
            raise SystemExit(f"a gas term is not gas({x}, {kind!r}) any more")
    return [(o, k, kind) for o, k, kind, _ in terms]


def legacy():
    """Totals with all three corrections reverted, then with each applied in
    turn. Returns {item: [before, +tanning, +gwp, +milk = now]}."""
    order = ["tanning", "gwp", "milk"]
    out = {k: [] for k in PRODUCTS}
    for i in range(len(order) + 1):
        with reverted(set(order[i:])):
            for k in PRODUCTS:
                out[k].append(total(k))
    bad = [k for k in PRODUCTS if round(out[k][0], 2) != BEFORE[k]]
    if bad:
        raise SystemExit("legacy() does not reproduce the published totals: "
                         + ", ".join(f"{k} {out[k][0]:.2f} vs {BEFORE[k]}" for k in bad))
    return out


CAUSE = {
    1: "tanning charged in full",
    2: "corrected warming potentials and soil nitrous oxide",
    3: "IDF's milk share",
}


def correction_rows(L):
    rows = []
    for k, (b, *steps) in sorted(L.items(), key=lambda kv: -abs(kv[1][-1] / kv[1][0] - 1)):
        now = steps[-1]
        if abs(now - b) < 0.005:
            continue
        moves = [(abs(steps[i] - ([b] + steps)[i]), i + 1) for i in range(3)]
        prev = [b] + steps
        signed = [(steps[i] - prev[i], i + 1) for i in range(3)]
        net = now - b
        # the corrections that moved it by half a cent in the direction it
        # moved overall, largest first; at least the largest (a total can
        # round across a cent on moves smaller than that). The shoe's GWP
        # move is -0.02 against tanning's +6.91 and is not "mostly from".
        ranked = sorted(signed, key=lambda x: -abs(x[0]))
        cause = ([CAUSE[i] for m, i in ranked if abs(m) > 0.005 and m * net > 0]
                 or [CAUSE[ranked[0][1]]])
        rows.append(f'<tr><td>{html.escape(PRODUCTS[k]["name"])}</td>'
                    f'<td class="n">{b:.2f}</td><td class="n">{now:.2f}</td>'
                    f'<td class="n">{100 * (now / b - 1):+.1f}%</td>'
                    f'<td>{"; ".join(cause)}</td></tr>')
    return "\n".join(rows)


# ------------------------------------------------------------------ table --
GROUPS = ("Food", "Transport", "Clothing")
NAMED = {"cheese": "cheese", "chicken": "chicken", "rice": "rice",
         "coffee": "coffee", "tomato_greenhouse": "heated-greenhouse tomatoes",
         "almond": "almonds", "banana": "bananas", "tomato_field": "field tomatoes",
         "beef": "beef"}


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


# How the prose names a food mid-sentence ("a field-grown tomato from Spain").
SHORT = {"beef": "kilogram of beef", "cheese": "kilogram of cheese",
         "chicken": "kilogram of chicken", "rice": "kilogram of rice",
         "coffee": "kilogram of coffee", "tomato_greenhouse": "heated-greenhouse tomato",
         "almond": "kilogram of almonds", "banana": "banana",
         "tomato_field": "field-grown tomato"}


def table_rows():
    rows = []
    for g in GROUPS:
        rows.append(f'<tr><td colspan="4" class="dim"><b>{g}</b></td></tr>')
        items = [(total(k), k) for k, p in PRODUCTS.items() if p.get("group", "Food") == g]
        for t, k in sorted(items, reverse=True):
            p = PRODUCTS[k]
            r = run(k)
            rows.append(f'<tr><td>{html.escape(p["name"])}</td><td class="n">{t:.2f}</td>'
                        f'<td>{html.escape(p["unit"])}</td>'
                        f'<td>{html.escape(r["origin_name"])} to {html.escape(r["dest_name"])}</td></tr>')
    return "\n".join(rows)


def foods():
    return [k for k, p in PRODUCTS.items() if p.get("group", "Food") == "Food"]


# ------------------------------------------------------------------- hero --
def hero(beef):
    import insight
    s = {x["id"]: x["total"] for x in beef["spine"]}
    farm = ("enteric", "landuse", "manure", "feed")
    after = sum(v for k, v in s.items() if k not in farm)
    spec = {
        "type": "split", "id": "cc-beef",
        "title": ("Where the greenhouse gas from one kilogram of beef, Brazil "
                  "to Texas, comes from, in kilograms of CO2e"),
        "unit": "kg", "decimals": 1,
        "total": {"label": "One kilogram of beef,", "value": beef["total"]},
        "parts": [
            {"label": "Methane, the cow's gut", "value": s["enteric"], "color": "acc"},
            {"label": "Forest cleared", "value": s["landuse"], "color": "moss"},
            {"label": "Manure", "value": s["manure"], "color": "ink"},
            {"label": "Feed", "value": s["feed"], "color": "dim"},
            {"label": "After the farm", "value": after, "color": "rule"},
        ],
    }
    return spec, after


# ----------------------------------------------------------------- values --
def km_word(x):
    return f"{round(x, -1):,.0f}"


def values():
    import insight
    import build_allocation_figure as F
    car_km = total("car_petrol") / 100.0          # kg CO2e per km, one occupant
    beef = run("beef")
    b = beef["total"]
    spec, after = hero(beef)
    enteric, land = stage(beef, "enteric"), stage(beef, "landuse")
    fr = {k: stage(run(k), "freight") / total(k) for k in foods()}
    ship_max = max(fr, key=fr.get)
    banana_air = total("banana", mode="air") / total("banana")
    beef_air = total("beef", mode="air") / b - 1
    field_air = total("tomato_field", mode="air") / total("tomato_field")
    # the heated tomato's adder on every route the model runs, both entries
    # on the same route (the comment this replaces measured 784 pairs)
    regions = list(D.REGIONS)
    pairs = [(total("tomato_greenhouse", origin=o, dest=d), total("tomato_field", origin=o, dest=d))
             for o in regions for d in regions if o != d]
    adders = [g - fd for g, fd in pairs]
    ratio = min((g - fd) / fd for g, fd in pairs)
    if not all(PRODUCTS[k]["transport_mode"] == "sea" for k in ("tomato_field", "tomato_greenhouse")):
        raise SystemExit("the tomato routes are no longer sea routes; the page says they are")
    nl_x = total("tomato_greenhouse", origin="NL", dest="US-NY") / total("tomato_field", origin="NL", dest="US-NY")
    farm = {}
    for k in foods():
        r = run(k)
        ids = [x["id"] for x in r["spine"]]
        farm[k] = sum(x["total"] for x in r["spine"][:ids.index("freight")]) / r["total"]
    # "the other high-footprint foods": every food of 2 kg CO2e or more
    farm_min = min(v for k, v in farm.items() if total(k) >= 2.0)
    field = run("tomato_field")
    loss = {}
    for k in foods():
        base, w = total(k), PRODUCTS[k]["waste_frac"]
        PRODUCTS[k]["waste_frac"] = 0.0
        try:
            loss[k] = 100 * (1 - total(k) / base)
        finally:
            PRODUCTS[k]["waste_frac"] = w
    lt = PRODUCTS["car_petrol"]["lifetime"]["default"]
    if PRODUCTS["car_ev"]["lifetime"]["default"] != lt:
        raise SystemExit("the two cars no longer share a lifetime; the page says one figure")
    life = {k: [total(k, life=lt / 2), total(k), total(k, life=lt * 2)] for k in ("car_petrol", "car_ev")}
    fuel = {k: stage(run(k), "fuel") for k in ("flight_short", "flight_long")}
    with reverted({"tanning", "gwp", "milk"}):
        old = run("leather_shoes")
        hide_before = stage(old, "hide") / old["total"]
    up_list = ", ".join(f"{SHORT[k].replace('kilogram of ', '')} {v:.0f}%" for k, v in
                        sorted(UPSTREAM["others"].items(), key=lambda kv: -kv[1]))
    disp = max(stage(run(k), "waste") / total(k) for k, p in PRODUCTS.items() if p.get("group") == "Clothing")
    shoes = run("leather_shoes")
    tan = stage(shoes, "tanning") / shoes["total"]
    hide = stage(shoes, "hide") / shoes["total"]
    cheese_rows, cheese_spread = F.compute(F.CHEESE)
    shoe_rows, shoe_spread = F.compute(F.SHOES)
    cr = {r[1]: r[4] for r in cheese_rows}
    sr = {r[1]: r[4] for r in shoe_rows}
    herd = F._stage_share(F.CHEESE)
    L = legacy()
    steps = [
        (f"<p>A kilogram of beef from a Brazilian herd, eaten in Texas, comes to "
         f"{b:.1f} kg of CO<sub>2</sub>e. This unit counts the warming effect of "
         f"every gas as carbon dioxide. A petrol car with one person in it "
         f"emits {car_km:.2f} kg a kilometer, including its share of the factory and "
         f"the road. So the kilogram of beef is {km_word(b / car_km)} km of driving.</p>", {"s": 0}),
        (f"<p>Split by source, {100 * (enteric + land) / b:.0f}% is two "
         f"things that happen on the ranch: methane from the cow's gut, and the "
         f"forest cleared for its pasture. Everything after the animal leaves the "
         f"farm is {100 * after / b:.1f}%. The {beef['km']:,.0f} km ocean "
         f"crossing is {100 * fr['beef']:.1f}% of the total.</p>", {"s": 1}),
    ]
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0
    v = {
        "h1": ("A kilogram of Brazilian beef carries the emissions of a "
               f"{km_word(b / car_km)}-kilometer drive"),
        "meta": (f"A kilogram of Brazilian beef comes to {b:.0f} kg CO2e, or {km_word(b / car_km)} km "
                 "of driving. How food is grown decides most footprints; "
                 "shipping matters little unless the food flies or goes a long way "
                 "by truck. A life-cycle model of twenty everyday things, with "
                 "its working shown."),
        "iso_km": km_word(UPSTREAM["beef"] / car_km),
        "farm_min": f"{100 * farm_min:.0f}",
        "hi_foods": and_list([NAMED[k] for k in sorted(farm, key=lambda k: -total(k))
                              if k != "beef" and total(k) >= 2.0]),
        "nl_x": f"{nl_x:.1f}",
        "fcult_pct": f"{100 * stage(field, 'cultivation') / field['total']:.0f}",
        "field_total": f"{field['total']:.2f}",
        "fuel_short": f"{fuel['flight_short']:.1f}", "fuel_long": f"{fuel['flight_long']:.1f}",
        "car_life": f"{lt:,.0f}",
        "petrol_half": f"{life['car_petrol'][0]:.1f}", "petrol_now": f"{life['car_petrol'][1]:.1f}",
        "petrol_double": f"{life['car_petrol'][2]:.1f}",
        "ev_half": f"{life['car_ev'][0]:.1f}", "ev_now": f"{life['car_ev'][1]:.1f}",
        "ev_double": f"{life['car_ev'][2]:.1f}",
        "loss_lo": f"{min(loss.values()):.0f}", "loss_hi": f"{max(loss.values()):.0f}",
        "disp_max": f"{100 * disp:.0f}",
        "mixed_over": f"{100 * max(D.WRITTEN_AT[g] / D.GWP[g] - 1 for g in ('ch4_bio', 'n2o')):.0f}",
        "enteric_pct": f"{100 * enteric / b:.0f}",
        "land_pct": f"{100 * land / b:.0f}",
        "beef_freight_pct": f"{100 * fr['beef']:.1f}",
        "ship_max_pct": f"{100 * fr[ship_max]:.0f}",
        "banana_air_x": f"{banana_air:.1f}",
        "stamp": insight.stamp(live=False),
        "takeaways": insight.takeaways([
            f"A kilogram of beef is {b / total('cheese'):.1f} times a kilogram of "
            f"hard cheese and {b / total('chicken'):.0f} times a kilogram of chicken. "
            "This is because a cow's gut makes methane and this herd's pasture was cut "
            "from forest.",
            f"Heat for a greenhouse adds about {sum(adders) / len(adders):.1f} kg to "
            "every kilogram of tomatoes on every sea route the model runs. That is more "
            "than twice the whole footprint of a field tomato on the "
            "same route.",
            f"Most of the footprint of a pair of leather shoes is the tanning, {100 * tan:.0f}% of it. "
            f"The shoe's share of the cow, the part that footprints argue over, is "
            f"{100 * hide:.0f}% of the pair.",
        ]),
        "hero": insight.scrolly(spec, steps, from_state={"s": 0}),
        "n_items": WORDS[len(PRODUCTS)],
        "n_regions": f"{len(D.REGIONS)}",
        "table": table_rows(),
        "tee_km": f"{total('tshirt_cotton') / car_km:.0f}",
        "trainer_beef_g": f"{1000 * total('sneakers') / b:.0f}",
        "corr_rows": correction_rows(L),
        "shoe_before": f"{L['leather_shoes'][0]:.2f}",
        "shoe_now": f"{L['leather_shoes'][-1]:.2f}",
        "soil_old": "4.4", "soil_new": f"{D.SOIL_N2O:.2f}",
        "gwp_bio": f"{D.GWP['ch4_bio']:g}", "gwp_fossil": f"{D.GWP['ch4_fossil']:g}",
        "gwp_n2o": f"{D.GWP['n2o']:g}",
        "milk_share": f"{100 * D.MILK_SHARE:.0f}",
        "herd_pct": f"{100 * herd:.0f}",
        "ch_se": f"{cr[0.63]:.1f}", "ch_flysjo": f"{cr[0.85]:.1f}",
        "ch_idf": f"{cr[D.MILK_SHARE]:.1f}", "ch_mass": f"{cr[0.98]:.1f}",
        "ch_none": f"{cr[1.0]:.1f}", "ch_spread": f"{cheese_spread:.2f}",
        "ch_se_hi": f"{cr[0.76]:.1f}", "ch_econ": f"{cr[0.92]:.1f}", "ch_prot": f"{cr[0.93]:.1f}",
        "shoe_lo": f"{sr[0.027]:.1f}", "shoe_hi": f"{sr[0.069]:.1f}",
        "shoe_lo_all": f"{min(sr.values()):.1f}",
        "shoe_x": f"{L['leather_shoes'][-1] / L['leather_shoes'][0]:.1f}",
        "hide_pct_before": f"{100 * hide_before:.0f}",
        "up_list": up_list,
        "shoe_spread": f"{shoe_spread:.2f}",
        "hide_pct": f"{100 * hide:.0f}",
        "heat_lo": f"{min(adders):.2f}", "heat_hi": f"{max(adders):.2f}",
        "n_routes": f"{len(adders):,}",
        "banana_km": f"{run('banana')['km']:,.0f}",
        "banana_sea": f"{total('banana'):.2f}",
        "beef_air_pct": f"{100 * beef_air:.0f}",
        "field_air_x": f"{field_air:.0f}",
        "chain_alt": chain_alt(),
        "upstream_beef": f"{UPSTREAM['beef']:.1f}",
        "upstream_pct": f"{100 * (1 - UPSTREAM['beef'] / b):.0f}",
        "slaughter_share": f"{100 * next(x['share'] for x in PRODUCTS['beef']['stages'] if x['id'] == 'slaughter'):.0f}",
        "hide_share": f"{100 * next(x['share'] for x in PRODUCTS['leather_shoes']['stages'] if x['id'] == 'hide'):.1f}",
        "zip_kb": f"{zip_kb:,}",
    }
    facts = dict(b=b, car_km=car_km, enteric=enteric, land=land, after=after,
                 fr=fr, banana_air=banana_air, tan=tan, hide=hide,
                 adders=adders, ratio=ratio, shoe_spread=shoe_spread,
                 cheese_spread=cheese_spread, beef_air=beef_air, L=L,
                 loss=loss, farm=farm, farm_min=farm_min,
                 field_cult=stage(field, "cultivation") / field["total"])
    return v, facts


def chain_alt():
    """The tomato chain figure's alt text, from the same trace() it draws."""
    import build_allocation_chain as C
    _, cult, fert, amm, gas = C.trace()
    g = lambda n: C.g(n["total"])   # noqa: E731  the figure's own formatter
    return html.escape(
        "A field tomato traced four supply-chain levels deep: the cultivation "
        f"stage at {g(cult)} of CO2e per kilogram, the fertiliser it needs at "
        f"{g(fert)}, the ammonia that fertiliser needs at {g(amm)}, and the "
        f"natural gas extraction behind the ammonia at {g(gas)}, with the "
        "physical quantity flowing along each arrow.")


def upstream(key):
    """QA's ISO-strict variant (D-26 item 1, not adopted; qa-audit
    cc_rev_exp.py "upstream"): the share at the stage where the co-products
    separate also charged to every stage before it. The split stage is the
    last share before the freight leg; a stage that already carries a share
    (the cheese's milk) takes the product of the two. Printed in Limits."""
    st = PRODUCTS[key]["stages"]
    ids = [x["id"] for x in st]
    pre = st[:ids.index("freight")] if "freight" in ids else st
    split = [i for i, x in enumerate(pre) if x.get("share", 1.0) < 1.0][-1]
    share = pre[split]["share"]
    saved = [(x, x.get("share")) for x in st]
    try:
        for x in pre[:split]:
            x["share"] = x.get("share", 1.0) * share
        return total(key)
    finally:
        for x, s in saved:
            if s is None:
                x.pop("share", None)
            else:
                x["share"] = s


def upstream_all():
    out = {}
    for k in foods():
        st = PRODUCTS[k]["stages"]
        if any(x.get("share", 1.0) < 1.0 for x in st):
            out[k] = upstream(k)
    UPSTREAM["beef"] = out.pop("beef")
    UPSTREAM["others"] = {k: 100 * (1 - v / total(k)) for k, v in out.items()}


UPSTREAM = {}


def claims(f):
    bad = []
    if not (f["enteric"] + f["land"]) / f["b"] > 0.5:
        bad.append("'most of it is the animal' (methane and land under half)")
    if not f["fr"]["beef"] < 0.01:
        bad.append("beef's ocean crossing is not under 1%")
    if not 9 <= f["banana_air"] < 10:
        bad.append(f"'nearly ten times' for the banana: {f['banana_air']:.2f}")
    if not f["tan"] > 0.5:
        bad.append("'mostly the tanning'")
    if not f["hide"] < 0.02:
        bad.append("'under 2%' for the hide")
    if not f["shoe_spread"] < f["cheese_spread"]:
        bad.append("allocation moves the shoe more than the cheese")
    if not max(f["fr"].values()) < 0.3:
        bad.append("shipping by sea or rail is not 'at most a quarter' of any food")
    if not f["ratio"] > 2:
        bad.append(f"'more than twice a field tomato' fails on some route: {f['ratio']:.2f}")
    if not min(f["adders"]) > 2:
        bad.append("heating adds under 2 kg on some route")
    if set(sorted(f["loss"], key=f["loss"].get)[-2:]) != {"tomato_field", "banana"}:
        bad.append("'most for the field tomato and the banana' (the two largest loss moves)")
    if not f["field_cult"] < 0.5:
        bad.append("'most of [the field tomato] comes after the farm'")
    if not f["farm_min"] > 0.5:
        bad.append("foods of 2 kg or more: under half before leaving the region")
    if not f["beef_air"] < 0.2:
        bad.append("air freight moves beef by a fifth or more")
    return bad


# ----------------------------------------------------------------- render --
def keep_from_shipped(text, shipped):
    stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render():
    upstream_all()
    t = open(TEMPLATE, encoding="utf-8").read()
    v, f = values()
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    return keep_from_shipped(t, open(PAGE, encoding="utf-8").read()), f


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("climate-cost.html")
    if not refs:
        return text, ["climate-cost.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    t, f = render()
    t, probs = cite(t)
    bad = claims(f)
    for p in probs:
        print("  " + p)
    for b in bad:
        print("  CLAIM FAILS: " + b)
    old = open(PAGE, "rb").read().decode("utf-8")   # bytes: trap 32
    print("  climate-cost.html: " + ("unchanged" if old == t else
                                     "would change" if not apply else "rewritten"))
    if apply and not bad and not probs:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if (probs or bad) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
