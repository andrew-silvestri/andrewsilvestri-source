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
         'An oxygen-rich atmosphere lasts about 1.08 &plusmn; 0.14 billion years more, and less than 1.5; this page uses about 1 and draws 0.8 to 1.5.'),
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
        ('one reading of the genes puts the origin',
         'Shih, P. M., Hemp, J., Ward, L. M., Matzke, N. J. &amp; Fischer, W. W. (2017). Crown group Oxyphotobacteria postdate the rise of oxygen. <i>Geobiology</i> 15, 19&ndash;29, <a href="https://doi.org/10.1111/gbi.12200">doi:10.1111/gbi.12200</a>.',
         'On this reading, an origin of oxygenic photosynthesis no earlier than about 2.5 to 2.6 billion years ago.'),
        ('Oxygen built up in the air from',
         'Poulton, S. W. et al. (2021). A 200-million-year delay in permanent atmospheric oxygenation. <i>Nature</i> 592, 232&ndash;236, <a href="https://doi.org/10.1038/s41586-021-03393-7">doi:10.1038/s41586-021-03393-7</a>; Gumsley, A. P. et al. (2017). Timing and tempo of the Great Oxidation Event. <i>PNAS</i> 114, 1811&ndash;1816, <a href="https://doi.org/10.1073/pnas.1608824114">doi:10.1073/pnas.1608824114</a>.',
         'The Great Oxidation Event from about 2.43 billion years ago, permanent by about 2.22.'),
        ('when one microbe came to live inside another',
         'Roger, A. J., Mu&ntilde;oz-G&oacute;mez, S. A. &amp; Kamikawa, R. (2017). The origin and diversification of mitochondria. <i>Current Biology</i> 27, R1177&ndash;R1192, <a href="https://doi.org/10.1016/j.cub.2017.09.015">doi:10.1016/j.cub.2017.09.015</a>.',
         'A single origin of mitochondria and of the eukaryotic cell.'),
        ('are from North China',
         'Miao, L. et al. (2024). 1.63-billion-year-old multicellular eukaryotes from the Chuanlinggou Formation in North China. <i>Science Advances</i> 10, eadk3208, <a href="https://doi.org/10.1126/sciadv.adk3208">doi:10.1126/sciadv.adk3208</a>; Betts, H. C. et al. (2018). Integrated genomic and fossil evidence illuminates life&rsquo;s early evolution and eukaryote origin. <i>Nature Ecology &amp; Evolution</i> 2, 1556&ndash;1562, <a href="https://doi.org/10.1038/s41559-018-0644-x">doi:10.1038/s41559-018-0644-x</a>.',
         'Single-celled eukaryote fossils about 1.65 billion years old in North China (and multicellular ones about 1.635); the last common ancestor of eukaryotes between 1.84 and 1.21 billion years ago.'),
        ('Large Ediacaran fossils at Mistaken Point',
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
         'Mayr, E. (1995). Can SETI succeed? Not likely. <i>Bioastronomy News</i> 7(3), in the debate with Carl Sagan; Spanish translation in Lemarchand, G. A. (ed.) (2010), <a href="https://arxiv.org/abs/1012.2591">arXiv:1012.2591</a>.',
         'Eyes and bioluminescence evolved many times; high intelligence once.'),
        ('Complex multicellular life, with specialized cells',
         'Knoll, A. H. (2011). The multiple origins of complex multicellularity. <i>Annual Review of Earth and Planetary Sciences</i> 39, 217&ndash;239, <a href="https://doi.org/10.1146/annurev.earth.031208.100209">doi:10.1146/annurev.earth.031208.100209</a>.',
         'Six origins of complex multicellularity: animals, land plants, florideophyte red algae, laminarialean brown algae (kelps) and two groups of fungi.'),
        ('Simple multicellularity evolved at least',
         'Grosberg, R. K. &amp; Strathmann, R. R. (2007). The evolution of multicellularity: a minor major transition? <i>Annual Review of Ecology, Evolution, and Systematics</i> 38, 621&ndash;654, <a href="https://doi.org/10.1146/annurev.ecolsys.36.102403.114735">doi:10.1146/annurev.ecolsys.36.102403.114735</a>.',
         'At least 25 origins of multicellularity.'),
        ('Farming began in at least',
         'Larson, G. et al. (2014). Current perspectives and the future of domestication studies. <i>PNAS</i> 111, 6139&ndash;6146, <a href="https://doi.org/10.1073/pnas.1323964111">doi:10.1073/pnas.1323964111</a>.',
         'At least 11 regions of independent domestication, from about 12,000 to 11,000 years ago.'),
        ('times among insects',
         'Mueller, U. G., Gerardo, N. M., Aanen, D. K., Six, D. L. &amp; Schultz, T. R. (2005). The evolution of agriculture in insects. <i>Annual Review of Ecology, Evolution, and Systematics</i> 36, 563&ndash;595, <a href="https://doi.org/10.1146/annurev.ecolsys.36.102003.152626">doi:10.1146/annurev.ecolsys.36.102003.152626</a>.',
         'Insect agriculture evolved once in ants, once in termites and seven times in ambrosia beetles.'),
        ('a 2012 analysis by David Spiegel and Edwin Turner',
         'Spiegel, D. S. &amp; Turner, E. L. (2012). Bayesian analysis of the astrobiological implications of life&rsquo;s early emergence on Earth. <i>PNAS</i> 109, 395&ndash;400, <a href="https://doi.org/10.1073/pnas.1111694108">doi:10.1073/pnas.1111694108</a>.',
         'Life&rsquo;s early start on Earth is consistent with a low probability of abiogenesis; the conclusion is dominated by the prior.'),
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
         'Mills, D. B., Macalady, J. L., Frank, A. &amp; Wright, J. T. (2025). A reassessment of the &ldquo;hard-steps&rdquo; model for the evolution of intelligent life. <i>Science Advances</i> 11(7), eads5698, <a href="https://doi.org/10.1126/sciadv.ads5698">doi:10.1126/sciadv.ads5698</a>; <a href="https://arxiv.org/abs/2408.10293">arXiv:2408.10293</a>.',
         'Steps gated by the environment, chiefly oxygen; eukaryotes and animals excluded for the first 52 percent of Earth&rsquo;s history; an account of the timing, not a falsification of the hard-steps model.'),
        ('In 2018 Anders Sandberg, Eric Drexler and Toby Ord',
         'Sandberg, A., Drexler, E. &amp; Ord, T. (2018). Dissolving the Fermi paradox. <a href="https://arxiv.org/abs/1806.02404">arXiv:1806.02404</a>.',
         'Table 1 parameter ranges; a 52 percent prior chance of fewer than one civilization in the galaxy; 53 to 99.6 percent after the Fermi observation.'),
        ('A 2015 search of about',
         'Griffith, R. L., Wright, J. T., Maldonado, J., Povich, M. S., Sigurdsson, S. &amp; Mullan, B. (2015). The &Gcirc; infrared search for extraterrestrial civilizations with large energy supplies. III. The reddest extended sources in WISE. <i>Astrophysical Journal Supplement Series</i> 217, 25, <a href="https://doi.org/10.1088/0067-0049/217/2/25">doi:10.1088/0067-0049/217/2/25</a>.',
         'About 100,000 galaxies; none reprocesses more than 85 percent of its starlight into mid-infrared heat.'),
        ('Breakthrough Listen observed',
         'Price, D. C. et al. (2020). The Breakthrough Listen search for intelligent life: observations of 1327 nearby stars over 1.10&ndash;3.45 GHz. <i>Astronomical Journal</i> 159, 86, <a href="https://doi.org/10.3847/1538-3881/ab65f1">doi:10.3847/1538-3881/ab65f1</a>.',
         'No candidate signals among 1,327 stars; for the 882 observed with the Green Bank Telescope at 1.1&ndash;1.9 GHz, fewer than 0.45 percent host a continuous narrowband transmitter above 2.1 &times; 10<sup>12</sup> W equivalent isotropic power (95 percent confidence).'),
        ("humanity's total energy supply",
         'Energy Institute, <i>Statistical Review of World Energy 2026</i>, <a href="https://www.energyinst.org/statistical-review">energyinst.org</a>.',
         'Total energy supply of 600.31 exajoules in 2025, about 19 trillion watts.'),
        ('Jason Wright and colleagues estimated in 2018',
         'Wright, J. T., Kanodia, S. &amp; Lubar, E. (2018). How much SETI has been done? Finding needles in the n-dimensional cosmic haystack. <i>Astronomical Journal</i> 156, 260, <a href="https://doi.org/10.3847/1538-3881/aae099">doi:10.3847/1538-3881/aae099</a>.',
         'Searches to date cover about 6 &times; 10<sup>&minus;18</sup> of the haystack, like 8,000 liters of the oceans, between a large hot tub and a small swimming pool.'),
        ('could cross the galaxy in less than',
         'Carroll-Nellenback, J., Frank, A., Wright, J. &amp; Scharf, C. (2019). The Fermi paradox and the Aurora effect: exo-civilization settlement, expansion, and steady states. <i>Astronomical Journal</i> 158, 117, <a href="https://doi.org/10.3847/1538-3881/ab31a3">doi:10.3847/1538-3881/ab31a3</a>.',
         'Settlement fronts cross the galaxy in at most about 300 million years; Earth can stay unvisited in a partly settled galaxy.'),
        ("of humanity's potential",
         'Ord, T. (2020). <i>The Precipice: Existential Risk and the Future of Humanity</i>. Bloomsbury, Table 6.1; values as stated by Ord in <a href="https://80000hours.org/podcast/episodes/toby-ord-the-precipice-existential-risk-future-humanity/">80,000 Hours interview, 2020</a>.',
         'About 1 in 6 for existential catastrophe this century; about 1 in 10 from unaligned AI. One person&rsquo;s estimates.'),
        ('superforecasters gave a median of',
         'Karger, E. et al. (2023). <i>Forecasting Existential Risks: Evidence from a Long-Run Forecasting Tournament</i>. Forecasting Research Institute, <a href="https://forecastingresearch.org/xpt">forecastingresearch.org</a>.',
         'Median probability of human extinction by 2100: 1 percent (superforecasters) and 6 percent (domain experts).'),
        ('survey of 2,778 AI researchers',
         'Grace, K. et al. (2024). Thousands of AI authors on the future of AI. <a href="https://arxiv.org/abs/2401.02843">arXiv:2401.02843</a>.',
         'Median 5 percent for an extremely bad outcome, such as human extinction, from advanced AI; 2,778 researchers surveyed.'),
        ('if the yearly risk were above 1 in 14,000',
         'Snyder-Beattie, A. E., Ord, T. &amp; Bonsall, M. B. (2019). An upper bound for the background rate of human extinction. <i>Scientific Reports</i> 9, 11054, <a href="https://doi.org/10.1038/s41598-019-47540-7">doi:10.1038/s41598-019-47540-7</a>.',
         'The annual probability of extinction from natural causes is very likely below 1 in 14,000, taking Homo sapiens to be 200,000 years old.'),
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
        ('and octopuses',
         'Amodio, P., Boeckle, M., Schnell, A. K., Ostoji&cacute;, L., Fiorito, G. &amp; Clayton, N. S. (2019). Grow smart and die young: why did cephalopods evolve intelligence? <i>Trends in Ecology &amp; Evolution</i> 34, 45&ndash;56, <a href="https://doi.org/10.1016/j.tree.2018.10.010">doi:10.1016/j.tree.2018.10.010</a>.',
         'Complex cognition in cephalopods, evolved independently of vertebrates.'),
        ('Dudley et al. 2007',
         'Dudley, R. et al. (2007). Gliding and the functional origins of flight: biomechanical novelty or necessity? <i>Annual Review of Ecology, Evolution, and Systematics</i> 38, 179&ndash;201, <a href="https://doi.org/10.1146/annurev.ecolsys.37.091305.110014">doi:10.1146/annurev.ecolsys.37.091305.110014</a>.',
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
    # Night work (night-shift lane, batch 2, 2026-11-13). nightshift/update_page.py applies this entry itself
    # (oxygen's idiom). BLS files and hashes in nightshift/data/fetched.json; the studies were read by the lane's
    # research agents (03 RESEARCH/nov-2026-batch2/night-shift/research/w2-0*.md) and re-checked in wave 3.
    "nightshift.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("usually worked a regular night shift",
         'U.S. Bureau of Labor Statistics, <a href="https://www.bls.gov/news.release/flex2.htm">Job Flexibilities and Work Schedules, 2024-2025</a>, news release, Tables 7 and 8.',
         'Share of wage and salary workers on a regular night shift (3.4 percent) and by occupation; the main reasons for night work, by sex.'),
        ("which the Census Bureau runs for BLS",
         'U.S. Bureau of Labor Statistics, <a href="https://www.bls.gov/tus/data.htm">American Time Use Survey data files</a>: respondent, activity, who, summary and roster files for 2024 and 2025, and the Leave and Job Flexibilities Module 2024-25 with its weights.',
         'The diaries and the usual-shift question this page joins.'),
        ("the share of the country asleep at 3 a.m.",
         'U.S. Bureau of Labor Statistics, <a href="https://www.bls.gov/tus/tables/a3-2025.htm">American Time Use Survey, Table A-3</a>, 2025.',
         'Percent of the population 15 and over sleeping and working at each hour of the day.'),
        ("usually slept six hours or less",
         'Centers for Disease Control and Prevention, &ldquo;Short Sleep Duration Among Workers &mdash; United States, 2010&rdquo;, <i>MMWR</i> 61(16):281-285, 2012, <a href="https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6116a2.htm">cdc.gov</a>.',
         'Short sleep (six hours or less) among regular night workers, 44.0 percent, and regular day workers, 28.8 percent.'),
        ("Danish night warehouse workers",
         'Nabe-Nielsen K. et al., &ldquo;Sleep duration and quality in permanent night work: an observational field study&rdquo;, <i>International Archives of Occupational and Environmental Health</i> 97(7):733-743, 2024, <a href="https://doi.org/10.1007/s00420-024-02080-0">doi:10.1007/s00420-024-02080-0</a> (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11416425/">PMC11416425</a>).',
         'Wrist actigraphy: 5 h 39 min of sleep after night shifts, 7 h 24 min on recovery days.'),
        ("rose at 20:50 on average",
         'Burgess H.J. and Fogg L.F., &ldquo;Individual differences in the amount and timing of salivary melatonin secretion&rdquo;, <i>PLoS ONE</i> 3(8):e3055, 2008, <a href="https://doi.org/10.1371/journal.pone.0003055">doi:10.1371/journal.pone.0003055</a>.',
         'Melatonin onset 20:50 and offset 08:21 on average (163 of 170 profiles), healthy adults aged 18 to 45.'),
        ("Core body temperature reaches its daily low",
         'Baehr E.K., Revelle W. and Eastman C.I., &ldquo;Individual differences in the phase and amplitude of the human circadian temperature rhythm: with an emphasis on morningness-eveningness&rdquo;, <i>Journal of Sleep Research</i> 9(2):117-127, 2000, <a href="https://doi.org/10.1046/j.1365-2869.2000.00196.x">doi:10.1046/j.1365-2869.2000.00196.x</a> (<a href="https://www.personality-project.org/revelle/publications/baehr.revelle.eastman.pdf">PDF</a>).',
         'Temperature minimum about 05:09 on average in 172 adults, about mid-sleep.'),
        ("when sleepiness peaks and attention fails most",
         'Mitler M.M. et al., &ldquo;Catastrophes, sleep, and public policy: consensus report&rdquo;, <i>Sleep</i> 11(1):100-109, 1988, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC2517096/">PMC2517096</a>.',
         'The early-morning peak of sleepiness and of sleep-related errors and accidents.'),
        ("A 2008 review of six studies",
         'Folkard S., &ldquo;Do permanent night workers show circadian adjustment? A review based on the endogenous melatonin rhythm&rdquo;, <i>Chronobiology International</i> 25(2):215-224, 2008, <a href="https://doi.org/10.1080/07420520802106835">doi:10.1080/07420520802106835</a>.',
         'Under 3 percent of permanent night workers fully adjusted; fewer than one in four adjusted enough to benefit.'),
        ("A 2013 study of police officers",
         'Boudreau P., Dumont G.A. and Boivin D.B., &ldquo;Circadian adaptation to night shift work influences sleep, performance, mood and the autonomic modulation of the heart&rdquo;, <i>PLoS ONE</i> 8(7):e70813, 2013, <a href="https://doi.org/10.1371/journal.pone.0070813">doi:10.1371/journal.pone.0070813</a>.',
         'Police officers on rotating shifts after seven consecutive nights; 7 of 17 evaluations showed circadian adaptation.'),
        ("On North Sea oil platforms, where crews live",
         'Gibbs M., Hampton S., Morgan L. and Arendt J., &ldquo;Adaptation of the circadian rhythm of 6-sulphatoxymelatonin to a shift schedule of seven nights followed by seven days in offshore oil installation workers&rdquo;, <i>Neuroscience Letters</i> 325(2):91-94, 2002, <a href="https://doi.org/10.1016/s0304-3940(02)00247-1">doi:10.1016/s0304-3940(02)00247-1</a>.',
         'Melatonin rhythm moved about five hours later over a week of nights on an offshore installation.'),
        ("In a laboratory, ten adults",
         'Scheer F.A.J.L., Hilton M.F., Mantzoros C.S. and Shea S.A., &ldquo;Adverse metabolic and cardiovascular consequences of circadian misalignment&rdquo;, <i>PNAS</i> 106(11):4453-4458, 2009, <a href="https://doi.org/10.1073/pnas.0808180106">doi:10.1073/pnas.0808180106</a>.',
         'Ten-day protocol, 10 adults: glucose up despite more insulin, leptin 17 percent lower, 3 of 8 with prediabetic post-meal glucose.'),
        ("an 18 percent higher risk of coronary heart disease",
         'Vetter C. et al., &ldquo;Association between rotating night shift work and risk of coronary heart disease among women&rdquo;, <i>JAMA</i> 315(16):1726-1734, 2016, <a href="https://doi.org/10.1001/jama.2016.4454">doi:10.1001/jama.2016.4454</a>.',
         'Hazard ratio 1.18 (1.10-1.26) for 10 or more years of rotating night shifts, Nurses&rsquo; Health Study.'),
        ("death from cardiovascular disease",
         'Gu F. et al., &ldquo;Total and cause-specific mortality of U.S. nurses working rotating night shifts&rdquo;, <i>American Journal of Preventive Medicine</i> 48(3):241-252, 2015, <a href="https://doi.org/10.1016/j.amepre.2014.10.018">doi:10.1016/j.amepre.2014.10.018</a>.',
         'Cardiovascular mortality hazard ratio 1.23 (1.09-1.38) for 15 or more years.'),
        ("a 58 percent higher risk of type 2 diabetes",
         'Pan A. et al., &ldquo;Rotating night shift work and risk of type 2 diabetes: two prospective cohort studies in women&rdquo;, <i>PLoS Medicine</i> 8(12):e1001141, 2011, <a href="https://doi.org/10.1371/journal.pmed.1001141">doi:10.1371/journal.pmed.1001141</a>.',
         'Hazard ratio 1.58 (1.43-1.74) for 20 or more years; 1.24 (1.13-1.37) with body mass index adjusted.'),
        ("A 2012 meta-analysis of 34 studies",
         'Vyas M.V. et al., &ldquo;Shift work and vascular events: systematic review and meta-analysis&rdquo;, <i>BMJ</i> 345:e4800, 2012, <a href="https://doi.org/10.1136/bmj.e4800">doi:10.1136/bmj.e4800</a>.',
         'Myocardial infarction risk ratio 1.23 (1.15-1.31); mortality not raised.'),
        ("probably carcinogenic to humans, Group 2A",
         'International Agency for Research on Cancer, <a href="https://publications.iarc.who.int/593">IARC Monographs Volume 124: Night Shift Work</a>, Working Group June 2019, published 2020.',
         'Group 2A; limited evidence in humans (breast, prostate, colon, rectum), sufficient evidence in experimental animals, strong mechanistic evidence in experimental animals.'),
        ("the relative risk of breast cancer for night work was 0.99",
         'Travis R.C. et al., &ldquo;Night shift work and breast cancer incidence: three prospective studies and meta-analysis of published studies&rdquo;, <i>Journal of the National Cancer Institute</i> 108(12):djw169, 2016, <a href="https://doi.org/10.1093/jnci/djw169">doi:10.1093/jnci/djw169</a>.',
         'Ten prospective studies, 1.4 million women: relative risk 0.99 (0.95-1.03); no excess at 20 or 30 years.'),
        ("find higher risks than studies that follow women forward",
         'Van N.T.H., Hoang T. and Myung S.-K., &ldquo;Night shift work and breast cancer risk: a meta-analysis of observational epidemiological studies&rdquo;, <i>Carcinogenesis</i> 42(10):1260-1269, 2021, <a href="https://doi.org/10.1093/carcin/bgab074">doi:10.1093/carcin/bgab074</a>.',
         'Case-control studies pooled odds ratio 1.34 (1.17-1.53); cohort studies 0.98 (0.93-1.03).'),
        ("Workers who fall ill tend to leave night work",
         'G&eacute;dor M. et al., &ldquo;Relationship between night work and health-related quality of life: an analysis based on profiles and cumulative duration of exposure to night work among French workers in the CONSTANCES cohort&rdquo;, <i>International Archives of Occupational and Environmental Health</i> 97(4):377-386, 2024, <a href="https://doi.org/10.1007/s00420-024-02053-3">doi:10.1007/s00420-024-02053-3</a>.',
         'Former night workers in poorer physical health than day workers; the authors attribute this to the healthy-worker survivor effect.'),
        ("which a 2021 genetic study found could inflate it",
         'Daghlas I. et al., &ldquo;Selection into shift work is influenced by educational attainment and body mass index: a Mendelian randomization study in the UK Biobank&rdquo;, <i>International Journal of Epidemiology</i> 50(4):1229-1240, 2021, <a href="https://doi.org/10.1093/ije/dyab031">doi:10.1093/ije/dyab031</a>.',
         'Genetic liability to lower education and higher body mass index raises the odds of shift work, which can bias shift-work studies.'),
        ("Simon Folkard and David Lombardi found",
         'Folkard S. and Lombardi D.A., &ldquo;Modeling the impact of the components of long work hours on injuries and accidents&rdquo;, <i>American Journal of Industrial Medicine</i> 49(11):953-963, 2006, <a href="https://stacks.cdc.gov/view/cdc/213463">CDC Stacks</a>.',
         'Risk 27.9 percent higher on nights than mornings; 36 percent higher on the fourth night than the first; 27.5 percent higher on 12-hour than 8-hour shifts.'),
        ("In a study published in 2016, on a closed track",
         'Lee M.L. et al., &ldquo;High risk of near-crash driving events following night-shift work&rdquo;, <i>PNAS</i> 113(1):176-181, 2016, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC4711869/">PMC4711869</a>.',
         'No near-crashes after sleep; near-crashes in 6 of 16 drives after a night shift, and 7 drives stopped early.'),
        ("In a sample of 3,476 American couples",
         'Presser H.B., &ldquo;Nonstandard work schedules and marital instability&rdquo;, <i>Journal of Marriage and Family</i> 62(1):93-110, 2000, <a href="https://doi.org/10.1111/j.1741-3737.2000.00093.x">doi:10.1111/j.1741-3737.2000.00093.x</a>.',
         'Fixed nights and separation or divorce among couples with children, by sex and length of marriage.'),
        ("A later study of newlyweds",
         'Kalil A., Ziol-Guest K.M. and Levin Epstein J., &ldquo;Nonstandard work and marital instability: evidence from the National Longitudinal Survey of Youth&rdquo;, <i>Journal of Marriage and Family</i> 72(5):1289-1300, 2010, <a href="https://doi.org/10.1111/j.1741-3737.2010.00765.x">doi:10.1111/j.1741-3737.2010.00765.x</a>.',
         'Wives&rsquo; fixed night shifts and divorce risk, among couples without children.'),
        ("2014 review found adverse associations",
         'Li J. et al., &ldquo;Parents&rsquo; nonstandard work schedules and child well-being: a critical review of the literature&rdquo;, <i>Journal of Primary Prevention</i> 35(1):53-73, 2014, <a href="https://doi.org/10.1007/s10935-013-0318-z">doi:10.1007/s10935-013-0318-z</a>.',
         '21 of 23 studies found adverse associations with child outcomes.'),
        ("No federal law requires a private employer",
         'U.S. Department of Labor, <a href="https://www.dol.gov/general/topic/workhours/nightwork">Night Work and Shift Work</a>.',
         'The Fair Labor Standards Act does not require extra pay for night work; such pay is a matter of agreement between employer and employee.'),
        ("a 10 percent differential for regularly scheduled work",
         '5 U.S.C. 5545(a), <a href="https://www.law.cornell.edu/uscode/text/5/5545">Night, standby, irregular, and hazardous duty differential</a>.',
         'Night pay of 10 percent of basic pay for regularly scheduled work between 6 p.m. and 6 a.m.'),
        ("In 13 European countries",
         'Desiere S. and Walter C., &ldquo;The Shift Premium: Evidence from a Discrete Choice Experiment&rdquo;, IZA Discussion Paper 16460, 2023, <a href="https://docs.iza.org/dp16460.pdf">PDF</a>.',
         'Shift premium 5 to 16 percent of gross wages among recipients in 13 EU countries (Structure of Earnings Survey); median required premium 36 percent for a fixed night shift in a Belgian choice experiment, about 8 percent among current night workers and 48 percent among day workers.'),
        ("Among 64,615 nurses",
         'Vetter C. et al., &ldquo;Mismatch of sleep and work timing and risk of type 2 diabetes&rdquo;, <i>Diabetes Care</i> 38(9):1707-1713, 2015, <a href="https://doi.org/10.2337/dc15-0302">doi:10.2337/dc15-0302</a>.',
         'Chronotype by shift-work interaction for type 2 diabetes in Nurses&rsquo; Health Study 2: early chronotypes&rsquo; risk rose with years of shift work; late chronotypes&rsquo; was highest on day work.'),
        ("moved young volunteers' melatonin onset",
         'Smith M.R., Fogg L.F. and Eastman C.I., &ldquo;Practical interventions to promote circadian adaptation to permanent night shift work: study 4&rdquo;, <i>Journal of Biological Rhythms</i> 24(2):161-172, 2009, <a href="https://doi.org/10.1177/0748730409332068">doi:10.1177/0748730409332068</a>.',
         'Simulated night shifts: bright light, dark glasses and dark sleep moved melatonin onset to about 03:22 on average, near the 03:00 compromise target.'),
    ],
    "space-depression.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("by the count in Jonathan McDowell's public tables",
         'J. McDowell, astronaut tables <i>rides.tsv</i> and <i>missions.tsv</i>, General Catalog of Artificial Space Objects, <a href="https://planet4589.org/space/astro/tsv/rides.tsv">planet4589.org</a>, CC BY 4.0, table dated 7 November 2026, fetched 13 November 2026.',
         'Every person-flight to orbit or beyond, its length and destination; counts, person-years and the longest flight.'),
        ("and colleagues gave weekly questionnaires",
         'N. Kanas and others, &ldquo;Psychosocial issues in space: results from Shuttle/Mir&rdquo;, <i>Gravitational and Space Biology Bulletin</i> 14(2):35-45, 2001, <a href="https://pubmed.ncbi.nlm.nih.gov/11865867/">PubMed 11865867</a>.',
         'Weekly mood and group climate questionnaires from five U.S. astronauts and eight Russian cosmonauts; no third-quarter effect.'),
        ("crew members on the International Space Station",
         'N. A. Kanas and others, &ldquo;Crewmember and mission control personnel interactions during International Space Station missions&rdquo;, <i>Aviation, Space, and Environmental Medicine</i> 78(6):601-607, 2007, <a href="https://pubmed.ncbi.nlm.nih.gov/17571662/">PubMed 17571662</a>.',
         'Seventeen ISS crew members; no decline in mood in the second half or any quarter; displacement of negative feeling to mission control.'),
        ("Its 2025 evidence report records",
         'NASA Human Research Program, <i>Risk of Adverse Cognitive or Behavioral Changes and Psychiatric Disorders</i>, evidence report, approved for public release 10 February 2025, <a href="https://ntrs.nasa.gov/citations/20250001454">NTRS 20250001454</a>.',
         'Nine behavioral health instances on ISS Expeditions 1 to 40, 0.62 per person-year; no in-flight diagnosis of anxiety or depression as of 2016; reluctance to report; a red risk for planetary missions; isolation and confinement as the main driver.'),
        ("Laura Barger of Harvard Medical School",
         'L. K. Barger and others, &ldquo;Prevalence of sleep deficiency and use of hypnotic drugs in astronauts before, during, and after spaceflight&rdquo;, <i>The Lancet Neurology</i> 13(9):904-912, 2014, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC4188436/">PMC4188436</a>.',
         'ISS crews slept 6.09 hours a night in flight; 75 percent of ISS crew members who answered (12 of 16) used sleep-promoting medication.'),
        ("The longest sealed rehearsal for Mars",
         'M. Basner and others, &ldquo;Psychological and behavioral changes during confinement in a 520-day simulated interplanetary mission to Mars&rdquo;, <i>PLoS ONE</i> 9(3):e93298, 2014, <a href="https://doi.org/10.1371/journal.pone.0093298">doi:10.1371/journal.pone.0093298</a>.',
         'Depressive symptoms in 93 percent of mission weeks for one crew member; conflicts with mission control five times as often as within the crew.'),
        ("sleep-wake cycle averaged",
         'M. Basner and others, &ldquo;Mars 520-d mission simulation reveals protracted crew hypokinesis and alterations of sleep duration and timing&rdquo;, <i>PNAS</i> 110(7):2635-2640, 2013, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3574912/">PMC3574912</a>.',
         'One crew member with a sleep-wake period of 24.98 hours.'),
        ("Lawrence Palinkas and colleagues interviewed",
         'L. A. Palinkas and others, &ldquo;Incidence of psychiatric disorders after extended residence in Antarctica&rdquo;, <i>International Journal of Circumpolar Health</i> 63(2):157-168, 2004, <a href="https://pubmed.ncbi.nlm.nih.gov/15253482/">PubMed 15253482</a>.',
         '313 winter-over personnel interviewed 1994 to 1997; 39 (12.5 percent) met DSM-IV criteria, 5.2 percent weighted; mood disorders most common.'),
        ("analog research by Suzanne Bell",
         'S. T. Bell, S. G. Brown and T. Mitchell, &ldquo;What we know about team dynamics for long-distance space missions: a systematic review of analog research&rdquo;, <i>Frontiers in Psychology</i> 10:811, 2019, <a href="https://doi.org/10.3389/fpsyg.2019.00811">doi:10.3389/fpsyg.2019.00811</a>.',
         '72 sources; team mood did not consistently support the third-quarter phenomenon.'),
        ("Gro Mjeldheim Sandal's team",
         'G. M. Sandal, F. J. R. van de Vijver and N. Smith, &ldquo;Psychological hibernation in Antarctica&rdquo;, <i>Frontiers in Psychology</i> 9:2235, 2018, <a href="https://doi.org/10.3389/fpsyg.2018.02235">doi:10.3389/fpsyg.2018.02235</a>.',
         'Two Concordia crews, 27 people, about 10 months; several measures at a minimum in midwinter, the third quarter.'),
        ("NASA's 2009 reference architecture",
         'B. G. Drake (ed.), <i>Human Exploration of Mars Design Reference Architecture 5.0</i>, NASA-SP-2009-566, July 2009, <a href="https://www.nasa.gov/wp-content/uploads/2015/09/373665main_nasa-sp-2009-566.pdf">PDF</a>.',
         'Short-stay missions of 500 to 650 days, long-stay of 890 to 950; the 916-day example (210, 496, 210 days); a crew of six.'),
        ("Between 2033 and mid-2036",
         'NASA Jet Propulsion Laboratory, Horizons System, observer ephemerides of Mars (499) and the Moon (301) from the geocenter, quantities 20, 21 and 23, <a href="https://ssd.jpl.nasa.gov/horizons/">ssd.jpl.nasa.gov/horizons</a>, computed 13 November 2026.',
         'One-way light time to Mars, daily 2033 to mid-2036, and to the Moon, hourly through 2033.'),
        ("NASA expects communication blackouts",
         'NASA, <i>Mars Communications Disruption and Delay</i>, Moon to Mars architecture white paper, 2023, <a href="https://www.nasa.gov/wp-content/uploads/2024/01/mars-communications-disruption-and-delay.pdf">PDF</a>.',
         'Communication blackouts are inevitable and can last weeks.'),
        ("no fewer than four crew members on the Martian surface",
         'NASA, <i>2025 Architecture Update</i>, Moon to Mars architecture, December 2025, <a href="https://www.nasa.gov/wp-content/uploads/2025/12/2025-architecture-update-for-publication.pdf">PDF</a>.',
         'Initial Mars missions assume no less than four crew members on the surface.'),
        ("In its 2025 risk record",
         'NASA Human System Risk Board, <i>Risk of Adverse Cognitive or Behavioral Conditions and Psychiatric Disorders</i>, risk record Rev D.1, 2025, <a href="https://www.nasa.gov/wp-content/uploads/2025/09/hsrb-behavioral-health-risk-record-rev-d-1-web.pdf">PDF</a>.',
         'Likelihood and consequence ratings by mission (July 2024 board decision); the ISS rate is likely an underestimate.'),
        ("had a major depressive episode in the past year",
         'Substance Abuse and Mental Health Services Administration, <i>Key Substance Use and Mental Health Indicators in the United States: Results from the 2025 National Survey on Drug Use and Health</i>, 2026, <a href="https://www.samhsa.gov/data/sites/default/files/reports/rpt57150/2025-nsduh-annual-national-report.pdf">PDF</a>.',
         '7.4 percent of U.S. adults (19.7 million) had a major depressive episode in the past year in 2025.'),
        ("E. C. Ihle and colleagues",
         'E. C. Ihle, J. B. Ritsher and N. Kanas, &ldquo;Positive psychological outcomes of spaceflight: an empirical study&rdquo;, <i>Aviation, Space, and Environmental Medicine</i> 77(2):93-101, 2006, <a href="https://pubmed.ncbi.nlm.nih.gov/16491575/">PubMed 16491575</a>.',
         'Anonymous survey of 175 astronauts and cosmonauts, 39 replies, every respondent positive about being in space.'),
        ("CHAPEA from NASA's start and end dates",
         'NASA, <i>Crew Health and Performance Exploration Analog</i>, <a href="https://www.nasa.gov/humans-in-space/chapea/">nasa.gov</a>, fetched 13 November 2026.',
         'Mission 1 from 25 June 2023 to 6 July 2024, four crew members.'),
        ("the HI-SEAS missions in months",
         'J. D. Rosenberg and others, HI-SEAS missions 3 to 5, <i>Frontiers in Physiology</i> 13:898841, 2022, <a href="https://doi.org/10.3389/fphys.2022.898841">doi:10.3389/fphys.2022.898841</a>.',
         'Eighteen people on 8-, 12- and 8-month missions.'),
    ],
    # What moved people toward lower-carbon choices (sustainable-messaging lane, 2026-11-13).
    # messaging/update_page.py applies this entry itself (oxygen's idiom). The lane's research and fact-check
    # files are in 03 RESEARCH/nov-2026-batch2/sustainable-messaging/research/.
    "messaging.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("Carbon labels in university",
         'B. Lohmann and others, &ldquo;Do carbon footprint labels promote climatarian diets? Evidence from a large-scale field experiment&rdquo;, <i>Journal of Environmental Economics and Management</i> 114 (2022), <a href="https://doi.org/10.1016/j.jeem.2022.102693">doi:10.1016/j.jeem.2022.102693</a>.',
         "Five Cambridge college cafeterias, 2020: vegetarian share 41.0 to 42.7 percent; high-carbon share down 2.7 points."),
        ("workplace cafeterias",
         'C. Lowrie and P. Lohmann, &ldquo;Do carbon labels encourage sustainable food choices? Evidence from a field experiment in call-centre worksite cafeterias&rdquo;, <i>Behavioural Public Policy</i> (2025), <a href="https://doi.org/10.1017/bpp.2025.10023">doi:10.1017/bpp.2025.10023</a>.',
         "Four call-centre cafeterias, 2023: vegetarian share up 1.5 points from 7 percent; no significant change in emissions."),
        ("screens telling diners that more and more",
         'E. N. &Ccedil;oker and others, &ldquo;A dynamic social norm messaging intervention to reduce meat consumption: A randomized cross-over trial in retail store restaurants&rdquo;, <i>Appetite</i> 169 (2022), <a href="https://doi.org/10.1016/j.appet.2021.105824">doi:10.1016/j.appet.2021.105824</a>.',
         "22 restaurants, preregistered: screens saying more and more customers choose the veggie options; no detectable change in the plant-based share of sales (about 10 percent)."),
        ("the best of three new names",
         'L. Bacon, D. Wise, S. Attwood and D. Vennard, <i>The Language of Sustainable Diets</i>, World Resources Institute, 2018, <a href="https://files.wri.org/d8/s3fs-public/language-sustainable-diets.pdf">PDF</a>.',
         "&lsquo;Field-grown Breakfast&rsquo;, the best of three names, tested in 3 cafes against 18 controls: 4.6 to 5.4 percent of breakfasts."),
        ("in a Cambridge experiment",
         'E. E. Garnett, A. Balmford, C. Sandbrook, M. A. Pilling and T. M. Marteau, &ldquo;Impact of increasing vegetarian availability on meal selection and sales in cafeterias&rdquo;, <i>PNAS</i> 116 (2019) 20923-20929, <a href="https://doi.org/10.1073/pnas.1907207116">doi:10.1073/pnas.1907207116</a>.',
         "Doubling vegetarian options raised the vegetarian share from 19.1 to 26.9 percent; no detectable rebound at dinner."),
        ("a Dijon cafeteria",
         'L. Arrazat and others, &ldquo;Effects of increasing the availability of vegetarian options on main meal choices, meal offer satisfaction and liking: a pre-post analysis in a French university cafeteria&rdquo;, <i>International Journal of Behavioral Nutrition and Physical Activity</i> 21 (2024) 75, <a href="https://doi.org/10.1186/s12966-024-01624-4">doi:10.1186/s12966-024-01624-4</a>.',
         "Vegetarian share of main dishes 23 to 45 percent, 37,299 choices."),
        ("Serving the plant-based dish unless diners asked for meat",
         'J. Ginn and G. Sparkman, &ldquo;Can you default to vegan? Plant-based defaults to change dining practices on college campuses&rdquo;, <i>Journal of Environmental Psychology</i> 93 (2024) 102226, <a href="https://doi.org/10.1016/j.jenvp.2023.102226">doi:10.1016/j.jenvp.2023.102226</a>; figures from the Food for Climate League summary.',
         "Three dining halls: plant-based share of hot dishes served 26.9 to 57.6 percent (model estimates); no effect in one of the three halls."),
        ("a restaurant's chef's menu",
         'M. J. Reinders, E. Bouwman and M. C. Onwezen, &ldquo;Reducing meat consumption in restaurants: exploring the default mechanism in a surprise menu, combined with effort and price incentives&rdquo;, <i>Journal of Environmental Psychology</i> 98 (2024) 102402, <a href="https://doi.org/10.1016/j.jenvp.2024.102402">doi:10.1016/j.jenvp.2024.102402</a>.',
         "Vegetarian share of chef&rsquo;s menus 15.8 percent in the unchanged week, 56.9 percent in the vegetarian-default week."),
        ("checking the plant-based meal on an event form",
         'R. Boronowsky and others, &ldquo;Plant-based default nudges effectively increase the sustainability of catered meals on college campuses: Three randomized controlled trials&rdquo;, <i>Frontiers in Sustainable Food Systems</i> 6 (2022) 1001157, <a href="https://doi.org/10.3389/fsufs.2022.1001157">doi:10.3389/fsufs.2022.1001157</a>.',
         "Three catered events: plant-based choice 18.4 to 65.5 percent (risk difference 46.8 points)."),
        ("a German energy supplier's online shop",
         'F. Ebeling and S. Lotz, &ldquo;Domestic uptake of green energy promoted by opt-out tariffs&rdquo;, <i>Nature Climate Change</i> 5 (2015) 868-871, <a href="https://doi.org/10.1038/nclimate2681">doi:10.1038/nclimate2681</a>.',
         "41,952 households: green share of contracts 7.2 percent (opt-in) against 69.1 percent (opt-out); premium 0.3 euro cents a kilowatt-hour."),
        ("Sacramento pricing trial",
         'M. Fowlie, C. Wolfram, P. Baylis, C. A. Spurlock, A. Todd and P. Cappers, &ldquo;Default effects and follow-on behaviour: Evidence from an electricity pricing program&rdquo;, <i>Review of Economic Studies</i> 88 (2021) 2886-2934, <a href="https://doi.org/10.1093/restud/rdab018">doi:10.1093/restud/rdab018</a>; working paper <a href="https://www.nber.org/papers/w23553">NBER 23553</a>.',
         "Time-of-use enrollment 19.3 against 97.9 percent; 18.1 and 92.6 percent in September 2013; households enrolled only by the default cut peak use by about a fifth as much."),
        ("a Swiss utility switched its customers",
         'U. Liebe, J. Gewinner and A. Diekmann, &ldquo;Large and persistent effects of green energy defaults in the household and business sectors&rdquo;, <i>Nature Human Behaviour</i> 5 (2021) 576-585, <a href="https://doi.org/10.1038/s41562-021-01070-3">doi:10.1038/s41562-021-01070-3</a>.',
         "About 80 percent of households still on the green default four years after the switch; not a randomized trial."),
        ("Home energy reports, which cut electricity use",
         'H. Allcott, &ldquo;Social norms and energy conservation&rdquo;, <i>Journal of Public Economics</i> 95 (2011) 1082-1095, <a href="https://doi.org/10.1016/j.jpubeco.2011.03.003">doi:10.1016/j.jpubeco.2011.03.003</a>.',
         "Home energy reports cut electricity use by about 2 percent."),
        ("Nudge trials published in academic journals",
         'S. DellaVigna and E. Linos, &ldquo;RCTs to scale: Comprehensive evidence from two nudge units&rdquo;, <i>Econometrica</i> 90 (2022) 81-116, <a href="https://doi.org/10.3982/ECTA18709">doi:10.3982/ECTA18709</a>.',
         "8.7 points in 26 academic trials against 1.4 points in 126 nudge-unit trials covering more than 23 million people; publication bias explains most of the gap."),
        ("from the first 10 sites to 111",
         'H. Allcott, &ldquo;Site selection bias in program evaluation&rdquo;, <i>Quarterly Journal of Economics</i> 130 (2015) 1117-1165, <a href="https://doi.org/10.1093/qje/qjv015">doi:10.1093/qje/qjv015</a>.',
         "1.71 percent at the first 10 sites against 1.31 percent across 111."),
        ("A 2022 reanalysis of more than 400 nudge effects",
         'M. Maier, F. Barto&scaron;, T. D. Stanley, D. R. Shanks, A. J. L. Harris and E.-J. Wagenmakers, &ldquo;No evidence for nudging after adjusting for publication bias&rdquo;, <i>PNAS</i> 119 (2022) e2200300119, <a href="https://doi.org/10.1073/pnas.2200300119">doi:10.1073/pnas.2200300119</a>; data from S. Mertens and others, <i>PNAS</i> 119 (2022) e2107346118.',
         "Decision structure d 0.58 to 0.12; decision information 0.25 to 0.00, after correction for publication bias."),
        ("For climate field interventions as a group",
         'M. Bergquist, M. Thiel, M. H. Goldberg and S. van der Linden, &ldquo;Field interventions for climate change mitigation behaviors: A second-order meta-analysis&rdquo;, <i>PNAS</i> 120 (2023) e2214851120, <a href="https://doi.org/10.1073/pnas.2214851120">doi:10.1073/pnas.2214851120</a>.',
         "d 0.18 after bias correction; 0.04 in the 32 adequately powered studies (each over 9,000 people)."),
        ("Nisa et al. 2019",
         'C. F. Nisa, J. J. B&eacute;langer, B. M. Schumpe and D. G. Faller, &ldquo;Meta-analysis of randomised controlled trials testing behavioural interventions to promote household action on climate change&rdquo;, <i>Nature Communications</i> 10 (2019) 4545, <a href="https://doi.org/10.1038/s41467-019-12457-2">doi:10.1038/s41467-019-12457-2</a>.',
         "Small samples d 0.335 against large samples d 0.028."),
        ("tested 11 interventions chosen by experts",
         'M. Vlasceanu, K. C. Doell, J. B. Bak-Coleman and others, &ldquo;Addressing climate change with behavioral science: A global intervention tournament in 63 countries&rdquo;, <i>Science Advances</i> 10 (2024) eadj5778, <a href="https://doi.org/10.1126/sciadv.adj5778">doi:10.1126/sciadv.adj5778</a>; data, <a href="https://zenodo.org/records/10345806">Zenodo 10345806</a> (CC BY 4.0).',
         "The 11 interventions, the outcomes and the participant data this page re-estimates."),
        ("A Swiss campus study found that sales of animal-based meals",
         'G. Russo, K. Gligori&cacute;, V. Moreau and R. West, study of meat-free days in the cafeterias of EPFL, preprint, 2025, <a href="https://arxiv.org/abs/2504.02899">arXiv:2504.02899</a>.',
         "Animal-based meals (meat, fish, seafood, dairy) a slightly larger share of sales the day after a meat-free day; not peer reviewed."),
        ("A 2025 review of rigorous trials aimed at cutting meat",
         'S. A. Green, B. A. Smith and M. B. Mathur, &ldquo;Meaningfully reducing consumption of meat and animal products is an unsolved problem: A meta-analysis&rdquo;, <i>Appetite</i> 216 (2026) 108233, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11957195/">PMC11957195</a>.',
         "SMD 0.07 over 41 studies; 0.01 after correction for publication bias; two choice-architecture studies met the criteria, most others measuring hypothetical choices or choices on the spot."),
        ("critics argue that it often reallocates",
         'N. Chater and G. Loewenstein, &ldquo;The i-frame and the s-frame: How focusing on individual-level solutions has led behavioral public policy astray&rdquo;, <i>Behavioral and Brain Sciences</i> 46 (2023) e147, <a href="https://doi.org/10.1017/S0140525X22002023">doi:10.1017/S0140525X22002023</a>.',
         "The argument that green tariffs can reallocate existing renewable power."),
        ("in a Swiss study, about half of the lowest-income",
         'C. Ghesla, M. Grieder and R. Schubert, &ldquo;Nudging the poor and the rich: A field study on the distributional effects of green electricity defaults&rdquo;, <i>Energy Economics</i> 86 (2020) 104616, <a href="https://doi.org/10.1016/j.eneco.2019.104616">doi:10.1016/j.eneco.2019.104616</a>.',
         "49.7 percent of the lowest-income customers on the green default would prefer one of two cheaper, less green tariffs."),
        ("lowered their support for a carbon tax",
         'D. Hagmann, E. H. Ho and G. Loewenstein, &ldquo;Nudging out support for a carbon tax&rdquo;, <i>Nature Climate Change</i> 9 (2019) 484-489, <a href="https://doi.org/10.1038/s41558-019-0474-0">doi:10.1038/s41558-019-0474-0</a>.',
         "Study 1A: support for a carbon tax 70.3 against 55.0 percent. Study 4: 70 against 60 percent; disclosure of the nudge&rsquo;s small effect raised it to 72 percent."),
        ("In 18 worksites that made part of the change",
         'R. Pechey and others, &ldquo;Impact of increasing the relative availability of meat-free options on food selection: two natural field experiments and an online randomised trial&rdquo;, <i>International Journal of Behavioral Nutrition and Physical Activity</i> 19 (2022) 9, <a href="https://doi.org/10.1186/s12966-021-01239-z">doi:10.1186/s12966-021-01239-z</a>.',
         "18 worksite cafeterias, partial implementation: +2.3 points, significant in the time-series analysis, not in the multilevel model."),
        ("14 percent more diners took vegetables",
         'B. P. Turnwald and others, &ldquo;Increasing vegetable intake by emphasizing tasty and enjoyable attributes: A randomized controlled multisite intervention for taste-focused labeling&rdquo;, <i>Psychological Science</i> 30 (2019) 1603-1615, <a href="https://doi.org/10.1177/0956797619872191">doi:10.1177/0956797619872191</a>.',
         "Taste-focused labels: 29 percent more selection than health-focused and 14 percent more than basic; 137,842 diner decisions."),
        ("6.9 points more meatless meals",
         'J. Anderson, G. Sparkman and others, <i>&ldquo;Reduce&rdquo; or &ldquo;Go Veg&rdquo;? Effects on Meal Choice</i>, Faunalytics, 2020, <a href="https://faunalytics.org/reduce-or-go-veg/">faunalytics.org</a>.',
         "Reduction appeal 25.8 against vegetarian appeal 18.9 percent meatless (617 analysed of 833); pledges 59.4 against 15.4 percent; meatless orders among pledgers 31.7 against 47.8 percent."),
        ("Donations to a climate charity rose",
         'P. Andre, T. Boneva, F. Chopra and A. Falk, &ldquo;Misperceived social norms and willingness to act against climate change&rdquo;, <i>Review of Economics and Statistics</i> 108 (2026) 1205-1221, <a href="https://doi.org/10.1162/rest_a_01468">doi:10.1162/rest_a_01468</a>.',
         "Learning that 62 percent of Americans try to fight global warming raised donations by 12 dollars, 4.7 percent."),
        ("Volunteers who had solar panels themselves",
         'G. T. Kraft-Todd, B. Bollinger, K. Gillingham, S. Lamp and D. G. Rand, &ldquo;Credibility-enhancing displays promote the provision of non-normative public goods&rdquo;, <i>Nature</i> 563 (2018) 245-248, <a href="https://doi.org/10.1038/s41586-018-0647-4">doi:10.1038/s41586-018-0647-4</a>.',
         "Ambassadors with solar recruited 62.8 percent more installations in 58 towns."),
        ("Health and environment messages cut electricity use",
         'O. I. Asensio and M. A. Delmas, &ldquo;Nonprice incentives and energy conservation&rdquo;, <i>PNAS</i> 112 (2015) E510-E515, <a href="https://doi.org/10.1073/pnas.1401880112">doi:10.1073/pnas.1401880112</a>.',
         "118 apartments: health and environment messages minus 8.2 percent; cost messages no measurable saving."),
        ("Fear appeals worked better",
         'M. B. Tannenbaum and others, &ldquo;Appealing to fear: A meta-analysis of fear appeal effectiveness and theories&rdquo;, <i>Psychological Bulletin</i> 141 (2015) 1178-1204, <a href="https://doi.org/10.1037/a0039729">doi:10.1037/a0039729</a>.',
         "d 0.43 with efficacy statements against 0.21 without."),
        ("37 more solar installations",
         'K. Gillingham and B. Bollinger, &ldquo;Social learning and solar photovoltaic adoption&rdquo;, <i>Management Science</i> 67 (2021) 7091-7112, <a href="https://doi.org/10.1287/mnsc.2020.3840">doi:10.1287/mnsc.2020.3840</a>.',
         "Solarize Connecticut: about 37 more installations per campaign town; no persistence after the campaign."),
        ("free home retrofits",
         'M. Fowlie, M. Greenstone and C. Wolfram, &ldquo;Do energy efficiency investments deliver? Evidence from the Weatherization Assistance Program&rdquo;, <i>Quarterly Journal of Economics</i> 133 (2018) 1597-1644, <a href="https://doi.org/10.1093/qje/qjy005">doi:10.1093/qje/qjy005</a>.',
         "Take-up of free weatherization from under 1 to about 6 percent with intensive outreach, at more than 1,000 dollars per extra household."),
        ("Efficiency information alone",
         'H. Allcott and R. L. Sweeney, &ldquo;The role of sales agents in information disclosure: Evidence from a field experiment&rdquo;, <i>Management Science</i> 63 (2017) 21-39, <a href="https://doi.org/10.1287/mnsc.2015.2327">doi:10.1287/mnsc.2015.2327</a>.',
         "Information had no effect on Energy Star water-heater purchases; a rebate with a sales incentive did."),
        ("Below-average users shown the average",
         'P. W. Schultz, J. M. Nolan, R. B. Cialdini, N. J. Goldstein and V. Griskevicius, &ldquo;The constructive, destructive, and reconstructive power of social norms&rdquo;, <i>Psychological Science</i> 18 (2007) 429-434, <a href="https://doi.org/10.1111/j.1467-9280.2007.01917.x">doi:10.1111/j.1467-9280.2007.01917.x</a>.',
         "Below-average households raised use after a descriptive norm alone; an approving emoticon removed the rise."),
        ("Shower energy fell 22 percent",
         'V. Tiefenbeck and others, &ldquo;Overcoming salience bias: How real-time feedback fosters resource conservation&rdquo;, <i>Management Science</i> 64 (2018) 1458-1476, <a href="https://doi.org/10.1287/mnsc.2016.2646">doi:10.1287/mnsc.2016.2646</a>.',
         "Real-time feedback cut shower energy 22 percent."),
        ("11.4 percent in hotels",
         'V. Tiefenbeck, A. W&ouml;rner, S. Sch&ouml;b, E. Fleisch and T. Staake, &ldquo;Real-time feedback promotes energy conservation in the absence of volunteer selection bias and monetary incentives&rdquo;, <i>Nature Energy</i> 4 (2019) 35-41, <a href="https://doi.org/10.1038/s41560-018-0282-1">doi:10.1038/s41560-018-0282-1</a>.',
         "Hotel guests: 11.4 percent less shower energy."),
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
    # Philosophers' guesses about nature (philosophy-physics lane, 2026-11-13). armchair/update_page.py applies
    # this entry itself (oxygen's idiom). The Gutenberg text is recorded in armchair/data/fetched.json; the
    # other sources were opened by the lane's research agents (03 RESEARCH/nov-2026-batch2/philosophy-physics).
    "armchair.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("the mythology of prolepsis",
         'Quentin Skinner, &ldquo;Meaning and Understanding in the History of Ideas&rdquo;, <i>History and Theory</i> 8(1), 3&ndash;53 (1969).',
         'The name and description of the mythology of prolepsis.'),
        ("waited for the telescope in 1610",
         'Galileo Galilei, <i>Sidereus Nuncius</i> (Venice, 1610); A&euml;tius 3.1.6 (DK 68 A91) for Democritus on the Milky Way.',
         "The Milky Way resolved into stars by telescope; the ancient report of Democritus's view."),
        ("which Aristotle reports from Empedocles and rejects",
         'Aristotle, <i>De Anima</i> II.7, 418b20&ndash;26, tr. J. A. Smith, MIT Internet Classics Archive.',
         "Empedocles' view that light travels and takes time, and Aristotle's rejection of it."),
        ("timings of Jupiter's moon Io in 1676",
         '&ldquo;D&eacute;monstration touchant le mouvement de la lumi&egrave;re trouv&eacute; par M. R&ouml;mer de l&rsquo;Acad&eacute;mie Royale des Sciences&rdquo;, <i>Journal des s&ccedil;avans</i>, 7 December 1676, 233&ndash;236 (unsigned report of R&oslash;mer&rsquo;s result).',
         "The finite speed of light from the timing of Io's eclipses."),
        ("in 1908 and 1909",
         'Jean Perrin, <i>Comptes rendus</i> 146, 967&ndash;970 (1908); &ldquo;Mouvement brownien et r&eacute;alit&eacute; mol&eacute;culaire&rdquo;, <i>Annales de chimie et de physique</i> 8e s&eacute;rie 18 (1909).',
         "Perrin's counts of particles in suspensions under the microscope, and the confirmation of molecular reality."),
        ("Kant argued in 1755",
         'Immanuel Kant, <i>Allgemeine Naturgeschichte und Theorie des Himmels</i> (1755), Part I, Akademie-Ausgabe 1:253&ndash;256 (korpora.org).',
         "Kant's view that the elliptical nebulae are star systems like the Milky Way."),
        ("read out at a meeting in 1925",
         'Edwin Hubble, &ldquo;Cepheids in Spiral Nebulae&rdquo;, read at the American Astronomical Society meeting, 1 January 1925; <i>The Observatory</i> 48, 139&ndash;142 (1925).',
         'Cepheid distances placing two spiral nebulae far outside the Milky Way.'),
        ("In 1835 Auguste Comte",
         'Auguste Comte, <i>Cours de philosophie positive</i>, vol. 2, 19th lesson (Paris: Bachelier, 1835), pp. 8&ndash;9.',
         'The chemical composition of the stars given as an example of what can never be known.'),
        ("identified sodium in the Sun's spectrum",
         'Gustav Kirchhoff, &ldquo;&Uuml;ber die Fraunhofer&rsquo;schen Linien&rdquo;, <i>Monatsberichte der K&ouml;niglichen Preussischen Akademie der Wissenschaften zu Berlin</i>, October 1859.',
         'Sodium identified in the solar atmosphere from the dark D lines.'),
        ("Wilhelm Ostwald argued in 1895",
         'Wilhelm Ostwald, <i>Die &Uuml;berwindung des wissenschaftlichen Materialismus</i> (Leipzig: Veit, 1895); preface dated November 1908 to <i>Grundriss der allgemeinen Chemie</i>, 4th ed. (1909), read in the 5th ed. (1917).',
         "Ostwald's case against atoms, and his concession after Perrin's results."),
        ("Aristotle worked out that in a void",
         'Aristotle, <i>Physics</i> IV.8, 216a11&ndash;21, tr. R. P. Hardie and R. K. Gaye, MIT Internet Classics Archive.',
         'Equal speed of fall in a void, derived and used as an argument against the void.'),
        ("then said there was no reason to believe it",
         'Edgar Allan Poe, <i>Eureka: A Prose Poem</i> (New York: Putnam, 1848), Project Gutenberg eBook 32037.',
         'Poe raising and setting aside finite light travel as the reason the sky is dark.'),
        ("Lord Kelvin made the calculation in 1901",
         'Lord Kelvin, &ldquo;On Ether and Gravitational Matter through Infinite Space&rdquo;, <i>Philosophical Magazine</i> ser. 6, 2, 161&ndash;177 (1901).',
         'The calculation that a finite age and finite light speed account for the dark sky.'),
        ("photographed in Orion in 1993",
         'C. R. O&rsquo;Dell, Z. Wen and X. Hu, &ldquo;Discovery of new objects in the Orion nebula on HST images: shocks, compact sources, and protoplanetary disks&rdquo;, <i>Astrophysical Journal</i> 410, 696 (1993).',
         'Discs of matter around young stars in Orion.'),
        ("table of simple substances",
         'Antoine Lavoisier, <i>Trait&eacute; &eacute;l&eacute;mentaire de chimie</i> (Paris, 1789), table of simple substances; English tr. <i>Elements of Chemistry</i>, Project Gutenberg eBook 30775.',
         'The table of simple substances, which includes light and caloric and omits water, air and earth.'),
        ("Kant held that the axioms",
         'Immanuel Kant, <i>Kritik der reinen Vernunft</i> (1781), A24; &ldquo;Kant&rsquo;s Views on Space and Time&rdquo;, <i>Stanford Encyclopedia of Philosophy</i>.',
         "Geometry's axioms as known a priori."),
        ("the eclipse expeditions of 1919",
         'F. W. Dyson, A. S. Eddington and C. Davidson, &ldquo;A Determination of the Deflection of Light by the Sun&rsquo;s Gravitational Field&rdquo;, <i>Philosophical Transactions of the Royal Society A</i> 220, 291&ndash;333 (1920).',
         'Starlight deflected by the Sun as general relativity predicts.'),
        ("Podolsky and Rosen argued in 1935",
         'A. Einstein, B. Podolsky and N. Rosen, &ldquo;Can Quantum-Mechanical Description of Physical Reality Be Considered Complete?&rdquo;, <i>Physical Review</i> 47, 777&ndash;780 (1935).',
         'The argument that quantum mechanics is incomplete.'),
        ("a test in Delft",
         'B. Hensen et al., &ldquo;Loophole-free Bell inequality violation using electron spins separated by 1.3 kilometres&rdquo;, <i>Nature</i> 526, 682&ndash;686 (2015).',
         'The first Bell test to close the main loopholes together.'),
    ],
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
    # The gradient of life (origins-of-life lane, 2026-11-13). origins/update_page.py applies this entry
    # itself (oxygen's idiom). Notes for each source: 03 RESEARCH/nov-2026-batch2/origins-of-life/research/w2-0*.md.
    "origins.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("warm ponds on land that dried and refilled",
         'B. Damer and D. Deamer, &ldquo;The hot spring hypothesis for an origin of life&rdquo;, <i>Astrobiology</i> 20(4):429&ndash;452, 2020, <a href="https://doi.org/10.1089/ast.2019.2045">doi:10.1089/ast.2019.2045</a>.',
         'The land-pool programme; its objections to vents (dilution, salt against membrane formation).'),
        ("cyanide and sulphur compounds near the surface",
         'B. H. Patel, C. Percivalle, D. J. Ritson, C. D. Duffy and J. D. Sutherland, &ldquo;Common origins of RNA, protein and lipid precursors in a cyanosulfidic protometabolism&rdquo;, <i>Nature Chemistry</i> 7:301&ndash;307, 2015, <a href="https://doi.org/10.1038/nchem.2202">doi:10.1038/nchem.2202</a>.',
         'The cyanosulfidic programme, driven by ultraviolet light.'),
        ("alkaline hydrothermal vents on the sea floor",
         'N. Lane and W. F. Martin, &ldquo;The origin of membrane bioenergetics&rdquo;, <i>Cell</i> 151(7):1406&ndash;1416, 2012, <a href="https://doi.org/10.1016/j.cell.2012.11.050">doi:10.1016/j.cell.2012.11.050</a>; and W. Martin and M. J. Russell, &ldquo;On the origins of cells&rdquo;, <i>Phil. Trans. R. Soc. B</i> 358:59&ndash;85, 2003, <a href="https://doi.org/10.1098/rstb.2002.1183">doi:10.1098/rstb.2002.1183</a>; first proposed in M. J. Russell, A. J. Hall, A. G. Cairns-Smith and P. S. Braterman, &ldquo;Submarine hot springs and the origin of life&rdquo;, <i>Nature</i> 336:117, 1988, <a href="https://doi.org/10.1038/336117a0">doi:10.1038/336117a0</a>.',
         'The alkaline-vent hypothesis and its proton gradient. A hypothesis.'),
        ("found in 2000",
         'D. S. Kelley et al., &ldquo;An off-axis hydrothermal vent field near the Mid-Atlantic Ridge at 30&deg;N&rdquo;, <i>Nature</i> 412:145&ndash;149, 2001, <a href="https://doi.org/10.1038/35084000">doi:10.1038/35084000</a>; and D. S. Kelley et al., &ldquo;A serpentinite-hosted ecosystem: the Lost City hydrothermal field&rdquo;, <i>Science</i> 307:1428&ndash;1434, 2005, <a href="https://doi.org/10.1126/science.1102556">doi:10.1126/science.1102556</a>.',
         'Lost City: carbonate chimneys, warm alkaline fluids rich in hydrogen.'),
        ("The MARHYS database collects the published measurements",
         'A. Diehl and W. Bach, <i>MARHYS (MARine HYdrothermal Solutions) Database 3.0</i>, PANGAEA, 2023, <a href="https://doi.org/10.1594/PANGAEA.958978">doi:10.1594/PANGAEA.958978</a>, CC BY 4.0, downloaded 7 November 2026.',
         'The Lost City fluid rows: pH, temperature, magnesium, with their primary sources.'),
        ("a 2018 reconstruction puts its pH",
         'J. Krissansen-Totton, G. N. Arney and D. C. Catling, &ldquo;Constraining the climate and ocean pH of the early Earth with a geological carbon cycle model&rdquo;, <i>PNAS</i> 115(16):4105&ndash;4110, 2018, <a href="https://doi.org/10.1073/pnas.1721296115">doi:10.1073/pnas.1721296115</a>.',
         'Ocean pH 6.6 (95 percent range 6.3 to 7.2) at 4.0 billion years ago. A model estimate.'),
        ("the Nernst factor",
         'National Institute of Standards and Technology, CODATA 2018 values of the molar gas constant and the Faraday constant, <a href="https://physics.nist.gov/cuu/Constants/">physics.nist.gov/cuu/Constants</a>.',
         'R and F, from which 59.2 millivolts per pH unit at 25 &deg;C follows.'),
        ("a working mitochondrion, which holds about 172",
         'BioNumbers BNID 101103, proton-motive force in perfused rat liver, 172 &plusmn; 12 mV, from Mollica et al., <i>Mol. Cell. Biochem.</i> 178:213, 1998, <a href="https://bionumbers.hms.harvard.edu/bionumber.aspx?id=101103">bionumbers.hms.harvard.edu</a>.',
         'The mitochondrial value in the text and the chart.'),
        ("a 2016 critique argued",
         'J. B. Jackson, &ldquo;Natural pH gradients in hydrothermal alkali vents were unlikely to have played a role in the origin of life&rdquo;, <i>Journal of Molecular Evolution</i> 83:1&ndash;11, 2016, <a href="https://doi.org/10.1007/s00239-016-9756-6">doi:10.1007/s00239-016-9756-6</a>.',
         'Mineral walls micrometres thick; the gradient not usable without later machinery.'),
        ("in a 2020 experiment",
         'R. Hudson et al., &ldquo;CO<sub>2</sub> reduction driven by a pH gradient&rdquo;, <i>PNAS</i> 117(37):22873&ndash;22879, 2020, <a href="https://doi.org/10.1073/pnas.2002659117">doi:10.1073/pnas.2002659117</a>.',
         'Formate at about 1.5 micromolar with pH 12.3 against 3.9; below quantification at pH 9.1; no carbon-carbon bonds.'),
        ("In 1961 Peter Mitchell",
         'P. Mitchell, &ldquo;Coupling of phosphorylation to electron and hydrogen transfer by a chemi-osmotic type of mechanism&rdquo;, <i>Nature</i> 191:144&ndash;148, 1961, <a href="https://doi.org/10.1038/191144a0">doi:10.1038/191144a0</a>.',
         'The chemiosmotic hypothesis.'),
        ("1978 Nobel Prize in Chemistry alone",
         'The Nobel Prize in Chemistry 1978, Peter Mitchell, <a href="https://www.nobelprize.org/prizes/chemistry/1978/summary/">nobelprize.org</a>.',
         'The sole award, for the chemiosmotic theory.'),
        ("each ATP costs about 2.7 protons",
         'I. N. Watt, M. G. Montgomery, M. J. Runswick, A. G. W. Leslie and J. E. Walker, &ldquo;Bioenergetic cost of making an adenosine triphosphate molecule in animal mitochondria&rdquo;, <i>PNAS</i> 107(39):16823&ndash;16827, 2010, <a href="https://doi.org/10.1073/pnas.1011099107">doi:10.1073/pnas.1011099107</a>.',
         'A c8 ring in bovine ATP synthase: 8 protons per turn, 3 ATP, 2.7 protons per ATP.'),
        ("150 to 200 millivolts across about 5 nanometres",
         'BioNumbers BNID 105801, electric field across the mitochondrial membrane, from N. Lane and W. F. Martin, &ldquo;The energetics of genome complexity&rdquo;, <i>Nature</i> 467:929&ndash;934, 2010, <a href="https://bionumbers.hms.harvard.edu/bionumber.aspx?id=105801">bionumbers.hms.harvard.edu</a>.',
         'About 150 to 200 mV over about 5 nm, some 3 &times; 10<sup>7</sup> volts a metre.'),
        ("Dry air breaks down into a spark",
         'C. R. Nave, &ldquo;Dielectric strength&rdquo;, <i>HyperPhysics</i>, Georgia State University, <a href="http://hyperphysics.phy-astr.gsu.edu/hbase/electric/dielec.html">hyperphysics.phy-astr.gsu.edu</a>.',
         'Air at about 3 million volts a metre.'),
        ("three sodium ions out and two potassium ions in",
         'R. L. Post and P. C. Jolly, &ldquo;The linkage of sodium, potassium, and ammonium active transport across the human erythrocyte membrane&rdquo;, <i>Biochim. Biophys. Acta</i> 25:118&ndash;128, 1957, <a href="https://doi.org/10.1016/0006-3002(57)90426-2">doi:10.1016/0006-3002(57)90426-2</a>.',
         'The 3:2 ratio of the sodium-potassium pump.'),
        ("Alan Hodgkin and Andrew Huxley measured in 1939",
         'A. L. Hodgkin and A. F. Huxley, &ldquo;Action potentials recorded from inside a nerve fibre&rdquo;, <i>Nature</i> 144:710&ndash;711, 1939, <a href="https://doi.org/10.1038/144710a0">doi:10.1038/144710a0</a>.',
         'A resting potential of about 50 mV and spikes of 80 to 95 mV in the squid giant axon.'),
        ("takes about 20 percent of the body's oxygen at rest",
         'M. E. Raichle and D. A. Gusnard, &ldquo;Appraising the brain&rsquo;s energy budget&rdquo;, <i>PNAS</i> 99(16):10237&ndash;10239, 2002, <a href="https://doi.org/10.1073/pnas.172399499">doi:10.1073/pnas.172399499</a>.',
         'The brain at about 2 percent of body weight and about 20 percent of oxygen use.'),
        ("A 2012 model of rat cortex",
         'C. Howarth, P. Gleeson and D. Attwell, &ldquo;Updated energy budgets for neural computation in the neocortex and cerebellum&rdquo;, <i>J. Cereb. Blood Flow Metab.</i> 32(7):1222&ndash;1232, 2012, <a href="https://doi.org/10.1038/jcbfm.2012.35">doi:10.1038/jcbfm.2012.35</a>.',
         'Signalling energy split: postsynaptic 50 percent, action potentials 21, resting potentials 20; most of it spent pumping sodium out.'),
        ("a spike reverses the beat of its cilia",
         'R. Eckert, &ldquo;Bioelectric control of ciliary activity&rdquo;, <i>Science</i> 176:473&ndash;481, 1972, <a href="https://doi.org/10.1126/science.176.4034.473">doi:10.1126/science.176.4034.473</a>; and Y. Naitoh and R. Eckert, <i>Science</i> 164:963&ndash;965, 1969, <a href="https://doi.org/10.1126/science.164.3882.963">doi:10.1126/science.164.3882.963</a>.',
         'The avoiding reaction: a front-end touch, calcium entry, ciliary reversal.'),
        ("The oldest widely accepted traces of life",
         'T. Djokic, M. J. Van Kranendonk, K. A. Campbell, M. R. Walter and C. R. Ward, &ldquo;Earliest signs of life on land preserved in ca. 3.5 Ga hot spring deposits&rdquo;, <i>Nature Communications</i> 8:15263, 2017, <a href="https://doi.org/10.1038/ncomms15263">doi:10.1038/ncomms15263</a>.',
         'The Dresser Formation, Pilbara, about 3.48 billion years; older claims are disputed.'),
        ("the oldest fossil brain",
         'X. Ma, X. Hou, G. D. Edgecombe and N. J. Strausfeld, &ldquo;Complex brain and optic lobes in an early Cambrian arthropod&rdquo;, <i>Nature</i> 490:258&ndash;261, 2012, <a href="https://doi.org/10.1038/nature11495">doi:10.1038/nature11495</a>.',
         '<i>Fuxianhuia protensa</i>, Chengjiang, about 520 million years.'),
        ("ICS chart 2024",
         'International Commission on Stratigraphy, <i>International Chronostratigraphic Chart</i>, v2024/12, <a href="https://stratigraphy.org/chart">stratigraphy.org/chart</a>; with the other timeline sources listed row by row in timeline.csv in the code archive.',
         'Era boundaries; the base of the Cambrian at 538.8 million years.'),
        ("defines it as an unpleasant sensory and emotional experience",
         'S. N. Raja et al., &ldquo;The revised International Association for the Study of Pain definition of pain: concepts, challenges, and compromises&rdquo;, <i>Pain</i> 161(9):1976&ndash;1982, 2020, <a href="https://doi.org/10.1097/j.pain.0000000000001939">doi:10.1097/j.pain.0000000000001939</a>.',
         'The 2020 definition, including experiences that resemble those tied to tissue damage, and the separation of pain from nociception.'),
        ("Walter Cannon named the process homeostasis in 1926",
         'W. B. Cannon, &ldquo;Organization for physiological homeostasis&rdquo;, <i>Physiological Reviews</i> 9(3):399&ndash;431, 1929, <a href="https://doi.org/10.1152/physrev.1929.9.3.399">doi:10.1152/physrev.1929.9.3.399</a>; Claude Bernard, <i>Introduction &agrave; l&rsquo;&eacute;tude de la m&eacute;decine exp&eacute;rimentale</i>, 1865.',
         'The internal environment (Bernard) and homeostasis (Cannon, first used in 1926).'),
        ("stays between 7.35 and 7.45",
         'E. Hopkins, T. Sanvictores and S. Sharma, &ldquo;Physiology, acid base balance&rdquo;, <i>StatPearls</i>, NCBI Bookshelf, <a href="https://www.ncbi.nlm.nih.gov/books/NBK507807/">NBK507807</a>.',
         'The normal range of arterial blood pH.'),
        ("In 1971 Michel Cabanac showed",
         'M. Cabanac, &ldquo;Physiological role of pleasure&rdquo;, <i>Science</i> 173:1103&ndash;1107, 1971, <a href="https://doi.org/10.1126/science.173.4002.1103">doi:10.1126/science.173.4002.1103</a>.',
         'Alliesthesia: the pleasantness of a stimulus depends on the internal state.'),
        ("Bud Craig argued that pain is a homeostatic emotion",
         'A. D. Craig, &ldquo;A new view of pain as a homeostatic emotion&rdquo;, <i>Trends in Neurosciences</i> 26(6):303&ndash;307, 2003, <a href="https://doi.org/10.1016/S0166-2236(03)00123-1">doi:10.1016/S0166-2236(03)00123-1</a>.',
         'Pain as a feeling that reports the body&rsquo;s state and motivates a response.'),
        ("In 2006 a team traced",
         'J. J. Cox et al., &ldquo;An SCN9A channelopathy causes congenital inability to experience pain&rdquo;, <i>Nature</i> 444:894&ndash;898, 2006, <a href="https://doi.org/10.1038/nature05413">doi:10.1038/nature05413</a>.',
         'SCN9A in three families from northern Pakistan; the street performer who died on his 14th birthday.'),
        ("a 1994 review of about 31 published cases",
         'S. Rosemberg, S. K. Marie and S. Kliemann, &ldquo;Congenital insensitivity to pain with anhidrosis (hereditary sensory and autonomic neuropathy type IV)&rdquo;, <i>Pediatric Neurology</i> 11(1):50&ndash;56, 1994, <a href="https://doi.org/10.1016/0887-8994(94)90091-4">doi:10.1016/0887-8994(94)90091-4</a>; via OMIM 256800.',
         'Almost 20 percent dying of hyperpyrexia within the first three years.'),
        ("The ASHRAE Global Thermal Comfort Database II holds",
         'V. F&ouml;ldv&aacute;ry Li&ccaron;ina et al., &ldquo;Development of the ASHRAE Global Thermal Comfort Database II&rdquo;, <i>Building and Environment</i> 142:502&ndash;512, 2018, <a href="https://doi.org/10.1016/j.buildenv.2018.06.022">doi:10.1016/j.buildenv.2018.06.022</a>; data version 2.1.0, <a href="https://zenodo.org/records/4993952">Zenodo 4993952</a>, CC BY 4.0, downloaded 7 November 2026.',
         'The 109,033 records, the preference and sensation votes, and the outdoor temperatures.'),
        ("adaptive model in the ASHRAE 55 standard",
         'R. J. de Dear and G. S. Brager, &ldquo;Thermal comfort in naturally ventilated buildings: revisions to ASHRAE Standard 55&rdquo;, <i>Energy and Buildings</i> 34(6):549&ndash;561, 2002, <a href="https://doi.org/10.1016/S0378-7788(02)00005-1">doi:10.1016/S0378-7788(02)00005-1</a>.',
         'The adaptive comfort line, 0.31 times prevailing mean outdoor temperature plus 17.8.'),
        ("Michael Humphreys and Fergus Nicol reported",
         'M. A. Humphreys and J. F. Nicol, &ldquo;Do people like to feel &lsquo;neutral&rsquo;? Response to the ASHRAE scale of subjective warmth in relation to thermal preference, indoor and outdoor temperature&rdquo;, <i>ASHRAE Transactions</i> 110(2), 2004.',
         'Sensation votes depend on outdoor temperature; preference votes much less.'),
        ("Colin Pittendrigh proposed the word teleonomy",
         'C. S. Pittendrigh, &ldquo;Adaptation, natural selection, and behavior&rdquo;, in A. Roe and G. G. Simpson (eds.), <i>Behavior and Evolution</i>, Yale University Press, 1958, pp. 390&ndash;416.',
         'The coinage of teleonomy.'),
        ("Ernst Mayr sharpened the distinction",
         'E. Mayr, &ldquo;Teleological and teleonomic, a new analysis&rdquo;, in R. S. Cohen and M. W. Wartofsky (eds.), <i>Boston Studies in the Philosophy of Science</i> 14:91&ndash;117, 1974, <a href="https://doi.org/10.1007/978-94-010-2128-9_6">doi:10.1007/978-94-010-2128-9_6</a>.',
         'Goal-directed behaviour under a program, as distinct from purpose.'),
        ("in a note added to later printings",
         'E. Schr&ouml;dinger, <i>What Is Life?</i>, Cambridge University Press, 1944, chapter 6; and the note to chapter 6 added in later printings, <a href="https://archive.org/details/WhatIsLife-EdwardSchrodinger">archive.org</a>.',
         'Order from the surroundings; the note that free energy is the better term.'),
        ("Jeremy England argues",
         'J. L. England, &ldquo;Statistical physics of self-replication&rdquo;, <i>J. Chem. Phys.</i> 139:121923, 2013, <a href="https://doi.org/10.1063/1.4818538">doi:10.1063/1.4818538</a>; and &ldquo;Dissipative adaptation in driven self-assembly&rdquo;, <i>Nature Nanotechnology</i> 10:919&ndash;923, 2015, <a href="https://doi.org/10.1038/nnano.2015.250">doi:10.1038/nnano.2015.250</a>.',
         'Dissipative adaptation. Supported by idealised models.'),
        ("free energy principle holds",
         'K. Friston, &ldquo;The free-energy principle: a unified brain theory?&rdquo;, <i>Nature Reviews Neuroscience</i> 11:127&ndash;138, 2010, <a href="https://doi.org/10.1038/nrn2787">doi:10.1038/nrn2787</a>.',
         'The principle.'),
        ("cannot be falsified as mathematics",
         'K. Friston et al., &ldquo;The free energy principle made simpler but not too simple&rdquo;, <i>Physics Reports</i> 1024:1&ndash;29, 2023, <a href="https://doi.org/10.1016/j.physrep.2023.07.001">doi:10.1016/j.physrep.2023.07.001</a>; for critiques, J. Bruineberg et al., <i>Behavioral and Brain Sciences</i> 45:e183, 2022.',
         'The authors&rsquo; statement that the principle is not falsifiable as mathematics, compared with Hamilton&rsquo;s principle.'),
        ("capture about a thousandth of the sunlight Earth absorbs",
         'C. B. Field, M. J. Behrenfeld, J. T. Randerson and P. Falkowski, &ldquo;Primary production of the biosphere: integrating terrestrial and oceanic components&rdquo;, <i>Science</i> 281:237&ndash;240, 1998, <a href="https://doi.org/10.1126/science.281.5374.237">doi:10.1126/science.281.5374.237</a>; K. E. Trenberth, J. T. Fasullo and J. Kiehl, <i>Bull. Amer. Meteor. Soc.</i> 90:311&ndash;324, 2009, <a href="https://doi.org/10.1175/2008BAMS2634.1">doi:10.1175/2008BAMS2634.1</a>.',
         'Net primary production of 104.9 Pg C a year, about 130 TW at 39 kJ per gram of carbon, against about 240 W/m&sup2; of absorbed sunlight over the Earth (about 122,000 TW): about 0.1 percent. This page&rsquo;s arithmetic.'),
        ("about 4.2 billion years ago on a 2024 estimate",
         'E. R. R. Moody et al., &ldquo;The nature of the last universal common ancestor and its impact on the early Earth system&rdquo;, <i>Nature Ecology &amp; Evolution</i> 8:1654&ndash;1666, 2024, <a href="https://doi.org/10.1038/s41559-024-02461-1">doi:10.1038/s41559-024-02461-1</a>.',
         'LUCA at about 4.2 billion years (4.09 to 4.33). A model estimate.'),
        ("when a mould's respiration was blocked in 1965",
         'C. L. Slayman, &ldquo;Electrical properties of <i>Neurospora crassa</i>: respiration and the intracellular potential&rdquo;, <i>J. Gen. Physiol.</i> 49:93&ndash;116, 1965, <a href="https://doi.org/10.1085/jgp.49.1.93">doi:10.1085/jgp.49.1.93</a>.',
         'A membrane potential near &minus;200 mV collapsing to about &minus;30 mV within a minute of blocking respiration.'),
        ("Reyer et al. 2020",
         'A. Reyer et al., &ldquo;Channelrhodopsin-mediated optogenetics highlights a central role of depolarization-dependent plant proton pumps&rdquo;, <i>PNAS</i> 117(34):20920&ndash;20925, 2020, <a href="https://doi.org/10.1073/pnas.2005626117">doi:10.1073/pnas.2005626117</a>.',
         'Leaf mesophyll membrane potential of about &minus;160 to &minus;180 mV.'),
        ("Lo et al. 2007",
         'C.-J. Lo, M. C. Leake, T. Pilizota and R. M. Berry, &ldquo;Nonequivalence of membrane voltage and ion-gradient as driving forces for the bacterial flagellar motor at low load&rdquo;, <i>Biophysical Journal</i> 93:294&ndash;302, 2007, <a href="https://doi.org/10.1529/biophysj.106.095265">doi:10.1529/biophysj.106.095265</a>.',
         '<i>E. coli</i> membrane voltage of &minus;140 &plusmn; 14 mV at pH 7.'),
        ("vented for more than 100,000 years",
         'K. A. Ludwig, C.-C. Shen, D. S. Kelley, H. Cheng and R. L. Edwards, &ldquo;U&ndash;Th systematics and <sup>230</sup>Th ages of carbonate chimneys at the Lost City Hydrothermal Field&rdquo;, <i>Geochimica et Cosmochimica Acta</i> 75:1869&ndash;1888, 2011, <a href="https://doi.org/10.1016/j.gca.2011.01.008">doi:10.1016/j.gca.2011.01.008</a>.',
         'Chimney ages up to 120,000 &plusmn; 13,000 years.'),
    ],
    # The sub-3 marathon (sub3-marathon lane, 2026-11-13). sub3/update_page.py applies this entry itself
    # (ethane's idiom). Data files and hashes in sub3/data/fetched.json; the papers were read by the lane's
    # research and fact-check agents (03 RESEARCH/nov-2026-batch2/sub3-marathon/research).
    "sub3.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("Seffrin and others (2026)",
         'A. Seffrin, E. Villiger, M. S. Andrade, T. Rosemann, K. Weiss, D. Ferreira and B. Knechtle, <i>BMW Berlin Marathon Results 1999&ndash;2025</i>, Zenodo, 2026, doi:10.5281/zenodo.19342683, CC BY 4.0, fetched 13 November 2026.',
         'Every Berlin figure on this page: finish times, halfway and 5-km splits, sex, by year.'),
        ("51.4 percent more runners",
         'E. J. Allen, P. M. Dechow, D. G. Pope and G. Wu, &ldquo;Reference-Dependent Preferences: Evidence from Marathon Runners&rdquo;, <i>Management Science</i> 63(6), 2017, 1657&ndash;1672 (NBER Working Paper 20343, 2014).',
         'The bunching of 9.5 million finishes just before round-number times, including 3:00.'),
        ("broken repeatedly from 2003 to 2022",
         'World Athletics, marathon world record progression (men); the records of 2003, 2007, 2008, 2011, 2013, 2014, 2018 and 2022 were set in Berlin.',
         'The men&rsquo;s world records set in Berlin from 2003 to 2022.'),
        ("Jack Daniels and Jimmy Gilbert's running formula",
         'J. Daniels and J. Gilbert, <i>Oxygen Power: Performance Tables for Distance Runners</i>, 1979.',
         'The VDOT equations: the oxygen cost of a running speed and the fraction of VO2max held for a given time; the equivalent half-marathon times.'),
        ("Michael Joyner's model of the marathon",
         'M. J. Joyner, &ldquo;Modeling: optimal marathon performance on the basis of physiological factors&rdquo;, <i>Journal of Applied Physiology</i> 70(2), 1991, 683&ndash;687.',
         'Marathon speed from VO2max, the fraction of it held and running economy.'),
        ("Elite marathoners hold about 75 to 85 percent of VO2max",
         'M. J. Joyner and E. F. Coyle, &ldquo;Endurance exercise performance: the physiology of champions&rdquo;, <i>Journal of Physiology</i> 586(1), 2008, 35&ndash;44.',
         'The fraction of VO2max held by elite marathoners.'),
        ("the slowest held about 60",
         'R. J. Maughan and J. B. Leiper, &ldquo;Aerobic capacity and fractional utilisation of aerobic capacity in elite and non-elite male and female marathon runners&rdquo;, <i>European Journal of Applied Physiology and Occupational Physiology</i> 52(1), 1983, 80&ndash;87.',
         'About 60 percent of VO2max for the slowest of 28 finishers of one marathon.'),
        ("Michele Zanini and colleagues",
         'M. Zanini, J. P. Folland and R. C. Blagrove, &ldquo;The effect of 90 and 120 min of running on the determinants of endurance performance in well-trained male marathon runners&rdquo;, <i>Scandinavian Journal of Medicine &amp; Science in Sports</i> 35(5), 2025, e70076.',
         'Lactate-threshold speed of 14.0, 13.5 and 13.0 km/h fresh, after 90 and after 120 minutes at 14.1 km/h, in 14 well-trained male marathoners.'),
        ("began to drift up against pace at about 25 km on average",
         'B. Smyth, E. Maunder, S. Meyler, B. Hunter and D. Muniz-Pumares, &ldquo;Decoupling of internal and external workload during a marathon: an analysis of durability in 82,303 recreational runners&rdquo;, <i>Sports Medicine</i> 52(9), 2022, 2283&ndash;2295.',
         'Heart rate against pace in 82,303 marathoners; the first decoupling at about 25 km.'),
        ("about 1 kilocalorie per kilogram of body weight per kilometre",
         'B. I. Rapoport, &ldquo;Metabolic factors limiting performance in marathon runners&rdquo;, <i>PLoS Computational Biology</i> 6(10), 2010, e1000960.',
         'About 1 kcal per kg per km and 2,950 kcal for a 70 kg runner; glycogen stores of about 88 g in the liver and 310 g in the leg muscles.'),
        ("measured at 72 percent of VO2max in trained cyclists",
         'L. J. C. van Loon, P. L. Greenhaff, D. Constantin-Teodosiu, W. H. M. Saris and A. J. M. Wagenmakers, &ldquo;The effects of increasing exercise intensity on muscle fuel utilisation in humans&rdquo;, <i>Journal of Physiology</i> 536, 2001, 295&ndash;304.',
         'Carbohydrate supplied 76 percent of energy at 72 percent of VO2max.'),
        ("Smyth found that about a third of runners hit the wall",
         'B. Smyth, &ldquo;How recreational marathon runners hit the wall: a large-scale data analysis of late-race pacing collapse in the marathon&rdquo;, <i>PLoS ONE</i> 16(5), 2021, e0251513.',
         'About 34 percent of 4.18 million race records met the definition; mean onset at about 29.5 km.'),
        ("taking up to 90 grams an hour",
         'D. T. Thomas, K. A. Erdman and L. M. Burke, &ldquo;Nutrition and Athletic Performance&rdquo;, joint position statement, <i>Medicine &amp; Science in Sports &amp; Exercise</i> 48(3), 2016, 543&ndash;568.',
         'Carbohydrate loading of 10 to 12 g per kg a day for 36 to 48 hours before events over 90 minutes; up to 90 g of carbohydrate an hour during events longer than 2.5 to 3 hours.'),
        ("seven runners on a treadmill in 1995",
         'O. K. Tsintzas, C. Williams, R. Singh, W. Wilson and J. Burrin, &ldquo;Influence of carbohydrate-electrolyte drinks on marathon running performance&rdquo;, <i>European Journal of Applied Physiology and Occupational Physiology</i> 70(2), 1995, 154&ndash;160.',
         'Seven trained runners, three treadmill marathons: 190.0 minutes with a 5.5 percent carbohydrate drink against 193.9 with water.'),
        ("hourly readings from the German weather service (DWD)",
         'Deutscher Wetterdienst, Climate Data Center, hourly air temperature, station 433 Berlin-Tempelhof, 1951&ndash;2025 (stundenwerte_TU_00433), fetched 13 November 2026.',
         'The race-morning temperatures, 09:00 to 13:00 local time.'),
        ("Nour El Helou and colleagues",
         'N. El Helou, M. Tafflet, G. Berthelot and others, &ldquo;Impact of environmental parameters on marathon running performance&rdquo;, <i>PLoS ONE</i> 7(5), 2012, e37407.',
         '1.79 million finishes at six marathons; air temperature as the main weather factor; best performances at roughly 4 to 10 &deg;C.'),
        ("Matthew Ely and colleagues",
         'M. R. Ely, S. N. Cheuvront, W. O. Roberts and S. J. Montain, &ldquo;Impact of weather on marathon-running performance&rdquo;, <i>Medicine &amp; Science in Sports &amp; Exercise</i> 39(3), 2007, 487&ndash;493.',
         'Slowing with rising temperature, larger for slower runners.'),
        ("Faster runners pace more evenly in the large studies",
         'R. O. Deaner, R. E. Carter, M. J. Joyner and S. K. Hunter, &ldquo;Men are more likely than women to slow in the marathon&rdquo;, <i>Medicine &amp; Science in Sports &amp; Exercise</i> 47(3), 2015, 607&ndash;616.',
         'Second-half slowing in 91,929 performances at 14 U.S. marathons; faster runners slowed less.'),
        ("Smyth and Daniel Muniz-Pumares",
         'B. Smyth and D. Muniz-Pumares, &ldquo;Calculation of critical speed from raw training data in recreational marathon runners&rdquo;, <i>Medicine &amp; Science in Sports &amp; Exercise</i> 52(12), 2020, 2637&ndash;2645.',
         'More than 25,000 runners; a start faster than critical speed raised the share who slowed by more than 25 percent from 17 to 23 percent.'),
        ("a 2025 review of 24 trials",
         'D. J. Ramos-Campo, C. Foster, L. Andreu-Caravaca, J. &Aacute;. Rubio-Arias and M. A. Rosenblat, &ldquo;Comparative Effects of Pacing Strategies on Endurance Performance: A Systematic Review and Network Meta-Analysis&rdquo;, <i>Sports Medicine</i> 56(3), 2026, 725&ndash;738 (online November 2025).',
         'No imposed pacing strategy beat self-selected pacing; 24 studies, 302 participants.'),
        ("enter the Boston Marathon in 2027",
         'Boston Athletic Association, &ldquo;Qualify&rdquo; (qualifying standards for the 2027 Boston Marathon) and its announcement of 29 September 2026 of the 2027 cutoff.',
         'Standards of 2:55:00 and 3:25:00 for ages 18 to 34; the cutoff of 5 minutes 17 seconds.'),
        ("ran 1:59:30 in London on 26 April 2026",
         'World Athletics, race report, London Marathon, 26 April 2026, and the press release of 23 July 2026 on ratified world records.',
         'Sawe&rsquo;s 1:59:30 and Assefa&rsquo;s 2:15:41, and their ratification.'),
        ("entry standard for the 2028 U.S. Olympic Marathon Trials",
         'USA Track &amp; Field, release of 2 June 2025 announcing the standards for the 2028 U.S. Olympic Team Trials &ndash; Marathon.',
         'The men&rsquo;s entry (&ldquo;B&rdquo;) standard of 2:16:00.'),
        ("Most modern men's world records have been run",
         'J. J. Díaz, A. Fernández-Ozcorta, M. Torres and J. Santos-Concejero, &ldquo;Men vs. women world marathon records&rsquo; pacing strategies from 1998 to 2018&rdquo;, <i>European Journal of Sport Science</i> 19(10), 2019, 1297&ndash;1302.',
         'Men&rsquo;s world records from 1998 to 2018 ran faster in the second half on average.'),
    ],
    "scales.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("found that the resting heat of warm-blooded animals",
         'M. Kleiber, &ldquo;Body size and metabolism&rdquo;, <i>Hilgardia</i> 6(11):315&ndash;353 (1932), <a href="https://doi.org/10.3733/hilg.v06n11p315">doi:10.3733/hilg.v06n11p315</a>.',
         'Resting heat production of mammals and birds rising with body mass to about the three-quarter power.'),
        ("the ecologist Ian Hatton and four colleagues",
         'I. A. Hatton, A. P. Dobson, D. Storch, E. D. Galbraith and M. Loreau, &ldquo;Linking scaling laws across eukaryotes&rdquo;, <i>PNAS</i> 116(43):21616&ndash;21622 (2019), <a href="https://doi.org/10.1073/pnas.1900492116">doi:10.1073/pnas.1900492116</a>; data and code, <a href="https://doi.org/10.5281/zenodo.3145281">Zenodo 3145281</a> (CC BY 4.0).',
         'The 8,098 resting metabolism measurements, the temperature correction and aggregation method rerun here, and the 70 kg human row.'),
        ("Anastassia Makarieva and colleagues reported",
         'A. M. Makarieva and others, &ldquo;Mean mass-specific metabolic rates are strikingly similar across life&rsquo;s major domains&rdquo;, <i>PNAS</i> 105(44):16994&ndash;16999 (2008), <a href="https://doi.org/10.1073/pnas.0802148105">doi:10.1073/pnas.0802148105</a>.',
         'Group means of about 0.3 to 9 W/kg across 3,006 species; growing unicells at 10 to 20 times their starved rates.'),
        ("in 2002 West and colleagues argued",
         'G. B. West, W. H. Woodruff and J. H. Brown, &ldquo;Allometric scaling of metabolic rate from molecules and mitochondria to cells and mammals&rdquo;, <i>PNAS</i> 99(suppl. 1):2473&ndash;2478 (2002), <a href="https://doi.org/10.1073/pnas.012579799">doi:10.1073/pnas.012579799</a>.',
         'One three-quarter-power line extended from mitochondria and cells to whole mammals.'),
        ("derived three quarters in 1997",
         'G. B. West, J. H. Brown and B. J. Enquist, &ldquo;A general model for the origin of allometric scaling laws in biology&rdquo;, <i>Science</i> 276:122&ndash;126 (1997), <a href="https://doi.org/10.1126/science.276.5309.122">doi:10.1126/science.276.5309.122</a>.',
         'The branching-network model that derives a three-quarter exponent.'),
        ("later work found the exponent curved",
         'T. Kolokotrones, V. Savage, E. J. Deeds and W. Fontana, &ldquo;Curvature in metabolic scaling&rdquo;, <i>Nature</i> 464:753&ndash;756 (2010), <a href="https://doi.org/10.1038/nature08920">doi:10.1038/nature08920</a>.',
         'Curvature of the mammal relation on log axes; the exponent is not one number.'),
        ("Sustained metabolic rates of free-ranging animals",
         'C. C. Peterson, K. A. Nagy and J. Diamond, &ldquo;Sustained metabolic scope&rdquo;, <i>PNAS</i> 87(6):2324&ndash;2328 (1990), <a href="https://doi.org/10.1073/pnas.87.6.2324">doi:10.1073/pnas.87.6.2324</a>.',
         'Sustained metabolic rates of free-ranging animals of up to about 7 times resting rates, most 1.5 to 5 times.'),
        ("The International Astronomical Union fixes",
         'A. Pr&scaron;a and others, &ldquo;Nominal values for selected solar and planetary quantities: IAU 2015 Resolution B3&rdquo;, <i>Astronomical Journal</i> 152:41 (2016), <a href="https://arxiv.org/abs/1605.09788">arXiv:1605.09788</a>.',
         'Nominal solar luminosity 3.828 &times; 10<sup>26</sup> W, effective temperature 5,772 K and solar mass parameter 1.3271244 &times; 10<sup>20</sup> m<sup>3</sup> s<sup>&minus;2</sup>.'),
        ("CODATA 2018 gravitational constant",
         'E. Tiesinga and others, &ldquo;CODATA recommended values of the fundamental physical constants: 2018&rdquo;, <i>Reviews of Modern Physics</i> 93:025010 (2021), <a href="https://physics.nist.gov/cgi-bin/cuu/Value?bg">NIST</a>.',
         'G = 6.67430 &times; 10<sup>&minus;11</sup> m<sup>3</sup> kg<sup>&minus;1</sup> s<sup>&minus;2</sup>.'),
        ("Zeki Eker, an astronomer",
         'Z. Eker and others, &ldquo;Interrelated main-sequence mass&ndash;luminosity, mass&ndash;radius, and mass&ndash;effective temperature relations&rdquo;, <i>MNRAS</i> 479:5491&ndash;5511 (2018), <a href="https://arxiv.org/abs/1807.02568">arXiv:1807.02568</a>; table, <a href="https://vizier.cfa.harvard.edu/viz-bin/VizieR?-source=J/MNRAS/479/5491">VizieR J/MNRAS/479/5491</a>.',
         'Masses, radii and temperatures of 509 main-sequence stars in detached eclipsing binaries, 0.179 to 31 solar masses.'),
        ("The reason is physical, not biological",
         'A. S. Eddington, &ldquo;On the relation between the masses and luminosities of the stars&rdquo;, <i>MNRAS</i> 84:308&ndash;333 (1924), <a href="https://doi.org/10.1093/mnras/84.5.308">doi:10.1093/mnras/84.5.308</a>.',
         'The mass&ndash;luminosity relation of stars from their internal structure: luminosity set by how fast radiation escapes.'),
        ("Eric Chaisson, an astrophysicist at Harvard",
         'E. J. Chaisson, &ldquo;Energy rate density as a complexity metric and evolutionary driver&rdquo;, <i>Complexity</i> 16(3):27&ndash;40 (2011), <a href="https://doi.org/10.1002/cplx.20323">doi:10.1002/cplx.20323</a>.',
         'Free energy rate density from galaxies to society.'),
        ("As a law it is weak",
         'K. Solis, &ldquo;Reexamining &lsquo;Free Energy Rate Density&rsquo; as a Complexity Metric&rdquo;, <i>Journal of Big History</i> 7(1):19&ndash;28 (2024), <a href="https://doi.org/10.22339/jbh.v7i1.7102">doi:10.22339/jbh.v7i1.7102</a>.',
         'That energy rate density has not been tested against other measures of complexity.'),
        ("the Energy Institute's statistics",
         'Our World in Data, &ldquo;Primary energy use per person&rdquo;, from the Energy Institute <i>Statistical Review of World Energy</i> (2026) and the U.S. EIA, <a href="https://ourworldindata.org/grapher/per-capita-energy-use">ourworldindata.org</a> (CC BY 4.0).',
         'Total energy supply per person by country, in kilowatt-hours a year.'),
        ("Geoffrey West and colleagues reported",
         'L. M. A. Bettencourt, J. Lobo, D. Helbing, C. K&uuml;hnert and G. B. West, &ldquo;Growth, innovation, scaling, and the pace of life in cities&rdquo;, <i>PNAS</i> 104(17):7301&ndash;7306 (2007), <a href="https://doi.org/10.1073/pnas.0610172104">doi:10.1073/pnas.0610172104</a>.',
         'Table 1: superlinear exponents for economic outputs, sublinear for road surface (0.83) and electrical cable length (0.87), household electricity at 1.00 (Germany) and 1.05 (China), US gasoline sales at 0.79.'),
        ("Bureau of Economic Analysis's county GDP",
         'U.S. Bureau of Economic Analysis, CAGDP1, GDP by county (line 3, current dollars), <a href="https://apps.bea.gov/regional/downloadzip.htm">apps.bea.gov</a>; U.S. Census Bureau, metropolitan and micropolitan population estimates 2020&ndash;2023, <a href="https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/metro/totals/">census.gov</a>.',
         'County GDP and metro population for the fit on this page.'),
        ("Michail Fragkias and colleagues found",
         'M. Fragkias, J. Lobo, D. Strumsky and K. C. Seto, &ldquo;Does size matter? Scaling of CO<sub>2</sub> emissions and U.S. urban areas&rdquo;, <i>PLoS ONE</i> 8(6):e64727 (2013), <a href="https://doi.org/10.1371/journal.pone.0064727">doi:10.1371/journal.pone.0064727</a>.',
         'An exponent of about 0.93 for fossil-fuel CO<sub>2</sub> of US metropolitan and micropolitan areas, and about 1 with density and income controls.'),
        ("Elsa Arcaute and colleagues",
         'E. Arcaute and others, &ldquo;Constructing cities, deconstructing scaling laws&rdquo;, <i>Journal of the Royal Society Interface</i> 12:20140745 (2015), <a href="https://doi.org/10.1098/rsif.2014.0745">doi:10.1098/rsif.2014.0745</a>.',
         'Scaling exponents of cities in England and Wales under thousands of boundary definitions.'),
    ],
    # Lane algae-carbon, 2026-11-13: the algae page (algae/update_page.py applies this table itself).
    "algae.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("in the estimate of Field and colleagues",
         'Field CB, Behrenfeld MJ, Randerson JT, Falkowski P. &ldquo;Primary production of the biosphere: integrating '
         'terrestrial and oceanic components&rdquo;. <i>Science</i> 281(5374):237&ndash;240, 1998.',
         'Ocean net primary production 48.5 Pg C a year, 1.0 of it macroalgae; land 56.4 (Table 1).'),
        ("One newer satellite model gives a lower total",
         'Kulk G, Platt T, Dingle J, et al. &ldquo;Primary production, an index of climate change in the ocean: '
         'satellite-based estimates over two decades&rdquo;. <i>Remote Sensing</i> 12(5):826, 2020.',
         'Phytoplankton primary production 38.8 to 42.1 Pg C a year, 1998&ndash;2018, one model; published satellite estimates about 32 to 70.7.'),
        ("according to the Global Carbon Budget",
         'Friedlingstein P, et al. &ldquo;Global Carbon Budget 2025&rdquo;. <i>Earth System Science Data</i> '
         '18:3211&ndash;3288, 2026. Data: Global_Carbon_Budget_2025_v1.0.xlsx, ICOS Carbon Portal. CC BY 4.0.',
         'Fossil and cement emissions in 2024; the ocean sink, 2015&ndash;2024 mean.'),
        ("2021 assessment attributes that uptake",
         'Canadell JG, Monteiro PMS, et al. &ldquo;Global Carbon and other Biogeochemical Cycles and '
         'Feedbacks&rdquo;. In <i>Climate Change 2021: The Physical Science Basis</i>, IPCC AR6 WG1, Chapter 5, '
         'Section 5.2.1.3, Figure 5.12 and Cross-Chapter Box 5.3, 2021.',
         'The ocean sink is mainly physical and chemical; the biological pump&rsquo;s role in it is assessed as minimal (Box 5.3); the natural cycle drawn in balance (Figure 5.12).'),
        ("Satellite-based estimates of this export range",
         'Siegel DA, DeVries T, Cetini&cacute; I, Bisson KM. &ldquo;Quantifying the ocean&rsquo;s biological '
         'pump and its carbon cycle impacts on global scales&rdquo;. <i>Annual Review of Marine Science</i> '
         '15:329&ndash;356, 2023.',
         'Satellite-based export below about 100 m of 4 to 10 Pg C a year (Table 1); sediment burial 0.02 to 0.2 Pg C a year (p. 330).'),
        ("The RECCAP2 synthesis",
         'Doney SC, Mitchell KA, Henson SA, et al. &ldquo;Observational and numerical modeling constraints on the '
         'global ocean biological carbon pump&rdquo;. <i>Global Biogeochemical Cycles</i> 38, e2024GB008156, 2024.',
         'Flux at 1,000 m: model mean 0.65, observation-based mean 0.95 Pg C a year (Table 5).'),
        ("Karen Filbee-Dexter and colleagues",
         'Filbee-Dexter K, Pessarrodona A, Pedersen MF, et al. &ldquo;Carbon export from seaweed forests to deep '
         'ocean sinks&rdquo;. <i>Nature Geoscience</i> 17:552&ndash;559, 2024.',
         '4 to 44 Tg C a year from brown-seaweed forests held for 100 years, of 317 Tg C a year production.'),
        ("the oceanographer David Siegel",
         'Siegel DA, DeVries T, Doney SC, Bell T. &ldquo;Assessing the sequestration time scales of some ocean-based '
         'carbon dioxide reduction strategies&rdquo;. <i>Environmental Research Letters</i> 16:104003, 2021. Data: '
         '&ldquo;CO2 sequestration fractions&rdquo;, figshare 15228690, CC0.',
         'The fraction of CO2 released at each depth that stays out of the air over time; the 208 m check.'),
        ("DeAngelo and colleagues sampled this removal fraction",
         'DeAngelo J, Saenz BT, Arzeno-Soltero IB, et al. &ldquo;Economic and biophysical limits to seaweed farming '
         'for climate change mitigation&rdquo;. <i>Nature Plants</i> 9:45&ndash;57, 2023.',
         'Removal fraction sampled from 0.4 to 1, literature values 0.4 to 0.75 (Table 1); costs of $480, $830 and typical runs of $1,120 to $2,090 a tonne of CO2; costs below $400 only above a fraction of 0.6.'),
        ("ocean-model runs by Berger and colleagues",
         'Berger M, Kwiatkowski L, Ho DT, Bopp L. &ldquo;Ocean dynamics and biological feedbacks limit the potential '
         'of macroalgae carbon dioxide removal&rdquo;. <i>Environmental Research Letters</i> 18:024039, 2023.',
         'Air-sea removal efficiency of macroalgae farming, 0.58 with and 0.79 without nutrient feedbacks.'),
        ("Bach and colleagues showed in 2021",
         'Bach LT, Tamsitt V, Gower J, et al. &ldquo;Testing the climate intervention potential of ocean '
         'afforestation using the Great Atlantic Sargassum Belt&rdquo;. <i>Nature Communications</i> 12:2556, 2021.',
         'Nutrient reallocation and calcification by epibionts reduce the CO2 removal of sinking seaweed.'),
        ("a company in Portland, Maine",
         'Simson A, Rabinowitz R. &ldquo;Under the sea: Running Tide&rsquo;s ill-fated adventure in ocean carbon '
         'removal&rdquo;. <i>Canary Media</i>, 19 September 2024; Running Tide press release, 19 March 2024; RÚV reporting of about 19,000 tonnes, via <i>Portland Press Herald</i>, 17 June 2024.',
         'Alkaline-coated wood sunk off Iceland in 2023, buyers, in-house verification, closure in June 2024.'),
        ("the EIFEX experiment",
         'Smetacek V, Klaas C, Strass VH, et al. &ldquo;Deep carbon export from a Southern Ocean iron-fertilized '
         'diatom bloom&rdquo;. <i>Nature</i> 487:313&ndash;319, 2012. Experiment record: Yoon JE, et al. '
         '<i>Biogeosciences</i> 15:5847&ndash;5889, 2018.',
         'At least half of the bloom biomass sank below 1,000 m; thirteen artificial iron experiments, 1993&ndash;2009.'),
        ("The LOHAFEX experiment",
         'Martin P, van der Loeff MR, Cassar N, et al. &ldquo;Iron fertilization enhanced net community production '
         'but not downward particle flux during the Southern Ocean iron fertilization experiment LOHAFEX&rdquo;. '
         '<i>Global Biogeochemical Cycles</i> 27:871&ndash;881, 2013.',
         'Production doubled; export was no higher than outside the patch; silicate limitation and grazing.'),
        ("a 2010 study by Andreas Oschlies",
         'Oschlies A, Koeve W, Rickels W, Rehdanz K. &ldquo;Side effects and accounting aspects of hypothetical '
         'large-scale Southern Ocean iron fertilization&rdquo;. <i>Biogeosciences</i> 7:4017&ndash;4035, 2010.',
         'Extra ocean uptake from the air per unit of extra export at 100 years, 0.22 for a one-year pulse (Table 1) and 0.51 in the best region (Table 2); nitrous oxide offset.'),
        ("Under the London Protocol",
         'London Convention and London Protocol, Resolution LC-LP.1 (2008) on the regulation of ocean '
         'fertilization.',
         'Ocean fertilization other than legitimate scientific research not to be allowed.'),
        ("2022 mitigation report states",
         'IPCC. <i>Climate Change 2022: Mitigation of Climate Change</i>, AR6 WG3, Chapter 12, Cross-Chapter Box 8, '
         '2022; Hepburn C, et al. &ldquo;The technological and economic prospects for CO2 utilization and '
         'removal&rdquo;. <i>Nature</i> 575:87&ndash;97, 2019.',
         'Using captured fossil CO2 in products does not remove CO2 from the atmosphere.'),
        ("2016 design case, capturing the CO2",
         'Davis R, Markham J, Kinchin C, et al. <i>Process Design and Economics for the Production of Algal Biomass</i>. '
         'NREL/TP-5100-64772, 2016.',
         'Emissions per tonne of algae, about 0.36 t CO2 per t CO2 fixed, from flue-gas capture, electricity and fertilizer (Tables 20&ndash;21); no drying in the design.'),
        ("Brilliant Planet, a London company",
         'Companies House, Brilliant Planet Limited (company 08491368), insolvency filings, 2024&ndash;2025.',
         'Administration from 14 November 2024.'),
        ("An independent 2026 analysis by Leonard and colleagues",
         'Leonard W, McClure DD, Ng KS, Yang A. &ldquo;Potential of Microalgal Biomass Production in Coastal Deserts for '
         'Carbon Dioxide Removal&rdquo;. <i>Environmental Science &amp; Technology</i> 60(33):23231&ndash;23244, 2026, '
         'doi:10.1021/acs.est.6c08729.',
         'Net removal and cost of desert algae burial, $181 to $661 a tonne of CO2.'),
        ("The National Academies judged that seaweed cultivation",
         'National Academies of Sciences, Engineering, and Medicine. <i>A Research Strategy for Ocean-based Carbon '
         'Dioxide Removal and Sequestration</i>. Washington, DC, 2022. doi:10.17226/26278.',
         'Seaweed cultivation appears to be a compelling strategy (Ch. 9); cost near $100 a tonne before monitoring; iron '
         'fertilization under $50.'),
        ("across publicly priced carbon-removal orders in 2024",
         'CDR.fyi, 2024 year in review (public summary); Frontier, direct air capture pathway page '
         '(frontierclimate.com), as listed on 13 November 2026.',
         'Weighted average price per tonne of publicly priced orders, $320 in 2024; Frontier&rsquo;s average contracted price for direct air capture, $646.'),
    ],
    # Climate effort (climate-dissonance lane, 2026-11-13). dissonance/update_page.py applies this entry itself
    # (lead's idiom). The survey, review, Meta and Yale and OWID figures come from dissonance/data; the rest are
    # quoted from the papers named here.
    "dissonance.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("the European Commission's survey",
         'European Commission, <i>Special Eurobarometer 565: Climate change</i> (Eurobarometer 103.2), fieldwork 18 February to 16 March 2025, EU27; Volume A data tables (questions QD2, QD3ab, QD5, QD6), data.europa.eu.',
         'The share of people in the EU aged 15 and over who call climate change a serious problem, who name each of the fourteen actions and at least one, and who name each actor as best placed to tackle climate change; the sample size.'),
        ("a review by Diana Ivanova and colleagues",
         'Diana Ivanova, John Barrett, Dominik Wiedenhofer and others, &ldquo;Quantifying the potential for climate change mitigation of consumption options&rdquo;, <i>Environmental Research Letters</i> 15(9):093001, 2020, and its supplementary data (sheet &ldquo;options&rdquo;).',
         'The per-person annual saving of each matched action: median, 25th and 75th percentiles and the number of estimates.'),
        ("consumption in the EU caused about",
         'Global Carbon Budget (Friedlingstein and others), consumption-based CO<sub>2</sub> emissions per person, European Union (27), as published by Our World in Data, <i>CO<sub>2</sub> and Greenhouse Gas Emissions</i> dataset, fetched 7 November 2026.',
         'The EU27 consumption-based CO<sub>2</sub> per person used as a scale.'),
        ("Shahzeen Attari and colleagues",
         'Shahzeen Z. Attari, Michael L. DeKay, Cliff I. Davidson and W&auml;ndi Bruine de Bruin, &ldquo;Public perceptions of energy consumption and savings&rdquo;, <i>Proceedings of the National Academy of Sciences</i> 107(37):16054&ndash;16059, 2010.',
         'The survey of 505 people in 2009; the slope of 0.28; curtailment named by 55.2% and efficiency by 11.7% as the most effective way to conserve energy.'),
        ("Ipsos asked 21,011 people",
         'Ipsos, <i>Environmental Perils of Perception</i>, April 2021; Global Advisor survey of 21,011 online adults aged 16&ndash;74 (18&ndash;74 in six markets) in 30 markets, 19 February to 5 March 2021.',
         'The share naming each action among the three that most reduce one person&rsquo;s emissions.'),
        ("Seth Wynes and Kimberly Nicholas",
         'Seth Wynes and Kimberly A. Nicholas, &ldquo;The climate mitigation gap: education and government recommendations miss the most effective individual actions&rdquo;, <i>Environmental Research Letters</i> 12(7):074024, 2017.',
         'Savings for living car-free (2.4 t a year), one fewer return transatlantic flight (1.6 t) and recycling (210 kg a year); their own UK green-power figure (0.043 t) and the note on double counting; 216 textbook recommendations, 8 of them high-impact.'),
        ("The Meta and Yale climate survey of 2023",
         'Meta Data for Good and Yale Program on Climate Change Communication, <i>Climate Change Opinion Survey</i>, 2023, country aggregates, Humanitarian Data Exchange (CC0).',
         'Adoption of electric cars, heat pumps and rooftop solar, and the difficulties named by those who had not adopted them.'),
        ("voluntary round of the HOPE project",
         'Ghislain Dubois, Benjamin Sovacool, Carlo Aall and others, &ldquo;It starts at home? Climate policies targeting household consumption and behavioral decisions are key to low-carbon futures&rdquo;, <i>Energy Research &amp; Social Science</i> 52:144&ndash;158, 2019.',
         'The 308 households in four cities and the shares choosing each action in the first, voluntary round.'),
        ("Robert Gifford listed 29",
         'Robert Gifford, &ldquo;The dragons of inaction: psychological barriers that limit climate change mitigation and adaptation&rdquo;, <i>American Psychologist</i> 66(4):290&ndash;302, 2011.',
         'The 29 psychological barriers.'),
        ("Elke Weber described a single-action bias",
         'Elke U. Weber, &ldquo;Experience-based and description-based perceptions of long-term risk: why global warming does not scare us (yet)&rdquo;, <i>Climatic Change</i> 77:103&ndash;120, 2006.',
         'The single-action bias.'),
        ("Alexander Maki and colleagues",
         'Alexander Maki, Amanda R. Carrico, Kaitlin T. Raimi and others, &ldquo;Meta-analysis of pro-environmental behaviour spillover&rdquo;, <i>Nature Sustainability</i> 2(4):307&ndash;315, 2019.',
         'Almost no spillover from one pro-environmental behaviour to the next, and a small positive effect on intentions.'),
        ("Christine Kormos and Robert Gifford",
         'Christine Kormos and Robert Gifford, &ldquo;The validity of self-report measures of proenvironmental behavior: a meta-analytic review&rdquo;, <i>Journal of Environmental Psychology</i> 40:359&ndash;371, 2014; as summarised by the North American Association for Environmental Education, eePRO research summary.',
         'The correlation of 0.46 between self-reported and objectively measured behaviour.'),
        ("The consultancy Carbone 4",
         'C&eacute;sar Dugast and Alexia Soyeux, <i>Faire sa part? Pouvoir et responsabilit&eacute; des individus, des entreprises et de l&rsquo;&Eacute;tat face &agrave; l&rsquo;urgence climatique</i>, Carbone 4, June 2019.',
         'The average French footprint of 10.8 t CO<sub>2</sub>e; about 25% from everyday behaviour if everyone did every action, 5&ndash;10% realistic, about 45% with investment.'),
        ("The Intergovernmental Panel on Climate Change",
         'IPCC, <i>Climate Change 2022: Mitigation of Climate Change</i>, Working Group III contribution to the Sixth Assessment Report, Summary for Policymakers, section C.10, and chapter 5.',
         'Demand-side potential of 40&ndash;70% by 2050 in end-use sectors; at least 5% rapidly from socio-cultural and behavioural change with policy support, more by 2050 with improved infrastructure.'),
    ],
    # A lower-carbon running shoe (eco-shoe lane, 2026-11-07). lowcarbon-shoe/update_page.py applies this
    # entry itself. Anchors are prose-only phrases: none appears in the hero's SVG labels or JSON.
    "lowcarbon-shoe.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("about 65 parts in all",
         'Lynette Cheah, Natalia Duque Ciceri, Elsa Olivetti, Seiko Matsumura, Dai Forterre, Richard Roth and Randolph Kirchain, &ldquo;Manufacturing-focused emissions reductions in footwear production&rdquo;, <i>Journal of Cleaner Production</i> 44, 2013, pp. 18-29, doi:10.1016/j.jclepro.2012.11.037 (author manuscript in MIT Open Access Articles).',
         'A shoe of 65 parts; 14 kg CO2e per pair for a shoe made in 2010 in a factory that burned coal; the part shares and cutting losses used for the typical trainer.'),
        ("an industry report of 2025",
         'Andy Polk, <i>Understanding and mitigating the modern footprint of the footwear industry: from manufacturing energy use to total emissions</i> (the &ldquo;Carbon Report&rdquo;), Footwear Innovation Foundation, 2025 (energy data for 33 factories in China and Viet Nam, April 2023 to March 2024).',
         'A 6.7 kg CO2e per pair cradle-to-grave example; electricity and fuel per pair at final assembly, from which the model derives 2.9 kWh; no coal in the factories surveyed.'),
        ("In one laboratory fatigue test",
         'C. Aimar, L. Org&eacute;as, S. Rolland du Roscoat, L. Bailly and D. Ferr&eacute; Sentis, &ldquo;Compression fatigue of elastomeric foams used in midsoles of running shoes&rdquo;, <i>Footwear Science</i> 16(2), 2024, pp. 93-103, doi:10.1080/19424280.2024.2317881.',
         'Stress-strain curves of an EVA foam and an expanded-TPU foam from the same test; loss of absorbed energy after 200,000 cycles, most of it in the first 10,000; loss factors.'),
        ("even after 640 km",
         'Mark W. Cornwall and Thomas G. McPoil, &ldquo;Can runners perceive changes in heel cushioning as the shoe ages with increased mileage?&rdquo;, <i>International Journal of Sports Physical Therapy</i> 12(4), 2017, pp. 616-624.',
         'Runners did not perceive the loss of heel cushioning up to 640 km.'),
        ("a manufacturer&rsquo;s claim",
         'Braskem, <i>I&rsquo;m green bio-based</i> product brochure, p. 12 (EVA figure reviewed by ERM, 2025; LCA to ISO 14040/14044).',
         'A manufacturer&rsquo;s claim, not an independent figure: a cradle-to-gate footprint of &minus;1.08 kg CO2e per kg for sugarcane-based EVA that counts the carbon taken up by the cane; the grade is not named.'),
        ("roughly 11 to 140 kWh",
         'Timothy Gutowski, Sheng Jiang, Daniel Cooper, Gero Corman et al., &ldquo;Note on the rate and energy efficiency limits for additive manufacturing&rdquo;, <i>Journal of Industrial Ecology</i> 21(S1), 2017, doi:10.1111/jiec.12664.',
         'Electricity per kilogram printed, measured on filament-extrusion and polymer powder-bed printers (Figure 1).'),
        ("of the footprint of new polyester fibre",
         'Franklin Associates (Eastern Research Group), <i>Life Cycle Inventory of 100% Postconsumer HDPE and PET Recycled Resin from Postconsumer Containers and Packaging</i>, revised final report for the Plastics Division of the American Chemistry Council, the Association of Postconsumer Plastic Recyclers, NAPCOR and the PET Resin Association, 19 January 2011, Tables 3-5 and 3-6.',
         'Recycled PET flake 0.80 and pellet 1.18-1.23 kg CO2e per kg against 2.75 for new PET resin (cut-off method, collection to reprocessing, US); the reprocessing step of 0.906 kg per kg that the model also uses for fibre processing.'),
        ("Fewer than 5 percent of used shoes are recycled",
         'Michael J. Lee and Shahin Rahimifard, &ldquo;An air-based automated material recycling system for postconsumer footwear products&rdquo;, <i>Resources, Conservation and Recycling</i> 69, 2012, pp. 90-99, doi:10.1016/j.resconrec.2012.09.008.',
         'Fewer than 5 percent of end-of-life shoes recycled (an estimate).'),
        ("a well-known take-back scheme",
         'Alexander Curtis and Amanda Hansson, &ldquo;Examining the viability of corporate recycling initiatives and their overall environmental impact: the case of Nike Grind and the Reuse-A-Shoe program&rdquo;, <i>Case Studies in the Environment</i> 3(1), 2019, pp. 1-7, doi:10.1525/cse.2019.001974.',
         'A take-back scheme that grinds collected shoes into surface materials.'),
        ("TPU makers already sell grades recycled from factory scrap",
         'Andrea Koh&aacute;ri and Tam&aacute;s B&aacute;r&aacute;ny, &ldquo;The growth and recyclability of thermoplastic polyurethanes&rdquo;, <i>Express Polymer Letters</i> 18(5), 2024, pp. 459-460, doi:10.3144/expresspolymlett.2024.33.',
         'Recycled TPU grades on the market contain post-industrial waste.'),
        ("A German study",
         'J&uuml;rgen Bertling, Ralf Bertling and Leandra Hamann, <i>Kunststoffe in der Umwelt: Mikro- und Makroplastik. Ursachen, Mengen, Umweltschicksale, Wirkungen, L&ouml;sungsans&auml;tze, Empfehlungen</i>, Kurzfassung der Konsortialstudie, Fraunhofer UMSICHT, Oberhausen, June 2018, Tabelle 3-1, doi:10.24406/umsicht-n-497117.',
         'Abrasion of shoe soles about 109 g and of tyres about 1,229 g per person per year in Germany (estimates).'),
        ("In a study of shoes walked and jogged on asphalt",
         'S. Manabe, Y. Shimizu, T. Yoshitomi, R. Fujinuma and M. Kobayashi, &ldquo;Release of microplastics from shoe outsoles into the environment by walking and jogging, and ingestion of shoe outsole microplastics by goldfish&rdquo;, <i>Microplastics</i> 4(4), 2025, article 92, doi:10.3390/microplastics4040092.',
         'Running shoes lost about 35 mg per km per pair over 92.4 km on asphalt.'),
        ("laboratory abrasion tests",
         'ISO 4649:2017 (withdrawn 2024), <i>Rubber, vulcanized or thermoplastic: determination of abrasion resistance using a rotating cylindrical drum device</i>; BASF, <i>Elastollan product range chart</i> (moulded polyester TPU, C series, DIN ISO 4649 method A); V&iacute;ctor M. Serrano-Mart&iacute;nez et al., &ldquo;Exploring the mechanical and thermal impact of natural fillers on thermoplastic polyurethane and styrene-butadiene rubber footwear sole materials&rdquo;, <i>Polymers</i> 16(22), 2024, article 3201, doi:10.3390/polym16223201 (shoe-sole SBR, EN 12770).',
         'Volume loss of moulded TPU (about 25-40 mm&sup3;) against a shoe-sole rubber (157 mm&sup3;); the drum test compares materials.'),
        ("standard drop test for running-shoe cushioning",
         'ASTM F1976-24, <i>Standard Test Method for Impact Attenuation of Athletic Shoe Cushioning Systems and Materials</i>, ASTM International, 2024.',
         'The drop test simulated here: an 8.5 kg mass, nominal 5 J for running shoes.'),
        ("derived from tests of five running shoes",
         'Franz Konstantin Fuss, Tizian Scharl and Niko Nagengast, &ldquo;A new method and set of parameters for evaluating the cushioning effect of shoe heels, revealing the inadvertent design of running shoes&rdquo;, <i>Bioengineering</i> 12(5), 2025, article 467, doi:10.3390/bioengineering12050467 (peak forces calculated there from the ASTM F1976 scores of five running shoes in E. Pisciotta and M. Shorten, <i>Footwear Science</i> 10(2), 2018, pp. 69-75, doi:10.1080/19424280.2018.1486462).',
         'Peak forces of 809-1,259 N for five running shoes in the 5 J drop test.'),
        ("In a published laboratory comparison",
         'Wouter Hoogkamer, Shalaya Kipp, Jesse H. Frank, Emily M. Farina, Geng Luo and Rodger Kram, &ldquo;A comparison of the energetic cost of running in marathon racing shoes&rdquo;, <i>Sports Medicine</i> 48(4), 2018, pp. 1009-1019, doi:10.1007/s40279-017-0811-2.',
         'Energy return of 75.9 percent for a racing shoe with an expanded-TPU midsole and 65.5 percent for one with an EVA midsole.'),
        ("for Viet Nam in 2025",
         'Ember, <i>Yearly electricity data</i>, release of 2026, CC-BY 4.0, ember-energy.org/data/yearly-electricity-data.',
         'Grid carbon intensity: Viet Nam 459, China 528, Indonesia 705 and the United States 384 g CO2e per kWh in 2025; lifecycle factors for solar and wind.'),
        ("industry eco-profiles",
         'PlasticsEurope, ISOPA, EUROPUR and Euromoulders eco-profiles (ethylene, butadiene, styrene, polybutadiene, polyethylene, MDI, polyether polyols, flexible polyurethane foam), 2005-2026; ADEME, <i>Base Carbone</i> (Licence Ouverte).',
         'Cradle-to-gate footprints of the plastics and their raw materials; the build-up of the TPU, EVA and SBR factors; recycling of plastic scrap to granules, the proxy for recycled TPU.'),
        ("a US industry study of resins and polyurethane raw materials",
         'Franklin Associates (Eastern Research Group), <i>Cradle-to-Gate Life Cycle Inventory of Nine Plastic Resins and Four Polyurethane Precursors</i>, for the Plastics Division of the American Chemistry Council, August 2011, Tables 6-5 and 12-5.',
         'Cradle-to-gate footprints of PET resin (2.73 kg CO2e per kg), the base of the new-polyester factor, and of polyether polyol (4.04 kg), used in the TPU stress case; US data, with fuels and energy from the U.S. LCI database and other background data from Franklin Associates&rsquo; own US database.'),
        ("EU footwear rules",
         '<i>Product Environmental Footprint Category Rules (PEFCR): Apparel and Footwear</i>, version 3.1 (final), 29 April 2025.',
         'Default packaging masses and manufacturing loss rates for footwear.'),
        ("usual US proportions",
         'US Environmental Protection Agency, <i>Advancing Sustainable Materials Management: 2018 Fact Sheet. Assessing Trends in Materials Generation and Management in the United States</i>, EPA 530-F-20-009, December 2020.',
         'Shares of US municipal waste landfilled (50.0 percent) and combusted with energy recovery (11.8 percent).'),
        ("published measurement on a new EVA trainer",
         'Raquel Verdejo, <i>Gas loss and durability of EVA foams used in running shoes</i>, PhD thesis, University of Birmingham, 2004, Table 6.5.',
         'A first-impact peak force of 1.10 kN for the heel of a new EVA trainer at 5 J, used to set the impact-rate factor.'),
        ("international standard for comparisons",
         'ISO 14044:2006 (amended 2017 and 2020), <i>Environmental management: life cycle assessment, requirements and guidelines</i>.',
         'A critical review is required before a comparative assertion is disclosed to the public.'),
    ],
    "aiweb.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ('an analyst at Gartner',
         'Gartner, &ldquo;Gartner Predicts Search Engine Volume Will Drop 25% by 2026, Due to AI Chatbots and Other Virtual Agents&rdquo;, press release, 19 February 2024, <a href="https://www.gartner.com/en/newsroom/press-releases/2024-02-19-gartner-predicts-search-engine-volume-will-drop-25-percent-by-2026-due-to-ai-chatbots-and-other-virtual-agents">gartner.com</a> (text read in the excerpt at <a href="https://search.slashdot.org/story/24/03/04/170221/gartner-predicts-search-engine-volume-will-drop-25-by-2026-due-to-ai-chatbots-and-other-virtual-agents">Slashdot</a>, 4 March 2024).',
         'The forecast, by Alan Antin, of a 25 percent fall in traditional search engine volume by 2026.'),
        ('told investors',
         'Alphabet Inc., Q3 2026 earnings call, 28 October 2026, <a href="https://s206.q4cdn.com/479360582/files/doc_events/2026/Oct/28/2026_Q3_Earnings_Transcript.pdf">transcript</a>; and Form 8-K, Exhibit 99.1, <a href="https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000080/googexhibit991q32026.htm">SEC</a>.',
         'Sundar Pichai: &ldquo;year-over-year query growth rate is the highest it&rsquo;s been in the last five years&rdquo;; Google Search &amp; other revenue of $63.35 billion against $56.57 billion a year earlier.'),
        ('Cloudflare, a network company',
         'Cloudflare, &ldquo;Cloudflare Radar 2025 Year in Review&rdquo;, 15 December 2025, <a href="https://blog.cloudflare.com/radar-2025-year-in-review">blog.cloudflare.com</a>.',
         'Humans 47 percent of HTML requests in a snapshot as of 2 December 2025; declared AI bots 4.2 percent and Googlebot 4.5 percent on average over 2025.'),
        ('In July 2025 Cloudflare counted',
         'Cloudflare, &ldquo;The crawl-to-click gap: Cloudflare data on AI bots, training, and referrals&rdquo;, 29 August 2025, <a href="https://blog.cloudflare.com/crawlers-click-ai-bots-training/">blog.cloudflare.com</a>.',
         'Crawl-to-referral ratios in July 2025: Google 5.4, OpenAI 1,091, Anthropic 38,066 HTML crawls per referred visit.'),
        ('The Pew Research Center tracked',
         'Pew Research Center, &ldquo;Google users are less likely to click on links when an AI summary appears in the results&rdquo;, 22 July 2025, <a href="https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/">pewresearch.org</a>.',
         '900 US adults, 68,879 searches in March 2025; clicks on 8 percent of searches with an AI summary, 15 percent without, 1 percent inside the summary.'),
        ('SparkToro, which studies search behavior',
         'Rand Fishkin, &ldquo;In 2026, less than one-third of Google searches still send a click&rdquo;, SparkToro, 8 June 2026, <a href="https://sparktoro.com/blog/in-2026-less-than-one-third-of-google-searches-still-send-a-click/">sparktoro.com</a>.',
         'Zero-click share of US Google searches: 68.01 percent (January to April 2026), 60.45 percent (2024); Similarweb panel estimates, mobile browsers but not the Google app.'),
        ('Chartbeat, which measures traffic',
         'Nic Newman, <i>Journalism, Media and Technology Trends and Predictions 2026</i>, Reuters Institute, 12 January 2026, <a href="https://reutersinstitute.politics.ox.ac.uk/journalism-media-and-technology-trends-and-predictions-2026">reutersinstitute.politics.ox.ac.uk</a>.',
         'Chartbeat data for more than 2,500 sites: Google search traffic to publishers down 33 percent worldwide, 38 percent in the US (November 2024 to November 2025); news executives expect search traffic to fall 43 percent within three years (268 of 280 respondents).'),
        ('Graphite, a search-marketing agency',
         'Ethan Smith, &ldquo;Debunking The Myth That Search Is Dying&rdquo;, Graphite, 15 January 2026, <a href="https://graphite.io/five-percent/debunking-the-myth-that-seo-traffic-has-dramatically-declined">graphite.io</a>.',
         'Organic Google traffic to more than 40,000 US sites down 2.5 percent in 2025 (Similarweb estimates); the ten largest sites up 1.6 percent on average; news, health and cooking among the categories down more than 10 percent.'),
        ('In Chartbeat\'s count',
         'Chartbeat, <i>Navigating the New Traffic Landscape</i> (Chartbeat Report, Q1 2026), <a href="https://lp.chartbeat.com/hubfs/Chartbeat-Report-2026Q1.pdf">PDF</a>.',
         'Search pageviews year on year: small publishers down 60 percent, large ones down 22 percent; AI platforms under 1 percent of publisher pageviews.'),
        ('Wikipedia, which relies on visits',
         'Wikimedia Foundation, &ldquo;New User Trends on Wikipedia&rdquo;, Diff, 17 October 2025, <a href="https://diff.wikimedia.org/2025/10/17/new-user-trends-on-wikipedia/">diff.wikimedia.org</a>.',
         'Human page views in recent months of 2025 down roughly 8 percent against the same months of 2024, after March to August 2025 bot traffic was reclassified.'),
        ('Microsoft announced what it called the open agentic web',
         'Frank X. Shaw, &ldquo;Microsoft Build 2025: The age of AI agents and building the open agentic web&rdquo;, 19 May 2025, <a href="https://blogs.microsoft.com/blog/2025/05/19/microsoft-build-2025-the-age-of-ai-agents-and-building-the-open-agentic-web/">blogs.microsoft.com</a>.',
         'Microsoft&rsquo;s &ldquo;open agentic web&rdquo;.'),
        ('a protocol for agents to make payments',
         'Google Cloud, &ldquo;Powering AI commerce with the new Agent Payments Protocol (AP2)&rdquo;, 16 September 2025, <a href="https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol">cloud.google.com</a>.',
         'Google&rsquo;s protocol for agent payments.'),
        ('OpenAI published one for agents to buy',
         'OpenAI, &ldquo;Buy it in ChatGPT: Instant Checkout and the Agentic Commerce Protocol&rdquo;, 29 September 2025, <a href="https://openai.com/index/buy-it-in-chatgpt/">openai.com</a>.',
         'Purchases inside ChatGPT and the Agentic Commerce Protocol.'),
        ('The Model Context Protocol',
         'Anthropic, &ldquo;Donating the Model Context Protocol and establishing the Agentic AI Foundation&rdquo;, 9 December 2025, <a href="https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation">anthropic.com</a>.',
         'More than 10,000 active public MCP servers.'),
        ('McKinsey, a consultancy',
         'McKinsey &amp; Company (QuantumBlack), &ldquo;Europe&rsquo;s agentic commerce moment&rdquo;, 2 March 2026, <a href="https://www.mckinsey.com/capabilities/quantumblack/our-insights/europes-agentic-commerce-moment-decision-influence-is-here-execution-is-coming">mckinsey.com</a>.',
         'Agents could orchestrate $3 trillion to $5 trillion of global commerce by 2030 (citing McKinsey&rsquo;s October 2025 report).'),
        ('that Imperva, a security firm, saw',
         'Thales (Imperva), &ldquo;2026 Bad Bot Report&rdquo;, 29 April 2026, <a href="https://www.imperva.com/blog/bad-bot-report-2026-bots-agentic-age/">imperva.com</a>.',
         'Automated software more than 53 percent of web traffic in 2025, up from 51 percent in 2024.'),
        ('HUMAN Security, which tracks them',
         'Aviad Kaiserman, &ldquo;State of Agentic Traffic &ndash; October 2026: Meta and OpenAI now account for 90% of agentic traffic&rdquo;, HUMAN Security, 9 November 2026, <a href="https://www.humansecurity.com/learn/blog/october-2026-agentic-traffic/">humansecurity.com</a>.',
         '85.2 percent of agentic requests to product or search pages; 1.9 percent to checkout or payment.'),
        ('sending checkout to merchants',
         'Forrester, &ldquo;What it means that the leader in agentic commerce just pulled back&rdquo;, March 2026, <a href="https://www.forrester.com/blogs/what-it-means-that-the-leader-in-agentic-commerce-just-pulled-back/">forrester.com</a>.',
         'OpenAI moving checkout from inside ChatGPT to merchants&rsquo; own apps and sites, a change described as temporary.'),
        ('In a 2025 Forrester survey',
         'Forrester, &ldquo;Many US consumers believe in agentic commerce, but few trust it to make purchases&rdquo;, 10 November 2025, <a href="https://www.forrester.com/report/many-us-consumers-believe-in-agentic-commerce-but-few-trust-it-to-make-purchases/RES188737">forrester.com</a>.',
         '24 percent of US online adults trust AI agents to make routine purchases.'),
        ('Shayne Longpre and colleagues',
         'Shayne Longpre et al., &ldquo;Consent in Crisis: The Rapid Decline of the AI Data Commons&rdquo;, 2024, <a href="https://arxiv.org/abs/2407.14933">arXiv:2407.14933</a>.',
         'Robots.txt restrictions on C4, RefinedWeb and Dolma: about 1 percent of tokens in mid-2023, 5 to 7 percent by April 2024, 20 to 33 percent for the most important domains.'),
        ('according to BuzzStream',
         'BuzzStream, study of news publishers blocking AI bots, 18 December 2025, updated 8 April 2026, <a href="https://www.buzzstream.com/blog/publishers-block-ai-study/">buzzstream.com</a>.',
         'About 79 percent of top US and UK news sites block at least one AI training bot.'),
        ('Across the million most-visited websites',
         'Paul Bouchaud and Pedro Ramaciotti, &ldquo;Web Crawler Restrictions, AI Training Datasets &amp; Political Biases&rdquo;, 10 October 2025 (data September 2025), <a href="https://arxiv.org/html/2510.09031v1">arXiv:2510.09031</a>.',
         'GPTBot fully blocked on 10.6 percent of the top one million websites.'),
        ('By one count',
         'Rob Kelly, &ldquo;AI Content Licensing Deals: June 2026 Update&rdquo;, Media and the Machine, 3 June 2026, <a href="https://mediaandthemachine.substack.com/p/ai-content-licensing-deals-june-2026">substack</a>.',
         '91 AI content-licensing deals publicly announced or reported since January 2023 (one person&rsquo;s tracker).'),
        ('News Corp\'s deal with OpenAI',
         'Engadget, reporting The Wall Street Journal, 22 May 2024, <a href="https://www.engadget.com/openai-will-reportedly-pay-250-million-to-put-news-corps-journalism-in-chatgpt-214615249.html">engadget.com</a>.',
         'About $250 million over five years, in cash and credits (reported; terms not disclosed).'),
        ('Amazon\'s with The New York Times',
         'Engadget, reporting The Wall Street Journal, 30 July 2025, <a href="https://www.engadget.com/ai/the-new-york-times-and-amazons-ai-licensing-deal-is-reportedly-worth-up-to-25-million-per-year-135523853/">engadget.com</a>.',
         '$20 million to $25 million a year (reported).'),
        ('TollBit, which sells licensing tools',
         'Digiday, reporting TollBit data, 11 February 2026, <a href="https://digiday.com/media/in-graphic-detail-ai-licensing-deals-protection-measures-arent-slowing-web-scraping/">digiday.com</a>.',
         'About 30 percent of AI bot scrapes in Q4 2025 bypassed explicit robots.txt permissions.'),
        ('copyright suits had been filed',
         'ChatGPT Is Eating the World, &ldquo;Latest map of U.S. copyright suits v. AI companies: total 157&rdquo;, 29 October 2026, <a href="https://chatgptiseatingtheworld.com/2026/10/29/latest-map-of-u-s-copyright-suits-v-ai-companies-total-157/">chatgptiseatingtheworld.com</a>.',
         '157 US copyright suits against AI companies.'),
        ('settlement with book authors',
         'Bloomberg Law, &ldquo;Anthropic, Authors&rsquo; $1.5 Billion Deal Earns Final Approval&rdquo;, 20 July 2026, <a href="https://news.bloomberglaw.com/ip-law/anthropic-authors-1-5-billion-deal-receives-final-approval">bloomberglaw.com</a>.',
         'The $1.5 billion settlement in Bartz v. Anthropic, over books from pirate libraries used in training.'),
        ('Europol\'s Innovation Lab',
         'Europol Innovation Lab, <i>Facing reality? Law enforcement and the challenge of deepfakes</i>, 2022, p. 5 and note 4, <a href="https://www.europol.europa.eu/publications-events/publications/facing-reality-law-enforcement-and-challenge-of-deepfakes">europol.europa.eu</a> (the sentence is in the report&rsquo;s PDF, not on the landing page).',
         '&ldquo;Experts estimate that as much as 90 % of online content may be synthetically generated by 2026&rdquo;, citing only Schick (2020).'),
        ('a 2020 book by Nina Schick',
         'Nina Schick, <i>Deepfakes: The Coming Infocalypse</i>, Twelve, 2020; interview reported by PetaPixel, 17 January 2023, <a href="https://petapixel.com/2023/01/17/90-of-online-content-could-be-generated-by-ai-by-2025-expert-says/">petapixel.com</a>.',
         'The book Europol cites, and Schick&rsquo;s 2023 statement that 90 percent &ldquo;might&rdquo; be reached by 2025, with no data given.'),
        ('ran a sample of new English-language articles',
         'Graphite, &ldquo;AI Now Writes as Many Online Articles as Humans&rdquo;, 15 May 2026, <a href="https://graphite.io/five-percent/research/ai-now-writes-as-many-online-articles-as-humans-do">graphite.io</a>.',
         '49.9 percent of new English articles mostly AI-written in Q1 2026, near half for five quarters; 55,400 Common Crawl articles; three commercial detectors (Pangram, Copyleaks, GPTZero) with false-positive rates of 1.4 to 1.8 percent.'),
        ('percent of Google\'s results',
         'Graphite, &ldquo;How Does AI-Generated Content Perform in Search and Answer Engines?&rdquo;, 14 October 2025, <a href="https://graphite.io/five-percent/ai-content-in-search-and-llms">graphite.io</a>.',
         'AI-generated pages 14 percent of Google results and 7 percent of first results (31,493 keywords, June 2025).'),
        ('NewsGuard, which rates news sites',
         'NewsGuard, AI Tracking Center, updated 23 June 2026, <a href="https://www.newsguardtech.com/special-reports/ai-tracking-center/">newsguardtech.com</a>.',
         '3,749 sites by June 2026; the 49 of early May 2023 are from NewsGuard&rsquo;s press release of 19 May 2023, &ldquo;NewsGuard Now Identifies 125 News and Information Websites Generated by AI&rdquo;, <a href="https://www.newsguardtech.com/press/newsguard-now-identifies-125-news-and-information-websites-generated-by-ai-develops-framework-for-defining-unreliable-ai-generated-news-and-information-sources/">newsguardtech.com</a>, which gives the earlier count.'),
        ('Ilia Shumailov and colleagues',
         'Ilia Shumailov et al., &ldquo;AI models collapse when trained on recursively generated data&rdquo;, <i>Nature</i> 631, 755&ndash;759, 24 July 2024, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11269175/">PMC11269175</a>.',
         'Model collapse under recursive training; keeping 10 percent of the original data gave only minor degradation.'),
        ('on Similarweb\'s estimates',
         'Similarweb, &ldquo;The Top 100 Most Visited Websites in the World (October 2026)&rdquo;, 10 November 2026, <a href="https://www.similarweb.com/blog/research/market-research/most-visited-websites/">similarweb.com</a>.',
         'google.com 88.4 billion and chatgpt.com 6.0 billion visits in October 2026, web only (a page updated monthly).'),
        ('surveyed by the Reuters Institute',
         'Felix M. Simon, Rasmus Kleis Nielsen and Richard Fletcher, <i>Generative AI and News Report 2026: From standalone tools to information infrastructure</i>, Reuters Institute, 29 October 2026, <a href="https://reutersinstitute.politics.ox.ac.uk/generative-ai-and-news-report-2026-standalone-tools-information-infrastructure">reutersinstitute.politics.ox.ac.uk</a>.',
         'Weekly use of standalone generative AI 34 percent (2025) and 51 percent (2026), six-country average; across nine countries, 57 percent saw AI answers in a search engine in the last week.'),
        ('Elon University canvassed',
         'Elon University, Imagining the Digital Future Center, <i>Being Human in 2035</i>, 2025, <a href="https://imaginingthedigitalfuture.org/reports-and-publications/being-human-in-2035/being-human-in-2035-research-methodologies-and-topline-findings/">imaginingthedigitalfuture.org</a>.',
         '301 experts (non-random): 16 percent mostly better, 23 percent mostly worse, 50 percent equal measure.'),
        ('In a 2024 Pew survey',
         'Pew Research Center, &ldquo;How the US Public and AI Experts View Artificial Intelligence&rdquo;, 3 April 2025, <a href="https://www.pewresearch.org/internet/2025/04/03/how-the-us-public-and-ai-experts-view-artificial-intelligence/">pewresearch.org</a>.',
         '56 percent of AI experts and 17 percent of the US public expect a positive impact over 20 years (surveyed August to October 2024).'),

        ('organic click volume &ldquo;has been relatively stable year-over-year&rdquo;',
         'Liz Reid, &ldquo;AI in Search is driving more queries and higher quality clicks&rdquo;, Google, 6 August 2025, <a href="https://blog.google/products-and-platforms/products/search/ai-search-driving-more-queries-higher-quality-clicks/">blog.google</a>.',
         'Google&rsquo;s statement that total organic clicks to websites are relatively stable year on year; no figures given.'),
        ('on a desktop-only panel in March 2025',
         'Danny Goodwin, &ldquo;Zero-click searches rise, organic clicks dip: Report&rdquo;, Search Engine Land, reporting Datos and SparkToro, 2025, <a href="https://searchengineland.com/zero-click-searches-up-organic-clicks-down-456660">searchengineland.com</a>.',
         'US desktop zero-click share 27.2 percent in March 2025, up from 24.4 percent a year before.'),
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
