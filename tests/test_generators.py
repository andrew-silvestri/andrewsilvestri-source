"""Every generator is a claim about a shipped file. This runs each one into a
throw-away copy of the repository and diffs what it produced against what is
shipped in site/. Nothing under the real tree is touched.

Why: a generator goes stale silently. rebuild_nav.py carried a nav group five
weeks after the pages dropped it; longevity-app.html and climate-cost-app.html
were edited in place while their template.html was not; skyline-code.zip
shipped a template three palette lines behind site/. Each of those was a
script that would have reverted a deliberate change the next time someone
trusted it. The check is cheap: run it, diff it, every time.

Scope: the text generators (pages, apps, nav, stamps, image dims) and the
download archives. Figure builders are out of scope here - each carries its
own layout audit(), and PNG bytes depend on the matplotlib build.
build_site.py is retired (HANDOFF: never run it; last valid 2026-08-01) and
runs only with --retired, so the report can say what it would do.

Run:
    python tests/test_generators.py             # all live generators
    python tests/test_generators.py --only nav  # one, by label substring
    python tests/test_generators.py --retired   # include build_site.py
    python tests/test_generators.py --keep      # leave the work copies behind
Exit status 1 if any generator drifts from the shipped tree or fails to run.
"""
import argparse
import difflib
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

# The pages carry characters a Windows console's default code page cannot
# print (the nav caret, for one); a diff line must never crash the report.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Directories never copied: version control, caches, the measurement rigs, and
# the raw longevity data (39 MB; build_lq.py reads the merged CSV beside it).
SKIP_DIRS = {".git", "backups", "_deslop", "node_modules", "__pycache__",
             "unpublished", os.path.join("site", "_preview"),
             os.path.join("longevity-quotient", "data", "raw")}
SKIP_PREFIXES = ("_audit-",)


def _ignore(root_rel):
    def ignore(d, names):
        rel = os.path.relpath(d, root_rel)
        rel = "" if rel == "." else rel
        out = set()
        for n in names:
            p = os.path.join(rel, n) if rel else n
            if p in SKIP_DIRS or n in SKIP_DIRS or n.startswith(SKIP_PREFIXES):
                out.add(n)
        return out
    return ignore


# label, argv (relative to the copy), cwd (relative), and what to compare:
#   "site"  - diff the whole site/ tree of the copy against the pristine copy
#   (built, shipped) pairs - a file the generator wrote, and the shipped file
#                           that is supposed to be identical to it
GENERATORS = [
    ("nav: rebuild_nav.py", ["rebuild_nav.py"], ".", "site"),
    ("atlas pages: update_atlas_pages.py --apply",
     ["update_atlas_pages.py", "--apply"], ".", "site"),
    ("longevity page: longevity-quotient/update_page.py --apply",
     ["update_page.py", "--apply"], "longevity-quotient", "site"),
    ("longevity app: longevity-quotient/build_lq.py",
     ["build_lq.py"], "longevity-quotient",
     [("longevity-quotient/longevity.html", "site/longevity-app.html")]),
    ("climate-cost app: climate-cost/lca.py --build",
     ["lca.py", "--build"], "climate-cost",
     [("climate-cost/climate-cost.html", "site/climate-cost-app.html")]),
    ("skyline app: skyline/build_app.py",
     ["build_app.py"], "skyline",
     [("skyline/skyline-app.html", "site/skyline-app.html")]),
    ("downloads: rezip_downloads.py", ["rezip_downloads.py"], ".", "zips"),
    ("thumbnails: build_thumbnails.py", ["build_thumbnails.py"], ".", "site"),
    ("image dims: sync_img_dims.py", ["sync_img_dims.py"], ".", "site"),
    ("cache stamps: bust_cache.py", ["bust_cache.py"], ".", "site"),
]
RETIRED = [
    ("RETIRED build_site.py (never run for real; see HANDOFF)",
     ["build_site.py"], ".", "site"),
]


def read_text(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def unified(a_path, b_path, a_name, b_name, limit):
    if not (a_path.endswith((".html", ".css", ".js", ".md", ".txt", ".csv", ".json", ".py"))):
        return ["  (binary; sizes %d -> %d)" % (os.path.getsize(a_path), os.path.getsize(b_path))]
    lines = list(difflib.unified_diff(read_text(a_path), read_text(b_path),
                                      a_name, b_name, lineterm="", n=0))
    n_changed = sum(1 for l in lines if l[:1] in "+-" and not l.startswith(("+++", "---")))
    head = lines[:limit]
    if len(lines) > limit:
        head.append("  ... %d more diff lines (%d changed lines in all)" % (len(lines) - limit, n_changed))
    return ["  " + l for l in head]


def tree_files(d):
    out = {}
    for root, ds, fs in os.walk(d):
        ds[:] = [x for x in ds if x not in ("downloads",)]
        for f in fs:
            p = os.path.join(root, f)
            out[os.path.relpath(p, d).replace(os.sep, "/")] = p
    return out


def diff_site(pristine, work, limit):
    a, b = tree_files(os.path.join(pristine, "site")), tree_files(os.path.join(work, "site"))
    report = []
    for rel in sorted(set(a) | set(b)):
        if rel not in a:
            report.append("+ site/%s (new file)" % rel)
        elif rel not in b:
            report.append("- site/%s (deleted)" % rel)
        elif not filecmp.cmp(a[rel], b[rel], shallow=False):
            report.append("~ site/%s" % rel)
            report += unified(a[rel], b[rel], "shipped", "generated", limit)
    return report


def zip_members(p):
    with zipfile.ZipFile(p) as z:
        return {i.filename: i.CRC for i in z.infolist()}


def diff_zips(pristine, work):
    a_dir, b_dir = (os.path.join(d, "site", "downloads") for d in (pristine, work))
    report = []
    for name in sorted(set(os.listdir(a_dir)) | set(os.listdir(b_dir))):
        if not name.endswith(".zip"):
            continue
        a, b = os.path.join(a_dir, name), os.path.join(b_dir, name)
        if not os.path.exists(b):
            report.append("- %s (generator did not produce it)" % name); continue
        if not os.path.exists(a):
            report.append("+ %s (not shipped)" % name); continue
        ma, mb = zip_members(a), zip_members(b)
        if ma == mb:
            continue
        report.append("~ site/downloads/%s" % name)
        for m in sorted(set(ma) | set(mb)):
            if m not in mb:
                report.append("    - %s  (shipped, generator drops it)" % m)
            elif m not in ma:
                report.append("    + %s  (generator adds it)" % m)
            elif ma[m] != mb[m]:
                report.append("    ~ %s  (content differs)" % m)
    return report


def run_one(spec, pristine, tmp, limit):
    label, argv, cwd, compare = spec
    work = os.path.join(tmp, "work-" + "".join(c if c.isalnum() else "_" for c in label)[:40])
    shutil.copytree(pristine, work)
    try:
        r = subprocess.run([PY] + argv, cwd=os.path.join(work, cwd),
                           capture_output=True, text=True, timeout=900,
                           encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "FAILED", ["  timed out after 900 s"]
    if r.returncode != 0:
        tail = (r.stderr or r.stdout).strip().splitlines()[-8:]
        return "FAILED", ["  exit %d" % r.returncode] + ["  " + l for l in tail]
    if compare == "site":
        report = diff_site(pristine, work, limit)
    elif compare == "zips":
        report = diff_zips(pristine, work)
    else:
        report = []
        for built, shipped in compare:
            bp, sp = os.path.join(work, built), os.path.join(pristine, shipped)
            if not os.path.exists(bp):
                report.append("  generator did not write %s" % built); continue
            if not filecmp.cmp(bp, sp, shallow=False):
                report.append("~ %s  vs  %s" % (shipped, built))
                report += unified(sp, bp, shipped, built, limit)
    return ("DRIFT" if report else "OK"), report


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="run generators whose label contains this")
    ap.add_argument("--retired", action="store_true", help="also run build_site.py")
    ap.add_argument("--keep", action="store_true", help="keep the work copies")
    ap.add_argument("--lines", type=int, default=14, help="diff lines shown per file")
    args = ap.parse_args()

    specs = GENERATORS + (RETIRED if args.retired else [])
    if args.only:
        specs = [s for s in specs if args.only.lower() in s[0].lower()]

    tmp = tempfile.mkdtemp(prefix="gen-check-")
    pristine = os.path.join(tmp, "pristine")
    print("copying the tree to %s ..." % tmp)
    shutil.copytree(ROOT, pristine, ignore=_ignore(ROOT))

    bad = 0
    try:
        for spec in specs:
            status, report = run_one(spec, pristine, tmp, args.lines)
            bad += status != "OK"
            print("%-6s %s" % (status, spec[0]))
            for line in report:
                print("  " + line)
    finally:
        if args.keep:
            print("work copies kept in", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d generator(s), %d drift or fail" % (len(specs), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
