"""The RRC Production Data Query dump, reduced to what the page uses (PLAN 3.5).

The dump (PDQ_DSV.zip, 3.8 GB compressed, 16 "}"-delimited tables) is too big
for this folder and is kept outside it; this script streams two of its tables
and writes one row per district and cycle month:

  vf    LEASE_GAS_DISPCD04_VOL + LEASE_CSGD_DISPCDE04_VOL   OG_LEASE_CYCLE_DISP
        (disposition code 4: vented or flared; the code does not separate them)
  prod  LEASE_GAS_PROD_VOL + LEASE_CSGD_PROD_VOL            OG_LEASE_CYCLE
  dist  DIST_GAS_PROD_VOL, DIST_CSGD_PROD_VOL               OG_DISTRICT_CYCLE

The join the plan asks for is checked here, where the lease rows are: every
disposition row with code-4 gas must have a lease-cycle row on (oil/gas code,
district, lease, cycle month). Misses are written per row (join_misses), so the
test reads them from the file the build reads. All volumes Mcf/month.

Where it came from (Q2, 2026-10-20): the RRC's "Data Sets Available for
Download" page links the dump as https://mft.rrc.texas.gov/link/1f5ddb8d-
329a-4459-b7f8-177b4f5ee60d, a GoAnywhere share; the file downloads by posting
that page's fileList form for the row and then requesting /link/godrivedownload
in the same session. That host refused every connection on 2026-10-18.

Run:  python pdq_dump.py --fetch <path to save PDQ_DSV.zip>   (3.8 GB; then reduces it)
      python pdq_dump.py <path to PDQ_DSV.zip>
Writes data/pdq_district_month.csv and data/pdq_district_month.json (the
dump's size, SHA-1 and extract dates, and the CSV's SHA-1, which
sources.rrc_vented_flared() checks before reading).
"""
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import os
import sys
import zipfile

LINK = "https://mft.rrc.texas.gov/link/1f5ddb8d-329a-4459-b7f8-177b4f5ee60d"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "pdq_district_month.csv")
META = os.path.join(HERE, "data", "pdq_district_month.json")


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows(z, name, want):
    with z.open(name) as f:
        t = io.TextIOWrapper(f, encoding="latin-1", newline="")
        head = t.readline().rstrip("\r\n").split("}")
        idx = [head.index(w) for w in want]       # raises if a column is missing
        for line in t:
            p = line.rstrip("\r\n").split("}")
            yield [p[i] for i in idx]


def fetch(dest, probe=False):
    """The GoAnywhere share as a browser walks it: the link page (session cookie and
    the fileList form's ViewState), the form posted for the one row, then the
    download in the same session. probe: stop after the first 4 bytes and return them."""
    import http.cookiejar
    import re
    import urllib.parse
    import urllib.request
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    page = op.open(LINK, timeout=60).read().decode("utf-8", "replace")
    form = page[page.index('<form id="fileList"'):]
    form = form[:form.index("</form>")]
    vs = re.search(r'name="javax.faces.ViewState"[^>]*value="([^"]+)"', form).group(1)
    row = re.search(r"'(fileTable:0:[\w]+)':'fileTable:0:[\w]+'", form).group(1)
    assert "PDQ_DSV.zip" in form, "the share no longer lists PDQ_DSV.zip"
    data = urllib.parse.urlencode({"fileList": "fileList", "fileList_SUBMIT": "1", "fileTable_selection": "",
                                   row: row, "javax.faces.ViewState": vs}).encode()
    # The post answers 302 to /link/godrivedownload and urllib follows it, so this
    # response IS the 3.8 GB file: read it as a stream, never with a bare .read().
    with op.open(urllib.request.Request("https://mft.rrc.texas.gov/webclient/godrive/PublicGoDrive.xhtml", data),
                 timeout=600) as r:
        assert r.geturl().endswith("/link/godrivedownload"), r.geturl()
        if probe:
            return r.read(4), r.headers.get("Content-Length")
        with open(dest, "wb") as f:
            for blk in iter(lambda: r.read(1 << 20), b""):
                f.write(blk)
    return dest


def main(zp):
    z = zipfile.ZipFile(zp)
    dr = next(rows(z, "GP_DATE_RANGE_CYCLE_DATA_TABLE.dsv",
                   ["OLDEST_PROD_CYCLE_YEAR_MONTH", "NEWEST_PROD_CYCLE_YEAR_MONTH",
                    "GAS_EXTRACT_DATE", "OIL_EXTRACT_DATE"]))
    names = {d: n for d, n in rows(z, "GP_DISTRICT_DATA_TABLE.dsv", ["DISTRICT_NO", "DISTRICT_NAME"])}

    vf = collections.defaultdict(lambda: [0, 0, 0])
    keys, n_disp = set(), 0
    for og, d, lease, ym, g4, c4 in rows(z, "OG_LEASE_CYCLE_DISP_DATA_TABLE.dsv",
            ["OIL_GAS_CODE", "DISTRICT_NO", "LEASE_NO", "CYCLE_YEAR_MONTH",
             "LEASE_GAS_DISPCD04_VOL", "LEASE_CSGD_DISPCDE04_VOL"]):
        n_disp += 1
        g, c = int(g4 or 0), int(c4 or 0)
        if g or c:
            a = vf[(d, ym)]; a[0] += g; a[1] += c; a[2] += 1
            keys.add((og, d, lease, ym))
    n_vf = len(keys)
    prod, n_lease = collections.defaultdict(lambda: [0, 0]), 0
    for og, d, lease, ym, g, c in rows(z, "OG_LEASE_CYCLE_DATA_TABLE.dsv",
            ["OIL_GAS_CODE", "DISTRICT_NO", "LEASE_NO", "CYCLE_YEAR_MONTH",
             "LEASE_GAS_PROD_VOL", "LEASE_CSGD_PROD_VOL"]):
        n_lease += 1
        a = prod[(d, ym)]; a[0] += int(g or 0); a[1] += int(c or 0)
        keys.discard((og, d, lease, ym))
    miss = collections.Counter((k[1], k[3]) for k in keys)
    dist = {(d, ym): (int(g or 0), int(c or 0)) for d, ym, g, c in rows(
        z, "OG_DISTRICT_CYCLE_DATA_TABLE.dsv",
        ["DISTRICT_NO", "CYCLE_YEAR_MONTH", "DIST_GAS_PROD_VOL", "DIST_CSGD_PROD_VOL"])}

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["district_no", "district_name", "cycle_year_month", "vf_gas_mcf", "vf_csgd_mcf",
                    "vf_rows", "prod_gas_mcf", "prod_csgd_mcf", "dist_table_gas_mcf",
                    "dist_table_csgd_mcf", "join_misses"])
        for k in sorted(set(vf) | set(prod) | set(dist)):
            a, b, c = vf.get(k, [0, 0, 0]), prod.get(k, [0, 0]), dist.get(k, ("", ""))
            w.writerow([k[0], names.get(k[0], ""), k[1], a[0], a[1], a[2], b[0], b[1], c[0], c[1],
                        miss.get(k, 0)])
    meta = {"dump": {"file": os.path.basename(zp), "bytes": os.path.getsize(zp), "sha1": sha1(zp),
                     "oldest_prod_cycle": dr[0], "newest_prod_cycle": dr[1],
                     "gas_extract_date": dr[2], "oil_extract_date": dr[3],
                     "url": "https://mft.rrc.texas.gov/link/1f5ddb8d-329a-4459-b7f8-177b4f5ee60d",
                     "downloaded": "2026-10-20"},
            "rows": {"disp": n_disp, "disp_with_vf": n_vf, "lease": n_lease},
            "csv_sha1": sha1(OUT), "written": dt.date.today().isoformat()}
    with open(META, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {OUT}: disp {n_disp:,} rows ({n_vf:,} with code 4), lease {n_lease:,}, "
          f"join misses {sum(miss.values())}; newest production cycle {dr[1]}")


if __name__ == "__main__":
    if sys.argv[1] == "--fetch":
        main(fetch(sys.argv[2]))
    else:
        main(sys.argv[1])
