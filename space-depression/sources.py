"""Readers for the space-depression page. Each reads a hash-checked raw file (netfetch.verified), so the flight
counts come out of McDowell's tables, the signal delays out of JPL Horizons, and every figure the page quotes
from a paper or a NASA report is matched in that document's own text (FACTS below) at build time.

rides()          [{days, kind, year, ongoing}] one per person per flight to orbit or beyond (suborbital hops out).
table_date()     the "Updated" line of McDowell's rides table, ISO date.
horizons(name)   [(ISO date or datetime, one-way light time in minutes, Sun-Earth-target angle in degrees)].
flat(name)       a source's text, whitespace collapsed.
quote(name, p)   the match of a regular expression in a source; raises if absent.
facts()          {key: value} for every FACTS row, each matched in its source.
"""
import datetime as dt
import html
import re

import pymupdf

from netfetch import verified

_cache = {}
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def flat(name):
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        else:
            b = p.read_bytes()
            try:
                t = b.decode("utf-8")
            except UnicodeDecodeError:
                t = b.decode("cp1252")
            t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", t, flags=re.S)
            t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        for a, b in (("﻿", ""), ("’", "'"), ("­", ""), ("‑", "-"), ("–", "-"),
                     ("−", "-"), (" ", " ")):
            t = t.replace(a, b)
        _cache[name] = re.sub(r"\s+", " ", t).strip()
    return _cache[name]


def quote(name, pattern):
    m = re.search(pattern, flat(name))
    if not m:
        raise LookupError(f"{name}: no match for {pattern!r}")
    return m


# ------------------------------------------------------------- McDowell ---
def _dur(s):
    """McDowell's duration: days, or d:h:m, or d:h:m:s; a trailing * marks a flight still under way on the
    table's date (its duration runs to that date)."""
    ongoing = s.endswith("*")
    f = [int(x) for x in s.rstrip("*?").strip().split(":")]
    f += [0] * (4 - len(f))
    d, h, m, sec = f
    return d + h / 24 + m / 1440 + sec / 86400, ongoing


def _tsv(name):
    lines = verified(name)[0].read_text(encoding="utf-8").split("\n")
    hdr = [h.strip() for h in lines[0][1:].split("\t")]
    return hdr, lines[1:]


def table_date():
    _, lines = _tsv("mcd_rides.tsv")
    m = re.search(r"# Updated (\d{4}) (\w{3}) +(\d+)", "\n".join(lines[:5]))
    return dt.date(int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))).isoformat()


def rides():
    hdr, lines = _tsv("mcd_rides.tsv")
    out = []
    for ln in lines:
        if ln.startswith("# Chimp"):          # the human section ends here; animals follow
            break
        if ln.startswith("#") or not ln.strip():
            continue
        out.append(dict(zip(hdr, [x.strip() for x in ln.split("\t")])))
    mh, mlines = _tsv("mcd_missions.tsv")
    M = {}
    for ln in mlines:
        if ln.startswith("#") or not ln.strip():
            continue
        r = dict(zip(mh, [x.strip() for x in ln.split("\t")]))
        M[r["HSFID"]] = r
    res = []
    for r in out:
        m = M[r["HSFID"]]
        if m["OrbID"].startswith("SO"):       # suborbital: minutes, not a stay
            continue
        days, ongoing = _dur(r["Duration"])
        kind = "moon" if m["DS"] not in ("", "-", "0") else "orbit"
        res.append({"days": round(days, 3), "kind": kind, "year": int(r["LDate"][:4]), "ongoing": ongoing,
                    "id": r["ID"], "name": r["Name"], "mission": r["Mission"]})
    return res


# -------------------------------------------------------------- Horizons ---
def horizons(name):
    t = verified(name)[0].read_text(encoding="utf-8")
    body = t[t.index("$$SOE") + 5:t.index("$$EOE")]
    out = []
    for ln in body.strip().splitlines():
        c = [x.strip() for x in ln.split(",")]
        # date, solar presence, lunar presence, delta (au), deldot, 1-way LT (min), S-O-T, /r
        d = dt.datetime.strptime(c[0], "%Y-%b-%d %H:%M")
        out.append((d, float(c[5]), float(c[6])))
    return out


# ----------------------------------------------------------------- facts ---
# key: (source, pattern, group or None, type). The value on the page is the matched text, so the page cannot
# carry a figure its source does not print.
FACTS = {
    # NASA Evidence Report and risk record
    "er_isolation": ("bmed_er.txt", r"primarily due to isolation and confinement", None, str),
    "er_iss_rate": ("bmed_er.txt", r"(0\.62) per person-year", 1, float),
    "er_iss_n": ("bmed_er.txt", r"(9) instances", 1, int),
    "rr_leo_short": ("hsrb_rr.pdf", r"Low Earth Orbit Short \(<30 days\) (\dx\d) Accepted", 1, str),
    "rr_leo_long": ("hsrb_rr.pdf", r"Long \(30 days to 1 year\) (\dx\d) Requires Mitigation 2x3 Accepted", 1, str),
    "rr_mars_prep": ("hsrb_rr.pdf", r"Mars Preparatory \(<1 year\) (\dx\d) Requires Mitigation", 1, str),
    "rr_mars_plan": ("hsrb_rr.pdf", r"Planetary \(730-1224 days\) (\dx\d) Requires Mitigation", 1, str),
    "rr_underest": ("hsrb_rr.pdf", r"likely an underestimate", None, str),
    "er_red": ("bmed_er.txt", r"recognized to be a red \(high\) risk", None, str),
    "er_reluct": ("bmed_er.txt", r"because of the astronauts' reluctance to report such symptoms", None, str),
    "er_nodx": ("bmed_er.txt", r"As of (2016), the IMM indicated that no astronaut \w+ \w+ officially diagnosed as having "
                               r"anxiety or depression during flight", 1, int),
    "arch_four": ("arch2025.pdf", r"no less than (four) crew members to the Martian surface", 1, str),
    # Mars-500
    "m500_weeks_pct": ("basner2014.xml", r"symptoms of depression in (93)% of mission weeks", 1, int),
    "m500_ctrl_x": ("basner2014.xml", r"Conflicts with mission control were reported (five) times more often", 1, str),
    "m500_days": ("basner2014.xml", r"(520)-day", 1, int),
    "m500_period": ("basner2013.html", r"(24\.98)", 1, float),
    # Antarctic winter-over (US stations)
    "pal_men": ("palinkas2004.txt", r"with (220) men and (93) women", None, str),
    "pal_any": ("palinkas2004.txt", r"Thirty-nine \((12\.5)%\) crewmembers", 1, float),
    "pal_weighted": ("palinkas2004.txt", r"incidence of DSM-IV disorders was (5\.2)%", 1, float),
    "pal_mood_first": ("palinkas2004.txt", r"Mood disorders were the most common diagnoses", None, str),
    # In-flight mood studies
    "kanas01_us": ("kanas2001.txt", r"completed by (five) U\.S\. astronauts, (eight) Russian cosmonauts", None, str),
    "kanas07_n": ("kanas2007.txt", r"completed weekly by (17) ISS crewmembers", 1, int),
    "barger_iss_h": ("barger2014.html", r"(6\.09) ± 0\.67 hours", 1, float),
    "barger_hyp": ("barger2014.html", r"(75)% of ISS crewmembers \(12/16\) reported using sleep-promoting medications", 1, int),
    # Analogs
    "chapea1": ("chapea.html", r"Mission 1 began (June 25, 2023) and ended (July 6, 2024)", None, str),
    "chapea_four": ("chapea.html", r"Each mission consists of four crew members", None, str),
    "sandal_n": ("sandal2018.html", r"Two crews \( ?N = (27)\) spending approximately (10) months at the Concordia", None, str),
    "hiseas": ("rosenberg2022.html", r"data from (18) subjects who participated in three HI-SEAS missions: (8)-month "
                                     r"HI-SEAS mission 3 \(HM3\), the (12)-month HI-SEAS mission 4", None, str),
    "bell_n": ("bell2019.xml", r"We were able to locate (72) different sources", 1, int),
    "bell_q3": ("bell2019.xml", r"team mood dynamics did not consistently support the third-quarter phenomenon", None, str),
    "sandal_mid": ("sandal2018.html", r"several variables reached a minimum value during the midwinter period, which "
                                      r"corresponded to the third quarter", None, str),
    "sandal_hib": ("sandal2018.html", r"psychological hibernation", None, str),
    # Mission architecture and signal delay
    "dra_short": ("dra5.pdf", r"short-stay missions range from (500) to (650) days", None, str),
    "dra_long": ("dra5.pdf", r"long-stay missions range from (890) to (950) days", None, str),
    "dra_916": ("dra5.pdf", r"TOTAL MISSION (916) days", 1, int),
    "dra_six": ("dra5.pdf", r"crew of six would be sent on each of these missions", None, str),
    "comm_blackout": ("mars_comm.pdf", r"blackouts are inevitable and can last weeks", None, str),
    # Base rate and counter-case
    "nsduh_mde": ("nsduh2025.pdf", r"to (7\.4) percent \(or 19\.7 million people\) in 2025", 1, float),
    "ihle": ("ihle2006.txt", r"anonymous questionnaire to (175) astronauts and cosmonauts.{0,80}?returned by (39) "
                             r"individuals", None, str),
}


def facts():
    out = {}
    for k, (src, pat, g, typ) in FACTS.items():
        m = quote(src, pat)
        if g is None:
            out[k] = list(m.groups()) if m.groups() else m.group(0)
        else:
            out[k] = typ(m.group(g))
    return out
