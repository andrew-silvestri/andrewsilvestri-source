# A lower-carbon running shoe: the LC-1 digital prototype

Source for https://andrewsilvestri.com/lowcarbon-shoe.html. Everything here is a
calculation or a simulation from public data; nobody has built or run in an LC-1.

| Path | What it is |
|---|---|
| `DESIGN.md` | The design: concept, bill of materials, assembly, why each choice, weaknesses |
| `BUILD.md` | How to build a test article at home, and cheap physical tests |
| `RESULTS.md` | Scorecard against the targets, what is calculated and what needs a physical test |
| `cad/` | `lc1_cad.py` (CadQuery; `--size` sets the US men's size), `upper_pattern.py`, `render.py`; `out/` holds STEP, STL, the DXF/SVG upper pattern, renders and `volumes.json` |
| `lca/` | The life-cycle model: `params.py` (every input with its source or "assumed"), `lca.py`, `run.py` (scenarios, Monte Carlo, tornado), `LCA.md` (ISO 14040/44 write-up); `results/` |
| `tests/` | Simulated and calculated tests: `fea_heel.py` (axisymmetric finite element model, scikit-fem), `materials.py`, `calc_tests.py`; `results/` |
| `build_lowcarbon_shoe.py` | Builds `outputs/payload.json` from the results and re-runs the LCA as a check |
| `hero.py`, `template.html`, `update_page.py` | The page's figures and generator |
| `test_lowcarbon_shoe.py` | The page's tests (`--break <name>` for each) |

Run, from this folder (Python 3.12; numpy, scipy, matplotlib; for CAD and FEA also
cadquery, scikit-fem, trimesh, ezdxf):

    python cad/lc1_cad.py && python cad/upper_pattern.py && python cad/render.py
    python tests/fea_heel.py && python tests/fea_heel.py lattice && python tests/calc_tests.py
    python lca/run.py
    python build_lowcarbon_shoe.py

The FEA takes several minutes. No licensed data is used. The research trail behind
every input (source documents, extraction scripts) is not in this archive; each
input in `lca/params.py` names its source.
