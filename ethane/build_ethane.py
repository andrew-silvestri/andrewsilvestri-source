"""Build ethane/outputs/payload.json from EIA's files (sources.py), and check it against what EIA printed.

The page is a dated record (D-60, option C): EIA's monthly volumes and EIA's own statements, with no ethane
price series behind it, because none is free to republish. So the only arithmetic here is on EIA's volumes,
and on the few prices EIA printed, converted through EIA's own heat content.

known_answers() reproduces figures EIA printed from the series this page draws, so a misread column, a
shifted month or a different series fails the build rather than reaching the page. The ones that do not
reproduce (2024's "rose 7%", the 2013 "down 9%", the 2022 "25% above the Henry Hub") are left off the
page; see NOTES.

Run:  python build_ethane.py
"""
import datetime as dt
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
START = "2009-01"            # the chart's first month: three years before the rejection EIA dates to late 2012

NOTES = {
    "2024_growth": "TIE 64785 says production 'rose 7%' to 'a record 2.8 million' b/d in 2024; today's series "
                   "gives 8.2% and 2.868 (later revisions, not traced). The page gives today's figures and says the "
                   "year was a record, which still holds for 2024 as written; it does not quote the 7%.",
    "2013_down9": "TIE 12291 says 'net ethane production was down 9% for the first four months in 2013'; field "
                  "production gives -7.9% (EIA's 'net' production is a different measure). Not on the page.",
    "2022_premium": "TIE 53659's paragraph is inconsistent ('ethane prices averaged 80 cents per MMBtu' for "
                    "2021 is a premium, and '$1.36 ... 25% above the Henry Hub' is 22% on the monthly Henry Hub "
                    "average of $6.07). The page quotes neither (plan review 18).",
    "prices": "No ethane price series is free to republish (D-60), and the plan review (5, 6) found that a gap "
              "computed between EIA's quoted ethane prices and a gas price depends on the heat-content "
              "convention and leaves out the costs of recovery, so the page quotes EIA's statements and "
              "computes no price gap.",
}


def ym_range(xs, a, b):
    return [x for x in xs if a <= x <= b]


def mean_of(series, months):
    return st.fmean(series[m] for m in months)


def year_mean(series, y):
    ms = [m for m in series if m.startswith(f"{y}-")]
    if len(ms) != 12:
        raise ValueError(f"{y}: {len(ms)} months")
    return mean_of(series, ms)


def first_ship():
    """TIE 25632 (April 1, 2016): "On March 9, the United States shipped the first waterborne exports of ethane"."""
    m = S.quote("eia_tie_25632.html", r"On (\w+) (\d+), the United States shipped the first waterborne exports of ethane")
    y = S.article("eia_tie_25632.html")[0][:4]
    return dt.datetime.strptime(f"{m.group(1)} {m.group(2)} {y}", "%B %d %Y").date().isoformat()


def build():
    N = S.ngpl()
    for ym, r in N.items():                 # EIA's total is the five products; a column read wrong breaks this
        if ym >= START and abs(r["ngl"] - (r["eth"] + r["pro"] + r["nbu"] + r["ibu"] + r["ngas"])) > 2:
            raise ValueError(f"{ym}: NGL total {r['ngl']} is not the sum of the five products")
    xs = sorted(m for m in N if m >= START)
    last = xs[-1]
    eth = {m: N[m]["eth"] for m in N}
    share = {m: N[m]["eth"] / N[m]["ngl"] for m in N}
    btu = S.ethane_btu()
    gal = btu["mmbtu_per_bbl"] / 42          # million Btu per gallon

    years = range(2009, int(last[:4]))
    pro = {m: N[m]["pro"] for m in N}
    annual = {y: {"eth": year_mean(eth, y), "pro": year_mean(pro, y), "share": year_mean(share, y)} for y in years}

    def per_mmbtu(cents):
        return cents / 100 / gal

    ttm = xs[-12:]                                         # the latest twelve months (plan review 10)
    peak_pre = max((m for m in xs if m <= "2022-03"), key=lambda m: eth[m])
    after = ym_range(xs, "2022-04", "2022-07")          # months EIA had seen when it wrote (2022-08-31)
    rej_lo, rej_hi = 200, 400                              # TIE 16191, read and checked in known_answers()
    e14 = annual[2014]["eth"]      # the year's average: the article does not say which months it had (ledger 57)
    other = {m: N[m]["ngl"] - N[m]["eth"] for m in N}

    P = {
        "through": last,
        "heat": {"mmbtu_per_bbl": btu["mmbtu_per_bbl"], "edition": btu["edition"], "mmbtu_per_gal": gal},
        "hero": {"x": xs,
                 "eth": [round(eth[m]) for m in xs],
                 "pro": [round(N[m]["pro"]) for m in xs],
                 "share": [round(100 * share[m], 2) for m in xs]},
        "annual": {str(y): {"eth": round(v["eth"], 1), "pro": round(v["pro"], 1), "share": round(v["share"], 4)}
                   for y, v in annual.items()},
        "last": {"month": last, "eth": eth[last]},
        "ttm": {"from": ttm[0], "to": ttm[-1], "eth": mean_of(eth, ttm), "pro": mean_of(pro, ttm),
                "other": mean_of(other, ttm), "share": sum(eth[m] for m in ttm) / sum(N[m]["ngl"] for m in ttm)},
        "low_share": min(((y, v["share"]) for y, v in annual.items()), key=lambda t: t[1]),
        "rejection_2014": {"lo": rej_lo, "hi": rej_hi, "recovered": e14,
                           "frac_lo": rej_lo / (e14 + rej_lo), "frac_hi": rej_hi / (e14 + rej_hi)},
        "price_2024_per_mmbtu": per_mmbtu(20),             # a check on EIA's own conversion, not printed
        "peak_2022": {"month": peak_pre, "eth": eth[peak_pre], "min_after": min(eth[m] for m in after)},
        "growth": {"eth": mean_of(eth, ttm) / annual[2015]["eth"],
                   "pro": mean_of(pro, ttm) / year_mean(pro, 2015),
                   "other": mean_of(other, ttm) / year_mean(other, 2015)},
        "share_by_year": {str(y): v["share"] for y, v in annual.items()},
        "articles": {n: S.article(n) for n in sorted(os.listdir(os.path.join(HERE, "data", "raw")))
                     if n.startswith(("eia_tie_", "eia_ngwu_"))},
        "first_ship": first_ship(),
        "notes": NOTES,
    }
    known_answers(P)
    return P


def known_answers(P):
    """Figures EIA printed, reproduced from the series and the articles this page draws on."""
    A = P["annual"]
    q = S.quote
    checks = [
        # TIE 28052 (2016-09-22): "From 2010 to 2015, the ethane share of total NGPL production dropped from 42% to 34%."
        ("ethane share 2010 = 42%, 2015 = 34% (TIE 28052)",
         q("eia_tie_28052.html", r"From 2010 to 2015, the ethane share of total NGPL production dropped from 42% to 34%")
         and round(100 * A["2010"]["share"]) == 42 and round(100 * A["2015"]["share"]) == 34),
        # TIE 25632 (2016-04-01): "Ethane production is expected to increase from 1.1 million barrels per day (b/d) in 2015"
        ("2015 = 1.1 million b/d (TIE 25632)",
         q("eia_tie_25632.html", r"increase from 1\.1 million barrels per day \(b/d\) in 2015")
         and round(A["2015"]["eth"] / 1000, 1) == 1.1),
        # TIE 39712 (2019-06-04): "Ethane production reached 1.71 million b/d in 2018, a 20% increase over 2017 levels."
        ("2018 = 1.71 million b/d, +20% (TIE 39712)",
         q("eia_tie_39712.html", r"Ethane production reached 1\.71 million b/d in 2018, a 20% increase over 2017")
         and round(A["2018"]["eth"] / 1000, 2) == 1.71 and round(100 * (A["2018"]["eth"] / A["2017"]["eth"] - 1)) == 20),
        # TIE 53659 (2022-08-31): "a monthly record of 2.5 million barrels per day (b/d) in March. More than 2.4
        # million b/d of ethane has been produced in the United States every month since then."
        ("March 2022 record 2.5 million b/d, over 2.4 every month after (TIE 53659)",
         q("eia_tie_53659.html", r"monthly record of 2\.5 million barrels per day \(b/d\) in March\. More than 2\.4 million")
         and P["peak_2022"]["month"] == "2022-03" and round(P["peak_2022"]["eth"] / 1000, 1) == 2.5
         and P["peak_2022"]["min_after"] > 2400),
        # TIE 64785 (2025-03-20): "average a record 2.8 million barrels per day (b/d) in 2024"
        ("2024 record 2.8 million b/d (TIE 64785)",
         q("eia_tie_64785.html", r"average a record 2\.8 million barrels per day \(b/d\) in 2024")
         and 2.8 <= A["2024"]["eth"] / 1000 < 2.9     # today's series: 2.868, revised up since (NOTES)
         and A["2024"]["eth"] == max(v["eth"] for y, v in A.items() if y <= "2024")),   # a record when written
        # TIE 64785: "under 20 cents per gallon (gal) for the year (approximately $3 per million British thermal
        # units [MMBtu])": EIA's own conversion, reproduced through MER Table A1's heat content
        ("20 cents a gallon is about $3/MMBtu at MER's heat content (TIE 64785)",
         q("eia_tie_64785.html", r"under 20 cents per gallon \(gal\) for the year \(approximately \$3 per million")
         and round(P["price_2024_per_mmbtu"]) == 3),
        # TIE 44456 (2020-07-22): "an approximate heat content of 2.8 million British thermal units (Btu) per barrel"
        ("ethane about 2.8 million Btu a barrel (TIE 44456, MER A1)",
         q("eia_tie_44456.html", r"approximate heat content of 2\.8 million British thermal units \(Btu\) per barrel")
         and round(P["heat"]["mmbtu_per_bbl"], 1) == 2.8),
        # TIE 16191 (2014-05-08): "Estimates of ethane rejection volumes range between 200 and 400 Mbbl/d."
        ("rejection 200-400 Mbbl/d (TIE 16191)",
         bool(q("eia_tie_16191.html", r"Estimates of ethane rejection volumes range between 200 and 400 Mbbl/d"))),
        # TIE 12291 (2013-07-29): "For the first six months of 2013, ethane prices averaged 27 cents per gallon"
        ("2013 first half 27 cents a gallon (TIE 12291)",
         bool(q("eia_tie_12291.html", r"For the first six months of 2013, ethane prices averaged 27 cents per gallon"))),
        # TIE 64785: "the natural gas price at the Houston Ship Channel averaged $1.86/MMBtu in 2024"
        ("Houston Ship Channel $1.86 in 2024 (TIE 64785)",
         bool(q("eia_tie_64785.html", r"Houston Ship Channel averaged \$1\.86/MMBtu in 2024"))),
        # TIE 53659: "the ethane premium remained steady at $1.36/MMBtu"
        ("first-half 2022 premium $1.36 (TIE 53659)",
         bool(q("eia_tie_53659.html", r"the ethane premium remained steady at \$1\.36/MMBtu"))),
        # NGWU 2019-02-14: within $1.00 of Henry Hub between late 2012 and mid-2017
        ("late 2012 to mid-2017 within $1.00 of Henry Hub (NGWU 2019-02-14)",
         bool(q("eia_ngwu_2019-02-14.html", r"Between late 2012 and mid-2017, ethane spot prices at the Mont Belvieu, "
                                            r"Texas HGL trading hub have been range-bound, staying within \$1\.00 per"))),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(("  ok    " if ok else "  FAIL  ") + n)
    if bad:
        raise SystemExit(f"{len(bad)} known answer(s) not reproduced")
    P["known_answers"] = [n for n, _ in checks]


if __name__ == "__main__":
    P = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1)
        f.write("\n")
    a = P["annual"]
    print(f"through {P['through']}; latest month ethane {P['last']['eth']:.0f} kb/d")
    t = P["ttm"]
    print(f"twelve months {t['from']}..{t['to']}: ethane {t['eth']:.0f}, share {100 * t['share']:.1f}%")
    print("share by year: " + ", ".join(f"{y} {100 * v['share']:.1f}" for y, v in a.items()))
    r = P["rejection_2014"]
    print(f"2014: recovered {r['recovered']:.0f}; left {r['lo']}-{r['hi']} = "
          f"{100 * r['frac_lo']:.1f}-{100 * r['frac_hi']:.1f}% of the ethane")
    g = P["growth"]
    print(f"growth 2015 -> twelve months: ethane x{g['eth']:.2f}, propane x{g['pro']:.2f}, other liquids x{g['other']:.2f}")
