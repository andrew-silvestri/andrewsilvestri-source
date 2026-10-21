"""The battery must never charge and discharge in the same hour.

Until 2026-10-21 model.optimize carried `c + d <= p_max` and a comment saying
it forbade simultaneous charge and discharge. It did not: with twelve hours of
one 720-hour block forced to -$250/MWh, the 2h case charged 0.538 MW and
discharged 0.462 MW at once in ten of them, burning energy for the negative
price. The synthetic year never goes below -$20, so nothing showed it; a real
ERCOT price file (README: drop one at data/prices.csv) would.

    python test_storage.py            # exit 0: no simultaneous hours
    python test_storage.py --break    # puts the old linear constraint back; must exit 1
"""
import sys

import numpy as np
import pulp

import model as M


def old_optimize(prices, duration_h=2, p_max=1.0, rte=0.86, c_deg=2.0):
    """The pre-2026-10-21 formulation, one block, for --break."""
    eta = np.sqrt(rte); E = duration_h * p_max; T = range(len(prices))
    prob = pulp.LpProblem("arb", pulp.LpMaximize)
    c = pulp.LpVariable.dicts("c", T, 0, p_max)
    d = pulp.LpVariable.dicts("d", T, 0, p_max)
    x = pulp.LpVariable.dicts("soc", range(len(prices) + 1), 0, E)
    prob += pulp.lpSum(prices[t] * (d[t] - c[t]) - c_deg * 0.5 * (d[t] + c[t]) for t in T)
    prob += x[0] == 0.5 * E
    for t in T:
        prob += x[t + 1] == x[t] + eta * c[t] - d[t] / eta
        prob += c[t] + d[t] <= p_max
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return dict(ch=np.array([c[t].value() for t in T]), dis=np.array([d[t].value() for t in T]))


def main(brk):
    prices, _ = M.load_prices()
    p = prices[24 * 180: 24 * 210].copy()  # one 720-hour block, July
    p[250:262] = -250.0
    r = old_optimize(p) if brk else M.optimize(p, 2)
    both = int(np.sum((r["ch"] > 1e-6) & (r["dis"] > 1e-6)))
    print(f"{'BREAK (old constraint)' if brk else 'model.optimize'}: "
          f"{both} hour(s) charging and discharging at once")
    return 1 if both else 0


if __name__ == "__main__":
    sys.exit(main("--break" in sys.argv))
