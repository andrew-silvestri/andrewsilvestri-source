"""Dated list of gas pipeline capacity leaving the Permian Basin.

What counts. A project is on the list when (a) its origin is in the basin
(Waha hub, the Delaware or Midland basin, or the New Mexico Permian) and (b)
a cited source describes it as moving gas out of the Permian. Excluded, with
the reason in EXCLUDED below: lines that connect points inside the basin,
lines that start downstream of it, and laterals.

The list starts after the capacity anchor. EIA reports PointLogic's estimate
of Permian pipeline takeaway capacity twice in the same week, at two values:
17.5 Bcf/d (Natural Gas Weekly Update, 2022-05-25) and 18 Bcf/d "as of May
2022" (Today in Energy 52598, 2022-06-02). The anchor carries both. That
estimate's definition of takeaway is not published; EIA counted Double E,
which runs from New Mexico to Waha, in the 5.5 Bcf/d "of takeaway capacity"
added in 2021, so it is wider than (a) and (b) above. Additions after the
anchor are therefore a different accounting stacked on it, and the page says
so.

Capacity and the tracker's own dates are read from EIA's pipeline projects
tracker (Aug 2026) by project name, never typed here, so a re-download that
changes them changes the list. A date the tracker does not give, or one a
newer source supersedes, is an overlay below with its source and the words
it rests on. `status` is "confirmed" only where an opened source says the
line is in service; everything else is "expected" and the page prints it as
"expected, per <source, date>".
"""
import datetime as dt

import openpyxl

from netfetch import verified

TRACKER = "EIA-NaturalGasPipelineProjectsAug2026.xlsx"
TRACKER_CITE = "EIA natural gas pipeline projects tracker, Aug 2026"

ANCHOR = {
    "date": (2022, 5),
    "bcfd": (17.5, 18.0),
    "sources": [
        ("EIA Natural Gas Weekly Update, 2022-05-25",
         "https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2022/05_26/",
         "takeaway capacity in the Permian, which is currently estimated to total 17.5 Bcf/d, according to PointLogic"),
        ("EIA Today in Energy, 2022-06-02",
         "https://www.eia.gov/todayinenergy/detail.php?id=52598",
         "Pipeline takeaway capacity in the Permian Basin is estimated to be 18 Bcf/d as of May 2022, according to PointLogic"),
    ],
}

# Each entry: tracker project name (exact), the sheet it is on, and, where the
# tracker is not the last word, an overlay with the month, status and source.
# "phase" splits a project whose capacity arrives in parts; its share is the
# tracker total times the fraction the source states.
PROJECTS = [
    {"name": "Oasis Pipeline Modernization Project ", "sheet": "hist"},
    {"name": "Whistler Pipeline Expansion", "sheet": "hist",
     "takeaway_source": ("EIA Today in Energy 56800, 2023-06-13",
                         "The Whistler Pipeline Capacity Expansion is expanding compression by installing three new "
                         "compressor stations on the pipeline, increasing capacity by 0.5 Bcf/d to 2.5 Bcf/d")},
    {"name": "Permian Highway Pipeline Expansion", "sheet": "hist"},
    {"name": "Matterhorn Express Pipeline", "sheet": "hist",
     # The tracker's Completed Date is 2024-09-15; EIA's own article says
     # October. Industrial Info reported it "now moving small amounts of gas"
     # on 2024-10-03. The month shown is October, and the disagreement is
     # carried rather than resolved.
     "overlay": {"month": (2024, 10), "status": "confirmed",
                 "source": ("EIA Today in Energy 64445, 2025-02-03",
                            "https://www.eia.gov/todayinenergy/detail.php?id=64445",
                            "entered service in October 2024"),
                 "disagrees": "tracker Completed Date 2024-09-15"}},
    {"name": "Tarzan Compressor Station Project", "sheet": "hist",
     # Tracker Completed Date 2025-11-05; its own note still reads "target
     # in-service 2026". The Completed Date is the field the tracker defines
     # as "completed or put in service", so it is used, and the note is
     # carried as a disagreement.
     "disagrees": "tracker note: target in-service 2026"},
    {"name": "Gulf Coast Express Expansion", "sheet": "current",
     "overlay": {"month": (2026, 6), "status": "confirmed",
                 "source": ("Pipeline & Gas Journal, 2026-07-23 (Kinder Morgan Q2 2026 results)",
                            "https://pgjonline.com/news/2026/july/kinder-morgan-raises-2026-outlook-as-gas-project-backlog-tops-96-billion",
                            "In June, the company placed the Gulf Coast Express expansion into service, increasing "
                            "transportation capacity by approximately 570 MMcf/d from the Permian Basin to South Texas")}},
    {"name": "Hugh Brinson Pipeline (formerly Warrior Pipeline) Phase I & II", "sheet": "current",
     "phase": ("Phase I", 1.5 / 2.2),
     "overlay": {"month": (2026, 9), "status": "confirmed",
                 "source": ("BIC Magazine, 2026-08-05",
                            "https://www.bicmagazine.com/projects-expansions/midstream/energy-transfer-started-hugh-brinson-pipeline/",
                            "has officially brought its Hugh Brinson Pipeline into commercial service ... on track to "
                            "reach its full Phase I capacity of 1.5 Bcf/d by September 1, 2026"),
                 "note": "in service from 2026-08; full 1.5 Bcf/d expected by 2026-09-01, shown from September"}},
    {"name": "Hugh Brinson Pipeline (formerly Warrior Pipeline) Phase I & II", "sheet": "current",
     "phase": ("Phase II", 0.7 / 2.2),
     "overlay": {"month": (2027, 1), "status": "expected",
                 "source": ("EIA Today in Energy 67707, 2026-05-26",
                            "https://www.eia.gov/todayinenergy/detail.php?id=67707",
                            "phase 2 to begin operations in the first quarter of 2027")}},
    {"name": "Blackcomb Pipeline", "sheet": "current",
     # Three dates from three sources, none confirming a start. Enbridge said
     # commissioning began 2026-07-31. The tracker's note (updated
     # 2026-07-06) is the latest dated expectation, so it sets the month.
     "overlay": {"month": (2026, 11), "status": "expected",
                 "source": (TRACKER_CITE, None, "In-service pushed back from July to November 2026"),
                 "also": [("EIA Today in Energy 67707, 2026-05-26", "slated to enter service in the third quarter 2026"),
                          ("Enbridge, 2026-08-06", "has begun commissioning and will soon enter service and ramp up "
                                                   "through the second half of 2026")]}},
    {"name": "Permian West Expansion", "sheet": "current",
     # The tracker gives a year only. Placed in January of it, and the page
     # states the year, not the month.
     "overlay": {"month": (2027, 1), "status": "expected", "year_only": True,
                 "source": (TRACKER_CITE, None, "Target in-service 2027")}},
    {"name": "Waha to Mexico (Wahalajara System Expansion)", "sheet": "current",
     "phase": ("Phase 1", 150 / 300),
     "overlay": {"month": (2027, 1), "status": "expected",
                 "source": (TRACKER_CITE, None, "Phase 1 (+150 MMcf/d) reached FID Sept 2025, fully sold, expected start Q1 2027")}},
    {"name": "Eiger Express Pipeline", "sheet": "current",
     "overlay": {"month": (2028, 7), "status": "expected",
                 "source": (TRACKER_CITE, None, "mid-2028 in-service retained")}},
    {"name": "DeLa Express Project", "sheet": "current",
     "overlay": {"month": (2028, 7), "status": "expected",
                 "source": (TRACKER_CITE, None, "in-service targeted July 2028"),
                 "note": "record last updated 2024-04-15; pre-applied at FERC"}},
    {"name": "Desert Southwest expansion project", "sheet": "current",
     "overlay": {"month": (2029, 10), "status": "expected",
                 "source": (TRACKER_CITE, None, "target in-service Q4 2029")}},
    {"name": "Saguaro Connector Pipeline", "sheet": "current",
     "overlay": {"month": (2030, 2), "status": "expected",
                 "source": (TRACKER_CITE, None, "pushing completion date from 2/15/27 unitl 2/15/30")}},
]

EXCLUDED = {
    "Apex": "status On Hold",
    "Blackfin Pipeline": "starts in Colorado County, downstream of the basin",
    "Traverse Pipeline": "Agua Dulce to Katy, downstream",
    "Mustang Express Pipeline": "Katy to Port Arthur, downstream",
    "Buffalo Run": "connects systems inside the basin",
    "Bull Run Extension": "Winkler County to Waha, inside the basin",
    "Forza pipeline": "Lea County NM to Winkler County TX, inside the basin",
    "ECCC pipeline": "Eddy County NM to Culberson County TX, inside the basin",
    "Dude Lateral Project": "lateral inside the basin",
    "WT-0 Compressor Station Project": "Transwestern lateral-to-lateral capacity; no source calls it takeaway",
    "Saguaro - Border Facility": "border crossing of the Saguaro Connector, counted once there",
}

SHEETS = {"hist": "Historical Projects (1996-2024)", "current": "Natural Gas Pipeline Projects"}


def _tracker():
    path, _ = verified(TRACKER)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for key, sn in SHEETS.items():
        rows = list(wb[sn].iter_rows(values_only=True, max_col=25))
        hdr = rows[1]
        assert hdr[16] == "Additional Capacity (MMcf/d)" and hdr[5] == "Completed Date", hdr[:17]
        for r in rows[2:]:
            if r[1]:
                out[(key, r[1])] = dict(zip(hdr, r))
    return out


def _mmcfd(v):
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).split()[0])  # "2800 (total project)"


def entries():
    """The list, in date order. Each entry: name, month, bcfd, status, source, record."""
    t = _tracker()
    out = []
    for p in PROJECTS:
        rec = t[(p["sheet"], p["name"])]
        bcfd = _mmcfd(rec["Additional Capacity (MMcf/d)"]) / 1000
        label = p["name"].strip()
        if "phase" in p:
            label += " " + p["phase"][0]
            bcfd *= p["phase"][1]
        ov = p.get("overlay")
        if ov:
            month, status, source = ov["month"], ov["status"], ov["source"]
        else:
            cd = rec["Completed Date"]
            assert isinstance(cd, dt.datetime), (label, cd)
            assert str(rec["Status"]).strip() == "Completed", (label, rec["Status"])
            month, status = (cd.year, cd.month), "confirmed"
            source = (TRACKER_CITE, None, f"Status Completed, Completed Date {cd.date()}")
        out.append({"name": label, "month": month, "bcfd": bcfd, "status": status, "source": source,
                    "disagrees": (ov or {}).get("disagrees") or p.get("disagrees"),
                    "takeaway_source": p.get("takeaway_source"), "record": rec})
    out.sort(key=lambda e: e["month"])
    return out


if __name__ == "__main__":
    lo, hi = ANCHOR["bcfd"]
    print(f"anchor {ANCHOR['date']}: {lo}-{hi} Bcf/d")
    for e in entries():
        lo += e["bcfd"]
        hi += e["bcfd"]
        print(f"{e['month'][0]}-{e['month'][1]:02d}  {e['bcfd']:5.3f}  {e['status']:9}  {lo:6.2f}-{hi:5.2f}  "
              f"{e['name'][:48]:48}  {e['source'][0]}" + (f"  [disagrees: {e['disagrees']}]" if e["disagrees"] else ""))
