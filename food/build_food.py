"""
Fat, sugar, salt: what prepared food has that raw food does not.

Applies the published hyper-palatable-food rules (Fazzino, Rohde & Sullivan,
Obesity 2019) to every solid food in USDA SR Legacy, splits the table into
raw and prepared by a stated rule, and asks whether the separation the two
groups show in fat-sugar space is a fact about food or an artefact of the
axes. Three nulls answer that. Everything on the page is read from the
payload this writes; nothing is typed.

Reads  data/sr_legacy_slim.csv   (fetch_data.py)
Writes outputs/food_payload.json
       outputs/items.csv          one row per food with its shares and flags

Run:  python3 build_food.py
"""

import collections
import csv
import json
import os
import random
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "sr_legacy_slim.csv")
OUT = os.path.join(HERE, "outputs")

# --- the published rules ---------------------------------------------------
# Fazzino TL, Rohde K, Sullivan DK. Hyper-palatable foods: development of a
# quantitative definition and application to the US food system database.
# Obesity 2019;27(11):1761-1768. doi:10.1002/oby.22639, Table 1.
# Fat, sugar and carbohydrate are per cent of energy (9 and 4 kcal/g); sodium
# is grams of sodium per gram of food, here as a percentage by weight.
# Carbohydrate in the CSOD rule is total carbohydrate minus fibre minus sugar.
RULES = {
    "FS":   {"name": "fat and sugar",         "fat_pct_kcal": 20, "sugar_pct_kcal": 20},
    "FSOD": {"name": "fat and sodium",        "fat_pct_kcal": 25, "sodium_pct_wt": 0.30},
    "CSOD": {"name": "carbohydrate and sodium", "carb_pct_kcal": 40, "sodium_pct_wt": 0.20},
}
SOURCE_RULES = ("Fazzino, Rohde & Sullivan, Obesity 27(11):1761-1768, 2019, "
                "doi:10.1002/oby.22639, Table 1")

# --- the page's own rule: what counts as raw, what counts as prepared ------
# Assumed. USDA has no processing field; "raw" in the description is the
# only marker of a food as grown or slaughtered, and USDA applies it to raw
# sausage and salted frozen egg too, so those words exclude an item.
RAW_EXCLUDE = ("sausage", "cured", "salted", "sugared", "bockwurst", "chorizo",
               "added solution", "enhanced")   # brine-injected pork is sold as "raw"
PREPARED_GROUPS = (
    "Snacks", "Sweets", "Baked Products", "Fast Foods", "Breakfast Cereals",
    "Sausages and Luncheon Meats", "Restaurant Foods",
    "Meals, Entrees, and Side Dishes", "Soups, Sauces, and Gravies",
    "Branded Food Products Database",
)
# The rules are for solids (Fazzino 2019 excluded 933 beverages and infant
# formulas), so the two beverage groups are out; so is USDA's QC material.
DROP_GROUPS = ("Beverages", "Alcoholic Beverages", "Quality Control Materials")
KCAL_FLOOR = 50          # kcal per 100 g; below it a % of energy is noise
SEED = 20260905
N_PERM = 1000
N_SIMPLEX = 200000

# Whole foods named on the plane. Names are chosen; positions are computed.
# Human milk is the one whole food the literature names as combining fat and
# sugar (DiFeliceantonio et al. 2018); it is a liquid, so it is outside the
# rule and is drawn, not counted.
NAMED_RAW = [
    ("coconut", "Nuts, coconut meat, raw"),
    ("avocado", "Avocados, raw, all commercial varieties"),
    ("medjool dates", "Dates, medjool"),
    ("banana", "Bananas, raw"),
    ("grape leaves", "Grape leaves, raw"),
    ("chicken leg", "Chicken, broilers or fryers, leg, meat and skin, raw"),
]
HUMAN_MILK = ("human milk", "Milk, human, mature, fluid")


def num(s):
    return float(s) if s not in ("", None) else None


def load():
    rows = []
    for r in csv.DictReader(open(DATA, encoding="utf-8")):
        kcal, fat, carb = num(r["kcal"]), num(r["fat_g"]), num(r["carb_g"])
        sugar = num(r["sugar_g"])
        if sugar is None:
            sugar = num(r["sugar_nlea_g"])
        na = num(r["sodium_mg"])
        fibre = num(r["fibre_g"])
        if None in (kcal, fat, carb, sugar, na) or kcal <= 0:
            continue
        fibre_missing = fibre is None
        fibre = fibre or 0.0
        pf = 900 * fat / kcal
        ps = 400 * sugar / kcal
        pc = 400 * max(carb - fibre - sugar, 0.0) / kcal
        napct = na / 1000.0                     # mg per 100 g -> % by weight
        d = r["description"]
        rows.append({
            "fdc_id": int(r["fdc_id"]), "description": d, "group": r["group"],
            "kcal": kcal, "fat_g": fat, "sugar_g": sugar, "carb_g": carb,
            "fibre_g": fibre, "fibre_missing": fibre_missing, "sodium_mg": na,
            "fat_pct_kcal": pf, "sugar_pct_kcal": ps, "carb_pct_kcal": pc,
            "sodium_pct_wt": napct,
        })
    return rows


def flag(r):
    R = RULES
    r["FS"] = r["fat_pct_kcal"] > R["FS"]["fat_pct_kcal"] and \
        r["sugar_pct_kcal"] > R["FS"]["sugar_pct_kcal"]
    r["FSOD"] = r["fat_pct_kcal"] > R["FSOD"]["fat_pct_kcal"] and \
        r["sodium_pct_wt"] >= R["FSOD"]["sodium_pct_wt"]
    r["CSOD"] = r["carb_pct_kcal"] > R["CSOD"]["carb_pct_kcal"] and \
        r["sodium_pct_wt"] >= R["CSOD"]["sodium_pct_wt"]
    r["HPF"] = r["FS"] or r["FSOD"] or r["CSOD"]


def classify(r):
    d = r["description"].lower()
    if r["group"] in DROP_GROUPS:
        return "dropped"
    if re.search(r"\braw\b", d):
        return "excluded" if any(w in d for w in RAW_EXCLUDE) else "raw"
    if r["group"] in PREPARED_GROUPS:
        return "prepared"
    return "other"


def in_fs(pf, ps):
    return pf > RULES["FS"]["fat_pct_kcal"] and ps > RULES["FS"]["sugar_pct_kcal"]


# --- null 1: shuffle within group, under the simplex ------------------------
def permutation_null(items, rng):
    """Keep each group's own marginals of fat % and sugar %; break the
    pairing. Sugar values are dealt to items in random order, each item
    taking a random value from those still consistent with fat + sugar <= 100
    (the constraint the axes impose). Sodium is shuffled the same way against
    fat and against carbohydrate; sodium has no simplex to respect."""
    pf = [r["fat_pct_kcal"] for r in items]
    ps = [r["sugar_pct_kcal"] for r in items]
    pc = [r["carb_pct_kcal"] for r in items]
    na = [r["sodium_pct_wt"] for r in items]
    fs, fsod, csod = [], [], []
    for _ in range(N_PERM):
        order = list(range(len(items)))
        rng.shuffle(order)
        pool = sorted(ps)
        n_fs = 0
        for i in order:
            f = pf[i]
            # pool is sorted, so the admissible values are a prefix
            lo, hi = 0, len(pool)
            while lo < hi:
                mid = (lo + hi) // 2
                if f + pool[mid] <= 100:
                    lo = mid + 1
                else:
                    hi = mid
            k = rng.randrange(lo) if lo else None
            s = pool.pop(k) if k is not None else 0.0
            if in_fs(f, s):
                n_fs += 1
        fs.append(n_fs)
        n1 = na[:]
        rng.shuffle(n1)
        fsod.append(sum(1 for f, x in zip(pf, n1)
                        if f > RULES["FSOD"]["fat_pct_kcal"]
                        and x >= RULES["FSOD"]["sodium_pct_wt"]))
        n2 = na[:]
        rng.shuffle(n2)
        csod.append(sum(1 for c, x in zip(pc, n2)
                        if c > RULES["CSOD"]["carb_pct_kcal"]
                        and x >= RULES["CSOD"]["sodium_pct_wt"]))

    def summ(v):
        return {"mean": statistics.mean(v), "min": min(v), "max": max(v),
                "counts": v}
    return {"FS": summ(fs), "FSOD": summ(fsod), "CSOD": summ(csod)}


# --- null 2: the simplex alone ---------------------------------------------
def simplex_null(rng):
    """Uniform over (fat, carbohydrate, protein) shares of energy, sugar a
    uniform fraction of carbohydrate: what share of arbitrary compositions
    the axes themselves put in the fat-and-sugar region."""
    n = 0
    for _ in range(N_SIMPLEX):
        a, b, c = (rng.expovariate(1.0) for _ in range(3))
        s = a + b + c
        pf, pcarb = 100 * a / s, 100 * b / s
        if in_fs(pf, rng.random() * pcarb):
            n += 1
    return n / N_SIMPLEX


# --- the pairs: the same food raw and prepared ------------------------------
PREP = re.compile(r"^(.*?),\s*(raw|cooked.*|canned.*|fried.*|roasted.*|"
                  r"baked.*|boiled.*)$")


def pairs(rows, by_group):
    """SR Legacy writes a food's preparations as suffixes of one base
    description. A base with a raw item and at least one prepared variant is
    a pair. USDA's "with salt" variants carry an imputed standard salt
    addition, not a measurement, and are left out."""
    base = collections.defaultdict(dict)
    for r in rows:
        m = PREP.match(r["description"])
        if m:
            base[m.group(1)][m.group(2)] = r
    out, n_with_salt = [], 0
    for b, v in base.items():
        raw = v.get("raw")
        if raw is None or by_group.get(raw["fdc_id"]) != "raw":
            continue
        if raw["kcal"] < KCAL_FLOOR:
            continue
        for prep, r in v.items():
            if prep == "raw" or r["kcal"] < KCAL_FLOOR:
                continue
            if "with salt" in prep or "with added salt" in prep:
                n_with_salt += 1
                continue
            out.append({"base": b, "prep": prep, "raw_id": raw["fdc_id"],
                        "prep_id": r["fdc_id"],
                        "raw": [raw["fat_pct_kcal"], raw["sodium_pct_wt"]],
                        "prepared": [r["fat_pct_kcal"], r["sodium_pct_wt"]],
                        "raw_FSOD": raw["FSOD"], "prep_FSOD": r["FSOD"],
                        "raw_HPF": raw["HPF"], "prep_HPF": r["HPF"]})
    return out, n_with_salt


def plain_name(desc):
    """A food's everyday name from a USDA description: the first piece,
    or the second where USDA leads with a class word (Nuts, Fish, ...)."""
    desc = re.sub(r"\s*\(.*?\)", "", desc)          # "(garbanzo beans, bengal gram)"
    parts = [p.strip() for p in desc.split(",")]
    if parts[0].lower() in ("nuts", "fish", "crustaceans", "mollusks", "seaweed") and len(parts) > 1:
        parts = parts[1:]
    return parts[0].lower()


def short(desc, n=30):
    """A USDA description cut to its first pieces, for a label."""
    parts = [p.strip() for p in desc.split(",")]
    s = parts[0]
    for p in parts[1:]:
        if len(s) + len(p) + 2 > n:
            break
        s += ", " + p
    return s.lower()


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(SEED)
    rows = load()
    for r in rows:
        flag(r)
        r["cls"] = classify(r)
    by_group = {r["fdc_id"]: r["cls"] for r in rows}
    sample = {c: [r for r in rows if r["cls"] == c] for c in
              ("raw", "prepared", "other", "excluded", "dropped")}
    R = [r for r in sample["raw"] if r["kcal"] >= KCAL_FLOOR]
    P = [r for r in sample["prepared"] if r["kcal"] >= KCAL_FLOOR]

    def counts(G):
        return {k: sum(1 for r in G if r[k]) for k in ("FS", "FSOD", "CSOD", "HPF")}

    obs = {"raw": counts(R), "prepared": counts(P)}
    below = {"raw": counts([r for r in sample["raw"] if r["kcal"] < KCAL_FLOOR]),
             "prepared": counts([r for r in sample["prepared"] if r["kcal"] < KCAL_FLOOR])}

    print(f"  raw {len(R)} (of {len(sample['raw'])}), prepared {len(P)} "
          f"(of {len(sample['prepared'])}), other {len(sample['other'])}, "
          f"excluded from raw {len(sample['excluded'])}, dropped {len(sample['dropped'])}")
    print(f"  observed raw {obs['raw']}  prepared {obs['prepared']}")

    # marginals, so the reader can see what independence would give
    def marg(G):
        n = len(G)
        return {"fat_gt20": sum(r["fat_pct_kcal"] > 20 for r in G) / n,
                "sugar_gt20": sum(r["sugar_pct_kcal"] > 20 for r in G) / n,
                "fat_gt25": sum(r["fat_pct_kcal"] > 25 for r in G) / n,
                "sodium_ge030": sum(r["sodium_pct_wt"] >= 0.30 for r in G) / n,
                "sodium_ge020": sum(r["sodium_pct_wt"] >= 0.20 for r in G) / n,
                "carb_gt40": sum(r["carb_pct_kcal"] > 40 for r in G) / n}
    marginals = {"raw": marg(R), "prepared": marg(P)}

    print("  permutation null ...")
    null = {"raw": permutation_null(R, rng), "prepared": permutation_null(P, rng)}
    for g in ("raw", "prepared"):
        s = null[g]["FS"]
        print(f"    {g:9s} FS observed {obs[g]['FS']}  null {s['mean']:.1f} [{s['min']}-{s['max']}]")
    simplex = simplex_null(rng)
    print(f"  simplex null: {simplex:.3f} of uniform compositions in the FS region")

    # null 3: grams, no simplex
    def mass(G, thr):
        return sum(1 for r in G if r["fat_g"] >= thr and r["sugar_g"] >= thr)
    mass_space = {str(t): {"raw": mass(R, t), "prepared": mass(P, t)} for t in (5, 10)}
    mass_named = {str(t): [plain_name(r["description"]) for r in R
                           if r["fat_g"] >= t and r["sugar_g"] >= t] for t in (5, 10)}

    # the exceptions the raw group does contain
    raw_hpf = [{"name": short(r["description"]), "kcal": r["kcal"],
                "fat_pct_kcal": r["fat_pct_kcal"], "sugar_pct_kcal": r["sugar_pct_kcal"],
                "sodium_pct_wt": r["sodium_pct_wt"],
                "rules": [k for k in ("FS", "FSOD", "CSOD") if r[k]],
                "above_floor": r["kcal"] >= KCAL_FLOOR}
               for r in sample["raw"] if r["HPF"]]

    # by SR food group, above the floor, groups large enough to say anything
    groups = []
    for g in sorted({r["group"] for r in rows if r["cls"] != "dropped"}):
        G = [r for r in rows if r["group"] == g and r["kcal"] >= KCAL_FLOOR
             and r["cls"] != "dropped"]
        Rg = [r for r in G if r["cls"] == "raw"]
        if len(G) < 20:
            continue
        groups.append({"group": g, "n": len(G),
                       "share_hpf": sum(r["HPF"] for r in G) / len(G),
                       "n_raw": len(Rg),
                       "share_hpf_raw": (sum(r["HPF"] for r in Rg) / len(Rg)) if len(Rg) >= 5 else None})
    groups.sort(key=lambda d: -d["share_hpf"])

    # pairs
    pr, n_with_salt = pairs(rows, by_group)
    flips = [p for p in pr if not p["raw_FSOD"] and p["prep_FSOD"]]
    flips_any = [p for p in pr if not p["raw_HPF"] and p["prep_HPF"]]
    print(f"  pairs {len(pr)} (with-salt variants left out: {n_with_salt}); "
          f"raw->FSOD flips {len(flips)}, raw->any-rule flips {len(flips_any)}")

    # named points: positions computed, names chosen
    by_desc = {r["description"]: r for r in rows}
    named_raw = []
    for label, desc in NAMED_RAW:
        r = by_desc.get(desc)
        if r is None:
            raise SystemExit(f"named food not in SR Legacy: {desc!r}")
        named_raw.append({"label": label, "description": desc,
                          "fat_pct_kcal": r["fat_pct_kcal"],
                          "sugar_pct_kcal": r["sugar_pct_kcal"],
                          "sodium_pct_wt": r["sodium_pct_wt"], "kcal": r["kcal"],
                          "cls": r["cls"]})
    hm = by_desc[HUMAN_MILK[1]]
    human_milk = {"label": HUMAN_MILK[0], "description": HUMAN_MILK[1],
                  "fat_pct_kcal": hm["fat_pct_kcal"], "sugar_pct_kcal": hm["sugar_pct_kcal"],
                  "sodium_pct_wt": hm["sodium_pct_wt"], "kcal": hm["kcal"],
                  "in_FS_region": in_fs(hm["fat_pct_kcal"], hm["sugar_pct_kcal"])}
    # prepared side: the item nearest the centroid of each of the three
    # largest prepared groups, so the names are picked by rule
    named_prepared = []
    big = collections.Counter(r["group"] for r in P).most_common(3)
    for g, _ in big:
        G = [r for r in P if r["group"] == g]
        cx = statistics.mean(r["fat_pct_kcal"] for r in G)
        cy = statistics.mean(r["sugar_pct_kcal"] for r in G)
        r = min(G, key=lambda r: (r["fat_pct_kcal"] - cx) ** 2 + (r["sugar_pct_kcal"] - cy) ** 2)
        named_prepared.append({"label": short(r["description"], 30), "group": g,
                               "description": r["description"],
                               "fat_pct_kcal": r["fat_pct_kcal"],
                               "sugar_pct_kcal": r["sugar_pct_kcal"]})

    # looked-up values, each with its source
    looked_up = {
        "rules": {"value": RULES, "source": SOURCE_RULES},
        "derivation": {"value": {"papers": 14, "foods": 75, "clusters": 3,
                                 "quote": "should not be assumed to be fixed or final"},
                       "source": "Fazzino, Rohde & Sullivan 2019, Methods and Discussion"},
        "fndds_2015_16": {"value": {"items_analysed": 7757, "share_hpf": 0.62,
                                    "of_hpf_FSOD": 0.70, "of_hpf_FS": 0.25, "of_hpf_CSOD": 0.16,
                                    "reduced_items": 443, "reduced_share_hpf": 0.49,
                                    "raw_vegetables_not_captured": 0.97},
                          "source": "Fazzino, Rohde & Sullivan 2019, Results and Tables 3-5"},
        "time_series": {"value": [{"year": 1988, "items": 6216, "share_hpf": 0.49},
                                  {"year": 2001, "items": 6125, "share_hpf": 0.62},
                                  {"year": 2018, "items": 6081, "share_hpf": 0.69}],
                        "reformulation_odds_2018": 4,
                        "source": "Demeke, Rohde, Chollet-Hinton, Sutton, L'Insalata & Fazzino, "
                                  "Public Health Nutrition 26(1):182-189, 2023, doi:10.1017/S1368980022001227"},
        "upf_overlap": {"value": "40-70%",
                        "source": "Sutton, Stratton, L'Insalata & Fazzino, Obesity 32(1):166-175, 2024, doi:10.1002/oby.23897"},
        "shelf_share": {"value": 0.671, "purchases_share": 0.594,
                        "source": "Fazzino, Bristi, Chollet-Hinton & Sutton, Public Health Nutrition 29(1):e110, 2026, doi:10.1017/S1368980026102614"},
        "rogers_2024": {"value": {"foods": 52, "raters_per_food": "72-224", "p_min": 0.41},
                        "source": "Rogers, Vural, Flynn & Brunstrom, Appetite 201:107596, 2024, doi:10.1016/j.appet.2024.107596"},
        "finlayson_2025": {"value": {"foods": 436, "raters": 3364, "liking_explained": 0.20},
                           "source": "Finlayson et al., Appetite 213:108029, 2025"},
        "difeliceantonio_2018": {"value": {"n": 206},
                                 "source": "DiFeliceantonio et al., Cell Metabolism 28(1):33-44, 2018, doi:10.1016/j.cmet.2018.05.018"},
        "moskowitz_1974": {"source": "Moskowitz, Kluter, Westerling & Jacobs, Science 184(4136):583-585, 1974"},
        "sadler_2015": {"source": "Sadler, McNulty & Gibson, Critical Reviews in Food Science and Nutrition 55(3):338-356, 2015"},
    }
    assumed = [
        {"key": "raw_rule", "text": "a food is raw if USDA's description says raw, unless it also says "
                                    + ", ".join(RAW_EXCLUDE)},
        {"key": "prepared_rule", "text": "a food is prepared if it is in one of these SR Legacy groups: "
                                         + "; ".join(PREPARED_GROUPS)},
        {"key": "kcal_floor", "text": f"foods under {KCAL_FLOOR} kcal per 100 g are left out of every count"},
        {"key": "beverages", "text": "the two beverage groups are left out, as the rules' authors left out liquids"},
        {"key": "fibre", "text": "fibre is taken as zero where SR Legacy has no value"},
        {"key": "sr_legacy", "text": "SR Legacy, frozen in April 2018, stands for the US food supply"},
        {"key": "with_salt", "text": "USDA's 'cooked, with salt' variants carry an imputed standard salt addition and are left out of the pairs"},
    ]

    payload = {
        "generated_from": "USDA FoodData Central, SR Legacy, April 2018 release (CC0)",
        "seed": SEED, "n_perm": N_PERM, "n_simplex": N_SIMPLEX, "kcal_floor": KCAL_FLOOR,
        "rules": RULES, "raw_exclude": list(RAW_EXCLUDE), "prepared_groups": list(PREPARED_GROUPS),
        "drop_groups": list(DROP_GROUPS),
        "n": {"loaded": len(rows), "raw_all": len(sample["raw"]), "raw": len(R),
              "prepared_all": len(sample["prepared"]), "prepared": len(P),
              "other": len(sample["other"]), "excluded_from_raw": len(sample["excluded"]),
              "dropped": len(sample["dropped"]),
              "fibre_missing": sum(1 for r in rows if r["fibre_missing"] and r["cls"] in ("raw", "prepared")),
              "with_salt_left_out": n_with_salt},
        "observed": obs, "below_floor": below, "marginals": marginals,
        "null_permutation": null, "null_simplex_share": simplex,
        "null_mass": {"counts": mass_space, "raw_named": mass_named},
        "raw_hpf_items": raw_hpf, "groups": groups,
        "pairs": pr, "n_pairs": len(pr), "n_flips_fsod": len(flips), "n_flips_any": len(flips_any),
        "named_raw": named_raw, "human_milk": human_milk, "named_prepared": named_prepared,
        "looked_up": looked_up, "assumed": assumed,
    }
    json.dump(payload, open(os.path.join(OUT, "food_payload.json"), "w", encoding="utf-8"),
              indent=1)
    cols = ["fdc_id", "description", "group", "cls", "kcal", "fat_g", "sugar_g", "carb_g",
            "fibre_g", "sodium_mg", "fat_pct_kcal", "sugar_pct_kcal", "carb_pct_kcal",
            "sodium_pct_wt", "FS", "FSOD", "CSOD", "HPF"]
    with open(os.path.join(OUT, "items.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: (round(r[c], 4) if isinstance(r[c], float) else r[c]) for c in cols})
    print(f"  wrote outputs/food_payload.json and outputs/items.csv")


if __name__ == "__main__":
    main()
