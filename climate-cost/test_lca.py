"""
Check the model against published footprints and against itself.

Two kinds of test. The first compares totals to the ranges in Poore & Nemecek
(Science, 2018) and related syntheses - not to a single number, because these
are distributions across thousands of farms and a point estimate would be false
precision. The second checks internal consistency: that the tree sums, that
a stage's allocation reaches the processes beneath it, and that the levers move the answer
in the direction physics says they should.
"""
import sys, math
from lca import Model, paths
# The module lca.py itself imported (it puts data/ on the path), not a second
# copy as data.processes: a --break that mutates a copy the engine never reads
# leaves every check green (found 2026-10-24, the tanning break exited 0).
import processes as D  # noqa: E402
PRODUCTS, REGIONS = D.PRODUCTS, D.REGIONS

# The constants D-26 and D-27 corrected (R5, 2026-10-24), held a second time
# here apart from data/processes.py, so an edit there fails whether or not it
# moves a total (HANDOFF trap 16). Sources: IPCC AR6 WGI Table 7.15 errata,
# 7 October 2025; IPCC 2019 Refinement Vol. 4 Ch. 11 Tables 11.1 and 11.3;
# IDF Bulletin 479 (2015).
GWP_HELD = {"ch4_bio": 25.3, "ch4_fossil": 28.1, "n2o": 267.0}
SOIL_HELD = (0.010 + 0.11 * 0.010 + 0.24 * 0.011) * 44.0 / 28.0 * 267.0
MILK_HELD = 0.88

# --break replays a historical fault in memory and the run must exit 1:
#   tanning  tanning back inside the hide stage, so the 2.2% share reaches it
#            (D-26 item 2: the shoe at 3.66)
#   gwp      the single-gas terms back at the values typed before the errata
#            (D-26 item 3: 38.0 enteric, 4.4 soil N2O, 0.42 gas leak)
#   milk     the herd stages back at Flysjo's Swedish 0.85 (D-27 item 5)
BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
if BREAK == "tanning":
    st = {x["id"]: x for x in PRODUCTS["leather_shoes"]["stages"]}
    st["hide"]["inputs"] = st["tanning"]["inputs"]
    PRODUCTS["leather_shoes"]["stages"].remove(st["tanning"])
elif BREAK == "gwp":
    PRODUCTS["beef"]["stages"][0]["direct"] = 38.0
    D.PROCESSES["field_n2o"]["direct"] = 4.4
    D.PROCESSES["natgas_extraction"]["direct"] = 0.42
elif BREAK == "milk":
    for x in PRODUCTS["cheese"]["stages"]:
        if x.get("share") == D.MILK_SHARE:
            x["share"] = 0.85
elif BREAK:
    raise SystemExit(f"unknown --break {BREAK}")

# (low, high) kg CO2e per kg, from the literature, at a comparable boundary
EXPECTED = {
    "beef":              (25, 100, "P&N beef herd 10th-90th percentile, 60 median"),
    "cheese":            (11, 30,  "P&N cheese, 21 median"),
    "chicken":           (3, 12,   "P&N poultry, 6 median"),
    "rice":              (2.5, 6,  "P&N rice, 4 median"),
    "coffee":            (2.5, 30, "P&N roasted, wide; wet-processed low end"),
    "tomato_greenhouse": (2, 8,    "heated glasshouse, northern Europe"),
    "tomato_field":      (0.3, 1.5,"P&N field tomato, 0.7-2.1 incl. glasshouse"),
    "banana":            (0.5, 1.5,"P&N bananas, 0.9 median"),
    "almond":            (1, 4,    "P&N nuts, 0.4-2.3; irrigation-heavy high"),

    # Transport, per 100 passenger-km. Anchors are the UK DESNZ conversion
    # factors and the IPCC AR6 transport chapter. Aviation figures include the
    # non-carbon effects, without which they roughly halve.
    "car_petrol":        (15, 30,  "DESNZ average petrol car, 0.17-0.19 "
                                   "kg/km tailpipe, plus vehicle and roads"),
    "car_ev":            (6, 20,   "battery electric on a 0.37 kg/kWh grid, "
                                   "pack and glider amortised"),
    "bus_city":          (4, 16,   "DESNZ average local bus, 0.10 kg/pkm"),
    "rail_intercity":    (0.2, 4,  "French electric rail; the grid is 0.06 "
                                   "kg/kWh, so this is meant to look absurd"),
    "flight_short":      (12, 32,  "DESNZ domestic and short-haul with "
                                   "radiative forcing, 0.15-0.25 kg/pkm"),
    "flight_long":       (10, 26,  "DESNZ long-haul economy with radiative "
                                   "forcing, 0.15-0.20 kg/pkm"),

    # Clothing, one garment through its whole life including laundry.
    "tshirt_cotton":     (3, 10,   "published cotton tee 2-7 kg; the spread "
                                   "is mostly whether care was counted"),
    "tshirt_poly":       (2, 9,    "polyester tee, worse fibre, lighter care"),
    "jeans":             (8, 35,   "Levi Strauss own LCA of a pair of 501s, "
                                   "33.4 kg over the garment's life"),
    "sneakers":          (7, 22,   "MIT running-shoe teardown, about 14 kg"),
    "leather_shoes":     (2, 25,   "tanning is most of a pair; the hide's "
                                   "share of the animal is a small part"),
}

fails = 0
print(f"{'item':26s} {'model':>8s}  {'expected':>13s}   source")
print("-"*86)
for key, (lo, hi, src) in EXPECTED.items():
    p = PRODUCTS[key]
    r = Model(key, p["default_origin"], p["default_dest"]).run()
    ok = lo <= r["total"] <= hi
    if not ok: fails += 1
    print(f"{p['name'][:26]:26s} {r['total']:8.2f}  {lo:5.1f} - {hi:5.1f}   "
          f"{'ok' if ok else '*** OUTSIDE ***'}  {src}")

print("\ninternal consistency")
print("-"*86)

# 1. every node's total equals its own direct plus its children
def check_sum(n, path=""):
    s = n["direct"] + sum(c["total"] for c in n["children"])
    if abs(s - n["total"]) > 1e-9:
        return [f"{path}/{n['name']}: total {n['total']:.6f} != {s:.6f}"]
    out = []
    for c in n["children"]:
        out += check_sum(c, path + "/" + n["name"])
    return out
bad = []
for key in PRODUCTS:
    p = PRODUCTS[key]
    r = Model(key, p["default_origin"], p["default_dest"]).run()
    for s in r["spine"]:
        bad += check_sum(s)
    if abs(sum(s["total"] for s in r["spine"]) - r["total"]) > 1e-9:
        bad.append(f"{key}: spine does not sum to total")
print(f"  tree sums correctly at every node      {'ok' if not bad else bad[:2]}")
if bad: fails += 1

# 2. allocation compounds: cheese carries 0.88 to milk on the herd stages.
# The stage is also scaled by the overproduction factor, because 8% of the
# cheese made is never eaten and the cow still had to produce it.
r = Model("cheese","FR","US-NY").run()
ent = [s for s in r["spine"] if s["id"]=="enteric"][0]
raw, op = 8.4 * 25.3 / 27.0, r["overproduce"]
ok = abs(ent["direct"] - raw*MILK_HELD*op) < 1e-9
print(f"  allocation x overproduction at stage   {'ok' if ok else 'FAIL'}"
      f"  ({raw:.3f} x {MILK_HELD} x {op:.3f} = {ent['direct']:.3f})")
fails += 0 if ok else 1

# 3. allocation compounds down a chain: feed stage inherits 0.88 onto ammonia
# One level, in one product. No edge below a stage in the data carries a
# share other than 1.0, so nothing compounds further than this (D-27).
feed = [s for s in r["spine"] if s["id"]=="feed"][0]
am = [c for c in feed["children"] if c["id"]=="ammonia"][0]
ok = abs(am["alloc"] - MILK_HELD) < 1e-9
print(f"  allocation compounds into children     {'ok' if ok else 'FAIL'}"
      f"  (ammonia alloc {am['alloc']:.2f})")
fails += 0 if ok else 1

# 4. levers move the right way
base = Model("tomato_field","ES","US-TX").run()["total"]
air  = Model("tomato_field","ES","US-TX", mode="air").run()["total"]
near = Model("tomato_field","MX","US-TX").run()["total"]
print(f"  air freight raises the total           {'ok' if air>base else 'FAIL'}"
      f"  ({base:.2f} -> {air:.2f})")
print(f"  a nearer origin lowers it              {'ok' if near<base else 'FAIL'}"
      f"  ({base:.2f} -> {near:.2f})")
fails += (0 if air>base else 1) + (0 if near<base else 1)

# 5. a dirtier destination grid raises a chilled product
cool_grid = Model("cheese","FR","US-NY").run()["total"]
dirty     = Model("cheese","FR","IN").run()["total"]
print(f"  a dirtier consuming grid raises it     {'ok' if dirty>cool_grid else 'FAIL'}"
      f"  ({cool_grid:.2f} -> {dirty:.2f})")
fails += 0 if dirty>cool_grid else 1

# 6. the greenhouse costs more than the field, same plant
f = Model("tomato_field","NL","US-NY").run()["total"]
g = Model("tomato_greenhouse","NL","US-NY").run()["total"]
print(f"  heated glass beats field, same route   {'ok' if g>f else 'FAIL'}"
      f"  ({f:.2f} field vs {g:.2f} glass)")
fails += 0 if g>f else 1

# 7. no production step is billed at the consumer's grid.
# This is the bug that hid longest: a French dairy's electricity was charged at
# India's grid intensity because someone in India ate the cheese. It is
# invisible in any single run - the number simply looks a bit high - and only
# shows up when the destination is changed and something moves that should not.
PR = D.PROCESSES
PRODUCER_STAGES = {"cultivation","harvest","packing","wet_mill","drying",
                   "hulling","milling","housing","slaughter","dairy",
                   "cheesemaking","feed","ageing","paddy","enteric","manure",
                   "landuse"}
mism = []
for pk, pp in PRODUCTS.items():
    for st in pp["stages"]:
        if st["id"] not in PRODUCER_STAGES:
            continue
        for cid, _a, _al in st["inputs"]:
            pr = PR.get(cid, {})
            if pr.get("grid_scaled") and pr.get("consumer_grid"):
                mism.append(f"{pk}/{st['id']} uses {cid}")
ok = not mism
print(f"  production power on the producing grid   {'ok' if ok else 'FAIL'}"
      f"  {mism[:2] if mism else ''}")
fails += 0 if ok else 1

# 8. and the consequence: a production-heavy item barely moves with destination
a = Model("beef","BR","FR").run()["total"]
b = Model("beef","BR","CN").run()["total"]
swing = abs(b-a)/a
ok = swing < 0.05
print(f"  destination barely moves beef            {'ok' if ok else 'FAIL'}"
      f"  ({swing:.1%} across France to China)")
fails += 0 if ok else 1

# 10. the three stage multipliers mean three things, and say so.
# Until 2026-09-04 one field called `allocation` held a co-product share, a
# lifetime amortisation and a shipment mass, which is how "allocation 160%"
# reached the screen and how a shoe came to "triple". A share is a fraction
# and must carry its basis; an amortisation must be the functional unit over
# the product's own lifetime default; a freight mass must be a plausible
# number of kilograms, not tonnes (the car delivery leg shipped as 1.4).
bad = []
for pk, pp in PRODUCTS.items():
    lt = pp.get("lifetime")
    for st in pp["stages"]:
        if "allocation" in st:
            bad.append(f"{pk}/{st['id']}: legacy `allocation` field")
        if "share" in st:
            if not 0 < st["share"] <= 1:
                bad.append(f"{pk}/{st['id']}: share {st['share']} outside (0,1]")
            if not st.get("basis"):
                bad.append(f"{pk}/{st['id']}: share without a basis")
        if "amortise" in st:
            if not lt or st["id"] not in lt["stages"]:
                bad.append(f"{pk}/{st['id']}: amortise on a stage the lifetime does not scale")
            elif abs(100.0 / st["amortise"] - lt["default"]) > 0.01 * lt["default"]:
                bad.append(f"{pk}/{st['id']}: 100/amortise = {100/st['amortise']:,.0f} "
                           f"but lifetime default is {lt['default']:,}")
        if "freight_kg" in st:
            if not st.get("transport"):
                bad.append(f"{pk}/{st['id']}: freight_kg on a non-transport stage")
            if not 0.05 <= st["freight_kg"] <= 20000:
                bad.append(f"{pk}/{st['id']}: freight_kg {st['freight_kg']} is not kilograms")
ok = not bad
print(f"  share/amortise/freight_kg are what they claim {'ok' if ok else 'FAIL'}"
      f"  {bad[:3] if bad else ''}")
fails += 0 if ok else 1

# 11. the corrected warming potentials, pinned as parameters (D-26 item 3).
# Each single-gas term is its pre-errata figure restated at the 2025 table.
held = {
    "beef enteric": (PRODUCTS["beef"]["stages"][0]["direct"], 38.0 * 25.3 / 27),
    "cheese enteric": (PRODUCTS["cheese"]["stages"][0]["direct"], 8.4 * 25.3 / 27),
    "soil N2O": (D.PROCESSES["field_n2o"]["direct"], SOIL_HELD),
    "gas leak": (D.PROCESSES["natgas_extraction"]["direct"], 0.42 * 28.1 / 28),
    "nitric acid": (D.PROCESSES["nitrate_fert"]["direct"], 1.4 * 267 / 273),
    "landfill": (D.PROCESSES["landfill"]["direct"], 0.55 * 25.3 / 27),
}
bad = [k for k, (got, want) in held.items() if abs(got - want) > 1e-9]
bad += [] if D.GWP == GWP_HELD else ["GWP table"]
ok = not bad
print(f"  warming potentials at the 2025 errata  {'ok' if ok else 'FAIL'}"
      f"  {bad if bad else ''}")
fails += 0 if ok else 1

# 12. tanning is charged in full (D-26 item 2). It serves only the leather, so
# no co-product share may reach it; at 2.2% the shoe was 3.66 kg, not 10.6.
r = Model("leather_shoes", "IT", "US-NY").run()
reach = []
def walk(n):
    if n["id"] == "leather":
        reach.append(n["alloc"])
    for c in n["children"]:
        walk(c)
for s in r["spine"]:
    walk(s)
ok = reach and all(abs(a - 1.0) < 1e-9 for a in reach)
print(f"  tanning charged at 1.0, not the hide's share {'ok' if ok else 'FAIL'}"
      f"  (alloc {reach}, pair {r['total']:.2f})")
fails += 0 if ok else 1

# 13. the dairy cow's milk share is IDF 2015's formula at BMR 0.02 (D-27 item 5)
herd = [x.get("share") for x in PRODUCTS["cheese"]["stages"]
        if x["id"] in ("enteric", "feed", "manure", "dairy")]
ok = all(h == MILK_HELD for h in herd)
print(f"  milk share is IDF's 0.88 on every herd stage {'ok' if ok else 'FAIL'}"
      f"  ({herd})")
fails += 0 if ok else 1

# 9. what the cutoff discards is genuinely small
r = Model("beef","BR","US-TX").run()
share = r["cut"]/r["total"]
ok = share < 0.01
print(f"  cutoff discards under 1% of the total  {'ok' if ok else 'FAIL'}"
      f"  ({share:.3%})")
fails += 0 if ok else 1

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
