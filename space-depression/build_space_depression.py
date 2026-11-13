"""Build outputs/payload.json for the space-depression page from the raw files (through sources.py).

What it computes
- Every person-flight to orbit or beyond from McDowell's rides table (suborbital hops left out): its length in days,
  where it went (Earth orbit, or out to the Moon) and its launch year; counts, person-years and the long tail.
- One-way light time from Earth to Mars, daily 2033-01-01 to 2036-06-30 (JPL Horizons), and to the Moon, hourly
  through 2033: the range of signal delay a crew would live with.
- The ground analogs the hero places on its bottom row, their lengths read from their sources.
- The one calculation the page shows in full: person-years one Mars crew would log against all human time beyond
  low Earth orbit so far.
- facts(): every figure the page quotes from a paper or a NASA report, matched in that document's text.

Gates (the build stops rather than write a payload that fails one)
- the rides table is real and recent: more than 1,400 orbital person-flights, table date in 2026 or later;
- every flight beyond low Earth orbit is under 14 days (the Moon row is short by construction: Apollo and Artemis);
- Mars light time stays inside 3 to 23 minutes and the Moon's inside 1.1 to 1.4 seconds (an order-of-magnitude check
  against the physics: 0.38 to 2.68 au, and 357,000 to 406,000 km);
- Horizons' own light time agrees with range / c to 0.1 percent (trap 30: check one quantity against the world).

Run:  python build_space_depression.py
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S          # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
AU_KM = 149597870.7
C_KM_S = 299792.458
YEAR = 365.25


def fail(msg):
    raise SystemExit("build_space_depression: " + msg)


def flights():
    R = S.rides()
    date = S.table_date()
    if len(R) < 1400 or date < "2026-01-01":
        fail(f"rides table looks wrong: {len(R)} orbital rides, dated {date}")
    moon = [r for r in R if r["kind"] == "moon"]
    if any(r["days"] >= 14 for r in moon):
        fail("a flight beyond low Earth orbit of 14 days or more: check the deep-space flag")
    longest = max(R, key=lambda r: r["days"])
    people = {r["id"] for r in R}
    long180 = [r for r in R if r["days"] > 180]
    long365 = [r for r in R if r["days"] >= 365]
    stats = {
        "table_date": date,
        "n_rides": len(R), "n_orbit": len(R) - len(moon), "n_moon": len(moon),
        "n_people": len(people), "n_people_moon": len({r["id"] for r in moon}),
        "py_total": round(sum(r["days"] for r in R) / YEAR, 2),
        "py_moon": round(sum(r["days"] for r in moon) / YEAR, 3),
        "moon_max_days": round(max(r["days"] for r in moon), 2),
        "n_gt180": len(long180), "n_people_gt180": len({r["id"] for r in long180}),
        "n_ge365": len(long365),
        "longest": {"days": round(longest["days"], 2), "mission": longest["mission"], "year": longest["year"],
                    "name": longest["name"].split(",")[0]},
        "n_ongoing": sum(r["ongoing"] for r in R),
        "share_under_30": round(sum(r["days"] < 30 for r in R) / len(R), 4),
        "first_year": min(r["year"] for r in R),
    }
    dots = sorted([round(r["days"], 2), 1 if r["kind"] == "moon" else 0, r["year"]] for r in R)
    return stats, dots


def delays():
    mars = S.horizons("horizons_mars.txt")
    moon = S.horizons("horizons_moon.txt")
    lo = min(mars, key=lambda x: x[1])
    hi = max(mars, key=lambda x: x[1])
    if not (3 < lo[1] < 4 and 21 < hi[1] < 23):
        fail(f"Mars light time {lo[1]:.2f} to {hi[1]:.2f} min is outside 3-23")
    ms = [x[1] * 60 for x in moon]
    if not (1.1 < min(ms) < 1.25 and 1.3 < max(ms) < 1.4):
        fail(f"Moon light time {min(ms):.3f} to {max(ms):.3f} s is outside 1.1-1.4")
    # light time against range / c, from the same file (column delta, au)
    t = S.verified("horizons_mars.txt")[0].read_text(encoding="utf-8")
    row = t[t.index("$$SOE") + 5:].strip().splitlines()[0].split(",")
    delta_au, lt_min = float(row[3]), float(row[5])
    if abs(delta_au * AU_KM / C_KM_S / 60 / lt_min - 1) > 1e-3:
        fail("Horizons light time does not equal range over the speed of light")
    near = [d for d, _, ang in mars if ang < 2]
    weekly = mars[::7]
    x = [round(d.year + (d.timetuple().tm_yday - 1) / (366 if d.year % 4 == 0 else 365), 4) for d, _, _ in weekly]
    return {
        "mars": {"x": x, "min": [round(v, 2) for _, v, _ in weekly],
                 "lo": {"min": round(lo[1], 2), "date": lo[0].date().isoformat()},
                 "hi": {"min": round(hi[1], 2), "date": hi[0].date().isoformat()},
                 "first": mars[0][0].date().isoformat(), "last": mars[-1][0].date().isoformat(),
                 "sun_lt2_days": len(near),
                 "sun_lt2_first": near[0].date().isoformat() if near else None,
                 "sun_lt2_last": near[-1].date().isoformat() if near else None},
        "moon": {"lo_s": round(min(ms), 2), "hi_s": round(max(ms), 2)},
    }


def analogs(F):
    a, b = (dt.datetime.strptime(s, "%B %d, %Y").date() for s in F["chapea1"])
    sandal_n, sandal_mo = (int(x) for x in F["sandal_n"])
    hs_n, hs_short, hs_long = (int(x) for x in F["hiseas"])
    mo = YEAR / 12
    return [
        # name, days, people, what was measured (short), the finding the hero states
        {"key": "m500", "name": "Mars-500", "days": F["m500_days"], "n": 6, "lo": None,
         "measure": "depression questionnaire, weekly"},
        {"key": "chapea", "name": "CHAPEA 1", "days": (b - a).days + 1, "n": 4, "lo": None,
         "measure": "no mood results published"},
        {"key": "concordia", "name": "Concordia", "days": round(sandal_mo * mo), "n": sandal_n, "lo": None,
         "measure": "positive and negative mood"},
        {"key": "hiseas", "name": "HI-SEAS", "days": round(hs_long * mo), "n": hs_n, "lo": round(hs_short * mo),
         "measure": "stress, not depression"},
    ]


def main():
    F = S.facts()
    stats, dots = flights()
    D = delays()
    crew_dra = 6 if F["dra_six"] else None
    crew_min = {"four": 4}[F["arch_four"]]
    py = {
        "mission_days": F["dra_916"],
        "crew_dra": crew_dra, "crew_min": crew_min,
        "py_dra": round(crew_dra * F["dra_916"] / YEAR, 2),
        "py_min": round(crew_min * F["dra_916"] / YEAR, 2),
    }
    py["x_moon_min"] = round(py["py_min"] / stats["py_moon"], 1)
    py["x_moon_dra"] = round(py["py_dra"] / stats["py_moon"], 1)
    P = {"through": stats["table_date"][:7], "stats": stats, "dots": dots, "delay": D, "analogs": analogs(F),
         "mars_crew": py, "facts": F,
         "fetched": json.load(open(os.path.join(HERE, "data", "fetched.json"), encoding="utf-8"))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True, default=str)
        f.write("\n")
    s = stats
    print(f"{s['n_rides']:,} person-flights ({s['n_orbit']:,} orbit, {s['n_moon']} Moon), {s['n_people']} people, "
          f"{s['py_total']} person-years; beyond LEO {s['py_moon']} person-years, {s['n_people_moon']} people")
    print(f"> 180 d: {s['n_gt180']} flights, {s['n_people_gt180']} people; >= 365 d: {s['n_ge365']}; longest "
          f"{s['longest']}")
    print(f"Mars delay {D['mars']['lo']} to {D['mars']['hi']}; Moon {D['moon']}; angle < 2 deg "
          f"{D['mars']['sun_lt2_days']} d")
    print(f"Mars crew: {py}")


if __name__ == "__main__":
    main()
