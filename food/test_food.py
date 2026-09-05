"""
The failure modes this project is exposed to.

1. The raw group leaks. USDA files raw sausage, salted frozen egg and
   brine-injected pork under "raw"; if the exclusion words stop matching,
   processed items enter the raw group and the exclusion the page reports is
   diluted. Fails if any raw item's description carries an exclusion word.
2. The known exception disappears. Human milk is the one whole food the
   literature names as combining fat and sugar; it must be above both lines
   and must not be counted in the raw group (it is a liquid).
3. The null does not reproduce. The page quotes the permutation null's mean
   and range; a fresh generator with the recorded seed must give the same.
4. The pairs figure carries imputed salt. USDA's "with salt" variants are
   left out by rule; none may be in the payload.
5. The page and the payload disagree. Rendering the template from the
   payload must give the shipped page byte for byte.
6. Every raw food the page calls an exception is actually one, and every
   raw food above the lines is listed.

Run:  python3 test_food.py
"""

import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_food as B                                    # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "food_payload.json")
ITEMS = os.path.join(HERE, "outputs", "items.csv")
PAGE = os.path.join(HERE, "..", "site", "food.html")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    items = list(csv.DictReader(open(ITEMS, encoding="utf-8")))
    fails = []

    # 1. the raw group holds nothing the exclusion words name
    leaks = [r["description"] for r in items if r["cls"] == "raw"
             and any(w in r["description"].lower() for w in P["raw_exclude"])]
    if leaks:
        fails.append(f"raw group leaks {len(leaks)} item(s): {leaks[:3]}")
    print(f"  1. raw group: {sum(r['cls'] == 'raw' for r in items)} items, {len(leaks)} leaks")

    # 2. human milk: above both lines, and not counted
    hm = P["human_milk"]
    hm_row = next(r for r in items if r["description"] == hm["description"])
    if not hm["in_FS_region"]:
        fails.append("human milk is not above both fat-and-sugar lines")
    if hm_row["cls"] == "raw":
        fails.append("human milk is counted in the raw group; it is a liquid and must not be")
    print(f"  2. human milk: fat {hm['fat_pct_kcal']:.0f}%, sugar {hm['sugar_pct_kcal']:.0f}%, "
          f"class {hm_row['cls']!r}")

    # 3. the permutation null reproduces from the recorded seed
    rows = B.load()
    for r in rows:
        B.flag(r)
        r["cls"] = B.classify(r)
    R = [r for r in rows if r["cls"] == "raw" and r["kcal"] >= P["kcal_floor"]]
    rng = random.Random(P["seed"])
    null = B.permutation_null(R, rng)["FS"]
    rec = P["null_permutation"]["raw"]["FS"]
    if (null["mean"], null["min"], null["max"]) != (rec["mean"], rec["min"], rec["max"]):
        fails.append(f"raw permutation null does not reproduce: got "
                     f"{null['mean']:.2f} [{null['min']}-{null['max']}], recorded "
                     f"{rec['mean']:.2f} [{rec['min']}-{rec['max']}]")
    print(f"  3. permutation null, raw: mean {null['mean']:.1f} [{null['min']}-{null['max']}], "
          f"recorded {rec['mean']:.1f} [{rec['min']}-{rec['max']}]")

    # 4. no imputed-salt variant in the pairs
    salted = [p for p in P["pairs"] if "with salt" in p["prep"] or "with added salt" in p["prep"]]
    if salted:
        fails.append(f"{len(salted)} 'with salt' variant(s) in the pairs")
    print(f"  4. pairs: {len(P['pairs'])}, with-salt variants inside: {len(salted)}")

    # 5. the page is what the payload says
    import update_page
    rendered, probs = update_page.cite(update_page.render(P))
    shipped = open(PAGE, encoding="utf-8").read()
    if probs:
        fails.append("citations: " + "; ".join(probs))
    if rendered != shipped:
        fails.append("site/food.html differs from the template rendered from the payload")
    print(f"  5. page: {'matches' if rendered == shipped else 'DIFFERS from'} the payload")

    # 6. the exceptions list is exactly the raw items above the lines
    listed = {e["name"] for e in P["raw_hpf_items"]}
    actual = {B.short(r["description"]) for r in rows if r["cls"] == "raw" and r["HPF"]}
    if listed != actual:
        fails.append(f"exception list {sorted(listed)} != raw items above the lines {sorted(actual)}")
    above = [e for e in P["raw_hpf_items"] if e["above_floor"]]
    if len(above) != P["observed"]["raw"]["HPF"]:
        fails.append("exceptions above the floor do not match the observed raw count")
    print(f"  6. raw exceptions: {len(listed)} listed, {len(above)} above the floor")

    if fails:
        print("\nFAIL")
        for f in fails:
            print("  - " + f)
        return 1
    print("\nok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
