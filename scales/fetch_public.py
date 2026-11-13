"""The public files the scales page reads, fetched into scales/data/raw/ and recorded in data/fetched.json.

Data
- hatton_link_scaling.zip: Hatton, Dobson, Storch, Galbraith and Loreau (2019), "Linking scaling laws
  across eukaryotes", PNAS 116:21616. Code and data, Zenodo record 3145281 (CC BY 4.0).
  Data/Metabolism.csv: 8,098 measurements of resting or basal metabolic power (W) and body mass (g).
- eker2018_table1.tsv: Eker and others (2018), MNRAS 479:5491. Masses, radii and effective
  temperatures of main-sequence stars in detached eclipsing binaries (VizieR J/MNRAS/479/5491, table1).
- owid_energy_per_capita.csv: Our World in Data, primary energy per person, kWh a year, from the
  Energy Institute Statistical Review and the US EIA (CC BY 4.0).
- owid_energy_per_capita.json: the metadata of that file (sources, method, date).
- bea_cagdp1.zip: US Bureau of Economic Analysis, GDP by county, current dollars, 2001-2024.
- census_cbsa_2023.csv: US Census Bureau, population estimates of metropolitan and micropolitan
  statistical areas and their counties, 2020-2023.

Documents the page quotes or reads figures from
- iau_2015_b3.pdf: Prsa and others (2016), AJ 152:41, arXiv:1605.09788: IAU 2015 Resolution B3
  (nominal solar luminosity and solar mass parameter).

Run:  python fetch_public.py [name ...]
"""
from netfetch import fetch

OWID = "https://ourworldindata.org/grapher/per-capita-energy-use"
FILES = {
    "hatton_link_scaling.zip": "https://zenodo.org/api/records/3145281/files/Link-scaling.zip/content",
    "eker2018_table1.tsv": "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/MNRAS/479/5491/table1"
                           "&-out.max=unlimited&-out.all",
    "owid_energy_per_capita.csv": OWID + ".csv?v=1&csvType=full&useColumnShortNames=true",
    "owid_energy_per_capita.json": OWID + ".metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "bea_cagdp1.zip": "https://apps.bea.gov/regional/zip/CAGDP1.zip",
    "census_cbsa_2023.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/metro/"
                            "totals/cbsa-est2023-alldata.csv",
    "iau_2015_b3.pdf": "https://arxiv.org/pdf/1605.09788",
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
            floor = 500 if name.endswith(".json") else 3000   # the metadata file is small by nature
            if p.stat().st_size < floor:
                bad.append(f"{name}: {p.stat().st_size} bytes, not a document")
        except Exception as e:   # report every failure, then exit 1
            bad.append(f"{name}: {e}")
    if bad:
        raise SystemExit("\n".join(bad))
