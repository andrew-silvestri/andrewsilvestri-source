# Data sources

## Used

**USDA FoodData Central, SR Legacy, April 2018 release.** Public domain
(CC0). 7,793 foods, nutrients per 100 g. The final release of the Standard
Reference database, frozen since; `fetch_data.py` pins it by SHA-256.
Download: `https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip`
(6.1 MB). Columns read, by FDC nutrient id: 1008 energy kcal, 1004 total
fat, 1005 carbohydrate by difference, 1003 protein, 2000 sugars total (1063
sugars total NLEA as the fallback), 1079 fibre total dietary, 1093 sodium.
The 25 food groups come from `food_category.csv`. 5,977 foods carry all of
energy, fat, carbohydrate, sugar and sodium; 279 of those are in the two
beverage groups or the quality-control group and are set aside.

What it lacks: any processing field (the raw / prepared split is by
description string and food group, see `build_food.py`); added sugar (only
total sugar); fibre for 24 of the raw and prepared foods.

## Looked up, not recomputed

Each carries its citation in `outputs/food_payload.json` under `looked_up`
and on the page under Sources.

- The three threshold pairs and how they were derived; 62% of FNDDS 2015-16
  items: Fazzino, Rohde & Sullivan, *Obesity* 27(11):1761-1768, 2019,
  doi:10.1002/oby.22639.
- 49% / 62% / 69% of items in 1988 / 2001 / 2017-18: Demeke et al., *Public
  Health Nutrition* 26(1):182-189, 2023, doi:10.1017/S1368980022001227.
- 40-70% overlap with NOVA ultra-processed: Sutton et al., *Obesity*
  32(1):166-175, 2024, doi:10.1002/oby.23897.
- 67.1% of store items, 59.4% of purchases: Fazzino et al., *Public Health
  Nutrition* 29(1):e110, 2026, doi:10.1017/S1368980026102614.
- No palatability difference by rule status: Rogers, Vural, Flynn &
  Brunstrom, *Appetite* 201:107596, 2024. Nutrients explain ~20% of liking:
  Finlayson et al., *Appetite* 213:108029, 2025.
- Fat plus carbohydrate valued supra-additively; breast milk the natural
  exception: DiFeliceantonio et al., *Cell Metabolism* 28(1):33-44, 2018.
- Pleasantness peaks with sugar: Moskowitz et al., *Science* 184:583-585,
  1974.
- The share-of-energy arithmetic: Sadler, McNulty & Gibson, *Crit Rev Food
  Sci Nutr* 55(3):338-356, 2015.

## Considered and not used

- **USDA FNDDS 2021-2023** (5,432 codes, as-eaten, WWEIA categories): would
  reproduce the paper's own prevalence on the current cycle; not needed for
  the claim. 200 MB.
- **USDA Global Branded Foods** (0.4-2 M items, label nutrients, ingredient
  text): named products; not needed. 428 MB.
- **Open Food Facts** (~4 M items, algorithmic NOVA, ODbL): crowdsourced,
  heavy filtering needed (the 2025 Fazzino-group cleaning kept about 10%);
  not used.
- **A FNDDS-code-to-NOVA table**: Martinez Steele et al., *J Nutr*
  153(1):225-241, 2023, supplement is descriptions by group to 2017-18; the
  NCI code-level files are request-only. Not obtainable without a request,
  and not needed: this page's axis is composition, not processing.
