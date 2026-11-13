"""The public files the space-depression page reads, fetched into data/raw/ and recorded in data/fetched.json.

Data
- mcd_rides.tsv, mcd_missions.tsv: Jonathan McDowell's astronaut tables (planet4589.org, CC-BY 4.0): one row per
  person per flight, with the flight's duration, and one row per mission, with a deep-space flag.
- horizons_mars.txt: JPL Horizons, Mars seen from Earth's centre, daily, 2033-01-01 to 2036-06-30: range, one-way
  light time, Sun-Earth-Mars angle.
- horizons_moon.txt: JPL Horizons, the Moon seen from Earth's centre, hourly through 2033: one-way light time.

Documents the page reads figures out of
- bmed_er.txt: NASA HRP Evidence Report, Risk of Adverse Cognitive or Behavioral Conditions and Psychiatric
  Disorders (NTRS 20250001454, approved February 2025), NTRS's text rendition of the .docx.
- hsrb_rr.pdf: NASA Human System Risk Board, Behavioral Health risk record, Rev D.1 (2025): the current ratings.
- basner2014.xml: Basner et al. 2014, PLoS ONE 9(3):e93298, Mars-500 psychological responses (manuscript XML).
- basner2013.html: Basner et al. 2013, PNAS 110(7):2635, Mars-500 sleep and activity (PMC3574912).
- palinkas2004.txt: Palinkas et al. 2004, Int J Circumpolar Health 63(2):157, Antarctic winter-over (abstract).
- kanas2001.txt, kanas2007.txt: Kanas et al., Shuttle/Mir and ISS crew mood studies (abstracts).
- barger2014.html: Barger et al. 2014, Lancet Neurology 13:904, sleep and hypnotics on ISS and shuttle (PMC4188436).
- dra5.pdf: NASA SP-2009-566, Mars Design Reference Architecture 5.0 (mission durations).
- mars_comm.pdf: NASA Moon to Mars white paper, Mars Communications Disruption and Delay (2023).
- nsduh2025.pdf: SAMHSA, 2025 National Survey on Drug Use and Health, annual national report.
- ihle2006.txt: Ihle et al. 2006, Aviat Space Environ Med 77:93, positive outcomes of spaceflight (abstract).
- chapea.html: NASA's CHAPEA page (mission dates, crew size).
- sandal2018.html: Sandal et al. 2018, Front Psychol 9:2235, Concordia winter-over, coping, mood and sleep.
- rosenberg2022.html: Rosenberg et al. 2022, Front Physiol 13:898841, HI-SEAS missions 3 to 5.
- arch2025.pdf: NASA 2025 Architecture Update (Mars surface crew size).

Run:  python fetch_public.py [name ...]
"""
from netfetch import fetch

HZ = ("https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND=%27{c}%27&OBJ_DATA=%27NO%27"
      "&MAKE_EPHEM=%27YES%27&EPHEM_TYPE=%27OBSERVER%27&CENTER=%27500%40399%27&START_TIME=%27{a}%27"
      "&STOP_TIME=%27{b}%27&STEP_SIZE=%27{s}%27&QUANTITIES=%2720%2C21%2C23%27&CSV_FORMAT=%27YES%27")
EF = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&retmode=text&id="
FILES = {
    "mcd_rides.tsv": "https://planet4589.org/space/astro/tsv/rides.tsv",
    "mcd_missions.tsv": "https://planet4589.org/space/astro/tsv/missions.tsv",
    "horizons_mars.txt": HZ.format(c="499", a="2033-01-01", b="2036-06-30", s="1d"),
    "horizons_moon.txt": HZ.format(c="301", a="2033-01-01", b="2033-12-31", s="1h"),
    "bmed_er.txt": "https://ntrs.nasa.gov/api/citations/20250001454/downloads/"
                   "BMed%20Evidence%20Report%20final%202-10-25.docx.txt",
    "hsrb_rr.pdf": "https://www.nasa.gov/wp-content/uploads/2025/09/hsrb-behavioral-health-risk-record-rev-d-1-web.pdf",
    "basner2014.xml": "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0093298&type=manuscript",
    "basner2013.html": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3574912/",
    "palinkas2004.txt": EF + "15253482",
    "kanas2001.txt": EF + "11865867",
    "kanas2007.txt": EF + "17571662",
    "barger2014.html": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4188436/",
    "dra5.pdf": "https://www.nasa.gov/wp-content/uploads/2015/09/373665main_nasa-sp-2009-566.pdf",
    "mars_comm.pdf": "https://www.nasa.gov/wp-content/uploads/2024/01/mars-communications-disruption-and-delay.pdf",
    "nsduh2025.pdf": "https://www.samhsa.gov/data/sites/default/files/reports/rpt57150/2025-nsduh-annual-national-report.pdf",
    "ihle2006.txt": EF + "16491575",
    "chapea.html": "https://www.nasa.gov/humans-in-space/chapea/",
    "sandal2018.html": "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.02235/full",
    "rosenberg2022.html": "https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2022.898841/full",
    "arch2025.pdf": "https://www.nasa.gov/wp-content/uploads/2025/12/2025-architecture-update-for-publication.pdf",
}


if __name__ == "__main__":
    import sys
    import time
    only = sys.argv[1:]
    bad = []
    for name, url in FILES.items():
        if only and name not in only:
            continue
        try:
            p = fetch(url, name)
            if p.stat().st_size < 1000:
                bad.append(f"{name}: {p.stat().st_size} bytes, not a document")
        except Exception as e:   # report every failure, then exit 1
            bad.append(f"{name}: {e}")
        if "eutils" in url:
            time.sleep(1.2)       # NCBI refuses more than three requests a second
    if bad:
        raise SystemExit("\n".join(bad))
