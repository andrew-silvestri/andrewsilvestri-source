# Data sources — Economy is not time

Every source the page rests on, what it contributes, and its licence. Nothing
on this page comes from a training manual: *Advanced Marathoning* and books
like it are copyrighted, their tables and prescriptions cannot be reproduced or
rebuilt as a calculator, and none was consulted. `test_economy.py` fails the
build if any source string names one.

## Computed from

| File | Source | Licence | What it gives |
|---|---|---|---|
| `data/lanferdini_2020_table1.xlsx` | Lanferdini et al., *Frontiers in Physiology* 11:979, 2020, doi:10.3389/fphys.2020.00979, PMC7419685, Supplementary Table 1 | CC BY 4.0 | 20 male recreational runners: maximal oxygen uptake, both ventilatory thresholds, running economy at 12 and 16 km/h, energy cost, velocity at maximum uptake, 3000 m time, age, mass. The only open table carrying all three terms of the performance model and a race result for the same people. |
| `data/vickers_2016_master.xlsx` | Vickers & Vertosick, *BMC Sports Science, Medicine and Rehabilitation* 8:26, 2016, doi:10.1186/s13102-016-0052-y, PMC5000509, Additional file 2 | CC BY 4.0 | 2,303 recreational runners with self-reported times at six distances, course difficulty, weekly volume, sex, age, BMI. 430 of them reported both a 5 km and a marathon. |

Both files ship inside `economy-code.zip`, so the page can be rebuilt from the
archive alone. `fetch_data.py` verifies both against a pinned SHA-256 and stops
the build on a mismatch rather than computing on a table nobody checked.

**Re-downloading.** Springer serves its supplement to a script, so the Vickers
file is fetched and hash-checked automatically. Frontiers and PMC both refuse
one: a scripted request for the Lanferdini file is answered with an HTML page.
That file is therefore verified in place, and if it is ever missing the script
stops and prints the landing page to fetch it from by hand. This is the only
manual step in the build.

## Equations

**Kipp S, Kram R, Hoogkamer W (2019).** *Extrapolating metabolic savings in
running: implications for performance predictions.* Frontiers in Physiology
10:79, doi:10.3389/fphys.2019.00079, PMC6378703. **Open access, CC BY.**

Equations 1–6 give gross oxygen uptake against speed for a reference runner of
58 kg and 1.71 m with a 0.45 m² frontal area, each a published cost-of-running
relation plus Pugh's air-resistance term, VO₂ (l/min) = 0.00354 · A · v³. The
coefficients were transcribed from the PMC full text on 2026-09-05 and are held
in two places — `model.py` and `test_economy.py` — so the test compares two
independent copies rather than a value against itself.

The paper also states three results of its own, which the build recomputes
before it will write anything: a 1% saving is worth 1.17% of speed at 2.60 m/s
and 0.65% at 5.72 m/s, and a 4% saving is worth 2.64% at 5.72 m/s. And it
reconciles its equation 2 with the measured 3000 m result below, at 4.79 m/s,
which is why this page can say the two routes to the exchange rate agree
without claiming the agreement as its own finding.

**Pugh LGCE (1970).** *Oxygen intake in track and treadmill running with
observations on the effect of air resistance.* Journal of Physiology 207:823.
The air-resistance term, used as Kipp et al. apply it.

## Looked up, never recomputed

| Source | What it supports |
|---|---|
| Joyner, *J Appl Physiol* 70(2):683–687, 1991, doi:10.1152/jappl.1991.70.2.683 | The form of the decomposition, its worked range, and the flat 10% reduction the model applies for wind and drift. |
| Joyner & Coyle, *J Physiol* 586(1):35–44, 2008, doi:10.1113/jphysiol.2007.143834, PMC2375555 | The ranges the three terms take in trained and elite runners; economy varies 30–40% between individuals. |
| Hoogkamer, Kipp, Spiering & Kram, *MSSE* 48(11):2175–2180, 2016, doi:10.1249/MSS.0000000000001012 | The measured exchange rate: 100 g per shoe cost 1.11% of metabolic rate (95% CI 0.88–1.35) and 0.78% of 3000 m time (0.52–1.04) in 18 trained men. |
| Coyle, *Exerc Sport Sci Rev* 23:25–63, 1995, PMID 7556353 | That maximal uptake explains 31–72% of the variance in the threshold, so the three terms are not independent. |
| Zanini, Folland & Blagrove, *Scand J Med Sci Sports* 35:e70076, 2025, PMC12082016 | Within-race decay in 14 trained runners: economy 4.2% and 5.8% worse at 90 and 120 minutes, peak uptake 3.1% and 7.1% down, threshold speed 14.0 → 13.0 km/h. |
| Hunter & Muniz-Pumares, *Eur J Sport Sci* 25:e70073, 2025, PMC12547624 | The same decay in 18 London finishers, and its correlation with marathon time. |
| Smyth & Muniz-Pumares, *MSSE* 52(12):2637–2645, 2020, PMC7664951 | Share of critical speed held against finish time, over 25,000 marathons. **The underlying training data are held under a research licence and are not public**, so these are the published values and cannot be recomputed here. |
| Jones, *J Physiol* 602(17):4113–4128, 2024, doi:10.1113/JP284205 | The argument that resistance to decay is a fourth determinant the three-term model omits, with individual differences from 0.4% to 32%. |
| Barnes & Kilding, *Sports Medicine – Open* 1:8, 2015, PMC4555089 | Economy norms by ability, and the measurement error a real change has to clear. |
| Van Hooren et al., *Sports Medicine* 54:1269–1316, 2024, PMC11127892 | That running technique explains 4–12% of between-runner economy per variable. |
| Advanced-footwear effect sizes, collected from thirteen papers; individual range from Knopp et al., *Sports Medicine* 53:1255–1271, 2023, PMC10185608 | The one sentence saying the published measurements span 1.10–4.20% and individual response −11.3% to +11.4%. Analysed on its own page, not here. |

## Deliberately not used

- **PhysioNet, Treadmill Maximal Exercise Tests (Málaga), v1.0.1.** 857
  subjects with breath-by-breath oxygen uptake. Its shipped licence is
  CC BY-NC-SA 4.0, the only non-commercial licence in the source list, and the
  ramp protocol does not give steady-state economy in any case. Avoided rather
  than argued about.
- **Strava-derived critical-speed data** (Smyth 2020, 2022). Not public; the
  printed results are quoted instead.
- **Breaking2 per-athlete values** (Jones et al. 2021). The individuals appear
  only as plotted points, and digitising a figure would be inventing data.
- **Any training log of the author's.** One person's numbers are one datum, not
  evidence, and none is used here in any form.
