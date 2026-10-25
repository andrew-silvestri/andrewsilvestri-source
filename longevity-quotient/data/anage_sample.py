"""Write data/anage_sample.csv: AnAge's own sample-size band for each species.

build_lq.effort_check() needs AnAge's "Sample size" field (tiny, small, medium,
large, huge), which ingest.py does not carry into the merged table. The raw
AnAge zip is not in the archive and not in the copies the site's generator
checks build from, so the build reads this small derived file instead and only
this script reads the zip.

Run:  python data/anage_sample.py
"""
import csv
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
z = zipfile.ZipFile(os.path.join(HERE, "raw", "anage_dataset.zip"))
nm = [x for x in z.namelist() if x.lower().endswith(".txt") and "anage" in x.lower()][0]
rows = {}
for r in csv.DictReader(io.StringIO(z.read(nm).decode("utf-8", "replace")), delimiter="\t"):
    rows[" ".join(f"{r['Genus']} {r['Species']}".split())] = r["Sample size"].strip().lower()
with open(os.path.join(HERE, "anage_sample.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["scientific_name", "sample_size"])
    for k in sorted(rows):
        w.writerow([k, rows[k]])
print(f"{len(rows)} AnAge species written to data/anage_sample.csv")
