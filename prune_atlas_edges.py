"""
Remove links the model should never have drawn.

The climate layer is wired to the historical disaster record, which is right
for the disaster types the climate actually drives -- storms, floods, droughts,
wildfires, heat extremes -- and wrong for the ones it does not. The global
temperature was linked to eighty earthquakes. Tracing the strongest route out
of a climate forcing ran

    Climate system -> Global temperature -> Japan Earthquake 2011 -> JPN grid

which is a false causal claim sitting in the middle of the model's headline
example. Plate tectonics does not read the temperature record.

Those edges come from the v5 core, three build generations back. This runs on
the built payload instead, so it applies whatever produced the file.

Run:  python3 prune_atlas_edges.py            report only
      python3 prune_atlas_edges.py --apply
"""

import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")

# Disaster types with no causal path from the temperature record.
TECTONIC = re.compile(r"\b(earthquake|tsunami|volcan|landslide|"
                      r"mass movement)\b", re.I)
# USGS quake nodes are named "M6.9 12 km ENE of ...".
USGS = re.compile(r"^M\d")
CLIMATE_SOURCES = {"GLOBAL_TEMP", "CLIMATE_SYS"}


def load():
    raw = open(DATA, encoding="utf-8").read()
    head = raw[:raw.index("=") + 1]
    return head, json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def tectonic(name):
    return bool(TECTONIC.search(name) or USGS.match(name))


def main(apply=False):
    head, D = load()
    name = D["name"]
    kind = [D["kinds"][k] for k in D["kind"]]
    inv = {int(v): k for k, v in D["idMap"].items()}

    drop = []
    for e, (s, t) in enumerate(zip(D["es"], D["et"])):
        if inv.get(s) in CLIMATE_SOURCES and kind[t] == "event" \
                and tectonic(name[t]):
            drop.append(e)
        # and the same link written the other way round
        elif inv.get(t) in CLIMATE_SOURCES and kind[s] == "event" \
                and tectonic(name[s]):
            drop.append(e)

    print(f"  {len(D['es']):,} links, {len(drop):,} to remove")
    for e in drop[:4]:
        print(f"    {name[D['es'][e]][:34]:<34} -> {name[D['et'][e]][:40]}")
    if len(drop) > 4:
        print(f"    ... and {len(drop) - 4:,} more")

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return

    keep = sorted(set(range(len(D["es"]))) - set(drop))
    for f in ("es", "et", "ew"):
        D[f] = [D[f][i] for i in keep]

    # A node that only ever had one of these links is now isolated. Report it
    # rather than silently changing the connectivity figure the page quotes.
    deg = [0] * D["n"]
    for s, t in zip(D["es"], D["et"]):
        deg[s] += 1
        deg[t] += 1
    iso = sum(1 for d in deg if d == 0)
    print(f"  {len(D['es']):,} links remain, {iso:,} isolated nodes "
          f"({100 * iso / D['n']:.2f}%)")

    open(DATA, "w", encoding="utf-8").write(
        head + json.dumps(D, separators=(",", ":")) + ";")
    print("  written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
