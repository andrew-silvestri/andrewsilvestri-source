"""The public files the lead page reads, fetched into lead/data/raw/ and recorded in data/fetched.json.

McFarland, Hauer and Reuben (PNAS 2022), CC BY-NC-ND 4.0
- pnas_sd01.xlsx: SI Dataset S01. Share of children aged 1-4 in each blood-lead band, by birth cohort
  and calendar year, with the population alive in each year (column leadpop).
- pnas_sd03.xlsx: SI Dataset S03. The IQ-loss formulas the paper applies to each band.
- pnas_si_appendix.pdf: SI Appendix (Tables S1-S3).
- mcfarland_pmc.xml: the article's full text from Europe PMC.
  pnas.org refuses scripted requests. The three SI files were saved through a browser from the article's
  supplementary-material page; record() hashes them as saved, and the build refuses any other bytes.

Other papers (open access)
- lanphear2005_pmc.xml: Lanphear et al. 2005, Environ Health Perspect 113:894, the pooled analysis.
- bellinger2012_pmc.xml: Bellinger 2012, Environ Health Perspect 120:501.
- reuben2017_pubmed.txt, trahan2014_pubmed.txt: PubMed abstracts of Reuben et al. 2017 (JAMA 317:1244, the
  Dunedin cohort) and Trahan et al. 2014 (Psychol Bull 140:1332, the Flynn-effect meta-analysis).
- larsen2023.pdf: Larsen and Sanchez-Triana 2023, Lancet Planet Health 7:e831. thelancet.com refuses
  scripted requests; this is the Internet Archive copy of the publisher PDF.

The phase-down
- gao_rced_86_80fs.pdf: GAO, "Air Pollution: EPA's Efforts To Reduce and End the Use of Lead in Gasoline",
  RCED-86-80FS, March 1986 (University of North Texas web archive; gao.gov refuses scripted requests).
- epa_1996_phaseout.html: EPA's release of 29 January 1996 on the end of leaded gasoline for road vehicles.

Measurements
- epa_ace_b1.xlsx: EPA, America's Children and the Environment, Indicator B1: median and 95th percentile
  blood lead in children aged 1-5, NHANES 1976-80 to 2017-March 2020.
- myb_<year>.txt: U.S. Bureau of Mines, Minerals Yearbook, the full-text (OCR) files the Internet Archive
  serves for each volume. The lead chapter's table of consumption by product carries the row for
  gasoline antiknock additives. data/gasoline_lead_myb.csv names the volume and table for each year.

Run:  python fetch_public.py [name ...]
"""
import csv

from netfetch import HERE, RAW, fetch, record

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML"
PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&retmode=text&id="
PNAS = "https://www.pnas.org/doi/suppl/10.1073/pnas.2118631119/suppl_file/"
FILES = {
    "mcfarland_pmc.xml": EPMC % "PMC8931364",
    "lanphear2005_pmc.xml": EPMC % "PMC1257652",
    "bellinger2012_pmc.xml": EPMC % "PMC3339460",
    "reuben2017_pubmed.txt": PUBMED + "28350927",
    "trahan2014_pubmed.txt": PUBMED + "24979188",
    "larsen2023.pdf": "https://web.archive.org/web/20250717170553id_/https://www.thelancet.com/action/showPdf"
                      "?pii=S2542-5196%2823%2900166-3",
    "gao_rced_86_80fs.pdf": "https://webarchive.library.unt.edu/eot2008/20081205084746id_/http://archive.gao.gov/d13t3/"
                            "129585.pdf",
    "epa_1996_phaseout.html": "https://www.epa.gov/archive/epa/aboutepa/epa-takes-final-step-phaseout-leaded-gasoline.html",
    "epa_ace_b1.xlsx": "https://www.epa.gov/system/files/documents/2025-12/b1.xlsx",
}
BROWSER = {
    "pnas_sd01.xlsx": PNAS + "pnas.2118631119.sd01.xlsx",
    "pnas_sd03.xlsx": PNAS + "pnas.2118631119.sd03.xlsx",
    "pnas_si_appendix.pdf": PNAS + "pnas.2118631119.sapp.pdf",
}


def yearbooks():
    """One OCR file per Minerals Yearbook volume the gasoline series cites."""
    out = {}
    with open(HERE / "data" / "gasoline_lead_myb.csv", encoding="utf-8") as f:
        for row in csv.DictReader(r for r in f if not r.startswith("#")):
            out[row["ocr_file"]] = row["ocr_url"]
    return out


if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    todo = dict(FILES)
    todo.update(yearbooks())
    for name, url in todo.items():
        if not only or name in only:
            p = fetch(url, name)
            if p.stat().st_size < 1500:
                raise SystemExit(f"{name}: {p.stat().st_size} bytes, not a document")
    for name, url in BROWSER.items():
        if not only or name in only:
            if not (RAW / name).exists():
                raise SystemExit(f"{name}: save {url} through a browser into data/raw/, then run again")
            record(name, url, "browser (pnas.org refuses scripted requests)")
