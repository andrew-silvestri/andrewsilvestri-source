"""The public EIA files the ethane page reads, fetched into ethane/data/raw/ and recorded in data/fetched.json.

Data (EIA, public domain with attribution)
- eia_ngpl_by_product_m.xls: field production of natural gas liquids by product, US, thousand barrels a day,
  monthly (ethane, propane, butanes, natural gasoline).
- eia_mer_a1.pdf: Monthly Energy Review, Appendix A, Table A1 (heat content of petroleum products, ethane).

What EIA has written about ethane rejection (the dated record the page is built on)
- eia_tie_<id>.html: Today in Energy articles; eia_ngwu_<date>.html: Natural Gas Weekly Update.
- eia_copyright.html: EIA's copyright and reuse page.

Run:  python fetch_public.py [name ...]
"""
from netfetch import fetch

TIE = "https://www.eia.gov/todayinenergy/detail.php?id="
FILES = {
    "eia_ngpl_by_product_m.xls": "https://www.eia.gov/dnav/pet/xls/PET_PNP_GP_DC_NUS_MBBLPD_M.xls",
    "eia_mer_a1.pdf": "https://www.eia.gov/totalenergy/data/monthly/pdf/sec12_2.pdf",
    "eia_ngwu_2019-02-14.html": "https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2019/02_14/",
    "eia_copyright.html": "https://www.eia.gov/about/copyrights_reuse.php",
}
for _id in (9590, 12291, 16191, 18371, 25632, 28052, 39712, 44456, 53659, 64785):
    FILES[f"eia_tie_{_id}.html"] = TIE + str(_id)


if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    for name, url in FILES.items():
        if not only or name in only:
            p = fetch(url, name)
            if p.stat().st_size < 4000:
                raise SystemExit(f"{name}: {p.stat().st_size} bytes, not a document")
