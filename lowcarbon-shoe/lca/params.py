"""Every number the LCA uses: (central, low, high, unit, basis, source).

basis: published = read from the cited document; derived = arithmetic on
published numbers (shown in the source note); assumed = a modelling choice with
no direct source, stated as such and swept in the Monte Carlo and the tornado.
Per-shoe masses are men's US 9. Factors are cradle-to-gate GWP100, kg CO2e/kg,
fossil GHG only (no biogenic uptake credit). ecoinvent is not used anywhere.
Full research trail: research/w2-01, w2-02, w2-03, w2-09 and research/data/*.csv.
"""

R = "research/data/"
PE = "PlasticsEurope / ISOPA eco-profiles"

# ---------------------------------------------------------------- factors
F = {
    # id: (central, low, high, unit, basis, source)
    "EVA": (2.30, 2.16, 3.42, "kg CO2e/kg", "derived",
            "LDPE 2.16 (PlasticsEurope PE eco-profile 2026) + vinyl-acetate share; high end ADEME Base Carbone generic plastic. factors_polymers.csv"),
    "TPU": (3.21, 3.00, 4.09, "kg CO2e/kg", "derived",
            "Stoichiometric build-up: MDI 2.76 (ISOPA 2021), polyether polyol 2.93 (ISOPA 2021), 1,4-butanediol assumed. No producer figure is published. factors_polymers.csv"),
    "rTPU": (0.55, 0.48, 0.91, "kg CO2e/kg", "derived",
             "Mechanical regrind + re-extrusion of post-industrial TPU; proxy ADEME Base Carbone PET recycling to granules (ids 34488, 34490). Cut-off: no burden from first life."),
    "SBR": (3.11, 2.32, 5.55, "kg CO2e/kg", "derived",
            "Outsole rubber compound proxy: SBR build-up from butadiene 1.95 and styrene 2.09 (PlasticsEurope); carbon black 3.25 (EPD-IES-0025254) is in the same range. factors_polymers.csv"),
    "PU_FOAM": (3.66, 3.16, 3.79, "kg CO2e/kg", "published",
                "Moulded flexible PU foam 3.66 (Euromoulders eco-profile); slabstock 3.16-3.79 (EUROPUR 2024)"),
    "PET_FIBRE": (2.64, 2.19, 3.10, "kg CO2e/kg", "derived",
                  "PET resin (CPME/PlasticsEurope 2017) + fibre processing (Zheng & Suh 2019 method). factors_polymers.csv"),
    "rPET_FIBRE": (1.32, 0.55, 2.32, "kg CO2e/kg", "derived",
                   "Mechanically recycled PET fibre: 25-75 % below virgin (Shen, Worrell & Patel 2010, Resour. Conserv. Recycl. 55:34-52)"),
    "ADHESIVE": (4.79, 0.88, 8.05, "kg CO2e/kg", "published",
                 "PU reactive adhesive, FEICA model EPD EPD-FEI-20220021-IBG2-EN (construction product used as proxy)"),
    "PAPERBOARD": (0.718, 0.531, 0.718, "kg CO2e/kg", "published",
                   "Corrugated board, fossil GHG (FEFCO carbon footprint 2018)"),
    "LDPE": (2.16, 2.09, 2.16, "kg CO2e/kg", "published", "LDPE (PlasticsEurope PE eco-profile 2026)"),
}

# electricity, heat, freight
E = {
    "GRID": (0.459, 0.459, 0.477, "kg CO2e/kWh", "published",
             "Ember yearly electricity data: Viet Nam 459 g/kWh (2025), 477 (recent-year high). CC-BY 4.0. Lifecycle basis. Other countries are scenarios, not uncertainty."),
    "GRID_CN": (0.528, 0.528, 0.528, "kg CO2e/kWh", "published", "Ember 2025, China 528 g/kWh (scenario)"),
    "GRID_ID": (0.705, 0.705, 0.705, "kg CO2e/kWh", "published", "Ember 2025, Indonesia 705 g/kWh (scenario)"),
    "GRID_US": (0.384, 0.384, 0.384, "kg CO2e/kWh", "published", "Ember 2025, United States 384 g/kWh"),
    "GRID_CLEAN": (0.048, 0.012, 0.048, "kg CO2e/kWh", "published", "Ember lifecycle factors: solar 48, wind 12 g/kWh"),
    "GAS": (0.0562, 0.0544, 0.0584, "kg CO2e/MJ", "published", "IPCC 2006 Vol 2 Table 2.2/2.3 natural gas, stationary combustion"),
    "LIQ_FUEL": (0.0741, 0.0726, 0.0748, "kg CO2e/MJ", "published", "IPCC 2006 Vol 2 Table 2.2, diesel/gasoline/LPG (diesel value used for all three)"),
    "COAL": (0.0953, 0.0902, 0.1004, "kg CO2e/MJ", "published", "IPCC 2006 Vol 2 Table 2.2, other bituminous coal"),
    "SHIP": (0.0198, 0.0161, 0.0198, "kg CO2e/t-km", "published", "DESNZ 2025 conversion factors, container ship average, incl. well-to-tank"),
    "TRUCK": (0.125, 0.102, 0.125, "kg CO2e/t-km", "published", "DESNZ 2025, HGV all diesel average laden"),
}

# incineration: fossil CO2 per kg burned (carbon content x 44/12; IPCC 2006 Vol 5 Ch 5 Eq 5.2)
INCIN = {"EVA": 2.94, "TPU": 2.45, "rTPU": 2.45, "SBR": 3.28, "PU_FOAM": 2.45, "PET_FIBRE": 2.29,
         "rPET_FIBRE": 2.29, "ADHESIVE": 2.45, "LDPE": 3.14, "PAPERBOARD": 0.0}

# ---------------------------------------------------------------- parameters
P = {
    "life_km": (550.0, 400.0, 800.0, "km", "assumed",
                "Retirement distance of the baseline shoe. Industry rule of thumb 300-500 miles (480-800 km) has no primary source (research/w1-06); "
                "Cook et al. 1985 and Aimar et al. 2024 (200k cycles ~ 400-700 km) bracket it."),
    "life_mult_lc1": (1.0, 1.0, 1.0, "x", "assumed",
                      "LC-1 sole life relative to baseline. Held at 1.0: runners retire shoes by rule of thumb and do not feel cushioning loss "
                      "(Cornwall & McPoil 2017). eTPU's slower fatigue (Aimar 2024) is shown only as a scenario (x1.15)."),
    "upper_lives": (1.0, 1.0, 2.0, "sole lives", "assumed",
                    "How many sole units one LC-1 upper serves. 1 = no resole (headline). No published upper-durability data (research/w2-04)."),
    "t1_kwh": (2.88, 1.17, 3.32, "kWh/pair", "derived",
               "Tier 1 (final assembly incl. stockfitting) grid electricity per pair: FIF 2025 Carbon Report athletic 3.32 kWh-eq x electricity share 86.8 %; "
               "low = FIF all-type mean 1.17; high = FIF athletic all carriers 3.32. The MIT 2010 figure (5.0) is not used as a bound: that factory also "
               "pressed its own soles, which this model counts separately at the sole maker. research/data/baseline_energy.csv"),
    "t1_gas_mj": (0.66, 0.27, 1.32, "MJ/pair", "derived", "FIF 2025 Table 2: natural gas + LPG shares x 3.32 kWh-eq"),
    "t1_liq_mj": (0.61, 0.25, 1.22, "MJ/pair", "derived", "FIF 2025 Table 2: diesel + gasoline shares x 3.32 kWh-eq"),
    "noglue_factor": (1.0, 0.6, 1.0, "x", "assumed",
                      "LC-1 assembly energy relative to baseline: no cementing, priming, activation ovens or chillers. No published split of assembly energy by step."),
    "eva_mould_kwh_kg": (2.5, 0.4, 3.08, "kWh/kg", "derived",
                         "EVA midsole moulding: 0.5 kWh/pair for 0.2 kg (baseline_energy.csv); high Bianchi et al. 2023 EVA injection 3.08 kWh/kg; low Thiriez & Gutowski 2006"),
    "vulc_kwh_pair": (0.22, 0.10, 0.60, "kWh/pair", "published", "Rubber outsole mixing + vulcanising, Eklund 2018 thesis, scaled by mass (baseline_energy.csv)"),
    "etpu_bead_kwh_kg": (1.5, 0.5, 3.0, "kWh/kg", "assumed",
                         "eTPU bead foaming at the bead supplier (grid power). NO open data found (research/w2-09)."),
    "etpu_mould_kwh_kg": (2.5, 1.0, 5.0, "kWh-eq/kg", "assumed",
                          "eTPU steam-chest moulding at the sole moulder. NO open data found (research/w2-09). Bead foaming + moulding (4.0) is set above EVA moulding (2.5) so as not to favour LC-1."),
    "etpu_steam_share": (0.5, 0.3, 0.7, "fraction", "assumed",
                         "Share of eTPU moulding energy delivered as steam from a natural-gas boiler (not electricity); steam does not get cleaner on a clean grid."),
    "boiler_eff": (0.90, 0.80, 0.95, "fraction", "assumed", "Natural-gas steam boiler efficiency (fuel to steam)"),
    "tpu_inj_kwh_kg": (0.94, 0.41, 1.09, "kWh/kg", "published", "Injection moulding, Thiriez & Gutowski 2006 (hydraulic 0.94; all-electric 0.41; plant 1.09)"),
    "knit_kwh_kg": (0.26, 0.26, 3.0, "kWh/kg", "published", "Fabric knitting 0.257 kWh/kg (Cotton Inc. LCA 2016); fully-fashioned knitting 3.0 (JRC IMPRO 2014) as high"),
    "spin_kwh_kg": (1.5, 0.75, 3.0, "kWh/kg", "published", "Polyester filament spinning 1.5 kWh/kg at 200 dtex (Ecobalyse default); 0.75-3.0 for 400-100 dtex (research/w2-09). Added to virgin and recycled fibre alike."),
    "ship_km": (13000.0, 11000.0, 16000.0, "km", "assumed", "Ho Chi Minh City to Los Angeles / Long Beach by sea (great-circle routing range)"),
    "truck_km": (1500.0, 500.0, 3000.0, "km", "assumed", "Port to distribution centre to store, US"),
    "incin_share": (0.19, 0.12, 0.30, "fraction", "derived",
                    "US MSW 2018: 11.8 % combusted, 50 % landfilled (EPA Facts and Figures) -> 19 % of disposed mass burned"),
    "landfill_kgco2e_kg": (0.022, 0.0, 0.05, "kg CO2e/kg", "published", "US EPA WARM v16, plastics landfilling (transport and operations; no degradation)"),
    "scrap_upper_cut": (0.32, 0.15, 0.35, "fraction", "published", "Upper cutting loss, Cheah et al. 2012 Fig. 4 (polyester -32 %)"),
    "scrap_pu": (0.50, 0.30, 0.50, "fraction", "published", "PU parts loss 50 %, Cheah et al. 2012 text"),
    "scrap_mould": (0.10, 0.05, 0.20, "fraction", "assumed", "Moulded sole parts flash/trim; PEFCR footwear default processing loss 15 %"),
    "scrap_knit": (0.05, 0.02, 0.10, "fraction", "assumed", "Knit-to-shape upper: little cutting loss"),
    "scrap_etpu": (0.05, 0.02, 0.15, "fraction", "assumed", "Steam-chest moulding: little flash; runners reground"),
    "eva_density": (170.0, 150.0, 250.0, "kg/m3", "published", "Midsole EVA 150-250 kg/m3 (Verdejo 2004 thesis); Aimar 2024 F1 170"),
    "etpu_density": (200.0, 190.0, 240.0, "kg/m3", "derived", "Design density of the eTPU midsole. tests/fea_heel.py (calibrated rate 1.5) puts 200 kg/m3 within 4 % of the EVA baseline's 5 J drop peak; Aimar 2024 tested 240, Meuchelboeck 2024 250; BASF lists current bead grades at 110-140 g/L bulk."),
    "rtpu_share": (0.75, 0.5, 1.0, "fraction", "assumed", "Post-industrial recycled TPU share in the outsole skin, rim and heel counter. Recycled TPU grades on the market are post-industrial (research/w2-06)."),
    "tpu_factor_stress": (6.96, 6.96, 6.96, "kg CO2e/kg", "published",
                          "Stress case only: finished TPU sealing-ring EPD (EPD-IES-0032224, ecoinvent background) - counter-evidence, not used centrally (DECISIONS.md)"),
}

# ---------------------------------------------------------------- inventories (g per SHOE)
# (component, module, factor id, grams, low, high, scrap param, process, fossil_virgin_fraction, basis/source)
BASELINE = [
    # Midsole grams are replaced in lca.rows_for by the SAME CAD volume as LC-1's midsole x EVA density
    # (71 g at 170 kg/m3), so both midsoles have one shape (the FEA compares that shape). The BOM's
    # 100 g (75-135, from Cheah et al. 2012 part shares) is kept here for reference.
    ("Midsole", "sole", "EVA", 100, 75, 135, "scrap_mould", "eva_mould", 1.0, "CAD volume x EVA density (BOM 100 g for reference)"),
    ("Outsole", "sole", "SBR", 45, 30, 60, "scrap_mould", "vulc", 0.8, "derived, Cheah part shares; 20 % natural rubber assumed"),
    ("Shank", "sole", "TPU", 4, 0, 30, "scrap_mould", "inj_t2", 1.0, "assumed"),
    ("Sockliner", "sole", "PU_FOAM", 22, 15, 30, "scrap_mould", None, 1.0, "derived, Cheah part shares"),
    ("Strobel board", "upper", "PET_FIBRE", 10, 6, 15, "scrap_upper_cut", None, 1.0, "assumed"),
    ("Upper mesh", "upper", "PET_FIBRE", 36, 25, 50, "scrap_upper_cut", "knit", 1.0, "assumed"),
    ("Lining", "upper", "PET_FIBRE", 10, 6, 16, "scrap_upper_cut", None, 1.0, "assumed"),
    ("Collar padding", "upper", "PU_FOAM", 8, 4, 14, "scrap_pu", None, 1.0, "assumed"),
    ("Overlays", "upper", "TPU", 8, 3, 15, "scrap_upper_cut", None, 1.0, "assumed"),
    ("Heel counter", "upper", "TPU", 9, 5, 15, "scrap_mould", "inj_t2", 1.0, "assumed"),
    ("Toe puff", "upper", "TPU", 3, 0, 6, "scrap_mould", None, 1.0, "assumed"),
    ("Laces", "upper", "PET_FIBRE", 5, 4, 8, None, None, 1.0, "published (research/w2-03)"),
    ("Thread", "upper", "PET_FIBRE", 2, 1, 3, None, None, 1.0, "published (research/w2-03)"),
    ("Adhesive and primer", "upper", "ADHESIVE", 7, 4, 12, None, None, 1.0, "published dry film (research/w2-03)"),
    ("Labels", "upper", "PET_FIBRE", 2, 1, 4, None, None, 1.0, "assumed"),
]
BASE_PACK = [  # g per PAIR
    ("Shoebox", "PAPERBOARD", 180, "published (PEFCR footwear default 200 g; research/w2-03)"),
    ("Tissue", "PAPERBOARD", 26, "published"),
    ("Polybag and tags", "LDPE", 12, "published"),
    ("Shipping carton share", "PAPERBOARD", 60, "published (PEFCR default)"),
]

# LC-1 masses come from the CAD volumes (cad/out/volumes.json) x density, see lca.py
LC1_UPPER = [
    ("Upper mesh and lining (recycled PET)", "upper", "rPET_FIBRE", 46, 31, 66, "scrap_upper_cut", "knit", 0.0, "as baseline mesh + lining (36 + 10 g)"),
    ("Collar padding (recycled PET spacer)", "upper", "rPET_FIBRE", 8, 4, 14, "scrap_upper_cut", None, 0.0, "as baseline padding mass; PET spacer in place of PU foam"),
    ("Strobel sock (recycled PET)", "upper", "rPET_FIBRE", 10, 6, 15, "scrap_upper_cut", None, 0.0, "as baseline strobel"),
    ("Heel counter (recycled TPU)", "upper", "rTPU_BLEND", 9, 5, 15, "scrap_mould", "inj_t2", None, "as baseline"),
    ("Laces (recycled PET)", "upper", "rPET_FIBRE", 5, 4, 8, None, None, 0.0, "as baseline"),
    ("Stitchdown thread (recycled PET)", "upper", "rPET_FIBRE", 3, 2, 5, None, None, 0.0, "assumed: stitchdown uses more thread"),
    ("Label (recycled PET)", "upper", "rPET_FIBRE", 1, 0.5, 2, None, None, 0.0, "assumed"),
]
LC1_PACK = [
    ("Paper sleeve (no shoebox)", "PAPERBOARD", 60, "assumed design choice"),
    ("Shipping carton share", "PAPERBOARD", 60, "published (PEFCR default)"),
]
SPACER_DENSITY = (150.0, 100.0, 200.0, "kg/m3", "assumed", "rPET 3-D spacer-fabric sockliner")
