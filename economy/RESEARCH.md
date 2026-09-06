# Research and feasibility: the mechanics of running economy

Stage 1 of `00 PUBLISH/prompts/NEW_PROJECTS.md` §5. Written 5 September 2026.
Lives in `03 RESEARCH/running/` with two feasibility scripts
(`compound_check.py`, writes `compound_rows.json`; `cohort_check.py`, writes
`cohort_rows.json`) and the downloads in `sources/`. No design decisions are
made here. No training log of the author's was found in the tree, and none
was used.

## 1. Verdict

**The project exists, but the brief's central claim does not survive.** The
decomposition is real, published and multiplicative in form. The
"flywheel" is not: at realistic gains the product exceeds the sum by a
rounding error, and the one strong non-linearity in the literature runs the
other way, so each per cent of economy buys *less* than a per cent of speed
at marathon pace. The honest version is a better page than the brief's,
because it contradicts things a reader believes.

Supportable claim, one sentence: *Marathon speed is the product of the
aerobic ceiling, the fraction of it a runner can hold, and the oxygen cost of
the stride; that product predicts performance far better than any term alone,
but each per cent saved in economy buys only two-thirds to nine-tenths of a
per cent of speed at race pace, the terms are correlated rather than
independent, and none of them holds still over 42 km.*

Not supportable: "improving any one term compounds with the others". Three
3 % gains give 9.37 % under the product and 9.00 % under the sum, 34 seconds
on a three-hour marathon (§4). That is the entire compounding effect, and the
cost–speed curvature removes ten to thirty-six per cent of each gain before
it is felt. The brief's interactive premise ("move two terms and see that the
result is not their sum") would show the reader a difference they cannot see.

What *is* non-additive, and computable from open equations: the curvilinear
cost of speed plus air resistance (Kipp, Kram and Hoogkamer 2019), which
makes the same economy gain worth 1.17 % of speed to a 4:30 marathoner and
0.64 % to a 2:03 one. That pace-dependence is the mechanism a reader has not
seen, and it is the candidate for Stage 2.

## 2. The primary literature

Everything below was confirmed against PubMed or the publisher page by the
research agents; items they could not verify are flagged. Open-access status
matters because Stage 3 must be able to quote an equation from a source a
reader can open.

### 2.1 The decomposition

**Joyner, *J Appl Physiol* 70(2):683–687, 1991, doi:10.1152/jappl.1991.70.2.683,
PMID 2022559. Closed.** The named model. Verbatim form: "marathon running
speed = VO2max (ml·kg⁻¹·min⁻¹) × %VO2max at LT × RE". In implementation
economy is not a divisor but three linear regressions of speed on VO2 with
positive intercepts (high, average, low economy: slopes 0.294, 0.288, 0.278
km/h per ml/kg/min, intercepts 2.65, 1.59, 1.25), all speeds then slowed by
a flat 10 % for wind resistance (7–8 %) and VO2 drift (2–3 %). Inputs 70/77/84
ml/kg/min, 75/80/85 % at LT, 27 combinations in Table 2; best case 1:57:58,
all-average 2:24:10. The sustainable fraction is a fixed input, not a
function of duration. The Discussion notes that exceptional values of the
three terms may be "mutually exclusive" (Pollock's 1500–10 000 m elites had
VO2max ~79 against marathoners' ~74 but were 2 ml/kg/min *less* economical at
19.3 km/h), the earliest statement that the terms trade off.

**di Prampero, *Eur J Appl Physiol* 90:420–429, 2003, doi:10.1007/s00421-003-0926-z,
PMID 12910345. Closed.** The same identity as v = F·VO2max/C with the
sustainable fraction folded into a duration-dependent maximal power
Emax(t). **di Prampero et al., *J Appl Physiol* 74(5):2318–2324, 1993,
PMID 8335562. Closed.** n = 16, energy cost of running 3.72 ± 0.24 J/kg/m
independent of speed on the treadmill. The brief's "di Prampero 1986 J Appl
Physiol" does not exist; the 1986 paper is *Int J Sports Med* 7:55–72 (PMID
3519480), closed, and its v = F·VO2max/C wording could not be verified from
the abstract.

**Joyner and Coyle, *J Physiol* 586(1):35–44, 2008, doi:10.1113/jphysiol.2007.143834,
PMC2375555. Open.** The canonical box diagram (Fig. 1): VO2max and lactate
threshold "interact to determine the performance VO2", which "interacts with
efficiency to establish the speed". Ranges: VO2max 70–85 elite, threshold
75–90 % of it, economy varying 30–40 % between individuals. **Bassett and
Howley, *MSSE* 32(1):70–84, 2000, PMID 10647532. Closed.** Speed at lactate
threshold "integrates all three" and is the best single predictor. **Coyle,
*Exerc Sport Sci Rev* 23:25–63, 1995, PMID 7556353. Closed.** VO2max explains
31–72 % of the variance in threshold VO2: the terms are correlated, not
independent inputs.

**Farrell et al., *Med Sci Sports* 11(4):338–344, 1979, PMID 530025. Closed.**
n = 18; velocity at lactate accumulation r ≥ 0.91 with performance at every
distance, and adding VO2max or economy to it did not raise the multiple
correlation. **Costill, Thomason and Roberts, *Med Sci Sports* 5:248–252,
1973, PMID 4774203.** Exists, closed, no abstract on PubMed, and no numbers
could be retrieved; treat any figure attributed to it as unverified. **Sjödin
and Svedenhag, *Sports Med* 2:83–99, 1985, PMID 3890068. Closed.** Review;
threshold the best predictor; no numbers in the abstract.

**Péronnet and Thibault, *J Appl Physiol* 67(1):453–465, 1989, PMID 2759974.
Closed.** The only place the sustainable fraction is an explicit function of
duration: sustainable aerobic power falls with ln(T/420 s) beyond seven
minutes, fitted to world records with 0.73 % mean error, marathon at 83.5 %
of maximal aerobic power. The coefficient E was not retrieved; the paper
would have to be obtained for Stage 3.

### 2.2 The non-linearity that matters

**Kipp, Kram and Hoogkamer, *Front Physiol* 10:79, 2019,
doi:10.3389/fphys.2019.00079, PMC6378703. Open, CC BY, with a calculator
spreadsheet in the supplement.** Gross VO2 at speed v (m/s) for a 58 kg,
1.71 m runner with 0.45 m² frontal area, verified against the PMC text:

| Eq. | Source curve | VO2 (ml/kg/min) |
|---|---|---|
| 1 | Léger and Mercier 1984, linear | 0.02724 v³ + 11.39 v + 2.209 |
| 2 | Batliner 2018, quadratic (their preferred) | 0.02724 v³ + 1.5355 v² + 1.5354 v + 15.661 |
| 3 | Black 2018 | 0.02724 v³ + 1.9128 v² + 3.2483 v + 25.806 |
| 4 | Kipp 2018 | 0.02724 v³ + 1.7321 v² + 0.538 v + 18.91 |
| 5 | Tam 2012, overground Kenyans | 0.0537 v³ + 9.8158 v + 5.7 |
| 6 | linear fit to Batliner + Pugh | 0.02724 v³ + 12.2 v + 1.11 |

The cubic term is Pugh's air resistance, VO2 (L/min) = 0.00354 · Ap · v³. The
paper's stated results, all reproduced by `compound_check.py` to within 0.01
percentage points: a 1 % economy gain is worth 1.17 % of speed at 2.60 m/s
and 0.65 % at 5.72 m/s; 4 % at 5.72 m/s is worth 2.64 % (1:59:47). One agent
transcribed the Eq. 3 and 4 linear terms with negative signs; the PMC text
has them positive, as in the table.

**Hoogkamer, Kipp, Spiering and Kram, *MSSE* 48(11):2175–2180, 2016,
PMID 27327023. Closed.** n = 18; +100 g per shoe raised metabolic rate 1.11 %
(95 % CI 0.88–1.35) and 3000 m time 0.78 % per 100 g (0.52–1.04). The title
says economy "directly translates"; the measured transfer was 0.70 to 1.
**Hoogkamer, Kram and Arellano, *Sports Med* 47:1739–1750, 2017,
PMID 28255937. Closed.** The 2-hour scenarios (2.7 % economy for 2.5 % speed;
drafting, 100 g lighter shoes). Superseded by Kipp 2019 on the extrapolation.

**Batliner et al., *Sports Med Int Open* 2:E1, 2018,
doi:10.1055/s-0043-122068, PMC6225957. Open.** n = 20 (10 average, 10
sub-elite); per-subject linear and quadratic VO2–speed coefficients, VO2max
and 10 km best are tabulated for all twenty. This is the individual-level
source behind Eq. 2 and the only open per-runner cost curve.

### 2.3 What the three-term model leaves out

**Jones, *J Physiol* 602(17):4113–4128, 2024, doi:10.1113/JP284205,
PMID 37606604. Open, CC BY.** Re-running Joyner with Breaking2 values
(80 ml/kg/min, 88 %, 192 ml/kg/km) predicts 1:55:05, which "confirms that the
Joyner model lacks an important variable". Critical power falls 8–11 % and W′
17–22 % after two hours of heavy cycling, with an individual range of 0.4 to
32 %; field marathoners held ~92 % of threshold pace to ~70 % of the distance
then fell to ~89 %. Fig. 6 adds resilience as a fourth determinant, as a box
diagram with no equation.

In-race deterioration, all confirmed: **Brueckner et al., *Eur J Appl
Physiol* 62:385–389, 1991, PMID 1893899** (closed; n = 10; cost rises 0.20–0.31
ml/kg/km per km after 32–42 km, about +5–8 % over a marathon). **Petersen et
al., 2007, PMID 17661071** (closed; n = 8; energy cost at marathon pace +4 %).
**Zanini, Folland and Blagrove, *Scand J Med Sci Sports* 35:e70076, 2025,
PMC12082016** (open; n = 14; economy +4.2 % at 90 min and +5.8 % at 120 min,
VO2peak −3.1 % and −7.1 %, threshold speed 14.0 → 13.0 km/h; Table 2 and Fig. 5
reusable). **Hunter and Muniz-Pumares, *Eur J Sport Sci* 25:e70073, 2025,
PMC12547624** (open; n = 18; after 90 min at threshold, VO2max 56.7 → 53.4 and
threshold speed 12.8 → 12.1 km/h, economy unchanged; the drop correlates
r = 0.68 with marathon time).

**Jones et al., *J Appl Physiol* 130(2):369–379, 2021,
doi:10.1152/japplphysiol.00647.2020, PMID 33151776.** The Breaking2 cohort;
hybrid CC BY at the publisher, whose site refused every fetch; an accepted
manuscript is on Exeter's repository (figshare 29774942). n = 16 world-class
men, VO2peak 71.0 ± 5.7 (range 62–84), threshold 83 ± 5 % and turn-point
92 ± 3 % of VO2peak, O2 cost 189 ± 14 ml/kg/km on the treadmill, 191 ± 19
overground at 21.1 km/h for the seven who reached steady state, at 94 ± 3 %
of VO2peak. **Per-athlete values exist only as plotted points (Fig. 5); there
is no table and no supplement.**

### 2.4 Critical speed, and the one large public-data result

**Jones and Vanhatalo, *Sports Med* 47(S1):65–78, 2017, PMC5371646. Open.**
**Jones et al., *Physiol Rep* 7(10):e14098, 2019, PMC6533178. Open.** The
power–duration hyperbola fits 2–20 minute events; the marathon lies below the
curve, so critical speed alone does not predict it. **Smyth and
Muniz-Pumares, *MSSE* 52(12):2637–2645, 2020, PMC7664951. Open.** Critical
speed from Strava training data for over 25 000 recreational marathoners:
r = 0.695 with marathon time; marathon run at 84.8 % of critical speed
overall, 93.0 % for 150-minute finishers falling to 78.9 % at 360 minutes.
**Smyth et al., *Sports Med* 52:2283–2295, 2022, PMC9388405. Open.**
n = 82 303; heart-rate decoupling as a durability index cuts prediction error
from 6.45 % to 5.16 %. Both datasets are under a Strava research licence and
are not public; only the printed results can be used.

### 2.5 Economy itself: measurement, norms, determinants

**Barnes and Kilding, *Sports Med Open* 1:8, 2015, PMC4555089. Open.**
Definitions, reliability (typical error 1.3–5 %, smallest worthwhile change
2.2–2.6 %), and Table 1 norms by ability and speed. At 16 km/h the band runs
roughly 180 ml/kg/km (elite) → 190 (highly trained) → 193–198 (moderately
trained) → 200–210 (recreational). The agent's extraction of the VO2max
column was garbled; re-read the PMC table before use. Economy "can vary by as
much as 30 % among trained runners with similar VO2max".

**Fletcher, Esau and MacIntosh, *J Appl Physiol* 107:1918–1922, 2009,
PMID 19833811** (closed) and **Shaw, Ingham and Folland, *MSSE*
46(10):1968–1973, 2014, PMID 24561819** (closed; n = 172): oxygen cost per km
is flat with speed while energy cost rises, because the respiratory exchange
ratio rises. The unit matters; the page should use energy cost or say why
not.

**Van Hooren et al., *Sports Med* 54:1269–1316, 2024, PMC11127892. Open.**
Meta-analysis of biomechanics and economy, 51 studies, n = 1 115. Pooled r:
contact time −0.02, stride length 0.12, footstrike g −0.02 (all trivial);
cadence −0.20; vertical displacement +0.35; vertical stiffness −0.31; leg
stiffness −0.28. "Running biomechanics can explain 4–12 % of the
between-individual variation in RE when considered in isolation."
**Folland et al., *MSSE* 49(7):1412–1423, 2017, PMC5473370. Open.** n = 97;
the best three-variable kinematic regression explains 39 % of energy-cost
variance. **Liu et al., *Front Physiol* 13:1059221, 2022, PMC9742541. Open.**
Leg stiffness pooled r −0.57, a larger figure than Van Hooren's; cite both.

**Kipp, Grabowski and Kram, *J Exp Biol* 221:jeb184218, 2018, PMID 30065039.**
Closed. The mechanistic model: 98 % of the rise in cost across 8–18 km/h is
explained by rate of force generation and active muscle volume, within
subjects. **Arellano and Kram, *Integr Comp Biol* 54:1084–1098, 2014,
PMC4296200. Open.** Task partition of net cost: weight support and propulsion
~80 %, leg swing ≤ 7 %, balance 2 %, arm swing −3 %; naive shares sum to
131 %, so the partition is additive with interactions, not a product.

**O'Sullivan et al., *J Sports Sci* 37:1521–1533, 2019, PMID 30810467.**
Closed. Across twelve training interventions, the change in economy did not
correlate with the change in performance (r = 0.46, not significant). The
acute footwear-mass link transfers; the training link is noisy.

### 2.6 Modifiers of economy with effect sizes

Footwear and mass: **Franz, Wierzbinski and Kram, *MSSE* 44(8):1519–1525,
2012, PMID 22367745** (closed; ~1 % VO2 per 100 g per shoe, n = 12).
**Hoogkamer et al., *Sports Med* 48:1009–1019, 2018, PMC5856879** (open;
n = 18; −4.16 % and −4.01 % versus two racing flats, mass-matched, every
subject improved, range −1.59 to −6.26 %; Table 1 reusable). **Barnes and
Kilding, *Sports Med* 49:331–342, 2019, PMID 30374945** (closed; n = 24;
−2.6 % versus spikes, −4.2 % versus a flat). **Joubert, Dominy and Burns,
*IJSPP* 18:164–170, 2023, PMID 36626911** (closed; −1.4 % at 12 km/h, not
significant at 10 km/h). Meta-analyses: **Xiao et al., *Int J Sports Med*
2025, PMID 40527489** (17 crossover trials, n = 281, g −0.44); **Kobayashi et
al., *Front Sports Act Living* 7:1710224, 2026, PMC12827780** (mean
difference −5.34 ml/kg/km, about −2.75 %); **Stephen et al., *J Sport Health
Sci* 14:101069, 2025, PMC12305619** (48 studies, n = 878; neither plate
stiffness nor energy return alone significant). **Knopp et al., *Sports Med*
53:1255–1271, 2023, PMC10185608** (open; seven world-class Kenyans ranged from
−11.4 % benefit to +11.3 % detriment in the same shoes).

Strength training: **Llanos-Lagos et al., *Sports Med* 54:895–932, 2024,
PMC11052887** (open; 31 studies, n = 652; high-load ES −0.27, CI −0.52 to
−0.02; plyometrics not significant overall). **Denadai et al., *Sports Med*
47:545–554, 2017, PMID 27497600** (closed; −3.9 ± 1.2 % economy). **Blagrove,
Howatson and Hayes, *Sports Med* 48:1117–1149, 2018, PMC5889786** (open;
n = 469; per-study 2–8 % in fourteen papers, six null; Tables 2–4 reusable).
**Eihara et al., *Sports Med Open* 8:138, 2022, PMC9653533** (open; heavy
resistance g −0.32, plyometric −0.13 not significant). **Ramos-Campo et al.,
*JSCR* 39:492–506, 2025, PMID 40153564** (closed; the only umbrella review;
VO2max unchanged in every meta-analysis).

Altitude: **Saunders et al., *J Appl Physiol* 96:931–937, 2004,
PMID 14607850** (closed; −3.3 % after 20 days live-high train-low, n = 22
elite) against **Schwalm et al., *JSCR* 2026, PMID 42302183** (closed; pooled
randomised trials SMD −0.20, not significant). Report as unresolved.

Long-term training: **Jones, *Br J Sports Med* 32:39–43, 1998, PMC1756052.
Open.** Paula Radcliffe 1991–95: VO2max 73 → 66, economy at 16 km/h 53 → 48
ml/kg/min (about −9 %), threshold 15.0 → 18.0 km/h. **Jones, *Int J Sports Sci
Coach* 1(2):101–116, 2006, doi:10.1260/174795406777641258.** Not on PubMed,
closed, full text not obtained; the widely quoted −15 % economy over eleven
years with VO2max flat is **unverified** and comes only through Barnes and
Kilding 2015, Moore 2016 and Hoogkamer 2018. Obtain the PDF before charting
it.

Null or negative modifiers, all meta-analytic: stretching no acute effect
(Warneke 2025, PMC12122984); imposed forefoot strike worsens economy
(Anderson 2020, PMID 31823338); orthoses worsen it, SMD +0.42 (Crago 2019,
PMID 31423908); age does not change the economy slope while VO2max falls
30 % (Quinn 2011, PMID 21982960, n = 51).

**Copyright.** *Advanced Marathoning* was not consulted and nothing above
derives from it. Daniels and Gilbert's VDOT tables are self-published and
not online; the Riegel exponent is sourced through Vickers and Vertosick
2016 (§3) rather than Riegel 1981, which has no free copy.

## 3. The primary data

Downloaded files are in `sources/`. The finding to state first: **no
per-athlete elite table is open.** Breaking2 individuals are plotted points;
Radcliffe's longitudinal table is paywalled and unverified; the Strava
critical-speed data are under a research licence. Elite numbers on the page
would be group means and published equations, labelled as such.

| Source | Licence | n, columns | Path | Carries |
|---|---|---|---|---|
| Kipp 2019 equations + supplement spreadsheet | CC BY | six cost curves, air term | (coefficients above; spreadsheet not downloaded) | every "x % economy → y % speed" figure |
| Batliner 2018 per-subject table | CC BY, in print | 20 runners: linear and quadratic coefficients, VO2max, 10 km best | (transcribe from PMC6225957) | spread of individual cost curves |
| Lanferdini et al. 2020, *Front Physiol* 11:979, Supplementary Table 1 | CC BY | 20 recreational men: VO2max, VT1, VT2, economy at 12 and 16 km/h, energy cost, vVO2max, 3000 m time, mass, age | `frontiers_2020_fphys00979_supp/Table_1.xlsx`, 17 kB | the only open file with all three terms and a race time per runner |
| Vickers and Vertosick 2016, *BMC Sports Sci Med Rehabil* 8:26, Additional file 2 | CC BY 4.0 | 2 303 recreational runners: self-reported 5 km, 10 km, 5 mi, 10 mi, half and marathon times, course difficulty, weekly miles, sex, age, BMI | `vickers_vertosick_2016_BMC_additional_file2_master_data.xlsx`, 380 kB | speed–distance decay, empirical sustainable-fraction proxy, Riegel exponent |
| Tam et al. 2012 (author copy, Brescia IRIS hdl 11379/248703) | publisher-closed, author copy open | group means n = 10 + 9; Table 5 individual values for three named elites | not downloaded | a worked elite instance of the Joyner model, F_mar 0.825/0.836 |
| PhysioNet "Treadmill Maximal Exercise Tests" v1.0.1 (Málaga) | shipped LICENSE.txt is **CC BY-NC-SA 4.0** | 857 subjects, 992 ramp tests; breath-by-breath VO2, speed, HR | `physionet_treadmill_malaga_v1.0.1/`, 23 MB | a population distribution of VO2max and VO2–speed slopes; no steady state, no race times, discipline unrecorded |
| Smyth 2021, *PLoS One*, "hitting the wall", S1 datasets | CC BY 4.0 | 77 CSVs; 1.93 M runners with sex, age, wall flag; 475 k wall events with onset km and slowdown | `smyth_2021_plosone_hit_the_wall_S1_Datasets.zip`, 37 MB | prevalence and size of late-race collapse; not split profiles |
| Kaggle marathon results: Chicago 1996–2023 (MIT), NYC 1970– (MIT), all-US 2023 (CC BY 4.0), Berlin 1974–2019 (CC0) | as listed | 0.4–1.5 M finishers each, finish times only | `kaggle_*.zip`, 2–25 MB | finish-time distributions; no splits |
| Age-grading factors (Alan Jones tables, CC0) | CC0 | ages 5–100 × road distances, 2020 and 2025 | `AlanJones_AgeGrade_*.xlsx` | age adjustment if ever needed |
| OSF cu9y2 energy-cost set; Zenodo 19394056, 7872393 | CC BY / unassigned | team-sport athletes; 16 Garmin runners; walk–run transition | small | weak for this model |

Not saved: the Boston 2015–17 split file on Kaggle (licence "Unknown");
Zenodo race archives for Berlin 1999–2025, Chicago 2024, London 2018–23 (open
but finish times only). Not obtainable: Strava critical-speed data (Smyth
2020, 2022), Polar Flow data (Emig and Peltonen 2020), Breaking2 per-athlete
values.

**Licence caution.** The PhysioNet set's non-commercial share-alike licence
is the only one in the table that could conflict with the site; Lanferdini
(n = 20, CC BY) is the fallback for a complete cohort.

## 4. Feasibility check: does it compound?

`compound_check.py`, from the Joyner identity and Kipp Eq. 2, no data
needed.

**Product versus sum.** With economy as a divisor, three equal gains p give
(1+p)²/(1−p) − 1 against 3p:

| p per term | product | sum | gap | 3:00 marathon, product | sum | gap |
|---|---|---|---|---|---|---|
| 1 % | 3.04 % | 3.0 % | 0.04 pp | 2:54:41 | 2:54:45 | 4 s |
| 2 % | 6.16 % | 6.0 % | 0.16 pp | 2:49:33 | 2:49:49 | 16 s |
| 3 % | 9.37 % | 9.0 % | 0.37 pp | 2:44:35 | 2:45:08 | 34 s |
| 5 % | 16.05 % | 15.0 % | 1.05 pp | 2:35:06 | 2:36:31 | 85 s |

**Cost–speed curvature, Kipp Eq. 2.** Speed gain for a metabolic saving,
solving (1 − x)·VO2(v′) = VO2(v):

| v m/s | marathon | drag share | elasticity | 1 % | 3 % | 4 % | 5 % |
|---|---|---|---|---|---|---|---|
| 2.60 | 4:30 | 1.6 % | 1.17 | 1.17 % | 3.55 % | 4.75 % | 5.97 % |
| 3.50 | 3:21 | 2.8 % | 0.88 | 0.89 % | 2.69 % | 3.61 % | 4.54 % |
| 4.00 | 2:56 | 3.6 % | 0.80 | 0.80 % | 2.43 % | 3.26 % | 4.10 % |
| 4.50 | 2:36 | 4.4 % | 0.73 | 0.74 % | 2.24 % | 3.01 % | 3.79 % |
| 5.50 | 2:08 | 6.0 % | 0.65 | 0.66 % | 2.00 % | 2.68 % | 3.38 % |
| 5.72 | 2:03 | 6.4 % | 0.64 | 0.64 % | 1.96 % | 2.63 % | 3.31 % |

The paper's three stated numbers (1.17 %, 0.65 %, 2.64 %) reproduce to
0.01 pp. Below about 3 m/s the gain slightly exceeds the saving; at
world-record pace it is under two-thirds. Joyner's own economy regressions,
with their positive intercepts, give elasticities of 0.85–0.94 by the same
logic. So the compounding bonus (+0.4 pp at 3 % per term) is an order of
magnitude smaller than the curvature penalty (−0.6 to −1.1 pp on a single
3 % term at 2:36–2:03 paces), and the terms are correlated besides.

**The duration feedback.** A faster runner finishes sooner and can hold a
higher fraction. It is real and small: Smyth 2020 gives 93 % of critical speed
at 150 min falling to 79 % at 360 min; Vickers and Vertosick's 430 runners
with both a 5 km and a marathon give a marathon-to-5 km speed ratio with
median 0.819 (IQR 0.776–0.853), rising from 0.805 in the slowest third to
0.828 in the fastest (`cohort_check.py`). Their Riegel exponent is 1.09
(IQR 1.075–1.119) against the 1.06–1.08 Riegel quoted for recreational men.

**Does the product predict performance?** In the one open cohort with all
three terms (Lanferdini 2020, n = 20, 3000 m times 560–718 s), the
correlation with 3000 m speed is +0.65 for VO2max alone, −0.16 for economy
alone, +0.10 for the VT2 fraction, and **+0.87 for VO2max divided by cost**.
The product beats every term, which is the decomposition's real content.
The fraction term contributes nothing at 3000 m, as expected for a ten-minute
race; 3000 m speed was 79–95 % of VO2max/cost, mean 88 %. No open cohort
lets the same check be run at marathon distance.

## 5. What a reader already believes, and what this adds

Already believed: VO2max is what makes elites elite; the marathon is "an
aerobic event"; good form is what economy means; a 4 % shoe is 4 % faster;
economy is a fixed trait; stretching, forefoot striking and orthotics help.

What the literature says instead, each with a source above:

- Among elites VO2max is flat and economy varies ~30 %; East African runners
  beat matched Europeans on economy by 5–12 % with equal or lower VO2max
  (Weston 2000, Lucia 2006, Santos-Concejero 2015), yet the best-controlled
  overground comparison found no difference (Tam 2012) and within a
  homogeneous Kenyan group economy did not predict performance (Mooses 2015).
- Technique explains 4–12 % of between-runner economy per variable and 39 %
  combined; contact time, stride length and footstrike have r ≈ 0.
- A 4 % economy gain is 2.6 % of speed at 2:03 pace and about 1 % at 10–12
  km/h; individual responses to the same shoe span −11 % to +11 %.
- Economy improves for years (Radcliffe −9 % in four, verified) and by 2–5 %
  in weeks of heavy strength training, with VO2max unchanged; but across
  training studies the change in economy does not predict the change in
  performance.
- The three terms are not fixed inputs: economy worsens 4–6 % and VO2peak
  falls 3–7 % within two hours of hard running, with an individual range from
  nothing to a third.
- Oxygen cost per km is flat with speed; energy cost is not.

That list is not "nothing"; each item contradicts the prior belief. The
compounding item the brief wanted is the one that does not.

## 6. Traps found

- **The pace calculator.** Everything in §4 could be reduced to one; the
  brief warns against it and the finding sharpens the warning, because the
  arithmetic the calculator would show (the sum) is within a rounding error
  of the truth.
- **"Directly translates."** Hoogkamer 2016's title says 1:1; its data say
  0.70:1. Quote the number, not the title.
- **The nested onion.** Economy does not decompose multiplicatively. Its
  determinants are an additive task partition with interactions, a set of
  correlates with r of 0.2–0.35, and a list of intervention deltas. Drawing
  it as nested multiplication would invent structure.
- **Units.** Kipp Eq. 2 is for a 58 kg runner and gives gross VO2; mixing it
  with net or energy-cost figures from other papers shifts every number.
- **Unverified elite numbers.** Radcliffe's −15 %, anything from Costill 1973,
  and any per-athlete Breaking2 value are secondhand. They do not go on a
  page with a `source=` field until the primary is in hand.
- **Correlated inputs.** A slider that moves one term with the others fixed
  is a counterfactual the literature says does not occur in trained
  runners; the page must say so.
- **The Strava results.** The only large-N marathon physiology is on data
  nobody can download; only its printed numbers can be used.

## 7. Kill criteria

- *Data does not exist.* Partly true: elite per-athlete data do not exist
  openly. The equations, the meta-analyses and two small open cohorts do,
  and the claim in §1 needs only those. Not killed.
- *Only a much weaker claim, and it is not interesting.* The claim is weaker
  than the brief's and it is more interesting (§5). Not killed.
- *The reader already knows it.* No; six of the seven items in §5 contradict
  the prior. Not killed.
- *Only copyrighted sources.* No; Kipp 2019, Jones 2024, Joyner and Coyle
  2008, Van Hooren 2024, Llanos-Lagos 2024, Hoogkamer 2018 and Barnes and
  Kilding 2015 are open, and the book was not needed. Not killed.

The project survives Stage 1 with its central claim replaced. Stage 2 should
start from the pace-dependence of the economy payoff, not from compounding,
and decide whether that mechanism needs to be moved to be believed.

## 8. Reproducing the check

`python compound_check.py` needs nothing but Python 3 and writes
`compound_rows.json`. `python cohort_check.py` needs `openpyxl` and the two
files in `sources/` named in §3, and writes `cohort_rows.json`. The Kipp
coefficients are transcribed from PMC6378703 and checked against the paper's
three stated results inside the script. The Lanferdini sheet has two header
rows and computed columns as Excel formulas; the script reads the measured
columns only. A Stage 3 generator would redo both inside the project folder.
