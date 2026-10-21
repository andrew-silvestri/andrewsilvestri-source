"""Build outputs/payload.json, the one file the figures, the page and the app read.

Every number the page prints is in here or is computed by update_page.py
from what is in here. Sources and their definitions: sources.py; the
capacity list: capacity.py; the model: model.py; the plan:
03 RESEARCH/takeaway/PLAN.md.

Run:  python build_takeaway.py
"""
import datetime as dt
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import capacity   # noqa: E402
import model as M   # noqa: E402
import reconcile   # noqa: E402
import sources     # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")

T0 = (2024, 8)                      # PLAN 3.3: inside "every day since July 26"
T0_ALT = [(2024, 7), (2024, 9)]     # the sensitivity cases
H_FROM = (2024, 6)                  # F2 starts two months before t0
CAP_UNTIL = (2030, 12)              # F1 and the app run to here
SCEN_UNTIL = (2031, 12)
FLARE_FROM = (2008, 1)              # PLAN 3.5
EVENT_MIN_BCFD = 0.5
WINDOW = 12
# PLAN 3.4, written before the build computed them.
PIN_BEFORE = ((2024, 5), (2024, 8))     # growth over the three months to t0
PIN_AFTER = ((2024, 9), (2024, 12))     # growth over the three months after Matterhorn
FLARE_BEFORE = [(2024, m) for m in (6, 7, 8, 9)]
FLARE_AFTER = [(2024, 11), (2024, 12), (2025, 1), (2025, 2)]


def key(ym):
    return f"{ym[0]}-{ym[1]:02d}"


def k_year():
    """Latest year EIA has filled every series k needs."""
    for y in range(dt.date.today().year, 2015, -1):
        try:
            sources.residue_share(y)
            return y
        except (KeyError, TypeError, ZeroDivisionError):
            continue
    raise RuntimeError("no year with marketed, dry, lease and plant fuel for both states")


def main():
    P = sources.steo_permian()
    release, last = sources.steo_release()
    entries = capacity.entries()
    pre = capacity.pre_anchor()
    lo0, hi0 = capacity.ANCHOR["bcfd"]

    # k
    ky = k_year()
    ks = sources.residue_share(ky)
    k_def = ks["both"]["net"]
    k_band = (ks["TX"]["net"], ks["both"]["dry"])

    # capacity by month, for F1 and the app
    adds = [(e["month"], e["bcfd"]) for e in entries]
    cap = {}
    for t in M.month_range(capacity.ANCHOR["date"], CAP_UNTIL):
        a = M.capacity_added(adds, capacity.ANCHOR["date"], t)
        conf = M.capacity_added([(e["month"], e["bcfd"]) for e in entries if e["status"] == "confirmed"],
                                capacity.ANCHOR["date"], t)
        cap[key(t)] = {"lo": lo0 + a, "hi": hi0 + a, "lo_confirmed": lo0 + conf, "hi_confirmed": hi0 + conf}

    # headroom on the record: lines confirmed in service only (the page review
    # found the first build counting Hugh Brinson's phase I, whose full
    # capacity was only expected, in the headline)
    conf_adds = [(e["month"], e["bcfd"]) for e in entries if e["status"] == "confirmed"]
    months = M.month_range(H_FROM, last)
    H = {key(t): v for t, v in M.headroom(P, conf_adds, k_def, T0, months).items()}
    H_all = {key(t): v for t, v in M.headroom(P, adds, k_def, T0, months).items()}
    Hb = {name: {key(t): v for t, v in M.headroom(P, conf_adds, kk, T0, months).items()}
          for name, kk in (("k_lo", k_band[0]), ("k_hi", k_band[1]))}
    Halt = {key(t0): {key(t): v for t, v in M.headroom(P, conf_adds, k_def, t0, months).items()} for t0 in T0_ALT}

    # the t0 checks (PLAN 3.4)
    pin = {"before": M.growth(P, *PIN_BEFORE), "after": M.growth(P, *PIN_AFTER),
           "before_span": [key(m) for m in PIN_BEFORE], "after_span": [key(m) for m in PIN_AFTER]}

    # venting and flaring, the three Permian districts (RRC PDQ dump; PLAN 3.5).
    # Until Q2 (2026-10-20) this was EIA's statewide monthly series, because the
    # dump's host refused every connection on 2026-10-18.
    vf = sources.rrc_vented_flared()
    pdq_meta, _ = sources.pdq_reduced()
    share = {t: v / g for t, (v, g) in vf.items() if t >= FLARE_FROM}
    starts = [e for e in pre] + [e for e in entries if e["status"] == "confirmed" and e["bcfd"] >= EVENT_MIN_BCFD]
    clusters = M.event_clusters([e["month"] for e in starts], WINDOW)
    ba = M.before_after(share, clusters, WINDOW)
    pl = M.placebo(share, clusters, WINDOW)
    plv = sorted(pl.values())
    for row in ba:
        if "diff" in row:
            row["rank_below"] = sum(1 for v in plv if v < row["diff"])
            row["placebo_n"] = len(plv)
    fb = [share[t] for t in FLARE_BEFORE if t in share]
    fa = [share[t] for t in FLARE_AFTER if t in share]
    flare_check = {"before_months": [key(t) for t in FLARE_BEFORE if t in share],
                   "after_months": [key(t) for t in FLARE_AFTER if t in share],
                   "missing": [key(t) for t in FLARE_BEFORE + FLARE_AFTER if t not in share],
                   "before": st.fmean(fb) if fb else None, "after": st.fmean(fa) if fa else None}

    # reconciliation, for Method
    rrc = reconcile.rrc_settled()
    ratio = reconcile.ratio_table(rrc, P)
    rs = reconcile.summary(ratio)

    # share of the three districts' gas from oil wells, latest calendar year
    # the settled RRC series covers in full
    years = sorted({t[0] for t in rrc})
    cy = max(y for y in years if all((y, m) in rrc for m in range(1, 13)))
    mcf = sources.rrc_permian_mcf()
    cs = sum(mcf[(cy, m)][0] for m in range(1, 13))
    gw = sum(mcf[(cy, m)][1] for m in range(1, 13))
    counties = sources.dpr_region_counties()

    def entry_out(e):
        src = e["source"]
        return {"name": e["name"], "month": key(e["month"]), "bcfd": e["bcfd"], "status": e["status"],
                "cite": src[0], "url": src[1], "quote": src[2], "disagrees": e["disagrees"],
                "year_only": bool(e.get("year_only"))}

    payload = {
        "built": dt.date.today().isoformat(),
        "steo": {"release": release, "last_historical": key(last),
                 "P": {key(t): v for t, v in sorted(P.items())}},
        "anchor": {"month": key(capacity.ANCHOR["date"]), "lo": lo0, "hi": hi0,
                   "sources": [{"cite": c, "url": u, "quote": q} for c, u, q in capacity.ANCHOR["sources"]]},
        "entries": [entry_out(e) for e in entries],
        "excluded": capacity.EXCLUDED,
        "pre_anchor": [{"name": e["name"], "month": key(e["month"]), "bcfd": e["bcfd"]} for e in pre],
        "capacity": cap,
        "k": {"year": ky, "default": k_def, "lo": k_band[0], "hi": k_band[1],
              "by_state": {s: {"dry": v["dry"], "net": v["net"]} for s, v in ks.items()}},
        "t0": key(T0), "t0_alt": [key(t) for t in T0_ALT],
        "H": H, "H_with_expected": H_all, "H_band": Hb, "H_alt": Halt,
        "pin": pin,
        "flaring": {"source": "RRC PDQ dump, districts 7C, 08 and 8A: disposition code 4 (vented or flared) "
                              "over gas well and casinghead production",
                    "dump": {k: pdq_meta["dump"][k] for k in ("gas_extract_date", "newest_prod_cycle", "downloaded")},
                    "unsettled_months": sources.PDQ_UNSETTLED,
                    "share": {key(t): v for t, v in sorted(share.items())},
                    "first": key(min(share)), "last": key(max(share)),
                    "clusters": [{"first": key(r["first"]), "last": key(r["last"]),
                                  "starts": [key(m) for m in r["starts"]],
                                  **{k: r[k] for k in ("before", "after", "diff", "rank_below", "placebo_n", "skip")
                                     if k in r}} for r in ba],
                    "starts": [{"name": e["name"], "month": key(e["month"]), "bcfd": e["bcfd"]} for e in starts],
                    "placebo_n": len(plv), "placebo_range": [plv[0], plv[-1]] if plv else None,
                    "placebo_months": [key(min(pl)), key(max(pl))] if pl else None,
                    "check": flare_check},
        "reconcile": {"n": rs["n"], "first": key(rs["first"]), "last": key(rs["last"]), "mean": rs["mean"],
                      "sd": rs["sd"], "min": rs["min"], "max": rs["max"], "lag": reconcile.RRC_LAG},
        "scenario": {"until": key(SCEN_UNTIL), "r_default": 0.0, "delay_default": 0},
        "csgd": {"year": cy, "share": cs / (cs + gw)},
        "region": {"TX": len(counties["TX"]), "NM": len(counties["NM"])},
        "window": WINDOW,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {OUT}")
    print(f"  STEO {release}, last historical {key(last)}; k {ky} = {k_def:.4f} ({k_band[0]:.4f}..{k_band[1]:.4f})")
    print(f"  H at {key(last)}: {H[key(last)]:+.3f} Bcf/d (band {Hb['k_lo'][key(last)]:+.3f}..{Hb['k_hi'][key(last)]:+.3f})")
    print(f"  pin: before {pin['before']:+.3f}, after {pin['after']:+.3f}")
    print(f"  flare check: before {flare_check['before']}, after {flare_check['after']}, missing {flare_check['missing']}")
    for r in payload["flaring"]["clusters"]:
        print("  cluster", r)


if __name__ == "__main__":
    main()
