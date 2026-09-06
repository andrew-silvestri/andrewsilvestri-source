"""
Every published footwear effect size this project draws, declared once.

This is the project's data. There is no download: no public dataset reports
these numbers, so each row was read out of the paper and is recorded here with
the sample it came from and a DOI. The shape follows
`climate-cost/data/processes.py` - a dict per entry, `note` for the prose
justification, `source` and `doi` for provenance, `quality` for confidence.

SIGN CONVENTION, and it is load-bearing.

    effect_pct is the percentage change in the metabolic or energy cost of
    running. POSITIVE means the test condition was BETTER (cost fell).

So every `family="aft"` row is positive - the shoe helped - and every
`family="mass"` row is negative, because adding mass to a shoe is a
manipulation that hurts. `test_shoes.py` asserts exactly that, because the
worst bug this repository has shipped came from an operation on a signed
field whose meaning was not pinned down (HANDOFF §8 item 12: the 11.65 kg
shoe).

DISPERSION, and it is the other load-bearing thing.

    `sd_pct` and `ci_pct` are different quantities and are never both set.
    Neither is ever derived from the other, and a row that published no
    dispersion carries None for both. Most of this literature reports a mean
    and nothing else; the figures say so rather than tidying it away.

INCLUSION RULE for family="aft": a controlled comparison of an
advanced-footwear shoe against a control shoe, reporting running economy or
metabolic cost as a percentage, found in the Stage 1 literature search
(`RESEARCH.md`). This is a collected table, not a systematic review, and the
page says so.
"""

# ---- studies: the one place a study's identity and colour live -------------
# F1 and F2 both read this. Three separate colour lists is the drift the
# retired shoe figure's own MAT comment warned about, in the file that then
# went on to keep its colours in three places anyway.
STUDIES = {
    "hoogkamer2016": dict(
        label="Hoogkamer et al. 2016", colour="slate",
        source="Hoogkamer W, Kipp S, Spiering BA, Kram R (2016). Altered "
               "Running Economy Directly Translates to Altered "
               "Distance-Running Performance. <i>Med Sci Sports Exerc</i> "
               "48(11):2175-2180.",
        doi="10.1249/MSS.0000000000001012"),
    "hoogkamer2018": dict(
        label="Hoogkamer et al. 2018", colour="slate",
        source="Hoogkamer W, Kipp S, Frank JH, Farina EM, Luo G, Kram R "
               "(2018). A Comparison of the Energetic Cost of Running in "
               "Marathon Racing Shoes. <i>Sports Med</i> 48(4):1009-1019 "
               "(correction, 48(6):1521-1522).",
        doi="10.1007/s40279-017-0811-2"),
    "hunter2019": dict(
        label="Hunter et al. 2019", colour="slate",
        source="Hunter I, McLeod A, Valentine D, Low T, Ward J, Hager R "
               "(2019). Running economy, mechanics, and marathon racing "
               "shoes. <i>J Sports Sci</i> 37(20):2367-2373.",
        doi="10.1080/02640414.2019.1633837"),
    "barnes2019": dict(
        label="Barnes & Kilding 2019", colour="acc",
        source="Barnes KR, Kilding AE (2019). A Randomized Crossover Study "
               "Investigating the Running Economy of Highly-Trained Male and "
               "Female Distance Runners in Marathon Racing Shoes versus Track "
               "Spikes. <i>Sports Med</i> 49(2):331-342.",
        doi="10.1007/s40279-018-1012-3"),
    "rodrigocarranza2020": dict(
        label="Rodrigo-Carranza et al. 2020", colour="slate",
        source="Rodrigo-Carranza V, Gonz&aacute;lez-Moh&iacute;no F, "
               "Santos-Concejero J, Gonz&aacute;lez-Rav&eacute; JM (2020). "
               "Influence of Shoe Mass on Performance and Running Economy in "
               "Trained Runners. <i>Front Physiol</i> 11:573660.",
        doi="10.3389/fphys.2020.573660"),
    "whiting2021": dict(
        label="Whiting et al. 2021", colour="slate",
        source="Whiting CS, Hoogkamer W, Kram R (2021). Metabolic cost of "
               "level, uphill, and downhill running in highly cushioned shoes "
               "with carbon-fiber plates. <i>J Sport Health Sci</i> "
               "11(3):303-308.",
        doi="10.1016/j.jshs.2021.10.004"),
    "knopp2023": dict(
        label="Knopp et al. 2023", colour="moss",
        source="Knopp M, Mu&ntilde;iz-Pardos B, Wackerhage H, "
               "Sch&ouml;nfelder M, Guppy F, Pitsiladis Y, Ruiz D (2023). "
               "Variability in Running Economy of Kenyan World-Class and "
               "European Amateur Male Runners with Advanced Footwear Running "
               "Technology. <i>Sports Med</i> 53(6):1255-1271.",
        doi="10.1007/s40279-023-01816-1"),
    "joubert2024": dict(
        label="Joubert et al. 2024", colour="slate",
        source="Joubert DP, Oehlert GM, Jones EJ, Burns GT (2024). "
               "Comparative Effects of Advanced Footwear Technology in Track "
               "Spikes and Road-Racing Shoes on Running Economy. <i>Int J "
               "Sports Physiol Perform</i> 19(7):705-711.",
        doi="10.1123/ijspp.2023-0372"),
    "joubert2026": dict(
        label="Joubert & Sanders 2026", colour="slate",
        source="Joubert DP, Sanders J (2026). Effects of Advanced Footwear "
               "Technology in Trail Running Shoes on Running Economy. <i>J "
               "Strength Cond Res</i>, ahead of print.",
        doi="10.1519/JSC.0000000000005553"),
    "guinness2020": dict(
        label="Guinness et al. 2020", colour="slate",
        source="Guinness J, Bhattacharya D, Chen J, Chen M, Loh A (2020). An "
               "Observational Study of the Effect of Nike Vaporfly Shoes on "
               "Marathon Performance. <i>arXiv</i>:2002.06105.",
        doi="10.48550/arXiv.2002.06105"),
}

# ---- the rows -------------------------------------------------------------
ROWS = {

    # --- family "aft": an advanced-footwear shoe against a control shoe -----

    "hoogkamer2018_proto_vs_streak": dict(
        family="aft", study="hoogkamer2018",
        comparison="prototype vs Nike Zoom Streak 6, mass matched",
        short="prototype vs flat",
        effect_pct=4.16, sd_pct=None, ci_pct=None,
        n=18, sex="male", level="high-caliber",
        speed_kmh=16.0, setting="treadmill, 14/16/18 km/h",
        note="The origin of the 4% figure. A prototype rather than a retail "
             "shoe, mass-matched with lead, at three elite marathon paces. "
             "Reported as a mean with no dispersion.",
        quality="A"),

    "hoogkamer2018_proto_vs_adios": dict(
        family="aft", study="hoogkamer2018",
        comparison="prototype vs Adidas Adizero Adios Boost, mass matched",
        short="prototype vs flat",
        effect_pct=4.01, sd_pct=None, ci_pct=None,
        n=18, sex="male", level="high-caliber",
        speed_kmh=16.0, setting="treadmill, 14/16/18 km/h",
        note="The same prototype against the other established racing shoe.",
        quality="A"),

    "barnes2019_vaporfly_vs_adios": dict(
        family="aft", study="barnes2019",
        comparison="Nike Vaporfly vs Adidas Adizero Adios 3",
        short="retail vs flat",
        effect_pct=4.2, sd_pct=1.2, ci_pct=None,
        individual_range_pct=(1.72, 7.15),
        individual_group="highly trained, vs racing flat",
        n=24, sex="12 male, 12 female", level="highly trained",
        speed_kmh=16.0, setting="treadmill, 14-18 km/h",
        note="One of only two studies here with women in the sample. Against "
             "the same shoe mass-matched the figure is 2.9%, so about a third "
             "of this comparison is the Vaporfly being lighter rather than "
             "anything about its foam or plate.",
        quality="A"),

    "whiting2021_level": dict(
        family="aft", study="whiting2021",
        comparison="Nike Vaporfly 4% vs Nike Zoom Streak 6, level",
        short="retail, level",
        effect_pct=3.83, sd_pct=None, ci_pct=None,
        n=16, sex="male", level="competitive",
        speed_kmh=13.0, setting="treadmill, level",
        note="Metabolic power rather than oxygen uptake. The level condition "
             "of the study that also ran it uphill and downhill.",
        quality="A"),

    "barnes2019_vaporfly_massmatched": dict(
        family="aft", study="barnes2019",
        comparison="Nike Vaporfly matched to Adios mass vs Adidas Adizero "
                   "Adios 3",
        short="retail, mass matched",
        effect_pct=2.9, sd_pct=1.3, ci_pct=None,
        n=24, sex="12 male, 12 female", level="highly trained",
        speed_kmh=16.0, setting="treadmill",
        note="The same pair of shoes as the 4.2% row with the mass difference "
             "removed. The gap between the two rows is what mass was worth.",
        quality="A"),

    "whiting2021_uphill": dict(
        family="aft", study="whiting2021",
        comparison="Nike Vaporfly 4% vs Nike Zoom Streak 6, +3 degrees",
        short="retail, uphill",
        effect_pct=2.82, sd_pct=None, ci_pct=None,
        n=16, sex="male", level="competitive",
        speed_kmh=13.0, setting="treadmill, +3 degrees",
        note="Significantly smaller than the same study's level condition.",
        quality="A"),

    "hunter2019_vaporfly_vs_adios": dict(
        family="aft", study="hunter2019",
        comparison="retail Nike Vaporfly 4% vs Adidas Adizero Adios Boost",
        short="retail vs flat",
        effect_pct=2.8, sd_pct=None, ci_pct=None,
        n=19, sex="male", level="trained",
        speed_kmh=16.0, setting="treadmill, 4.44 m/s",
        note="The consumer version of the shoe, measured by an independent "
             "group against the same control brand as the prototype study, at "
             "about two thirds of the prototype's benefit.",
        quality="A"),

    "whiting2021_downhill": dict(
        family="aft", study="whiting2021",
        comparison="Nike Vaporfly 4% vs Nike Zoom Streak 6, -3 degrees",
        short="retail, downhill",
        effect_pct=2.70, sd_pct=None, ci_pct=None,
        n=16, sex="male", level="competitive",
        speed_kmh=13.0, setting="treadmill, -3 degrees",
        note="Not statistically distinguishable from the level condition in "
             "the paper, unlike the uphill one.",
        quality="A"),

    "barnes2019_vaporfly_vs_spike": dict(
        family="aft", study="barnes2019",
        comparison="Nike Vaporfly vs Nike Zoom Matumbo 3 track spike",
        short="retail vs spike",
        effect_pct=2.6, sd_pct=1.3, ci_pct=None,
        individual_range_pct=(-0.50, 5.34),
        individual_group="highly trained, vs track spike",
        n=24, sex="12 male, 12 female", level="highly trained",
        speed_kmh=16.0, setting="treadmill",
        note="The lower end of the individual range is negative: at least one "
             "runner was less economical in the shoe than in the control. The "
             "population mean and the individual outcome are different "
             "quantities and this row carries both.",
        quality="A"),

    "joubert2024_spike_a": dict(
        family="aft", study="joubert2024",
        comparison="AFT track spike vs traditional track spike",
        short="AFT spike vs spike",
        effect_pct=2.1, sd_pct=1.0, ci_pct=None,
        n=9, sex="male", level="distance runners",
        speed_kmh=16.0, setting="treadmill",
        note="The first of two AFT spikes the study tested.",
        quality="A"),

    "joubert2024_spike_b": dict(
        family="aft", study="joubert2024",
        comparison="second AFT track spike vs traditional track spike",
        short="AFT spike vs spike",
        effect_pct=1.8, sd_pct=1.0, ci_pct=None,
        n=9, sex="male", level="distance runners",
        speed_kmh=16.0, setting="treadmill",
        note="The second AFT spike in the same study. Included because the "
             "table's rule is every controlled comparison, and dropping the "
             "smaller of a study's two arms is how a collected table starts "
             "flattering itself.",
        quality="A"),

    "hunter2019_vaporfly_vs_streak": dict(
        family="aft", study="hunter2019",
        comparison="retail Nike Vaporfly 4% vs Nike Zoom Streak",
        short="retail vs flat",
        effect_pct=1.9, sd_pct=None, ci_pct=None,
        n=19, sex="male", level="trained",
        speed_kmh=16.0, setting="treadmill, 4.44 m/s",
        note="The same retail shoe as the 2.8% row, against the other control.",
        quality="A"),

    "joubert2026_trail": dict(
        family="aft", study="joubert2026",
        comparison="AFT trail shoe vs control trail shoe, outdoors",
        short="AFT trail, outdoors",
        effect_pct=1.1, sd_pct=1.1, ci_pct=None,
        n=8, sex="not stated in the abstract", level="trail runners",
        speed_kmh=11.5,
        setting="outdoor trail, portable analyser",
        note="The only row measured outside a laboratory, and the slowest. Its "
             "standard deviation equals its mean.",
        quality="B"),

    # --- family "mass": mass added to a shoe --------------------------------

    "hoogkamer2016_mass_metabolic": dict(
        family="mass", study="hoogkamer2016",
        comparison="+100 g per shoe, metabolic rate",
        short="metabolic cost",
        effect_pct=-1.11, sd_pct=None, ci_pct=(-1.35, -0.88),
        n=18, sex="male", level="sub-20-min 5 km",
        speed_kmh=12.6, setting="treadmill, 3.5 m/s",
        note="The founding constant of the field, restated from Frederick, "
             "Daniels and Hayes 1984 and measured directly here. The one "
             "genuine confidence interval in this table.",
        quality="A"),

    "hoogkamer2016_mass_time": dict(
        family="mass", study="hoogkamer2016",
        comparison="+100 g per shoe, 3000 m time-trial time",
        short="race time",
        effect_pct=-0.78, sd_pct=None, ci_pct=(-1.04, -0.52),
        n=18, sex="male", level="sub-20-min 5 km",
        speed_kmh=None, setting="3000 m time trial",
        measures="time",
        note="The only row in the table measured as race time rather than as "
             "oxygen or energy cost. Its ratio to the metabolic row is the "
             "transfer coefficient the page uses, and labels assumed wherever "
             "it is applied to anything but added mass.",
        quality="A"),

    "rodrigocarranza2020_mass_85vt2": dict(
        family="mass", study="rodrigocarranza2020",
        comparison="+100 g per shoe, energy cost at 85% of VT2",
        short="energy cost at 85% VT2",
        effect_pct=-7.40, sd_pct=None, ci_pct=None,
        n=11, sex="6 male, 5 female", level="trained",
        speed_kmh=None, setting="treadmill, 85% of second ventilatory threshold",
        note="Several times the accepted per-100 g figure, for the same "
             "manipulation. Peer-reviewed, not retracted, and rarely cited "
             "against the number it contradicts.",
        quality="B"),

    "rodrigocarranza2020_mass_95vt2": dict(
        family="mass", study="rodrigocarranza2020",
        comparison="+100 g per shoe, energy cost at 95% of VT2",
        short="energy cost at 95% VT2",
        effect_pct=-10.21, sd_pct=None, ci_pct=None,
        n=11, sex="6 male, 5 female", level="trained",
        speed_kmh=None, setting="treadmill, 95% of second ventilatory threshold",
        note="The same study's harder condition, further still from the "
             "accepted figure.",
        quality="B"),

    # --- family "individual": a per-athlete range, no mean ------------------

    "knopp2023_kenyan": dict(
        family="individual", study="knopp2023",
        comparison="three AFT models vs a racing flat, per-athlete range",
        short="world-class Kenyan runners",
        effect_pct=None, sd_pct=None, ci_pct=None,
        individual_range_pct=(-11.3, 11.4),
        individual_group="world-class Kenyan runners",
        n=7, sex="male", level="world-class, mean half-marathon 59:30",
        speed_kmh=None, setting="treadmill",
        note="The group the shoes were designed for, and the widest range "
             "anyone has published. Recorded as the paper states it: an 11.3% "
             "drawback to an 11.4% benefit.",
        quality="A"),

    "knopp2023_amateur": dict(
        family="individual", study="knopp2023",
        comparison="three AFT models vs a racing flat, per-athlete range",
        short="European amateur runners",
        effect_pct=None, sd_pct=None, ci_pct=None,
        individual_range_pct=(-1.1, 9.7),
        individual_group="European amateur runners",
        n=7, sex="male", level="amateur",
        speed_kmh=None, setting="treadmill",
        note="The comparison group in the same study.",
        quality="A"),

    # --- family "race": observed finishing times ----------------------------

    "guinness2020_men": dict(
        family="race", study="guinness2020",
        comparison="Vaporfly vs not, marathon finishing time, men",
        short="observed in races, men",
        effect_pct=None, sd_pct=None, ci_pct=(1.4, 2.8),
        n=None, sex="male", level="elite and sub-elite",
        speed_kmh=None,
        setting="22 marathons 2015-2019, shoes read from public race photographs",
        measures="time",
        note="Observational, not randomised: runners chose their own shoes and "
             "the fastest adopted them first. The interval is the result; "
             "there is no point estimate to draw.",
        quality="B"),

    "guinness2020_women": dict(
        family="race", study="guinness2020",
        comparison="Vaporfly vs not, marathon finishing time, women",
        short="observed in races, women",
        effect_pct=None, sd_pct=None, ci_pct=(0.6, 2.2),
        n=None, sex="female", level="elite and sub-elite",
        speed_kmh=None,
        setting="22 marathons 2015-2019, shoes read from public race photographs",
        measures="time",
        note="The women's interval from the same model.",
        quality="B"),
}

# ---- what the page says about the literature it does not tabulate ----------
# Meta-analyses are cited in prose and in Sources; they are not rows, because
# a standardised mean difference does not share an axis with a percentage and
# putting them on one would be the conflation the whole page argues against.
META = {
    "xiao2025": dict(
        label="Xiao et al. 2025", smd=-0.44, ci=(-0.59, -0.30),
        studies=17, n=281,
        note="Also reports time-trial performance at g=-0.23, about half the "
             "size of the oxygen effect.",
        source="Xiao Y, Hu X, Tian D, Qiu A (2025). Effects of Advanced "
               "Footwear Technology on Running Economy and Endurance "
               "Performance: A Meta-Analysis. <i>Int J Sports Med</i> "
               "47(2):81-94.",
        doi="10.1055/a-2637-7283"),
    "stephen2025": dict(
        label="Stephen et al. 2025", smd=-0.44, ci=(-0.60, -0.28),
        studies=48, n=878,
        note="Neither longitudinal bending stiffness alone nor midsole energy "
             "return alone significantly affected oxygen consumption; only "
             "their interaction did. Quality of evidence graded low or very "
             "low for almost every outcome.",
        source="Stephen CHN, Kelly LA, Schuster RW, Diamond LE (2025). The "
               "effects of running shoe longitudinal bending stiffness and "
               "midsole energy return on oxygen consumption and ankle "
               "mechanics and energetics. <i>J Sport Health Sci</i> 14:101069.",
        doi="10.1016/j.jshs.2025.101069"),
    "rodrigocarranza2022": dict(
        label="Rodrigo-Carranza et al. 2022", smd=-0.43, ci=(-0.58, -0.28),
        studies=12, n=None,
        note="A curved plate improved economy 3.45% against no plate; a flat "
             "plate showed no improvement.",
        source="Rodrigo-Carranza V, Gonz&aacute;lez-Moh&iacute;no F, "
               "Santos-Concejero J, Gonz&aacute;lez-Rav&eacute; JM (2022). The "
               "effects of footwear midsole longitudinal bending stiffness on "
               "running economy and ground contact biomechanics. <i>Eur J "
               "Sport Sci</i> 22(10):1508-1521.",
        doi="10.1080/17461391.2021.1955014"),
    "ortega2021": dict(
        label="Ortega et al. 2021", smd=None, ci=None, studies=None, n=None,
        note="Puts the bending-stiffness literature at about 3% deterioration "
             "to about 3% improvement. The sign of the effect is not settled.",
        source="Ortega JA, Healey LA, Swinnen W, Hoogkamer W (2021). "
               "Energetics and Biomechanics of Running Footwear with Increased "
               "Longitudinal Bending Stiffness: A Narrative Review. <i>Sports "
               "Med</i> 51(5):873-894.",
        doi="10.1007/s40279-020-01406-5"),
    "fuller2015": dict(
        label="Fuller et al. 2015", smd=None, ci=None, studies=19, n=None,
        note="Found a significant positive association between shoe mass and "
             "metabolic cost, and no studies at all reporting effects on "
             "running performance as opposed to economy, as of April 2014.",
        source="Fuller JT, Bellenger CR, Thewlis D, Tsiros MD, Buckley JD "
               "(2015). The effect of footwear on running performance and "
               "running economy in distance runners. <i>Sports Med</i> "
               "45(3):411-422.",
        doi="10.1007/s40279-014-0283-6"),
}

# ---- the one thing on the page that is not measured -----------------------
# Applying this to anything but added mass is an assumption, and every number
# derived through it carries assumed=True into the payload and the word
# "assumed" onto the page.
TRANSFER_NOTE = (
    "The ratio of the two Hoogkamer 2016 rows: a 1% change in the metabolic "
    "cost of running bought this fraction of a percent in 3000 m time, for "
    "added shoe mass, in trained men. It has never been measured for advanced "
    "footwear."
)
