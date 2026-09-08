"""
The true climate cost of a thing: a life-cycle model that shows its working.

Give it three inputs - an item, where it was produced, where it is consumed -
and it returns the greenhouse gas emissions of every step, arranged the way the
thing actually happens: a spine of life-cycle stages from field to bin, with a
branching tree hanging off each stage showing where the emissions inside that
stage came from.

Two ideas make it more useful than a footprint number.

**Recursion.** A tomato needs fertiliser; the fertiliser needs ammonia; the
ammonia needs natural gas; extracting the gas leaks methane. That chain is four
levels deep and every level is a real emission somewhere. Most published
footprints collapse it to one figure. This expands it until the remaining
contributions fall below a cutoff, and reports the cutoff so you know what was
dropped.

**Allocation.** Every branch carries a multiplier saying how much of that
process belongs to our product. A slaughterhouse also makes leather; a dairy
cow also becomes beef; a coffee mill also sells pulp. Those multipliers compound
down the path, so a process four levels deep might contribute only a third of
its emissions to our tomato. Allocation is where most of the disagreement
between published footprints actually lives, and it is usually invisible. Here
it is a number on every edge.

Run:
    python3 lca.py                          # tomato, Spain to Texas
    python3 lca.py --item beef --from BR --to US-TX
    python3 lca.py --list                   # what is available
    python3 lca.py --build                  # write the visualiser
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "data"))
from processes import PROCESSES, PRODUCTS, REGIONS, TRANSPORT  # noqa: E402

# Expansion stops when a branch contributes less than this share of the
# product total. Reported in the output so the reader knows what is missing.
CUTOFF = 0.0015
MAX_DEPTH = 6


def great_circle(a, b):
    """Kilometers between two regions."""
    r1, r2 = REGIONS[a], REGIONS[b]
    p1, p2 = math.radians(r1["lat"]), math.radians(r2["lat"])
    dl = math.radians(r2["lon"] - r1["lon"])
    dp = p2 - p1
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(h)))


def route_km(a, b, mode):
    """Realistic path length. Sea routes are not straight lines, and road
    freight follows roads; a flat detour factor is cruder than routing but
    honest about being an approximation."""
    gc = great_circle(a, b)
    factor = {"sea": 1.35, "road": 1.25, "rail": 1.20, "air": 1.05}[mode]
    return gc * factor


class Model:
    def __init__(self, item, origin, dest, mode=None, life=None):
        if item not in PRODUCTS:
            raise SystemExit(f"unknown item: {item}")
        for r in (origin, dest):
            if r not in REGIONS:
                raise SystemExit(f"unknown region: {r}")
        self.p = PRODUCTS[item]
        self.item = item
        self.origin, self.dest = origin, dest
        self.mode = mode or self.p["transport_mode"]
        self.grid_o = REGIONS[origin]["grid"]
        self.grid_d = REGIONS[dest]["grid"]
        self.km = route_km(origin, dest, self.mode)
        self.cut = 0.0            # emissions dropped below the cutoff
        # Capital goods are charged to one unit of use as one part in a
        # lifetime. Those lifetimes are assumptions rather than measurements,
        # so they are a parameter here and a control in the visualiser; the
        # default reproduces every published figure exactly.
        lt = self.p.get("lifetime")
        self.life_scale = (lt["default"] / life) if (lt and life) else 1.0
        self.life_stages = set(lt["stages"]) if lt else set()

    # ---------------------------------------------------------------- core --
    def factor(self, pid):
        """Direct emissions of one unit of a process, before its inputs."""
        pr = PROCESSES[pid]
        if pr.get("grid_scaled"):
            return self.grid_d if pr.get("consumer_grid") else self.grid_o
        return pr["direct"]

    def expand(self, pid, amount, alloc, depth, total_hint):
        """Recursively expand one process into a node with children.

        `amount` is how many units of this process our functional unit needs.
        `alloc` is the product of every allocation factor between here and the
        product, so it is what actually reaches us.
        """
        # A transport mode used as an input carries kilometers, not units of a
        # process. One kilogram is a thousandth of a tonne, so kilometers
        # become tonne-kilometers by dividing by a thousand.
        if pid in TRANSPORT:
            tm = TRANSPORT[pid]
            e = tm["ef"] * (amount / 1000.0) * alloc
            return {"id": pid, "name": tm["name"], "unit": "km",
                    "amount": amount, "alloc": alloc, "direct": e,
                    "total": e, "children": [], "quality": "A",
                    "note": f"{amount:,.0f} km at {tm['ef']} kg CO2e per "
                            f"tonne-kilometer. {tm['note']}"}
        pr = PROCESSES[pid]
        direct = self.factor(pid) * amount * alloc
        node = {
            "id": pid, "name": pr["name"], "unit": pr["unit"],
            "amount": amount, "alloc": alloc,
            "direct": direct, "note": pr.get("note", ""),
            "quality": pr.get("quality", "B"),
            "children": [],
        }
        if depth < MAX_DEPTH:
            for cid, camt, calloc in pr.get("inputs", []):
                child_alloc = alloc * calloc
                # cheap look-ahead so a whole subtree can be dropped at once
                if cid in TRANSPORT:
                    rough = abs(TRANSPORT[cid]["ef"] * camt / 1000.0 *
                                amount * child_alloc)
                else:
                    rough = abs(self.factor(cid) * camt * amount * child_alloc)
                if total_hint and rough < CUTOFF * total_hint:
                    self.cut += rough
                    continue
                node["children"].append(
                    self.expand(cid, camt * amount, child_alloc,
                                depth + 1, total_hint))
        node["total"] = direct + sum(c["total"] for c in node["children"])
        return node

    def transport_node(self, mult, alloc, amount):
        """The freight leg. `mult` is everything that scales the emission
        (share x amortisation x waste scale x kilograms shipped); `alloc` is
        the share x amortisation that reaches the product, reported the same
        way every other node reports it; `amount` is the tonne-kilometers
        actually moved for one functional unit."""
        t = TRANSPORT[self.mode]
        kgco2 = t["ef"] * (self.km / 1000.0) * mult
        return {
            "id": "freight_" + self.mode, "name": t["name"],
            "unit": "tonne-km", "amount": amount, "alloc": alloc,
            "direct": kgco2, "total": kgco2, "children": [],
            "quality": "A",
            "note": (f"{self.km:,.0f} km by {t['name']} at {t['ef']} kg CO2e "
                     f"per tonne-kilometer. {t['note']}"),
        }

    def run(self, two_pass=True):
        """Build the spine. The first pass exists only to learn the total, so
        the cutoff can be expressed as a share of it rather than an absolute
        number that would mean different things for a banana and a cow."""
        if two_pass:
            rough = self.run(two_pass=False)["total"]
        else:
            rough = 0.0
        self.cut = 0.0

        # To eat one kilogram you must produce more than one, because some is
        # lost between the field and the plate. Every stage before the bin is
        # therefore scaled by 1/(1 - waste). Leaving this out - which the first
        # version did - understates the whole chain by the loss fraction, which
        # for a tomato is nearly a fifth.
        w = self.p["waste_frac"]
        overproduce = 1.0 / (1.0 - w)

        spine = []
        for st in self.p["stages"]:
            # Three multipliers, three meanings (see processes.py): a
            # co-product share, a capital-good amortisation, and the mass
            # shipped on a freight leg. Share and amortisation reach every
            # node in the stage; the mass reaches only the freight node.
            share = st.get("share", 1.0)
            amort = st.get("amortise", 1.0)
            if st["id"] in self.life_stages:
                amort *= self.life_scale
            alloc = share * amort
            scale = 1.0 if st.get("waste") else overproduce
            kids = []
            if st.get("transport"):
                kg = st.get("freight_kg", 1.0)
                kids.append(self.transport_node(alloc * scale * kg, alloc,
                                                self.km / 1000.0 * kg * scale))
            for cid, camt, calloc in st["inputs"]:
                kids.append(self.expand(cid, camt * scale, alloc * calloc,
                                        1, rough))
            direct = st.get("direct", 0.0) * alloc * scale
            node = {
                "id": st["id"], "name": st["name"], "alloc": alloc,
                "direct": direct, "note": st.get("note", ""),
                "children": kids,
                "land_use": bool(st.get("land_use")),
                # the allocation basis travels with the number, so the
                # visualiser can say *which kind* of share this is
                "basis": st.get("basis", ""),
            }
            if st.get("waste"):
                # The wasted mass itself decays in landfill. Everything above
                # has already been scaled up to produce it.
                node["direct"] = (PROCESSES["landfill"]["direct"]
                                  * (overproduce - 1.0) * alloc)
                # The unit is the product's own: this model carries cars and
                # flights as well as food.
                node["note"] += (f" Losses run about {w:.0%} for this product, "
                                 f"so {overproduce:.2f} units leave the line "
                                 f"for every one that reaches the buyer, and "
                                 f"every stage above is scaled accordingly.")
            node["total"] = node["direct"] + sum(c["total"] for c in kids)
            spine.append(node)

        total = sum(s["total"] for s in spine)
        return {
            "item": self.item, "name": self.p["name"],
            "unit": self.p["unit"], "category": self.p["category"],
            "note": self.p["note"],
            "origin": self.origin, "origin_name": REGIONS[self.origin]["name"],
            "dest": self.dest, "dest_name": REGIONS[self.dest]["name"],
            "mode": self.mode, "km": self.km,
            "grid_origin": self.grid_o, "grid_dest": self.grid_d,
            "spine": spine, "total": total,
            "waste_frac": w, "overproduce": overproduce,
            "cut": self.cut, "cutoff": CUTOFF,
        }


# ------------------------------------------------------------ presentation --
def paths(node, prefix=None, out=None):
    """Every root-to-leaf path with its direct emissions, for ranking."""
    prefix = prefix or []
    out = out if out is not None else []
    here = prefix + [node["name"]]
    if node["direct"] != 0:
        out.append((here, node["direct"], node.get("alloc", 1.0)))
    for c in node["children"]:
        paths(c, here, out)
    return out


def show(res, top=14):
    print(f"\n{res['name']} - {res['unit']}")
    print(f"{res['origin_name']} to {res['dest_name']}, "
          f"{res['km']:,.0f} km by {TRANSPORT[res['mode']]['name']}")
    print(f"grid: {res['grid_origin']:.2f} kg/kWh at origin, "
          f"{res['grid_dest']:.2f} at destination")
    print(f"\n{'':2}TOTAL  {res['total']:8.2f} kg CO2e per {res['unit']}\n")

    print(f"  {'stage':26s} {'kg CO2e':>9s} {'share':>7s}  alloc")
    print("  " + "-" * 54)
    for s in res["spine"]:
        share = s["total"] / res["total"] * 100 if res["total"] else 0
        a = "" if abs(s["alloc"] - 1.0) < 1e-9 else f"x{s['alloc']:.2f}"
        print(f"  {s['name'][:26]:26s} {s['total']:9.3f} {share:6.1f}%  {a}")

    allp = []
    for s in res["spine"]:
        paths(s, [], allp)
    allp.sort(key=lambda x: -abs(x[1]))
    print(f"\n  the {top} largest individual sources")
    print("  " + "-" * 54)
    for names, val, alloc in allp[:top]:
        a = "" if abs(alloc - 1.0) < 1e-9 else f"  (x{alloc:.2f})"
        print(f"  {val:8.3f}  {' -> '.join(names)}{a}")

    if res["cut"]:
        print(f"\n  {res['cut']:.4f} kg CO2e dropped below the "
              f"{res['cutoff']:.2%} cutoff")


def build_site(path=None):
    """Precompute every item at its default route and write the visualiser."""
    data = {"regions": REGIONS, "transport": TRANSPORT, "runs": {}, "items": {}}
    for key, p in PRODUCTS.items():
        data["items"][key] = {
            "name": p["name"], "category": p["category"], "note": p["note"],
            "group": p.get("group", "Food"),
            "unit": p["unit"], "origin": p["default_origin"],
            "dest": p["default_dest"], "mode": p["transport_mode"],
        }
        res = Model(key, p["default_origin"], p["default_dest"]).run()
        data["runs"][key] = res

    # The page recomputes rather than looking answers up, so it needs the graph
    # itself. Precomputing every item against every origin and destination would
    # be 20 x 20 x 9 runs and would still only cover the combinations someone
    # thought of in advance.
    data["processes"] = PROCESSES
    data["products"] = PRODUCTS
    data["cutoff"] = CUTOFF
    data["max_depth"] = MAX_DEPTH

    # Coastlines for the globe. Simplified far below the atlas resolution
    # because this globe is drawn a third the size, and detail nobody can
    # resolve is only weight.
    coast = os.path.join(HERE, "data", "coast.json")
    data["coast"] = json.load(open(coast)) if os.path.exists(coast) else []

    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    for token, src in (("/*ENGINE*/", "engine.js"), ("/*SCENE*/", "scene.js")):
        code = open(os.path.join(HERE, src), encoding="utf-8").read()
        if token not in tpl:
            raise SystemExit(f"template.html has no {token} slot")
        tpl = tpl.replace(token, code)
    html = tpl.replace("/*DATA*/", json.dumps(data, ensure_ascii=False,
                                              separators=(",", ":")))
    out = path or os.path.join(HERE, "climate-cost.html")
    # newline="\n": site/.gitattributes declares eol=lf and Python text mode on Windows writes CRLF.
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print(f"visualiser written: {out} "
          f"({os.path.getsize(out)/1024:.0f} kB, self-contained)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--item", default="tomato_field")
    ap.add_argument("--from", dest="origin", default=None)
    ap.add_argument("--to", dest="dest", default=None)
    ap.add_argument("--mode", default=None, choices=list(TRANSPORT))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="one line per item at its default route")
    a = ap.parse_args()

    if a.list:
        print("\nitems")
        for k, p in PRODUCTS.items():
            print(f"  {k:20s} {p['name']:32s} {p['category']}")
        print("\nregions")
        for k, r in REGIONS.items():
            print(f"  {k:7s} {r['name']:16s} grid {r['grid']:.2f} kg/kWh")
        print("\ntransport")
        for k, t in TRANSPORT.items():
            print(f"  {k:6s} {t['name']:22s} {t['ef']:6.3f} kg/tonne-km")
        return 0

    if a.build:
        build_site()
        return 0

    if a.all:
        print(f"\n  {'item':26s} {'kg CO2e':>9s}  route")
        print("  " + "-" * 62)
        rows = []
        for k, p in PRODUCTS.items():
            r = Model(k, p["default_origin"], p["default_dest"]).run()
            rows.append((r["total"], p["name"], r))
        for tot, name, r in sorted(rows, key=lambda x: -x[0]):
            print(f"  {name[:26]:26s} {tot:9.2f}  "
                  f"{r['origin_name']} to {r['dest_name']}")
        return 0

    p = PRODUCTS[a.item]
    res = Model(a.item, a.origin or p["default_origin"],
                a.dest or p["default_dest"], a.mode).run()
    show(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
