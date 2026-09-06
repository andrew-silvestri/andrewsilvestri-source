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
    "heat.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("resistive electric boiler",
         'Zuberi, Hasanbeigi &amp; Morrow, <i>Electrification of industrial '
         'process heat</i>, Lawrence Berkeley National Laboratory, 2021.',
         "Electric boiler efficiency and capital cost ranges."),
        ("At a gas price of $3.50",
         'U.S. Energy Information Administration, <i>Electric Power Monthly</i> '
         'Table 5.6.A and the Natural Gas Industrial Price series.',
         "Texas industrial electricity and gas prices."),
        ("grid carbon intensity",
         'U.S. EPA, <i>eGRID2023</i> (revised 12 June 2025), ERCT subregion '
         'output emission rates; and EPA, <i>Emission Factors for Greenhouse '
         'Gas Inventories</i>, stationary combustion.',
         "Grid carbon intensity, 733.862 lb CO&#8322;/MWh or 0.333 t/MWh, and "
         "the natural gas emission factor. The CO&#8322; rate is used rather "
         "than the CO&#8322;e rate, because the gas factor it is compared "
         "against is also carbon dioxide only."),
        ("levelised cost",
         'NREL, <i>Annual Technology Baseline</i> 2024, financial assumptions.',
         "Discount rate, economic life and the levelisation method."),
    ],
    "economy.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("cost-of-running curve",
         'Kipp, Kram &amp; Hoogkamer, <i>Frontiers in Physiology</i> 10:79, 2019, '
         'doi:10.3389/fphys.2019.00079.',
         "The six published cost-of-running curves with Pugh's air-resistance "
         "term, the equations this page computes with, and the reconciliation "
         "with the measured 3000 m result; open access, CC BY."),
        ("3000 metre race times",
         'Hoogkamer, Kipp, Spiering &amp; Kram, <i>Medicine &amp; Science in Sports '
         '&amp; Exercise</i> 48(11):2175-2180, 2016, '
         'doi:10.1249/MSS.0000000000001012.',
         "The measured exchange rate: 100 g per shoe cost 1.11% of metabolic "
         "rate and 0.78% of 3000 m time in 18 trained men."),
        ("decomposes into three measured quantities",
         'Joyner, <i>Journal of Applied Physiology</i> 70(2):683-687, 1991, '
         'doi:10.1152/jappl.1991.70.2.683; and Joyner &amp; Coyle, <i>Journal of '
         'Physiology</i> 586(1):35-44, 2008, doi:10.1113/jphysiol.2007.143834.',
         "The form of the decomposition and the ranges its three terms take in "
         "trained and elite runners."),
        ("carrying all three terms",
         'Lanferdini <i>et al.</i>, <i>Frontiers in Physiology</i> 11:979, 2020, '
         'doi:10.3389/fphys.2020.00979, Supplementary Table 1.',
         "Twenty recreational men with maximal oxygen uptake, both ventilatory "
         "thresholds, running economy and a 3000 m time; CC BY 4.0."),
        ("two hours of running raised",
         'Zanini, Folland &amp; Blagrove, <i>Scandinavian Journal of Medicine &amp; '
         'Science in Sports</i> 35:e70076, 2025.',
         "The within-race decay of all three terms over 90 and 120 minutes in "
         "14 trained runners."),
        ("critical speed a runner holds",
         'Smyth &amp; Muniz-Pumares, <i>Medicine &amp; Science in Sports &amp; '
         'Exercise</i> 52(12):2637-2645, 2020.',
         "The share of critical speed held against finish time, over 25,000 "
         "marathons; the underlying training data are held under a research "
         "licence and are not public."),
        ("fourth determinant",
         'Jones, <i>Journal of Physiology</i> 602(17):4113-4128, 2024, '
         'doi:10.1113/JP284205.',
         "The argument that resistance to within-race decay is an independent "
         "determinant the three-term model omits."),
        ("advanced footwear disagree",
         'Effect sizes collected from thirteen papers; the individual range is '
         'Knopp <i>et al.</i>, <i>Sports Medicine</i> 53:1255-1271, 2023.',
         "The spread of published advanced-footwear effect sizes, quoted here "
         "and analysed on its own page."),
        ("variance in the threshold",
         'Coyle, <i>Exercise and Sport Sciences Reviews</i> 23:25-63, 1995, '
         'PMID 7556353.',
         "That maximal oxygen uptake explains 31-72% of the variance in the "
         "lactate threshold, so the three terms are not independent."),
        ("2,303 recreational runners",
         'Vickers &amp; Vertosick, <i>BMC Sports Science, Medicine and '
         'Rehabilitation</i> 8:26, 2016, doi:10.1186/s13102-016-0052-y.',
         "Self-reported race times at six distances for 2,303 runners, used "
         "for the fall in sustainable pace between 5 km and the marathon; "
         "CC BY 4.0."),
    ],
    "neuron.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("public archive of reconstructed neurons",
         'Ascoli, Donohue &amp; Halavi, <i>The Journal of Neuroscience</i> '
         '27(35):9247-9251, 2007, doi:10.1523/JNEUROSCI.2055-07.2007; Tecuatl, '
         'Ljungquist &amp; Ascoli, <i>FASEB BioAdvances</i> 6(7):207-221, 2024, '
         'doi:10.1096/fba.2024-00048.',
         "NeuroMorpho.Org, the archive every count on this page is computed from; "
         "CC BY 4.0."),
        ("a figure from electron microscopy",
         'Shepherd &amp; Harris, <i>The Journal of Neuroscience</i> '
         '18(20):8300-8310, 1998, doi:10.1523/JNEUROSCI.18-20-08300.1998.',
         "The 0.17 um calibre of a CA3-to-CA1 axon shaft, the thinnest structure "
         "a drawing at true proportions would have to render."),
        ("visible light cannot resolve anything that small",
         'Huang, Bates &amp; Zhuang, <i>Annual Review of Biochemistry</i> '
         '78:993-1016, 2009, doi:10.1146/annurev.biochem.77.061906.092014.',
         "The diffraction limit: 200-300 nm laterally, 500-700 nm axially."),
        ("cell traced through a whole brain keeps its axon",
         'Winnubst <i>et al.</i>, <i>Cell</i> 179(1):268-281.e13, 2019, '
         'doi:10.1016/j.cell.2019.07.042.',
         "Whole-brain single-neuron reconstruction; more than 85 m of axon across "
         "more than 1,000 projection neurons."),
        ("come from one paper",
         'Yamashita, Vavladeli, Pala, Galan, Crochet, Petersen &amp; Petersen, '
         '<i>Frontiers in Neuroanatomy</i> 12:33, 2018, doi:10.3389/fnana.2018.00033.',
         "The projection cells in the complete set; its full text contains no "
         "statement about shrinkage or a correction, and describes its axon tracing "
         "as possibly incomplete. CC BY 4.0."),
        ("The published figure for that is",
         'van Pelt, van Ooyen &amp; Uylings, <i>Frontiers in Neuroanatomy</i> '
         '8:54, 2014, doi:10.3389/fnana.2014.00054.',
         "How much intracortical axon a 300 um slice removes: 48-49%, against "
         "15-17% of dendrite."),
        ("loses roughly half its thickness",
         'Gardella <i>et al.</i>, <i>Journal of Neuroscience Methods</i> '
         '124(1):45-59, 2003, doi:10.1016/S0165-0270(02)00363-1.',
         "Measured shrinkage by embedding method; 80 um vibratome sections "
         "finished at 31.78 um."),
        ("in the preparation these files come from",
         'Mohan <i>et al.</i>, <i>Cerebral Cortex</i> 25(12):4839-4853, 2015, '
         'doi:10.1093/cercor/bhv188.',
         "63 +/- 10% z shrinkage measured in 350 um slices, and the finding that "
         "total dendritic length rises only 11 +/- 2% when corrected."),
        ("leaving depth-derived measurements out of its own analysis",
         'Gouwens <i>et al.</i>, <i>Nature Neuroscience</i> 22(7):1182-1195, '
         '2019, doi:10.1038/s41593-019-0417-0.',
         "The Allen Cell Types morphologies, and the decision to exclude "
         "z-derived features rather than correct the coordinates."),
        ("rather than by correcting the coordinates",
         'Lee <i>et al.</i>, <i>eLife</i> 10:e65482, 2021, '
         'doi:10.7554/eLife.65482.',
         "Where a per-cell shrinkage correction is applied: downstream, in the "
         "Patch-seq pipeline, not in the distributed files."),
        ("which is the paper that states the shrinkage correction",
         'Emmenegger, Qi, Wang &amp; Feldmeyer, <i>Cerebral Cortex</i> '
         '28(4):1439-1457, 2018, doi:10.1093/cercor/bhx352, attributing Marx '
         '<i>et al.</i>, <i>Nature Protocols</i> 7(2):394-407, 2012, '
         'doi:10.1038/nprot.2011.449.',
         "The x1.1 and x2.1 correction factors, and the laboratory whose cells "
         "make up most of the fully-qualified set."),
        ("the widths differed by about a factor of two on visually matched segments",
         'Blackman, Grabuschnig, Legenstein &amp; Sjostrom, <i>Frontiers in '
         'Neuroanatomy</i> 8:65, 2014, doi:10.3389/fnana.2014.00065.',
         "The same eight cells reconstructed two ways: 1.80 +/- 0.15 um against "
         "0.91 +/- 0.09 um."),
        ("The field's own tracing benchmark excluded diameter",
         'Gillette, Brown &amp; Ascoli, <i>Neuroinformatics</i> 9(2-3):233-245, '
         '2011, doi:10.1007/s12021-011-9117-y.',
         "Diameter left out of the DIADEM competition as too subjective at the "
         "resolutions used for whole-arbor reconstruction."),
        ("three experts tracing one dendrite",
         'Fernholz, Guggiana Nilo, Bonhoeffer &amp; Kist, <i>PLoS Computational '
         'Biology</i> 20(2):e1011774, 2024, doi:10.1371/journal.pcbi.1011774.',
         "Inter-operator agreement on a traced arbor, and one person's agreement "
         "with themselves."),
        ("which contains no such factor",
         'Megias, Emri, Freund &amp; Gulyas, <i>Neuroscience</i> '
         '102(3):527-540, 2001, doi:10.1016/S0306-4522(00)00496-6.',
         "Where dendritic spines are on a CA1 pyramidal cell; it carries no "
         "membrane-area factor, though it is often cited for one."),
        ("from a 2016 study of human cortical cells",
         'Eyal <i>et al.</i>, <i>eLife</i> 5:e16553, 2016, '
         'doi:10.7554/eLife.16553.',
         "The spine membrane-area factor, F = 1.78-2.39, applied only beyond "
         "60 um from the soma."),
        ("comes from a 1965 paper on the frog neuromuscular junction",
         'Katz &amp; Miledi, <i>Proceedings of the Royal Society B</i> '
         '161(985):483-495, 1965, doi:10.1098/rspb.1965.0016.',
         "The measured synaptic delay: a minimum of 0.4-0.5 ms and a modal value "
         "near 0.75 ms, at 20 C in low-calcium Ringer."),
        ("releases in about a hundred and fifty microseconds",
         'Sabatini &amp; Regehr, <i>Nature</i> 384(6605):170-172, 1996, '
         'doi:10.1038/384170a0.',
         "Transmitter release 150 us after the onset of the presynaptic action "
         "potential, at physiological temperature."),
    ],
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
         "photograph ratings by 6,212 raters; the deposit is CC BY 4.0."),
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
        ("Until February 2026 the short one",
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
         "Least Concern species have twice the papers of threatened ones."),
        ("Brooke et al. 2014",
         'Brooke, Bielby, Nambiar &amp; Carbone, <i>PLoS ONE</i> 9(4):e93195, 2014, '
         'doi:10.1371/journal.pone.0093195.',
         "286 carnivores; IUCN status estimate -0.047, z = -0.82, p = 0.41 "
         "beside body mass, range and diet breadth."),
        ("McKenzie &amp; Robertson 2015",
         'McKenzie &amp; Robertson, <i>PLoS ONE</i> 10(7):e0131004, 2015, '
         'doi:10.1371/journal.pone.0131004.',
         "225 British breeding birds; Red List status null (p = 0.34), national "
         "action-plan status positive (t = 3.14)."),
        ("Fleming &amp; Bateman 2016",
         'Fleming &amp; Bateman, <i>Mammal Review</i> 46(4):241-254, 2016, '
         'doi:10.1111/mam.12066.',
         "331 Australian mammals; the threat-term result is in the paywalled "
         "full text and was not read for this page."),
        ("dos Santos et al. 2020",
         'dos Santos <i>et al.</i>, <i>Animal Conservation</i> 23(6):679-688, 2020, '
         'doi:10.1111/acv.12586.',
         "4,108 terrestrial mammals, hurdle model; the abstract reports threat "
         "status as weakly associated with research presence and volume."),
        ("Adamo et al. 2021",
         'Adamo <i>et al.</i>, <i>Nature Plants</i> 7:574-578, 2021, '
         'doi:10.1038/s41477-021-00912-2.',
         "113 Alpine plants; colour, conspicuousness and range predict research "
         "attention. Paywalled; not read for this page."),
        ("Tam et al. 2022",
         'Tam, Lagisz, Cornwell &amp; Nakagawa, <i>GigaScience</i> 11:giac074, 2022, '
         'doi:10.1093/gigascience/giac074.',
         "5,497 mammals; IUCN status linear -16.4 [-19.3, -13.6] with a "
         "quadratic term; Google Trends the strongest fixed effect."),
        ("Mammola et al. 2023",
         'Mammola <i>et al.</i>, <i>eLife</i> 12:RP88251, 2023, '
         'doi:10.7554/eLife.88251.',
         "3,019 species across 29 phyla; being on the Red List raises interest "
         "whether the species is endangered or of Least Concern."),
        ("Guedes et al. 2023",
         'Guedes, Moura &amp; Diniz-Filho, <i>Ecography</i> 2023:e06491, 2023, '
         'doi:10.1111/ecog.06491.',
         "10,531 reptiles; body size, description year and proximity to "
         "institutions dominate. Full text not reached for this page."),
        ("Ducatez &amp; DeVore 2026",
         'Ducatez &amp; DeVore, <i>PLoS ONE</i> 21:e0347198, 2026, '
         'doi:10.1371/journal.pone.0347198.',
         "370 turtles; extinction risk -0.10, t = -0.46, p = 0.64; phylogeny "
         "66% of the variance; assessed species more studied than unassessed."),
        ("endangered-species spending",
         'Metrick &amp; Weitzman, <i>Land Economics</i> 72(1):1-16, 1996, '
         'doi:10.2307/3147153.',
         "Endangered Species Act spending FY1989-91: over half to ten species; "
         "body length and taxon outweigh endangerment rank."),
        ("LIFE species-project budget",
         'Mammides, <i>Biodiversity and Conservation</i> 28(5):1291-1296, 2019, '
         'doi:10.1007/s10531-019-01725-8.',
         "Over 800 EU LIFE species projects since 1992; birds and mammals take "
         "69% of projects and 75% of the species budget."),
        ("global database of conservation projects",
         'Gu&eacute;nard <i>et al.</i>, <i>PNAS</i> 122:e2412479122, 2025, '
         'doi:10.1073/pnas.2412479122.',
         "About 14,600 projects over 25 years: 6% of threatened species ever "
         "funded, 29% of funds to Least Concern species."),
        ("one estimate puts",
         'Cowie, Bouchet &amp; Fontaine, <i>Biological Reviews</i> 97(2):640-663, 2022, '
         'doi:10.1111/brv.12816.',
         "7.5-13% of the roughly two million known species estimated extinct "
         "since 1500, against 0.04% recorded on the Red List."),
        ("Data Deficient mammals",
         'Bland <i>et al.</i>, <i>Conservation Biology</i> 29(1):250-259, 2015, '
         'doi:10.1111/cobi.12372.',
         "64% of Data Deficient mammals predicted to be threatened."),
        ("Data Deficient amphibians",
         'Borgelt <i>et al.</i>, <i>Communications Biology</i> 5:679, 2022, '
         'doi:10.1038/s42003-022-03638-9.',
         "85% of Data Deficient amphibians predicted to be threatened."),
        ("resurveyed in 2024",
         'White <i>et al.</i>, <i>Nature Plants</i> 10:1627-1634, 2024, '
         'doi:10.1038/s41477-024-01832-7.',
         "99% of Centinela's supposed microendemic plants have since been "
         "collected elsewhere."),
        ("monitored for fifteen years",
         'Martin <i>et al.</i>, <i>Conservation Letters</i> 5(4):274-280, 2012, '
         'doi:10.1111/j.1755-263X.2012.00239.x.',
         "The Christmas Island pipistrelle was monitored from 1994 and lost in "
         "2009 while a captive-breeding decision was delayed."),
        ("zoo holdings favour large",
         'Frynta <i>et al.</i>, <i>PLoS ONE</i> 8(5):e63110, 2013, '
         'doi:10.1371/journal.pone.0063110.',
         "Rated beauty and body size predict which mammal families zoos hold "
         "and in what numbers; Red List status does not."),
        ("non-threatened species is cited",
         'Conde <i>et al.</i>, <i>PLoS ONE</i> 8(12):e80311, 2013, '
         'doi:10.1371/journal.pone.0080311.',
         "3,955 species in 837 zoos, 23% threatened; only 2 of 59 orders hold "
         "more threatened species than random would."),
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
         "95% uncertainties. Not openly licensed: the authors reserve "
         "commercial rights."),
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
         "deliberately standardised way, and its own description of them."),
        ("The grids are a digitisation of maps that were drawn",
         'Davies, H.S., Green, J.A.M. &amp; Duarte, J.C., <i>Earth System '
         'Dynamics</i> 11(1):291-299, 2020, doi:10.5194/esd-11-291-2020. '
         'Data at OSF 8NEQ4, doi:10.17605/OSF.IO/8NEQ4, CC0 1.0.',
         "The gridded scenarios themselves, their 0.25 degree resolution, the "
         "artificial two-degree polar land mask, and the CC0 licence."),
        ("it was devised for a television series and reached print in a trade "
         "book",
         'Nield, T., <i>Supercontinent: Ten Billion Years in the Life of Our '
         'Planet</i>, Granta, 2007.',
         "Novopangaea's only source. Roy Livermore devised it for the BBC "
         "series The Future Is Wild in the late 1990s; it has no "
         "peer-reviewed primary source."),
        ("the field's own review names uncertainty quantification as an "
         "open problem",
         'Seton, M. <i>et al.</i>, <i>Nature Reviews Earth &amp; Environment</i> '
         '4:185-204, 2023, doi:10.1038/s43017-022-00384-8.',
         "Why no reconstruction on this page carries a formal error bar."),
        ("The models share ancestry",
         'Buffan, L., Jones, L.A., Domeier, M., Scotese, C.R., Zahirovic, S. '
         '&amp; Varela, S., <i>Methods in Ecology and Evolution</i> '
         '14:3007-3019, 2023, doi:10.1111/2041-210X.14204.',
         "Inter-model disagreement measured on a global grid, and the caveat "
         "that shared ancestry makes the true spread of admissible "
         "reconstructions wider than the measured spread between models."),
        ("cannot determine its longitude at all",
         'M&#252;ller, R.D. <i>et al.</i>, <i>Solid Earth</i> 13(7):1127-1159, '
         '2022, doi:10.5194/se-13-1127-2022.',
         "Verbatim: because the Earth's magnetic dipole field is radially "
         "symmetric, palaeo-longitudinal information cannot be determined "
         "from palaeomagnetic data alone."),
        ("Equal Earth, which is equal-area",
         'Savri&#269;, B., Patterson, T. &amp; Jenny, B., <i>International '
         'Journal of Geographical Information Science</i> 33(3):454-465, 2019, '
         'doi:10.1080/13658816.2018.1504949.',
         "The projection used for both maps, chosen because every number in "
         "their captions is an area claim and because its pole line keeps the "
         "circumpolar scenario legible."),
    ],
    "food.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("quantitative definition",
         'Fazzino, Rohde &amp; Sullivan, <i>Obesity</i> 27(11):1761-1768, 2019, '
         'doi:10.1002/oby.22639.',
         "The three threshold pairs, how they were drawn from 75 named foods, "
         "and the 62% of FNDDS 2015-16 items, the fresh foods not captured and "
         "the reduced-content products that were."),
        ("Human milk, the one whole food",
         'DiFeliceantonio <i>et al.</i>, <i>Cell Metabolism</i> 28(1):33-44, 2018, '
         'doi:10.1016/j.cmet.2018.05.018.',
         "Foods combining fat and carbohydrate are valued above equally liked "
         "fat-only or carbohydrate-only foods; the authors name breast milk as "
         "the natural exception."),
        ("rated 52 foods",
         'Rogers, Vural, Flynn &amp; Brunstrom, <i>Appetite</i> 201:107596, 2024, '
         'doi:10.1016/j.appet.2024.107596.',
         "No difference in rated palatability between foods meeting the "
         "hyper-palatable rule and foods not meeting it."),
        ("rate 436 foods",
         'Finlayson <i>et al.</i>, <i>Appetite</i> 213:108029, 2025.',
         "Nutrient content explains about a fifth of rated liking."),
        ("1988 to 2018",
         'Demeke, Rohde, Chollet-Hinton, Sutton, L&rsquo;Insalata &amp; Fazzino, '
         '<i>Public Health Nutrition</i> 26(1):182-189, 2023, '
         'doi:10.1017/S1368980022001227.',
         "Share of items meeting the rule in the 1988, 2001 and 2017-18 US "
         "survey databases, and the odds for items present in all three."),
        ("store shelves met the rule",
         'Fazzino, Bristi, Chollet-Hinton &amp; Sutton, <i>Public Health '
         'Nutrition</i> 29(1):e110, 2026, doi:10.1017/S1368980026102614.',
         "Share of store items and of household purchases meeting the rule, "
         "Circana scanner data 2015-2018."),
        ("moderate overlap",
         'Sutton, Stratton, L&rsquo;Insalata &amp; Fazzino, <i>Obesity</i> 32(1):166-175, '
         '2024, doi:10.1002/oby.23897.',
         "The 40-70% overlap between the hyper-palatable rule, the NOVA "
         "ultra-processed class and high energy density."),
        ("SR Legacy release of April 2018",
         'U.S. Department of Agriculture, Agricultural Research Service, '
         '<i>FoodData Central</i>, SR Legacy, April 2018 release (CC0).',
         "Every computed number on the page: energy, fat, carbohydrate, sugar, "
         "fibre and sodium per 100 g for each food, and the food groups."),
        ("pleasantness peaks",
         'Moskowitz, Kluter, Westerling &amp; Jacobs, <i>Science</i> '
         '184(4136):583-585, 1974.',
         "Perceived sweetness rises with sucrose concentration while "
         "pleasantness rises and then falls."),
        ("Sadler and colleagues",
         'Sadler, McNulty &amp; Gibson, <i>Critical Reviews in Food Science and '
         'Nutrition</i> 55(3):338-356, 2015.',
         "The inverse fat-sugar relation in diets on a share-of-energy basis "
         "is partly arithmetic."),
    ],
    "storage.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("hourly prices",
         'ERCOT, <i>Day-Ahead Market Settlement Point Prices</i>, historical '
         'archive.',
         "The price shape the synthetic year is calibrated to reproduce."),
        ("cycling cost",
         'Mongird <i>et al.</i>, <i>Grid Energy Storage Technology Cost and '
         'Performance Assessment</i>, Pacific Northwest National Laboratory, '
         '2020.',
         "Degradation cost per megawatt hour of throughput, and round-trip "
         "efficiency."),
        ("linear programming",
         'Sioshansi, Denholm, Jenkin &amp; Weiss, <i>Energy Economics</i>, '
         '2009 - estimating the value of electricity storage under '
         'perfect foresight.',
         "The perfect-foresight dispatch formulation and its upper-bound "
         "character."),
        ("four hours",
         'Denholm <i>et al.</i>, <i>The Four-Hour Challenge</i>, National '
         'Renewable Energy Laboratory, 2019.',
         "Why duration value flattens past four hours."),
        ("annualised capital cost",
         'NREL, <i>Annual Technology Baseline</i> 2024, utility-scale battery '
         'storage, 4-hour duration, Moderate scenario, Market case.',
         "The capital cost the right-hand panel compares against: $1,938/kW "
         "capex (overnight cost, grid connection and construction finance) "
         "plus $44/kW-yr fixed operations, annualised over the dataset's own "
         "twenty-year capital recovery period at an eight per cent real "
         "discount rate, for about $242/kW-yr. A representative figure for "
         "scale, not a quote for any particular project."),
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
    "climate-cost.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("published literature",
         'Poore &amp; Nemecek, <i>Science</i> 360:987, 2018 - reducing food’s '
         'environmental impacts through producers and consumers.',
         "Per-kilogram footprints and the spread within each food."),
        ("fertiliser",
         'IPCC, <i>2019 Refinement to the 2006 Guidelines for National '
         'Greenhouse Gas Inventories</i>, Volume 4 Chapter 11 - direct and '
         'indirect nitrous oxide from managed soils.',
         "The emission factor for nitrogen applied to soils."),
        ("methane",
         'IPCC, <i>Sixth Assessment Report</i>, Working Group I Chapter 7, '
         'Table 7.15 - global warming potentials.',
         "Methane at 27 and nitrous oxide at 273 over a century."),
        ("tonne-kilometre",
         'UK Department for Energy Security and Net Zero, <i>Greenhouse gas '
         'reporting: conversion factors</i>, 2023.',
         "Freight emission factors by mode."),
        ("allocation",
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
         "The physical allocation formula AF = 1 - 6.04 x BMR and the 88% "
         "milk share at a typical beef-to-milk ratio of 0.02."),
        ("Lunesu",
         'Lunesu, Correddu, Carta, Sechi, Farina &amp; Pulina, <i>Animals</i> '
         '15:3546, 2025 - attributing farm-to-slaughter emissions to hides.',
         "Hide share of the animal: 2.7% by economic allocation (2023 mean), "
         "5.9% by live weight (range 4.2-6.9%)."),
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
    block = (f'\n<h2>Sources</h2>\n'
             f'<p class="small">Numbered markers in the text above point here. '
             f'Emission factors, cost ranges and lifespan figures are '
             f'representative values from these sources, not measurements '
             f'made for this project.</p>\n'
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
