# Fat, sugar, salt

What prepared food has that no raw food has: the combination. Every solid
food in USDA SR Legacy, placed by the share of its energy from fat and from
sugar and by its sodium by weight, against the published hyper-palatable-food
thresholds (Fazzino, Rohde & Sullivan, *Obesity* 2019), split into raw and
prepared by a stated rule, with three nulls that ask whether the separation
is a fact about food or an artefact of the axes.

## Run it

```
python3 fetch_data.py      # downloads the pinned USDA zip, checks its hash, writes data/sr_legacy_slim.csv
python3 build_food.py      # the rule, the split, the nulls, the pairs -> outputs/food_payload.json, outputs/items.csv
python3 fig_food.py        # four figures -> ../site/assets/food_fig*.png, each audited (must print 0 problems)
python3 update_page.py --apply   # writes ../site/food.html from template.html and the payload
python3 test_food.py       # the project's own failure modes
```

`fetch_data.py` needs the network once; the other scripts run offline.
`fig_food.py` needs matplotlib and Pillow and the site's `sitefig.py`,
`fig_floor.py` and `fonts/` one level up. `build_food.py` takes about a
minute, most of it the 1,000-deal permutation null.

## What it computes

- For each food: fat, sugar and starch as per cent of energy (9 and 4
  kcal/g; starch is carbohydrate less fibre less sugar), sodium as per cent
  by weight (mg per 100 g over 1,000), and whether it clears each of the
  three published pairs.
- The split: raw if the USDA description says raw and none of the exclusion
  words (`RAW_EXCLUDE`); prepared if in one of ten SR groups
  (`PREPARED_GROUPS`). Both are the page's rule and are labelled assumed.
  Beverages are out, as in the source paper. Foods under 50 kcal per 100 g
  are left out of every count.
- Null 1: within each group, sugar shares dealt back to foods at random under
  fat + sugar <= 100; sodium shuffled against fat and against starch.
  Seeded; the test checks the recorded numbers reproduce.
- Null 2: uniform Dirichlet over fat, carbohydrate and protein shares, sugar
  a uniform fraction of carbohydrate.
- Null 3: grams per 100 g, no constraint.
- Pairs: raw items and their prepared variants by USDA's own suffix naming;
  "with salt" variants left out because USDA imputes that salt.

## Files

| File | What |
|---|---|
| `fetch_data.py` | pinned download, SHA-256, six-column slim table |
| `build_food.py` | the model; writes the payload and the per-item table |
| `fig_food.py` | the four figures, through `sitefig.py` |
| `template.html`, `update_page.py` | the page, every number from the payload |
| `test_food.py` | leak test for the raw group, the human-milk exception, null reproducibility, the pairs exclusion, page-payload agreement |
| `data/sr_legacy_slim.csv` | 7,793 foods, the eight nutrient columns read |
| `outputs/food_payload.json` | everything the page and figures read |
| `outputs/items.csv` | one row per food with shares and flags |
| `DATA_SOURCES.md` | where the data is from and what it lacks |
| `RESEARCH.md` | the Stage 1 research and feasibility memo; this is the only copy (`03 RESEARCH/food/` holds a pointer and the scratch scripts it superseded) |

## What it does not claim

Composition is not palatability; two rating studies find the rule does not
predict liking, and the page says so. Nothing about intent, addiction or a
"bliss point" is asserted. The rule is not the NOVA ultra-processed
classification and the page does not use NOVA.
