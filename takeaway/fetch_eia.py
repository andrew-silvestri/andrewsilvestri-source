"""EIA files for the takeaway page. EIA data are public domain with attribution
(https://www.eia.gov/about/copyrights_reuse.php).

- STEO_m.xlsx: the Short-Term Energy Outlook's monthly data workbook, every
  table including 10a (drilling productivity, by region) and 10b (shale gas by
  formation). Index https://www.eia.gov/outlooks/steo/data/browser/
  10a has rigs, wells, DUCs, new-well gas and the existing-production change
  for the Permian region, but no total production row.
- 10atab.pdf, 10btab.pdf: the same tables as published, to check the
  workbook's sheet against the table EIA prints.
- EIA-NaturalGasPipelineProjectsAug2026.xlsx: the pipeline projects tracker.
  Index https://www.eia.gov/naturalgas/pipelines/

Run:  python fetch_eia.py
"""
from netfetch import fetch

FILES = {
    "STEO_m.xlsx": "https://www.eia.gov/outlooks/steo/xls/STEO_m.xlsx",
    "10atab.pdf": "https://www.eia.gov/outlooks/steo/tables/pdf/10atab.pdf",
    "10btab.pdf": "https://www.eia.gov/outlooks/steo/tables/pdf/10btab.pdf",
    # The Drilling Productivity Report's last standalone workbook (May 2024),
    # before DPR moved into STEO 10a. It carries total gas production by
    # region, which STEO 10a does not.
    "dpr-data.xlsx": "https://www.eia.gov/petroleum/drilling/xls/dpr-data.xlsx",
    # Natural gas production summary by state, annual (MMcf): gross
    # withdrawals (by well type), repressuring, vented and flared,
    # nonhydrocarbon gases removed, marketed production, natural gas plant
    # liquids production (gaseous equivalent), dry production.
    # https://www.eia.gov/dnav/ng/ng_prod_sum_dc_stx_mmcf_a.htm (and _snm_)
    "NG_PROD_SUM_DC_STX_MMCF_A.xls": "https://www.eia.gov/dnav/ng/xls/NG_PROD_SUM_DC_STX_MMCF_A.xls",
    "NG_PROD_SUM_DC_SNM_MMCF_A.xls": "https://www.eia.gov/dnav/ng/xls/NG_PROD_SUM_DC_SNM_MMCF_A.xls",
    "EIA-NaturalGasPipelineProjectsAug2026.xlsx":
        "https://www.eia.gov/naturalgas/pipelines/EIA-NaturalGasPipelineProjectsAug2026.xlsx",
}

if __name__ == "__main__":
    for name, url in FILES.items():
        fetch(url, name)
