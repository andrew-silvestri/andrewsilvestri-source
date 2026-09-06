# Data sources

There is no download step in this project. No public dataset reports footwear
effect sizes, so every number was read out of the paper that published it and
declared in `data/studies.py` with its sample, its setting, a note and a DOI.
That file is the data.

This page therefore cannot be rebuilt from a fetch; it can be rebuilt from the
table, and the table can be checked against the papers.

## The papers, and what each supplies

| Source | Supplies | Access |
|---|---|---|
| Hoogkamer, Kipp, Frank, Farina, Luo & Kram 2018, *Sports Med* 48(4):1009-1019 (doi 10.1007/s40279-017-0811-2) | The two prototype comparisons — the origin of "4%". A correction was published at 48(6):1521-1522. | Open access in PMC |
| Hunter, McLeod, Valentine, Low, Ward & Hager 2019, *J Sports Sci* 37(20):2367-2373 (doi 10.1080/02640414.2019.1633837) | The retail shoe against the same two controls, by an independent group | Abstract carries both figures |
| Barnes & Kilding 2019, *Sports Med* 49(2):331-342 (doi 10.1007/s40279-018-1012-3) | Three comparisons with standard deviations, two per-athlete ranges, and the only sample with women in it besides one | Abstract carries the means, SDs and ranges |
| Whiting, Hoogkamer & Kram 2021, *J Sport Health Sci* 11(3):303-308 (doi 10.1016/j.jshs.2021.10.004) | Level, uphill and downhill | Open access in PMC |
| Joubert, Oehlert, Jones & Burns 2024, *Int J Sports Physiol Perform* 19(7):705-711 (doi 10.1123/ijspp.2023-0372) | Two AFT track spikes against a traditional spike | Abstract carries both arms |
| Joubert & Sanders 2026, *J Strength Cond Res*, ahead of print (doi 10.1519/JSC.0000000000005553) | The only comparison measured outdoors | Abstract |
| Hoogkamer, Kipp, Spiering & Kram 2016, *Med Sci Sports Exerc* 48(11):2175-2180 (doi 10.1249/MSS.0000000000001012) | The per-100 g mass rule, the only confidence intervals in the table, and both halves of the transfer coefficient | Abstract carries both figures with CIs |
| Rodrigo-Carranza, González-Mohíno, Santos-Concejero & González-Ravé 2020, *Front Physiol* 11:573660 (doi 10.3389/fphys.2020.573660) | The added-mass trial that contradicts the rule by six to nine times | Open access |
| Knopp, Muñiz-Pardos, Wackerhage, Schönfelder, Guppy, Pitsiladis & Ruiz 2023, *Sports Med* 53(6):1255-1271 (doi 10.1007/s40279-023-01816-1) | The two widest published individual ranges | Open access in PMC |
| Guinness, Bhattacharya, Chen, Chen & Loh 2020, arXiv:2002.06105 | The observed marathon-time intervals for men and for women | Preprint, open |

Meta-analyses (cited in prose, not rows in the table, because a standardised
mean difference does not share an axis with a percentage): Xiao et al. 2025
(doi 10.1055/a-2637-7283), Stephen et al. 2025 (doi 10.1016/j.jshs.2025.101069),
Rodrigo-Carranza et al. 2022 (doi 10.1080/17461391.2021.1955014), Ortega et al.
2021 (doi 10.1007/s40279-020-01406-5), Fuller et al. 2015
(doi 10.1007/s40279-014-0283-6).

Not a paper: Frederick, Daniels & Hayes 1984, in *Current Topics in Sports
Medicine*, Urban & Schwarzenberg, 616-625 — the origin of the ~1% per 100 g
rule. A book chapter, not indexed in PubMed, cited as the antecedent that
Hoogkamer 2016 measured directly.

## What is absent, and why

**There is no shoe specification database.** No free, comprehensive source
gives shoe mass, stack height, foam type or plate geometry by model.

World Athletics publishes an approved-shoe list (checked in Stage 1: the
20 January 2024 PDF, about 600 rows). It carries brand, model, six
event-eligibility flags and development-shoe dates, and **no specifications at
all**. It answers "may this shoe be worn in this event", not "what is this
shoe". The regulations themselves — Book C, C2.1A, approved 2 December 2025 —
are a free PDF and give the stack-height and single-plate rules.

The consequence is on the page: this project compares studies, not shoes. Any
design that needs per-model specifications cannot be built from public data.

**Guinness et al.'s underlying data is public but unlicensed.** The marathon
results and hand-curated shoe labels are on GitHub at `joeguinness/vaporfly`
with no licence stated, so this project cites the published estimates rather
than redistributing the CSVs.

**Most of these papers are paywalled in their published form**, but every
number used here appears in the abstract, which is free. That is why the table
records effect sizes, samples and settings rather than anything requiring the
full text.

## What the table is not

It was assembled by one literature search rather than under a registered
protocol, so it is a collection and not a systematic review, and it applies no
quality weighting. The inclusion rule for the laboratory comparisons is stated
in `data/studies.py` and on the page: every controlled comparison of an
advanced-footwear shoe against a control shoe reporting running economy or
metabolic cost as a percentage. Where a study reported two arms, both are in.
