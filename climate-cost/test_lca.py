"""
Check the model against published footprints and against itself.

Two kinds of test. The first compares totals to the ranges in Poore & Nemecek
(Science, 2018) and related syntheses - not to a single number, because these
are distributions across thousands of farms and a point estimate would be false
precision. The second checks internal consistency: that the tree sums, that
allocation compounds the way it claims to, and that the levers move the answer
in the direction physics says they should.
"""
import sys, math
from lca import Model, paths
from data.processes import PRODUCTS, REGIONS

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
    "leather_shoes":     (2, 25,   "range is dominated by the hide "
                                   "allocation, not by manufacture"),
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

# 2. allocation compounds: cheese carries 0.85 to milk on the herd stages.
# The stage is also scaled by the overproduction factor, because 8% of the
# cheese made is never eaten and the cow still had to produce it.
r = Model("cheese","FR","US-NY").run()
ent = [s for s in r["spine"] if s["id"]=="enteric"][0]
raw, op = 8.4, r["overproduce"]
ok = abs(ent["direct"] - raw*0.85*op) < 1e-9
print(f"  allocation x overproduction at stage   {'ok' if ok else 'FAIL'}"
      f"  ({raw} x 0.85 x {op:.3f} = {ent['direct']:.3f})")
fails += 0 if ok else 1

# 3. allocation compounds down a chain: feed stage inherits 0.85 onto ammonia
feed = [s for s in r["spine"] if s["id"]=="feed"][0]
am = [c for c in feed["children"] if c["id"]=="ammonia"][0]
ok = abs(am["alloc"] - 0.85) < 1e-9
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
from data.processes import PROCESSES as PR
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

# 9. what the cutoff discards is genuinely small
r = Model("beef","BR","US-TX").run()
share = r["cut"]/r["total"]
ok = share < 0.01
print(f"  cutoff discards under 1% of the total  {'ok' if ok else 'FAIL'}"
      f"  ({share:.3%})")
fails += 0 if ok else 1

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
