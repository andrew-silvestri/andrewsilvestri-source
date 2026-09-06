"""Stage 1 feasibility check for NEW_PROJECTS.md section 5 (running economy).

Question: does "improving one term compounds with the others" survive the
published equations?  Two computations, both from named sources:

1. Product versus sum.  Joyner 1991 (J Appl Physiol 70:683) writes marathon
   speed = VO2max x fraction x economy.  With economy as an oxygen cost per
   km (a divisor), equal gains p in each term give (1+p)^2/(1-p) - 1 against
   the additive 3p.

2. Cost-speed curvature.  Kipp, Kram & Hoogkamer 2019 (Front Physiol 10:79,
   PMC6378703), Eq 2: gross VO2 (ml/kg/min) at speed v (m/s) for a 58 kg,
   1.71 m runner at sea level,
       VO2(v) = 0.02724 v^3 + 1.5355 v^2 + 1.5354 v + 15.661
   (Batliner 2018 quadratic plus the Pugh air-resistance cube).  A saving of
   x in metabolic cost lets the runner hold speed v' where
   (1-x) VO2(v') = VO2(v).  The speed gain is less than x because the curve
   is convex.

Writes compound_rows.json and prints the tables.  No design decisions.
"""
import json

MARATHON_M = 42195.0

def vo2_kipp(v):
    return 0.02724 * v**3 + 1.5355 * v**2 + 1.5354 * v + 15.661

def dvo2_kipp(v):
    return 3 * 0.02724 * v**2 + 2 * 1.5355 * v + 1.5354

def solve_speed(target, v0):
    v = v0
    for _ in range(50):
        v -= (vo2_kipp(v) - target) / dvo2_kipp(v)
    return v

def hms(seconds):
    s = int(round(seconds))
    return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"

rows = {"product_vs_sum": [], "kipp_eq2": []}

print("1. Product versus sum, three terms each improved by p")
print(f"{'p':>5} {'product %':>10} {'sum %':>7} {'gap pp':>7} {'3:00 marathon, product':>24} {'sum':>9} {'gap s':>6}")
for p in (0.01, 0.02, 0.03, 0.05):
    prod = (1 + p) ** 2 / (1 - p) - 1
    add = 3 * p
    t0 = 3 * 3600
    t_prod = t0 / (1 + prod)
    t_add = t0 / (1 + add)
    rows["product_vs_sum"].append(dict(p=p, product=prod, sum=add, gap_pp=100 * (prod - add),
                                       t_product_s=t_prod, t_sum_s=t_add))
    print(f"{100*p:>4.0f}% {100*prod:>9.2f}% {100*add:>6.1f}% {100*(prod-add):>7.2f} {hms(t_prod):>24} {hms(t_add):>9} {t_add - t_prod:>6.0f}")

print()
print("2. Kipp 2019 Eq 2: speed gain for a metabolic saving, by baseline pace")
print(f"{'v m/s':>6} {'marathon':>9} {'VO2':>6} {'drag %':>7} {'elast':>6} {'1%':>6} {'3%':>6} {'4%':>6} {'5%':>6}")
for v in (2.60, 3.50, 4.00, 4.50, 5.50, 5.72):
    base = vo2_kipp(v)
    drag = 0.02724 * v**3 / base
    elast = base / (v * dvo2_kipp(v))
    gains = {}
    for x in (0.01, 0.03, 0.04, 0.05):
        v2 = solve_speed(base / (1 - x), v)
        gains[x] = v2 / v - 1
    rows["kipp_eq2"].append(dict(v=v, marathon_s=MARATHON_M / v, vo2=base, drag_share=drag,
                                 elasticity=elast, gain={str(k): g for k, g in gains.items()}))
    print(f"{v:>6.2f} {hms(MARATHON_M / v):>9} {base:>6.1f} {100*drag:>6.1f}% {elast:>6.2f} "
          + " ".join(f"{100*gains[x]:>5.2f}%" for x in (0.01, 0.03, 0.04, 0.05)))

print()
print("3. Check against the paper's stated numbers")
checks = [(2.60, 0.01, 1.17), (5.72, 0.01, 0.65), (5.72, 0.04, 2.64)]
for v, x, stated in checks:
    got = 100 * (solve_speed(vo2_kipp(v) / (1 - x), v) / v - 1)
    print(f"  v={v} saving={100*x:.0f}%  computed {got:.2f}%  paper {stated:.2f}%")
rows["checks"] = [dict(v=v, saving=x, stated=s) for v, x, s in checks]

with open("compound_rows.json", "w") as fh:
    json.dump(rows, fh, indent=1)
