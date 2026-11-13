"""
Build outputs/payload.json for the night-shift page from the BLS American Time Use Survey files in data/raw/.

Who is a night worker. The ATUS Leave and Job Flexibilities Module, 2024-25 (lvresp-2425), asked every employed
wage and salary respondent which shift they usually work (LRSCHEDULE: 1 regular daytime, 2 evening, 3 night,
4 rotating, 5 split, 6 irregular, 7 other). Those respondents also kept the ordinary ATUS diary for one day, so
the module can be joined to their diaries (atusact, atuswho) by TUCASEID. This page compares usual night
workers (LRSCHEDULE 3) with usual day workers (LRSCHEDULE 1) and with everyone the ATUS covers (age 15 and up).

Checks that run before anything is written, each against a figure BLS printed (flex-2425.htm, a3-2025.htm):
  - the night share of wage and salary workers, BLS Table 7, 3.4 percent (module weights, LUFINLWGT);
  - the number of night workers, Table 8, 5,144 thousand (weights over 700 person-days: 2024 has 366 days,
    2025 has 334 because no diaries were collected in October 2025);
  - the reasons for night work, Table 8 (preference 30.7, nature of job 19.8, pay 17.5, family 16.5 ...);
  - ATUS Table A-3, 2025: 94.9 percent of people asleep at 3 a.m., 42.5 at 7 a.m., 28.1 working at 10 a.m.
A build that misses any of them stops.

The diary day runs 04:00 to 04:00. A respondent counts as in an activity at clock time t if the activity
starts at or before t and ends after it; that is how Table A-3 counts, and the check above reproduces it.
Standard errors use the 160 replicate weights by successive-difference replication (Fay), as BLS documents:
SE = sqrt(4/160 * sum (theta_r - theta_0)^2).

Run:  python build_nightshift.py
"""
import json
import os
import re
import sys
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "outputs", "payload.json")
STEP = 10                                  # minutes per slot on the clock
SLOTS = 1440 // STEP
DAYS = {2024: 366, 2025: 334}              # diary days each year represents (no October 2025)

SLEEP = lambda c: c // 100 == 101          # 0101xx sleeping (not 0102 sleeplessness)
WORK = lambda c: c // 100 == 501           # 0501xx working, main and other jobs
FAMILY = [20, 22, 23, 24, 25, 26, 40, 51, 52, 53]   # BLS's TRTFAMILY codes (reproduced exactly)
FRIENDS = [54]                                       # TRTFRIEND
REASONS = {1: "family", 2: "pay", 3: "school", 4: "no_other", 5: "nature", 6: "preference", 7: "other"}


def read(zipname, member, usecols=None):
    with zipfile.ZipFile(os.path.join(RAW, zipname)) as z, z.open(member) as h:
        return pd.read_csv(h, usecols=usecols)


def years(kind, usecols=None):
    return pd.concat([read(f"atus{kind}-{y}.zip", f"atus{kind}_{y}.dat", usecols) for y in DAYS],
                     ignore_index=True)


def fay(est, w0, reps):
    t0 = np.asarray(est(w0), dtype=float)
    r = np.array([est(reps[:, i]) for i in range(reps.shape[1])], dtype=float)
    return t0, np.sqrt(4 / 160 * ((r - t0) ** 2).sum(axis=0))


def printed(htm, table_id, label_re, ncols):
    """The row of one BLS HTML table (by its id) whose header cell matches label_re: its first ncols numbers."""
    t = open(os.path.join(RAW, htm), encoding="utf-8", errors="replace").read()
    i = t.find(f'id="{table_id}"')
    if i < 0:
        raise SystemExit(f"{htm}: no table {table_id}")
    t = t[i:t.find("</table>", i)]
    for row in re.findall(r"<tr.*?</tr>", t, flags=re.S):
        th = re.search(r"<th[^>]*>(.*?)</th>", row, flags=re.S)
        if th and re.search(label_re, re.sub(r"<[^>]+>", "", th.group(1)).strip()):
            cells = [re.sub(r"<[^>]+>|,", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)]
            nums = [float(c) for c in cells if re.fullmatch(r"-?\d+(\.\d+)?", c)]
            return nums[:ncols]
    raise SystemExit(f"{htm}: no row matching {label_re!r}")


def occupancy(act, ids, pred):
    """Matrix [case, slot]: 1 if the case is in an activity matching pred at the slot's start."""
    a = act[act.TUCASEID.isin(ids) & pred(act.TRCODE.values)]
    idx = pd.Index(ids)
    M = np.zeros((len(ids), SLOTS), dtype=np.int8)
    rows = idx.get_indexer(a.TUCASEID.values)
    end = a.TUCUMDUR24.values
    start = end - a.TUACTDUR24.values
    for r, s, e in zip(rows, start, end):
        lo = -(-s // STEP)                 # first slot start >= s
        hi = -(-e // STEP)                 # slots with start < e
        if hi > lo:
            M[r, lo:min(hi, SLOTS)] = 1
    return M


def main():
    # ---------------------------------------------------------------- module and weights
    lv = read("lvresp-2425.zip", "lvresp_2425.dat", ["TUCASEID", "LRSCHEDULE", "LEJF_7", "LUFINLWGT"])
    lw = read("lvwgts-2425.zip", "lvwgts_2425.dat")
    lw.columns = [c.upper() for c in lw.columns]
    lv = lv.merge(lw, on="TUCASEID", how="left", validate="1:1")
    REP = [f"LUFINLWGT{i:03d}" for i in range(1, 161)]
    if lv[REP + ["LUFINLWGT"]].isna().any().any():
        raise SystemExit("module respondents without weights")
    yr = (lv.TUCASEID // 10 ** 10).astype(int)
    W = lv.LUFINLWGT.values.astype(float)
    R = lv[REP].values.astype(float)
    sch = lv.LRSCHEDULE.values
    valid = sch > 0

    def share(k):
        return lambda w: (w * ((sch == k) & valid)).sum() / (w * valid).sum() * 100
    night_pct, night_se = fay(share(3), W, R)
    day_pct, _ = fay(share(1), W, R)
    pub7 = printed("flex-2425.htm", "jf_table72025.html", r"^Total, 15 years and over$", 9)
    # columns: total (thousands), daytime, non-daytime, evening, night, rotating, irregular, split, other
    days = sum(DAYS[y] for y in DAYS)
    night_k = (W * (sch == 3)).sum() / days / 1e3
    rs = lv.LEJF_7.values

    def reasons(w):
        m = (sch == 3) & (rs > 0)
        return np.array([(w * m * (rs == k)).sum() / (w * m).sum() * 100 for k in REASONS])
    rs_pct, rs_se = fay(reasons, W, R)
    pub8 = {"preference": 30.7, "nature": 19.8, "pay": 17.5, "family": 16.5, "no_other": 10.8}

    # ---------------------------------------------------------------- diaries
    act = years("act", ["TUCASEID", "TUACTIVITY_N", "TUACTDUR24", "TUCUMDUR24", "TRCODE"])
    who = years("who", ["TUCASEID", "TUACTIVITY_N", "TUWHO_CODE"])
    resp = years("resp", ["TUCASEID", "TUFINLWGT", "TUDIARYDAY", "TRTFAMILY", "TRTFRIEND"])
    summ = years("sum", ["TUCASEID", "TESEX", "TEAGE"])
    if (act.groupby("TUCASEID").TUCUMDUR24.max() != 1440).any():
        raise SystemExit("a diary does not end at 1440 minutes")

    # company: an activity is "with family or friends" if any who-code is family or friend; work is excluded
    fam = who[who.TUWHO_CODE.isin(FAMILY + FRIENDS)][["TUCASEID", "TUACTIVITY_N"]].drop_duplicates()
    act = act.merge(fam.assign(company=1), on=["TUCASEID", "TUACTIVITY_N"], how="left")
    act["company"] = act.company.fillna(0).astype(int)

    # Table A-3 check (2025 alone, everyone 15+, diary weights)
    r25 = resp[resp.TUCASEID // 10 ** 10 == 2025].set_index("TUCASEID").TUFINLWGT
    ids25 = r25.index.values
    a25 = act[act.TUCASEID.isin(ids25)]
    S25 = occupancy(a25, ids25, SLEEP)
    K25 = occupancy(a25, ids25, WORK)
    w25 = r25.values.astype(float)
    slot = lambda h: ((h - 4) % 24) * 60 // STEP
    a3 = {"sleep_03": (w25 * S25[:, slot(3)]).sum() / w25.sum() * 100,
          "sleep_07": (w25 * S25[:, slot(7)]).sum() / w25.sum() * 100,
          "work_10": (w25 * K25[:, slot(10)]).sum() / w25.sum() * 100}
    pubA3 = {"sleep_03": 94.9, "sleep_07": 42.5, "work_10": 28.1}

    # population clock (2024-25 pooled; each year's weights scaled to one average day)
    rr = resp.set_index("TUCASEID")
    y_all = (rr.index.values // 10 ** 10)
    wpop = rr.TUFINLWGT.values / np.array([DAYS[y] for y in y_all])
    ids = rr.index.values
    Sp = occupancy(act, ids, SLEEP)
    Kp = occupancy(act, ids, WORK)
    pop_sleep = (wpop[:, None] * Sp).sum(0) / wpop.sum() * 100
    pop_work = (wpop[:, None] * Kp).sum(0) / wpop.sum() * 100
    pop_free = 100 - pop_sleep - pop_work

    # module respondents by group and by whether the diary day had paid work
    m = lv[["TUCASEID", "LRSCHEDULE"]].copy()
    workmin = act[WORK(act.TRCODE.values)].groupby("TUCASEID").TUACTDUR24.sum()
    sleepmin = act[SLEEP(act.TRCODE.values)].groupby("TUCASEID").TUACTDUR24.sum()
    m["work"] = m.TUCASEID.map(workmin).fillna(0).values
    m["sleep"] = m.TUCASEID.map(sleepmin).fillna(0).values
    m = m.merge(resp[["TUCASEID", "TRTFAMILY", "TRTFRIEND", "TUDIARYDAY"]], on="TUCASEID", how="left")
    m = m.merge(summ, on="TUCASEID", how="left")
    if len(m) != len(lv) or (m.TUCASEID.values != lv.TUCASEID.values).any():
        raise SystemExit("module/diary join changed the row order")
    worked = m.work.values > 0
    S = occupancy(act, m.TUCASEID.values, SLEEP)
    K = occupancy(act, m.TUCASEID.values, WORK)
    C = occupancy(act[act.company == 1], m.TUCASEID.values, lambda c: ~WORK(c))

    groups = {"night_work": (sch == 3) & worked, "night_off": (sch == 3) & ~worked,
              "day_work": (sch == 1) & worked, "day_off": (sch == 1) & ~worked}
    out_groups = {}
    for g, mask in groups.items():
        def mean(col):
            return lambda w: (w * mask * col).sum() / (w * mask).sum()
        sl, sl_se = fay(mean(m.sleep.values), W, R)
        wk, wk_se = fay(mean(m.work.values), W, R)
        fam_, fam_se = fay(mean(m.TRTFAMILY.values), W, R)
        fr, fr_se = fay(mean(m.TRTFRIEND.values), W, R)
        wg = W * mask
        out_groups[g] = {
            "n": int(mask.sum()),
            "sleep_min": round(float(sl), 1), "sleep_se": round(float(sl_se), 1),
            "work_min": round(float(wk), 1), "work_se": round(float(wk_se), 1),
            "family_min": round(float(fam_), 1), "family_se": round(float(fam_se), 1),
            "friends_min": round(float(fr), 1), "friends_se": round(float(fr_se), 1),
            "clock": {
                "sleep": [round(float(x), 1) for x in (wg[:, None] * S).sum(0) / wg.sum() * 100],
                "work": [round(float(x), 1) for x in (wg[:, None] * K).sum(0) / wg.sum() * 100],
                "company": [round(float(x), 1) for x in (wg[:, None] * C).sum(0) / wg.sum() * 100],
            },
        }
        # where the group's sleep falls: the population share awake at the same clock minutes
        sw = (wg[:, None] * S).sum(0)
        out_groups[g]["pop_awake_while_asleep"] = round(float((sw * (100 - pop_sleep)).sum() / sw.sum()), 1)
        kw = (wg[:, None] * K).sum(0)
        out_groups[g]["pop_asleep_while_working"] = round(float((kw * pop_sleep).sum() / kw.sum()), 1) if kw.sum() else None
        ev = [slot(h) for h in (18, 19, 20, 21)]
        busy = np.clip(S + K, 0, 1)[:, ev].mean(1)          # share of 18:00-22:00 slots asleep or working
        out_groups[g]["evening_busy_pct"] = round(float((wg * busy).sum() / wg.sum() * 100), 1)

    # difference in workday sleep, night minus day, with its own replicate SE
    nw, dw = groups["night_work"], groups["day_work"]

    def diff(w):
        return ((w * nw * m.sleep.values).sum() / (w * nw).sum()
                - (w * dw * m.sleep.values).sum() / (w * dw).sum())
    dsl, dsl_se = fay(diff, W, R)

    def diff_fam(w):
        f = m.TRTFAMILY.values + m.TRTFRIEND.values
        return (w * nw * f).sum() / (w * nw).sum() - (w * dw * f).sum() / (w * dw).sum()
    dfa, dfa_se = fay(diff_fam, W, R)

    def diff_fam_off(w):
        f = m.TRTFAMILY.values + m.TRTFRIEND.values
        no, do = groups["night_off"], groups["day_off"]
        return (w * no * f).sum() / (w * no).sum() - (w * do * f).sum() / (w * do).sum()
    dfo, dfo_se = fay(diff_fam_off, W, R)

    # sleep episodes on the clock: runs of sleep slots, the clock read as a circle (the run that ends the
    # diary at 04:00 joins the one that starts it, an approximation: they are different nights)
    def episodes(row):
        if row.all():
            return [SLOTS]
        r = np.roll(row, -int(np.argmin(row)))      # start at an awake slot
        runs, k = [], 0
        for x in r:
            if x:
                k += 1
            elif k:
                runs.append(k)
                k = 0
        if k:
            runs.append(k)
        return runs
    for g, mask in groups.items():
        ep = [episodes(S[i]) if S[i].any() else [0] for i in range(len(m))]
        longest = np.array([max(e) * STEP for e in ep], dtype=float)
        two = np.array([sum(1 for x in e if x * STEP >= 30) >= 2 for e in ep], dtype=float)
        lo, lo_se = fay(lambda w: (w * mask * longest).sum() / (w * mask).sum(), W, R)
        tw, tw_se = fay(lambda w: (w * mask * two).sum() / (w * mask).sum() * 100, W, R)
        out_groups[g].update({"longest_sleep_min": round(float(lo), 1), "longest_sleep_se": round(float(lo_se), 1),
                              "two_sleeps_pct": round(float(tw), 1), "two_sleeps_se": round(float(tw_se), 1)})

    # sex mix of night workers (module weights)
    sex = m.TESEX.values
    men_share = (W * (sch == 3) * (sex == 1)).sum() / (W * (sch == 3)).sum() * 100

    P = {
        "source": "BLS American Time Use Survey 2024 and 2025 microdata, with the Leave and Job Flexibilities "
                  "Module 2024-25",
        "through": "2025-12",
        "slot_min": STEP, "clock_start": "04:00",
        "module": {"n": int(len(lv)), "n_night": int((sch == 3).sum()), "n_day": int((sch == 1).sum()),
                   "night_pct": round(float(night_pct), 2), "night_se": round(float(night_se), 2),
                   "day_pct": round(float(day_pct), 2), "night_thousands": round(float(night_k)),
                   "men_share_night": round(float(men_share), 1),
                   "reasons": {REASONS[k]: round(float(v), 1) for k, v in zip(REASONS, rs_pct)},
                   "reasons_se": {REASONS[k]: round(float(v), 1) for k, v in zip(REASONS, rs_se)}},
        "checks": {"table7_night_printed": pub7, "a3_2025": {k: round(v, 2) for k, v in a3.items()},
                   "a3_printed": pubA3, "table8_printed": pub8},
        "pop": {"sleep": [round(float(x), 1) for x in pop_sleep], "work": [round(float(x), 1) for x in pop_work],
                "free": [round(float(x), 1) for x in pop_free], "n": int(len(ids))},
        "groups": out_groups,
        "diff_sleep_min": round(float(dsl), 1), "diff_sleep_se": round(float(dsl_se), 1),
        "diff_company_min": round(float(dfa), 1), "diff_company_se": round(float(dfa_se), 1),
        "diff_company_off_min": round(float(dfo), 1), "diff_company_off_se": round(float(dfo_se), 1),
    }

    # ---------------------------------------------------------------- checks against printed figures
    bad = []
    if abs(P["module"]["night_pct"] - pub7[4]) > 0.05 or abs(P["module"]["day_pct"] - pub7[1]) > 0.05:
        bad.append(f"night share {P['module']['night_pct']} vs Table 7's {pub7[4]}")
    if abs(days and (W.sum() / days / 1e3) - pub7[0]) > 1:
        bad.append(f"workers {W.sum() / days / 1e3:.0f} thousand vs Table 7's {pub7[0]:.0f}")
    if abs(night_k - 5144) > 1:
        bad.append(f"night workers {night_k:.0f} thousand vs Table 8's 5,144")
    for k, v in pub8.items():
        if abs(P["module"]["reasons"][k] - v) > 0.06:
            bad.append(f"reason {k} {P['module']['reasons'][k]} vs Table 8's {v}")
    for k, v in pubA3.items():
        if abs(a3[k] - v) > 0.06:
            bad.append(f"A-3 {k} {a3[k]:.2f} vs printed {v}")
    if bad:
        raise SystemExit("build does not reproduce BLS's printed figures:\n  " + "\n  ".join(bad))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1)
    for g, d in out_groups.items():
        print(f"  {g:10s} n={d['n']:5d} sleep {d['sleep_min']:6.1f} ({d['sleep_se']}) work {d['work_min']:6.1f} "
              f"family {d['family_min']:6.1f} friends {d['friends_min']:5.1f} pop awake while asleep "
              f"{d['pop_awake_while_asleep']} evening busy {d['evening_busy_pct']}")
    for g, d in out_groups.items():
        print(f"  {g:10s} longest sleep {d['longest_sleep_min']} ({d['longest_sleep_se']}) two+ sleeps "
              f"{d['two_sleeps_pct']}% ({d['two_sleeps_se']})")
    print(f"  days off company night - day {dfo:.1f} (SE {dfo_se:.1f})")
    print(f"  night - day workday sleep {dsl:.1f} min (SE {dsl_se:.1f}); company {dfa:.1f} (SE {dfa_se:.1f})")
    print(f"  checks: night {night_pct:.2f}% ({night_k:.0f}k), A-3 {a3}")
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
