"""LC-1 vs baseline running shoe: cradle-to-grave GHG per pair and per 100 km.

ISO 14040/44 structure (written up in LCA.md):
  goal and scope   compare a mainstream cemented EVA/rubber daily trainer with LC-1,
                   men's US 9, functional unit = one pair per 100 km run;
                   cradle to grave; retail and consumer travel excluded for both.
  inventory        params.py (masses, energy, distances; every row sourced or
                   labelled assumed) + cad/out/volumes.json for both midsoles
                   (same shape) and LC-1's other sole parts.
  impact           GWP100, kg CO2e, fossil GHG only (no biogenic uptake credit).
  interpretation   run.py: deterministic case, scenarios, Monte Carlo, tornado.

Allocation: cut-off. Recycled content carries only its recycling burden; no credit
is given for material sent to recycling or for energy recovered by incineration.
A 50:50 split is run as a sensitivity scenario.

Power scopes. Each process is made at one of three kinds of site:
  t1    final assembly (Tier 1)
  sole  the sole maker (moulding, vulcanising, injection of sole parts)
  t2    every other supplier (yarn spinning, knitting, heel counters, bead foaming)
LC-1 is SPECIFIED with renewable electricity at t1 and sole only; t2 stays on the
grid. Steam for eTPU moulding comes from a natural-gas boiler in every case.
"""
import json
import os

import params as PR

HERE = os.path.dirname(os.path.abspath(__file__))
VOL = os.path.join(HERE, "..", "cad", "out", "volumes.json")
TPU_SOLID_DENSITY = 1200.0  # kg/m3; FormFutura ReForm rTPU 95A datasheet 1.21 g/cm3 (research/w2-07)

STAGES = ["materials", "part_making", "assembly", "packaging", "transport", "end_of_life"]
FIBRES = ("PET_FIBRE", "rPET_FIBRE")


def load_volumes():
    with open(VOL, encoding="utf-8") as f:
        return json.load(f)["volumes_cm3"]


def central():
    x = {}
    for pre, d in (("F.", PR.F), ("E.", PR.E), ("P.", PR.P)):
        for k, v in d.items():
            x[pre + k] = v[0]
    for row in PR.BASELINE:
        x["M.base." + row[0]] = row[3]
    for row in PR.LC1_UPPER:
        x["M.lc1." + row[0]] = row[3]
    x["P.spacer_density"] = PR.SPACER_DENSITY[0]
    return x


def ranges():
    """key -> (low, central, high) for every swept input."""
    out = {}
    for pre, d in (("F.", PR.F), ("E.", PR.E), ("P.", PR.P)):
        for k, v in d.items():
            if v[1] != v[2]:
                out[pre + k] = (v[1], v[0], v[2])
    for row in PR.BASELINE:
        if row[0] != "Midsole":  # its mass follows P.eva_density
            out["M.base." + row[0]] = (row[4], row[3], row[5])
    for row in PR.LC1_UPPER:
        out["M.lc1." + row[0]] = (row[4], row[3], row[5])
    out["P.spacer_density"] = PR.SPACER_DENSITY[1], PR.SPACER_DENSITY[0], PR.SPACER_DENSITY[2]
    for k in ("E.GRID_US", "E.GRID_CN", "E.GRID_ID", "E.GRID_CLEAN", "P.tpu_factor_stress", "P.life_mult_lc1", "P.upper_lives"):
        out.pop(k, None)
    return out


def ef(x, fid):
    if fid == "rTPU_BLEND":
        s = x["P.rtpu_share"]
        return s * x["F.rTPU"] + (1 - s) * x["F.TPU"]
    return x["F." + fid]


def incin(fid):
    return PR.INCIN["TPU" if fid == "rTPU_BLEND" else fid]


def fossil_frac(x, fid, given):
    if fid == "rTPU_BLEND":
        return 1 - x["P.rtpu_share"]
    return given


def lc1_sole_rows(x, vol):
    """LC-1 sole unit, g per shoe, from CAD volume (cm3) x density."""
    dens_t = TPU_SOLID_DENSITY / 1000.0
    return [
        ("Midsole (expanded TPU)", "sole", "TPU", vol["midsole"] * x["P.etpu_density"] / 1000.0, "scrap_etpu", "etpu", 1.0),
        ("Outsole skin (TPU, recycled share)", "sole", "rTPU_BLEND", vol["outsole"] * dens_t, "scrap_mould", "inj_sole", None),
        ("Stitch rim (TPU, recycled share)", "sole", "rTPU_BLEND", vol["rim"] * dens_t, "scrap_mould", "inj_sole", None),
        ("Sockliner (recycled PET spacer)", "sole", "rPET_FIBRE", vol["sockliner"] * x["P.spacer_density"] / 1000.0, "scrap_knit", None, 0.0),
    ]


def rows_for(x, shoe, vol):
    if shoe == "baseline":
        out = []
        for r in PR.BASELINE:
            g = vol["midsole"] * x["P.eva_density"] / 1000.0 if r[0] == "Midsole" else x["M.base." + r[0]]
            out.append((r[0], r[1], r[2], g, r[6], r[7], r[8]))
        return out
    up = [(r[0], r[1], r[2], x["M.lc1." + r[0]], r[6], r[7], r[8]) for r in PR.LC1_UPPER]
    return lc1_sole_rows(x, vol) + up


def process_ghg(x, proc, fid, kg_in, g):
    """kg CO2e for making a part from kg_in of material. g = dict of grid factors
    for 't1', 'sole', 't2'."""
    out = 0.0
    if fid in FIBRES:  # yarn spinning at a textile supplier
        out += x["P.spin_kwh_kg"] * kg_in * g["t2"]
    if proc is None:
        return out
    if proc == "eva_mould":
        return out + x["P.eva_mould_kwh_kg"] * kg_in * g["sole"]
    if proc == "vulc":
        return out + x["P.vulc_kwh_pair"] * g["sole"]  # per PAIR: the energy is given per pair, not per kg
    if proc == "inj_sole":
        return out + x["P.tpu_inj_kwh_kg"] * kg_in * g["sole"]
    if proc == "inj_t2":
        return out + x["P.tpu_inj_kwh_kg"] * kg_in * g["t2"]
    if proc == "knit":
        return out + x["P.knit_kwh_kg"] * kg_in * g["t2"]
    if proc == "etpu":
        bead = x["P.etpu_bead_kwh_kg"] * kg_in * g["t2"]
        kwh = x["P.etpu_mould_kwh_kg"] * kg_in
        st = x["P.etpu_steam_share"]
        mould = (1 - st) * kwh * g["sole"] + st * kwh * 3.6 / x["P.boiler_eff"] * x["E.GAS"]
        return out + bead + mould
    raise KeyError(proc)


def grids(x, clean_t1=False, clean_sole=False, country="E.GRID"):
    c = x["E.GRID_CLEAN"]
    gr = x[country]
    return {"t1": c if clean_t1 else gr, "sole": c if clean_sole else gr, "t2": gr}


def shoe_pair(x, shoe, vol, g, tpu_override=None, cff=False, pack=None):
    """Stage totals (kg CO2e per pair), part breakdown, masses (g per pair)."""
    xx = dict(x)
    if tpu_override is not None:
        xx["F.TPU"] = tpu_override
    if cff:  # 50:50 split of the recycling burden between first and second life
        xx["F.rTPU"] = 0.5 * (xx["F.rTPU"] + xx["F.TPU"])
        xx["F.rPET_FIBRE"] = 0.5 * (xx["F.rPET_FIBRE"] + xx["F.PET_FIBRE"])
    st = dict.fromkeys(STAGES, 0.0)
    parts, parts_mat, mass = {}, {}, dict(product_g=0.0, fossil_virgin_g=0.0, polymer_g=0.0, recycled_g=0.0)
    eol_parts = {}
    for name, module, fid, gr, scrap_key, proc, fos in rows_for(xx, shoe, vol):
        kg = 2 * gr / 1000.0  # pair
        s = xx["P." + scrap_key] if scrap_key else 0.0
        kg_in = kg / (1 - s)
        mat = kg_in * ef(xx, fid)
        mk = process_ghg(xx, proc, fid, kg_in, g)
        st["materials"] += mat
        st["part_making"] += mk
        parts[name] = parts.get(name, 0.0) + mat + mk
        parts_mat[name] = parts_mat.get(name, 0.0) + mat
        ff = fossil_frac(xx, fid, fos)
        mass["product_g"] += 1000 * kg
        mass["fossil_virgin_g"] += 1000 * kg * ff
        mass["polymer_g"] += 1000 * kg
        if fid == "rTPU_BLEND":
            mass["recycled_g"] += 1000 * kg * (1 - ff)
        elif fid.startswith("r"):
            mass["recycled_g"] += 1000 * kg
        e = kg * (xx["P.incin_share"] * incin(fid) + (1 - xx["P.incin_share"]) * xx["P.landfill_kgco2e_kg"])
        st["end_of_life"] += e
        eol_parts[name] = e
    f_asm = 1.0 if shoe == "baseline" else xx["P.noglue_factor"]
    st["assembly"] = f_asm * (xx["P.t1_kwh"] * g["t1"] + xx["P.t1_gas_mj"] * xx["E.GAS"] + xx["P.t1_liq_mj"] * xx["E.LIQ_FUEL"])
    if pack is None:
        pack = PR.BASE_PACK if shoe == "baseline" else PR.LC1_PACK
    pack_kg = sum(p[2] for p in pack) / 1000.0
    st["packaging"] = sum(p[2] / 1000.0 * xx["F." + p[1]] for p in pack)
    t = (mass["product_g"] / 1000.0 + pack_kg) / 1000.0
    st["transport"] = t * (xx["P.ship_km"] * xx["E.SHIP"] + xx["P.truck_km"] * xx["E.TRUCK"])
    return dict(stages=st, total=sum(st.values()), parts=parts, parts_materials=parts_mat, eol_parts=eol_parts,
                mass=mass, pack_g=1000 * pack_kg)


def extra_sole(x, vol, g, tpu_override=None, cff=False):
    """One replacement LC-1 sole unit (pair): sole materials and making, a restitch
    on US grid power (0.3 kWh, assumed), a 60 g paper sleeve, freight, and the
    end of life of the worn sole."""
    xx = dict(x)
    if tpu_override is not None:
        xx["F.TPU"] = tpu_override
    if cff:
        xx["F.rTPU"] = 0.5 * (xx["F.rTPU"] + xx["F.TPU"])
        xx["F.rPET_FIBRE"] = 0.5 * (xx["F.rPET_FIBRE"] + xx["F.PET_FIBRE"])
    tot, kg_sole = 0.0, 0.0
    for name, module, fid, gr, scrap_key, proc, fos in lc1_sole_rows(xx, vol):
        kg = 2 * gr / 1000.0
        s = xx["P." + scrap_key] if scrap_key else 0.0
        kg_in = kg / (1 - s)
        tot += kg_in * ef(xx, fid) + process_ghg(xx, proc, fid, kg_in, g)
        tot += kg * (xx["P.incin_share"] * incin(fid) + (1 - xx["P.incin_share"]) * xx["P.landfill_kgco2e_kg"])
        kg_sole += kg
    tot += 0.3 * xx["E.GRID_US"] + 0.06 * xx["F.PAPERBOARD"]
    tot += (kg_sole + 0.06) / 1000.0 * (xx["P.ship_km"] * xx["E.SHIP"] + xx["P.truck_km"] * xx["E.TRUCK"])
    return tot


def evaluate(x, vol, upper_lives=None, clean_lc1=True, clean_base=False, life_mult=None,
             tpu_override=None, country="E.GRID", cff=False, lc1_pack=None):
    gb = grids(x, clean_base, clean_base, country)
    gl = grids(x, clean_lc1, clean_lc1, country)
    b = shoe_pair(x, "baseline", vol, gb, tpu_override, cff)
    l = shoe_pair(x, "lc1", vol, gl, tpu_override, cff, lc1_pack)
    U = x["P.upper_lives"] if upper_lives is None else upper_lives
    m = x["P.life_mult_lc1"] if life_mult is None else life_mult
    L = x["P.life_km"]
    S = extra_sole(x, vol, gl, tpu_override, cff)
    b100 = 100 * b["total"] / L
    l100 = 100 * (l["total"] + (U - 1) * S) / (U * L * m)
    return dict(baseline=b, lc1=l, extra_sole=S, base_per100=b100, lc1_per100=l100,
                reduction_pct=100 * (1 - l100 / b100))


def cheah_check(x):
    """Not a validation: both inputs are worked back from the paper's own results,
    so this only shows that the IPCC coal factor used here is close to the paper's
    (2.0 kg CO2 per kg coal). 5.0 kWh x 0.88 kg/kWh + 57.5 MJ coal x IPCC factor,
    against the paper's 4.4 + 5.0 = 9.4 kg."""
    elec = 5.0 * 0.88
    coal = 57.5 * x["E.COAL"]
    return dict(electricity=round(elec, 2), coal=round(coal, 2), total=round(elec + coal, 2), paper_total=9.4,
                note="factor check only; not a validation of the model")
