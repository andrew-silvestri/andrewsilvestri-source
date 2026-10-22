"""Build site/lauf-app.html: app_template.html with engine.js and the data inlined.

The data is the model's defaults and slider limits, and the reported distributions the app sets its
result beside (the latest year's informative reports, and the change into it). The browser computes
the model's side itself, through the engine tests/test_parity_lauf.py holds to model.py.

Run:  python build_app.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAYLOAD = HERE / "outputs" / "payload.json"
TEMPLATE = HERE / "app_template.html"
ENGINE = HERE / "engine.js"
APP = ROOT / "site" / "lauf-app.html"
N_SYSTEMS = 20000     # the browser's sample: quantiles steady to about 0.02 points, fast on a phone
SEED = 20261022


def app_data(P):
    y0, y1 = P["years"]
    obs = {"year": y1, "year_prev": y1 - 1,
           # the change on systems not zero, whole or repeated in either year: all pairs include
           # exact repeats (a change of zero), which pull the middle in (page claims check, finding 3)
           "change": P["persistence"][str(y1)]["change_informative"],
           "level_informative": P["distribution"][str(y1)]["US"]["informative"]}
    return {"defaults": P["model"]["defaults"], "limits": P["model"]["limits"], "observed": obs,
            "n_systems": N_SYSTEMS, "seed": SEED}


def build():
    P = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    t = TEMPLATE.read_text(encoding="utf-8")
    for marker in ("/*ENGINE*/", "/*DATA*/null"):
        assert t.count(marker) == 1, marker
    t = t.replace("/*ENGINE*/", ENGINE.read_text(encoding="utf-8"))
    t = t.replace("/*DATA*/null", json.dumps(app_data(P), sort_keys=True, separators=(",", ":")))
    return t


if __name__ == "__main__":
    out = build()
    old = APP.read_bytes().decode("utf-8") if APP.exists() else None
    with open(APP, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"{APP.name}: " + ("unchanged" if old == out else "written") + f" ({len(out.encode()) / 1024:.0f} KB)")
