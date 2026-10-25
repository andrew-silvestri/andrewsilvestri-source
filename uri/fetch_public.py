"""The public documents the Uri page reads, fetched into uri/data/raw/ and recorded in data/fetched.json.

Texas
- tx_os_2023.pdf: Texas Natural Gas Securitization Finance Corporation, Customer Rate Relief Bonds
  (Winter Storm Uri), Taxable Series 2023, Official Statement dated March 9, 2023 (tranches, coupons,
  the expected amortization schedule, the regulatory asset amounts, sources and uses).
- tx_outstanding_2026.pdf: the Corporation's Report of Outstanding Bonds and Estimated Administrative
  Expenses, prepared 01/28/2026 (balances at 12/31/2025: a check on the schedule).
- tx_utilcode_104.pdf: Texas Utilities Code Chapter 104 (Subchapter I, customer rate relief, HB 1520).
- tx_rrc_2023-10-04.html: Railroad Commission announcement of the first charge, October 2023.
- tx_tariff_6263.pdf, tx_tariff_6776.pdf, tx_tariff_6931.pdf: RRC gas tariff reports (CenterPoint Energy
  Entex/Texas Gas, Atmos Energy Mid-Tex, Atmos Energy West Texas) carrying the customer rate relief rate and its true-ups.
- tx_atmos_midtex_2025-07.pdf: Atmos Energy Mid-Tex tariff book effective 07-01-2025 (the CRR rate of
  2024-25, $0.1180/Ccf).
- tx_tgs_crr.pdf, tx_tgs_securitization.html: Texas Gas Service's rate schedule CRR and its page stating
  the charge per Mcf and what an average residential customer pays a month (the known answer).

Oklahoma
- ok_ong_order.pdf, ok_suo_order.pdf: Oklahoma Corporation Commission financing orders 723033 (Oklahoma
  Natural Gas, PUD 202100079) and 723435 (Summit Utilities Oklahoma, formerly CenterPoint Energy
  Oklahoma Gas, PUD 202100087).
- ok_ong_ial.pdf, ok_suo_ial.pdf: the Issuance Advice Letters (final terms, sinking fund schedules,
  ongoing costs, the initial charge by class and its workpapers).
- ok_ong_trueup_2026-03.pdf, ok_suo_trueup_2026-03.pdf: the latest true-up letters (charges from May 2026).
- ok_suo_servicer_2026-09.pdf: Summit's servicer's certificate of 2026-09-24 (balance after the October 1, 2026
  payment: a check on the schedule).
- ok_sb1050.pdf, ok_74os_9073.html: SB 1050 (2021) as enrolled, the February 2021 Regulated Utility Consumer
  Protection Act, and 74 O.S. s.9073 as codified.
- ok_sb1049.pdf: SB 1049 (2021) as enrolled, the act for cooperative and municipal utilities.

EIA (public domain with attribution): residential consumption (MMcf) and residential consumers, Texas
and Oklahoma, annual; the same series lostgas/ reads. eia_glossary_c.html: EIA's glossary, letter C
(the cubic foot of natural gas at 60 F and 14.73 psia).

The OCC and the Texas issuer serve their files to scripted clients; when one does not, the copy saved by
the research pass with curl on 2026-10-24 (03 RESEARCH/uri/refs/) is recorded instead, and the manifest
says so in its "via" column.

Run:  python fetch_public.py
"""
import shutil
from pathlib import Path

from netfetch import RAW, fetch, record

OCC = "https://oklahoma.gov/content/dam/ok/en/occ/documents/pu/pud-reports-page/securitization-reports/"
FILES = {
    "tx_os_2023.pdf": ("https://tngsfc.com/bonddocs/TNGSFC%20CRR%20Bonds,%20Taxable%20Series%202023.pdf",
                       "tx/TNGSFC_CRR_Bonds_Series2023_OS.pdf"),
    "tx_outstanding_2026.pdf": ("https://tngsfc.com/pdf/Report%20of%20Oustanding%20Bonds%20and%20Estimated%20"
                                "Administrative%20Expenses.pdf", "tx/TNGSFC_Report_Outstanding_Bonds_Admin_Expenses.pdf"),
    "tx_utilcode_104.pdf": ("https://tcss.legis.texas.gov/resources/UT/pdf/UT.104.pdf", "tx/TX_UtilCode_Ch104.pdf"),
    "tx_rrc_2023-10-04.html": ("https://www.rrc.texas.gov/announcements/100423-customer-rate-relief-charges-"
                               "included-natural-gas-bills-starting-october-2023",
                               "tx/RRC_announcement_2023-10-04_CRR_charges_Oct2023.html"),
    "tx_tariff_6263.pdf": ("https://rrc.texas.gov/media/gastariffs/gftr0048b_6263.pdf", "tx/RRC_tariff_gftr0048b_6263.pdf"),
    "tx_tariff_6776.pdf": ("https://www.rrc.texas.gov/media/gastariffs/gftr0048b_6776.pdf", "tx/RRC_tariff_gftr0048b_6776.pdf"),
    "tx_tariff_6931.pdf": ("https://www.rrc.texas.gov/media/gastariffs/gftr0048b_6931.pdf", "tx/RRC_tariff_gftr0048b_6931.pdf"),
    "tx_atmos_midtex_2025-07.pdf": (("https://www.atmosenergy.com/static/372582059e73b4772075f6dd74107497/"
                                     "Mid-Tex%20Tariffs%20-%20July%201,%202025.pdf"),
                                    "tx/Atmos_MidTex_Tariffs_2025-07-01.pdf"),
    "tx_tgs_crr.pdf": ("https://www.texasgasservice.com/media/TGS/Tariffs/All/CRR.pdf", "tx/TGS_RateSchedule_CRR.pdf"),
    "tx_tgs_securitization.html": ("https://www.texasgasservice.com/Securitization", "tx/TGS_securitization_page.html"),
    "ok_ong_order.pdf": (OCC + "securitization-costs/ong/ong-financing-order-723033.pdf", "ok/ong_financing_order_723033.pdf"),
    "ok_ong_ial.pdf": (OCC + "securitization-costs/ong/ong-issuance-advice-letter.pdf",
                       "ok/ong_issuance_advice_letter_2022-08-23.pdf"),
    "ok_ong_trueup_2026-03.pdf": (OCC + "ong/2026-03-02-ong-trueup-letter-and-workpapers.pdf",
                                  "ok/ong_trueup_letter_2026-03-02.pdf"),
    "ok_suo_order.pdf": (OCC + "securitization-costs/summit/suo-financing-order-723435.pdf",
                         "ok/suo_financing_order_723435.pdf"),
    "ok_suo_ial.pdf": (OCC + "securitization-costs/summit/suo-issuance-advice-letter.pdf", "ok/suo_issuance_advice_letter.pdf"),
    "ok_suo_trueup_2026-03.pdf": (OCC + "summit/2026-03-27-suo-trueup-letter.pdf", "ok/suo_trueup_letter_2026-03-27.pdf"),
    "ok_suo_servicer_2026-09.pdf": (OCC + "summit/2026-09-24-suo-servicers-certificate.pdf",
                                    "ok/suo_servicers_certificate_2026-09-24.pdf"),
    "ok_sb1049.pdf": ("https://oklegislature.gov/cf_pdf/2021-22%20enr/sb/sb1049%20enr.pdf",
                      "ok/ok_sb1049_2021_enrolled_UNREGULATED_utility_act.pdf"),
    "ok_sb1050.pdf": ("https://oklegislature.gov/cf_pdf/2021-22%20enr/sb/sb1050%20enr.pdf",
                      "ok/ok_sb1050_2021_enrolled_regulated_utility_act.pdf"),
    "ok_74os_9073.html": ("https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID=488457", "ok/oscn_74OS_9073.html"),
}
FILES["eia_glossary_c.html"] = ("https://www.eia.gov/tools/glossary/index.php?id=C", None)
for st in ("TX", "OK"):
    for code in (f"N3010{st}2", f"NA1501_S{st}_8"):
        FILES[f"eia_{code}a.xls"] = (f"https://www.eia.gov/dnav/ng/hist_xls/{code}a.xls", None)

REFS = Path(__file__).resolve().parents[2] / "03 RESEARCH" / "uri" / "refs"


def looks_real(p):
    b = p.read_bytes()[:2048].lower()
    return len(p.read_bytes()) > 4000 and (b.startswith(b"%pdf") or b"<html" in b or b"<!doctype" in b
                                           or b.startswith(b"\xd0\xcf\x11\xe0"))


if __name__ == "__main__":
    import sys
    only = sys.argv[1:]                              # optional: fetch only the files named
    for name, (url, ref) in FILES.items():
        if only and name not in only:
            continue
        try:
            p = fetch(url, name)
            if not looks_real(p):
                raise RuntimeError("not a document (%d bytes)" % p.stat().st_size)
        except Exception as e:                       # noqa: BLE001 - any refusal falls back to the saved copy
            if ref is None:
                raise
            shutil.copyfile(REFS / ref, RAW / name)
            record(name, url, f"curl 2026-10-24, research copy 03 RESEARCH/uri/refs/{ref} (urllib: {str(e)[:60]})")
