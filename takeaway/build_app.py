"""Build site/takeaway-app.html: app_template.html with engine.js and the data inlined.

The data is the payload's production record and capacity list and nothing
else: no forecast and no derived series, so the browser recomputes every
number it shows through the same engine the parity test holds to model.py.

Run:  python build_app.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAYLOAD = HERE / "outputs" / "payload.json"
TEMPLATE = HERE / "app_template.html"
ENGINE = HERE / "engine.js"
APP = ROOT / "site" / "takeaway-app.html"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def label(name):
    return name.replace(" (formerly Warrior Pipeline) Phase I & II", "")


def app_data(P):
    """What the page script reads, in the shape engine.scenario takes."""
    entries = []
    for i, e in enumerate(P["entries"]):
        y, m = map(int, e["month"].split("-"))
        entries.append({"key": f"e{i}", "label": label(e["name"]), "month": e["month"], "bcfd": e["bcfd"],
                        "status": e["status"], "when": str(y) if e["year_only"] else f"{MONTHS[m - 1]} {y}"})
    return {"P": P["steo"]["P"], "last": P["steo"]["last_historical"], "until": P["scenario"]["until"],
            "entries": entries, "k_default": P["k"]["default"], "t0": P["t0"],
            "t0_options": sorted([P["t0"]] + P["t0_alt"])}


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
