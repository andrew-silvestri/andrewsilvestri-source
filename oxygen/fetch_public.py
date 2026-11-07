"""The public files the oxygen page reads, fetched into oxygen/data/raw/ and recorded in data/fetched.json.

Data
- eia_mtbe_net_input_m.xls: refinery and blender net input of MTBE, US, thousand barrels a month (EIA MMTRIUS1).
- eia_mer_t1003.csv: Monthly Energy Review Table 10.3, fuel ethanol overview, monthly and annual (EIA).
- eia_gasoline_supplied_a.xls: finished motor gasoline product supplied, US, thousand barrels a day (EIA MGFUPUS2).
- eia_rfg_supplied_a.xls: reformulated motor gasoline product supplied, US, thousand barrels a day (EIA MGRUPUS2).
- ers_feed_grains.csv: USDA ERS Feed Grains Database, yearbook tables, all years (corn production and use).

Documents the page quotes or reads figures from
- uscode_7545_2000.html: 42 U.S.C. 7545 (Clean Air Act section 211), 2000 edition: the oxygen requirements.
- dole_1990.pdf: Senator Dole's press release of 29 March 1990 on the reformulated gasoline amendment.
- crec_2000_s3514.html: Congressional Record, 4 May 2000, Senator Daschle introducing S. 2503.
- eia_mtbe_1999.pdf: EIA, "MTBE, Oxygenates, and Motor Gasoline" (1999/2000): MTBE demand by year and use.
- epa_brp_1999.pdf: EPA Blue Ribbon Panel on Oxygenates in Gasoline, report, September 1999.
- usgs_wri034200.pdf: USGS WRIR 03-4200, MTBE in ground water and source water, 1993-2002 (2004).
- epa_state_bans_2007.pdf: EPA420-B-07-013, State Actions Banning MTBE (Statewide), August 2007 (archived).
- fr_2006_26691.pdf: Federal Register 71 FR 26691, 8 May 2006: removal of the RFG oxygen content requirement.
- eia_mtbe2006.pdf: EIA, "Eliminating MTBE in Gasoline in 2006", 22 February 2006.
- nrc_1999_ozone.html: National Research Council, Ozone-Forming Potential of Reformulated Gasoline (1999), summary.
- plaw_109_58.html: Energy Policy Act of 2005, Public Law 109-58 (the renewable fuel program and the oxygen repeal).
- epa_mtbe_water.html, epa_mtbe_gas.html: EPA's archived MTBE pages (Santa Monica; taste and odour; use since 1979).
- eia_faq_ethanol.html: EIA FAQ, how much ethanol is in gasoline (E10).
- lark_reply_2022.pdf: Lark and others, reply to Taheripour et al.'s comments on their 2022 PNAS study.
- eia_copyright.html: EIA's copyright and reuse page.

Run:  python fetch_public.py [name ...]
"""
from netfetch import fetch

DNAV = "https://www.eia.gov/dnav/pet/hist_xls/"
FILES = {
    "eia_mtbe_net_input_m.xls": DNAV + "MMTRIUS1m.xls",
    "eia_mer_t1003.csv": "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T10.03",
    "eia_gasoline_supplied_a.xls": DNAV + "MGFUPUS2a.xls",
    "eia_rfg_supplied_a.xls": DNAV + "MGRUPUS2a.xls",
    "ers_feed_grains.csv": "https://www.ers.usda.gov/media/5766/feed-grains-yearbook-tables-all-years.csv",
    "uscode_7545_2000.html": "https://www.govinfo.gov/content/pkg/USCODE-2000-title42/html/"
                             "USCODE-2000-title42-chap85-subchapII-partA-sec7545.htm",
    "dole_1990.pdf": "https://dolearchivecollections.ku.edu/collections/press_releases/900329ame.pdf",
    "crec_2000_s3514.html": "https://www.congress.gov/106/crec/2000/05/04/146/54/modified/CREC-2000-05-04-pt1-PgS3514-2.htm",
    "eia_mtbe_1999.pdf": "https://www.eia.gov/outlooks/steo/special/pdf/mtbe.pdf",
    "epa_brp_1999.pdf": "https://archive.epa.gov/oust/mtbe-a/web/pdf/r99021.pdf",
    "usgs_wri034200.pdf": "https://pubs.usgs.gov/wri/wri034200/wri034200.pdf",
    "epa_state_bans_2007.pdf": "http://web.archive.org/web/2009id_/http://www.epa.gov/mtbe/420b07013.pdf",
    "fr_2006_26691.pdf": "https://www.govinfo.gov/content/pkg/FR-2006-05-08/pdf/06-4252.pdf",
    "eia_mtbe2006.pdf": "https://www.eia.gov/petroleum/archive/mtbe2006.pdf",
    "nrc_1999_ozone.html": "https://www.nationalacademies.org/read/9461/chapter/2",
    "plaw_109_58.html": "https://www.govinfo.gov/content/pkg/PLAW-109publ58/html/PLAW-109publ58.htm",
    "epa_mtbe_water.html": "https://archive.epa.gov/mtbe/web/html/water.html",
    "epa_mtbe_gas.html": "https://archive.epa.gov/mtbe/web/html/gas.html",
    "eia_faq_ethanol.html": "https://www.eia.gov/tools/faqs/faq.php?id=27&t=10",
    "lark_reply_2022.pdf": "https://www.gibbs-lab.wisc.edu/assets/Reply-to-Taheripour-et-al.pdf",
    "eia_copyright.html": "https://www.eia.gov/about/copyrights_reuse.php",
}


if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    bad = []
    for name, url in FILES.items():
        if only and name not in only:
            continue
        try:
            p = fetch(url, name)
            if p.stat().st_size < 3000:
                bad.append(f"{name}: {p.stat().st_size} bytes, not a document")
        except Exception as e:   # report every failure, then exit 1
            bad.append(f"{name}: {e}")
    if bad:
        raise SystemExit("\n".join(bad))
