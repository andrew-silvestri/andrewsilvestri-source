"""What measurement alone does to a distribution system's reported LAUF, when nothing is lost.

A system takes gas in through city-gate stations and delivers it through N customer meters. With no
loss, every bit of reported LAUF = (measured in - measured out) / measured out is measurement. The
model draws many such systems, each over two consecutive years, and returns two distributions to set
beside what operators report: the LEVEL across systems in one year, and the CHANGE in a system's figure
from one year to the next. Those are the two things the data can be compared on (plan review,
findings 3 and 4); a share-of-spread or a share-negative is not computed, because neither is defined
against a zero-loss model.

Every error is a relative error on a volume, in percent, split into a part that a system keeps from
year to year (persistent) and a part redrawn each year (transient). Each input is an assumption with
a default, labelled as one on the page and adjustable in the app:

  city gate        standard uncertainty of the station's annual total (%); share of it persistent
  fleet mean       the mean registration error of the customer meter fleet (%), across systems
                   (persistent: a fleet's meters age together); its year-to-year drift (%)
  meter scatter    each customer meter's own error (%): it averages as 1/sqrt(N) and is kept so that
                   a reader can see it vanish (plan review, finding 4)
  temperature      share of customer meters NOT temperature-compensated; mean gas temperature at the
                   meter, deg F, and its year-to-year standard deviation. An uncompensated meter reads
                   actual volume and bills it as if at 60 F, so delivered standard volume is
                   misstated by (T_base/T_gas - 1), T absolute (PHMSA Report to Congress 2017, p. 10:
                   "Some ... volume meters automatically compensate")
  timing           standard deviation of the billing-period mismatch against the 12 months to June 30
                   (%), transient, zero mean

Sign: LAUF = (in - out)/out. An in-meter reading high, or out-meters reading low, raises reported LAUF.

Pure numpy; engine.js is the browser port and test_lauf.py holds the two to each other.
"""
import numpy as np

T_BASE_F = 60.0
DEFAULTS = {
    "n_meters": 2000,            # customer meters in the system
    "cg_u": 0.5,                 # city-gate standard uncertainty, % of annual total
    "cg_persist": 0.5,           # share of city-gate variance that persists year to year
    "fleet_mean_sd": 0.5,        # sd across systems of the fleet's mean customer-meter error, %
    "fleet_drift": 0.2,          # sd of the fleet mean's change from one year to the next, %
    "meter_sd": 1.0,             # each customer meter's own error, sd, %
    "uncomp_share": 0.7,         # share of customer meters without temperature compensation
    "gas_temp_f": 55.0,          # mean gas temperature at the meter over a year, deg F
    "gas_temp_sd_f": 1.5,        # year-to-year sd of that annual mean, deg F
    "timing_sd": 0.5,            # sd of the billing-period mismatch, %, transient
}
LIMITS = {   # the app's slider ranges; the model accepts anything finite
    "n_meters": (50, 200000), "cg_u": (0.0, 2.0), "cg_persist": (0.0, 1.0), "fleet_mean_sd": (0.0, 2.0),
    "fleet_drift": (0.0, 1.0), "meter_sd": (0.0, 3.0), "uncomp_share": (0.0, 1.0),
    "gas_temp_f": (40.0, 75.0), "gas_temp_sd_f": (0.0, 5.0), "timing_sd": (0.0, 2.0),
}


def temp_bias_pct(gas_temp_f):
    """Relative misstatement of delivered standard volume by an uncompensated meter, %.
    Negative when the gas is colder than 60 F: the meter under-registers standard volume."""
    t = (np.asarray(gas_temp_f, float) - 32.0) / 1.8 + 273.15
    tb = (T_BASE_F - 32.0) / 1.8 + 273.15
    # billed (actual) volume V; true standard volume V * tb / t; billed / true - 1 = t / tb - 1
    return 100.0 * (t / tb - 1.0)


def simulate(p, n_systems, rng):
    """LAUF (%) for n_systems systems in year 1 and year 2, measurement only. Returns (y1, y2)."""
    p = {**DEFAULTS, **p}
    n = n_systems
    cg_var = p["cg_u"] ** 2
    cg_p = rng.standard_normal(n) * np.sqrt(cg_var * p["cg_persist"])
    cg_t = rng.standard_normal((2, n)) * np.sqrt(cg_var * (1 - p["cg_persist"]))
    fleet = rng.standard_normal(n) * p["fleet_mean_sd"]
    drift = rng.standard_normal(n) * p["fleet_drift"]
    scatter = rng.standard_normal((2, n)) * p["meter_sd"] / np.sqrt(p["n_meters"])
    temps = p["gas_temp_f"] + rng.standard_normal((2, n)) * p["gas_temp_sd_f"]
    tbias = p["uncomp_share"] * temp_bias_pct(temps)
    timing = rng.standard_normal((2, n)) * p["timing_sd"]
    out = []
    for y in (0, 1):
        e_in = cg_p + cg_t[y]                                    # % error on measured receipts
        e_out = fleet + (drift if y == 1 else 0.0) + scatter[y] + tbias[y] + timing[y]   # % on deliveries
        out.append(100.0 * ((1 + e_in / 100.0) / (1 + e_out / 100.0) - 1.0))
    return out[0], out[1]


def summary(p, n_systems=200000, seed=20261022):
    """Quantiles of the level (year 1) and of the year-to-year change, as the payload stores them."""
    y1, y2 = simulate(p, n_systems, np.random.default_rng(seed))
    q = (10, 25, 50, 75, 90)
    lv = {f"p{k}": float(np.percentile(y1, k)) for k in q}
    ch = {f"p{k}": float(np.percentile(y2 - y1, k)) for k in q}
    return {"level": lv, "change": ch, "level_sd": float(np.std(y1)), "change_sd": float(np.std(y2 - y1)),
            "abs_change_median": float(np.median(np.abs(y2 - y1)))}
