"""Assemble the visualiser: template + data + app into one self-contained file."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "data", "skylines.json"),
                      encoding="utf-8"))
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
app = open(os.path.join(HERE, "app.js"), encoding="utf-8").read()
blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
html = tpl.replace("/*APP*/", app).replace(
    "/*DATA*/", json.dumps(blob, ensure_ascii=False))
out = os.path.join(HERE, "skyline-app.html")
open(out, "w", encoding="utf-8").write(html)
print(f"  {out}  ({os.path.getsize(out)/1024:.0f} kB, "
      f"{len(data['cities'])} cities)")
