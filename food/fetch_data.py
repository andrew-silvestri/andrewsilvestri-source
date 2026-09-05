"""
Fetch USDA SR Legacy and reduce it to the columns this project reads.

One public-domain download, pinned by hash. SR Legacy is the final (April
2018) release of the Standard Reference database, frozen since, so the hash
is expected to hold; if USDA re-hosts the file and it changes, the build stops
here rather than computing on a table nobody checked.

Writes data/sr_legacy_slim.csv: one row per food with the six nutrient
amounts per 100 g that the rules need. The raw zip stays in data/raw/, which
the code archive skips.

Run:  python3 fetch_data.py
"""

import csv
import hashlib
import io
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "sr_legacy_slim.csv")

URL = ("https://fdc.nal.usda.gov/fdc-datasets/"
       "FoodData_Central_sr_legacy_food_csv_2018-04.zip")
SHA256 = "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0"
ZIP = os.path.join(RAW, "FoodData_Central_sr_legacy_food_csv_2018-04.zip")
PREFIX = "FoodData_Central_sr_legacy_food_csv_2018-04/"

# FoodData Central nutrient ids. Sugar has two ids in SR Legacy: 2000 is
# "Sugars, Total" and 1063 "Sugars, Total NLEA"; an item carries one or the
# other, so the slim table takes 2000 and falls back to 1063.
NUTRIENTS = {"1008": "kcal", "1004": "fat_g", "1005": "carb_g",
             "1003": "protein_g", "2000": "sugar_g", "1063": "sugar_nlea_g",
             "1079": "fibre_g", "1093": "sodium_mg"}


def fetch():
    os.makedirs(RAW, exist_ok=True)
    if not os.path.exists(ZIP):
        print(f"  downloading {URL}")
        urllib.request.urlretrieve(URL, ZIP)
    h = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()
    if h != SHA256:
        sys.exit(f"  SHA-256 mismatch for {ZIP}\n    got      {h}\n"
                 f"    expected {SHA256}\n  The pinned release has changed; "
                 f"nothing was written.")
    print(f"  {os.path.basename(ZIP)} verified")


def slim():
    z = zipfile.ZipFile(ZIP)

    def rows(name):
        return csv.DictReader(io.TextIOWrapper(z.open(PREFIX + name),
                                               encoding="utf-8"))

    cats = {r["id"]: r["description"] for r in rows("food_category.csv")}
    foods = {}
    for r in rows("food.csv"):
        foods[r["fdc_id"]] = {"fdc_id": r["fdc_id"],
                              "description": r["description"],
                              "group": cats.get(r["food_category_id"], "")}
    for r in rows("food_nutrient.csv"):
        col = NUTRIENTS.get(r["nutrient_id"])
        if col and r["fdc_id"] in foods:
            foods[r["fdc_id"]][col] = r["amount"]
    cols = ["fdc_id", "description", "group"] + list(NUTRIENTS.values())
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in sorted(foods.values(), key=lambda f: int(f["fdc_id"])):
            w.writerow({c: f.get(c, "") for c in cols})
    print(f"  {len(foods):,} foods -> {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    fetch()
    slim()
