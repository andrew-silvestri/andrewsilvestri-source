# Research and feasibility: the science of modern food

Stage 1 of `00 PUBLISH/prompts/NEW_PROJECTS.md` §3. Written 5 September 2026.
Lives in `03 RESEARCH/food/` with the SR Legacy download (`sr_legacy.zip`),
the feasibility script (`hpf_check.py`, writes `hpf_rows.json` and
`feas_scatter.png`) and the null script (`null_check.py`). No design
decisions are made here.

## 1. Verdict

**The project exists, in a narrower form than the brief states.** The
compositional half of the claim is supportable from a single public-domain
download and a named, peer-reviewed definition. The intent half ("engineered")
and the addiction half are not supportable from data and go on the page only
as labelled interpretation, or not at all.

Supportable claim, one sentence: *Foods that combine fat with sugar, or fat or
starch with salt, in the proportions that the published hyper-palatable-food
definition specifies are almost absent from the raw food supply and are the
majority of formulated foods, and the share of the US food supply meeting that
definition rose from about half to about two-thirds between 1988 and 2018.*

Not supportable: that the combinations were designed to be addictive. The
peer-reviewed hyper-palatable-food work itself says the engineering claim comes
from documentaries and journalism, and two 2024–2025 rating studies find that
meeting the definition does not predict how much people say they like a food.

## 2. The primary literature

**The quantitative definition.** Fazzino, Rohde and Sullivan, *Obesity*
27(11):1761–1768, 2019, doi:10.1002/oby.22639. Three clusters, any one of
which makes a food hyper-palatable (HPF):

| Cluster | Rule |
|---|---|
| FSOD (fat and sodium) | fat > 25 % of kcal **and** sodium ≥ 0.30 % by weight |
| FS (fat and sugar) | fat > 20 % of kcal **and** sugar > 20 % of kcal |
| CSOD (carbohydrate and sodium) | carbohydrate > 40 % of kcal **and** sodium ≥ 0.20 % by weight |

Fat and carbohydrate are per cent of energy (9 and 4 kcal/g); sodium is grams
of sodium per gram of food. Carbohydrate in CSOD is total carbohydrate minus
fibre minus sugar. Sugar is total sugar, natural plus added. Liquids are
excluded by the authors.

How the thresholds were derived matters for the page: 14 papers with
descriptive definitions of hyper-palatable foods yielded 75 named solid foods,
which were plotted and segmented by eye into three clusters; the cut-points are
the minimum values inside each cluster. The authors say so and say the
cut-points "should not be assumed to be fixed or final". There is no formal
clustering behind them.

Applied to USDA FNDDS 2015–2016 (8,690 items, 933 beverages excluded, 7,757
analysed): 62 % met at least one cluster (FSOD 70 % of those, FS 25 %, CSOD
16 %; under 10 % in more than one). By food group: meats 75 %, eggs 85 %,
grains 71 %, milk 69 %, fats and oils 65 %, sweets 51 %, vegetables 47 %, beans
and nuts 42 %, fruit 7 %. Of 443 items labelled reduced-fat, -sugar, -salt or
-calorie, 49 % were still HPF. The discriminant-validity check is the part
this project stands on: no fresh or raw fruit, meat or fish met any cluster,
and 97 % of 69 raw vegetables did not (chives and arugula are caught by FS
because their energy denominator is tiny). A second finding: the same food
code (e.g. chicken leg) is HPF or not depending on preparation, so the
definition is about what is done to a food, not the food.

**The time series.** Demeke et al., *Public Health Nutrition* 26(1):182–189,
2023, doi:10.1017/S1368980022001227. NHANES-III 1988 (6,216 items), FNDDS 2001
(6,125), FNDDS 2017–18 (6,081): HPF 49 % → 62 % → 69 %; FSOD 32/42/49 %, FS
12/13/13 %, CSOD 10/13/12 %. The 3,893 items present in all three years were
2.4× (2001) and over 4× (2018) as likely to be HPF as in 1988, which the
authors read as reformulation. Sensitivity κ = 0.48 across database
structures; the three databases are not identical in construction.

**HPF versus ultra-processed.** Sutton et al., *Obesity* 32(1):166–175, 2024,
doi:10.1002/oby.23897: HPF, NOVA ultra-processed (UPF) and high energy density
overlap "40 %–70 %"; HPF rose 14 points 1988–2018, UPF 4. Jun, Knowles and
Fazzino, *PLoS One* 20(6):e0325479, 2025: Open Food Facts, 314,229 items, 17
countries, HPF 54.5 % (Australia) to 68.0 % (Bulgaria), US 63.0 %; items both
HPF and NOVA-4 33–50 %. So HPF is not a synonym for ultra-processed, and this
project does not need NOVA at all: its axis is composition.

**Shelf and purchase share.** Fazzino et al., *Public Health Nutrition*
29(1):e110, 2026, doi:10.1017/S1368980026102614: Circana scanner data
2015–2018, HPF = 67.1 % of items per store, 59.4 % of household purchases.

**Fat plus carbohydrate as a reward signal.** DiFeliceantonio et al., *Cell
Metabolism* 28(1):33–44, 2018, doi:10.1016/j.cmet.2018.05.018 (N = 206):
people bid more for foods containing both fat and carbohydrate than for
equally liked, equicaloric fat-only or carbohydrate-only foods, with a
supra-additive striatal response. The paper's remark that fat–carbohydrate
foods are rare in nature apart from breast milk is paraphrased from an indexed
snippet; the full text was paywalled and the exact wording is unverified. The
press-release quote from the senior author is verified.

**The "rarely in nature" statement elsewhere.** Schulte, Avena and Gearhardt,
*PLoS One* 10(2):e0117959, 2015, and Gearhardt et al., *BMJ* 383:e075354,
2023, both assert it; the BMJ piece gives two examples (apple, salmon). No
paper was found that plots or tabulates the joint fat–sugar–sodium
distribution of raw versus formulated foods across a composition database.
The Fazzino 2019 discriminant check is the nearest thing. **That analysis is
open**, which is good for the site (it would be computed, from a public source)
and a caution (there is no published number for the separation itself to cite;
the page's number would be its own, labelled computed).

**Bliss point.** Moskowitz, Kluter, Westerling and Jacobs, *Science*
184(4136):583–585, 1974: perceived sweetness rises monotonically with sucrose
concentration, pleasantness rises then falls. This is the peer-reviewed basis;
"bliss point" as a phrase and the industry anecdotes are from Moss, *Salt Sugar
Fat* (2013), a copyrighted book that is not needed for anything on the page.

**The intake experiment.** Hall et al., *Cell Metabolism* 30(1):67–77, 2019,
doi:10.1016/j.cmet.2019.05.008: N = 20, inpatient crossover, two 14-day arms
matched for presented energy, macronutrients, sugar, sodium and fibre;
ultra-processed arm +508 ± 106 kcal/day and +0.9 kg versus −0.9 kg. This is
about ultra-processing, not the HPF composition rule; it is context, not
evidence for the claim.

**The critiques, which the page must carry.** Rogers, Vural, Flynn and
Brunstrom, *Appetite* 201:107596, 2024: 52 foods rated by 72–224 people each;
no palatability difference HPF vs non-HPF or UPF vs non-UPF (p ≥ 0.41);
"results do not support the use of hypothetical combinations of food
ingredients as proxies for palatability." Finlayson et al., *Appetite*
213:108029, 2025: 436 foods, 3,364 raters; nutrients explain about 20 % of
liking. Fletcher and Kenny, *Neuropsychopharmacology* 43(13):2506–2513, 2018:
the food-addiction construct has no identified agent and unvalidated
tolerance/withdrawal. Sadler, McNulty and Gibson, *Crit Rev Food Sci Nutr*
55(3):338–356, 2015: at diet level the sugar–fat inverse relation on a
per-cent-energy basis is partly arithmetic (the shares sum to 100). That
arithmetic applies to any %-energy plot on this page and must be stated.

## 3. The primary data

All of the following are free. None requires a key for bulk download.

| Source | Items | Fields needed | Processing marker | Size, licence |
|---|---|---|---|---|
| USDA SR Legacy (Apr 2018, frozen) | 7,793 | kcal, fat, total sugar, carbohydrate, fibre, sodium per 100 g | 25 food groups; "raw"/"cooked"/"canned" only in the description string | 6.1 MB zip CSV, CC0 |
| USDA Foundation Foods | 394 | same; recent analytical values | inherits SR groups | 3.7 MB zip, CC0 |
| USDA FNDDS 2021–2023 | 5,432 codes | same, as-eaten; includes home-prepared recipes with public ingredient table | WWEIA category (172) on every code; no NOVA | 200 MB zip, CC0 |
| USDA Global Branded Foods | 0.4–2.0 M (count unverified) | label nutrients, brand, ingredient text, category | brand and ingredients | 428 MB zip, CC0 |
| Open Food Facts | ~4 M | per 100 g; algorithmic NOVA (marked experimental by OFF) | NOVA 1–4 | 7.8 GB parquet, ODbL |

Not obtainable without a request: a clean FNDDS-code-to-NOVA table (Martínez
Steele et al., *J Nutr* 153(1):225–241, 2023, supplement mmc1.xlsx is
descriptions by group to 2017–18; NCI's code-level files are proposal-gated).
Not obtainable at all: added-sugar values in SR Legacy, Foundation or FNDDS,
and the 1988 and 2001 databases in a form matching Demeke 2023 without
rebuilding their harmonisation. Fazzino 2019's item-level classification is
not published, but the rule is explicit and reproducible from FNDDS.

Recommendation on sources: SR Legacy is enough for the separation figure (see
§4) and carries the human-milk item, the raw-versus-cooked variants, and every
formulated group. Branded Foods adds named products if Stage 2 wants them.
FNDDS adds as-eaten dishes and lets the 2015–16 prevalence be reproduced on
the current cycle. Open Food Facts is not needed and brings crowdsourced noise
(the 2025 Fazzino-group cleaning kept about 10 % of it).

## 4. Feasibility check: is the separation real?

Done on SR Legacy today, in the session scratchpad, not the repo. Rule as in
§2 except that CSOD used total carbohydrate rather than carbohydrate minus
fibre and sugar, so CSOD counts here are slightly high; the FS and FSOD
counts are exact. Groups:

- **raw**: description contains "raw", minus items whose description also
  contains sausage, cured, salted, bockwurst or chorizo (USDA calls raw
  sausage "raw"); 980 items, 835 at ≥ 50 kcal/100 g.
- **formulated**: food groups Snacks, Sweets, Baked Products, Fast Foods,
  Breakfast Cereals, Sausages and Luncheon Meats, Restaurant Foods, Meals,
  Entrees and Side Dishes, Soups, Sauces and Gravies, Branded; 1,781 items,
  1,701 at ≥ 50 kcal/100 g.

Items at ≥ 50 kcal/100 g, count inside each cluster's region:

| Region | raw (n = 835) | formulated (n = 1,701) |
|---|---|---|
| FS: fat > 20 % and sugar > 20 % of kcal | 1 (grape leaves) | 350 |
| FSOD: fat > 25 % of kcal and Na ≥ 0.30 % | 0 | 744 |
| CSOD: carb > 40 % of kcal and Na ≥ 0.20 % | 0 | 900 |
| any | 1 | 84 % |

Without the energy floor, 8 of 980 raw items qualify, all low-energy leafy
vegetables or tomatillos caught by the FS denominator, the artefact Fazzino
2019 also reports. Human milk (70 kcal, 56 % fat, 39 % sugar) meets FS, which
is the DiFeliceantonio exception, present in the data rather than asserted.
Coconut (85 % fat, 7 % sugar), avocado (82 %, 2 %), cashew (71 %, 4 %) and
dates or bananas (near 0 % fat) all sit on an axis, not in the interior. A
scatter of the two groups in fat–sugar space shows raw foods along the two
axes in an L and formulated foods filling the interior; in fat–sodium space
raw foods lie flat below 0.1 % sodium and formulated foods float above 0.3 %.
Plain-cooked, unsalted items (401) contribute 4 HPF, all cured or fatty pork.

So the figure the brief hopes for is real, with two caveats that go on the
page: the % energy axes are compositional (they sum to 100, so the raw L is
partly arithmetic, per Sadler 2015), and "raw" is a description-string rule,
not a NOVA classification.

## 5. What a reader already believes, and what this adds

Already believed: junk food is high in fat, sugar and salt. That is not what
the data says, and correcting it is the project:

1. **It is the co-occurrence, not the amount.** Nuts are 70–85 % fat, dates
   are 90 % sugar, and neither is hyper-palatable by the definition. Raw foods
   occupy the axes; formulated foods occupy the interior. A reader has not seen
   this drawn.
2. **The definition is quantitative and covers most of the supply.** 62 % of
   US FNDDS items in 2015–16, 69 % in 2017–18, 67 % of items on store shelves.
   Readers think of a small category of junk; the definition catches most
   meat and grain preparations, and half of "reduced" products.
3. **It is preparation, not the food.** Chicken leg is or is not HPF by how
   it is cooked. That cuts against a pure "industrial versus natural" framing:
   home cooking with added salt and fat produces the same compositions. The
   brief's word "industrially" is only supported by the scanner-data and
   reformulation papers, not by the composition rule.
4. **The rise is reformulation.** Items present in the US database in 1988,
   2001 and 2018 became four times as likely to be HPF.
5. **The definition may not measure palatability.** Two rating studies say it
   does not. The page must say so, or it is the loud version.

## 6. Traps found

- The thresholds were drawn by eye from 75 foods. Present them as the
  published rule, with that origin stated, not as a natural boundary.
- Low-energy foods break %-energy rules. An energy floor, or plotting absolute
  g/100 g alongside, is needed; the choice belongs to Stage 2.
- USDA "raw" includes raw sausage and salted frozen egg. Any whole-food rule
  must be written down and tested.
- "Engineered", "addictive" and "bliss point" are claims about intent and
  mechanism. Composition is measured; those are interpretation and get the
  label. Moss's book is not a source for any number.
- HPF and ultra-processed are different things with 40–70 % overlap. Do not
  use them interchangeably and do not import Hall 2019 as evidence for
  composition.

## 7. Kill criteria

None met. Data exists and is public domain; the weaker claim is more
interesting than the loud one (§5); the honest version is not something a
reader already knows; no needed source is copyright-locked.

## 8. Reproducing the check

Download `FoodData_Central_sr_legacy_food_csv_2018-04.zip` from
`https://fdc.nal.usda.gov/fdc-datasets/`. Nutrient ids: 1008 kcal, 1004 fat,
1005 carbohydrate, 2000 total sugar (1063 NLEA fallback), 1093 sodium mg,
1079 fibre. Per 100 g: fat % kcal = 9·fat/kcal, sugar % kcal = 4·sugar/kcal,
sodium % weight = mg/1000. Group by food_category.csv names and a
case-insensitive "raw" match on food.csv descriptions with the exclusions in
§4. `hpf_check.py` in this folder does it; `null_check.py` runs §9. A Stage 3
generator would redo both inside the project folder.

## 9. The null: is the L geometry or food?

Asked after Stage 1: fat %, carbohydrate % and protein % of energy sum to
100, so the fat–sugar plane is a constrained simplex and raw foods "on the
axes" could be geometry. Three nulls, same groups and energy floor as §4
(raw n = 835, formulated n = 1,701), seed 1, 1,000 permutations.

**Null 1, permutation within group.** Each group keeps its own marginal
distributions of fat % and sugar % but the pairing is shuffled, rejecting any
pair with fat + sugar > 100 (the simplex constraint). Sodium is shuffled
against fat and against carbohydrate the same way.

| Region | raw observed | raw null mean [min–max] | formulated observed | formulated null |
|---|---|---|---|---|
| FS | 1 | 30.8 [21–40] | 350 | 355 [323–384] |
| FSOD | 0 | 5.1 [1–7] | 744 | 692 [662–723] |
| CSOD | 0 | 2.6 [0–8] | 900 | 970 [949–998] |

Raw foods avoid the fat-and-sugar interior about thirty times more strongly
than their marginals predict (79 % of raw items are > 20 % fat, 7 % are > 20 %
sugar, so independence expects 48 in the region before the simplex rejection,
31 after; one is observed, and it is grape leaves). Formulated foods land in
the interior at exactly the rate independence predicts: their fat and sugar
marginals are both high and the pairing is random. That is the honest
statement of the figure: formulation does not target the interior, it
removes the exclusion.

For the two sodium rules the separation is one-dimensional. Only 1 % of raw
items reach 0.30 % sodium by weight (seaweed, some shellfish), so no
co-occurrence structure is needed to explain it: sodium above the threshold
means salt was added. Formulated FSOD is slightly above chance, CSOD slightly
below.

**Null 2, pure geometry.** Uniform Dirichlet(1,1,1) over (fat, carbohydrate,
protein) energy shares, sugar a uniform fraction of carbohydrate, 200,000
draws: 15.6 % of random compositions fall in the FS region. Raw foods are at
0.1 %, formulated at 20.6 %. The simplex does not empty the interior.

**Null 3, mass space.** Grams per 100 g have no energy-share constraint.
Items with ≥ 10 g fat and ≥ 10 g sugar per 100 g: raw 1 of 835 (a sugared
frozen egg yolk that the "raw" rule let through, so 0 true raw items),
formulated 334 of 1,701 (19.6 %). At ≥ 5 g each: raw 7 of 835 (three nuts,
soybeans, chickpeas, soy flour, the egg yolk), formulated 553 (32.5 %). The
separation is the same in mass space as in energy-share space.

Conclusion: the L is a fact about raw food, not about the axes. The figure
can be drawn, provided the page says that formulated foods occupy the
interior at chance given their marginals, and that the sodium half of the
definition is a statement about added salt rather than a combination.
