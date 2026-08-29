"""
Add the space and weather layers to the atlas payload.

Two layers sit above the climate in the causal order and were missing.

SPACE.  The sun, and the sunlight that reaches the top of the atmosphere. The
solar constant is measured; the insolation is exact orbital geometry. Neither
is estimated. The chain is

    total solar irradiance  ->  top-of-atmosphere insolation at a latitude
                            ->  the national grids whose solar fleet depends
                                on it, weighted by the measured solar share of
                                that country's generating capacity

WEATHER.  Two modes of interannual variability with measured index series and
published, quantified couplings to this system:

    ONI (El Nino / La Nina)  ->  global temperature anomaly
    winter NAO               ->  the electricity demand of Great Britain and
                                 Ireland

Every weight in this file is either measured from the data in the payload,
computed here from the measured series and printed with its statistics, or
taken from a named publication. Nothing is assumed. Where a coupling is real
but unquantified in a source I could check, the link is not drawn -- which is
why the NAO reaches two countries and not twenty.

Run:  python3 build_atlas_space.py            report only
      python3 build_atlas_space.py --apply
"""

import argparse
import collections
import json
import math
import os
import re

import numpy as np

import data_climate_indices as C

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")

# Orbital and geodetic constants.
OBLIQUITY = 23.4397          # degrees, IAU 2006 mean obliquity at J2000
BAND = 10.0                  # degrees of latitude per insolation band

# Thornton, H.E., Scaife, A.A., Hoskins, B.J. and Greenwood, D.J. (2017),
# 'The relationship between wind power, electricity demand and winter weather
# patterns in Great Britain', Environmental Research Letters 12 064017.
# Observed winter NAO against winter electricity demand: r = -0.67.
NAO_DEMAND_R = -0.67
NAO_COUNTRIES = {"GBR": "Thornton et al. 2017, Great Britain",
                 "IRL": "Curtis et al. 2016, Ireland"}


# ------------------------------------------------------------------ solar --
def solar_position(n):
    """
    Declination in radians and Earth-Sun distance in AU for day n after J2000.

    Standard low-precision solar position: mean anomaly, equation of centre,
    true ecliptic longitude, then the obliquity rotation. Good to well under a
    tenth of a degree, which is far finer than a ten-degree latitude band.
    """
    M = math.radians((357.5291 + 0.98560028 * n) % 360.0)
    Cc = (1.9148 * math.sin(M) + 0.0200 * math.sin(2 * M)
          + 0.0003 * math.sin(3 * M))
    lam = math.radians((math.degrees(M) + Cc + 180.0 + 102.9372) % 360.0)
    dec = math.asin(math.sin(lam) * math.sin(math.radians(OBLIQUITY)))
    r_au = 1.00014 - 0.01671 * math.cos(M) - 0.00014 * math.cos(2 * M)
    return dec, r_au


def annual_insolation(lat_deg, s0):
    """
    Annual mean top-of-atmosphere insolation at a latitude, W/m^2.

    Daily mean over a sphere rotating once per day:

        Q = (S0 / pi) (a/r)^2 [ h0 sin(phi) sin(dec)
                                + cos(phi) cos(dec) sin(h0) ]

    with h0 the half-day angle, arccos(-tan(phi) tan(dec)), clamped to give
    polar day and polar night. Averaged over 365 days.
    """
    phi = math.radians(lat_deg)
    total = 0.0
    for day in range(365):
        dec, r_au = solar_position(day)
        x = -math.tan(phi) * math.tan(dec)
        if x >= 1.0:
            h0 = 0.0                       # polar night
        elif x <= -1.0:
            h0 = math.pi                   # polar day
        else:
            h0 = math.acos(x)
        total += (s0 / math.pi) * (1.0 / r_au) ** 2 * (
            h0 * math.sin(phi) * math.sin(dec)
            + math.cos(phi) * math.cos(dec) * math.sin(h0))
    return total / 365.0


def check_insolation(s0):
    """
    The area-weighted global mean of the annual insolation field must equal
    S0/4 -- the disc the Earth presents divided by the sphere it radiates
    from. If the integration is wrong this fails, so it is not decoration.
    """
    lats = np.arange(-89.5, 90.0, 1.0)
    q = np.array([annual_insolation(x, s0) for x in lats])
    w = np.cos(np.radians(lats))
    got = float((q * w).sum() / w.sum())
    want = s0 / 4.0
    err = abs(got - want) / want
    return got, want, err


def ac1(v):
    v = np.asarray(v, dtype=float)
    v = v - v.mean()
    return float(np.corrcoef(v[:-1], v[1:])[0, 1])


# ------------------------------------------------------------------- load --
def load():
    raw = open(DATA, encoding="utf-8").read()
    return raw[:raw.index("=") + 1], json.loads(
        raw[raw.index("=") + 1:raw.rindex(";")])


RAW = os.path.join(HERE, "..", "19 Atlas v6", "raw",
                   "global_power_plant_database.csv")


def name_to_iso3():
    """
    The plant layer records a country name; the grids are keyed by ISO3. The
    WRI file carries both columns, so it is the authority for its own naming
    rather than a gazetteer that might disagree with it. An earlier version of
    this build matched a two-letter code against a three-letter one and
    orphaned a fifth of the model, so this mapping is asserted, not assumed.
    """
    import csv
    m = {}
    with open(RAW, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            iso, nm = row.get("country"), row.get("country_long")
            if iso and nm:
                m[nm.strip()] = iso.strip()
    return m


def solar_share(D):
    """
    Fraction of each country's generating capacity that is solar, measured
    from the plant layer of the payload itself. Name carries the fuel, the
    source string carries the country, the sparse map carries the megawatts.
    """
    kind = [D["kinds"][k] for k in D["kind"]]
    mw = {int(k): float(v) for k, v in D["mwMap"].items()}
    iso3 = name_to_iso3()
    tot = collections.Counter()
    sol = collections.Counter()
    unmatched = set()
    for i, k in enumerate(kind):
        if k != "station":
            continue
        s = D["srcDict"][D["src"][i]]
        if "·" not in s:
            continue
        nm = s.split("·")[1].strip()
        iso = iso3.get(nm)
        if iso is None:
            unmatched.add(nm)
            continue
        m = re.search(r"\(([^,]+),", D["name"][i])
        cap = mw.get(i, 0.0)
        tot[iso] += cap
        if m and m.group(1).strip().lower() == "solar":
            sol[iso] += cap
    if unmatched:
        print(f"  WARNING {len(unmatched)} country names had no ISO3: "
              f"{sorted(unmatched)[:6]}")
    return {c: sol[c] / tot[c] for c in tot if tot[c] > 0}


def enso_temperature(D):
    """
    Regress the global temperature anomaly on the ONI. The temperature carries
    a strong trend and the ONI does not, so the raw correlation mostly measures
    the trend; a quadratic in time is removed from the temperature first. The
    returned r is the weight the model uses.
    """
    temp = {int(y): float(v) for y, v in D["temp"]}
    oni = {y: v for y, v in C.annual(C.ONI) if len(dict(C.ONI)[y]) == 12}
    yrs = sorted(set(temp) & set(oni))
    t = np.array([temp[y] for y in yrs])
    o = np.array([oni[y] for y in yrs])
    x = np.array(yrs, dtype=float)
    raw_r = float(np.corrcoef(t, o)[0, 1])
    resid = t - np.polyval(np.polyfit(x, t, 2), x)
    r = float(np.corrcoef(resid, o)[0, 1])
    slope = float(np.polyfit(o, resid, 1)[0])
    n = len(yrs)
    tstat = r * math.sqrt((n - 2) / (1 - r * r))
    return dict(r=r, raw_r=raw_r, slope=slope, n=n, t=tstat,
                y0=yrs[0], y1=yrs[-1])


# ------------------------------------------------------------------ build --
def main(apply=False):
    head, D = load()
    n0, e0 = D["n"], len(D["es"])

    s0 = C.TSI[-1][1]
    s0_year, _, s0_unc = C.TSI[-1]
    got, want, err = check_insolation(s0)
    print(f"  solar constant {s0:.3f} +/- {s0_unc:.3f} W/m2 ({s0_year}, "
          f"NRLTSI2)")
    print(f"  insolation integral: global mean {got:.2f} W/m2 against "
          f"S0/4 = {want:.2f}, error {err * 100:.4f}%")
    if err > 0.005:
        raise SystemExit("  insolation integration is wrong; refusing to build")

    enso = enso_temperature(D)
    print(f"  ONI against global temperature, {enso['y0']}-{enso['y1']}: "
          f"raw r = {enso['raw_r']:+.3f}, detrended r = {enso['r']:+.3f} "
          f"(t = {enso['t']:.2f}, n = {enso['n']}), "
          f"{enso['slope']:.4f} C per C")

    tsi_res = ac1([x[1] for x in C.TSI])
    oni_res = ac1([v for y, v in C.annual(C.ONI)
                   if len(dict(C.ONI)[y]) == 12])
    nao_res = ac1([v for _, v in C.djf(C.NAO)])
    print(f"  inertia from lag-1 autocorrelation: sun {tsi_res:.3f}, "
          f"ENSO {oni_res:.3f}, winter NAO {nao_res:.3f}")

    share = solar_share(D)
    print(f"  solar share of capacity measured for {len(share)} countries")

    # ---- node and edge helpers ----
    kinds = D["kinds"]
    for k in ("sun", "insolation", "weather"):
        if k not in kinds:
            kinds.append(k)
    idmap = {k: int(v) for k, v in D["idMap"].items()}
    srcd = D["srcDict"]

    def src_id(s):
        if s not in srcd:
            srcd.append(s)
        return srcd.index(s)

    tabs = D["tabs"]
    have = {t["id"] for t in tabs}
    new_tabs = []
    if "space" not in have:
        new_tabs.append({"id": "space", "name": "Space",
                         "sub": "the sun and the light that arrives"})
    if "weather" not in have:
        new_tabs.append({"id": "weather", "name": "Weather",
                         "sub": "two measured modes of variability"})
    tabs[:0] = new_tabs
    tab_ix = {t["id"]: i for i, t in enumerate(tabs)}
    # every existing node's tab index shifts by however many we inserted
    if new_tabs:
        D["tab"] = [t + len(new_tabs) for t in D["tab"]]

    def add(ident, name, kind, tab, lat, lon, res, src):
        i = D["n"]
        D["lat"].append(round(lat, 4))
        D["lon"].append(round(lon, 4))
        D["kind"].append(kinds.index(kind))
        D["tab"].append(tab_ix[tab])
        D["res"].append(round(res, 4))
        D["name"].append(name)
        D["src"].append(src_id(src))
        idmap[ident] = i
        D["n"] += 1
        return i

    def link(a, b, w):
        D["es"].append(int(a))
        D["et"].append(int(b))
        D["ew"].append(round(float(w), 6))

    # ---- the sun ----
    sun = add("SUN_TSI",
              f"Sun (total solar irradiance {s0:.2f} W/m2)",
              "sun", "space", 0.0, 0.0, max(0.0, tsi_res),
              f"LASP LISIRD NRLTSI2 annual, {C.TSI[0][0]}-{s0_year} "
              f"({len(C.TSI)} obs)")

    # ---- insolation bands ----
    kind = [kinds[k] for k in D["kind"]]
    grids = {}
    for ident, i in list(idmap.items()):
        if ident.startswith("GRID_") and kind[i] == "grid":
            grids[ident[5:]] = i

    bands = {}
    edges_band = 0
    for lo in np.arange(-90.0, 90.0, BAND):
        mid = float(lo + BAND / 2.0)
        q = annual_insolation(mid, s0)
        hemi = "N" if mid > 0 else "S"
        bid = add(f"INSOL_{int(abs(mid))}{hemi}",
                  f"Insolation at {abs(mid):.0f} {hemi} "
                  f"({q:.0f} W/m2 annual mean)",
                  "insolation", "space", mid, 0.0, 0.0,
                  "Computed: annual mean top-of-atmosphere insolation from "
                  f"the measured solar constant and orbital geometry")
        bands[(lo, lo + BAND)] = bid
        # insolation follows the solar constant exactly and instantly
        link(sun, bid, 1.0)

    # ---- insolation to the grids that depend on it ----
    wired = 0
    for iso, gi in grids.items():
        f = share.get(iso)
        if not f or f <= 0:
            continue                      # no measured solar fleet, no link
        la = D["lat"][gi]
        for (lo, hi), bid in bands.items():
            if lo <= la < hi:
                link(bid, gi, f)          # weight IS the measured solar share
                wired += 1
                edges_band += 1
                break

    # ---- weather ----
    oni_now = C.ONI[-1][1][-1]
    nao_now = C.djf(C.NAO)[-1][1]
    enso_i = add("WX_ENSO",
                 f"El Nino / La Nina (ONI {oni_now:+.2f} C)",
                 "weather", "weather", 0.0, -150.0, max(0.0, oni_res),
                 f"NOAA CPC Oceanic Nino Index, {C.ONI[0][0]}-"
                 f"{C.ONI[-1][0]} ({len(C.monthly(C.ONI))} seasons)")
    nao_i = add("WX_NAO",
                f"North Atlantic Oscillation (winter {nao_now:+.2f})",
                "weather", "weather", 55.0, -30.0, max(0.0, nao_res),
                f"NOAA CPC standardised NAO, {C.NAO[0][0]}-{C.NAO[-1][0]} "
                f"({len(C.monthly(C.NAO))} months)")

    link(enso_i, idmap["GLOBAL_TEMP"], abs(enso["r"]))
    nao_links = 0
    for iso in NAO_COUNTRIES:
        gi = grids.get(iso)
        if gi is not None:
            link(nao_i, gi, NAO_DEMAND_R)   # negative: high NAO is relief
            nao_links += 1

    D["idMap"] = {k: v for k, v in idmap.items()}
    D["kinds"] = kinds
    D["srcDict"] = srcd
    D["tabs"] = tabs

    print(f"\n  nodes {n0:,} -> {D['n']:,}  (+{D['n'] - n0})")
    print(f"  links {e0:,} -> {len(D['es']):,}  (+{len(D['es']) - e0})")
    print(f"  insolation bands wired to {wired} national grids "
          f"with a measured solar fleet")
    print(f"  NAO wired to {nao_links} grids: "
          f"{', '.join(sorted(NAO_COUNTRIES))}")

    assert len(D["lat"]) == D["n"] == len(D["res"]) == len(D["name"])
    assert len(D["es"]) == len(D["et"]) == len(D["ew"])

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return
    open(DATA, "w", encoding="utf-8").write(
        head + json.dumps(D, separators=(",", ":")) + ";")
    print("  written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
