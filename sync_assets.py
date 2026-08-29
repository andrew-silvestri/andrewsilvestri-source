"""
Sync figures into site/assets, and delete the ones nothing references.

Written after discovering that every project figure on the site was stale. The
figures live under each project as outputs/fig1_....png, but the pages
reference them with a project prefix — heat_fig1_....png — and hand-copying
had been dropping them at the unprefixed name. The pages kept rendering months
old images while the source figures were current, and nothing complained,
because a file that exists is a file that loads.

So the copy is no longer done by hand. This reads every <img src> the site
actually asks for, resolves it back to a source figure, copies it, and reports
anything it could not resolve. Then it removes assets no page references.

Run:
    python3 sync_assets.py            # report only
    python3 sync_assets.py --apply    # copy and prune
"""

import argparse
import filecmp
import glob
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
SITE = os.path.join(HERE, "site")
ASSETS = os.path.join(SITE, "assets")

# prefix on the site  ->  folder holding outputs/
PREFIX_SOURCE = {
    "heat_": os.path.join(PARENT, "01 Industrial Heat Breakeven"),
    "dac_": os.path.join(PARENT, "02 DAC Adsorption TEA"),
    "storage_": os.path.join(PARENT, "03 Storage Revenue Stack"),
    "web_": os.path.join(PARENT, "10 World Energy Web"),
    "web5_": os.path.join(PARENT, "14 World Energy Web v5"),
}

# figures whose site name is not just prefix + source name
EXPLICIT = {
    "lq_allometry.png": ("00 PUBLISH/longevity-quotient", "fig1_allometry.png"),
    "lq_ranked.png": ("00 PUBLISH/longevity-quotient", "fig2_lq_ranked.png"),
    "lq_wild_captive.png": ("00 PUBLISH/longevity-quotient",
                            "fig3_wild_vs_captive.png"),
    "lq_orders.png": ("00 PUBLISH/longevity-quotient", "fig4_orders.png"),
    # energy_model_chart.png and energy_model_throughlines.png are NOT here.
    # They used to be copied from 18 Final Deliverables, which is a snapshot of
    # a retired 7,192-node model. They are now generated straight into
    # site/assets by build_model_chart.py and build_throughlines.py, reading
    # the live payload. Re-adding them here would overwrite the current
    # figures with figures of a model that no longer exists.
}


def referenced():
    """Every asset path the site asks for."""
    want = set()
    for page in glob.glob(os.path.join(SITE, "*.html")):
        html = open(page, encoding="utf-8", errors="ignore").read()
        for m in re.findall(r'(?:href|src)="([^"]+)"', html):
            m = m.split("#")[0].split("?")[0]
            if m.startswith("assets/"):
                want.add(m[len("assets/"):])
    return want


def source_for(name):
    """Where a given site asset should be copied from, or None."""
    if name in EXPLICIT:
        folder, fig = EXPLICIT[name]
        for base in (os.path.join(PARENT, folder), os.path.join(HERE, folder)):
            for cand in (os.path.join(base, "outputs", fig),
                         os.path.join(base, "out", fig),
                         os.path.join(base, fig)):
                if os.path.exists(cand):
                    return cand
        return None
    for pref, base in PREFIX_SOURCE.items():
        if name.startswith(pref):
            stem = name[len(pref):]
            for cand in (os.path.join(base, "outputs", stem),
                         os.path.join(base, "out", stem),
                         os.path.join(base, stem)):
                if os.path.exists(cand):
                    return cand
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually copy and delete; otherwise report only")
    args = ap.parse_args()

    want = referenced()
    on_disk = set()
    for r, _, fs in os.walk(ASSETS):
        for f in fs:
            rel = os.path.relpath(os.path.join(r, f), ASSETS).replace("\\", "/")
            on_disk.add(rel)

    stale, fresh, unresolved, missing = [], [], [], []
    for name in sorted(want):
        dst = os.path.join(ASSETS, name)
        src = source_for(name)
        if src is None:
            if not os.path.exists(dst):
                missing.append(name)
            elif not name.endswith(".png"):
                pass                       # js, html and the like live here
            else:
                unresolved.append(name)
            continue
        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            fresh.append(name)
        else:
            stale.append((name, src))

    orphans = sorted(on_disk - want)

    print(f"referenced by a page : {len(want)}")
    print(f"already current      : {len(fresh)}")
    print(f"STALE or absent      : {len(stale)}")
    for name, src in stale:
        print(f"    {name:38s} <- {os.path.relpath(src, PARENT)}")
    if unresolved:
        print(f"could not resolve    : {len(unresolved)}")
        for n in unresolved:
            print(f"    {n}  (kept; no source folder matched)")
    if missing:
        print(f"REFERENCED BUT ABSENT: {len(missing)}")
        for n in missing:
            print(f"    {n}  <-- this is a broken image on the site")

    dead = sum(os.path.getsize(os.path.join(ASSETS, o)) for o in orphans)
    print(f"orphaned assets      : {len(orphans)}  ({dead/1e6:.1f} MB)")
    for o in orphans:
        print(f"    {o}")

    if not args.apply:
        print("\nreport only. Re-run with --apply to copy and prune.")
        return 0

    for name, src in stale:
        dst = os.path.join(ASSETS, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    for o in orphans:
        os.remove(os.path.join(ASSETS, o))
    print(f"\ncopied {len(stale)}, removed {len(orphans)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
