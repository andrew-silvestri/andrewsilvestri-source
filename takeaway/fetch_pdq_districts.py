"""Monthly district totals from the RRC's Production Data Query (PDQ web).

The RRC's Permian workbook (fetch_rrc.py) is said by the RRC to be districts
7C, 08 and 8A. This fetches each of those districts' monthly totals so the
test can check that identity month by month, from files on disk rather than
from the network (test_takeaway.py, check 2).

PDQ web: https://webapps2.rrc.texas.gov/EWA/productionQueryAction.do,
"General Production Query", view District, well type Both, page size View
All. It is a public form; this submits it twice per district, as a reader
would. "View All" returns at most 200 rows (a query for 2008-01..2026 said
"226 results" and listed 200, ending 2024-08), so each district is asked for
in two spans of at most 15 years. The host refuses Python's TLS handshake
and answers curl, so the request goes through curl. Each response is saved
as pdq_<district>_<first year>.html and recorded in data/fetched.json like
any other raw file.

Run:  python fetch_pdq_districts.py
"""
import html
import re
import subprocess
import urllib.parse

from netfetch import RAW, record

BASE = "https://webapps2.rrc.texas.gov"
QUERY = "/EWA/productionQueryAction.do"
DISTRICTS = ("7C", "08", "8A")
SPANS = (("2008", "2022"), ("2023", None))  # None: the latest year the form offers


def _curl(url, jar, data=None):
    cmd = ["curl", "-sSL", "--fail", "-c", jar, "-b", jar, "-A", "Mozilla/5.0", "--max-time", "300", url]
    if data is not None:
        cmd[1:1] = ["--data-binary", "@-"]
    return subprocess.run(cmd, input=data, capture_output=True, check=True).stdout.decode("utf-8", "replace")


def fetch_district(d, y0, y1):
    jar = str(RAW / f"_pdq_{d}.cookies")
    page = _curl(BASE + QUERY, jar)
    action = re.search(r'<form name="generalProductionQueryActionForm" method="post" action="([^"]+)"', page).group(1)
    fields = {html.unescape(k): html.unescape(v)
              for k, v in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', page)}
    for name in re.findall(r'<select name="([^"]+)"', page):
        fields.setdefault(name, "None Selected")
    fields.update({
        "searchArgs.initialViewArg": "District",
        "searchArgs.startMonthArg": "01", "searchArgs.startYearArg": y0,
        "searchArgs.endMonthArg": "12", "searchArgs.endYearArg": y1,
        "searchArgs.leaseTypeArg": "Both",
        "searchArgs.districtCodeArg": d,
        "searchArgs.onShoreCountyCodeArg": "None Selected",
        "pager.pageSize": "-1",
        "methodToCall": "search",
    })
    out = _curl(BASE + action, jar, urllib.parse.urlencode(fields).encode())
    (RAW / f"_pdq_{d}.cookies").unlink(missing_ok=True)
    n = int(re.search(r"(\d+) results", re.sub(r"<[^>]+>", " ", out)).group(1))
    assert n <= 200, f"{d} {y0}-{y1}: {n} results, more than View All returns"
    name = f"pdq_{d}_{y0}.html"
    (RAW / name).write_text(out, encoding="utf-8", newline="\n")
    q = urllib.parse.urlencode({"view": "District", "district": d, "from": f"{y0}-01",
                                "to": f"{y1}-12", "wellType": "Both"})
    return record(name, f"{BASE}{QUERY}?{q}", "curl POST of the PDQ web form")


def latest_option(page_html):
    """Latest year the form offers, so the query asks for everything filed."""
    return max(re.findall(r'<option value="(\d{4})"', page_html))


if __name__ == "__main__":
    probe = _curl(BASE + QUERY, str(RAW / "_pdq_probe.cookies"))
    (RAW / "_pdq_probe.cookies").unlink(missing_ok=True)
    last = latest_option(probe)
    for d in DISTRICTS:
        for y0, y1 in SPANS:
            fetch_district(d, y0, y1 or last)
