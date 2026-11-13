"""Published figures the algae page uses, each with its source.

These are not measured here. They are read from the papers named beside them (page, table or
section given) and typed in. Low / central / high are the spread of published estimates, not
confidence intervals. Values marked ASSUMED are this page's choices inside a published range.

Units: t C means tonnes of carbon. Per-100 figures are tonnes of carbon per 100 t fixed.
Prices are US dollars per tonne of CO2 (not carbon); no source states a dollar year.
"""

# ------------------------------------------------------------ natural ocean flows (Pg C per year)
NPP_OCEAN = 48.5        # Field et al. 1998, Science 281:237, Table 1 (includes 1.0 for macroalgae)
NPP_MACRO = 1.0         # same table
NPP_LAND = 56.4         # same table (land total; ocean + land = 104.9)
NPP_SAT = (38.8, 42.1)  # Kulk et al. 2020, Remote Sens. 12:826, 1998-2018 satellite models
EXPORT_100M = (4, 10)   # Siegel et al. 2023, Annu. Rev. Mar. Sci. 15:329, Table 1, range of estimates
FLUX_1000M = 0.65       # Doney et al. 2024, Global Biogeochem. Cycles 38, RECCAP2 synthesis (published value)
BURIAL = (0.02, 0.2)    # Siegel 2023 Table 1; IPCC AR6 WG1 Fig. 5.12 uses 0.2

# ------------------------------------------------------------ funnels, t C per 100 t fixed
# deep = sinks below 1,000 m or is buried. held = NET carbon taken from the air and still out of
# contact with it after 100 years. None = no published estimate.
FUNNEL = [
    dict(key="plankton", label="Natural plankton",
         deep=(1.2, 2.0, 2.7), held=(0, 0, 0), gross=(1.8, 3.75, 5.4),
         note="Natural cycle, in balance before industry: the gross flow out is matched by a return flow.",
         src="Doney 2024 Table 5 (flux at 1,000 m over NPP); Ricour 2023 and Siegel 2021 (25 t of each 100 t "
             "exported still out at 100 years, x 15 t exported); IPCC AR6 WG1 Cross-Chapter Box 5.3"),
    dict(key="kelp", label="Natural seaweed",
         deep=(None, None, None), held=(0, 0, 0), gross=(1.3, 6.0, 13.9),
         note="Natural cycle; no global estimate of the share that reaches 1,000 m.",
         src="Filbee-Dexter et al. 2024, Nature Geoscience: 4 to 44 Tg C a year of 317 Tg C brown-forest NPP"),
    dict(key="iron", label="Iron fertilization",
         deep=(0, 1, 50), held=(0, 2, 30), gross=None,
         note="Low: LOHAFEX and SOIREE, no extra export. High: EIFEX-like deep export with the model's best region.",
         src="de Baar et al. 2005 and 2008; Smetacek et al. 2012; Oschlies et al. 2010 Tables 1-2 "
             "(0.22 of extra export becomes air uptake at 100 years; N2O offset 3-9 percent)"),
    dict(key="seaweed", label="Farmed seaweed, sunk",
         from_air=(0.40, 0.55, 0.79), reach=(0.80, 0.90, 0.98), ret_depth=(1000, 2100, None), ret_high=0.95,
         deep=(80, 90, 98), held=None, gross=None,
         note="Product of three fractions: drawn from the air, reaching 1,000 m, retained there 100 years.",
         src="DeAngelo et al. 2023, Nature Plants 9:45, Table 1; Berger et al. 2023, Environ. Res. Lett.; "
             "Bach et al. 2021, Nature Communications; retention from Siegel et al. 2021 (high case ASSUMED 0.95 "
             "below 3,000 m)"),
    dict(key="pondfuel", label="Pond algae to fuel",
         deep=(0, 0, 0), held=(-67, -36, -5), gross=None,
         note="The carbon returns to the air when fuel burns or feed is eaten; the energy used is a net emission.",
         src="Davis et al. 2016, NREL/TP-5100-64772, Table 21 (0.36 t CO2 emitted per t fixed); "
             "IPCC AR6 WG3 Cross-Chapter Box 8; Hepburn et al. 2019, Nature 575:87"),
    dict(key="pondburied", label="Pond algae, buried",
         harvest=(0.85, 0.92, 0.96), from_air=(0.50, 0.75, 1.00), tomb=(0.80, 0.95, 0.99), energy=(26, 28, 13),
         deep=(85, 92, 96), held=None, gross=None,
         note="Harvested x drawn from the air x kept in the burial pit, less the energy and materials used.",
         src="Leonard et al. 2026, Environ. Sci. Technol. (energy and embodied emissions); Davis et al. 2016 "
             "(harvest losses); tomb retention ASSUMED"),
]

# ------------------------------------------------------------ costs, $ per t CO2 (all model estimates)
COSTS = {
    "iron": dict(lo=50, hi=1000, text="under $50 (NASEM 2022) to over $1,000 offshore (Bach et al. 2023)"),
    "seaweed": dict(lo=480, hi=2090, best=480, nutrient=830, typ_lo=1120,
                    text="$480 in the best case; typical model runs $1,120 to $2,090 (DeAngelo et al. 2023)"),
    "seaweed_nasem": 100,      # NASEM 2022 Table S.1, p. 10, excludes monitoring
    "pondburied": dict(lo=181, hi=661, text="$181 optimistic to $661 realistic (Leonard et al. 2026)"),
    "dac_paid": 646,           # Frontier, average price of its direct-air-capture purchases
    "cdrfyi_2024": 320,        # CDR.fyi, average price of publicly priced orders, 2024
}

# ------------------------------------------------------------ the record
RECORD = {
    "iron_experiments": 13, "iron_first": 1993, "iron_last": 2009,     # Yoon et al. 2018; Boyd et al. 2007
    "eifex_year": 2004, "eifex_deep_share": 0.5,                         # Smetacek et al. 2012, Nature 487:313
    "lohafex_year": 2009, "lohafex_iron_t": 4,                           # Martin et al. 2013
    "haida_year": 2012, "haida_t": 100,                                  # about 100 t iron sulphate
    "running_tide_t": 19000, "running_tide_year": 2023, "running_tide_shut": "June 2024",
    "brilliant_planet_admin": "November 2024",                           # Companies House 08491368
    "removal_fraction_deangelo": 0.5,                                    # DeAngelo 2023 Table 1, value used
    "co2_per_dry_t": 1.83,       # t CO2 per t dry algae at 50 percent carbon (44/12 x 0.5)
    "nrel_energy": 0.36,         # Davis et al. 2016 Table 21: t CO2 emitted per t CO2 fixed, incl. flue-gas capture
    "oschlies_ratio": 0.22,      # Oschlies et al. 2010 Table 1: air uptake / extra export, 1-yr pulse, at 100 yr
}
