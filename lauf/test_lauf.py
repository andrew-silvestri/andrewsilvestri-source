"""The lost-gas page's own failure modes. Each check exists because the fault it names happened while
the page was built, or is the most likely way the page goes wrong without anyone seeing it; each has a
--break that reproduces that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38).

 1. state    Reports are counted by STOP, the state of operation. The first Stage 1 run used
             OFFICE_ADDRESS_STATE and got Texas wrong by 5 to 14 reports a year (all gases). --break state
             counts by the office address again.
 2. eia      EIA Table A1 parses: the recomputed percentage rounds to the printed one in every row,
             2018-2024. The 2022 and 2023 editions print a minus apart from its number, and the
             first parser lost Texas in both. --break eia parses without joining the minus.
 3. model    Known answers: no uncertainty gives exactly zero; a meter's own error averages as
             1/sqrt(N); the temperature bias equals its closed form and has the sign the physics
             gives (cold gas under-registers, raising reported LAUF). --break model inverts the sign.
 4. names    No operator's name appears on the page or in a figure's alt text (packet rule); the
             downloadable table carries them. --break names writes one name into the page text read.
 5. quotes   Every quotation on the page is in its source file. --break quotes alters one.
 6. page     The page equals what update_page.py renders from the payload (no hand edit, no stale
             figure). --break page moves one payload figure.
 7. filter   Only natural gas systems are counted from 2015; propane and the rest are left out and
             counted. --break filter keeps them.

Run:  python test_lauf.py [--break state|eia|model|names|quotes|page|filter]
"""
import csv
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import model as M          # noqa: E402
import sources as S        # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "lauf.html")
CSV = os.path.join(HERE, "outputs", "operator_lauf.csv")
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def page_text():
    t = open(PAGE, encoding="utf-8").read()
    t = re.sub(r"(?is)<(script|style|head|nav)\b.*?</\1>", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    R = S.phmsa_reports()
    # 1 state ------------------------------------------------------------------
    import openpyxl, io, zipfile     # noqa: E401  only for the office-address replay
    y = 2024
    ng = [r for r in R if r["year"] == y and S.natural_gas(r)]
    tx = len({r["operator_id"] for r in ng if r["state"] == "TX"})
    if BREAK == "state":
        path, _ = S.verified(S.ZIP)
        ws = openpyxl.load_workbook(io.BytesIO(zipfile.ZipFile(path).read(f"annual_gas_distribution_{y}.xlsx")),
                                    read_only=True).worksheets[0]
        it = ws.iter_rows(values_only=True)
        for row in it:
            if row and row[0] == "DATAFILE_AS_OF":
                hdr = list(row); break
        rows = [dict(zip(hdr, row)) for row in it if row]
        tx = len({d.get("OPERATOR_ID") for d in rows if d.get("OFFICE_ADDRESS_STATE") == "TX"
                  and isinstance(d.get("PERCENT_UNACC_GAS"), (int, float))
                  and (d.get("COMMODITY") or "").replace("OTHER GAS: ", "") == "Natural Gas"})
    want = P["distribution"][str(y)]["TX"]["all"]["n"]
    check("1 state", tx == want, f"{y} Texas natural gas reports by state of operation {tx}, payload {want}")
    # 2 eia --------------------------------------------------------------------
    bad, n = [], 0
    if BREAK == "eia":
        orig = S._text
        S._text = lambda name: re.sub(r"(?m)^", "", orig(name).replace("-", "- ") if name.endswith(("2022.pdf", "2023.pdf")) else orig(name))
    for yy in range(2018, 2025):
        try:
            rows = S.eia_a1(yy)
        except RuntimeError as e:
            bad.append(str(e)); continue
        for st, v in rows.items():
            n += 1
            if v["printed_pct"] != "<" and f"{round(v['pct'], 1):.1f}" != f"{float(v['printed_pct']):.1f}":
                bad.append(f"{yy} {st} {v['pct']:.2f} vs {v['printed_pct']}")
    if BREAK == "eia":
        S._text = orig
    check("2 eia", not bad and n == 21, f"{n} of 21 rows parsed and round to the printed %" + (f"; {bad[:2]}" if bad else ""))
    # 3 model ------------------------------------------------------------------
    z = {k: 0 for k in M.DEFAULTS}
    z.update(n_meters=100, gas_temp_f=M.T_BASE_F)
    y1, y2 = M.simulate(z, 1000, np.random.default_rng(1))
    zero = float(max(np.abs(y1).max(), np.abs(y2).max()))
    p = dict(z, meter_sd=2.0, n_meters=10000)
    a, _ = M.simulate(p, 200000, np.random.default_rng(2))
    sd, exp = float(a.std()), 2.0 / np.sqrt(10000)
    tb = float(M.temp_bias_pct(50.0))
    closed = 100 * (((50 - 32) / 1.8 + 273.15) / ((60 - 32) / 1.8 + 273.15) - 1)
    if BREAK == "model":
        tb = -tb
    cold = dict(z, uncomp_share=1.0, gas_temp_f=50.0)
    lauf_cold = float(M.simulate(cold, 10, np.random.default_rng(3))[0][0])
    ok3 = zero == 0.0 and abs(sd - exp) / exp < 0.02 and abs(tb - closed) < 1e-12 and tb < 0 and lauf_cold > 0
    check("3 model", ok3, f"no uncertainty -> max |LAUF| {zero}; meter scatter sd {sd:.4f} vs 1/sqrt(N) {exp:.4f}; "
                          f"bias at 50 F {tb:.4f}% (closed form {closed:.4f}); all-cold system reports {lauf_cold:+.3f}%")
    # 4 names ------------------------------------------------------------------
    text = page_text().lower()
    names = {row["operator_name"].strip() for row in csv.DictReader(open(CSV, encoding="utf-8")) if row["operator_name"]}
    if BREAK == "names":
        text += " " + sorted(names, key=len)[-1].lower()
    # names short or generic enough to be ordinary words are not names on a page (a "City of X" is)
    hits = sorted(nm for nm in names if len(nm) > 12 and nm.lower() in text)
    check("4 names", not hits and len(names) > 1000, f"{len(names):,} operator names in the table, {len(hits)} on the page"
                                                     + (f": {hits[:2]}" if hits else ""))
    # 5 quotes -----------------------------------------------------------------
    files = {"report_mix": "report_congress_lauf_2017.pdf", "report_proxy": "report_congress_lauf_2017.pdf",
             "report_meters": "report_congress_lauf_2017.pdf", "partg": "gd_annual_form_cy2018_forward.pdf"}
    missing = []
    for k, f in files.items():
        q = P["quotes"][k][:60]
        if BREAK == "quotes" and k == "report_proxy":
            q = q.replace("not a valid", "a valid")
        src = re.sub(r"\s+", " ", S._text(f))
        if q not in src:
            missing.append(k)
        if q not in page_text() and k != "partg":
            missing.append(k + " (page)")
    check("5 quotes", not missing, f"{len(files)} quotations found in their source files and on the page"
                                   + (f"; missing {missing}" if missing else ""))
    # 6 page -------------------------------------------------------------------
    import update_page as U
    PP = json.loads(json.dumps(P))
    if BREAK == "page":
        PP["reporting"][str(P["years"][1])]["negative"] += 0.01
    t, _ = U.cite(U.render(PP))
    same = t == open(PAGE, "rb").read().decode("utf-8")
    check("6 page", same, "site/lauf.html equals what update_page.py renders from the payload")
    # 7 filter -----------------------------------------------------------------
    keep = S.natural_gas
    if BREAK == "filter":
        S.natural_gas = lambda r: True
    kept = [r for r in R if S.natural_gas(r)]
    S.natural_gas = keep
    other = sum(1 for r in kept if r["year"] >= 2015 and (r["commodity"] or "").replace("OTHER GAS: ", "") != "Natural Gas")
    ok7 = other == 0 and P["excluded_non_natural_gas"] > 0
    check("7 filter", ok7, f"{other} non-natural-gas reports kept from 2015; {P['excluded_non_natural_gas']} left out")
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
