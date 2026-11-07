"""Midsole material models for the simulated tests.

Every curve is engineering compressive stress (MPa) against engineering strain,
quasi-static, from published data:

  EVA_F1   filled EVA midsole foam, 170 kg/m3 (Aimar et al. 2024, Footwear Science
           16(2):93-103, doi:10.1080/19424280.2024.2317881, Fig. 4a, first cycle,
           4 s^-1, 2 mm specimens; digitised in research/data/foam_curves.csv).
           Peak stress at 80 % strain = sigma_max/rho x rho from Fig. 5a/Table 2.
  ETPU_F3  expanded TPU bead foam, 240 kg/m3, same paper and test.
  LATTICE  printed TPU gyroid, Gibson & Ashby (Cellular Solids, 2nd ed. 1997)
           open-cell elastomer scaling: E* = C1 Es phi^n, elastic-buckling plateau
           0.05 Es phi^2, densification strain 1 - 1.4 phi. Es and the exponents
           are uncertain (research/w2-08-fea-inputs.md section 2): central Es =
           14.5 MPa (FDM TPU 95A, measured), C1 = 1, n = 2.

Impact-rate factor RATE (stress at drop-test rates / Aimar quasi-static), applied
to every foam alike. CALIBRATED: with RATE 1.5 this FE model reproduces Verdejo's
measured first-impact peak, 1.10 kN, for a new EVA trainer heel (171.5 kg/m3,
20 mm, F1614 5 J, 45 mm striker; Verdejo 2004 thesis) within 5 %, and puts the
baseline drop at about 0.9 kN, inside the published F1976 range 809-1,259 N
(research/v-02-fea-check.md). An earlier value of 3.7 came from the ratio of
Verdejo's impact-rate stress to Aimar's quasi-static stress; that ratio already
contains the striker-edge effect the FE models, so it double-counted. The
LC-1/baseline ratio DOES depend on RATE (the curves differ in shape): fea_heel.py
reports it for RATE 1-5.
"""
import numpy as np

RATE = 1.5

# 0.1/0.2 EVA points are F1's own line (0.046/0.098), not the F1/F2 overlap; the
# 0.7 points (EVA 0.613, eTPU 0.466 MPa) come from the same digitiser run
# (research/v-02-fea-check.md finding 8), replacing a straight 0.6-0.8 chord.
_STRAIN = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
_EVA = np.array([0.0, 0.046, 0.098, 0.143, 0.183, 0.237, 0.351, 0.613, 7.164 * 0.17])
_ETPU = np.array([0.0, 0.028, 0.073, 0.109, 0.144, 0.202, 0.295, 0.466, 3.295 * 0.24])

CURVES = {
    "EVA_F1": dict(strain=_STRAIN, stress=_EVA, density=170.0, nu=0.20,
                   label="EVA foam, 170 kg/m3 (Aimar 2024 F1)"),
    "ETPU_F3": dict(strain=_STRAIN, stress=_ETPU, density=240.0, nu=0.25,
                    label="Expanded TPU bead foam, 240 kg/m3 (Aimar 2024 F3)"),
}


def foam_stress(name, eps, density=None, n_dens=2.0, rate=RATE):
    """Stress (MPa) at compressive strain eps (array). Density scaling by
    (rho/rho_ref)^n_dens (Gibson-Ashby, closed-cell foams; n uncertain 1.5-2.5).
    Beyond 0.8 strain the curve continues with the 0.6-0.8 log slope."""
    c = CURVES[name]
    e = np.clip(np.asarray(eps, float), 0.0, 0.92)
    s = np.interp(e, c["strain"], c["stress"])
    hi = e > 0.8
    if np.any(hi):
        k = np.log(c["stress"][-1] / c["stress"][-2]) / 0.1
        s = np.where(hi, c["stress"][-1] * np.exp(k * (e - 0.8)), s)
    if density is not None:
        s = s * (density / c["density"]) ** n_dens
    return s * rate


def lattice_stress(eps, phi, Es=14.5, C1=1.0, n=2.0, rate=RATE):
    """Gibson-Ashby elastomeric open-cell curve: linear to the buckling plateau,
    plateau, then densification sigma = sig_pl / (1 - (eps/eps_D))^1.5 capped."""
    e = np.clip(np.asarray(eps, float), 0.0, 0.95)
    E = C1 * Es * phi ** n
    sig_pl = 0.05 * Es * phi ** 2 * (C1 * phi ** (n - 2) if n != 2 else 1.0)
    eps_y = sig_pl / E
    eps_d = 1.0 - 1.4 * phi
    s = np.where(e < eps_y, E * e, sig_pl)
    dens = e > 0.6 * eps_d
    x = np.clip((e - 0.6 * eps_d) / (0.4 * eps_d), 0, 0.97)
    s = np.where(dens, np.maximum(s, sig_pl / (1 - x) ** 1.5), s)
    return s * rate


def secant_modulus(stress_fn, eps):
    """Secant modulus (MPa) at strain eps; small-strain limit from the first segment."""
    e = np.maximum(np.asarray(eps, float), 0.02)
    return stress_fn(e) / e
