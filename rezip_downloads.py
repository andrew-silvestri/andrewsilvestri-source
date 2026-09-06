"""
Rebuild the download archives that have a source folder in this repo -
atlas, heat, storage, skyline and longevity - and check all eleven
archives in site/downloads/ for things that must never ship.

figstyle.py and both projects' model.py used to exist only inside
site/downloads/heat-code.zip and storage-code.zip - the sibling source
folders sync_assets.py expected were never created, so a change to either
generator meant editing inside a zip. heat/ and storage/ (unpacked from those
same zips, see SITE_REVAMP_2026-08-30.md) are the source of truth now; the
zips are a build artifact of them, not the other way around. This is what
keeps the two in sync: run it after editing anything under a source folder,
before publishing, so the file someone downloads from the site matches the
code that actually produced its figures.

Entry order is preserved from whatever the zip already contains - appending
new files at the end, dropping ones that no longer exist in the source
folder - specifically so that re-running this against an unmodified source
folder reproduces the original zip's namelist() exactly.

What is never shipped: bytecode caches, node_modules, package-manager files,
a built page, and a folder's outputs/ - unless a target says otherwise: the
longevity download keeps its outputs/ data files (the model of record and
its provenance) but not the figures, which are the site's assets. On
2026-09-04 storage-code.zip shipped __pycache__/ and outputs/ (ten files,
443 KB) because a builder had just been run in storage/ and this script
walked the folder as it stood. The rules are now checked against every
archive on every run, and an archive that fails them is not written.

Two sessions running this at once corrupted an archive the same day. A lock
file in site/downloads/ now makes the second run wait its turn or give up,
and each archive is written beside itself and moved into place, so a run
that dies half-way leaves the shipped zip as it was.

Run:
    python3 rezip_downloads.py            # rebuild every generated archive
    python3 rezip_downloads.py --verify   # rebuild each into a temp file and
                                          # diff names and content against
                                          # what is shipped, then scan all
                                          # twelve archives for forbidden
                                          # entries. Writes nothing. Exit 1
                                          # on any difference or any hit.
"""

import argparse
import fnmatch
import os
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, "site", "downloads")
LOCK = os.path.join(DOWNLOADS, ".rezip.lock")
LOCK_WAIT_S = 60          # how long a second run waits for the first
LOCK_STALE_S = 15 * 60    # a lock older than this belongs to a dead run

# Never shipped in a download: package-manager state, bytecode caches, a
# model's own outputs/, and a built page (skyline-app.html is built by
# skyline/build_app.py next to it, longevity.html by build_lq.py; the shipped
# copies are site/skyline-app.html and site/longevity-app.html).
SKIP_DIRS = {"node_modules", "__pycache__", "outputs", ".ipynb_checkpoints"}
SKIP_FILES = {"package.json", "package-lock.json", "skyline-app.html",
              "longevity.html", ".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def target(folder, name, extras=None, keep=(), skip=()):
    """folder: source folder under the repo, or None for an archive assembled
    from named files alone; name: the zip in site/downloads; extras: archive
    name -> path outside the folder (a download whose main file is the
    shipped file itself, or every entry when folder is None); keep: SKIP_DIRS
    this archive may ship; skip: extra path globs, relative to the folder,
    this archive must not."""
    return dict(folder=folder, zip=os.path.join(DOWNLOADS, name),
                extras=extras or {}, keep=frozenset(keep), skip=tuple(skip))


def files_target(name, entries):
    """An archive of named files from around the repo: archive name -> path
    relative to the repo root. For atlas-code.zip, whose sources are the root
    build scripts, the tests and the shipped app, and which had no generator
    until 2026-09-05 - it was cut by hand on 2026-08-29 and still carried
    build_hero.py after that file was deleted."""
    return target(None, name, extras={k: os.path.join(HERE, v) for k, v in entries.items()})


ATLAS_FILES = {
    # the pipeline, in order (HANDOFF section 5)
    "build_atlas_global.py": "build_atlas_global.py",
    "build_atlas.py": "build_atlas.py",
    "build_atlas_space.py": "build_atlas_space.py",
    "build_atlas_brain.py": "build_atlas_brain.py",
    "prune_atlas_edges.py": "prune_atlas_edges.py",
    "build_scenarios.py": "build_scenarios.py",
    "data_climate_indices.py": "data_climate_indices.py",
    # the engine the figures use, and the figures
    "build_throughlines.py": "build_throughlines.py",
    "build_atlas_figures.py": "build_atlas_figures.py",
    "build_model_chart.py": "build_model_chart.py",
    "build_layer_diagram.py": "build_layer_diagram.py",
    "build_hero_figure.py": "build_hero_figure.py",
    "build_propagation_diagram.py": "build_propagation_diagram.py",
    "sitefig.py": "sitefig.py",
    "fig_floor.py": "fig_floor.py",
    "fonts/IBMPlexSans-Regular.otf": "fonts/IBMPlexSans-Regular.otf",
    "fonts/IBMPlexSans-SemiBold.otf": "fonts/IBMPlexSans-SemiBold.otf",
    "fonts/IBMPlexSans-Italic.otf": "fonts/IBMPlexSans-Italic.otf",
    "fonts/IBMPlexMono-Regular.otf": "fonts/IBMPlexMono-Regular.otf",
    "fonts/LICENSE-IBMPlex.txt": "fonts/LICENSE-IBMPlex.txt",
    # the pages' generator and the stamps
    "update_atlas_pages.py": "update_atlas_pages.py",
    "bust_cache.py": "bust_cache.py",
    # the app, as shipped
    "site/atlas-app.html": "site/atlas-app.html",
    "site/assets/atlas-app.js": "site/assets/atlas-app.js",
    # the tests, including the one model.html names
    "tests/test_parity.py": "tests/test_parity.py",
    "tests/parity_engine.js": "tests/parity_engine.js",
    "tests/test_atlas_interaction.js": "tests/test_atlas_interaction.js",
    "tests/probe_scene.js": "tests/probe_scene.js",
    "tests/three-stub.js": "tests/three-stub.js",
    "README.md": "atlas-code-README.md",
}


TARGETS = [
    files_target("atlas-code.zip", ATLAS_FILES),
    target("heat", "heat-code.zip"),
    target("storage", "storage-code.zip"),
    # bookshelf-code.zip retired with its app on 2026-09-05 (PHASE5): the last
    # build is unpublished/downloads/bookshelf-code.zip, its sources bookshelf/
    # and unpublished/bookshelf-app.html.
    # skyline/ was unpacked from its own zip on 2026-09-04 (FIX_SKYLINE): the
    # zip had been the only copy of the generator, and its template had
    # drifted three lines behind site/skyline-app.html.
    target("skyline", "skyline-code.zip"),
    # The longevity download had no generator until 2026-09-04. It ships the
    # model, the data pipeline, the merged table and the outputs/ data files
    # a reader would want to reproduce (lq_table, provenance, summaries) -
    # but not the raw source dumps (39 MB, rebuilt by data/ingest.py from the
    # sources in DATA_SOURCES.md), not the figures (the site's assets), not
    # the built app, not the node state.
    target("longevity-quotient", "longevity-code.zip",
           keep={"outputs"},
           skip=("data/raw", "data/raw/*", "outputs/*.png")),
    # Fat, sugar, salt: the three scripts, the slimmed USDA table and the
    # payload the page is written from; not the 6 MB USDA zip (fetch_data.py
    # re-downloads and hash-checks it), not the figures (the site's assets).
    # Where the ground goes: the readers, the gates, the model, the figures,
    # the committed derived data (the 0.7 MB packed scenario masks and the
    # slim station table) and the payload - everything needed to reproduce
    # every number without re-fetching. Not data/raw: the four fetchers
    # re-download and hash-check it, and the scenario archive alone unpacks
    # to about 400 MB.
    target("continents", "continents-code.zip", keep={"outputs"},
           skip=("data/raw", "data/raw/*", "outputs/*.png")),
    target("food", "food-code.zip", keep={"outputs"},
           skip=("data/raw", "data/raw/*", "outputs/*.png")),
    # Economy is not time: the model, both open cohort tables (CC BY, so they
    # ship and the page can be rebuilt from the archive alone), the payload and
    # the tests. Not the figures, which are the site's assets.
    target("economy", "economy-code.zip", keep={"outputs"},
           skip=("data/raw", "data/raw/*", "outputs/*.png")),
    # What a fast shoe is worth: the declared table of published effect sizes,
    # the build, the figures and the tests. There is no data/ download to
    # exclude - no public dataset carries these numbers, so data/studies.py is
    # itself the data and ships. Not the figures, which are the site's assets.
    target("shoes", "shoes-code.zip", keep={"outputs"},
           skip=("outputs/*.png",)),
    # Studied, not endangered: the scripts, the open inputs and the payload.
    # Not data/raw/ (re-downloaded and hash-checked by the fetch scripts),
    # not the figures, and NOT any file with a Red List category beside a
    # species name - data/iucn_aves.csv and data/birds_joined.csv - because
    # the IUCN Red List terms of use (v3.1, 2024, section 4) prohibit
    # redistributing Red List data in any form; the reader fetches that
    # column with their own token. beauty/test_beauty.py opens the built zip
    # and fails if a category column has crept in.
    #
    # This rule stays HERE rather than inside beauty/, and the difference is
    # not cosmetic. On 2026-09-05 a session that knew nothing about the Red
    # List rebuilt every archive; this target's skip list held anyway,
    # because it sits in the path the archive is built by. In beauty/ it
    # would have protected only a run that went through beauty/'s own
    # tooling. Moving it next to the project it describes reads better and
    # protects less. HANDOFF.md section 8, trap 19.
    target("beauty", "beauty-code.zip", keep={"outputs"},
           skip=("data/raw", "data/raw/*", "data/iucn_aves.csv",
                 "data/birds_joined.csv", "outputs/*.png")),
    # The measured neuron: the scripts, the frozen census, the opened complete
    # set and the three reconstructions the figures draw; not the 1,500 sampled
    # files, which fetch_data.py pulls again.
    target("neuron", "neuron-code.zip", keep={"outputs"},
           skip=("data/_work", "data/_work/*")),
]


def polluted(names, keep=(), skip=()):
    """The entries in names that the rules say must never ship."""
    bad = []
    for n in names:
        rel = n.rstrip("/")
        parts = rel.split("/")
        if any(p in SKIP_DIRS and p not in keep for p in parts) \
                or parts[-1] in SKIP_FILES \
                or parts[-1].endswith(SKIP_SUFFIXES) \
                or any(fnmatch.fnmatch(rel, g) for g in skip):
            bad.append(n)
    return bad


def _all_paths(src_dir, keep=(), skip=()):
    """Every path under src_dir, files and directories, as archive-style
    forward-slash relative names - directories carrying the trailing slash
    a zip uses to mark a directory entry - minus what the rules skip."""
    dirs, files = [], []
    for root, ds, fs in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir).replace(os.sep, "/")
        rel_root = "" if rel_root == "." else rel_root
        ds[:] = sorted(d for d in ds
                       if not polluted([(rel_root + "/" if rel_root else "") + d + "/"], keep, skip))
        if rel_root:
            dirs.append(rel_root + "/")
        for f in sorted(fs):
            rel = (rel_root + "/" if rel_root else "") + f
            if not polluted([rel], keep, skip):
                files.append(rel)
    return dirs, files


def _order(t, src_dir, quiet=False):
    """The entry order for a rebuilt archive: the existing zip's order for
    every name still present, then anything new (directories first, then
    files, each sorted). Names the zip had that the source no longer has are
    dropped with a warning, since silently losing a file out of a shipped
    download is exactly the kind of drift this script exists to prevent -
    unless they are pollution, which is dropped without regret."""
    dirs, files = _all_paths(src_dir, t["keep"], t["skip"]) if src_dir else ([], [])
    all_names = set(dirs) | set(files) | set(t["extras"])
    order = []
    if os.path.exists(t["zip"]):
        with zipfile.ZipFile(t["zip"]) as old:
            for name in old.namelist():
                if name in all_names:
                    order.append(name)
                elif not quiet:
                    why = "never shipped" if polluted([name], t["keep"], t["skip"]) else \
                        (f"no longer in {os.path.basename(src_dir)}/" if src_dir else "no longer listed")
                    print(f"  ! dropping {name!r} from {os.path.basename(t['zip'])} - {why}")
    seen = set(order)
    return order + sorted(n for n in all_names if n not in seen)


def _write(order, src_dir, extras, out_path):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in order:
            if name.endswith("/"):
                z.writestr(zipfile.ZipInfo(name), "")
            else:
                z.write(extras[name] if name in extras else os.path.join(src_dir, name), name)


def rezip(t, src_dir):
    """Rebuild t['zip'] from src_dir. Written beside the target and moved
    into place, so a failure leaves the shipped archive untouched."""
    order = _order(t, src_dir)
    bad = polluted(order, t["keep"], t["skip"])
    if bad:
        raise SystemExit(f"refusing to write {os.path.basename(t['zip'])}: "
                         f"{len(bad)} entries the rules forbid: {bad[:4]}")
    tmp = t["zip"] + ".tmp"
    try:
        _write(order, src_dir, t["extras"], tmp)
        os.replace(tmp, t["zip"])
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return order


def _members(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return [(i.filename, i.CRC) for i in z.infolist()]


def verify(t, src_dir):
    """Build what rezip() would write into a temporary file and compare its
    entry names and content (CRCs) against the shipped archive. The shipped
    archive is read and never written. Returns True when they agree and the
    shipped archive carries nothing the rules forbid."""
    name = os.path.basename(t["zip"])
    if not os.path.exists(t["zip"]):
        print(f"  {name}: MISSING (nothing shipped to verify)")
        return False
    shipped = _members(t["zip"])
    bad = polluted([n for n, _ in shipped], t["keep"], t["skip"])
    order = _order(t, src_dir, quiet=True)
    with tempfile.TemporaryDirectory() as tmp:
        fresh = os.path.join(tmp, name)
        _write(order, src_dir, t["extras"], fresh)
        built = _members(fresh)
    ok = shipped == built and not bad
    print(f"  {name}: {'agrees with source' if ok else 'DIFFERS'} "
          f"({len(shipped)} shipped, {len(built)} from source)")
    if bad:
        print(f"    shipped archive carries {len(bad)} forbidden entries: {bad[:6]}")
    if shipped != built:
        s, b = dict(shipped), dict(built)
        for n in sorted(set(s) | set(b)):
            if n not in b:
                print(f"    - {n}  (shipped, not in source)")
            elif n not in s:
                print(f"    + {n}  (in source, not shipped)")
            elif s[n] != b[n]:
                print(f"    ~ {n}  (content differs)")
        if [n for n, _ in shipped] != [n for n, _ in built] and set(s) == set(b):
            print("    (same names, different order)")
    return ok


def scan_all():
    """Every archive in site/downloads/, generated or not, against the rules
    (a generated one against its own target's allowances). Returns True when
    none carries a forbidden entry."""
    by_zip = {t["zip"]: t for t in TARGETS}
    ok = True
    names = sorted(f for f in os.listdir(DOWNLOADS) if f.endswith(".zip"))
    for f in names:
        p = os.path.join(DOWNLOADS, f)
        t = by_zip.get(p)
        with zipfile.ZipFile(p) as z:
            entries = z.namelist()
        bad = polluted(entries, t["keep"] if t else (), t["skip"] if t else ())
        tag = "generated" if t else "no generator"
        if bad:
            ok = False
            print(f"  {f}: {len(bad)} forbidden of {len(entries)} ({tag}): {bad[:5]}")
        else:
            print(f"  {f}: clean, {len(entries)} entries ({tag})")
    print(f"  {len(names)} archives scanned")
    return ok


class Lock:
    """One rezip at a time per downloads folder. Created with O_EXCL so two
    runs cannot both think they hold it; waits LOCK_WAIT_S for a holder to
    finish; removes a lock older than LOCK_STALE_S as left by a dead run."""

    def __enter__(self):
        os.makedirs(DOWNLOADS, exist_ok=True)
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"{os.getpid()} {time.time():.0f}\n".encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(LOCK)
                except OSError:
                    continue
                if age > LOCK_STALE_S:
                    print(f"  removing stale lock ({age / 60:.0f} min old)")
                    try:
                        os.remove(LOCK)
                    except OSError:
                        pass
                    continue
                if time.time() > deadline:
                    raise SystemExit(f"another rezip_downloads.py holds {LOCK} "
                                     f"({age:.0f} s old); giving up after {LOCK_WAIT_S} s")
                time.sleep(0.5)

    def __exit__(self, *exc):
        try:
            os.remove(LOCK)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="compare a fresh build against the shipped archives "
                         "and scan all twelve, without writing anything")
    args = ap.parse_args()

    ok = True
    with Lock():
        for t in TARGETS:
            src = os.path.join(HERE, t["folder"]) if t["folder"] else None
            if args.verify:
                ok = verify(t, src) and ok
            else:
                names = rezip(t, src)
                print(f"  wrote {os.path.relpath(t['zip'], HERE)}  "
                      f"({len(names)} entries)")
        print()
        ok = scan_all() and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
