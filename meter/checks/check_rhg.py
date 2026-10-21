"""Known-answer check: the orifice discharge coefficient and expansibility from `fluids`.

Two independent comparisons, because one is not enough (HANDOFF trap 16):

1. fluids against the worked examples printed in its own documentation
   (https://fluids.readthedocs.io/fluids.flow_meter.html, opened 2026-10-18):
       C_Reader_Harris_Gallagher(D=0.07391, Do=0.0222, rho=1.165, mu=1.85E-5,
                                 m=0.12, taps='flange')        -> 0.5990326277163659
       orifice_expansibility(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, k=1.4)
                                                               -> 0.9974739057343425
   This pins the installed version to its documented behaviour and nothing more:
   the documentation's numbers were produced by the same code.

2. fluids against the Reader-Harris/Gallagher equation transcribed here from a
   source fluids did not write (Wikipedia, "Orifice plate", the ISO 5167-2 form,
   opened 2026-10-18), over a grid of beta, Reynolds number, pipe size and all
   three tap layouts, inside the ISO 5167-2 range (Re_D >= 5000, beta 0.1-0.75,
   D 50 mm to 1 m). Inside that range fluids' two additions that are not in the
   standard (the max() in the slope term and the (1 + 8 t1) low-Re factor; see
   its source) are inactive, so the two must agree to rounding.

   Found while writing this: fluids' DOCSTRING prints the small-pipe term as
   0.11(0.75 - beta)(2.8 - D/0.0254); its CODE uses 0.011, which is what the
   standard's form carries. The code is right and the docstring is a typo.
   --break reproduces that typo in the transcription, so the check is shown to
   catch exactly the error a reader of fluids' docs would make; it also puts
   the 1989 expansibility constant (0.41) in place of 0.351. Both grid rows
   must fail.

Exits 0 when both agree, 1 otherwise. `--break` must exit 1.
"""
import sys
from math import exp, pi, sqrt

import fluids
from fluids.flow_meter import C_Reader_Harris_Gallagher, orifice_expansibility

BREAK = "--break" in sys.argv
SMALL_PIPE = 0.11 if BREAK else 0.011   # 0.11 is the docstring's typo

DOC_C = 0.5990326277163659
DOC_EPS = 0.9974739057343425
TOL_DOC = 1e-14      # same code, same inputs: only float noise is allowed
TOL_GRID = 1e-12     # two transcriptions of one equation: rounding only


def rhg_iso(D, Do, Re_D, taps):
    """ISO 5167-2 Reader-Harris/Gallagher (1998), as printed in the standard's form."""
    b = Do / D
    if taps == "corner":
        L1 = L2 = 0.0
    elif taps == "flange":
        L1 = L2 = 0.0254 / D
    elif taps == "D":
        L1, L2 = 1.0, 0.47
    A = (19000.0 * b / Re_D) ** 0.8
    M2 = 2.0 * L2 / (1.0 - b)
    C = (0.5961 + 0.0261 * b**2 - 0.216 * b**8
         + 0.000521 * (1e6 * b / Re_D) ** 0.7
         + (0.0188 + 0.0063 * A) * b**3.5 * (1e6 / Re_D) ** 0.3
         + (0.043 + 0.080 * exp(-10 * L1) - 0.123 * exp(-7 * L1)) * (1 - 0.11 * A) * b**4 / (1 - b**4)
         - 0.031 * (M2 - 0.8 * M2**1.1) * b**1.3)
    if D < 0.07112:
        C += SMALL_PIPE * (0.75 - b) * (2.8 - D / 0.0254)
    return C


def eps_iso(b, P1, P2, k):
    return 1 - ((0.41 if BREAK else 0.351) + 0.256 * b**4 + 0.93 * b**8) * (1 - (P2 / P1) ** (1 / k))


def main():
    fails = 0
    print(f"fluids {fluids.__version__}{'  [--break: small-pipe term 0.11, eps constant 0.41]' if BREAK else ''}")

    c = C_Reader_Harris_Gallagher(D=0.07391, Do=0.0222, rho=1.165, mu=1.85E-5, m=0.12, taps="flange")
    e = orifice_expansibility(D=0.0739, Do=0.0222, P1=1E5, P2=9.9E4, k=1.4)
    for name, got, want in (("doc example C", c, DOC_C), ("doc example eps", e, DOC_EPS)):
        ok = abs(got - want) <= TOL_DOC
        fails += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {got!r} vs documented {want!r}")

    # The documented C example also against the independent transcription.
    rho, mu, m, D = 1.165, 1.85E-5, 0.12, 0.07391
    Re = rho * (m / (0.25 * pi * D * D * rho)) * D / mu
    ind = rhg_iso(D, 0.0222, Re, "flange")
    ok = abs(ind - DOC_C) <= TOL_GRID
    fails += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} doc example C, independent transcription: {ind!r} (Re_D {Re:.0f})")

    worst_c = worst_e = 0.0
    n = 0
    mu = 1.1e-5
    for D in (0.0525, 0.0627, 0.1023, 0.2027, 0.3048, 0.5, 0.9):
        for b in (0.10, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75):
            Do = b * D
            if Do < 0.0125:
                continue
            for Re in (5e3, 2e4, 1e5, 1e6, 1e7, 1e8):
                if b > 0.56 and Re < 16000 * b * b:
                    continue
                for taps in ("corner", "flange", "D"):
                    if taps == "flange" and Re < 170000 * b * b * D:
                        continue
                    rho = 50.0
                    mflow = Re * mu * 0.25 * pi * D   # m = Re mu pi D / 4
                    cf = C_Reader_Harris_Gallagher(D, Do, rho, mu, mflow, taps=taps)
                    ci = rhg_iso(D, Do, Re, taps)
                    worst_c = max(worst_c, abs(cf - ci) / ci)
                    for r in (0.8, 0.9, 0.99):
                        for k in (1.2, 1.3, 1.4):
                            ef = orifice_expansibility(D, Do, 5e6, 5e6 * r, k)
                            worst_e = max(worst_e, abs(ef - eps_iso(b, 5e6, 5e6 * r, k)))
                    n += 1
    for name, w in (("grid C, worst relative", worst_c), ("grid eps, worst absolute", worst_e)):
        ok = w <= TOL_GRID
        fails += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {w:.3e} over {n} cases (tolerance {TOL_GRID:g})")

    print(f"{fails} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
