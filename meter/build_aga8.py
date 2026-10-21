"""Compile the NIST AGA8 reference code in aga8/ into a shared library.

The model calls GERG-2008 (Z, kappa) and the GROSS heating-value routine
through ctypes. The C++ in aga8/ is NIST's, unchanged except line endings
(aga8/NIST_COMMIT.txt); aga8_capi.cpp is the only file written here.

Needs a C++ compiler on PATH (g++; this tree used MinGW-W64 13.2.0).
Writes _build/aga8.dll (Windows) or _build/libaga8.so. Then run
checks/check_z.py, which gates the library against NIST's own test points.

Run:  python build_aga8.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "aga8"
OUT = HERE / "_build" / ("aga8.dll" if sys.platform == "win32" else "libaga8.so")


def main():
    OUT.parent.mkdir(exist_ok=True)
    srcs = [SRC / n for n in ("aga8_capi.cpp", "GERG2008.cpp", "Detail.cpp", "Gross.cpp")]
    cmd = ["g++", "-O2", "-shared", "-I", str(SRC), "-o", str(OUT)] + [str(s) for s in srcs]
    cmd[1:1] = ["-static"] if sys.platform == "win32" else ["-fPIC"]
    print(" ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
