"""Texas Railroad Commission files for the takeaway page. RRC data are public.

- permian-basin-2008-to-current.xlsx: the RRC's own Permian Basin workbook,
  from https://www.rrc.texas.gov/oil-and-gas/major-oil-and-gas-formations/permian-basin/
  That page defines the basin for RRC production figures as "districts 7C,
  08, and 8A".
- pdq-dump-user-manual.pdf: column definitions for the Production Data Query
  dump, from https://www.rrc.texas.gov/resource-center/research/data-sets-available-for-download/
- pr-disposition-codes.pdf: Form PR disposition codes (gas code 4 is
  "Vented or flared"), from
  https://www.rrc.texas.gov/oil-and-gas/research-and-statistics/production-data/

The dump itself (PDQ_DSV.zip, up to 5 GB) is served from mft.rrc.texas.gov
and is fetched by fetch_pdq.py.

Run:  python fetch_rrc.py
"""
from netfetch import fetch

FILES = {
    "permian-basin-2008-to-current.xlsx":
        "https://www.rrc.texas.gov/media/aagdoxfx/permian-basin-2008-to-current.xlsx",
    "pdq-dump-user-manual.pdf": "https://www.rrc.texas.gov/media/50ypu2cg/pdq-dump-user-manual.pdf",
    "pr-disposition-codes.pdf": "https://www.rrc.texas.gov/media/wzsbfq4u/pr-disposition-codes.pdf",
}

if __name__ == "__main__":
    for name, url in FILES.items():
        fetch(url, name)
