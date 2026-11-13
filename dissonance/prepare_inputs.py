"""
Write the three input tables in data/ from the files the research step downloaded.

The research step fetched each source with curl on 7 November 2026 (URLs in data/SOURCES.md). This script
keeps only the rows and columns the page uses, so the archive carries small CSV files, not 20 MB of
spreadsheets. It does not change a value.

  data/eb_climate_2025.csv       Special Eurobarometer 565 (2025) and 538 (2023), EU27 rows of the
                                 action list (QD6 / QC6), the six-month question (QD5) and the
                                 seriousness question (QD2), read from the Volume A workbooks.
  data/eb565_qd3ab.csv           Special Eurobarometer 565, QD3ab ("best placed to tackle climate
                                 change", first and further answers), EU27, from Volume A; with the
                                 weighted total of the sheet, which is the EU27 sample.
  data/ivanova2020_options.csv   Ivanova et al. (2020) supplementary data, sheet "options": every row,
                                 nine of its 28 columns.
  data/owid_eu27.csv             Our World in Data CO2 dataset (Global Carbon Budget), European Union (27),
                                 2015 on: population, territorial and consumption-based CO2 per person.
  data/metayale2023_behaviour.csv Meta and Yale Climate Change Opinion Survey 2023, country aggregates:
                                 the adoption items and the barriers of those who have not adopted.

Run:  python prepare_inputs.py <lane research/data folder>
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")

IVA_COLS = ["ID", "Authors", "Publication year", "Original consumption options",
            "Aggregated consumption options", "Consumption domain",
            "Absolute carbon mitigation potential (tCO2eq/cap per year)", "Absolute Unit",
            "Geographical context"]


def main(src):
    eb = pd.read_csv(os.path.join(src, "eurobarometer", "eb_actions.csv"), dtype=str)
    eb.to_csv(os.path.join(OUT, "eb_climate_2025.csv"), index=False, lineterminator="\n")
    print(f"eb_climate_2025.csv: {len(eb)} rows")

    import openpyxl
    ws = openpyxl.load_workbook(os.path.join(src, "eurobarometer", "SP565_volume_A.xlsx"),
                                read_only=True)["QD3ab"]
    rows = list(ws.iter_rows(min_row=9, max_row=33, max_col=3, values_only=True))
    if "EU27" not in str(rows[0][2]) or rows[1][1] != "Total":
        raise SystemExit("QD3ab: column C is not EU27, or row 10 is not the total")
    total = rows[1][2]
    out = ["answer,weighted_count,published_share,weighted_total"]
    for fr, en in zip(rows[3::2], rows[4::2]):        # French row holds the count, English row the share
        out.append(f'"{en[1]}",{fr[2]},{en[2]},{total}')
    open(os.path.join(OUT, "eb565_qd3ab.csv"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"eb565_qd3ab.csv: {len(out) - 1} rows, total {total}")

    iva = pd.read_excel(os.path.join(src, "ivanova2020", "ERL_15_9_093001_suppdata.xlsx"),
                        sheet_name="options").dropna(how="all")
    iva = iva[IVA_COLS]
    iva.to_csv(os.path.join(OUT, "ivanova2020_options.csv"), index=False, lineterminator="\n")
    print(f"ivanova2020_options.csv: {len(iva)} rows")

    my = pd.read_csv(os.path.join(src, "metayale2023", "meta_2023_behaviors_aggregate.csv"))
    keep = my.variable.str.startswith("adoption_") | my.variable.str.endswith("_haventadopted")
    my = my[keep][["country_code", "country", "variable", "response", "N", "pct"]]
    my.to_csv(os.path.join(OUT, "metayale2023_behaviour.csv"), index=False, lineterminator="\n",
              float_format="%.4f")
    print(f"metayale2023_behaviour.csv: {len(my)} rows, {my.country_code.nunique()} countries")

    ow = pd.read_csv(os.path.join(src, "owid", "owid-co2-data.csv"))
    ow = ow[(ow.country == "European Union (27)") & (ow.year >= 2015)]
    ow = ow[["country", "year", "population", "co2_per_capita", "consumption_co2_per_capita"]]
    ow.to_csv(os.path.join(OUT, "owid_eu27.csv"), index=False, lineterminator="\n")
    print(f"owid_eu27.csv: {len(ow)} rows")


if __name__ == "__main__":
    main(sys.argv[1])
