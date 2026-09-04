"""
Industrial Heat Electrification Break-Even Model (Texas)
========================================================
Levelized Cost of Heat (LCOH, $/MMBtu delivered) comparison:
  resistive electric boiler vs conventional natural-gas boiler.

Scope locked per: industrialHeatingBEpointAbstractCreation.pdf (Energy Week packet)
Inputs/ranges per: "Industrial Heat Electrification for Process Steam in Texas_
  Literature, Data, and Modeling Inputs" (docx) and industrialHeatingExcelMaster.xlsx

Functional unit: 1 MMBtu of useful heat delivered to process.
LCOH = fuel + levelized capex + fixed O&M, all per MMBtu delivered.

All baseline numbers are placeholders traceable to the source doc's assumption
table (LBNL/DOE IAC Tipsheet #3, NREL EFS, Zuberi et al., EPA). Update PRICES
from EIA before poster use — see data/eia_price_template.csv.

Run:  python3 model.py     (writes PNGs to outputs/ and results CSVs)
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
from dataclasses import dataclass, asdict
import csv, os, json

KWH_PER_MMBTU = 293.07  # NREL EFS conversion

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(OUT, exist_ok=True)


@dataclass
class Params:
    # efficiencies (source doc: eta_e 0.95-0.99, eta_g 0.80-0.90; master xlsx base 0.98/0.85)
    eta_e: float = 0.98
    eta_g: float = 0.85
    # energy prices — UPDATE FROM EIA (EPM Table 5.6.A; TX industrial NG series)
    P_e: float = 0.065       # $/kWh, TX industrial retail electricity (placeholder)
    P_g: float = 3.50        # $/MMBtu, TX industrial natural gas (placeholder)
    # capex, installed, per unit thermal capacity (LBNL tipsheet / NREL EFS scaling;
    # electric ~40% below gas purchase price in EFS example; +-50% sensitivity)
    capex_g: float = 50000.0  # $ per (MMBtu/hr) capacity
    capex_e: float = 30000.0  # $ per (MMBtu/hr) capacity
    # fixed O&M as fraction of capex per year (doc: ~1% electric; gas higher, burner/tube maint.)
    fom_e: float = 0.01
    fom_g: float = 0.02
    # finance
    r: float = 0.08          # real discount rate (doc baseline 8%, range 5-12%)
    life: int = 20           # years (range 15-30)
    hours: float = 6000.0    # operating hours/yr at rated output (range 4000-8000; CF 47% ~ 4100 h)
    # emissions
    ef_gas: float = 53.06    # kgCO2/MMBtu fuel, EPA stationary combustion
    grid_ci: float = 0.333   # tCO2/MWh, the published ERCOT average: eGRID2023
    # (revised 2025-06-12) gives the ERCT subregion 733.862 lb CO2/MWh, which is
    # 0.3329 t/MWh. CO2 rather than the 736.629 CO2e rate, because ef_gas below
    # is a CO2 factor and the two have to be the same gas. Scenario variable.


def crf(r, n):
    """Capital recovery factor."""
    if r == 0:
        return 1.0 / n
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def lcoh(p: Params):
    """Return dict of LCOH components [$/MMBtu delivered] for gas and electric."""
    # fuel
    fuel_g = p.P_g / p.eta_g
    fuel_e = KWH_PER_MMBTU * p.P_e / p.eta_e
    # annual delivered heat per unit capacity (MMBtu/yr per MMBtu/hr rated)
    q_annual = p.hours
    lev_capex_g = p.capex_g * crf(p.r, p.life) / q_annual
    lev_capex_e = p.capex_e * crf(p.r, p.life) / q_annual
    fom_g_ = p.capex_g * p.fom_g / q_annual
    fom_e_ = p.capex_e * p.fom_e / q_annual
    return {
        "gas":  {"fuel": fuel_g, "capex": lev_capex_g, "fom": fom_g_,
                 "total": fuel_g + lev_capex_g + fom_g_},
        "elec": {"fuel": fuel_e, "capex": lev_capex_e, "fom": fom_e_,
                 "total": fuel_e + lev_capex_e + fom_e_},
    }


def breakeven_Pe(p: Params, full=True):
    """Electricity price [$/kWh] at which electric LCOH == gas LCOH.
    full=False -> fuel-only spark-gap threshold (doc's poster equation)."""
    if not full:
        return p.eta_e * p.P_g / (KWH_PER_MMBTU * p.eta_g)
    r = lcoh(p)
    nonfuel_gap = r["gas"]["total"] - (r["elec"]["capex"] + r["elec"]["fom"])
    return nonfuel_gap * p.eta_e / KWH_PER_MMBTU


def emissions(p: Params):
    """kgCO2 per MMBtu delivered."""
    e_gas = p.ef_gas / p.eta_g
    e_elec = p.grid_ci * KWH_PER_MMBTU / 1000.0 / p.eta_e * 1000.0  # tCO2/MWh -> kg/kWh
    return {"gas": e_gas, "elec": e_elec,
            "parity_grid_ci": p.ef_gas / p.eta_g * p.eta_e / KWH_PER_MMBTU}  # tCO2/MWh


# ----------------------------------------------------------------------------- figures
def fig_breakeven_line(p: Params):
    Pg = np.linspace(1.5, 8.0, 200)
    be_full, be_fuel = [], []
    for pg in Pg:
        q = Params(**{**asdict(p), "P_g": pg})
        be_full.append(breakeven_Pe(q) * 100)          # cents/kWh
        be_fuel.append(breakeven_Pe(q, full=False) * 100)
    be_full = np.array(be_full)
    be_fuel = np.array(be_fuel)
    retail = p.P_e * 100
    here = breakeven_Pe(p) * 100

    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))

    # No region fill above the break-even line: the shaded gap pulled the eye
    # to empty area and flattened the two lines the result rests on. The
    # dotted gap at the operating price, and its label, mark the one boundary
    # that matters (2026-09-04).
    ax.axhline(retail, color=figstyle.WARM, lw=1.6)
    ax.plot(Pg, be_full, color=figstyle.ACC, lw=2.6)
    ax.plot(Pg, be_fuel, color=figstyle.COOL, lw=2.0, ls="--")

    # Direct labels on the curves. A legend box is one more object to place and
    # the commonest thing for it to land on is the data.
    ax.annotate("break-even, full cost", xy=(Pg[-1], be_full[-1]),
                xytext=(-6, 9), textcoords="offset points", ha="right",
                color=figstyle.ACC, fontsize=FS_1)
    ax.annotate("fuel only", xy=(Pg[-1], be_fuel[-1]), xytext=(-6, -18),
                textcoords="offset points", ha="right",
                color=figstyle.COOL, fontsize=FS_1)
    ax.annotate(f"Texas industrial retail, {retail:.1f} ¢/kWh",
                xy=(Pg[0], retail), xytext=(5, -17),
                textcoords="offset points", ha="left",
                color=figstyle.WARM, fontsize=FS_1)

    # The answer, stated once, in the middle of the shaded gap where there is
    # guaranteed room for it.
    ax.annotate(f"electricity must fall about {retail/here:.1f}×\n"
                f"to {here:.2f} ¢/kWh at ${p.P_g:.2f} gas",
                xy=(p.P_g, (here + retail) / 2), xytext=(p.P_g + 0.45,
                                                         (here + retail) / 2),
                color=figstyle.INK, fontsize=FS_1, va="center",
                arrowprops=dict(arrowstyle="-|>", color=figstyle.DIM, lw=1.2,
                                shrinkA=2, shrinkB=2))
    ax.plot([p.P_g], [here], "o", color=figstyle.ACC, ms=7, zorder=5)
    ax.vlines(p.P_g, here, retail, color=figstyle.DIM, lw=1.0, ls=":")

    ax.set_xlim(Pg[0], Pg[-1])
    ax.set_ylim(0, retail * 1.12)
    ax.set_xlabel("Natural gas price  [$/MMBtu]")
    ax.set_ylabel("Electricity price  [¢/kWh]")
    figstyle.finish(fig, f"{OUT}/fig1_breakeven_price.png",
                    title="How cheap electricity has to get",
                    subtitle="Break-even price for an e-boiler to match a gas "
                             "boiler, per MMBtu delivered")


def fig_lcoh_bars(p: Params):
    r = lcoh(p)
    labels = ["Gas boiler", "Electric boiler"]
    fuel = [r["gas"]["fuel"], r["elec"]["fuel"]]
    cap = [r["gas"]["capex"], r["elec"]["capex"]]
    fom = [r["gas"]["fom"], r["elec"]["fom"]]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    b1 = ax.bar(labels, fuel, label="Fuel/energy", color=figstyle.COOL)
    b2 = ax.bar(labels, cap, bottom=fuel, label="Levelized capex", color=figstyle.WARM)
    ax.bar(labels, fom, bottom=np.array(fuel) + np.array(cap), label="Fixed O&M", color=figstyle.GREEN)
    for i, l in enumerate(labels):
        tot = fuel[i] + cap[i] + fom[i]
        ax.text(i, tot + 0.15, f"${tot:.2f}", ha="center", fontweight="bold")
    ax.set_ylabel("LCOH  [$/MMBtu delivered]")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    # The old title carried the parameters inline as "$P_e$=6.5¢/kWh,
    # $P_g$=$3.5/MMBtu": an odd number of dollar signs, so matplotlib stopped
    # treating them as mathtext and drew the markup raw, and the line ran off
    # the right edge of a 7in canvas. figstyle.finish already reserves a header
    # strip for exactly this, which is what every other figure here uses.
    figstyle.finish(fig, f"{OUT}/fig2_lcoh_stacked.png",
                    title="What the two boilers actually cost",
                    subtitle=f"{p.P_e*100:.1f}¢/kWh electricity, "
                             f"\\${p.P_g:g}/MMBtu gas, {p.hours:.0f} h/yr")


def fig_contour(p: Params):
    Pe = np.linspace(0.02, 0.12, 120)   # $/kWh
    Pg = np.linspace(1.5, 8.0, 120)
    PE, PG = np.meshgrid(Pe, Pg)
    gap = np.zeros_like(PE)
    base = asdict(p)
    for i in range(PG.shape[0]):
        for j in range(PE.shape[1]):
            q = Params(**{**base, "P_e": PE[i, j], "P_g": PG[i, j]})
            r = lcoh(q)
            gap[i, j] = r["elec"]["total"] - r["gas"]["total"]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))
    lim = np.nanmax(np.abs(gap))
    cs = ax.contourf(PE * 100, PG, gap, levels=21, cmap="RdBu_r", vmin=-lim, vmax=lim)
    zero = ax.contour(PE * 100, PG, gap, levels=[0], colors=figstyle.INK, linewidths=2)
    ax.clabel(zero, fmt="parity")
    ax.plot(p.P_e * 100, p.P_g, "*", color=figstyle.INK, ms=16)
    ax.annotate("TX baseline", (p.P_e * 100 + 0.15, p.P_g + 0.1))
    fig.colorbar(cs, label="LCOH(elec) − LCOH(gas)  [$/MMBtu]")
    ax.set_xlabel("Electricity price  [¢/kWh]")
    ax.set_ylabel("Natural gas price  [$/MMBtu]")
    figstyle.finish(fig, f"{OUT}/fig3_costgap_contour.png")


def fig_tornado(p: Params):
    base_gap = lcoh(p)["elec"]["total"] - lcoh(p)["gas"]["total"]
    swings = {
        "Electricity price (4.5–9.0 ¢/kWh)": ("P_e", 0.045, 0.090),
        "Gas price ($2.0–6.0/MMBtu)": ("P_g", 2.0, 6.0),
        "Operating hours (4000–8000)": ("hours", 4000, 8000),
        "Gas boiler η (0.80–0.90)": ("eta_g", 0.80, 0.90),
        "Electric boiler η (0.95–0.99)": ("eta_e", 0.95, 0.99),
        "Electric capex ±50%": ("capex_e", 15000, 45000),
        "Gas capex ±50%": ("capex_g", 25000, 75000),
        "Discount rate (5–12%)": ("r", 0.05, 0.12),
    }
    rows = []
    for label, (k, lo, hi) in swings.items():
        g_lo = (lambda q: lcoh(q)["elec"]["total"] - lcoh(q)["gas"]["total"])(
            Params(**{**asdict(p), k: lo}))
        g_hi = (lambda q: lcoh(q)["elec"]["total"] - lcoh(q)["gas"]["total"])(
            Params(**{**asdict(p), k: hi}))
        rows.append((label, g_lo, g_hi))
    rows.sort(key=lambda t: abs(t[2] - t[1]))
    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))
    for i, (label, lo, hi) in enumerate(rows):
        ax.barh(i, hi - lo, left=lo, color=figstyle.COOL if hi >= lo else figstyle.ACC, alpha=0.85)
        ax.text(min(lo, hi) - 0.1, i, label, ha="right", va="center", fontsize=FS_2)
    ax.axvline(base_gap, color=figstyle.INK, lw=1.5, label=f"baseline gap = ${base_gap:.2f}")
    ax.axvline(0, color=figstyle.WARM, ls="--", lw=1.2, label="parity")
    ax.set_yticks([])
    ax.set_xlabel("LCOH(elec) − LCOH(gas)  [$/MMBtu delivered]")
    ax.legend(loc="lower right", fontsize=FS_2)
    ax.grid(axis="x", alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig4_tornado.png")


def fig_emissions(p: Params):
    ci = np.linspace(0, 0.6, 200)  # tCO2/MWh
    e_el = ci * KWH_PER_MMBTU / p.eta_e  # kg/MMBtu (t/MWh == kg/kWh)
    em = emissions(p)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))
    ax.plot(ci, e_el, lw=2.5, label="Electric boiler (avg grid CI)")
    ax.axhline(em["gas"], color=figstyle.WARM, lw=2.5, label=f"Gas boiler = {em['gas']:.1f} kg/MMBtu")
    ax.axvline(em["parity_grid_ci"], color=figstyle.DIM, ls="--", lw=1.5)
    ax.annotate(f"parity @ {em['parity_grid_ci']:.3f} tCO₂/MWh",
                (em["parity_grid_ci"] + 0.01, 10), fontsize=FS_1)
    ax.plot(p.grid_ci, p.grid_ci * KWH_PER_MMBTU / p.eta_e, "*", color=figstyle.INK, ms=15)
    # left of the star, not right: the label is long enough that the old
    # right-hand offset ran it off the canvas
    ax.annotate(f"ERCOT average, eGRID2023 ({p.grid_ci:g})",
                (p.grid_ci, p.grid_ci * KWH_PER_MMBTU / p.eta_e),
                xytext=(12, -16), textcoords="offset points", ha="left",
                fontsize=FS_2, color=figstyle.INK)
    ax.set_xlabel("Grid carbon intensity  [tCO₂/MWh]")
    ax.set_ylabel("Emissions  [kgCO₂ / MMBtu delivered]")
    ax.legend(fontsize=FS_2)
    ax.grid(alpha=0.3)
    figstyle.finish(fig, f"{OUT}/fig5_emissions_parity.png")


def main():
    p = Params()
    r = lcoh(p)
    em = emissions(p)
    summary = {
        "LCOH_gas_$/MMBtu": round(r["gas"]["total"], 3),
        "LCOH_elec_$/MMBtu": round(r["elec"]["total"], 3),
        "gap_$/MMBtu": round(r["elec"]["total"] - r["gas"]["total"], 3),
        "breakeven_Pe_cents/kWh_fullLCOH": round(breakeven_Pe(p) * 100, 3),
        "breakeven_Pe_cents/kWh_fuelOnly": round(breakeven_Pe(p, full=False) * 100, 3),
        "emissions_gas_kg/MMBtu": round(em["gas"], 2),
        "emissions_elec_kg/MMBtu": round(em["elec"], 2),
        "emissions_parity_gridCI_t/MWh": round(em["parity_grid_ci"], 4),
    }
    with open(f"{OUT}/summary.json", "w") as f:
        json.dump({"params": asdict(p), "results": summary}, f, indent=2)
    with open(f"{OUT}/summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in summary.items():
            w.writerow([k, v])
    fig_breakeven_line(p)
    fig_lcoh_bars(p)
    fig_contour(p)
    fig_tornado(p)
    fig_emissions(p)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
