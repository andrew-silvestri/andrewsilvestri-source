"""The other public documents the lost-gas page quotes or reads.

- eia_a1_<year>.pdf, 2018-2024: EIA Natural Gas Annual, Table A1, natural gas
  losses and unaccounted for by state. Public domain with attribution
  (https://www.eia.gov/about/copyrights_reuse.php). 2024 is the current
  edition; earlier years are EIA's archive copies.
- fr_2018-01324.pdf: Federal Register 83 FR 3462 (2018-01-25), the PHMSA notice
  that moves percent LAUF to a consumption denominator and allows negatives.
- tx_16tac_ch7_2024.pdf: Railroad Commission of Texas, 16 TAC Chapter 7
  compilation effective 2024-04-08 (s.7.5525, Lost and Unaccounted for Gas).
- ok_oac165_ch45_2024.pdf: Oklahoma Corporation Commission, OAC 165 Chapter 45,
  Gas Service Utilities, effective 2024-10-01 (165:45-7-11).
- ok_oac165_ch50_2019.pdf: OAC 165 Chapter 50, Fuel, Purchased Gas, and
  Purchased Power Adjustment Clauses, effective 2019-07-25 (165:50-3-2).
- ok_tariff_<n>.pdf: the Commission-approved tariff schedules of Oklahoma's
  largest gas distribution utility that say how lost, used and unaccounted-for
  gas is recovered: 1001 (purchased gas adjustment clause), 1071 (unrecovered
  purchased gas cost), 1191 (lost, used and unaccounted-for gas rider). Cited
  in Sources for a public fact; the page's prose names no operator (packet).
- eia_<series>.xls: EIA annual series for Texas and Oklahoma, residential
  consumption (MMcf), residential consumers (count), residential price and
  citygate price ($/Mcf).

Run:  python fetch_public.py
"""
from netfetch import fetch

FILES = {f"eia_a1_{y}.pdf": f"https://www.eia.gov/naturalgas/annual/archive/{y}/pdf/table_a01.pdf"
         for y in range(2018, 2024)}
FILES["eia_a1_2024.pdf"] = "https://www.eia.gov/naturalgas/annual/pdf/table_a01.pdf"
FILES.update({
    "fr_2018-01324.pdf": "https://www.govinfo.gov/content/pkg/FR-2018-01-25/pdf/2018-01324.pdf",
    "tx_16tac_ch7_2024.pdf": "https://www.rrc.state.tx.us/media/ykpcxhmr/chapter7-all-effective-april8-2024.pdf",
    "ok_oac165_ch45_2024.pdf": ("https://oklahoma.gov/content/dam/ok/en/occ/documents/ajls/jls-courts/rules/2024/"
                                "chapter-45-gas-service-utilities-effective-10-01-24.pdf"),
    "ok_oac165_ch50_2019.pdf": ("https://oklahoma.gov/content/dam/ok/en/occ/documents/ajls/jls-courts/rules/"
                                "archive-2019-only/ch50finalrules072519.pdf"),
})
FILES.update({f"ok_tariff_{n}.pdf": f"https://www.oklahomanaturalgas.com/media/ONG/Tariffs/{n}.pdf"
              for n in (1001, 1071, 1191)})
EIA = {st: {"res_mmcf": f"N3010{st}2", "res_price": f"N3010{st}3", "citygate": f"N3050{st}3",
            "res_consumers": f"NA1501_S{st}_8"} for st in ("TX", "OK")}
FILES.update({f"eia_{code}a.xls": f"https://www.eia.gov/dnav/ng/hist_xls/{code}a.xls"
              for st in EIA.values() for code in st.values()})

if __name__ == "__main__":
    for name, url in FILES.items():
        fetch(url, name)
