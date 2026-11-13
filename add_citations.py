"""
Attach citations to the project pages.

Every claim on this site that came from somewhere should say where. This walks
each project page, drops a superscript marker after the specific sentence a
source supports, and appends a Sources section listing them.

The markers are anchored to phrases rather than to positions, so re-running
after an edit does not scatter them: if the phrase moved, the marker moves with
it; if the phrase is gone, the script says so instead of silently dropping the
reference. That last part matters - a citation list that quietly loses entries
is worse than none, because it still looks complete.

Run:
    python3 add_citations.py            # report what it would do
    python3 add_citations.py --apply

This script was disarmed for one day. On 2026-09-05 it was added to
tests/test_generators.py - it had never been checked, in a repository that had
spent a day on exactly this class of bug - and the check found it could not
reproduce four of the pages it claimed to own. All four are now resolved:

  * strip() was not idempotent. Fixed the same day; see strip()'s own note.
  * storage.html cited a reference PAGES did not have, at "annualised capital
    cost", so a run dropped the marker and renumbered. The entry is now here.
    Its shipped numbering also predated this script's own rule - references
    run in order of first appearance - and a run corrects it.
  * longevity.html's "ocean quahog" anchor matched inside a marginalia aside
    before it matched the prose, so a run put a superscript in the margin
    list. Asides are no longer eligible (see build()), and that page has since
    been removed from PAGES for a better reason: its own generator owns it.
  * heat.html had been hand-corrected to eGRID2023 with the 733.862 lb/MWh
    detail and CO&#8322; entities, and no PAGES entry could reproduce it
    because build() ran html.escape over "what". The entry is updated and
    "what" is now emitted as authored, exactly as "src" always was. Both are
    HTML fragments written in the table below; nothing in PAGES relies on
    being escaped, which was checked before the change.
  * economy.html carried two <h2>Sources</h2>. Fixed by that project.

food.html and climate-cost.html round-trip cleanly and are the model.

A page can also opt out of PAGES entirely and own its reference list, which is
what shoes/update_page.py does: it builds the list from its project's data and
calls build() with it, so the citation text lives once, beside the numbers.
"""

import argparse
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

# For each page: the reference list, and for each reference the phrase in the
# prose it supports. The phrase must be unique on the page.
PAGES = {
    # R4 (2026-10-23): heat.html runs on EIA's monthly Texas prices and ERCOT's
    # hourly prices. Every source opened by R4 that day (SOURCES Part 7);
    # heat/update_page.py applies this entry itself. D-19's corrections (the
    # Zuberi title, ATB for the rate only) carry over.
    "heat.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("LBNL's study of boiler electrification",
         'Zuberi, Hasanbeigi &amp; Morrow, <i>Electrification of Boilers in '
         'U.S. Manufacturing</i>, Lawrence Berkeley National Laboratory, '
         'LBNL-2001436, November 2021.',
         "Electric boilers 95-99% efficient, existing fossil boilers 70-80%; "
         "electric capital nearly 40% below gas; fixed operations 1% of "
         "investment; the twenty-year life."),
        ("On EIA's Texas industrial prices",
         'U.S. Energy Information Administration, API v2: electricity retail '
         'sales (Texas, industrial, monthly price); natural gas Texas '
         'industrial price N3035TX3; Texas heat content of deliveries to '
         'consumers; percent of industrial deliveries included in prices, '
         'N3035TX4.',
         "Every monthly price and the gas conversion; EIA's coverage of "
         "industrial gas deliveries."),
        ("ERCOT's real-time market",
         'ERCOT, <i>Historical RTM Load Zone and Hub Prices</i> (NP6-785-ER), '
         'Market Information System report 13061, 2011 to date.',
         "The hourly hub-average price the second boiler buys at."),
        ("ERCOT's own charges",
         'Oncor Electric Delivery, <i>Tariff for Retail Delivery Service</i>, '
         's.6.1.1.1.7 Transmission Service (2026); CenterPoint Energy Houston '
         'Electric, <i>Tariff for Retail Delivery Service</i>, s.6.1.1.1.5; ERCOT '
         'Market Notice M-A111125-01 (administrative fee); Potomac Economics, '
         '<i>2025 State of the Market Report for the ERCOT Electricity Markets</i>.',
         "The low, central and high charges on top of the wholesale price: no "
         "per-kWh delivery charge at transmission voltage, demand charges set "
         "in four summer intervals, the $0.61/MWh fee, ancillary services and "
         "uplift per MWh of load."),
        ("EPA's eGRID",
         'U.S. EPA, <i>eGRID2023</i> (revised 12 June 2025), ERCT subregion '
         'output emission rates; and EPA, <i>GHG Emission Factors Hub</i> 2025, '
         'stationary combustion.',
         "ERCOT's average rate, 733.862 lb CO&#8322;/MWh, and the natural gas "
         "factor, 53.06 kg CO&#8322;/MMBtu. CO&#8322; rather than CO&#8322;e, "
         "because the gas factor is carbon dioxide only."),
        ("EPA's AVERT",
         'U.S. EPA, <i>AVERT</i> v4.3, avoided emission rates, 2023 data, Texas '
         'region (calculated April 2024).',
         "The marginal rate: 1,293.7 lb CO&#8322;/MWh for a load that is the "
         "same in every hour, adjusted for transmission and distribution "
         "losses."),
        ("capital recovered over",
         'NREL, <i>Annual Technology Baseline</i> 2024, financial assumptions.',
         # ATB uses a 30-year recovery period and a fixed charge rate; only
         # the 8% matches the model (D-19 item 5).
         "The eight percent discount rate."),
    ],
    # economy.html: RETIRED 2026-09-09 with the Running group.
    # Commented, not deleted - these tuples are the citation data and
    # republishing is uncommenting. Same as food and neuron above.
    # "economy.html": [
    #     ("Anchor phrase", "Source", "What it supports"),
    #     ("cost-of-running curve",
    #      'Kipp, Kram &amp; Hoogkamer, <i>Frontiers in Physiology</i> 10:79, 2019, '
    #      'doi:10.3389/fphys.2019.00079.',
    #      "The six published cost-of-running curves with Pugh's air-resistance "
    #      "term, the equations this page computes with, and the reconciliation "
    #      "with the measured 3000 m result; open access, CC BY."),
    #     ("3000 meter race times",
    #      'Hoogkamer, Kipp, Spiering &amp; Kram, <i>Medicine &amp; Science in Sports '
    #      '&amp; Exercise</i> 48(11):2175-2180, 2016, '
    #      'doi:10.1249/MSS.0000000000001012.',
    #      "The measured exchange rate: 100 g per shoe cost 1.11% of metabolic "
    #      "rate and 0.78% of 3000 m time in 18 trained men."),
    #     ("decomposes into three measured quantities",
    #      'Joyner, <i>Journal of Applied Physiology</i> 70(2):683-687, 1991, '
    #      'doi:10.1152/jappl.1991.70.2.683; and Joyner &amp; Coyle, <i>Journal of '
    #      'Physiology</i> 586(1):35-44, 2008, doi:10.1113/jphysiol.2007.143834.',
    #      "The form of the decomposition and the ranges its three terms take in "
    #      "trained and elite runners."),
    #     ("carrying all three terms",
    #      'Lanferdini <i>et al.</i>, <i>Frontiers in Physiology</i> 11:979, 2020, '
    #      'doi:10.3389/fphys.2020.00979, Supplementary Table 1.',
    #      "Twenty recreational men with maximal oxygen uptake, both ventilatory "
    #      "thresholds, running economy and a 3000 m time; CC BY 4.0."),
    #     ("two hours of running raised",
    #      'Zanini, Folland &amp; Blagrove, <i>Scandinavian Journal of Medicine &amp; '
    #      'Science in Sports</i> 35:e70076, 2025.',
    #      "The within-race decay of all three terms over 90 and 120 minutes in "
    #      "14 trained runners."),
    #     ("critical speed a runner holds",
    #      'Smyth &amp; Muniz-Pumares, <i>Medicine &amp; Science in Sports &amp; '
    #      'Exercise</i> 52(12):2637-2645, 2020.',
    #      "The share of critical speed held against finish time, over 25,000 "
    #      "marathons; the underlying training data are held under a research "
    #      "license and are not public."),
    #     ("fourth determinant",
    #      'Jones, <i>Journal of Physiology</i> 602(17):4113-4128, 2024, '
    #      'doi:10.1113/JP284205.',
    #      "The argument that resistance to within-race decay is an independent "
    #      "determinant the three-term model omits."),
    #     ("advanced footwear disagree",
    #      'Effect sizes collected from thirteen papers; the individual range is '
    #      'Knopp <i>et al.</i>, <i>Sports Medicine</i> 53:1255-1271, 2023.',
    #      "The spread of published advanced-footwear effect sizes, quoted here "
    #      "and analyzed on its own page."),
    #     ("variance in the threshold",
    #      'Coyle, <i>Exercise and Sport Sciences Reviews</i> 23:25-63, 1995, '
    #      'PMID 7556353.',
    #      "That maximal oxygen uptake explains 31-72% of the variance in the "
    #      "lactate threshold, so the three terms are not independent."),
    #     ("2,303 recreational runners",
    #      'Vickers &amp; Vertosick, <i>BMC Sports Science, Medicine and '
    #      'Rehabilitation</i> 8:26, 2016, doi:10.1186/s13102-016-0052-y.',
    #      "Self-reported race times at six distances for 2,303 runners, used "
    #      "for the fall in sustainable pace between 5 km and the marathon; "
    #      "CC BY 4.0."),
    # ],
    # neuron.html: UNPUBLISHED 2026-09-09 (unpublished/RETIRED.md).
    # Commented, not deleted: these tuples ARE the citation data for that
    # page - anchor phrase, source, what it supports - and republishing is
    # uncommenting rather than rebuilding them from the article. Left live,
    # the script reported 'does not exist' as a problem on every run, which
    # teaches a reader to skip the problems block.
    # "neuron.html": [
    #     ("Anchor phrase", "Source", "What it supports"),
    #     ("public archive of reconstructed neurons",
    #      'Ascoli, Donohue &amp; Halavi, <i>The Journal of Neuroscience</i> '
    #      '27(35):9247-9251, 2007, doi:10.1523/JNEUROSCI.2055-07.2007; Tecuatl, '
    #      'Ljungquist &amp; Ascoli, <i>FASEB BioAdvances</i> 6(7):207-221, 2024, '
    #      'doi:10.1096/fba.2024-00048.',
    #      "NeuroMorpho.Org, the archive every count on this page is computed from; "
    #      "CC BY 4.0."),
    #     ("a figure from electron microscopy",
    #      'Shepherd &amp; Harris, <i>The Journal of Neuroscience</i> '
    #      '18(20):8300-8310, 1998, doi:10.1523/JNEUROSCI.18-20-08300.1998.',
    #      "The 0.17 um calibre of a CA3-to-CA1 axon shaft, the thinnest structure "
    #      "a drawing at true proportions would have to render."),
    #     ("visible light cannot resolve anything that small",
    #      'Huang, Bates &amp; Zhuang, <i>Annual Review of Biochemistry</i> '
    #      '78:993-1016, 2009, doi:10.1146/annurev.biochem.77.061906.092014.',
    #      "The diffraction limit: 200-300 nm laterally, 500-700 nm axially."),
    #     ("cell traced through a whole brain keeps its axon",
    #      'Winnubst <i>et al.</i>, <i>Cell</i> 179(1):268-281.e13, 2019, '
    #      'doi:10.1016/j.cell.2019.07.042.',
    #      "Whole-brain single-neuron reconstruction; more than 85 m of axon across "
    #      "more than 1,000 projection neurons."),
    #     ("come from one paper",
    #      'Yamashita, Vavladeli, Pala, Galan, Crochet, Petersen &amp; Petersen, '
    #      '<i>Frontiers in Neuroanatomy</i> 12:33, 2018, doi:10.3389/fnana.2018.00033.',
    #      "The projection cells in the complete set; its full text contains no "
    #      "statement about shrinkage or a correction, and describes its axon tracing "
    #      "as possibly incomplete. CC BY 4.0."),
    #     ("The published figure for that is",
    #      'van Pelt, van Ooyen &amp; Uylings, <i>Frontiers in Neuroanatomy</i> '
    #      '8:54, 2014, doi:10.3389/fnana.2014.00054.',
    #      "How much intracortical axon a 300 um slice removes: 48-49%, against "
    #      "15-17% of dendrite."),
    #     ("loses roughly half its thickness",
    #      'Gardella <i>et al.</i>, <i>Journal of Neuroscience Methods</i> '
    #      '124(1):45-59, 2003, doi:10.1016/S0165-0270(02)00363-1.',
    #      "Measured shrinkage by embedding method; 80 um vibratome sections "
    #      "finished at 31.78 um."),
    #     ("in the preparation these files come from",
    #      'Mohan <i>et al.</i>, <i>Cerebral Cortex</i> 25(12):4839-4853, 2015, '
    #      'doi:10.1093/cercor/bhv188.',
    #      "63 +/- 10% z shrinkage measured in 350 um slices, and the finding that "
    #      "total dendritic length rises only 11 +/- 2% when corrected."),
    #     ("leaving depth-derived measurements out of its own analysis",
    #      'Gouwens <i>et al.</i>, <i>Nature Neuroscience</i> 22(7):1182-1195, '
    #      '2019, doi:10.1038/s41593-019-0417-0.',
    #      "The Allen Cell Types morphologies, and the decision to exclude "
    #      "z-derived features rather than correct the coordinates."),
    #     ("rather than by correcting the coordinates",
    #      'Lee <i>et al.</i>, <i>eLife</i> 10:e65482, 2021, '
    #      'doi:10.7554/eLife.65482.',
    #      "Where a per-cell shrinkage correction is applied: downstream, in the "
    #      "Patch-seq pipeline, not in the distributed files."),
    #     ("which is the paper that states the shrinkage correction",
    #      'Emmenegger, Qi, Wang &amp; Feldmeyer, <i>Cerebral Cortex</i> '
    #      '28(4):1439-1457, 2018, doi:10.1093/cercor/bhx352, attributing Marx '
    #      '<i>et al.</i>, <i>Nature Protocols</i> 7(2):394-407, 2012, '
    #      'doi:10.1038/nprot.2011.449.',
    #      "The x1.1 and x2.1 correction factors, and the laboratory whose cells "
    #      "make up most of the fully-qualified set."),
    #     ("the widths differed by about a factor of two on visually matched segments",
    #      'Blackman, Grabuschnig, Legenstein &amp; Sjostrom, <i>Frontiers in '
    #      'Neuroanatomy</i> 8:65, 2014, doi:10.3389/fnana.2014.00065.',
    #      "The same eight cells reconstructed two ways: 1.80 +/- 0.15 um against "
    #      "0.91 +/- 0.09 um."),
    #     ("The field's own tracing benchmark excluded diameter",
    #      'Gillette, Brown &amp; Ascoli, <i>Neuroinformatics</i> 9(2-3):233-245, '
    #      '2011, doi:10.1007/s12021-011-9117-y.',
    #      "Diameter left out of the DIADEM competition as too subjective at the "
    #      "resolutions used for whole-arbor reconstruction."),
    #     ("three experts tracing one dendrite",
    #      'Fernholz, Guggiana Nilo, Bonhoeffer &amp; Kist, <i>PLoS Computational '
    #      'Biology</i> 20(2):e1011774, 2024, doi:10.1371/journal.pcbi.1011774.',
    #      "Inter-operator agreement on a traced arbor, and one person's agreement "
    #      "with themselves."),
    #     ("which contains no such factor",
    #      'Megias, Emri, Freund &amp; Gulyas, <i>Neuroscience</i> '
    #      '102(3):527-540, 2001, doi:10.1016/S0306-4522(00)00496-6.',
    #      "Where dendritic spines are on a CA1 pyramidal cell; it carries no "
    #      "membrane-area factor, though it is often cited for one."),
    #     ("from a 2016 study of human cortical cells",
    #      'Eyal <i>et al.</i>, <i>eLife</i> 5:e16553, 2016, '
    #      'doi:10.7554/eLife.16553.',
    #      "The spine membrane-area factor, F = 1.78-2.39, applied only beyond "
    #      "60 um from the soma."),
    #     ("comes from a 1965 paper on the frog neuromuscular junction",
    #      'Katz &amp; Miledi, <i>Proceedings of the Royal Society B</i> '
    #      '161(985):483-495, 1965, doi:10.1098/rspb.1965.0016.',
    #      "The measured synaptic delay: a minimum of 0.4-0.5 ms and a modal value "
    #      "near 0.75 ms, at 20 C in low-calcium Ringer."),
    #     ("releases in about a hundred and fifty microseconds",
    #      'Sabatini &amp; Regehr, <i>Nature</i> 384(6605):170-172, 1996, '
    #      'doi:10.1038/384170a0.',
    #      "Transmitter release 150 us after the onset of the presynaptic action "
    #      "potential, at physiological temperature."),
    # ],
    "beauty.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("AVONET gives body mass",
         'Tobias <i>et al.</i>, <i>Ecology Letters</i> 25(3):581-597, 2022, '
         'doi:10.1111/ele.13898.',
         "Body mass, range size, family and order for 11,009 bird species on "
         "the HBW-BirdLife v5 taxonomy; CC BY 4.0."),
        ("iratebirds project",
         'Santangeli <i>et al.</i>, <i>npj Biodiversity</i> 2:20, 2023, '
         'doi:10.1038/s44185-023-00026-2.',
         "Rated attractiveness per species and sex from over 400,000 "
         "photograph ratings by more than 6,000 people; the deposit is CC BY 4.0."),
        ("GBIF backbone gives the year",
         'GBIF Secretariat, <i>GBIF Backbone Taxonomy</i>, checklist dataset, '
         'doi:10.15468/39omei.',
         "The full scientific name with authorship, from which the year of "
         "description is read."),
        ("public-attention measure",
         'Mittermeier <i>et al.</i>, <i>Conservation Biology</i> 35(2):412-423, 2021, '
         'doi:10.1111/cobi.13702.',
         "Wikipedia pageviews as a measure of public interest in species, "
         "the method this page borrows."),
        ("OpenAlex gives the number of papers",
         'Priem, Piwowar &amp; Orr, <i>arXiv</i> 2205.01833, 2022.',
         "The open index of scholarly works whose title-and-abstract search "
         "gives the paper counts; data CC0."),
        ("changed meaning in February 2026",
         'OpenAlex, &ldquo;New features and usage-based pricing&rdquo;, 24 February 2026, '
         'https://blog.openalex.org/openalex-api-new-features-and-usage-based-pricing/.',
         "The date the bare search parameter was redefined as full-text search "
         "and the API became metered, at $0.0001 for a filtered list call."),
        ("Table 1a",
         'IUCN, <i>The IUCN Red List of Threatened Species</i>, version 2026-1, '
         'summary statistics Table 1a, 2026, https://www.iucnredlist.org.',
         "Described, evaluated and threatened species by major group, and the "
         "category per bird species through the Red List API."),
        ("published bird model used a tree",
         'Ducatez &amp; Lefebvre, <i>PLoS ONE</i> 9(2):e89955, 2014, '
         'doi:10.1371/journal.pone.0089955.',
         "10,064 birds; phylogeny takes 74% of the variance in research effort; "
         "Least Concern species have twice the papers of threatened ones in a "
         "bivariate comparison, not a model term."),
        ("Brooke et al. 2014",
         'Brooke, Bielby, Nambiar &amp; Carbone, <i>PLoS ONE</i> 9(4):e93195, 2014, '
         'doi:10.1371/journal.pone.0093195.',
         "286 carnivores; IUCN status dropped from the model beside body mass, "
         "range and diet breadth at the second simplification step "
         "(likelihood-ratio p = 0.848, Table S5)."),
        ("McKenzie &amp; Robertson 2015",
         'McKenzie &amp; Robertson, <i>PLoS ONE</i> 10(7):e0131004, 2015, '
         'doi:10.1371/journal.pone.0131004.',
         "225 British breeding birds; Red List status null (univariate p = 0.34; "
         "multivariable t = 0.45, p = 0.65), national action-plan status "
         "positive in the multivariable model (t = 3.14)."),
        ("Fleming &amp; Bateman 2016",
         'Fleming &amp; Bateman, <i>Mammal Review</i> 46(4):241-254, 2016, '
         'doi:10.1111/mam.12066.',
         "331 Australian mammals; the threat-term result is in the paywalled "
         "full text and was not read for this page."),
        ("dos Santos et al. 2020",
         'dos Santos <i>et al.</i>, <i>Animal Conservation</i> 23(6):679-688, 2020, '
         'doi:10.1111/acv.12586.',
         "4,108 terrestrial mammals, hurdle model; the abstract reports threat "
         "status as weakly associated with research presence and volume. Read "
         "from the abstract; the full text is open access but was not reached."),
        ("Adamo et al. 2021",
         'Adamo <i>et al.</i>, <i>Nature Plants</i> 7:574-578, 2021, '
         'doi:10.1038/s41477-021-00912-2.',
         "113 Alpine plants; color, conspicuousness and range predict research "
         "attention; the authors' published code has no threat-status term. "
         "Paywalled; not read for this page."),
        ("Tam et al. 2022",
         'Tam, Lagisz, Cornwell &amp; Nakagawa, <i>GigaScience</i> 11:giac074, 2022, '
         'doi:10.1093/gigascience/giac074.',
         "5,497 mammals; IUCN status linear -16.4 [-19.3, -13.6] with a "
         "quadratic term; Google Trends a strong positive predictor."),
        ("Mammola et al. 2023",
         'Mammola <i>et al.</i>, <i>eLife</i> 12:RP88251, 2023, '
         'doi:10.7554/eLife.88251.',
         "3,019 species across 29 phyla; being on the Red List raises interest "
         "whether the species is endangered or of Least Concern."),
        ("Guedes et al. 2023",
         'Guedes, Moura &amp; Diniz-Filho, <i>Ecography</i> 2023:e06491, 2023, '
         'doi:10.1111/ecog.06491.',
         "10,531 reptiles; body size, description year and proximity to "
         "institutions dominate. Full text open access (CC BY), not reached past "
         "the publisher's bot wall."),
        ("Ducatez &amp; DeVore 2026",
         'Ducatez &amp; DeVore, <i>PLoS ONE</i> 21:e0347198, 2026, '
         'doi:10.1371/journal.pone.0347198.',
         "370 turtles; threatened vs non-threatened -0.10, t = -0.46, p = 0.64 "
         "(the extinction-risk ordinal +0.10, p = 0.14); phylogeny 66% of the "
         "variance; assessed species more studied than unassessed."),
        ("h-index dataset of their own",
         'Tam <i>et al.</i>, GigaDB dataset 102237, 2022, doi:10.5524/102237.',
         "Per-species h-index, publication count, Red List category and Google "
         "Trends for 7,521 mammals; CC0."),
    ],
    "continents.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("MIDAS estimates of GNSS station motion",
         'Blewitt, G., Kreemer, C., Hammond, W.C. &amp; Gazeaux, J., '
         '<i>Journal of Geophysical Research: Solid Earth</i> 121(3):2054-2068, '
         '2016, doi:10.1002/2015JB012552.',
         "The velocity estimator behind every station used here, and its "
         "stated accuracy of 0.23 mm/yr RMS in horizontal velocity on the "
         "stable North American interior."),
        ("the IGS realisation of ITRF2020",
         'Altamimi, Z., Metivier, L., Rebischung, P., Collilieux, X., '
         'Chanard, K. &amp; Barneoud, J., <i>Geophysical Research Letters</i> '
         '50(24):e2023GL106373, 2023, doi:10.1029/2023GL106373.',
         "ITRF2020-PMM, the independently estimated plate motion model every "
         "fitted rotation on this page is checked against; 13 plates from 518 "
         "sites, fitting that velocity field to 0.25 mm/yr WRMS."),
        ("equation 1 of Altamimi and colleagues 2017",
         'Altamimi, Z., Metivier, L., Rebischung, P., Rouby, H. &amp; '
         'Collilieux, X., <i>Geophysical Journal International</i> '
         '209(3):1906-1912, 2017, doi:10.1093/gji/ggx136.',
         "The Euler-pole-to-surface-velocity relation used to fit every plate. "
         "Neither MORVEL nor the NNR-MORVEL56 paper states it."),
        ("Bird's PB2002 model",
         'Bird, P., <i>Geochemistry, Geophysics, Geosystems</i> 4(3):1027, '
         '2003, doi:10.1029/2001GC000252.',
         "The plate boundary geometry every distance on this page is measured "
         "to: 52 plates and 13 diffuse deformation zones."),
        ("Table 1 of the paper itself",
         'Argus, D.F., Gordon, R.G. &amp; DeMets, C., <i>Geochemistry, '
         'Geophysics, Geosystems</i> 12(11):Q11001, 2011, '
         'doi:10.1029/2011GC003751.',
         "NNR-MORVEL56, the geologically averaged plate motions, with their "
         "95% uncertainties. The paper states 'This paper is not subject to "
         "U.S. copyright'; the MORVEL website reserves its authors' "
         "commercial rights to the graphics and results generated from "
         "that site."),
        ("MORVEL's averaging interval is not one number",
         'DeMets, C., Gordon, R.G. &amp; Argus, D.F., <i>Geophysical Journal '
         'International</i> 181(1):1-80, 2010, '
         'doi:10.1111/j.1365-246X.2009.04491.x.',
         "MORVEL itself, including the averaging intervals and the section "
         "documenting plate boundaries that have slowed within the last few "
         "million years, which this page reproduces independently."),
        ("end-members of a spectrum of possibilities",
         'Davies, H.S., Green, J.A.M. &amp; Duarte, J.C., <i>Global and '
         'Planetary Change</i> 169:133-144, 2018, '
         'doi:10.1016/j.gloplacha.2018.07.015.',
         "The one paper that built all four future geometries, in a "
         "deliberately standardised way, and its statement that the "
         "supercontinent-cycle modes they stand for 'should be treated as "
         "end-members of a spectrum of possibilities'."),
        ("The grids are a digitisation of maps that were drawn",
         'Davies, H.S., Green, J.A.M. &amp; Duarte, J.C., <i>Earth System '
         'Dynamics</i> 11(1):291-299, 2020, doi:10.5194/esd-11-291-2020. '
         'Data at OSF 8NEQ4, doi:10.17605/OSF.IO/8NEQ4, CC0 1.0.',
         "The gridded scenarios themselves, their 0.25 degree resolution, the "
         "artificial two-degree polar land mask, and the CC0 license."),
        ("it was devised for a television series and reached print in a trade "
         "book",
         'Nield, T., <i>Supercontinent: Ten Billion Years in the Life of Our '
         'Planet</i>, Granta, 2007.',
         "Novopangaea's only source. Roy Livermore devised it in the late "
         "1990s for The Future Is Wild, a 2002 television series "
         "co-produced by Arte, ZDF, ORF, Mediaset, Animal Planet and "
         "Discovery; it has no peer-reviewed primary source."),
        ("the field's own review names uncertainty quantification as an "
         "open problem",
         'Seton, M. <i>et al.</i>, <i>Nature Reviews Earth &amp; Environment</i> '
         '4:185-204, 2023, doi:10.1038/s43017-022-00384-8.',
         "Why no reconstruction on this page carries a formal error bar."),
        ("The models share ancestry",
         'Buffan, L., Jones, L.A., Domeier, M., Scotese, C.R., Zahirovic, S. '
         '&amp; Varela, S., <i>Methods in Ecology and Evolution</i> '
         '14:3007-3019, 2023, doi:10.1111/2041-210X.14204.',
         "Inter-model disagreement measured on a global grid, and the "
         "common ancestry it documents between several of the models. That "
         "the true spread is therefore wider is this page's inference, not "
         "the paper's."),
        ("cannot determine its longitude at all unless further assumptions "
         "are made",
         'M&#252;ller, R.D. <i>et al.</i>, <i>Solid Earth</i> 13(7):1127-1159, '
         '2022, doi:10.5194/se-13-1127-2022.',
         "Verbatim: since the Earth's magnetic dipole field is radially "
         "symmetric, paleo-longitudinal information cannot be determined "
         "from paleomagnetic data alone unless further assumptions are "
         "made."),
        ("Equal Earth, which is equal-area",
         'Savri&#269;, B., Patterson, T. &amp; Jenny, B., <i>International '
         'Journal of Geographical Information Science</i> 33(3):454-465, 2019, '
         'doi:10.1080/13658816.2018.1504949.',
         "The projection used for both maps, chosen because every number in "
         "their captions is an area claim and because its pole line keeps the "
         "circumpolar scenario legible."),
    ],
    # food.html: UNPUBLISHED 2026-09-09 (unpublished/RETIRED.md).
    # Commented, not deleted: these tuples ARE the citation data for that
    # page - anchor phrase, source, what it supports - and republishing is
    # uncommenting rather than rebuilding them from the article. Left live,
    # the script reported 'does not exist' as a problem on every run, which
    # teaches a reader to skip the problems block.
    # "food.html": [
    #     ("Anchor phrase", "Source", "What it supports"),
    #     ("quantitative definition",
    #      'Fazzino, Rohde &amp; Sullivan, <i>Obesity</i> 27(11):1761-1768, 2019, '
    #      'doi:10.1002/oby.22639.',
    #      "The three threshold pairs, how they were drawn from 75 named foods, "
    #      "and the 62% of FNDDS 2015-16 items, the fresh foods not captured and "
    #      "the reduced-content products that were."),
    #     ("Human milk, the one whole food",
    #      'DiFeliceantonio <i>et al.</i>, <i>Cell Metabolism</i> 28(1):33-44, 2018, '
    #      'doi:10.1016/j.cmet.2018.05.018.',
    #      "Foods combining fat and carbohydrate are valued above equally liked "
    #      "fat-only or carbohydrate-only foods; the authors name breast milk as "
    #      "the natural exception."),
    #     ("rated 52 foods",
    #      'Rogers, Vural, Flynn &amp; Brunstrom, <i>Appetite</i> 201:107596, 2024, '
    #      'doi:10.1016/j.appet.2024.107596.',
    #      "No difference in rated palatability between foods meeting the "
    #      "hyper-palatable rule and foods not meeting it."),
    #     ("rate 436 foods",
    #      'Finlayson <i>et al.</i>, <i>Appetite</i> 213:108029, 2025.',
    #      "Nutrient content explains about a fifth of rated liking."),
    #     ("1988 to 2018",
    #      'Demeke, Rohde, Chollet-Hinton, Sutton, L&rsquo;Insalata &amp; Fazzino, '
    #      '<i>Public Health Nutrition</i> 26(1):182-189, 2023, '
    #      'doi:10.1017/S1368980022001227.',
    #      "Share of items meeting the rule in the 1988, 2001 and 2017-18 US "
    #      "survey databases, and the odds for items present in all three."),
    #     ("store shelves met the rule",
    #      'Fazzino, Bristi, Chollet-Hinton &amp; Sutton, <i>Public Health '
    #      'Nutrition</i> 29(1):e110, 2026, doi:10.1017/S1368980026102614.',
    #      "Share of store items and of household purchases meeting the rule, "
    #      "Circana scanner data 2015-2018."),
    #     ("moderate overlap",
    #      'Sutton, Stratton, L&rsquo;Insalata &amp; Fazzino, <i>Obesity</i> 32(1):166-175, '
    #      '2024, doi:10.1002/oby.23897.',
    #      "The 40-70% overlap between the hyper-palatable rule, the NOVA "
    #      "ultra-processed class and high energy density."),
    #     ("SR Legacy release of April 2018",
    #      'U.S. Department of Agriculture, Agricultural Research Service, '
    #      '<i>FoodData Central</i>, SR Legacy, April 2018 release (CC0).',
    #      "Every computed number on the page: energy, fat, carbohydrate, sugar, "
    #      "fibre and sodium per 100 g for each food, and the food groups."),
    #     ("pleasantness peaks",
    #      'Moskowitz, Kluter, Westerling &amp; Jacobs, <i>Science</i> '
    #      '184(4136):583-585, 1974.',
    #      "Perceived sweetness rises with sucrose concentration while "
    #      "pleasantness rises and then falls."),
    #     ("Sadler and colleagues",
    #      'Sadler, McNulty &amp; Gibson, <i>Critical Reviews in Food Science and '
    #      'Nutrition</i> 55(3):338-356, 2015.',
    #      "The inverse fat-sugar relation in diets on a share-of-energy basis "
    #      "is partly arithmetic."),
    # ],
    # R4 (2026-10-23, D-20): the page runs on ERCOT's real prices. Every source
    # was opened by R4 that day (SOURCES_VERIFIED Part 7). storage/update_page.py
    # applies this entry itself (lostgas's idiom). Denholm et al. 2023 left with
    # the synthetic year's "flattens past four hours", which no longer appears.
    "storage.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("historical settlement point prices",
         'ERCOT, <i>Historical DAM Load Zone and Hub Prices</i> (NP4-180-ER) and '
         '<i>Historical RTM Load Zone and Hub Prices</i> (NP6-785-ER), Market '
         'Information System reports 13060 and 13061, 2011 to date.',
         "Every price the battery trades on: real-time and day-ahead, hubs and "
         "load zones. ERCOT's terms allow raw public data to be redistributed in "
         "compilations, charts and analyses."),
        ("independent market monitor",
         'Potomac Economics, <i>2025 State of the Market Report for the ERCOT '
         'Electricity Markets</i>, June 2026.',
         "ERCOT's share of Texas demand (about 90%), the fleet's size at the end "
         "of 2025, its revenue 2021-2025 (Figure 17, read by eye), what ECRS "
         "stands for, and the quoted passages on revenue spikes, the 2025 "
         "decline, ancillary services before 2024 and price spikes in the "
         "solar ramp."),
        ("on-peak trades EIA publishes",
         'U.S. Energy Information Administration, <i>Wholesale Electricity and '
         'Natural Gas Market Data</i>, ICE, 2015 (ice_electric-2015final.xls).',
         "The independent check on the price reader: ERCOT North 345 kV on-peak "
         "trades."),
        ("a linear program",
         'Sioshansi, Denholm, Jenkin &amp; Weiss, &ldquo;Estimating the value '
         'of electricity storage in PJM: Arbitrage and some welfare '
         'effects&rdquo;, <i>Energy Economics</i> 31(2):269&ndash;277, 2009.',
         "The perfect-foresight dispatch formulation and its upper-bound "
         "character."),
        ("round-trip efficiency",
         'Mongird <i>et al.</i>, <i>2020 Grid Energy Storage Technology Cost and '
         'Performance Assessment</i>, Pacific Northwest National Laboratory, '
         'DOE/PA-0204, December 2020.',
         # D-21 item 3: the report gives RTE 86% (p.13) and no degradation
         # cost per MWh; its per-MWh figures are variable O&M, $0.5125/MWh,
         # and RTE losses, $0.005/kWh (Figure 2). Re-opened by R4, 2026-10-23.
         "Round-trip efficiency (86%). It gives no degradation cost; the "
         "model's $2/MWh of throughput is an assumption."),
        ("Annual Technology Baseline",
         'NREL, <i>Annual Technology Baseline</i> 2024 (2022 dollars), '
         'utility-scale battery storage, 4-hour duration, Moderate scenario, '
         'Market case.',
         "The cost reference: $1,938/kW capex (overnight cost, grid connection "
         "and construction finance) "
         # D-21 item 4: ATB gives batteries no discount rate and a 15-year
         # life; the twenty years and the 8% are the model's.
         "plus $44/kW-yr fixed operations, annualised over twenty years at "
         "an assumed eight percent; ATB itself gives these batteries a 15-year "
         "life and no financial assumptions. A representative figure for scale, "
         "not a quote for any particular project."),
    ],
    # longevity.html is not here on purpose. Its page generator
    # (longevity-quotient/update_page.py) edits the shipped file in place and
    # keeps whatever Sources block it finds, so the page already owns its
    # reference list; a PAGES entry made a second owner and the two disagreed.
    # The entry was also stale against the prose - two of its ten anchors
    # ("rockfishes of Sebastidae", "bats of Chiroptera") no longer appear on
    # the page at all, and five others now match only inside the data-source
    # table. Removed 2026-09-05. Still open, and the longevity project's to
    # decide: the page lists ten references and carries one marker.
    # lostgas/update_page.py applies this entry itself (takeaway's idiom). Every
    # source was opened by Q6 on 2026-10-22 or R3 on 2026-10-23 (SOURCES_VERIFIED,
    # Q6 lines and Part 6). The Oklahoma tariff names its utility: a citation for a
    # public fact; the page's prose names no operator (R3 packet, plan review 10).
    "lostgas.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("as a percentage of the gas used",
         'Pipeline and Hazardous Materials Safety Administration, <i>Gas Distribution '
         'Annual Data, 2010 to present</i>, Form PHMSA F 7100.1-1, Part G; and the form '
         'itself, rev. 10/11/2018 ("CY 2018 and forward").',
         "Each operator's percent unaccounted for, by state of operation, its owner type, "
         "and the Part G definition."),
        ("says what it is",
         'Pipeline and Hazardous Materials Safety Administration, <i>Report on lost '
         'and unaccounted for natural gas metrics</i>, report to Congress under '
         'section 29 of the PIPES Act of 2016, May 2017.',
         "That LAUF combines measurement inaccuracy and unknown leaks in unknowable "
         "shares, is not a proxy for leaks or emissions, and the instruction to report "
         "a negative as zero."),
        ("negatives are allowed",
         'Federal Register 83 FR 3462, 25 January 2018, "Pipeline Safety: '
         'Information Collection Activities".',
         "PHMSA's change to a consumption denominator and its allowing negative "
         "values, from calendar year 2018 reports."),
        ("presumes that all lost and unaccounted-for gas",
         'Railroad Commission of Texas, 16 Texas Administrative Code s.7.5525, Lost '
         'and Unaccounted for Gas, and s.7.5519, Gas Cost Recovery (Chapter 7 '
         'compilation effective 8 April 2024).',
         "The presumption, meter errors named in (a); lost-gas expense above 5.0% of gas "
         "metered in disallowed for ratemaking unless the Commission allows more (b), (c); "
         "the Commission's review of the reasonableness of gas expense (d); purchased gas "
         "adjustment clauses (7.5519)."),
        ("Oklahoma's rule requires gas to be measured",
         'Oklahoma Corporation Commission, Oklahoma Administrative Code 165:45-7-11, '
         'Gas measurement requirements (Chapter 45 effective 1 October 2024); and 165:50, '
         'Fuel, Purchased Gas, and Purchased Power Adjustment Clauses (effective 25 July 2019).',
         "Measurement so that LAUF may be determined, no percentage; the purchased gas "
         "adjustment rules, which do not mention lost gas."),
        ("large utility's tariff",
         'Oklahoma Natural Gas Company, tariff schedules 1001 (Purchased Gas Adjustment '
         'Clause), 1071 (Unrecovered Purchased Gas Cost) and 1191 (Lost, Used, and '
         'Unaccounted for Gas Rider), as approved by the Oklahoma Corporation Commission.',
         "\"LUFG shall be collected through the PGA\", the two percent safe harbor and "
         "the Commission's power to disallow the excess; LUFG includes gas used."),
        ("at the city gate",
         'U.S. Energy Information Administration, natural gas series for Texas and Oklahoma: '
         'residential consumption, number of residential consumers, residential price and '
         'citygate price, annual.',
         "Gas per household and the price utilities pay for gas, by state."),
        ("Reader-Harris/Gallagher discharge coefficient",
         'Reader-Harris, <i>ISO 5167: Past and Present</i>, Global Flow Measurement Workshop, '
         '2022; and Emerson, <i>Conditioning Orifice Technology and Orifice Standards</i>, '
         'technical note, Table 6, quoting ISO 5167-2:2003, section 5.3.3.1.',
         "The orifice equation the meter model uses and its coefficient's stated uncertainty."),
        ("AGA Report No. 8",
         'National Institute of Standards and Technology, <i>AGA8</i> reference code '
         '(GERG-2008, DETAIL and GROSS), github.com/usnistgov/AGA8; not subject to '
         'copyright protection in the United States (17 U.S.C. 105), foreign copyright may '
         'apply.',
         "Compressibility and heating value in the meter model."),
        ("the median Henry Hub price",
         'U.S. Energy Information Administration, <i>Henry Hub Natural Gas Spot Price</i>, '
         'monthly, series RNGWHHD.',
         "The price the meter model's imbalance is valued at."),
    ],
    # uri/update_page.py applies this entry itself (lostgas's idiom). Every source was opened by Q12 on
    # 2026-10-24 (SOURCES_VERIFIED Part 8; files and hashes in uri/data/fetched.json). Utilities are named
    # as the filings name them, for the figures the filings give (Q12 packet).
    # Ethane left in the gas (Q11, 2026-10-25): EIA sources only, archived (D-60 C).
    "ethane.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("The share is ethane over EIA's total for the five liquids",
         'U.S. Energy Information Administration, <i>Natural Gas Plant Field Production</i>, U.S. field production of natural gas liquids by product, thousand barrels per day, monthly (PET_PNP_GP_DC_NUS_MBBLPD_M), fetched 25 October 2026.',
         'Every volume and share on the page: ethane, propane and the total of the five plant liquids, 2009 to the latest month.'),
        ('EIA used the same measure in',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;First shipment of ethane from U.S. Gulf Coast arrives in Europe&rdquo;, 22 September 2016.',
         "Ethane as a feedstock for plastics; propane, butanes and natural gasoline cannot be left in the gas as ethane can; the choice depends on prices, demand and the plants' ability; ethane's share of NGPL, 42% in 2010 and 34% in 2015."),
        ('Today in Energy, August 31, 2022',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;EIA expects U.S. ethane production to grow by 9% in the second half of 2022&rdquo;, 31 August 2022.',
         'Ethylene as a precursor of plastics and resins; the premium since 2017.'),
        ('Today in Energy, January 15, 2013',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;2012 Brief: Natural gas liquids prices down in 2012&rdquo;, 15 January 2013.',
         'What ethane rejection is, its limit, and when it occurs.'),
        ('EIA described what had changed',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;Ethane production expected to increase as petrochemical consumption and exports expand&rdquo;, 1 April 2016.',
         'The ethane in raw gas exceeding what could be consumed and exported; prices at or below gas; the wave of investment from 2012; the first waterborne exports, March 2016; 1.1 million b/d in 2015.'),
        ('more heat than the national average',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;Newly released heat content data allow for state-to-state natural gas comparisons&rdquo;, 14 October 2014.',
         "Heat content of delivered gas in West Virginia and North Dakota, July 2014, and what it may indicate; the Btu range appliances need; where rejection was most evident in 2013."),
        ('Today in Energy, July 29, 2013',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;Natural gas liquids prices trend down since the start of 2012&rdquo;, 29 July 2013.',
         'The first-half 2013 price, 27 cents a gallon, and ethane left in the gas because it was low against gas.'),
        ('Today in Energy, May 8, 2014',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;High value of liquids drives U.S. producers to target wet natural gas resources&rdquo;, 8 May 2014.',
         'Ethane priced below gas and sold as natural gas; the estimates of 200 to 400 thousand barrels a day.'),
        ('Natural Gas Weekly Update, February 14, 2019',
         'U.S. Energy Information Administration, <i>Natural Gas Weekly Update</i>, week ending February 13, 2019, released February 14, 2019, &ldquo;As energy markets are showing more love, ethane is feeling less rejected&rdquo;.',
         "Prices within $1.00/MMBtu of Henry Hub from late 2012 to mid-2017; EIA's test of rejection against dry gas production."),
        ('Today in Energy, March 20, 2025',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;U.S. ethane production, consumption, and exports set new records in 2024&rdquo;, 20 March 2025.',
         "The 2024 prices as EIA states them; the Houston Ship Channel price; the 2024 record and its causes in EIA's words; Mont Belvieu as the main pricing hub."),
        ('Several new petrochemical crackers were commissioned in the United States in 2018',
         'U.S. Energy Information Administration, <i>Today in Energy</i>, &ldquo;U.S. hydrocarbon gas liquids production reaches 5 million barrels per day in 2018&rdquo;, 4 June 2019.',
         "Recovery when ethane's value covers the costs; the crackers of 2018; 1.71 million b/d in 2018, 20% above 2017."),
        ("EIA gives ethane's approximate heat content",
         'U.S. Energy Information Administration, <i>Monthly Energy Review</i>, September 2026, Appendix A, Table A1, Approximate Heat Content of Petroleum and Biofuels.',
         "Ethane's heat content, 2.783 million Btu a barrel."),
        ('found no ethane price series that is free to republish',
         'U.S. Energy Information Administration, Copyrights and Reuse.',
         "EIA's publications are public domain; material licensed from private organizations may be protected."),
    ],
    # One clean-air rule, three orders of effects (chain-reactions lane, 2026-11-07). oxygen/update_page.py
    # applies this entry itself (ethane's idiom). Files and hashes in oxygen/data/fetched.json; every entry was
    # checked by the lane's fact-check agents (03 RESEARCH/nov-2026-articles/chain-reactions/research/w3-0*.md).
    "greatfilter.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ('probably in the summer of 1950',
         'Jones, E. M., &ldquo;Where is everybody?&rdquo; An account of Fermi&rsquo;s question, Los Alamos National Laboratory report LA-10311-MS, March 1985, <a href="https://www.osti.gov/biblio/5746675">OSTI</a>.',
         'The lunch at Los Alamos, the companions, York&rsquo;s recollection of the reasoning, and the uncertain date (1950 judged most probable).'),
        ('he called it the Great Filter',
         'Hanson, R., &ldquo;The Great Filter &mdash; Are We Almost Past It?&rdquo;, 15 September 1998, <a href="https://mason.gmu.edu/~rhanson/greatfilter.html">essay</a>.',
         'The Great Filter argument, and the point that the easier the past steps, the worse the future odds.'),
        ('Earth formed 4.54',
         'Dalrymple, G. B. (2001). The age of the Earth in the twentieth century: a problem (mostly) solved. <i>Geological Society Special Publications</i> 190, 205&ndash;221, <a href="https://doi.org/10.1144/GSL.SP.2001.190.01.14">doi:10.1144/GSL.SP.2001.190.01.14</a>.',
         'Earth&rsquo;s age, 4.54 billion years, within about 1 percent.'),
        ('Zircon crystals show liquid water',
         'Wilde, S. A., Valley, J. W., Peck, W. H. &amp; Graham, C. M. (2001). Evidence from detrital zircons for the existence of continental crust and oceans on the Earth 4.4 Gyr ago. <i>Nature</i> 409, 175&ndash;178, <a href="https://doi.org/10.1038/35051550">doi:10.1038/35051550</a>.',
         'A 4.404-billion-year-old zircon whose oxygen isotopes indicate liquid water.'),
        ('models put the end of an',
         'Ozaki, K. &amp; Reinhard, C. T. (2021). The future lifespan of Earth&rsquo;s oxygenated atmosphere. <i>Nature Geoscience</i> 14, 138&ndash;142, <a href="https://doi.org/10.1038/s41561-021-00693-5">doi:10.1038/s41561-021-00693-5</a>.',
         'An oxygen-rich atmosphere lasts about 1.08 &plusmn; 0.14 billion years more; this page uses about 1 (range 0.8 to 1.5).'),
        ('The oldest widely accepted fossils are',
         'Djokic, T., Van Kranendonk, M. J., Campbell, K. A., Walter, M. R. &amp; Ward, C. R. (2017). Earliest signs of life on land preserved in ca. 3.5 Ga hot spring deposits. <i>Nature Communications</i> 8, 15263, <a href="https://doi.org/10.1038/ncomms15263">doi:10.1038/ncomms15263</a>.',
         'Evidence of life in the 3.48-billion-year-old Dresser Formation.'),
        ('disputed traces',
         'Bell, E. A., Boehnke, P., Harrison, T. M. &amp; Mao, W. L. (2015). Potentially biogenic carbon preserved in a 4.1 billion-year-old zircon. <i>PNAS</i> 112, 14518&ndash;14521, <a href="https://doi.org/10.1073/pnas.1517557112">doi:10.1073/pnas.1517557112</a>.',
         'Carbon of possible biological origin in a 4.1-billion-year-old zircon; disputed.'),
        ('A molecular clock puts the last common ancestor',
         'Moody, E. R. R. et al. (2024). The nature of the last universal common ancestor and its impact on the early Earth system. <i>Nature Ecology &amp; Evolution</i> 8, 1654&ndash;1666, <a href="https://doi.org/10.1038/s41559-024-02461-1">doi:10.1038/s41559-024-02461-1</a>.',
         'The last universal common ancestor about 4.2 billion years ago (4.09 to 4.33), living in an existing ecosystem.'),
        ('Rocks show oxygen being made',
         'Planavsky, N. J. et al. (2014). Evidence for oxygenic photosynthesis half a billion years before the Great Oxidation Event. <i>Nature Geoscience</i> 7, 283&ndash;286, <a href="https://doi.org/10.1038/ngeo2122">doi:10.1038/ngeo2122</a>.',
         'Oxygen production by at least 2.95 billion years ago.'),
        ('one reading of the genes puts the origin later',
         'Shih, P. M., Hemp, J., Ward, L. M., Matzke, N. J. &amp; Fischer, W. W. (2017). Crown group Oxyphotobacteria postdate the rise of oxygen. <i>Geobiology</i> 15, 19&ndash;29, <a href="https://doi.org/10.1111/gbi.12200">doi:10.1111/gbi.12200</a>.',
         'A later origin of oxygenic photosynthesis, near 2.5 to 2.6 billion years ago.'),
        ('Oxygen built up in the air from',
         'Poulton, S. W. et al. (2021). A 200-million-year delay in permanent atmospheric oxygenation. <i>Nature</i> 592, 232&ndash;236, <a href="https://doi.org/10.1038/s41586-021-03393-7">doi:10.1038/s41586-021-03393-7</a>; Gumsley, A. P. et al. (2017). Timing and tempo of the Great Oxidation Event. <i>PNAS</i> 114, 1811&ndash;1816, <a href="https://doi.org/10.1073/pnas.1608824114">doi:10.1073/pnas.1608824114</a>.',
         'The Great Oxidation Event from about 2.43 billion years ago, permanent by about 2.22.'),
        ('when one microbe came to live inside another',
         'Roger, A. J., Mu&ntilde;oz-G&oacute;mez, S. A. &amp; Kamikawa, R. (2017). The origin and diversification of mitochondria. <i>Current Biology</i> 27, R1177&ndash;R1192, <a href="https://doi.org/10.1016/j.cub.2017.09.015">doi:10.1016/j.cub.2017.09.015</a>.',
         'A single origin of mitochondria and of the eukaryotic cell.'),
        ('are from North China',
         'Miao, L. et al. (2024). 1.63-billion-year-old multicellular eukaryotes from the Chuanlinggou Formation in North China. <i>Science Advances</i> 10, eadk3208, <a href="https://doi.org/10.1126/sciadv.adk3208">doi:10.1126/sciadv.adk3208</a>; Betts, H. C. et al. (2018). Integrated genomic and fossil evidence illuminates life&rsquo;s early evolution and eukaryote origin. <i>Nature Ecology &amp; Evolution</i> 2, 1556&ndash;1562, <a href="https://doi.org/10.1038/s41559-018-0644-x">doi:10.1038/s41559-018-0644-x</a>.',
         'Eukaryote fossils about 1.635 billion years old; the last common ancestor of eukaryotes between 1.84 and 1.21 billion years ago.'),
        ('Large fossils appear',
         'Matthews, J. J. et al. (2021). A chronostratigraphic framework for the rise of the Ediacaran macrobiota: new constraints from Mistaken Point Ecological Reserve, Newfoundland. <i>GSA Bulletin</i> 133, 612&ndash;624, <a href="https://doi.org/10.1130/B35646.1">doi:10.1130/B35646.1</a>.',
         'Ediacaran fossils at Mistaken Point dated 574.17 &plusmn; 0.66 million years.'),
        ('Stone tools are',
         'Harmand, S. et al. (2015). 3.3-million-year-old stone tools from Lomekwi 3, West Turkana, Kenya. <i>Nature</i> 521, 310&ndash;315, <a href="https://doi.org/10.1038/nature14464">doi:10.1038/nature14464</a>.',
         'The oldest known stone tools.'),
        ('Homo sapiens about',
         'Hublin, J.-J. et al. (2017). New fossils from Jebel Irhoud, Morocco and the pan-African origin of <i>Homo sapiens</i>. <i>Nature</i> 546, 289&ndash;292, <a href="https://doi.org/10.1038/nature22336">doi:10.1038/nature22336</a>.',
         'Homo sapiens fossils about 315,000 years old.'),
        ('radio dates from',
         'The Nobel Prize, &ldquo;Guglielmo Marconi &mdash; Biographical&rdquo;, <a href="https://www.nobelprize.org/prizes/physics/1909/marconi/biographical/">nobelprize.org</a>.',
         'Marconi&rsquo;s first radio signals in 1895 and the transatlantic signal of December 1901.'),
        ('made this argument in 1995',
         'Mayr, E. (1995). The search for extraterrestrial intelligence: a debate with Carl Sagan. <i>Bioastronomy News</i> 7(3); Spanish translation in Lemarchand, G. A. (ed.) (2010), <a href="https://arxiv.org/abs/1012.2591">arXiv:1012.2591</a>.',
         'Eyes and bioluminescence evolved many times; high intelligence once.'),
        ('Complex multicellular life, with tissues and organs',
         'Knoll, A. H. (2011). The multiple origins of complex multicellularity. <i>Annual Review of Earth and Planetary Sciences</i> 39, 217&ndash;239, <a href="https://doi.org/10.1146/annurev.earth.031208.100209">doi:10.1146/annurev.earth.031208.100209</a>.',
         'Six origins of complex multicellularity: animals, land plants, florideophyte red algae, brown algae and two groups of fungi.'),
        ('Simple multicellularity evolved at least',
         'Grosberg, R. K. &amp; Strathmann, R. R. (2007). The evolution of multicellularity: a minor major transition? <i>Annual Review of Ecology, Evolution, and Systematics</i> 38, 621&ndash;654, <a href="https://doi.org/10.1146/annurev.ecolsys.36.102403.114735">doi:10.1146/annurev.ecolsys.36.102403.114735</a>.',
         'At least 25 origins of multicellularity.'),
        ('Farming began in at least',
         'Larson, G. et al. (2014). Current perspectives and the future of domestication studies. <i>PNAS</i> 111, 6139&ndash;6146, <a href="https://doi.org/10.1073/pnas.1323964111">doi:10.1073/pnas.1323964111</a>.',
         'At least 11 regions of independent domestication, from about 12,000 to 11,000 years ago.'),
        ('times among insects',
         'Mueller, U. G., Gerardo, N. M., Aanen, D. K., Six, D. L. &amp; Schultz, T. R. (2005). The evolution of agriculture in insects. <i>Annual Review of Ecology, Evolution, and Systematics</i> 36, 563&ndash;595, <a href="https://doi.org/10.1146/annurev.ecolsys.36.102003.152626">doi:10.1146/annurev.ecolsys.36.102003.152626</a>.',
         'Insect agriculture evolved once in ants, once in termites and seven times in ambrosia beetles.'),
        ('In 1983 David Raup and James Valentine showed',
         'Raup, D. M. &amp; Valentine, J. W. (1983). Multiple origins of life. <i>PNAS</i> 80, 2981&ndash;2984, <a href="https://doi.org/10.1073/pnas.80.10.2981">doi:10.1073/pnas.80.10.2981</a>.',
         'Several origins of life with all but one lineage extinct are consistent with the record.'),
        ('Nitrogen fixation is another warning',
         'Boyd, E. S. &amp; Peters, J. W. (2013). New insights into the evolutionary history of biological nitrogen fixation. <i>Frontiers in Microbiology</i> 4, 201, <a href="https://doi.org/10.3389/fmicb.2013.00201">doi:10.3389/fmicb.2013.00201</a>.',
         'A single origin of nitrogenase, spread widely by gene transfer.'),
        ('The biochemist Nick Lane answers',
         'Lane, N. (2014). Bioenergetic constraints on the evolution of complex life. <i>Cold Spring Harbor Perspectives in Biology</i> 6, a015982, <a href="https://doi.org/10.1101/cshperspect.a015982">doi:10.1101/cshperspect.a015982</a>.',
         'At least 20 independent origins of archezoa, none outcompeted; the barrier to complex cells is energetic.'),
        ('Brandon Carter proposed it in 1983',
         'Carter, B. (1983). The anthropic principle and its implications for biological evolution. <i>Philosophical Transactions of the Royal Society A</i> 310, 347&ndash;363, <a href="https://doi.org/10.1098/rsta.1983.0096">doi:10.1098/rsta.1983.0096</a>.',
         'The hard-steps model.'),
        ('Andrew Watson worked it out',
         'Watson, A. J. (2008). Implications of an anthropic model of evolution for emergence of complex life and intelligence. <i>Astrobiology</i> 8, 175&ndash;185, <a href="https://doi.org/10.1089/ast.2006.0115">doi:10.1089/ast.2006.0115</a>.',
         'Expected step times in the hard-steps model; with a 5-billion-year window and 1 billion left, a best guess of four hard steps.'),
        ('In 2025 Daniel Mills, Adam Frank and colleagues argued',
         'Mills, D. B., Macalady, J. L., Frank, A. &amp; Wright, J. T. (2025). A reassessment of the &ldquo;hard-steps&rdquo; model for the evolution of intelligent life. <i>Science Advances</i>; <a href="https://arxiv.org/abs/2408.10293">arXiv:2408.10293</a>.',
         'Steps gated by the environment, chiefly oxygen; eukaryotes and animals excluded for about 52 percent of Earth&rsquo;s history.'),
        ('In 2018 Anders Sandberg, Eric Drexler and Toby Ord',
         'Sandberg, A., Drexler, E. &amp; Ord, T. (2018). Dissolving the Fermi paradox. <a href="https://arxiv.org/abs/1806.02404">arXiv:1806.02404</a>.',
         'Table 1 parameter ranges; a 52 percent prior chance of fewer than one civilization in the galaxy; 53 to 99.6 percent after the Fermi observation.'),
        ('A 2015 search of about',
         'Griffith, R. L., Wright, J. T., Maldonado, J., Povich, M. S., Sigurdsson, S. &amp; Mullan, B. (2015). The &Gcirc; infrared search for extraterrestrial civilizations with large energy supplies. III. <i>Astrophysical Journal Supplement Series</i> 217, 25, <a href="https://doi.org/10.1088/0067-0049/217/2/25">doi:10.1088/0067-0049/217/2/25</a>.',
         'About 100,000 galaxies; none reprocesses more than 85 percent of its starlight into mid-infrared heat.'),
        ('Breakthrough Listen observed',
         'Price, D. C. et al. (2020). The Breakthrough Listen search for intelligent life: observations of 1327 nearby stars over 1.10&ndash;3.45 GHz. <i>Astronomical Journal</i> 159, 86, <a href="https://doi.org/10.3847/1538-3881/ab65f1">doi:10.3847/1538-3881/ab65f1</a>.',
         'No candidate signals; fewer than 0.45 percent of the stars host a transmitter above about 2.1 &times; 10<sup>12</sup> W.'),
        ("humanity's total energy supply",
         'Energy Institute, <i>Statistical Review of World Energy 2026</i>, <a href="https://www.energyinst.org/statistical-review">energyinst.org</a>.',
         'Total energy supply of 600.31 exajoules in 2025, about 19 trillion watts.'),
        ('Jason Wright and colleagues estimated in 2018',
         'Wright, J. T., Kanodia, S. &amp; Lubar, E. (2018). How much SETI has been done? Finding needles in the n-dimensional cosmic haystack. <i>Astronomical Journal</i> 156, 260, <a href="https://doi.org/10.3847/1538-3881/aae099">doi:10.3847/1538-3881/aae099</a>.',
         'Searches to date cover about 6 &times; 10<sup>&minus;18</sup> of the haystack, like 8,000 litres of the oceans.'),
        ('could cross the galaxy in less than',
         'Carroll-Nellenback, J., Frank, A., Wright, J. &amp; Scharf, C. (2019). The Fermi paradox and the Aurora effect: exo-civilization settlement, expansion, and steady states. <i>Astronomical Journal</i> 158, 117, <a href="https://doi.org/10.3847/1538-3881/ab31a3">doi:10.3847/1538-3881/ab31a3</a>.',
         'Settlement fronts cross the galaxy in at most about 300 million years; Earth can stay unvisited in a partly settled galaxy.'),
        ("of humanity's potential",
         'Ord, T. (2020). <i>The Precipice: Existential Risk and the Future of Humanity</i>. Bloomsbury, Table 6.1; values as stated by Ord in <a href="https://80000hours.org/podcast/episodes/toby-ord-the-precipice-existential-risk-future-humanity/">80,000 Hours interview, 2020</a>.',
         'About 1 in 6 for existential catastrophe this century; about 1 in 10 from unaligned AI. One person&rsquo;s estimates.'),
        ('superforecasters gave a median of',
         'Karger, E. et al. (2023). <i>Forecasting Existential Risk: Evidence from a Long-Run Forecasting Tournament</i>. Forecasting Research Institute, <a href="https://forecastingresearch.org/xpt">forecastingresearch.org</a>.',
         'Median probability of human extinction by 2100: 1 percent (superforecasters) and 6 percent (domain experts).'),
        ('median of 2,778 AI researchers',
         'Grace, K. et al. (2024). Thousands of AI authors on the future of AI. <a href="https://arxiv.org/abs/2401.02843">arXiv:2401.02843</a>.',
         'Median 5 percent for an extremely bad outcome, such as human extinction, from advanced AI.'),
        ('if the yearly risk were above 1 in 14,000',
         'Snyder-Beattie, A. E., Ord, T. &amp; Bonsall, M. B. (2019). An upper bound for the background rate of human extinction. <i>Scientific Reports</i> 9, 11054, <a href="https://doi.org/10.1038/s41598-019-47540-7">doi:10.1038/s41598-019-47540-7</a>.',
         'The annual probability of extinction from natural causes is very likely below 1 in 14,000.'),
        ('In 2008 the philosopher Nick Bostrom argued',
         'Bostrom, N. (2008). Where are they? Why I hope the search for extraterrestrial life finds nothing. <i>MIT Technology Review</i>, May/June, 72&ndash;77, <a href="https://nickbostrom.com/extraterrestrial.pdf">PDF</a>.',
         'Independent life on Mars would make early steps look easy and move the filter later; complex fossils would be worse news.'),
        ('simulations find that a few percent',
         'Worth, R. J., Sigurdsson, S. &amp; House, C. H. (2013). Seeding life on the moons of the outer planets via lithopanspermia. <i>Astrobiology</i> 13, 1155&ndash;1165, <a href="https://doi.org/10.1089/ast.2013.1028">doi:10.1089/ast.2013.1028</a>.',
         'About 2.6 percent of simulated Mars ejecta reach Earth.'),
        ('Gilman et al. 2023',
         'Gilman, I. S. et al. (2023). The CAM lineages of planet Earth. <i>Annals of Botany</i> 132, 627&ndash;654, <a href="https://doi.org/10.1093/aob/mcad135">doi:10.1093/aob/mcad135</a>.',
         'At least 66 origins of CAM photosynthesis.'),
        ('Sage et al. 2011',
         'Sage, R. F., Christin, P.-A. &amp; Edwards, E. J. (2011). The C4 plant lineages of planet Earth. <i>Journal of Experimental Botany</i> 62, 3155&ndash;3169, <a href="https://doi.org/10.1093/jxb/err048">doi:10.1093/jxb/err048</a>.',
         '62 lineages of C4 photosynthesis.'),
        ('via Lamb et al. 2009',
         'Lamb, T. D., Arendt, D. &amp; Collin, S. P. (2009). The evolution of phototransduction and eyes. <i>Philosophical Transactions of the Royal Society B</i> 364, 2791&ndash;2793, <a href="https://doi.org/10.1098/rstb.2009.0106">doi:10.1098/rstb.2009.0106</a>.',
         'Eyes evolved at least 40 and possibly 65 times (von Salvini-Plawen and Mayr 1977), with a shared molecular toolkit.'),
        ('Emery and Clayton 2004',
         'Emery, N. J. &amp; Clayton, N. S. (2004). The mentality of crows: convergent evolution of intelligence in corvids and apes. <i>Science</i> 306, 1903&ndash;1907, <a href="https://doi.org/10.1126/science.1098410">doi:10.1126/science.1098410</a>.',
         'Complex cognition evolved separately in corvids and apes; the count of five lineages is this page&rsquo;s tally.'),
        ('Dudley et al. 2007',
         'Dudley, R. et al. (2007). Gliding and the functional origins of flight. <i>Annual Review of Ecology, Evolution, and Systematics</i> 38, 179&ndash;201, <a href="https://doi.org/10.1146/annurev.ecolsys.37.091305.110014">doi:10.1146/annurev.ecolsys.37.091305.110014</a>.',
         'Powered flight evolved in insects, pterosaurs, birds and bats.'),
        ('Woods 2010',
         'Woods, C. (ed.) (2010). <i>Visible Language: Inventions of Writing in the Ancient Middle East and Beyond</i>. Oriental Institute Museum Publications 32, University of Chicago.',
         'Writing invented independently in Mesopotamia, Egypt, China and Mesoamerica.'),
        ('Ponce-Toledo et al. 2017',
         'Ponce-Toledo, R. I. et al. (2017). An early-branching freshwater cyanobacterium at the origin of plastids. <i>Current Biology</i> 27, 386&ndash;391, <a href="https://doi.org/10.1016/j.cub.2016.11.056">doi:10.1016/j.cub.2016.11.056</a>.',
         'Primary plastids of Archaeplastida from one cyanobacterium; Paulinella is the second, separate case.'),
        ('Fischer et al. 2016',
         'Fischer, W. W., Hemp, J. &amp; Johnson, J. E. (2016). Evolution of oxygenic photosynthesis. <i>Annual Review of Earth and Planetary Sciences</i> 44, 647&ndash;683, <a href="https://doi.org/10.1146/annurev-earth-060313-054810">doi:10.1146/annurev-earth-060313-054810</a>.',
         'Oxygenic photosynthesis evolved once, in the ancestors of cyanobacteria.'),
        ('Tennie et al. 2009',
         'Tennie, C., Call, J. &amp; Tomasello, M. (2009). Ratcheting up the ratchet: on the evolution of cumulative culture. <i>Philosophical Transactions of the Royal Society B</i> 364, 2405&ndash;2415, <a href="https://doi.org/10.1098/rstb.2009.0052">doi:10.1098/rstb.2009.0052</a>.',
         'Cumulative culture is, as far as is known, unique to humans.'),
    ],
    "oxygen.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("where carbon monoxide was too high",
         '42 U.S.C. 7545(k)(2)(B) and (m)(2), Clean Air Act section 211, as added by the Clean Air Act Amendments of 1990 (P.L. 101-549, section 219), United States Code, 2000 edition, <a href="https://www.govinfo.gov/content/pkg/USCODE-2000-title42/html/USCODE-2000-title42-chap85-subchapII-partA-sec7545.htm">govinfo.gov</a>.',
         'The 2.0 percent oxygen requirement for reformulated gasoline from 1995 and the 2.7 percent winter oxygenated fuel requirement from 1992.'),
        ("Senator Bob Dole's office said the amendment would",
         'Office of Senator Bob Dole, press release on the Daschle-Dole reformulated gasoline amendment, 29 March 1990, <a href="https://dolearchivecollections.ku.edu/collections/press_releases/900329ame.pdf">Robert J. Dole Institute of Politics archive</a>.',
         'The amendment and its stated aim for grain-based fuels such as ethanol.'),
        ("EPA said refiners also chose it for economic reasons",
         'U.S. Environmental Protection Agency, &ldquo;Methyl Tertiary Butyl Ether (MTBE): Gasoline&rdquo;, <a href="https://archive.epa.gov/mtbe/web/html/gas.html">archived web page</a>.',
         'MTBE made from methanol and isobutylene; shipped through existing pipelines, unlike ethanol; lower volatility; chosen for blending characteristics and economic reasons; used at low levels since 1979 to replace lead.'),
        ("the federal panel on oxygenates",
         'Blue Ribbon Panel on Oxygenates in Gasoline, <i>Achieving Clean Air and Clean Water</i>, EPA420-R-99-021, U.S. Environmental Protection Agency, September 1999, <a href="https://archive.epa.gov/oust/mtbe-a/web/pdf/r99021.pdf">PDF</a>.',
         'MTBE in over 85 percent of reformulated gasoline and ethanol in about 8 percent; ethanol blended at terminals; releases from underground gasoline storage systems as the major source of contamination; the turpentine-like taste and odour.'),
        ("Reformulated gasoline was about a third of U.S. gasoline from 1996 on",
         'U.S. Energy Information Administration, product supplied of reformulated motor gasoline (MGRUPUS2) and of finished motor gasoline (MGFUPUS2), annual, fetched 7 November 2026.',
         'The share of reformulated gasoline in U.S. gasoline, and the gasoline total behind the ethanol and MTBE shares.'),
        ("EIA named the oxygen programmes as the cause",
         'U.S. Energy Information Administration, &ldquo;MTBE, Oxygenates, and Motor Gasoline&rdquo;, <i>Short-Term Energy Outlook</i> special analysis, February 2000 (revised March 2000), <a href="https://www.eia.gov/outlooks/steo/special/pdf/mtbe.pdf">PDF</a>.',
         'MTBE use growing in the 1980s after lead; demand of 83,000 b/d in 1990 and 161,000 b/d in 1994; 269,000 b/d in gasoline by 1997; the oxygen programmes as the cause of the growth.'),
        ("The annual average reaches its peak in",
         'U.S. Energy Information Administration, U.S. refinery and blender net input of MTBE (MMTRIUS1), monthly, fetched 7 November 2026.',
         'MTBE use by month, 1993 to 2016: the winter peaks, the 1994-95 increase, the 1999 annual peak and the 2006 collapse.'),
        ("turpentine-like taste and smell",
         'U.S. Environmental Protection Agency, &ldquo;Methyl Tertiary Butyl Ether (MTBE): Drinking Water&rdquo;, <a href="https://archive.epa.gov/mtbe/web/html/water.html">archived web page</a>.',
         'The taste and smell of MTBE in water at about 20 to 40 parts per billion; the Santa Monica Charnock and Arcadia well fields, 1996, half of the city\'s drinking water.'),
        ("times as often in high-use areas",
         'M. J. Moran, J. S. Zogorski and P. J. Squillace, <i>Occurrence and implications of methyl tert-butyl ether and gasoline hydrocarbons in ground water and source water in the United States and in drinking water in 12 Northeast and Mid-Atlantic states, 1993&ndash;2002</i>, U.S. Geological Survey Water-Resources Investigations Report 03-4200, 2004, <a href="https://pubs.usgs.gov/wri/wri034200/">pubs.usgs.gov</a>.',
         'Detection ratios of 4.9 to 7.5 between areas of high and low MTBE use; the population-density caveat; low concentrations in most detections.'),
        ("EPA's list of state actions gives",
         'U.S. Environmental Protection Agency, <i>State Actions Banning MTBE (Statewide)</i>, EPA420-B-07-013, August 2007, <a href="http://web.archive.org/web/2009id_/http://www.epa.gov/mtbe/420b07013.pdf">archived copy</a>.',
         "The 25 states with a partial or complete ban, seven of them complete; their phaseout dates; California's 1999 executive order."),
        ("EIA described the bans as a response to water contamination",
         'U.S. Energy Information Administration, &ldquo;Eliminating MTBE in Gasoline in 2006&rdquo;, 22 February 2006, <a href="https://www.eia.gov/petroleum/archive/mtbe2006.pdf">PDF</a>.',
         'State bans due to water contamination concerns; refiners\' reasons for removing MTBE in 2006; about 130 thousand barrels a day of ethanol needed to replace it.'),
        ("Water suppliers sued the oil companies that made and sold MTBE",
         'U.S. Environmental Protection Agency, <i>Regulatory Determinations Support Document for Selected Contaminants from the Second Drinking Water Contaminant Candidate List</i>, chapter 13, MTBE, 2008, <a href="https://www.epa.gov/sites/default/files/2014-09/documents/chapter_13_mtbe.pdf">PDF</a>.',
         'Lawsuits by water suppliers against gasoline manufacturers and distributors.'),
        ("ethanol stood to lose much of its market in reformulated gasoline",
         'Congressional Research Service, <i>MTBE in Gasoline: Clean Air and Drinking Water Issues</i>, RL32787, 2006, <a href="https://www.everycrsreport.com/reports/RL32787.html">everycrsreport.com</a>; and <i>Fuel Ethanol: Background and Public Policy Issues</i>, RL30369, July 2002.',
         'The ethanol market at stake in the oxygen requirement; the bills of 2000 to 2005; the 2003 failure largely over the MTBE liability safe harbor.'),
        ("He described the waiver as",
         'Senator Tom Daschle, introduction of S. 2503, the Renewable Fuels Act of 2000, <i>Congressional Record</i>, 4 May 2000, S3514, <a href="https://www.congress.gov/106/crec/2000/05/04/146/54/modified/CREC-2000-05-04-pt1-PgS3514-2.htm">congress.gov</a>.',
         'MTBE in groundwater as an unanticipated development; state waivers of the oxygen rule as a trade for a renewable fuels standard.'),
        ("billion in 2012",
         'Energy Policy Act of 2005, Public Law 109-58, sections 1501 and 1504, 8 August 2005, <a href="https://www.govinfo.gov/content/pkg/PLAW-109publ58/html/PLAW-109publ58.htm">govinfo.gov</a>.',
         'The renewable fuel volumes for 2006 to 2012; the end of the oxygen requirement for reformulated gasoline, with its toxics reductions kept.'),
        ("The national requirement ended on",
         'U.S. Environmental Protection Agency, &ldquo;Regulation of Fuels and Fuel Additives: Removal of Reformulated Gasoline Oxygen Content Requirement&rdquo;, final rule, 71 FR 26691, 8 May 2006, <a href="https://www.govinfo.gov/content/pkg/FR-2006-05-08/pdf/06-4252.pdf">PDF</a>.',
         'The effective date, 5 May 2006.'),
        ("A 1978 law exempted ethanol blends from the federal gasoline tax",
         'Energy Tax Act of 1978, Public Law 95-618, section 221, 92 Stat. 3174, <a href="https://www.govinfo.gov/content/pkg/STATUTE-92/pdf/STATUTE-92-Pg3174.pdf">govinfo.gov</a>.',
         'The exemption of alcohol fuel blends from the federal motor fuels excise tax.'),
        ("a federal appeals court struck the rule down in 1995",
         '<i>American Petroleum Institute v. Environmental Protection Agency</i>, 52 F.3d 1113 (D.C. Cir. 1995).',
         "EPA's 1994 renewable oxygenate requirement (30 percent of the oxygen in reformulated gasoline) and the court's decision against it."),
        ("took effect only in September 2007",
         'U.S. Environmental Protection Agency, &ldquo;Regulation of Fuels and Fuel Additives: Renewable Fuel Standard Program&rdquo;, final rule, 72 FR 23900, 1 May 2007, <a href="https://www.federalregister.gov/documents/2007/05/01/E7-7140">federalregister.gov</a>.',
         'The start of the full renewable fuel standard rules, 1 September 2007.'),
        ("Energy Independence and Security Act of 2007",
         'Energy Independence and Security Act of 2007, Public Law 110-140, section 202, <a href="https://www.govinfo.gov/content/pkg/PLAW-110publ140/html/PLAW-110publ140.htm">govinfo.gov</a>.',
         'The expanded renewable fuel standard: 36 billion gallons by 2022, of which up to 15 billion conventional.'),
        ("Most U.S. gasoline is now E10",
         'U.S. Energy Information Administration, &ldquo;How much ethanol is in gasoline, and how does it affect fuel economy?&rdquo;, <a href="https://www.eia.gov/tools/faqs/faq.php?id=27&amp;t=10">FAQ</a>.',
         'Most finished motor gasoline sold in the United States is E10, about 10 percent ethanol.'),
        ("upgraded, replaced or closed by the end of 1998",
         'U.S. Environmental Protection Agency, 40 CFR 280.21, &ldquo;Upgrading of existing UST systems&rdquo; (rule of 23 September 1988), <a href="https://www.govinfo.gov/content/pkg/CFR-2014-title40-vol27/xml/CFR-2014-title40-vol27-sec280-21.xml">govinfo.gov</a>.',
         'The deadline of 22 December 1998 for upgrading existing underground storage tanks.'),
        ("National Research Council committee found in 1999",
         'National Research Council, <i>Ozone-Forming Potential of Reformulated Gasoline</i>, National Academy Press, 1999, <a href="https://www.nationalacademies.org/read/9461/chapter/2">Summary</a>.',
         'Oxygenates in reformulated gasoline have little impact on ozone air quality.'),
        ("did not measurably improve ozone",
         'M. Auffhammer and R. Kellogg, &ldquo;Clearing the Air? The Effects of Gasoline Content Regulation on Air Quality&rdquo;, <i>American Economic Review</i> 101(6), 2011, 2687&ndash;2722, <a href="https://doi.org/10.1257/aer.101.6.2687">doi.org</a>.',
         "Federal gasoline content standards did not improve air quality; California's targeted rules did."),
        ("One study of the 2007 expansion of the mandate estimated",
         'T. J. Lark and others, &ldquo;Environmental outcomes of the US Renewable Fuel Standard&rdquo;, <i>Proceedings of the National Academy of Sciences</i> 119(9), 2022, e2101084119, <a href="https://doi.org/10.1073/pnas.2101084119">doi.org</a>.',
         'Corn prices about 30 percent higher and cropland about 2.1 million hectares larger, 2008 to 2016; carbon intensity no less than gasoline and likely at least 24 percent higher (estimates).'),
        ("its authors replied that the critique was unsupported",
         'T. J. Lark and others, &ldquo;Reply to Taheripour et al.: Comments on &lsquo;Environmental Outcomes of the US Renewable Fuel Standard&rsquo;&rdquo;, 7 April 2022, <a href="https://www.gibbs-lab.wisc.edu/assets/Reply-to-Taheripour-et-al.pdf">PDF</a>.',
         "Taheripour and others' comments that the study overestimated corn ethanol's emissions, and the authors' reply."),
        ("Ethanol use is EIA's fuel ethanol consumption",
         'U.S. Energy Information Administration, <i>Monthly Energy Review</i>, Table 10.3, Fuel Ethanol Overview (ENTCPUS), fetched 7 November 2026.',
         'Fuel ethanol use by month and year, and its share of gasoline.'),
        ("The corn share is USDA's corn use for fuel alcohol",
         'U.S. Department of Agriculture, Economic Research Service, Feed Grains Database, yearbook tables 4 and 31, fetched 7 November 2026.',
         'Corn production and corn used for fuel alcohol by marketing year.'),
        ("returns as distillers' grains for animal feed",
         "L. Hoffman and A. Baker, <i>Estimating the Substitution of Distillers' Grains for Corn and Soybean Meal in the U.S. Feed Complex</i>, FDS-11I01, USDA Economic Research Service, October 2011, <a href=\"https://www.ers.usda.gov/media/9423/fds-11i01.pdf\">PDF</a>.",
         "Dry-mill ethanol yields distillers' grains equal to about a third of the corn's weight."),
    ],
    "uri.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("order for one utility describes",
         'Oklahoma Corporation Commission, Final Financing Order No. 723435, Cause No. PUD 202100087 '
         '(CenterPoint Energy Resources Corp., now Summit Utilities Oklahoma), 10 February 2022.',
         "The price rise from February 12, 2021; extreme purchase costs of $75,678,535 incurred February 7 "
         "to 21, 2021; allocation by February 2021 usage; the fixed-price and LIHEAP exclusions."),
        ("the Commission found for Oklahoma Natural Gas",
         'Oklahoma Corporation Commission, Final Financing Order No. 723033, Cause No. PUD 202100079 '
         '(Oklahoma Natural Gas Company), 25 January 2022.',
         "Bills in excess of $1,000 without the order; extreme purchase costs of $1,284,101,405 incurred "
         "February 11 to 19, 2021; allocation by February 2021 usage; the fixed-price and LIHEAP exclusions."),
        ("under laws both states passed in 2021",
         'Texas Utilities Code, Chapter 104, Subchapter I (House Bill 1520, 87th Legislature, 2021); '
         'Oklahoma Senate Bill 1050 (2021), the February 2021 Regulated Utility Consumer Protection Act, '
         '74 O.S. ss.9070-9081.',
         "The securitization laws; s.104.373(a), the uniform monthly volumetric charge on all current and "
         "future customers."),
        ("the issuer's report",
         'Texas Natural Gas Securitization Finance Corporation, <i>Report of Outstanding Bonds and Estimated '
         'Administrative Expenses</i>, prepared 28 January 2026.',
         "Balances at 31 December 2025 (A-1 $1,519,264,998; A-2 $1,707,285,000) and the 2026 administrative "
         "expense estimate."),
        ("its servicer's certificate",
         "Summit Utilities Oklahoma, Servicer's Certificate, Oklahoma Development Finance Authority "
         'Ratepayer-Backed Bonds (Summit Utilities Oklahoma) Series 2022, 24 September 2026, as posted by the '
         'Oklahoma Corporation Commission.',
         "The balance after the October 1, 2026 payment, $67,526,998.31, equal to the expected schedule."),
        ("Three bond issues carry the costs",
         'Texas Natural Gas Securitization Finance Corporation, <i>Customer Rate Relief Bonds (Winter Storm '
         'Uri), Taxable Series 2023</i>, Official Statement, 9 March 2023.',
         "Principal, tranches, coupons, the 30/360 basis and payment dates, the expected amortization "
         "schedule, the uses of proceeds (including six months of capitalized interest and the reserve), the "
         "regulatory asset amounts, the charge at $0.00 through September 2023, SB 30 and HB 500, and the "
         "background quoted."),
        ("Issuance Advice Letters",
         'Oklahoma Natural Gas Company and Oklahoma Development Finance Authority, Issuance Advice Letter, '
         '23 August 2022; Summit Utilities Oklahoma and ODFA, Issuance Advice Letter, October 2022; both filed '
         'with the Oklahoma Corporation Commission.',
         "Final terms, tranches and coupons, expected sinking fund schedules, issuance and ongoing costs, the "
         "reserve subaccounts, the initial charges by class and their workpapers."),
        ("in the 2026 true-up",
         'Oklahoma Natural Gas Company, WESCR true-up letter and workpapers, 2 March 2026; Summit Utilities '
         'Oklahoma, WESCRM true-up letter, 27 March 2026.',
         "The charges by class from May 2026, Oklahoma Natural Gas's estimates from November 2026, and its "
         "re-set allocation shares."),
        ("it is reset at least once a year",
         'Railroad Commission of Texas, announcement of 4 October 2023; RRC gas tariff reports GSD-1 for '
         'Atmos Energy Mid-Tex (6776), CenterPoint Energy Entex (6263) and Atmos Energy West Texas (6931), '
         '20 October 2026; Atmos Energy Mid-Tex tariffs effective 1 July 2025; Texas Gas Service rate '
         'schedule CRR.',
         "The charge's rates: $1.10 per Mcf from October 2023, $0.1180, $0.120 and $0.113 per Ccf since; "
         "$0.11362 at 14.73 psia; sales customers; the West Texas division's filed $0.2140."),
        ("Texas Gas Service says its average home",
         'Texas Gas Service, <i>Securitization</i> (texasgasservice.com/Securitization), read 24 October 2026.',
         "$1.13 per Mcf and about $3.96 a month for the average residential customer."),
        ("EIA's residential consumption per residential consumer",
         'U.S. Energy Information Administration, natural gas series for Texas and Oklahoma: residential '
         'consumption (N3010TX2, N3010OK2) and number of residential consumers (NA1501_STX_8, NA1501_SOK_8), '
         'annual; and <i>Glossary</i>, letter C.',
         "Gas used per home in Texas and Oklahoma, 2015 to 2024; and EIA's glossary, \"Cubic foot (cf), natural "
         "gas\": 60 degrees Fahrenheit and 14.73 pounds per square inch."),
        ("which a separate law covers",
         'Oklahoma Senate Bill 1049 (2021), the February 2021 Unregulated Utility Consumer Protection Act.',
         "The separate provision for utilities whose rates the Commission does not set."),
    ],
    # "meter.html" was here until 2026-10-23 (R3): the page is now a redirect stub to
    # lostgas.html, whose own entry above cites what its appendix keeps of the meter
    # work. The full list is in git history (git show 0dec34e:add_citations.py).
    "climate-cost.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("published literature",
         'Poore &amp; Nemecek, <i>Science</i> 360:987, 2018 - reducing food’s '
         'environmental impacts through producers and consumers.',
         "Per-kilogram footprints and the spread within each food."),
        # R5 (2026-10-24): climate-cost/update_page.py applies this entry
        # itself. The GWP entry cites the corrected table (errata of 7 October
        # 2025, opened that day; SOURCES); "methane" anchored it until the
        # rework, and the word now first appears in the standfirst's prose.
        ("fertiliser",
         'IPCC, <i>2019 Refinement to the 2006 Guidelines for National '
         'Greenhouse Gas Inventories</i>, Volume 4 Chapter 11 - direct and '
         'indirect nitrous oxide from managed soils, Tables 11.1 and 11.3.',
         "How much nitrous oxide nitrogen on a field gives off: 1% of it "
         "directly, plus 1% of the 11% that drifts off as gas and 1.1% of the "
         "24% that washes away (the wet-climate default)."),
        ("over a century",
         'IPCC, <i>Sixth Assessment Report</i>, Working Group I Chapter 7, '
         'Table 7.15 - global warming potentials, as corrected by the '
         '<a href="https://www.ipcc.ch/report/ar6/wg1/about/errata/">Working '
         'Group I errata</a> of 7 October 2025.',
         "Methane at 25.3 (non-fossil) and 28.1 (fossil) and nitrous oxide at "
         "267 over a century; the table first read 27.0, 29.8 and 273."),
        ("tonne-kilometer",
         'UK Department for Energy Security and Net Zero, <i>Greenhouse gas '
         'reporting: conversion factors</i>, 2023.',
         "Freight emission factors by mode."),
        ("allocation standard",
         'ISO 14044:2006, <i>Environmental management - Life cycle assessment '
         '- Requirements and guidelines</i>, clause 4.3.4.',
         "The allocation hierarchy: avoid, then physical, then economic."),
        ("Flysjö",
         'Flysjö, Cederberg, Henriksson &amp; Ledgard, <i>International '
         'Journal of Life Cycle Assessment</i> 16:420, 2011 - how does '
         'co-product handling affect the carbon footprint of milk? Table 1.',
         "Milk-to-meat allocation by physical (85-86%), economic (88-92%), "
         "protein (93-94%) and mass (98%) bases, and 63-76% by system "
         "expansion."),
        ("International Dairy Federation",
         'International Dairy Federation, <i>A common carbon footprint '
         'approach for the dairy sector</i>, Bulletin 479, 2015, pp. 34-36.',
         "The physical formula for a dairy cow's milk share (1 minus 6.04 "
         "times the ratio of beef to milk the farm sells) and its 88% default "
         "(read through secondary sources; the bulletin is not open access)."),
        ("Lunesu",
         'Lunesu, Correddu, Carta, Sechi, Farina &amp; Pulina, <i>Animals</i> '
         '15:3546, 2025 - attributing farm-to-slaughter emissions to hides.',
         "Hide share of the animal: 2.7% by economic allocation (2023 mean), "
         "5.9% by live weight (range 4.2-6.9%)."),
    ],
    # takeaway/update_page.py applies this entry itself (meter/update_page.py's
    # idiom), so the page's generator and this table cannot disagree.
    "takeaway.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("basin's three districts",
         'Railroad Commission of Texas, <i>Permian Basin Information</i> and its '
         'workbook <i>Permian Basin 2008 To Current</i> (production by month, '
         'from the Production Data Query).',
         "The Permian as districts 7C, 08 and 8A; gas from oil wells "
         "(casinghead) and from gas wells, by month."),
        ("may have reached capacity",
         'Railroad Commission of Texas, <i>Flaring Regulation</i> (Oil and Gas '
         'FAQ).',
         "Statewide Rule 32, and that flaring may be needed where existing "
         "pipelines have reached capacity."),
        ("Natural Gas Intelligence data",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '3 February 2025, "Natural gas spot prices fell across key regional '
         'trading hubs in 2024".',
         "Waha below zero on 42% of trading days in 2024 (Natural Gas "
         "Intelligence data), and Matterhorn Express entering service in "
         "October 2024."),
        ("which EIA counted as takeaway in 2021",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, 2 June '
         '2022, "Natural gas production in the Permian Basin reached an annual '
         'high in 2021".',
         "Three pipelines, Double E among them, as 5.5 Bcf/d of takeaway "
         "capacity that came online in 2021."),
        ("began taking gas",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '6 September 2019, "Permian Basin natural gas prices up as a new '
         'pipeline nears completion".',
         "Limited takeaway kept Waha prices very low or negative in the months "
         "before Gulf Coast Express; deliveries into it began on 8 August 2019."),
        ("EIA's project tracker",
         'U.S. Energy Information Administration, <i>Natural Gas Pipeline '
         'Projects</i> tracker, August 2026 edition.',
         "Each line's capacity, status and, where it gives one, completion "
         "date or expected year."),
        ("Where a newer report gives a date",
         'Pipeline &amp; Gas Journal, 23 July 2026 (Kinder Morgan second-quarter '
         'results); BIC Magazine, 5 August 2026 (Hugh Brinson Pipeline); '
         'Enbridge, 6 August 2026 (Blackcomb Pipeline commissioning); '
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '26 May 2026 (planned capacity additions in 2026 and 2027).',
         "The in-service and expected dates the table attributes to each; "
         "Enbridge for Blackcomb's commissioning, which the page does not count "
         "as service."),
        ("Table 5a, series NGMPPM",
         'U.S. Energy Information Administration, <i>Short-Term Energy '
         'Outlook</i>, October 2026, data tables (STEO_m.xlsx).',
         "Marketed natural gas production, Permian region, monthly (Table 5a); "
         "shale gas production by formation (Table 10b)."),
        ("drawn by county",
         'U.S. Energy Information Administration, <i>Drilling Productivity '
         'Report</i>, its methodology (August 2014) and data workbook (May '
         '2024, RegionCounties sheet).',
         "The Permian region's counties, and that the regions follow county "
         "lines rather than geology."),
        ("EIA gives both by state",
         'U.S. Energy Information Administration, natural gas gross withdrawals '
         'and production, and consumption by end use, Texas and New Mexico, '
         'annual; and the definitions for those tables.',
         "Marketed and dry production, lease and plant fuel; marketed "
         "production includes gas used in field and plant operations; plant "
         "liquids are reported by state of origin."),
        ("every day since July 26",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '10 September 2024, "Natural gas pipeline capacity from the Permian '
         'Basin is set to increase".',
         "Waha below zero every day since 26 July 2024, and Matterhorn Express "
         "expected to begin service in September 2024."),
        # Q2, 2026-10-20: the dump replaced EIA's statewide monthly series
        # (anchor "from state agency data") once its host answered.
        ("Production Data Query dump",
         'Railroad Commission of Texas, <i>Production Data Query</i> dump '
         '(PDQ_DSV.zip, extract of 18 September 2026) and its user manual; and '
         'Form PR, <i>Monthly Production Report, Disposition Codes</i> '
         '(OG-2014-001A).',
         "Gas vented or flared (casinghead and gas-well disposition code 4, "
         "\"Vented or flared\") and production, by lease, district and month."),
        ("shut-ins of 2020",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '9 March 2021 (republished 22 December 2021), "U.S. crude oil production '
         'fell by 8% in 2020".',
         "Operators shut in wells as crude prices fell from March 2020."),
        ("February 2021 winter storm",
         'U.S. Energy Information Administration, <i>Today in Energy</i>, '
         '10 May 2021, "February 2021 weather triggers largest monthly '
         'decline in U.S. natural gas production".',
         "Texas gas production fell by a record 4.3 Bcf/d in February 2021, "
         "mostly from freeze-offs."),
        ("spring maintenance",
         'Reuters, in Pipeline &amp; Gas Journal, 28 May 2026, "Waha gas prices '
         'hit 16-week high as Permian pipeline constraints ease".',
         "Waha daily prices below zero 49 times in 2024, 39 in 2025 and 87 in "
         "2026 to date, and a record 78-day run below zero attributed to "
         "spring maintenance."),
    ],
    # Who gets an unemployment check (safety-nets lane, 2026-11-07). safetynet/update_page.py applies this
    # entry itself (ethane's idiom). Every document was fetched into safetynet/data/raw/ (fetched.json); the
    # figures the page takes from the papers and reports are matched in their text at render time.
    "safetynet.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("calls this ratio the recipiency rate",
         'U.S. Department of Labor, Employment and Training Administration, <i>Unemployment Insurance Chartbook</i>, chart A.12 (United States, 1950 on) and chart A.13 (states, 1976 on), insured unemployment in regular programs as a percentage of total unemployment, fetched 7 November 2026.',
         'Every national figure from 1950 and every state figure from 1976 to the year before the latest.'),
        ("monthly ETA 5159 reports",
         'U.S. Department of Labor, Employment and Training Administration, ETA 5159 Claims and Payment Activities, monthly by state (ar5159.csv), fetched 7 November 2026; definitions in ET Handbook 401, 5th edition, and the column map in ET Handbook 402 (UI data map, ar5159).',
         'State UI continued weeks claimed (columns c21 and c22), from which the page reproduces DOL&rsquo;s figures and computes the latest year.'),
        ("Local Area Unemployment Statistics for a state",
         'U.S. Bureau of Labor Statistics, Current Population Survey (LNU03000000, LNU03023621, LNU03023653) and Local Area Unemployment Statistics (statewide unemployed, not seasonally adjusted), monthly, public API v1, fetched 7 November 2026.',
         'The unemployed, nationally and by state, and the unemployed by reason.'),
        ("during the lapse in federal appropriations",
         'U.S. Bureau of Labor Statistics, <i>Labor Force Statistics from the Current Population Survey</i>, table 1, Employment status of the civilian noninstitutional population, 1955 to date, notes on 2025 annual averages and on historical comparability.',
         'Annual estimates for 2025 are 11-month averages that exclude October, for which no data were collected.'),
        ("A count in a Federal Reserve Bank of Minneapolis study",
         'Juliet Cramer and Ryan Nunn, &ldquo;Understanding Eligibility and Take-Up in State Unemployment Insurance Programs&rdquo;, Federal Reserve Bank of Minneapolis, Community Development Working Paper, January 2026.',
         'States paying 12 weeks or fewer than 26 as of spring 2025; estimated eligibility of 46.1% of the unemployed in 2024; its 5.4-point fall since 2000 and the parts due to maximum weeks (2.6) and composition (2.1).'),
        ("Gordon Dahl and Matthew Knepper",
         'Gordon B. Dahl and Matthew M. Knepper, &ldquo;Unemployment Insurance, Starting Salaries, and Jobs&rdquo;, NBER Working Paper 30152, June 2022.',
         "The seven states that cut maximum weeks; North Carolina's 2013 cuts, their size and the insolvency behind them; short-term recipiency falling from 30% to 10%; Florida's 12 to 23 weeks from January 2012 (table 1, note 2); employment growth and starting salaries within multi-state firms."),
        ("In a BLS survey in 2022",
         'U.S. Bureau of Labor Statistics, &ldquo;Characteristics of Unemployment Insurance Applicants and Benefit Recipients &ndash; 2022&rdquo;, news release USDL-23-0586, 29 March 2023.',
         'Shares of the unemployed who applied, of applicants who received benefits, and of non-applicants who thought they were ineligible.'),
        ("Rebecca Blank and David Card found",
         'Rebecca M. Blank and David Card, &ldquo;Recent Trends in Insured and Uninsured Unemployment: Is There an Explanation?&rdquo;, NBER Working Paper 2871, 1989; <i>Quarterly Journal of Economics</i> 106(4), 1991.',
         'Take-up fell abruptly between 1980 and 1982, a 6-point fall in the share of the unemployed receiving benefits.'),
        ("population estimates for July",
         'U.S. Census Bureau, Vintage 2025 population estimates, states (NST-EST2025-ALLDATA).',
         'State populations, and the Census regions, for the share of residents in low states.'),
        ("where a rule gives longer benefits",
         'David Card, Raj Chetty and Andrea Weber, &ldquo;Cash-on-Hand and Competing Models of Intertemporal Behavior: New Evidence from the Labor Market&rdquo;, NBER Working Paper 12639, 2006; <i>Quarterly Journal of Economics</i> 122(4), 2007.',
         'An extension from 20 to 30 weeks lowers job-finding in the first 20 weeks by 5-9%.'),
        ("One group of economists credited",
         'Marcus Hagedorn, Iourii Manovskii and Kurt Mitman, &ldquo;The Impact of Unemployment Benefit Extensions on Employment: The 2014 Employment Miracle?&rdquo;, NBER Working Paper 20884, 2015; <i>American Economic Journal: Macroeconomics</i> 17(4), 2025.',
         '2.1 million people finding work in 2014 due to the end of the extensions.'),
        ("another study, using a different method",
         'Gabriel Chodorow-Reich, John Coglianese and Loukas Karabarbounis, &ldquo;The Macro Effects of Unemployment Benefit Extensions: A Measurement Error Approach&rdquo;, <i>Quarterly Journal of Economics</i> 134(1), 2019.',
         'Great Recession extensions raised the unemployment rate by at most 0.3 percentage point.'),
        ("recommended solvency standard",
         'U.S. Department of Labor, Employment and Training Administration, <i>State Unemployment Insurance Trust Fund Solvency Report 2026</i>, February 2026.',
         'UI taxes paid primarily by employers; states meeting the recommended minimum solvency standard on 1 January 2026 and at the start of 2020.'),
        ("Jonathan Gruber found",
         'Jonathan Gruber, &ldquo;The Consumption Smoothing Benefits of Unemployment Insurance&rdquo;, NBER Working Paper 4750, 1994; <i>American Economic Review</i> 87(1), 1997.',
         'The average 7% fall in food consumption on becoming unemployed (Panel Study of Income Dynamics, 1968-1987), and over three times as large without UI.'),
        ("Peter Ganong and Pascal Noel found",
         'Peter Ganong and Pascal Noel, &ldquo;Consumer Spending During Unemployment: Positive and Normative Implications&rdquo;, NBER Working Paper 25417, 2019; <i>American Economic Review</i> 109(7), 2019.',
         'Spending drops sharply at benefit exhaustion.'),
    ],
    # Lane lost-einsteins, 2026-11-07: the lead page (lead/update_page.py applies this table itself).
    "lead.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("McFarland, Hauer and Reuben estimated",
         'McFarland MJ, Hauer ME, Reuben A. &ldquo;Half of US population exposed to adverse lead levels in early '
         'childhood&rdquo;. <i>Proceedings of the National Academy of Sciences</i> 119(11):e2118631119, 2022, with '
         'Supporting Information Datasets S01 and S03. CC BY-NC-ND 4.0.',
         'Blood-lead bands by birth year and calendar year, 1940 on; gasoline as the dominant source from the 1940s '
         'to the late 1980s; the IQ loss per band; the total, the per-person figure and the cohort means the build '
         'reproduces.'),
        ("recorded each year how much lead American factories used",
         'U.S. Bureau of Mines, <i>Minerals Yearbook</i>, chapter &ldquo;Lead&rdquo;, editions of 1945 to 1991, table '
         'of lead consumption by product (row &ldquo;tetraethyl lead&rdquo;, later &ldquo;gasoline antiknock '
         'additives&rdquo; and &ldquo;gasoline additives&rdquo;), read from the Internet Archive&rsquo;s copies.',
         'Lead used to make the gasoline additive, 1941 to 1991; Department of Commerce estimates for 1987 to '
         '1991.'),
        ("issued its first limits on lead in gasoline in 1973",
         'U.S. Environmental Protection Agency, &ldquo;EPA takes final step in phaseout of leaded gasoline&rdquo;, '
         'press release, 29 January 1996.',
         'First standards in 1973; catalytic converters needing lead-free fuel from 1975; 0.1 gram a gallon by '
         '1986; the ban for road vehicles from 1 January 1996.'),
        ("about 2.3 grams in the late 1960s",
         'U.S. General Accounting Office, <i>Air Pollution: EPA&rsquo;s Efforts To Reduce and End the Use of Lead in '
         'Gasoline</i>, GAO/RCED-86-80FS, March 1986.',
         'About 2.3 grams per leaded gallon in the late 1960s and early 1970s; the 0.10 gram standard.'),
        ("as tabulated by EPA in America's Children and the Environment",
         'U.S. Environmental Protection Agency, <i>America&rsquo;s Children and the Environment</i>, Biomonitoring: '
         'Lead, indicator B1, from CDC&rsquo;s National Health and Nutrition Examination Survey, 1976 to March 2020.',
         'Median and 95th percentile blood lead of children aged one to five, by survey period.'),
        ("used 5 µg/dL as its reference value",
         'Ruckart PZ, Jones RL, Courtney JG, et al. &ldquo;Update of the blood lead reference value &mdash; United '
         'States, 2021&rdquo;. <i>MMWR</i> 70(43):1509&ndash;1512, 2021.',
         'The reference value of 5 &micro;g/dL adopted in 2012 and lowered to 3.5 &micro;g/dL in 2021.'),
        ("A commentary on the paper in the same journal",
         'Sampson RJ. &ldquo;Legacies of inequality, legacy lead exposures, and improving population '
         'well-being&rdquo;. <i>Proceedings of the National Academy of Sciences</i> 119(14):e2202401119, 2022.',
         'Estimates built on gasoline alone are likely to understate exposure from paint, plumbing and industry.'),
        ("Lanphear and colleagues give",
         'Lanphear BP, Hornung R, Khoury J, et al. &ldquo;Low-level environmental lead exposure and children&rsquo;s '
         'intellectual function: an international pooled analysis&rdquo;. <i>Environmental Health Perspectives</i> '
         '113(7):894&ndash;899, 2005.',
         'The log-linear slopes, 2.70 IQ points per natural-log unit of blood lead at the IQ test and 2.04 for '
         'early-childhood blood lead, and the 5th percentiles of their data, 2.4 and 4.1 &micro;g/dL.'),
        ("the curve of Crump and colleagues",
         'Crump KS, Van Landingham C, Bowers TS, et al. &ldquo;A statistical reevaluation of the data used in the '
         'Lanphear et al. (2005) pooled-analysis that related low levels of blood lead to intellectual deficits in '
         'children&rdquo;. <i>Critical Reviews in Toxicology</i> 43(9):785&ndash;799, 2013.',
         'The no-threshold function, as applied by Larsen and S&aacute;nchez-Triana with a slope of 3.246.'),
        ("Larsen and Sánchez-Triana estimated",
         'Larsen B, S&aacute;nchez-Triana E. &ldquo;Global health burden and cost of lead exposure in children and '
         'adults: a health impact and economic modelling analysis&rdquo;. <i>The Lancet Planetary Health</i> '
         '7(10):e831&ndash;e840, 2023. CC BY 4.0.',
         'IQ points lost by children under five in 2019, worldwide, by income group and region; the mean loss per '
         'child over the first five years in low- and middle-income countries; the dose-response used.'),
        ("2024 review of the science",
         'U.S. Environmental Protection Agency, <i>Integrated Science Assessment for Lead</i>, final report, '
         'EPA/600/R-23/375, January 2024.',
         'The causal relationship between lead exposure and cognitive effects in children.'),
        ("In 2001, one review argued",
         'Kaufman AS. &ldquo;Do low levels of lead produce IQ loss in children? A careful examination of the '
         'literature&rdquo;. <i>Archives of Clinical Neuropsychology</i> 16(4):303&ndash;341, 2001.',
         'The argument that confounding by parental IQ and home environment may account for low-level '
         'associations.'),
        ("In Dunedin, New Zealand",
         'Reuben A, Caspi A, Belsky DW, et al. &ldquo;Association of childhood blood lead levels with cognitive '
         'function and socioeconomic status at age 38 years and with IQ change and socioeconomic mobility between '
         'childhood and adulthood&rdquo;. <i>JAMA</i> 317(12):1244&ndash;1251, 2017.',
         'Adult IQ 1.61 points lower for each 5 &micro;g/dL of blood lead at age 11, adjusted for maternal IQ, '
         'childhood IQ and childhood socioeconomic status.'),
        ("In Sweden, a study of the gasoline phase-out",
         'Gr&ouml;nqvist H, Nilsson JP, Robling P-O. &ldquo;Understanding how low levels of early lead exposure affect '
         'children&rsquo;s life trajectories&rdquo;. <i>Journal of Political Economy</i> 128(9):3376&ndash;3433, 2020.',
         'Effects of the phase-out on school grades, high-school completion and convictions; no consistent effect on '
         'the enlistment cognitive test; no significant effect on earnings measured at ages 29 to 40.'),
        ("according to a meta-analysis",
         'Trahan LH, Stuebing KK, Fletcher JM, Hiscock M. &ldquo;The Flynn effect: a meta-analysis&rdquo;. '
         '<i>Psychological Bulletin</i> 140(5):1332&ndash;1360, 2014.',
         'A mean rise of 2.31 IQ points per decade across 285 studies since 1951.'),
        ("Exposure was higher in poorer families",
         'Centers for Disease Control and Prevention. &ldquo;Blood lead levels in children aged 1&ndash;5 years '
         '&mdash; United States, 1999&ndash;2010&rdquo;. <i>MMWR</i> 62(13):245&ndash;248, 2013.',
         'Disparities in children&rsquo;s blood lead by income, race and age of housing.'),
    ],
}


def strip(t):
    """Remove any citations already present, so the script is re-runnable.

    The replacement is "" and not "\\n": build() inserts a block that both
    begins with a newline and ends with two, so a strip that put one back left
    the page one blank line longer on every pass. The script claimed to be
    re-runnable and was not - every page in PAGES gained a line each time it
    ran. Found 2026-09-05 when add_citations.py was first added to
    tests/test_generators.py; strip(build(x)) == x is what re-runnable means,
    and the test now holds it to that.
    """
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    t = re.sub(r'\n<h2>Sources</h2>.*?</ol>\n\n', "", t, flags=re.S)
    return t


def build(page, refs):
    path = os.path.join(SITE, page)
    if not os.path.exists(path):
        return None, [f"{page} does not exist"]
    t = strip(open(path, encoding="utf-8").read())

    problems = []
    body_end = t.find("<footer")
    if body_end < 0:
        return None, [f"{page} has no footer to insert before"]

    # Only the text between tags is eligible. Matching anywhere would let a
    # phrase inside an attribute collect a marker, which silently corrupts the
    # tag: the first version of this put a superscript inside a <meta
    # description> and the reference simply never appeared on the page.
    body = t[:body_end]
    spans = []
    depth_pos = 0
    for m in re.finditer(r"<[^>]*>", body):
        if m.start() > depth_pos:
            spans.append((depth_pos, m.start()))
        depth_pos = m.end()
    if depth_pos < len(body):
        spans.append((depth_pos, len(body)))

    # ...and only inside <main>, so nothing in the nav or head is annotated.
    # "<main", not "<main>": the deslop pass gave <main> a class, and an exact
    # match then failed silently, which let the nav become eligible for markers.
    main_at = t.find("<main")
    spans = [(a, b) for a, b in spans if main_at < 0 or a >= main_at]

    # ...and not inside a marginalia aside. The margin list repeats phrases
    # from the prose - it is a summary of it - so an anchor can match there
    # first and the marker lands in the margin, where a superscript pointing
    # at a reference list makes no sense and the numbering after it shifts.
    # longevity.html's "ocean quahog" did exactly that: the phrase appears in
    # the aside at 4,666 and in the prose at 12,720, and the aside won.
    asides = [(m.start(), m.end()) for m in re.finditer(r"<aside\b.*?</aside>", body, re.S)]
    if asides:
        spans = [(a, b) for a, b in spans
                 if not any(x <= a and b <= y for x, y in asides)]

    def find_in_text(phrase):
        pat = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")
        for a, b in spans:
            m = pat.search(body, a, b)
            if m:
                return m.end()
        return None

    # Number by where they appear, not by the order they sit in this file. A
    # reader meeting marker 5 before marker 2 assumes something is broken, and
    # they are right to: numbered references run in order of first appearance.
    found = []
    for phrase, src, what in refs[1:]:
        pos = find_in_text(phrase)
        if pos is None:
            problems.append(f"{page}: phrase not found in prose - {phrase!r}")
            continue
        found.append({"pos": pos, "src": src, "what": what,
                      "phrase": phrase})
    found.sort(key=lambda f: f["pos"])
    for i, f in enumerate(found, 1):
        f["n"] = i

    # Insert from the back so earlier offsets stay valid.
    for f in sorted(found, key=lambda f: -f["pos"]):
        marker = (f'<sup class="cite" id="cr{f["n"]}">'
                  f'<a href="#ref{f["n"]}">{f["n"]}</a></sup>')
        t = t[:f["pos"]] + marker + t[f["pos"]:]

    body_end = t.find("<footer")
    items = "".join(
        f'<li id="ref{f["n"]}"><span class="src">{f["src"]}</span>'
        f'<span class="what">{f["what"]}</span></li>'
        for f in found)
    # NO STANDING LINE UNDER <h2>Sources</h2>, and this is deliberate.
    # There was one until 2026-09-09: "Numbered markers in the text above
    # point here. Emission factors, cost ranges and lifespan figures are
    # representative values from these sources, not measurements made for
    # this project." It was written for climate-cost.html, where every
    # word of it is true, and then emitted verbatim on all eight pages
    # carrying a Sources list. On beauty.html it promised emission factors
    # under a list of ornithology papers; on continents.html, under
    # plate-motion models; on shoes.html, under running trials.
    #
    # One page's sentence became eight pages' boilerplate because the
    # block is generated in one place - the same property that makes the
    # rest of this script worth having. The rule is narrow: a generator
    # may emit STRUCTURE for every page and may not emit a CLAIM, because
    # a claim is about a particular page's sources and this script does
    # not know what they are. A page that needs to say what its sources
    # are for says it in its own prose, where it can be checked.
    block = (f'\n<h2>Sources</h2>\n'
             f'<ol class="refs">{items}</ol>\n\n')
    t = t[:body_end] + block + t[body_end:]
    return t, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    allprob, done = [], 0
    for page, refs in PAGES.items():
        out, probs = build(page, refs)
        allprob += probs
        if out is None:
            continue
        placed = out.count('class="cite"')
        print(f"  {page:22s} {placed} of {len(refs)-1} markers placed")
        if a.apply:
            open(os.path.join(SITE, page), "w", encoding="utf-8", newline="\n").write(out)
            done += 1

    if allprob:
        print("\n  problems:")
        for p in allprob:
            print(f"    {p}")
    if a.apply:
        print(f"\n  wrote {done} page(s)")
    else:
        print("\n  report only. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
