"""
The published figures this page stands on, one primary source per row.

There is no machine-readable dataset of evolutionary steps or of independent origins: each number below is
copied from the paper named beside it, as read in its abstract or full text (the lane's research notes list the
URL opened for each). The build reads these tables; it never types a number of its own. Values that are a
judgement of this page, not of a source, say so in their "note".

Units: Ga = billions of years ago, Ma = millions of years ago, Gyr = billions of years (a duration).
"""

# ------------------------------------------------------------------ the chain ---
# The habitable window: when Earth's surface could first hold life, and when it will stop holding complex life.
WINDOW = {
    "earth_ga": 4.54,      # Dalrymple 2001; USGS "Age of the Earth"
    "start_ga": 4.4,       # Wilde et al. 2001: zircon 4.404 Ga shows liquid water
    "start_band": (4.5, 4.2),
    "end_gyr": 1.0,        # Ozaki & Reinhard 2021: oxygen-rich air lasts ~1.08 +/- 0.14 Gyr more
    "end_band": (0.8, 1.5),
    "refs": ["dalrymple2001", "wilde2001", "ozaki2021"],
}

# The steps of the chain. best: the date the timeline draws (Ga). band: the range the page shows (Ga).
# count: independent origins of the step (see ORIGINS). The wait of a step is measured from the previous
# step's best date (the window's start for the first).
STEPS = [
    {"key": "life", "name": "Life", "short": "Life",
     "best": 3.48, "band": (3.48, 3.43), "early": 4.2, "early_band": (4.33, 4.09),
     "what": "oldest widely accepted fossils (Dresser Formation); a molecular clock puts the last common "
             "ancestor of all life near 4.2 Ga",
     "count": "unknown", "count_word": "one surviving lineage",
     "refs": ["djokic2017", "moody2024"]},
    {"key": "photo", "name": "Oxygen-making photosynthesis", "short": "O2 photo",
     "best": 2.95, "band": (2.95, 2.5),
     "what": "oxygen being made by 2.95 Ga on manganese and molybdenum evidence; another reading puts the origin "
             "near 2.5-2.6 Ga, just before oxygen built up in the air from 2.43 Ga",
     "count": 1, "count_word": "once",
     "refs": ["planavsky2014", "shih2017", "poulton2021"]},
    {"key": "cell", "name": "Complex (eukaryotic) cell", "short": "Cell",
     "best": 1.635, "band": (1.65, 1.62),
     "what": "oldest accepted eukaryote fossils; molecular clocks put the common ancestor of all eukaryotes "
             "between 1.84 and 1.21 Ga",
     "count": 1, "count_word": "once",
     "refs": ["miao2024", "betts2018"]},
    {"key": "multi", "name": "Complex multicellular life", "short": "Animals",
     "best": 0.574, "band": (0.5748, 0.5735),
     "what": "large Ediacaran fossils at Mistaken Point, 574 Ma; the Cambrian begins 538.8 Ma",
     "count": 6, "count_word": "6 times",
     "refs": ["matthews2021", "knoll2011"]},
    {"key": "tech", "name": "Technology", "short": "Tech",
     "best": 0.0033, "band": (0.0033, 0.0),
     "what": "stone tools 3.3 Ma; Homo sapiens 315 ka; radio from 1895",
     "count": 1, "count_word": "once",
     "refs": ["harmand2015", "hublin2017", "marconi"]},
]
# Dates the hero's cards name beyond the steps' own (Ma unless stated).
EXTRA = {"leca_lo_ga": 1.21, "leca_hi_ga": 1.842, "goe_ga": 2.43, "cambrian_ma": 538.8, "sapiens_ka": 315,
         "radio_year": 1895, "contested_life_ga": 4.1}

# ------------------------------------------------------------ independent origins ---
# (trait, count drawn, label, on the chain?, source key, note). count drawn = the lower bound where the source
# gives "at least".
ORIGINS = [
    ("CAM photosynthesis", 66, "66+", False, "gilman2023", "a minimum from known plant lineages"),
    ("C4 photosynthesis", 62, "62", False, "sage2011", ""),
    ("Eyes", 40, "40-65", False, "lamb2009", "organs independent; the light-sensing genes shared"),
    ("Simple multicellularity", 25, "25+", False, "grosberg2007", "count depends on the definition"),
    ("Farming, by humans", 11, "11+", False, "larson2014", "centres of plant and animal domestication"),
    ("Farming, by insects", 9, "9", False, "mueller2005", "ants once, termites once, beetles seven times"),
    ("Complex multicellularity", 6, "6", True, "knoll2011", "animals, land plants, red and brown algae, two fungi"),
    ("Complex cognition", 5, "5+", False, "emery2004", "this page's tally of lineages; no formal count exists"),
    ("Powered flight", 4, "4", False, "dudley2007", "insects, pterosaurs, birds, bats"),
    ("Writing", 4, "4", False, "woods2010", "Egypt's independence is debated"),
    ("Chloroplasts", 2, "2", False, "ponce2017", "primary endosymbiosis of a cyanobacterium"),
    ("Oxygen-making photosynthesis", 1, "1", True, "fischer2016", ""),
    ("Complex (eukaryotic) cell", 1, "1", True, "roger2017", ""),
    ("Cumulative technology", 1, "1", True, "tennie2009", "culture that builds on itself"),
]

# ------------------------------------------------------------- the hard-steps model ---
# A demonstration, not a fit: five steps with very different expected waits (Gyr) if each ran on its own, in
# Earth's window. w2-03 gives the expected output (0.093, 1.01, 1.09, 1.10, 1.10 at T = 5.5) and two
# known-answer cases; test_greatfilter.py checks them.
HARD = {"means_gyr": [0.1, 10.0, 100.0, 1000.0, 10000.0], "seed": 20261113, "n_target": 200_000}
WATSON = {"T": 5.0, "left": 1.0, "n": 4}    # Watson 2008: a 5 Ga window with 1 Ga left suggests n = 4

# ------------------------------------------------------ Sandberg, Drexler & Ord 2018 ---
# Table 1: log-uniform ranges, and a log-normal for the rate of abiogenesis (sd 50 orders of magnitude).
SDO = {"R*": (1, 100), "fp": (0.1, 1), "ne": (0.1, 1), "fi": (0.001, 1), "fc": (0.01, 1), "L": (100, 1e10),
       "lnR_sd_dex": 50, "paper_p_alone": 0.52, "post_lo": 0.53, "post_hi": 0.996, "univ_lo": 0.39,
       "univ_hi": 0.85, "seed": 1, "n": 2_000_000}

# --------------------------------------------------------------- the searched sky ---
SKY = {
    "ghat_galaxies": 100_000, "ghat_max_frac": 0.85,            # Griffith et al. 2015
    "bl_stars": 1327, "bl_eirp_w": 2.1e12, "bl_frac": 0.0045,   # Price et al. 2020
    "haystack": 6.0e-18, "haystack_litres": 8000,               # Wright, Kanodia & Lubar 2018
    "k1_w": 4e12,                                               # Kardashev 1964, Type I (4e19 erg/s)
    "human_ej": 600.31, "human_year": 2025,                     # Energy Institute Statistical Review 2026
    "cross_myr": 300,                                           # Carroll-Nellenback et al. 2019, upper limit
}

# ---------------------------------------------------------- estimates of what lies ahead ---
# (what, value as printed, kind, who, year, source key)
AHEAD = [
    ("Existential catastrophe this century", "about 1 in 6", "one person's estimate", "Toby Ord", 2020, "ord2020"),
    ("of which from unaligned AI", "about 1 in 10", "one person's estimate", "Toby Ord", 2020, "ord2020"),
    ("Human extinction by 2100", "1%", "median of superforecasters", "XPT tournament", 2023, "karger2023"),
    ("Human extinction by 2100", "6%", "median of domain experts", "XPT tournament", 2023, "karger2023"),
    ("Extremely bad outcome from advanced AI", "5%", "median of 2,778 AI researchers", "Grace et al.", 2024,
     "grace2024"),
    ("Extinction from natural causes, per year", "below 1 in 14,000", "bound from the human fossil record",
     "Snyder-Beattie, Ord & Bonsall", 2019, "sb2019"),
]
AHEAD_NUM = {"ord_total": 1 / 6, "xpt_sf": 0.01, "xpt_ex": 0.06, "grace": 0.05, "sb_year": 1 / 14000}

# ------------------------------------------------------------------ the counter-case ---
COUNTER = {
    "mills_frac": 0.52,       # Mills et al. 2025: oxygen excluded eukaryotes and animals for ~52% of Earth history
    "worth_mars": 0.026,      # Worth, Sigurdsson & House 2013: share of simulated Mars ejecta that reach Earth
    "lane_archezoa": 20,      # Lane 2014: at least 20 independent origins of archezoa
    "mayr_year": 1995,        # Mayr 1995: eyes many times, high intelligence once
}
