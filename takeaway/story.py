"""The reworked page's findings (R2, 2026-10-23): the pattern, the hero's
series, and the readings of "how full now". build_takeaway.py calls
story(); everything here goes into payload["story"].

Plan and review: 03 RESEARCH/takeaway/r2/PLAN_R2.md. The model is model.py,
unchanged: H(t) = [C(t) - C(t0)] - k [P(t) - P(t0)].

Production before STEO's window. STEO's monthly workbook starts in January
four years before its release, so the hero's early months come from EIA's
last Drilling Productivity Report (total gas, to 2023-06) times SPLICE.
SPLICE is FROZEN, not recomputed: the review found that each January moves
STEO's window a year forward, so a recomputed overlap shrinks to six months
on a 2027 release and to nothing on a 2028 one. It is the mean of STEO /
DPR over the 18 months the Oct 2026 release shares with DPR (2022-01 to
2023-06, range 0.9505 to 0.9877). The ratio drifts up over those months;
marketed gas excludes flaring, which was higher in 2019, so a constant ratio
slightly overstates 2019 production and so understates the 2019 discrepancy
the page reports. p_long() refuses to build if any month from the hero's
start is covered by neither source.
"""
import statistics as st

import capacity
import cited
import model as M
import sources

SPLICE = 0.9740                      # STEO Oct 2026 / DPR, 2022-01..2023-06, n=18
SPLICE_RANGE = (0.9505, 0.9877)
SPLICE_N = 18
HERO_FROM = (2018, 1)
PACE_FROM = (2017, 1)                # the pace basis for "months of growth"
REF_2019 = (2019, 7)                 # EIA TIE 41213: GCX deliveries began 2019-08-08
BIG = ["Gulf Coast Express", "Permian Highway Pipeline Project", "Whistler Pipeline Project",
       "Matterhorn Express Pipeline"]
SHORT = {"Gulf Coast Express": "Gulf Coast Express", "Permian Highway Pipeline Project": "Permian Highway",
         "Whistler Pipeline Project": "Whistler", "Matterhorn Express Pipeline": "Matterhorn Express",
         "Gulf Coast Express Expansion": "Gulf Coast Express expansion",
         "Whistler Pipeline Expansion": "Whistler expansion",
         "Permian Highway Pipeline Expansion": "Permian Highway expansion"}


def key(ym):
    return f"{ym[0]}-{ym[1]:02d}"


def p_long(P_steo, dpr):
    """STEO marketed where STEO has it; DPR x SPLICE before that. Raises on a gap."""
    first = min(P_steo)
    out = {t: v * SPLICE for t, v in dpr.items() if t < first}
    out.update(P_steo)
    missing = [t for t in M.month_range(HERO_FROM, max(P_steo)) if t not in out]
    if missing:
        raise RuntimeError(f"production has no source for {len(missing)} months from {key(missing[0])}: "
                           "STEO's window has moved past DPR's last month; freeze a STEO vintage (story.py)")
    return out


def k_permian(year, ks):
    """EIA's own Permian ratio: STEO 10b shale-formation dry gas over 5a
    region marketed gas, calendar `year`; and that less the statewide lease
    and plant fuel share. Biased low (10b omits conventional gas)."""
    f, P = sources.steo_formation(), sources.steo_permian()
    ms = [t for t in P if t[0] == year and t in f]
    assert len(ms) == 12, (year, len(ms))
    dry = sum(f[t] for t in ms) / sum(P[t] for t in ms)
    fuel = ks["both"]["dry"] - ks["both"]["net"]
    return dry, dry - fuel


def story(P_steo, entries, k, k_band, ks, k_year, t0, flaring_share, vf):
    dpr = sources.dpr_permian()
    P = p_long(P_steo, dpr)
    last = max(P_steo)
    ov = [t for t in P_steo if t in dpr]
    pre = capacity.pre_anchor_takeaway()
    conf = [e for e in entries if e["status"] == "confirmed"]
    adds = [(e["month"], e["bcfd"]) for e in pre] + [(e["month"], e["bcfd"]) for e in conf]
    months = M.month_range(HERO_FROM, last)

    def H(kk, ad=adds, tt=t0):
        return M.headroom(P, ad, kk, tt, months)

    def below(h):
        return [key(t) for t in months if t > t0 and h[t] < 0]

    # the hero: both lines as change from t0, so the gap between them is H
    pipe = [M.capacity_added(adds, t0, t) for t in months]
    gas = [k * (P[t] - P[t0]) for t in months]

    # readings of "how full now", each one choice from the default
    kp_dry, kp_net = k_permian(k_year, ks)

    def k_fit(ad):
        return sum(b for m, b in ad if REF_2019 < m <= t0) / (P[t0] - P[REF_2019])
    double_e = (capacity.completed(capacity.PRE_ANCHOR_SEEN), 1.35)
    no_sm = [a for a in adds if a[0] != (2020, 7)]
    fits = {"list": k_fit(adds), "no_south_mainline": k_fit(no_sm), "with_double_e": k_fit(adds + [double_e])}
    tarzan = next(e for e in conf if e["name"].startswith("Tarzan"))
    no_tarzan = [a for a in adds if a != (tarzan["month"], tarzan["bcfd"])]
    hb1 = next(e for e in entries if e["name"].endswith("Phase I & II Phase I"))
    readings = []

    def reading(name, why, h):
        readings.append({"name": name, "why": why, "H": h[last], "below": below(h)})
    reading("default", f"k = {k:.3f}, lines confirmed in service, full in {key(t0)}", H(k))
    reading("k_lo", f"k = {k_band[0]:.3f}, Texas alone", H(k_band[0]))
    reading("k_hi", f"k = {k_band[1]:.3f}, dry gas without fuel", H(k_band[1]))
    reading("k_permian", f"k = {kp_net:.3f}, EIA's Permian figures less fuel", H(kp_net))
    reading("k_fit", f"k = {fits['list']:.3f}, mid-2019 as full as {key(t0)}", H(fits["list"]))
    reading("no_tarzan", "Tarzan not counted", H(k, no_tarzan))
    hb_full = adds + [(hb1["month"], hb1["bcfd"])]
    reading("hb_full", f"Hugh Brinson phase I counted at {hb1['bcfd']:g} Bcf/d", H(k, hb_full))
    for alt in (M.add_months(t0, -1), M.add_months(t0, 1)):
        reading("t0_" + key(alt), f"full in {key(alt)} instead", H(k, adds, alt))

    # the pace, and how many months of it each line holds
    yrs = M.months_between(PACE_FROM, last) / 12
    pace = {"default": k * (P[last] - P[PACE_FROM]) / yrs, "k_permian": kp_net * (P[last] - P[PACE_FROM]) / yrs,
            "k_fit": fits["list"] * (P[last] - P[PACE_FROM]) / yrs}
    by_name = {e["name"]: e for e in pre + conf}
    Hd = H(k)
    lines = []
    for n in BIG:
        e = by_name[n]
        m = e["month"]
        before = Hd[M.add_months(m, -1)]
        back = next((t for t in months if t > m and Hd[t] <= before), None)
        lines.append({"name": SHORT[n], "month": key(m), "bcfd": e["bcfd"],
                      "months_default": 12 * e["bcfd"] / pace["default"],
                      "months_low": 12 * e["bcfd"] / pace["k_fit"],
                      "recovered": key(back) if back else None,
                      "recovery_months": M.months_between(m, back) if back else None})
    hero_starts = [e for e in pre + conf if e["bcfd"] >= 0.5 and e["month"] >= HERO_FROM]

    # by calendar year: the arithmetic's room, Waha's below-zero days, flaring
    neg = cited.reuters_counts()
    years = []
    for y in range(HERO_FROM[0], last[0] + 1):
        ms = [t for t in months if t[0] == y]
        vm = [t for t in vf if t[0] == y]
        row = {"year": y, "H_mean": st.fmean(Hd[t] for t in ms), "H_min": min(Hd[t] for t in ms),
               "H_mean_fit": st.fmean(H(fits["list"])[t] for t in ms), "neg": neg.get(y)}
        if len(vm) == 12:
            d = sum(sources.days(t) for t in vm)
            row["vf_bcfd"] = sum(vf[t][0] for t in vm) / 1e6 / d
            row["gross_bcfd"] = sum(vf[t][1] for t in vm) / 1e6 / d
            row["vf_share"] = row["vf_bcfd"] / row["gross_bcfd"]
        years.append(row)

    # gas needing a pipe added, against pipe added, from 2019
    a = (2019, 1)
    since = {"from": key(a), "dP": P[last] - P[a], "gas": k * (P[last] - P[a]),
             "gas_permian": kp_net * (P[last] - P[a]), "pipe": sum(b for m, b in adds if a < m <= last)}

    exp = [e for e in entries if e["status"] == "expected"]
    return {
        "splice": SPLICE, "splice_range": list(SPLICE_RANGE), "splice_n": SPLICE_N,
        "overlap_now": len(ov),
        "hero": {"x": [key(t) for t in months], "pipe": pipe, "gas": gas,
                 # the same line at the two-point k: the band between the two
                 # is the hero's statement that k is uncertain (review 2, 7)
                 "gas_fit": [fits["list"] * (P[t] - P[t0]) for t in months],
                 "starts": [{"name": SHORT.get(e["name"], e["name"]), "month": key(e["month"]), "bcfd": e["bcfd"]}
                            for e in hero_starts],
                 "vf": [flaring_share.get(key(t)) for t in months]},
        "H_hero": {key(t): v for t, v in Hd.items()},
        "pre_anchor": [{"name": e["name"], "month": key(e["month"]), "bcfd": e["bcfd"], "why": e["why"]} for e in pre],
        "k_permian": {"dry": kp_dry, "net": kp_net, "year": k_year},
        "k_fit": fits, "ref_2019": key(REF_2019),
        "H_ref_2019": {"default": Hd[REF_2019], "k_permian": H(kp_net)[REF_2019]},
        "readings": readings, "pace": pace, "pace_from": key(PACE_FROM), "lines": lines,
        "years": years, "since": since,
        "expected": [{"name": e["name"], "month": key(e["month"]), "bcfd": e["bcfd"], "stage": str(e["record"].get("Status") or "").strip(),
                      "months_default": 12 * e["bcfd"] / pace["default"]} for e in exp],
        "last": key(last),
    }
