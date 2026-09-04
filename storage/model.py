"""
Storage Revenue Stack Simulator — ERCOT-style Battery Arbitrage (LP)
====================================================================
"Model 1" from 2yearPlanWeeklyModeling.pdf (storage revenue stack simulator,
baseline + sensitivity framework). Also covers options #1 and #24 from
UT_Energy_Poster_Options_Table (battery arbitrage backtest; 2h vs 4h vs 8h value).

Perfect-foresight LP dispatch of a 1 MW battery against hourly prices:
    max  sum_t  p_t*(dis_t - ch_t) - c_deg*(dis_t + ch_t)/2
    s.t. soc_{t+1} = soc_t + eta_c*ch_t - dis_t/eta_d,  0 <= soc <= E
         0 <= ch_t, dis_t <= P_max
Perfect foresight = upper bound on arbitrage revenue; note in write-ups.

PRICES: real ERCOT settlement data is not reachable from this sandbox
(ercot.com blocked). The model generates a documented synthetic hourly year
calibrated to ERCOT DAM statistics (diurnal + seasonal shape, scarcity spikes,
occasional negative prices). Drop a real ERCOT CSV at data/prices.csv
(columns: timestamp, price_usd_mwh) and it will be used automatically.

Run: python3 model.py    (writes PNGs + CSVs to outputs/, ~1 min for 3 LPs)
"""
import numpy as np
import matplotlib
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import figstyle
figstyle.use()
import pulp, os, json, csv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)


# --------------------------------------------------------------------- prices
def synthetic_ercot_prices(hours=8760):
    """Synthetic ERCOT-like hourly DAM prices, documented + reproducible (seed 42).
    Calibration targets (approximate, based on public ERCOT summaries):
    mean ~$35-45/MWh, summer scarcity spikes, ~1-2% negative hours."""
    t = np.arange(hours)
    day = t // 24
    hod = t % 24
    doy = day % 365
    seasonal = 30 + 12 * np.exp(-((doy - 205) ** 2) / (2 * 45 ** 2))       # summer bump
    diurnal = 1.0 + 0.35 * np.exp(-((hod - 18) ** 2) / (2 * 2.5 ** 2)) \
                  + 0.15 * np.exp(-((hod - 8) ** 2) / (2 * 2.0 ** 2)) \
                  - 0.25 * np.exp(-((hod - 3) ** 2) / (2 * 3.0 ** 2)) \
                  - 0.20 * np.exp(-((hod - 13) ** 2) / (2 * 2.0 ** 2))     # solar belly
    noise = rng.lognormal(mean=0.0, sigma=0.35, size=hours)
    base = seasonal * diurnal * noise
    # scarcity spikes: mostly summer evenings
    spike_prob = 0.002 + 0.02 * np.exp(-((doy - 205) ** 2) / (2 * 30 ** 2)) * \
                 np.exp(-((hod - 18) ** 2) / (2 * 2.0 ** 2))
    spikes = rng.random(hours) < spike_prob
    base[spikes] *= rng.uniform(8, 60, spikes.sum())
    base = np.minimum(base, 5000.0)                                        # cap
    # negative-price hours (wind-heavy nights, spring)
    # Applied only where no scarcity spike was written, and no longer gated on
    # the diurnal shape, which previously halved the intended rate to 0.7%.
    neg = (rng.random(hours) < 0.015) & (~spikes)
    base[neg] = -rng.uniform(1, 20, neg.sum())
    return base


def load_prices():
    f = os.path.join(HERE, "data", "prices.csv")
    if os.path.exists(f):
        import pandas as pd
        df = pd.read_csv(f)
        p = df["price_usd_mwh"].to_numpy(float)
        print(f"loaded {len(p)} real price hours from data/prices.csv")
        return p, "real"
    return synthetic_ercot_prices(), "synthetic (seed 42, calibrated shape)"


# --------------------------------------------------------------------- LP dispatch
def optimize(prices, duration_h=4, p_max=1.0, rte=0.86, c_deg=2.0,
             soc0_frac=0.5, chunk_days=30):
    """Perfect-foresight LP, solved in monthly chunks (SoC carried across chunks).
    Returns dict with dispatch arrays and annual metrics. c_deg in $/MWh throughput."""
    eta = np.sqrt(rte)
    E = duration_h * p_max
    n = len(prices)
    ch = np.zeros(n); dis = np.zeros(n); soc = np.zeros(n + 1)
    soc[0] = soc0_frac * E
    chunk = chunk_days * 24
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        T = range(s, e)
        prob = pulp.LpProblem("arb", pulp.LpMaximize)
        c = pulp.LpVariable.dicts("c", T, 0, p_max)
        d = pulp.LpVariable.dicts("d", T, 0, p_max)
        x = pulp.LpVariable.dicts("soc", range(s, e + 1), 0, E)
        prob += pulp.lpSum(prices[t] * (d[t] - c[t]) - c_deg * 0.5 * (d[t] + c[t])
                           for t in T)
        prob += x[s] == soc[s]
        for t in T:
            prob += x[t + 1] == x[t] + eta * c[t] - d[t] / eta
            # Charging and discharging in the same hour must be forbidden
            # explicitly. Without this the LP will, at a sufficiently negative
            # price, charge and discharge at once purely to dissipate energy —
            # it earns |p|*c*(1-rte) for a cycling charge of
            # 0.5*c_deg*c*(1+rte), which pays whenever the price is below
            # about -$13/MWh at these defaults. The synthetic price series
            # never triggers it, but ERCOT reaches -$250/MWh, so a real price
            # file would. One linear constraint closes it: at most one of the
            # two can run at full power, which is what a real inverter does.
            prob += c[t] + d[t] <= p_max
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        for t in T:
            ch[t] = c[t].value(); dis[t] = d[t].value()
            soc[t + 1] = x[t + 1].value()
    gross = float(np.sum(prices * (dis - ch)))
    # The LP already charges itself for cycling; reporting the gross figure
    # while the objective maximised the net one overstates revenue and, worse,
    # flattens the cycling-cost sensitivity to near-nothing. Both are reported
    # here and the net one is the headline.
    deg_cost = float(c_deg * 0.5 * np.sum(dis + ch))
    net = gross - deg_cost
    thru = float(np.sum(dis))
    # Equivalent full cycles are counted on the storage side, not the meter
    # side. One full traversal of the state of charge delivers only eta*E to
    # the grid, so dividing AC discharge by E understates cycles by 1/eta.
    cycles = thru / (E * eta)
    # A "4 hour" battery bounded on the state of charge sustains rated output
    # for E*eta/p_max hours, not E/p_max. Report what it actually delivers.
    duration_ac = E * eta / p_max
    ann = 8760 / len(prices)
    return dict(ch=ch, dis=dis, soc=soc[:-1],
                revenue=net, revenue_gross=gross, deg_cost=deg_cost,
                throughput=thru, cycles=cycles,
                rev_per_kw_yr=net / (p_max * 1000) * ann,
                rev_per_kw_yr_gross=gross / (p_max * 1000) * ann,
                duration=duration_h, duration_ac=duration_ac,
                rte=rte, c_deg=c_deg)


# --------------------------------------------------------------------- capital cost reference
# Source: the Annual Technology Baseline (ATB) 2024 electricity dataset,
# downloaded directly from
#   https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv/2024/v3.0.0/ATBe.csv
# (NREL has rebranded to NLR; the ATB now lives at https://atb.nlr.gov/ - the
# old atb.nrel.gov address is what was unreachable when this model first
# picked up a $334/kWh capex from search-engine summaries instead of the
# primary source. That figure was wrong; the values below are the real ones.)
#
# Row: technology = Utility-Scale Battery Storage, 4Hr Battery Storage,
# Moderate scenario, Market case, core_metric_variable 2024.
#
# CAPEX is confirmed $/kW, not $/kWh, because it is exactly the sum of ATB's
# own cost-component rows for this technology/year:
#   OCC (overnight capital cost)     1769.877 $/kW
#   GCC (grid connection cost)        100.000 $/kW
#   CFC (construction finance cost)    68.327 $/kW
#   ---------------------------------------------
#   CAPEX                            1938.204 $/kW   (= $484.55/kWh for this 4h system)
# Fixed O&M                            44.247 $/kW-yr
#
# ATB does not publish a fixed-charge rate for standalone storage (it has no
# LCOE, since it does not sell energy at a single levelized price), so the
# capex is annualized here with a plain capital-recovery factor at this
# site's house discount rate (8% real, matching heat/model.py's Params.r)
# over ATB's own capital recovery period for this technology, 20 years (the
# dataset carries crpyears values of 20 and 30 for this row; the reported
# capex and O&M figures are identical either way, so 20 is used directly
# rather than assumed):
#   CRF = r(1+r)^n / ((1+r)^n - 1), r = 0.08, n = 20  =>  CRF ≈ 0.101852
#   annualized = CRF * CAPEX + Fixed O&M
#              ≈ 0.101852 * 1938.204 + 44.247 ≈ 197.41 + 44.247 ≈ 241.66 $/kW-yr
ATB_OCC_USD_PER_KW_2024 = 1769.877
ATB_GCC_USD_PER_KW_2024 = 100.000
ATB_CFC_USD_PER_KW_2024 = 68.327
ATB_CAPEX_USD_PER_KW_2024 = (ATB_OCC_USD_PER_KW_2024 + ATB_GCC_USD_PER_KW_2024
                              + ATB_CFC_USD_PER_KW_2024)
ATB_FOM_USD_PER_KW_YR_2024 = 44.247
ATB_DISCOUNT_RATE = 0.08
ATB_CRP_YR = 20


def annualized_storage_cost_per_kw_yr():
    """Annualized capital + fixed O&M cost of a 4-hour utility-scale battery,
    $/kW-yr, from the ATB inputs documented above. This is a cost reference
    for scale, not a revenue-vs-cost verdict: it excludes capacity payments,
    ancillary services, and every other revenue stream a real battery earns
    besides energy arbitrage."""
    r, n = ATB_DISCOUNT_RATE, ATB_CRP_YR
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    return crf * ATB_CAPEX_USD_PER_KW_2024 + ATB_FOM_USD_PER_KW_YR_2024


# --------------------------------------------------------------------- figures
def fig_price_duration(prices, tag):
    srt = np.sort(prices)[::-1]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=fig_size(NOTES, 2.2))
    a1.plot(srt, lw=2)
    a1.set_yscale("symlog", linthresh=100)
    a1.set_xlabel("Hours (sorted)"); a1.set_ylabel("Price [$/MWh]")
    # These titles ran wider than a two-up subplot at the default title size,
    # colliding with each other and clipping off the right edge - shorter
    # text and a smaller size here, not just a wider figure, since the
    # figure width is capped by the site's own column width regardless.
    a1.grid(alpha=0.3)
    a2.plot(np.arange(24), [prices[h::24].mean() for h in range(24)], lw=2.5, marker="o", ms=4)
    a2.set_xlabel("Hour of day"); a2.set_ylabel("Mean price [$/MWh]")
    a2.grid(alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig1_prices.png")


def fig_dispatch_week(res, prices, start_day=200):
    s, e = start_day * 24, (start_day + 7) * 24
    t = np.arange(s, e)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=fig_size(NOTES, PLOT), sharex=True)
    a1.plot(t, prices[s:e], color=figstyle.DIM, lw=1.5)
    a1.set_ylabel("Price [$/MWh]"); a1.set_yscale("symlog", linthresh=100)
    a1.grid(alpha=0.3)
    a2.bar(t, res["dis"][s:e], color=figstyle.GREEN, label="discharge [MW]")
    a2.bar(t, -res["ch"][s:e], color=figstyle.WARM, label="charge [MW]")
    a2.plot(t, res["soc"][s:e] / (res["duration"]), color=figstyle.COOL, lw=1.5,
            label="SoC [fraction]")
    # Outside the axes, not a fixed corner: the dispatch bars and SoC line
    # both regularly saturate every corner of this panel (batteries that spend
    # most of a summer week pinned near full/empty), so any in-axes loc
    # eventually sits on top of data as the synthetic price series moves. A
    # figure-level legend with an "outside" loc reserves its own strip via
    # constrained_layout instead of sitting inside axes space, which is the
    # one placement that cannot collide regardless of how the bars/line are
    # shaped. (ax.legend() rejects "outside ..." locs - only fig.legend()
    # accepts them - so the handles are pulled from a2 and handed to fig.)
    handles, labels = a2.get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3,
               frameon=False, fontsize=FS_1)
    a2.set_xlabel("Hour of year"); a2.grid(alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig2_dispatch_week.png")


def fig_duration_value(results):
    durs = [r["duration"] for r in results]
    revs = [r["rev_per_kw_yr"] for r in results]
    cyc = [r["cycles"] for r in results]
    x = np.arange(len(durs))
    cap_cost = annualized_storage_cost_per_kw_yr()

    # Two panels, two scales on purpose: the main panel is sized to the
    # revenue bars alone, so the taper from step to step - the reason this
    # figure exists - stays the tallest thing on the page. The capital-cost
    # comparison needs a much bigger number (~$242) on the same axis, and
    # sharing one scale between them used to squash the revenue bars into the
    # bottom of the panel. Giving the cost its own narrow companion axes lets
    # both be legible without either rescaling the other.
    fig, (a1, a2) = plt.subplots(
        1, 2, figsize=fig_size(NOTES, 1.6), gridspec_kw={"width_ratios": [2.3, 1.3]})

    bars = a1.bar(x, revs, color=figstyle.COOL, alpha=0.9, width=0.55)
    a1.set_xticks(x)
    a1.set_xticklabels([f"{d}h\n{c:.0f} cycles/yr" for d, c in zip(durs, cyc)])
    top = max(revs) * 1.45
    for b, r in zip(bars, revs):
        a1.text(b.get_x() + b.get_width() / 2, r + top * 0.02, f"${r:.1f}/kW-yr",
                ha="center", va="bottom", fontsize=FS_1)

    # The headline is the *step*, not the level: a dotted line holds the
    # previous bar's height out to the next bar's position, and a vertical
    # arrow in the gap between the two bars - not on top of either one - is
    # exactly the revenue gained by extending duration further. Anchoring the
    # arrow and its label at the midpoint between the bars, rather than at the
    # next bar's own x position, is what keeps both away from the bars and
    # their value labels regardless of how the numbers move.
    for i in range(len(durs) - 1):
        y0, y1 = revs[i], revs[i + 1]
        x_mid = (x[i] + x[i + 1]) / 2
        # Inset the arrow from both ends so it doesn't touch the dotted line
        # or the bar top, but cap the inset at a fraction of the step itself -
        # a fixed inset sized for the bigger step swallowed the smaller step
        # whole and inverted the arrow (tail ended up above head).
        inset = min(top * 0.015, (y1 - y0) * 0.3)
        a1.plot([x[i], x[i + 1]], [y0, y0], ls=":", color=figstyle.DIM, lw=1.3)
        a1.annotate("", xy=(x_mid, y1 - inset), xytext=(x_mid, y0 + inset),
                    arrowprops=dict(arrowstyle="-|>", color=figstyle.ACC, lw=1.8))
        a1.text(x_mid, max(y0, y1) + top * 0.09, f"+${y1 - y0:.1f}/kW-yr",
                ha="center", va="bottom", fontsize=FS_1, color=figstyle.INK)

    a1.set_ylabel("Arbitrage revenue [$/kW-yr]")
    a1.set_ylim(0, top)
    a1.set_xlim(-0.6, len(durs) - 1 + 0.6)
    a1.grid(axis="y", alpha=0.3)
    # Drop any auto-placed tick that lands right under the axis top: a tick
    # label is centered on its data value, so one within a few percent of
    # `top` pokes its upper half past the axes spine and into the reserved
    # title strip above the figure. The headroom in `top` exists so the
    # tallest bar and its annotation have room to breathe, not so a tick can
    # sit flush with it.
    a1.set_yticks([t for t in a1.get_yticks() if t <= top * 0.85])

    # Capital-cost reference (ATB 2024, see annualized_storage_cost_per_kw_yr
    # above for the source and the annualization math), on its own axes with
    # its own scale so the ~$242 figure never dictates the revenue panel's
    # y-range. It sits next to the best-case revenue bar so the two numbers
    # are readable at a glance without crushing anything else.
    best_dur, best_rev = durs[-1], revs[-1]
    cx = np.arange(2)
    cvals = [best_rev, cap_cost]
    cbars = a2.bar(cx, cvals, color=[figstyle.COOL, figstyle.WARM],
                    alpha=0.9, width=0.6)
    ctop = cap_cost * 1.36   # headroom for the value label and the top tick, now that no title strip sits above
    for b, v in zip(cbars, cvals):
        a2.text(b.get_x() + b.get_width() / 2, v + ctop * 0.02, f"${v:.0f}",
                ha="center", va="bottom", fontsize=FS_1)
    a2.set_xticks(cx)
    a2.set_xticklabels([f"Best case\n({best_dur}h arbitrage)",
                        "Capital cost\n(4h system)"])
    a2.set_ylim(0, ctop)
    a2.set_yticks([0, 100, 200])   # the locator would also own a tick at the frame's edge
    a2.set_xlim(-0.6, 1.6)
    a2.grid(axis="y", alpha=0.3)

    # No literal "$" pairs in the subtitle or footnote: matplotlib's mathtext
    # parser treats text between two unescaped "$" as a math expression, and
    # these strings have multiple dollar amounts - the first version of this
    # figure silently mangled into something unreadable when written with a
    # bare "$" in it.
    step_a, step_b = revs[1] - revs[0], revs[2] - revs[1]
    figstyle.finish(fig, f"{OUT}/fig3_duration_value.png",
        title="Energy-arbitrage value by duration (perfect foresight upper bound)",
        subtitle=(f"Added value shrinks with duration: +{step_a:.1f}/kW-yr going "
                  f"{durs[0]}h→{durs[1]}h, then only +{step_b:.1f}/kW-yr "
                  f"going {durs[1]}h→{durs[2]}h"),
        footnote=(f"NREL ATB 2024 — annualized capex + FOM, 4h system: {cap_cost:.0f}/kW-yr. "
                  "Scale reference, not a payback verdict: energy arbitrage is only one of\n"
                  "several revenue streams a real battery earns (capacity, ancillary services)."))


def fig_sensitivity(prices):
    rtes = [0.80, 0.86, 0.92]
    degs = [0.0, 2.0, 5.0, 10.0]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    for rte in rtes:
        vals = [optimize(prices, 4, rte=rte, c_deg=cd)["rev_per_kw_yr"] for cd in degs]
        ax.plot(degs, vals, marker="o", lw=2.5, label=f"RTE {rte:.0%}")
    ax.set_xlabel("Degradation cost  [$/MWh throughput]")
    ax.set_ylabel("Revenue  [$/kW-yr]")
    ax.legend(); ax.grid(alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig4_sensitivity.png")


def fig_monthly(res, prices):
    rev_m = []
    for m in range(12):
        s, e = m * 730, (m + 1) * 730
        rev_m.append(np.sum(prices[s:e] * (res["dis"][s:e] - res["ch"][s:e])) / 1000)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))
    # Numeric positions, not the month letters as categories. Passing the
    # letters straight to bar() made matplotlib treat them as categories, and
    # because J, M and A each appear more than once it collapsed them: the
    # chart drew eight bars for twelve months and silently dropped May, June,
    # July and August - the scarcity months this figure exists to show.
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.bar(range(12), rev_m, color=figstyle.WARM)
    ax.set_xticks(range(12))
    ax.set_xticklabels(months)
    ax.set_ylabel("Revenue [$k, 1 MW / 4 h]")
    ax.grid(axis="y", alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig5_monthly.png")


def main():
    prices, tag = load_prices()
    fig_price_duration(prices, tag)
    results = [optimize(prices, d) for d in (2, 4, 8)]
    r4 = results[1]
    fig_dispatch_week(r4, prices)
    fig_duration_value(results)
    fig_monthly(r4, prices)
    fig_sensitivity(prices)
    summary = {
        "price_source": tag,
        "price_mean": round(float(prices.mean()), 2),
        "price_p99": round(float(np.percentile(prices, 99)), 1),
        "neg_hours": int((prices < 0).sum()),
        **{f"rev_$/kW-yr_{r['duration']}h": round(r["rev_per_kw_yr"], 1) for r in results},
        **{f"cycles_{r['duration']}h": round(r["cycles"], 1) for r in results},
    }
    with open(f"{OUT}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    with open(f"{OUT}/summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        [w.writerow([k, v]) for k, v in summary.items()]
    # hourly dispatch CSV for the workbook
    with open(f"{OUT}/dispatch_4h.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hour", "price_usd_mwh", "charge_mw", "discharge_mw", "soc_mwh"])
        for t in range(len(prices)):
            w.writerow([t, round(prices[t], 2), round(r4["ch"][t], 4),
                        round(r4["dis"][t], 4), round(r4["soc"][t], 4)])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
