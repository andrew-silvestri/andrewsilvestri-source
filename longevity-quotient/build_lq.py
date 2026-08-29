"""
Longevity Quotient — allometric model, taxonomic aggregation, and visualiser.

LQ is defined by analogy with the encephalisation quotient. A species'
observed lifespan is divided by the lifespan predicted for an animal of its
body mass, where the prediction comes from an ordinary least squares fit of

    log10(L) = a + b * log10(M)

L is maximum lifespan in years, M is adult body mass in grams. LQ = 1 means the
species lives exactly as long as its mass predicts.

Two baselines are computed.

  LQ_global  fit over every species in the table
  LQ_class   fit within the species' own group, where that group is large
             enough and the fit is sound

The group baseline is the more meaningful of the two. Birds live roughly twice
as long as mammals of equal mass, so a global fit charges every bird a bonus it
did not earn and every mammal a penalty. The global fit is kept because it is
what most casual presentations of this idea actually mean.

Colonial organisms are excluded from every fit. A 4,265-year black coral or an
11,000-year glass sponge is a colony age, not the lifespan of an individual;
including them would drag the invertebrate baseline into nonsense. They are
still carried in the data and shown in the visualiser, flagged as colonial.

Run:
    python3 build_lq.py

Writes outputs/ figures, outputs/lq_table.csv, outputs/group_summary.csv,
outputs/summary.json, and the self-contained longevity.html visualiser.
"""

import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# The merged table is the model of record when it exists. The hand-checked
# seed is kept beside it and is still the highest-precedence source inside the
# merge, so this is a widening rather than a replacement - and if the merge has
# never been run, the seed alone still builds a working model.
_SEED = os.path.join(HERE, "data", "animals.csv")
_MERGED = os.path.join(HERE, "data", "animals_merged.csv")
DATA = _MERGED if os.path.exists(_MERGED) else _SEED
OUT = os.path.join(HERE, "outputs")

# The site palette. Black is not in it: these figures are read on a
# dark page, and a black rule or marker on that page is invisible.
INK, DIM = "#e3e6f2", "#8b93b0"

MIN_CLASS_N = 6
MIN_CLASS_R2 = 0.15

# Regression weights by data grade.
#
# Maximum longevity is a record, not a rate, so it scales with how hard anyone
# looked. A well-banded species accumulates a long maximum; an obscure one keeps
# whatever its single recaptured individual gave. That noise should not set the
# baseline everything else is measured against.
#
# The first attempt at fixing this simply dropped the uncertain grades. It made
# things worse. AnAge's sample size tracks how charismatic and tractable an
# animal is rather than anything about ageing, so the dropped records skewed
# small-bodied and short-lived: at 3,334 species, filtering moved the mammal
# slope from 0.158 to 0.120 — away from the 0.15-0.20 the comparative
# literature reports — and shifted every class quotient below 1.0 at once.
# Deleting a third of a sample is a large intervention and it was not a random
# third.
#
# Three strategies are available, and which one is right is an empirical
# question rather than a matter of taste. It was settled by simulation: build a
# table with a known slope, mark a third of it grade C, depress those lifespans
# by the sampling artefact, and see which method recovers the slope that was put
# in. Repeated with grade-C records skewed small-bodied, large-bodied, and not
# skewed at all:
#
#     C records skew     unweighted   hard filter   weighted    truth
#     small-bodied            0.199         0.160      0.175    0.160
#     large-bodied            0.120         0.160      0.146    0.160
#     no mass skew            0.171         0.160      0.164    0.160
#
# The hard filter recovers the truth exactly in every case; weighting gets 3-9%
# of the way wrong; leaving the artefact in costs up to 25%. The reason is that
# grade C marks a *bias*, not merely noise: those lifespans are systematically
# depressed by low sampling effort. Down-weighting a bias still lets it through.
# Deleting it does not.
#
# So "filter" is the default. "weighted" and "none" are kept because the
# simulation encodes an assumption — that the grade-C depression is roughly
# multiplicative and independent of mass — and it is worth being able to check
# what happens if that assumption is wrong. Choose with --weights.
FIT_STRATEGY = "filter"          # filter | weighted | none
QUALITY_WEIGHT = {"A": 1.0, "B": 0.5, "C": 0.2}
DEFAULT_WEIGHT = 0.5
EXCLUDE_GRADES = {"C"}

RANKS = ["kingdom", "phylum", "class", "order", "family", "genus"]

# Classes are pooled into baseline groups. Fish classes are combined because
# separately they are too thin to fit; the many small invertebrate classes are
# combined for the same reason. The pooling is coarse and is declared as such
# on the page.
FISH = {"Actinopterygii", "Chondrichthyes", "Sarcopterygii",
        "Petromyzontida", "Myxini", "Dipnoi"}
VERT = {"Mammalia", "Aves", "Reptilia", "Amphibia"}

# Different sources use different, equally valid taxonomies. AnAge carries the
# older fish classes (Teleostei, Chondrostei, Holostei) that modern usage folds
# into Actinopterygii, and the older mammal orders (Soricomorpha,
# Erinaceomorpha) that fold into Eulipotyphla. Left alone these fragment the
# groups: a merged table splits into an "Actinopterygii" group of 32 and a
# "Teleostei" group of 329 that ought to be one, and — worse — every class this
# file does not recognise falls into the invertebrate baseline, so 348 fish end
# up being told what an invertebrate of their mass should live.
#
# Names are normalised on load, from whichever source. The canonical form is
# the modern one.
CLASS_SYNONYM = {
    "Teleostei": "Actinopterygii",
    "Chondrostei": "Actinopterygii",
    "Holostei": "Actinopterygii",
    "Actinopteri": "Actinopterygii",
    "Neopterygii": "Actinopterygii",
    "Coelacanthi": "Sarcopterygii",
    "Actinistia": "Sarcopterygii",
    "Elasmobranchii": "Chondrichthyes",
    "Holocephali": "Chondrichthyes",
    "Cephalaspidomorphi": "Petromyzontida",
    "Hyperoartia": "Petromyzontida",
    "Petromyzonti": "Petromyzontida",
    "Insecta ": "Insecta",
    "Secernentea": "Chromadorea",
    "Reptilia ": "Reptilia",
}

ORDER_SYNONYM = {
    "Soricomorpha": "Eulipotyphla",
    "Erinaceomorpha": "Eulipotyphla",
    "Insectivora": "Eulipotyphla",
    "Cetacea": "Artiodactyla",
    "Cetartiodactyla": "Artiodactyla",
    "Caudata": "Urodela",
    "Crocodylia": "Crocodilia",
    "Struthioniformes ": "Struthioniformes",
    "Scorpaeniformes": "Perciformes",
    "Perciformes ": "Perciformes",
    "Trachichthyiformes": "Beryciformes",
    "Cypriniformes ": "Cypriniformes",
    "Squamata ": "Squamata",
    "Rodentia ": "Rodentia",
}


def normalise(row):
    """Fold source-specific taxon names onto one canonical set."""
    changed = []
    c = row["class"].strip()
    if c in CLASS_SYNONYM:
        changed.append(("class", c, CLASS_SYNONYM[c]))
        row["class"] = CLASS_SYNONYM[c]
    o = row["order"].strip()
    if o in ORDER_SYNONYM:
        changed.append(("order", o, ORDER_SYNONYM[o]))
        row["order"] = ORDER_SYNONYM[o]
    return changed


def pool_of(row):
    cls = row["class"]
    if cls in VERT:
        return cls
    if cls in FISH:
        return "Pisces"
    return "Invertebrata"


def load(path=DATA):
    rows = []
    renames = {}
    unknown_classes = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for rank, old, new in normalise(r):
                renames[(rank, old, new)] = renames.get((rank, old, new), 0) + 1
            wild = float(r["wild_yr"]) if r["wild_yr"].strip() else None
            cap = float(r["captive_yr"]) if r["captive_yr"].strip() else None
            if wild is None and cap is None:
                continue
            vals = [v for v in (wild, cap) if v is not None]
            row = {
                "name": r["common_name"],
                "sci": r["scientific_name"],
                "mass_g": float(r["mass_g"]),
                "wild": wild,
                "captive": cap,
                # The average is over whichever measurements exist. A species
                # never held in captivity is not penalised with a zero; its
                # average is its wild value.
                "average": sum(vals) / len(vals),
                "maximum": max(vals),
                "colonial": r.get("colonial", "no").strip().lower() == "yes",
                "quality": r["quality"],
                "note": r.get("note", ""),
            }
            for rk in RANKS:
                row[rk] = r[rk].strip()
            row["pool"] = pool_of(r)
            if row["pool"] == "Invertebrata" and row["phylum"] == "Chordata":
                unknown_classes[r["class"]] = \
                    unknown_classes.get(r["class"], 0) + 1
            rows.append(row)

    if renames:
        print("taxonomy normalised:")
        for (rank, old, new), n in sorted(renames.items(),
                                          key=lambda kv: -kv[1]):
            print(f"    {rank:6s} {old:22s} -> {new:18s} ({n} rows)")
        print()
    # A chordate landing in the invertebrate baseline means a class name this
    # file does not know. That silently fits vertebrates against an
    # invertebrate curve, so it is shouted about rather than logged.
    if unknown_classes:
        print("WARNING — chordate classes not recognised, so pooled as "
              "invertebrates:")
        for k, n in sorted(unknown_classes.items(), key=lambda kv: -kv[1]):
            print(f"    {k:24s} {n} species")
        print("    Add them to FISH or CLASS_SYNONYM in build_lq.py.\n")
    return rows


def weight_of(row):
    if FIT_STRATEGY != "weighted":
        return 1.0
    return QUALITY_WEIGHT.get(row.get("quality", ""), DEFAULT_WEIGHT)


def in_fit(row):
    """Whether a record contributes to the regressions at all."""
    if row["colonial"]:
        return False
    if FIT_STRATEGY == "filter" and row["quality"] in EXCLUDE_GRADES:
        return False
    return True


def ols_loglog(rows, life_key="maximum"):
    """Weighted fit of log10(L) = a + b*log10(M).

    Returns (a, b, r2, n_eff). n_eff is Kish's effective sample size,
    (sum w)^2 / sum w^2 — the number of equally-weighted records the weighted
    set is worth. It is the honest n to quote: 1,000 records at weight 0.2 do
    not carry the information of 1,000 records at weight 1.
    """
    xs = [math.log10(r["mass_g"]) for r in rows]
    ys = [math.log10(r[life_key]) for r in rows]
    ws = [weight_of(r) for r in rows]
    sw = sum(ws)
    if sw == 0:
        return float("nan"), float("nan"), float("nan"), 0
    n_eff = sw ** 2 / sum(w * w for w in ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    sxy = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    if sxx == 0:
        return float("nan"), float("nan"), float("nan"), n_eff
    b = sxy / sxx
    a = my - b * mx
    ss_res = sum(w * (y - (a + b * x)) ** 2 for w, x, y in zip(ws, xs, ys))
    ss_tot = sum(w * (y - my) ** 2 for w, y in zip(ws, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return a, b, r2, n_eff


def predict(a, b, mass_g):
    return 10 ** (a + b * math.log10(mass_g))


def geomean(vals):
    vals = [v for v in vals if v and v > 0]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def median(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def build(path=DATA):
    rows = load(path)
    fit_rows = [r for r in rows if in_fit(r)]
    grade_census = {}
    for r in rows:
        if not r["colonial"]:
            grade_census[r["quality"]] = grade_census.get(r["quality"], 0) + 1

    ga, gb, gr2, gn = ols_loglog(fit_rows)

    pools = {}
    for r in fit_rows:
        pools.setdefault(r["pool"], []).append(r)

    fits, rejected = {}, {}
    for pool, members in pools.items():
        if len(members) < MIN_CLASS_N:
            rejected[pool] = f"fewer than {MIN_CLASS_N} species"
            continue
        a, b, r2, n = ols_loglog(members)
        if b <= 0:
            rejected[pool] = f"fit slope not positive (b={b:.3f}, n_eff={n:.0f})"
        elif r2 < MIN_CLASS_R2:
            rejected[pool] = f"fit too weak (r2={r2:.3f}, n_eff={n:.0f})"
        else:
            fits[pool] = (a, b, r2, n)

    for r in rows:
        r["pred_global"] = predict(ga, gb, r["mass_g"])
        f = fits.get(r["pool"])
        r["pred_class"] = predict(f[0], f[1], r["mass_g"]) if f else None
        for metric in ("wild", "captive", "average", "maximum"):
            v = r[metric]
            r["lq_global_" + metric] = (v / r["pred_global"]) if v else None
            r["lq_class_" + metric] = (
                (v / r["pred_class"]) if (v and r["pred_class"]) else None)

    os.makedirs(OUT, exist_ok=True)

    # ---- species table --------------------------------------------------
    cols = (["name", "sci"] + RANKS +
            ["mass_g", "wild", "captive", "average", "maximum", "colonial",
             "pred_global", "pred_class", "lq_global_maximum",
             "lq_class_maximum", "quality"])
    with open(os.path.join(OUT, "lq_table.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: -(r["lq_class_maximum"] or 0)):
            w.writerow([round(r[c], 4) if isinstance(r.get(c), float)
                        else r.get(c) for c in cols])

    # ---- group table ----------------------------------------------------
    groups = rank_summary(rows)
    with open(os.path.join(OUT, "group_summary.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "group", "n_species", "n_colonial",
                    "geomean_lq_class", "median_lifespan_yr",
                    "min_mass_g", "max_mass_g", "longest_lived_species",
                    "longest_lived_yr"])
        for rk in RANKS:
            for g in groups[rk]:
                w.writerow([rk, g["group"], g["n"], g["n_colonial"],
                            None if g["geo_lq"] is None
                            else round(g["geo_lq"], 4),
                            round(g["med_life"], 3), g["min_mass"],
                            g["max_mass"], g["top_name"], g["top_life"]])

    summary = {
        "n_species": len(rows),
        "n_colonial_excluded_from_fits": sum(1 for r in rows if r["colonial"]),
        "grade_census": grade_census,
        "quality_weights": QUALITY_WEIGHT,
        "ranks": {rk: len({r[rk] for r in rows if r[rk]}) for rk in RANKS},
        "global_fit": {"a": ga, "b": gb, "r2": gr2, "n": gn},
        "class_fits": {k: {"a": v[0], "b": v[1], "r2": v[2], "n": v[3]}
                       for k, v in fits.items()},
        "rejected_fits": rejected,
    }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    report(rows, summary, fits, rejected, groups)
    write_html(rows, summary)
    try:
        figures(rows, summary, fit_rows)
    except ImportError:
        print("\nmatplotlib not present; figures skipped "
              "(the visualiser does not need them)")
    return rows, summary


def rank_summary(rows):
    """Aggregate every taxonomic rank. Colonial organisms are counted but
    kept out of the quotient statistics."""
    out = {}
    for rk in RANKS:
        buckets = {}
        for r in rows:
            key = r[rk]
            if key:
                buckets.setdefault(key, []).append(r)
        groups = []
        for key, members in buckets.items():
            solo = [m for m in members if not m["colonial"]]
            top = max(members, key=lambda m: m["maximum"])
            groups.append({
                "group": key,
                "n": len(members),
                "n_colonial": len(members) - len(solo),
                "geo_lq": geomean([m["lq_class_maximum"] for m in solo]),
                "med_life": median([m["maximum"] for m in members]),
                "min_mass": min(m["mass_g"] for m in members),
                "max_mass": max(m["mass_g"] for m in members),
                "top_name": top["name"],
                "top_life": top["maximum"],
            })
        groups.sort(key=lambda g: -(g["geo_lq"] or 0))
        out[rk] = groups
    return out


def report(rows, summary, fits, rejected, groups):
    print(f"{len(rows)} species  "
          + "  ".join(f"{summary['ranks'][r]} {r}" for r in RANKS))
    gc = summary["grade_census"]
    print(f"{summary['n_colonial_excluded_from_fits']} colonial organisms "
          f"excluded from every fit.")
    print(f"fit strategy: {FIT_STRATEGY}  "
          + {"filter": "(grade C dropped from the regressions)",
             "weighted": "(grade C kept, down-weighted)",
             "none": "(every record counts equally)"}[FIT_STRATEGY])
    print("    grades present — " + "  ".join(
        f"{g}: {gc[g]}" for g in sorted(gc)))
    if FIT_STRATEGY == "weighted":
        print("    n below is Kish effective sample size, not a row count")
    print()
    g = summary["global_fit"]
    print(f"global : log10 L = {g['a']:.3f} + {g['b']:.3f} log10 M   "
          f"(r2={g['r2']:.3f}, n_eff={g['n']:.0f})")
    for k in sorted(fits):
        a, b, r2, n = fits[k]
        print(f"{k:14s}: log10 L = {a:.3f} + {b:.3f} log10 M   "
              f"(r2={r2:.3f}, n_eff={n:.0f})")
    for k in sorted(rejected):
        print(f"{k:14s}: no group fit — {rejected[k]}; using global baseline")

    print("\nClasses ranked by geometric mean quotient (n >= 3):")
    for gr in [g for g in groups["class"] if g["n"] >= 3 and g["geo_lq"]][:10]:
        print(f"  {gr['group']:18s} n={gr['n']:3d}  "
              f"LQ {gr['geo_lq']:5.2f}  median life "
              f"{gr['med_life']:6.1f} yr")
    print("\nOrders with the highest quotient (n >= 4):")
    for gr in [g for g in groups["order"] if g["n"] >= 4 and g["geo_lq"]][:6]:
        print(f"  {gr['group']:18s} n={gr['n']:3d}  LQ {gr['geo_lq']:5.2f}"
              f"   longest: {gr['top_name']} ({gr['top_life']:g} yr)")
    print("Orders with the lowest quotient (n >= 4):")
    low = [g for g in groups["order"] if g["n"] >= 4 and g["geo_lq"]][-4:]
    for gr in reversed(low):
        print(f"  {gr['group']:18s} n={gr['n']:3d}  LQ {gr['geo_lq']:5.2f}"
              f"   longest: {gr['top_name']} ({gr['top_life']:g} yr)")
    top = sorted([r for r in rows if r["lq_class_maximum"] and
                  not r["colonial"]], key=lambda r: -r["lq_class_maximum"])[:8]
    print("\nHighest LQ against own group:")
    for r in top:
        print(f"  {r['name']:32s} {r['lq_class_maximum']:6.2f}")
    bot = sorted([r for r in rows if r["lq_class_maximum"]],
                 key=lambda r: r["lq_class_maximum"])[:5]
    print("Lowest LQ against own group:")
    for r in bot:
        print(f"  {r['name']:32s} {r['lq_class_maximum']:6.2f}")


# ------------------------------------------------------------------ figures

def _save(fig, name):
    """Save a figure only after checking that nothing on it collides.

    These four figures used to call savefig directly, so they were the one
    set on the site that was never checked; the audit already existed next
    door in fig_lq_explained.py and simply was not wired to them.
    """
    from fig_lq_explained import audit
    bad = audit(fig)
    if bad:
        print(f"  LAYOUT  {name}")
        for b in bad[:5]:
            print(f"            {b}")
    fig.savefig(os.path.join(OUT, name), dpi=150)
    plt.close(fig)
    return bad


def figures(rows, summary, fit_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ga, gb = summary["global_fit"]["a"], summary["global_fit"]["b"]
    colors = {"Mammalia": "#8b7ff2", "Aves": "#5aa8d8", "Reptilia": "#4f9d84",
              "Amphibia": "#a98fd8", "Pisces": "#6f7fd8",
              "Invertebrata": "#d86a86"}

    fig, ax = plt.subplots(figsize=(9.5, 6.6))
    for pool in sorted({r["pool"] for r in rows}):
        sel = [r for r in rows if r["pool"] == pool and not r["colonial"]]
        ax.scatter([r["mass_g"] for r in sel], [r["maximum"] for r in sel],
                   s=20, alpha=.8, label=pool, color=colors.get(pool, "#888"),
                   edgecolor="none")
    col = [r for r in rows if r["colonial"]]
    if col:
        ax.scatter([r["mass_g"] for r in col], [r["maximum"] for r in col],
                   s=42, facecolor="none", edgecolor="#d86a86", lw=1.3,
                   label="colonial (excluded from fit)")
    xs = [10 ** (i / 4) for i in range(-28, 34)]
    ax.plot(xs, [predict(ga, gb, x) for x in xs], "--", color=INK, lw=1.2,
            label=f"global fit, slope {gb:.3f}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("adult body mass (g)")
    ax.set_ylabel("maximum lifespan (years)")
    ax.set_title(f"Lifespan against body mass — {len(rows)} species")
    # The legend goes outside the axes. Inside, the bottom right corner is
    # occupied by the densest part of the cloud, so the key covered the data.
    ax.legend(fontsize=8, frameon=False, loc="upper left",
              bbox_to_anchor=(1.01, 1.0), borderaxespad=0)
    ax.grid(alpha=.18, which="both")
    fig.tight_layout()

    # Species labels are placed last, against the settled axes, and any label
    # that would land on one already written is dropped rather than stacked.
    # Writing them all at a fixed offset produced "TurquoiseLabord's
    # chameleon" where two species sat close together, and pushed the label
    # of the heaviest animal off the right edge.
    named = ("Greenland shark", "Ocean quahog", "Bowhead whale",
             "Naked mole-rat", "Brandt's bat", "Olm", "Glass sponge",
             "Giant Pacific octopus", "Common shrew", "Turquoise killifish",
             "Black coral", "Labord's chameleon")
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    taken = []
    x0ax, x1ax = ax.get_window_extent(renderer=ren).x0, \
        ax.get_window_extent(renderer=ren).x1
    for r in sorted([r for r in rows if r["name"] in named],
                    key=lambda r: -r["maximum"]):
        px, py = ax.transData.transform((r["mass_g"], r["maximum"]))
        right = px > (x0ax + x1ax) / 2          # label inward near the edge
        ha, dx = ("right", -5) if right else ("left", 5)
        t = ax.annotate(r["name"], (r["mass_g"], r["maximum"]), fontsize=7,
                        xytext=(dx, 4), textcoords="offset points", ha=ha)
        bb = t.get_window_extent(renderer=ren)
        if any(bb.overlaps(o) for o in taken) or bb.x0 < x0ax or bb.x1 > x1ax:
            t.remove()
            continue
        taken.append(bb)
    _save(fig, "fig1_allometry.png")

    ranked = sorted([r for r in rows if r["lq_class_maximum"]
                     and not r["colonial"]],
                    key=lambda r: r["lq_class_maximum"])
    sel = ranked[:12] + ranked[-18:]
    fig, ax = plt.subplots(figsize=(9, 8.8))
    ax.barh([r["name"] for r in sel], [r["lq_class_maximum"] for r in sel],
            color=[colors.get(r["pool"], "#888") for r in sel])
    ax.axvline(1, color=DIM, lw=1.2, ls="--")
    ax.set_xlabel("longevity quotient (observed ÷ predicted for its group)")
    ax.set_title("Who beats their body mass, and who does not")
    ax.tick_params(labelsize=8.5)
    ax.grid(axis="x", alpha=.18)
    fig.tight_layout()
    _save(fig, "fig2_lq_ranked.png")

    pair = [r for r in rows if r["wild"] and r["captive"]]
    pair.sort(key=lambda r: r["captive"] / r["wild"])
    sel = pair[:10] + pair[-16:]
    fig, ax = plt.subplots(figsize=(9, 7.8))
    for i, r in enumerate(sel):
        ax.plot([r["wild"], r["captive"]], [i, i], color="#bbb", lw=1.4,
                zorder=1)
    ax.scatter([r["wild"] for r in sel], range(len(sel)), s=32,
               color="#4f9d84", label="wild", zorder=2)
    ax.scatter([r["captive"] for r in sel], range(len(sel)), s=32,
               color="#8b7ff2", label="captive", zorder=2)
    ax.set_yticks(range(len(sel)))
    ax.set_yticklabels([r["name"] for r in sel], fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlabel("maximum lifespan (years, log scale)")
    ax.set_title("Wild against captive — where protection helps, and where it "
                 "does not")
    ax.legend(fontsize=9, frameon=False)
    ax.grid(axis="x", alpha=.18, which="both")
    fig.tight_layout()
    _save(fig, "fig3_wild_vs_captive.png")

    # order-level comparison
    groups = rank_summary(rows)
    ords = [g for g in groups["order"] if g["n"] >= 4 and g["geo_lq"]]
    ords.sort(key=lambda g: g["geo_lq"])
    fig, ax = plt.subplots(figsize=(9, max(5, .3 * len(ords) + 1.5)))
    ax.barh([g["group"] for g in ords], [g["geo_lq"] for g in ords],
            color="#5a4fb0")
    ax.axvline(1, color=DIM, lw=1.2, ls="--")
    ax.set_xlabel("geometric mean longevity quotient")
    ax.set_title("Orders compared (four or more species each)")
    ax.tick_params(labelsize=8.5)
    ax.grid(axis="x", alpha=.18)
    fig.tight_layout()
    _save(fig, "fig4_orders.png")
    print("\nfigures written to outputs/")


# --------------------------------------------------------------------- html
def write_html(rows, summary):
    """Write the visualiser.

    The payload is column-oriented and dictionary-encoded, which is not
    premature: a row-oriented dump of this table spends 427 kB repeating the
    word "Mammalia" and 2,921 genus names, because taxonomy is exactly the kind
    of field that has a few hundred distinct values and eight thousand
    occurrences. Encoding each rank once and storing indices takes the page
    from 2.4 MB to well under a megabyte, and the browser parses a flat array
    of integers far faster than it parses eight thousand object literals.

    It is also handed over as a JSON string for JSON.parse rather than as a
    JavaScript object literal. The literal has to go through the full
    expression parser; JSON.parse has a dedicated one, and on a payload this
    size the difference is the gap between a page that appears and a page that
    hesitates.
    """
    # dictionary-encoded fields: a few hundred distinct values, thousands of uses
    DICT = ["c", "q", "note"] + [rk[:2] for rk in RANKS]
    NUM = ["m", "w", "p", "a", "mx", "pg", "pc", "col"]
    COLS = ["n", "s"] + NUM + DICT

    tables = {k: {} for k in DICT}

    def idx(field, value):
        d = tables[field]
        v = value or ""
        if v not in d:
            d[v] = len(d)
        return d[v]

    cols = {c: [] for c in COLS}
    for r in rows:
        cols["n"].append(r["name"])
        cols["s"].append(r["sci"])
        cols["m"].append(r["mass_g"])
        cols["w"].append(r["wild"])
        cols["p"].append(r["captive"])
        cols["a"].append(round(r["average"], 3))
        cols["mx"].append(r["maximum"])
        cols["pg"].append(round(r["pred_global"], 4))
        cols["pc"].append(round(r["pred_class"], 4) if r["pred_class"]
                          else None)
        cols["col"].append(1 if r["colonial"] else 0)
        cols["c"].append(idx("c", r["pool"]))
        cols["q"].append(idx("q", r["quality"]))
        cols["note"].append(idx("note", r.get("note", "")))
        for rk in RANKS:
            cols[rk[:2]].append(idx(rk[:2], r[rk]))

    payload = {
        "n": len(rows),
        "cols": cols,
        "dict": {k: [s for s, _ in sorted(v.items(), key=lambda kv: kv[1])]
                 for k, v in tables.items()},
        "dictFields": DICT,
    }

    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("/*DATA*/", json.dumps(blob, ensure_ascii=False))
    html = html.replace("/*FITS*/", json.dumps(summary, ensure_ascii=False,
                                               separators=(",", ":")))
    path = os.path.join(HERE, "longevity.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"\nvisualiser written: {path} "
          f"({os.path.getsize(path)/1024:.0f} kB, self-contained)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--weights", default=FIT_STRATEGY,
                    choices=["filter", "weighted", "none"],
                    help="how to handle low-confidence records: drop them from "
                         "the fits (default, best in simulation), down-weight "
                         "them, or treat every record equally")
    ap.add_argument("--data", default=DATA,
                    help="species table to build from "
                         "(default data/animals.csv; pass "
                         "data/animals_merged.csv after a merge)")
    args = ap.parse_args()
    FIT_STRATEGY = args.weights
    build(args.data)
