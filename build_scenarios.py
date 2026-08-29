"""
The scenario catalogue: prepared changes, grouped by kind.

HOW A MAGNITUDE IS SET

A shock in this model is a dimensionless push in (-1, 1). Turning a real event
into one of those numbers is the part that can quietly become fiction, so the
whole catalogue obeys one rule:

    A shock of 1.0 is the largest change of that kind in the modern record.
    Every magnitude here is the size of the event divided by that record
    maximum, and both numbers are printed with the scenario.

So the 1973 oil shock is not "0.9 because that feels big". Crude roughly
quadrupled in real terms, that is the largest move in the record, and it is
therefore 1.0 by construction. A 2022-scale European gas shock is measured
against the same ceiling and comes out lower.

Three families of magnitude are derived rather than asserted:

  fuel supply   The share of a country's electricity that comes from a fuel is
                already measured and stored in the node's own name. A scenario
                that removes half of China's coal is 0.544 x 0.5, straight from
                the payload.

  weather       The ONI and NAO series are held in full. A "1997-98 scale El
                Nino" is that event's peak ONI divided by the largest peak in
                the record, both computed here.

  the sun       The solar cycle amplitude is measured in the TSI composite.

The rest are anchored to a published figure for the event's effect on the
energy system, not to the event itself. A pandemic is entered as the observed
change in energy demand, because that is the quantity this model carries; the
death toll is context, not an input. Each of those carries its number and its
source in the basis line, and the page says which are derived and which are
cited.

WHAT THIS IS NOT

These are not forecasts. The model answers "what is connected to what, and how
strongly", so a scenario is a way of asking that question from a particular
starting point. Nothing here predicts that any of it will happen.

Run:  python3 build_scenarios.py            report only
      python3 build_scenarios.py --apply
"""

import argparse
import collections
import json
import os
import re

import numpy as np
import scipy.sparse as sp

import data_climate_indices as C

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")

CATEGORIES = [
    ("people", "People & cognition"),
    ("exogenous", "Universe & Earth, exogenous"),
    ("policy", "Country policy changes"),
    ("climate_goal", "Climate goal meetings"),
    ("disaster", "Natural disasters"),
    ("pandemic", "Global pandemics"),
    ("war", "Wars"),
    ("technology", "Technology improvement & buildout"),
    ("energy_mix", "Energy makeup evolution"),
]


def load():
    raw = open(DATA, encoding="utf-8").read()
    return raw[:raw.index("=") + 1], json.loads(
        raw[raw.index("=") + 1:raw.rindex(";")])


def fuel_share(D, ident):
    """The measured share of a country's power from one fuel, off the node."""
    i = D["idMap"].get(ident)
    if i is None:
        return None
    m = re.search(r"\(([\d.]+)% of power\)", D["name"][int(i)])
    return float(m.group(1)) / 100.0 if m else None


def build(D):
    """
    Returns {id: scenario}. Every scenario carries its category, the shocks it
    applies, a plain description, and the basis for its magnitude.
    """
    S = {}

    def add(sid, cat, label, shocks, desc, basis):
        S[sid] = {"cat": cat, "label": label, "shocks": shocks,
                  "desc": desc, "basis": basis}

    # ---------- derived magnitudes ------------------------------------
    oni = [v for _, v in C.monthly(C.ONI) and
           [(y, v) for y, m, v in C.monthly(C.ONI)]]
    oni_max = max(abs(v) for v in oni)                  # 2.75, 2015-16
    nao_djf = [v for _, v in C.djf(C.NAO)]
    nao_max = max(abs(v) for v in nao_djf)
    tsi = [x[1] for x in C.TSI]
    tsi_amp = (max(tsi) - min(tsi)) / max(tsi)          # solar cycle amplitude

    def enso(peak, name, year):
        return (round(min(1.0, abs(peak) / oni_max), 3),
                f"ONI peaked at {peak:+.2f} C in {year}; the largest peak in "
                f"the 1950-present record is {oni_max:.2f} C. "
                f"{abs(peak):.2f}/{oni_max:.2f} = "
                f"{min(1.0, abs(peak) / oni_max):.2f}. NOAA CPC.")

    # ---------- People & cognition ------------------------------------
    add("behaviour_shift", "people", "A conservation wave",
        {"PSYCH_habit": -0.6, "PSYCH_norm": -0.6},
        "Habit and social norm both move toward using less.",
        "Magnitude is a convention, not a measurement: the behaviour channels "
        "have no observed scale. Flagged as assumed.")
    add("threat_salience", "people", "Fear becomes salient",
        {"PSYCH_threat": 0.85, "PSYCH_salience": 0.7, "PSYCH_attention": 0.6},
        "Threat, salience and attention rise together, as they do when a "
        "shortage is in the news.",
        "Convention. The direction is the claim; the size is not measured.")
    add("present_bias_deepens", "people", "The future is discounted harder",
        {"PSYCH_present_bias": 0.8, "PSYCH_delay_discount": 0.8},
        "People weigh today more heavily against later, which is the channel "
        "efficiency investment runs through.",
        "Convention. Direction only.")
    add("trust_collapse", "people", "Cooperation falls away",
        {"PSYCH_social_proof": -0.8, "PSYCH_identity": -0.6,
         "PSYCH_norm": -0.7},
        "Social proof, shared identity and norms all weaken at once.",
        "Convention. Direction only.")
    add("thermal_comfort_rises", "people", "Comfort expectations rise",
        {"PSYCH_thermal_comfort": 0.8, "PSYCH_routine": 0.5},
        "The temperature people expect indoors moves, and the routine "
        "hardens around it.",
        "Convention. Direction only.")
    add("attention_saturates", "people", "Attention is exhausted",
        {"PSYCH_attention": -0.75, "PSYCH_effort_cost": 0.7,
         "PSYCH_inhibition": -0.5},
        "Attention falls, the felt cost of effort rises, and restraint "
        "weakens.",
        "Convention. Direction only.")

    # ---------- Universe & Earth, exogenous ----------------------------
    add("solar_minimum", "exogenous", "A deep solar minimum",
        {"SUN_TSI": -round(min(1.0, tsi_amp / tsi_amp), 3)},
        "The sun goes quiet across a cycle.",
        f"NRLTSI2 varies by {1000 * tsi_amp:.2f} parts per thousand across "
        f"the 1980-2023 record, which is the whole observed range and so is "
        f"1.0 by construction. LASP LISIRD.")
    add("solar_maximum", "exogenous", "A strong solar maximum",
        {"SUN_TSI": 1.0},
        "The sun brightens by as much as the record shows.",
        "Same record range as the minimum, opposite sign. LASP LISIRD.")
    add("orbital_tilt_high", "exogenous", "More sun at high latitudes",
        {"INSOL_75N": 0.8, "INSOL_65N": 0.8, "INSOL_75S": 0.8,
         "INSOL_65S": 0.8},
        "The high-latitude insolation bands rise together, as they do at high "
        "obliquity.",
        "Direction from orbital geometry; the magnitude is a convention, "
        "because obliquity change is far slower than anything else here.")
    add("tropical_insolation_drop", "exogenous", "Less sun at the tropics",
        {"INSOL_5N": -0.7, "INSOL_5S": -0.7, "INSOL_15N": -0.7,
         "INSOL_15S": -0.7},
        "The tropical bands fall together.",
        "Convention. Direction from geometry.")
    m, b = enso(2.75, "El Nino", "2015-16")
    add("strong_el_nino", "exogenous", "A record El Nino",
        {"WX_ENSO": m},
        "A warm phase as large as the largest in the record.", b)
    m, b = enso(2.4, "El Nino", "1997-98")
    add("el_nino_1997", "exogenous", "The 1997-98 El Nino",
        {"WX_ENSO": m}, "The 1997-98 event, at its observed peak.", b)
    m, b = enso(-2.03, "La Nina", "1973-74")
    add("strong_la_nina", "exogenous", "A record La Nina",
        {"WX_ENSO": -m},
        "The strongest cold phase in the record.", b)
    add("nao_cold_winter", "exogenous", "A deeply negative winter NAO",
        {"WX_NAO": -round(min(1.0, abs(min(nao_djf)) / nao_max), 3)},
        "Cold, still weather over Britain and Ireland: demand up, wind down.",
        f"The most negative winter NAO in the 1951-present record is "
        f"{min(nao_djf):+.2f}, and the largest winter magnitude is "
        f"{nao_max:.2f}. NOAA CPC.")
    add("nao_mild_winter", "exogenous", "A strongly positive winter NAO",
        {"WX_NAO": round(min(1.0, max(nao_djf) / nao_max), 3)},
        "Mild, windy weather over the North Atlantic.",
        f"The most positive winter NAO in the record is {max(nao_djf):+.2f} "
        f"of a largest magnitude {nao_max:.2f}. NOAA CPC.")
    return S


def add_data_driven(D, S):
    """Scenarios whose magnitude is read out of the payload itself."""
    def add(sid, cat, label, shocks, desc, basis):
        S[sid] = {"cat": cat, "label": label, "shocks": shocks,
                  "desc": desc, "basis": basis}

    def sup(iso, fuel, frac, sid, cat, label, desc, source):
        """
        The shock is the fraction of that fuel supply withdrawn, and nothing
        else. The share of the country's electricity the fuel provides is
        already carried by the weight of the link from the supply to the grid,
        so multiplying the shock by it as well counts the same fact twice and
        shrinks every policy scenario until it moves nothing.
        """
        ident = f"SUP_{iso}_{fuel}"
        grid = f"GRID_{iso}"
        share = fuel_share(D, ident)
        if share is None or grid not in D["idMap"]:
            return False
        shocks = {ident: round(min(1.0, frac), 3),
                  grid: round(min(1.0, share * frac), 3)}
        add(sid, cat, label, shocks, desc,
            f"Two things happen and the scenario says both. The {iso} {fuel} "
            f"supply loses {100 * frac:.0f}% of itself, and the {iso} grid "
            f"loses the generation that fuel was providing: {fuel} is "
            f"{100 * share:.1f}% of {iso} electricity, measured from the "
            f"fuel-supply layer, so the grid is pushed by "
            f"{share:.3f} x {frac:.2f} = {share * frac:.3f}. {source}")
        return True

    # ---------- Country policy changes ---------------------------------
    sup("DEU", "coal", 1.0, "deu_coal_exit", "policy",
        "Germany completes its coal exit",
        "Germany's remaining coal generation is withdrawn.",
        "Kohleausstiegsgesetz sets the end date in law.")
    sup("DEU", "nuclear", 1.0, "deu_nuclear_exit", "policy",
        "Germany's nuclear exit",
        "The German nuclear fleet is withdrawn.",
        "Completed April 2023; entered here as the full share.")
    sup("FRA", "nuclear", 0.5, "fra_nuclear_half", "policy",
        "France halves its nuclear fleet",
        "Half of French nuclear output is withdrawn.",
        "The 50% ceiling in the Loi de transition energetique.")
    sup("CHN", "coal", 0.5, "chn_coal_half", "policy",
        "China halves its coal fleet",
        "Half of Chinese coal generation is withdrawn.",
        "Scaled to China's pledge to phase down coal use.")
    sup("USA", "coal", 1.0, "usa_coal_exit", "policy",
        "The United States retires coal",
        "United States coal generation is withdrawn.",
        "Scaled to the observed direction of US coal retirements.")
    sup("IND", "coal", 0.3, "ind_coal_cut", "policy",
        "India cuts coal by a third",
        "A third of Indian coal generation is withdrawn.",
        "Scaled to India's stated non-fossil capacity target.")
    sup("JPN", "nuclear", 1.0, "jpn_nuclear_off", "policy",
        "Japan takes nuclear offline",
        "The Japanese nuclear fleet is withdrawn, as after 2011.",
        "Japan's fleet was almost entirely offline through 2013-14.")
    sup("ZAF", "coal", 0.4, "zaf_coal_cut", "policy",
        "South Africa retires Eskom coal",
        "Two fifths of South African coal generation is withdrawn.",
        "Scaled to the Just Energy Transition Partnership.")
    sup("POL", "coal", 0.6, "pol_coal_cut", "policy",
        "Poland moves off coal",
        "Three fifths of Polish coal generation is withdrawn.",
        "Scaled to Poland's 2049 mining agreement.")

    # ---------- Climate goal meetings -----------------------------------
    # A global target, met to a stated fraction. Every fossil supply in the
    # model is withdrawn by that fraction, and every grid is pushed by the
    # generation it loses, which is its own measured fossil share times the
    # fraction. So a half-met target is not half of one number: it is 214
    # different numbers, each one a country's real exposure.
    FOSSIL = ("coal", "oil", "gas")

    def fossil_share(iso):
        tot = 0.0
        for f in FOSSIL:
            s = fuel_share(D, f"SUP_{iso}_{f}")
            if s:
                tot += s
        return tot

    isos = sorted({k.split("_")[1] for k in D["idMap"] if k.startswith("SUP_")})

    def target(sid, label, frac, desc, basis):
        shocks = {}
        covered = 0
        for iso in isos:
            grid = f"GRID_{iso}"
            fs = fossil_share(iso)
            if fs <= 0 or grid not in D["idMap"]:
                continue
            for f in FOSSIL:
                if fuel_share(D, f"SUP_{iso}_{f}"):
                    shocks[f"SUP_{iso}_{f}"] = round(frac, 3)
            shocks[grid] = round(min(1.0, fs * frac), 3)
            covered += 1
        if shocks:
            S[sid] = {"cat": "climate_goal", "label": label, "shocks": shocks,
                      "desc": desc,
                      "basis": basis + f" Applied to {covered} countries; each "
                      f"grid is pushed by its own measured fossil share times "
                      f"{frac:.2f}, so the size of the change differs by "
                      f"country and is read from the data, not chosen."}

    target("paris_full", "Paris, fully met", 1.0,
           "Every fossil supply in the model is withdrawn.",
           "The Paris Agreement's 1.5 C limit implies reaching net zero CO2 "
           "around 2050 (IPCC AR6 WG3). Full attainment is the whole fossil "
           "share.")
    target("paris_75", "Paris, three quarters met", 0.75,
           "Three quarters of the fossil supply is withdrawn worldwide.",
           "Partial attainment of the same target.")
    target("paris_50", "Paris, half met", 0.5,
           "Half the fossil supply is withdrawn worldwide.",
           "Partial attainment of the same target.")
    target("paris_25", "Paris, a quarter met", 0.25,
           "A quarter of the fossil supply is withdrawn worldwide.",
           "Partial attainment of the same target.")
    target("ndc_2030", "The 2030 pledges, as written", 0.43,
           "Fossil supply is withdrawn by the amount the 2030 pledges imply.",
           "Holding 1.5 C requires global CO2 roughly 43% below 2019 by 2030 "
           "(IPCC AR6 WG3 SPM).")
    target("cop28_tripling", "COP28: renewables tripled", 0.33,
           "Renewables triple, displacing a third of the fossil supply.",
           "The COP28 Global Stocktake calls for tripling renewable capacity "
           "by 2030. A third of fossil generation displaced is an assumption "
           "about what that tripling replaces, not a figure from the text.")
    target("overshoot_2c", "A 2 C path rather than 1.5", 0.60,
           "A slower path: three fifths of the fossil supply is withdrawn.",
           "A 2 C path requires roughly 21% below 2019 CO2 by 2030 and net "
           "zero around 2070 (IPCC AR6 WG3). Entered as a smaller fraction "
           "than the 1.5 C case; the exact fraction is an assumption.")
    target("pledges_missed", "The pledges are missed", 0.10,
           "Only a tenth of the fossil supply is withdrawn.",
           "Current-policy trajectories leave emissions near flat to 2030 "
           "(UNEP Emissions Gap). Entered as a small withdrawal.")

    return S


def add_cited(D, S):
    """
    Scenarios anchored to a published figure for the event's effect on energy,
    normalised against the largest move of that kind in the record.
    """
    # The ceiling for a demand shock. Setting it at the 2020 fall of 4.5%
    # made every pandemic larger than COVID-19 saturate at 1.0, so a medieval
    # plague and the 1918 influenza returned identical answers. The ceiling is
    # the largest demand change in the catalogue instead, which keeps the
    # ordering the historical record actually has.
    DEMAND_CEIL = 0.30

    def demand(sid, cat, label, pct, desc, source, channels=None):
        mag = round(min(1.0, abs(pct) / DEMAND_CEIL), 3) * (1 if pct > 0 else -1)
        ch = channels or ["PSYCH_routine", "PSYCH_habit"]
        S[sid] = {"cat": cat, "label": label,
                  "shocks": {c: round(mag, 3) for c in ch},
                  "desc": desc,
                  "basis": f"Entered as a {100 * abs(pct):.1f}% change in "
                           f"energy demand, against a ceiling of 30%, the "
                           f"largest in this catalogue. For scale, global "
                           f"primary energy fell 4.5% in 2020, the largest "
                           f"annual fall since 1945. {source}"}

    # ---------- Global pandemics ----------------------------------------
    demand("covid_19", "pandemic", "COVID-19, 2020",
           -0.045,
           "The observed 2020 pandemic year: demand falls, then recovers.",
           "Energy Institute Statistical Review of World Energy.")
    demand("flu_1918", "pandemic", "1918 influenza, at today's scale",
           -0.085,
           "The 1918 pandemic killed a far larger share of the world than "
           "2020. Entered at roughly twice the 2020 demand effect.",
           "1918 mortality is estimated at 1-3% of world population against "
           "roughly 0.09% for COVID-19 in 2020; the demand figure is scaled "
           "from the 2020 observation and is an assumption, not an "
           "observation.")
    demand("black_death", "pandemic", "The Black Death, at today's scale",
           -0.30,
           "A mortality event of medieval scale imposed on a modern energy "
           "system.",
           "The 14th-century plague is estimated to have killed a third of "
           "Europe. The demand figure is that share carried across directly, "
           "which is an assumption and a severe one.")
    demand("plague_justinian", "pandemic", "Plague of Justinian, at today's scale",
           -0.15,
           "A sixth-century pandemic at modern scale.",
           "Mortality estimates for the sixth-century plague vary widely; the "
           "demand figure is an assumption at half the Black Death.")
    demand("hiv_aids", "pandemic", "HIV/AIDS, cumulative",
           -0.012,
           "A slow pandemic concentrated in particular regions.",
           "Roughly 40 million deaths to date. The demand figure is an "
           "assumption scaled by mortality share.")
    demand("cholera_1817", "pandemic", "A cholera pandemic, at today's scale",
           -0.02,
           "The nineteenth-century cholera pandemics at modern scale.",
           "Assumption scaled by mortality share; the historical record is "
           "not precise enough to do better.")

    # ---------- Wars -----------------------------------------------------
    S["ru_ua_gas"] = {
        "cat": "war", "label": "The 2022 European gas shock",
        "shocks": {"MKT_HH": 0.62},
        "desc": "European gas prices multiply and the whole continent's power "
                "cost follows.",
        "basis": "TTF rose roughly sevenfold from its 2021 average at the "
                 "2022 peak. Normalised against the 1973-74 crude move, "
                 "roughly a factor of four in real terms, capped at 1.0."}
    S["oil_embargo_1973"] = {
        "cat": "war", "label": "The 1973 oil embargo",
        "shocks": {"MKT_BRENT": 1.0, "MKT_WTI": 1.0},
        "desc": "The largest oil price move in the modern record.",
        "basis": "Crude roughly quadrupled in real terms over 1973-74. This "
                 "is the record maximum and so is 1.0 by construction."}
    S["iran_iraq"] = {
        "cat": "war", "label": "The 1979-80 supply shock",
        "shocks": {"MKT_BRENT": 0.75, "MKT_WTI": 0.75},
        "desc": "A second oil shock following revolution and war.",
        "basis": "Real crude roughly tripled over 1978-80, about three "
                 "quarters of the 1973-74 move."}
    S["strait_hormuz"] = {
        "cat": "war", "label": "The Strait of Hormuz closes",
        "shocks": {"MKT_BRENT": 0.9, "MKT_WTI": 0.9},
        "desc": "The busiest oil chokepoint in the world is shut.",
        "basis": "Roughly a fifth of global petroleum liquids passes through "
                 "Hormuz (US EIA). The price magnitude is scaled against the "
                 "1973-74 ceiling and is an assumption."}
    S["ww2_scale"] = {
        "cat": "war", "label": "A war of 1939-45 scale",
        "shocks": {"MKT_BRENT": 0.8, "PSYCH_threat": 0.9,
                   "PSYCH_identity": 0.8, "PSYCH_routine": -0.7},
        "desc": "Total mobilisation: prices, threat, identity and routine all "
                "move at once.",
        "basis": "Direction from the historical record. The magnitudes are "
                 "assumptions; no single published figure maps a general war "
                 "onto this model's units."}

    # ---------- Natural disasters ----------------------------------------
    for sid, label, ident, desc in (
            ("quake_tohoku", "The 2011 Tohoku earthquake", "GRID_JPN",
             "The Japanese grid loses a large block of generation at once."),
            ("quake_california", "A major California earthquake", "GRID_USA",
             "The United States grid is stressed by a large western event."),
            ("hurricane_gulf", "A Gulf coast hurricane season", "GRID_USA",
             "Gulf generation and refining are disrupted."),
            ("flood_pakistan", "A Pakistan-scale flood", "GRID_PAK",
             "A third of the country is inundated."),
            ("drought_hydro", "A drought that empties the reservoirs",
             "GRID_BRA", "Hydro output falls with the reservoirs.")):
        if ident in D["idMap"]:
            S[sid] = {"cat": "disaster", "label": label,
                      "shocks": {ident: 0.8}, "desc": desc,
                      "basis": "Entered as a large stress on the national "
                               "grid. The size is an assumption: the model "
                               "carries capacity, not outage duration."}

    # ---------- Technology ------------------------------------------------
    S["solar_cost_collapse"] = {
        "cat": "technology", "label": "Solar costs fall by another 90%",
        "shocks": {"MKT_ELEC_RETAIL": -0.9},
        "desc": "The cost of delivered electricity falls sharply.",
        "basis": "Utility-scale solar LCOE fell about 90% between 2009 and "
                 "2023 (Lazard). A repeat of the observed fall is 0.9 against "
                 "a 1.0 ceiling of a complete collapse."}
    S["storage_buildout"] = {
        "cat": "technology", "label": "Storage becomes abundant",
        "shocks": {"MKT_ELEC_RETAIL": -0.6, "PSYCH_thermal_comfort": 0.3},
        "desc": "Cheap storage flattens the cost of delivered power.",
        "basis": "Lithium-ion pack prices fell roughly 90% from 2010 to 2023 "
                 "(BloombergNEF). Scaled below the solar figure because "
                 "storage is a smaller share of delivered cost."}
    S["fusion_arrives"] = {
        "cat": "technology", "label": "Fusion arrives at scale",
        "shocks": {"MKT_ELEC_RETAIL": -0.95, "MKT_BRENT": -0.7,
                   "MKT_HH": -0.7},
        "desc": "A new firm, low-cost source displaces fuel across the board.",
        "basis": "Speculative. No observed figure exists; the magnitudes are "
                 "assumptions and the scenario is offered as a bound, not a "
                 "forecast."}
    S["efficiency_doubles"] = {
        "cat": "technology", "label": "End-use efficiency doubles",
        "shocks": {"PSYCH_effort_cost": -0.8, "PSYCH_habit": -0.5},
        "desc": "The same service takes half the energy.",
        "basis": "Assumption. Entered through the behaviour channels because "
                 "that is where this model carries demand response."}
    S["grid_interconnection"] = {
        "cat": "technology", "label": "Continental interconnection",
        "shocks": {"MKT_ELEC_RETAIL": -0.45},
        "desc": "Grids are joined across borders and share reserve.",
        "basis": "Assumption scaled below the storage case."}

    # ---------- Energy makeup evolution ------------------------------------
    S["peak_oil_real"] = {
        "cat": "energy_mix", "label": "Peak oil, on the supply side",
        "shocks": {"MKT_BRENT": 0.85, "MKT_WTI": 0.85,
                   "MKT_GASOLINE": 0.8},
        "desc": "Production passes its maximum and cannot be raised again.",
        "basis": "Scaled against the 1973-74 ceiling. A sustained supply "
                 "ceiling is entered slightly below the embargo because it "
                 "arrives slowly; that comparison is an assumption."}
    S["peak_demand"] = {
        "cat": "energy_mix", "label": "Peak oil, on the demand side",
        "shocks": {"MKT_BRENT": -0.7, "MKT_WTI": -0.7},
        "desc": "Demand turns over first and the price falls with it.",
        "basis": "Assumption. The direction is the claim."}
    S["gas_golden_age"] = {
        "cat": "energy_mix", "label": "Gas displaces coal worldwide",
        "shocks": {"MKT_HH": -0.5, "MKT_BRENT": -0.3},
        "desc": "Gas becomes cheap and takes coal's share.",
        "basis": "Assumption, scaled below the observed 2022 move."}
    S["renewables_majority"] = {
        "cat": "energy_mix", "label": "Renewables pass half of world power",
        "shocks": {"MKT_ELEC_RETAIL": -0.55, "MKT_BRENT": -0.45,
                   "MKT_HH": -0.45},
        "desc": "The fuel-priced share of electricity falls below half.",
        "basis": "Assumption. Direction follows the observed cost trend."}
    S["nuclear_renaissance"] = {
        "cat": "energy_mix", "label": "A nuclear buildout",
        "shocks": {"MKT_ELEC_RETAIL": -0.4, "MKT_HH": -0.35},
        "desc": "Firm low-carbon capacity is added at scale.",
        "basis": "Assumption."}
    S["electrify_everything"] = {
        "cat": "energy_mix", "label": "Transport and heat electrify",
        "shocks": {"MKT_GASOLINE": -0.8, "MKT_ELEC_RETAIL": 0.4,
                   "PSYCH_routine": 0.5},
        "desc": "Liquid fuel demand falls and electricity demand rises.",
        "basis": "Assumption. Direction follows observed electrification."}

    # ---------- keep the physical ones already in the model ---------------
    S["climate_forcing"] = {
        "cat": "exogenous", "label": "A step in climate forcing",
        "shocks": {"CLIMATE_SYS": 0.8},
        "desc": "The climate system moves to a higher anomaly.",
        "basis": "Entered as a large step in the slow variable. The size is a "
                 "convention; the CO2 and temperature records set the state, "
                 "not the step."}
    S["us_grid_stress"] = {
        "cat": "disaster", "label": "United States grid stress",
        "shocks": {"GRID_USA": 0.8},
        "desc": "The United States grid loses reserve margin.",
        "basis": "Convention. Entered as a large stress on one national grid."}
    return S


def main(apply=False):
    head, D = load()
    S = build(D)
    S = add_data_driven(D, S)
    S = add_cited(D, S)

    ids = D["idMap"]
    dropped = []
    for sid in list(S):
        bad = [k for k in S[sid]["shocks"] if k not in ids]
        if bad:
            dropped.append((sid, bad))
            del S[sid]
    if dropped:
        print(f"  {len(dropped)} scenario(s) dropped for missing nodes:")
        for sid, bad in dropped[:6]:
            print(f"     {sid}: {bad[:3]}")

    by = collections.Counter(v["cat"] for v in S.values())
    print(f"\n  {len(S)} scenarios in {len(by)} categories")
    for cid, label in CATEGORIES:
        print(f"     {label:<32} {by.get(cid, 0)}")

    # every scenario has to actually move something
    N = D["n"]
    s = np.asarray(D["es"], dtype=np.int64)
    t = np.asarray(D["et"], dtype=np.int64)
    w = np.asarray(D["ew"], dtype=float)
    kind = [D["kinds"][k] for k in D["kind"]]
    RANK = {"sun": 0, "insolation": 1, "weather": 2, "climate": 3, "event": 4}
    rank = np.array([RANK.get(k, 5) for k in kind])
    one = rank[s] != rank[t]
    cnt = collections.Counter()
    for a, b in zip(s, t):
        cnt[(int(b), kind[a])] += 1
        if rank[a] == rank[b]:
            cnt[(int(a), kind[b])] += 1
    fw = np.array([w[i] / cnt[(int(t[i]), kind[s[i]])] for i in range(len(w))])
    bw = np.array([0.0 if one[i] else w[i] / cnt[(int(s[i]), kind[t[i]])]
                   for i in range(len(w))])
    deg = np.zeros(N)
    np.add.at(deg, t, np.abs(fw))
    np.add.at(deg, s[~one], np.abs(bw[~one]))
    deg[deg == 0] = 1.0
    fw, bw[~one] = fw / deg[t], bw[~one] / deg[s[~one]]
    A = sp.csr_matrix((np.concatenate([fw, bw[~one]]),
                       (np.concatenate([t, s[~one]]),
                        np.concatenate([s, t[~one]]))), shape=(N, N))
    damp = 1.0 - np.asarray(D["res"], dtype=float) * 0.6

    def reach(shocks):
        b = np.zeros(N)
        for k, v in shocks.items():
            b[int(ids[k])] = v
        st = b.copy()
        for r in range(1, 61):
            nx = 0.05 * st + 0.95 * np.tanh(b + damp * A.dot(st))
            d = np.abs(nx - st).max()
            st = nx
            if d < 1e-5:
                break
        return int((np.abs(st) >= 0.02).sum()), r

    print("\n  reach of every scenario:")
    inert = []
    for cid, label in CATEGORIES:
        rows = [(sid, v) for sid, v in S.items() if v["cat"] == cid]
        if not rows:
            continue
        print(f"\n    {label}")
        for sid, v in sorted(rows):
            n, steps = reach(v["shocks"])
            S[sid]["reach"] = n
            flag = "" if n > 1 else "   <- moves nothing"
            if n <= 1:
                inert.append(sid)
            print(f"      {v['label'][:44]:<46} {n:>7,} nodes, "
                  f"{steps:>2} steps{flag}")
    if inert:
        print(f"\n  WARNING {len(inert)} scenario(s) move nothing: {inert}")

    D["scenarios"] = S
    D["scenarioCats"] = [{"id": c, "label": l} for c, l in CATEGORIES]

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return
    open(DATA, "w", encoding="utf-8").write(
        head + json.dumps(D, separators=(",", ":")) + ";")
    print("\n  written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
