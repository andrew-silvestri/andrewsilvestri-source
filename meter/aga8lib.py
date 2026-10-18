"""ctypes access to the NIST AGA8 reference code built by build_aga8.py.

GERG-2008 for compressibility Z and the isentropic exponent kappa; the GROSS
routine GrossHv for the molar ideal gross heating value. Units: T K, P kPa,
D mol/L, x 21 mole fractions in NIST order (NIST below), HV kJ/mol at
298.15 K, molar mass g/mol.
"""
import ctypes
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DLL = Path(os.environ.get("METER_AGA8_DLL",
                          HERE / "_build" / ("aga8.dll" if sys.platform == "win32" else "libaga8.so")))

# GERG2008.cpp lines 55-75; Detail.cpp and Gross.cpp use the same order.
NIST = ["methane", "nitrogen", "CO2", "ethane", "propane", "ibutane", "butane",
        "ipentane", "pentane", "hexane", "heptane", "octane", "nonane", "decane",
        "hydrogen", "oxygen", "CO", "water", "H2S", "helium", "argon"]
R_GERG = 8.314472   # J/(mol K), GERG2008.cpp:665; Z is defined against this R

_D = ctypes.c_double
_X = _D * 21


class AGA8:
    def __init__(self, path=DLL):
        if not Path(path).exists():
            raise FileNotFoundError(f"{path}: run build_aga8.py first")
        lib = ctypes.CDLL(str(path))
        lib.setup()
        lib.d_gerg.argtypes = [_D, _D, ctypes.POINTER(_D), ctypes.POINTER(_D)]
        lib.d_gerg.restype = ctypes.c_int
        lib.p_gerg.argtypes = [_D, _D, ctypes.POINTER(_D), ctypes.POINTER(_D), ctypes.POINTER(_D)]
        lib.kappa_gerg.argtypes = [_D, _D, ctypes.POINTER(_D), ctypes.POINTER(_D)]
        lib.hv_gross.argtypes = [ctypes.POINTER(_D), ctypes.POINTER(_D)]
        lib.mm_gerg.argtypes = [ctypes.POINTER(_D), ctypes.POINTER(_D)]
        self.lib = lib

    def density(self, T, P_kPa, x):
        D = _D()
        err = self.lib.d_gerg(T, P_kPa, _X(*x), ctypes.byref(D))
        if err:
            raise RuntimeError(f"GERG-2008 density failed (ierr {err}) at {T} K, {P_kPa} kPa")
        return D.value                     # mol/L

    def z(self, T, P_kPa, x):
        return P_kPa / (self.density(T, P_kPa, x) * R_GERG * T)

    def kappa(self, T, P_kPa, x):
        K = _D()
        self.lib.kappa_gerg(T, self.density(T, P_kPa, x), _X(*x), ctypes.byref(K))
        return K.value

    def hv(self, x):
        H = _D()
        self.lib.hv_gross(_X(*x), ctypes.byref(H))
        return H.value                     # kJ/mol, ideal gross, 298.15 K

    def molar_mass(self, x):
        M = _D()
        self.lib.mm_gerg(_X(*x), ctypes.byref(M))
        return M.value                     # g/mol
