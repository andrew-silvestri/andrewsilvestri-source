"""Everything this project reads, pulled from two public APIs, with hashes.

Three products, in the order they are built:

  data/neurons.csv.gz   one row per reconstruction for the whole of
                        NeuroMorpho.Org - the census the cascade and the app
                        are computed from.  A complete enumeration, not a
                        sample: the API is paged to exhaustion.

  data/swc_metrics.csv  morphometrics computed by swclib from files actually
                        downloaded, for a sample spanning many archives.  The
                        cross-archive spread is the point: with two datasets
                        the reach/thickness relationship is confounded with
                        which dataset a cell came from, and the whole question
                        of whether a gradient exists needs more than two.

  data/complete_metrics.csv
                        the reconstructions that pass all five constraints,
                        opened and measured.  The cascade counts them from
                        the archive's flags; this is what the files hold.

  data/swc/<source>/    the three reconstructions the figures draw, and only
                        those: the two in figure 2, and the one from the
                        complete set that figure 5 draws at three scales.
                        Everything else is discarded after its metrics are
                        taken, because a figure needs a few files and the
                        repository does not need fifteen hundred.

Sources.  NeuroMorpho.Org v8.x, CC BY 4.0, no key: the REST API and the
documented static paths under /dableFiles/.  Its HTML pages must not be
scraped and are not touched here.  Allen Cell Types, free, non-commercial
with an explicit carve-out for journalistic publication with citation: the
Allen Institute API, no key.  Allen is fetched separately because its archive
name on NeuroMorpho contains spaces and the Solr endpoint cannot be queried
for a multiword value.

Run:  python3 fetch_data.py                   # everything, ~1 hour
      python3 fetch_data.py --skip-census     # reuse an existing census
      python3 fetch_data.py --sample 20       # a smaller SWC sample
      python3 fetch_data.py --exemplars-only  # re-choose the two cells figure 2
                                              # draws, from the saved metrics
      python3 fetch_data.py --complete-only   # open the complete set again and
                                              # re-choose the cell figure 5 draws
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import random
import shutil
import ssl
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swclib                                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SWC = os.path.join(DATA, "swc")
NMO = "https://neuromorpho.org/api"
ALLEN = "http://api.brain-map.org/api/v2/data/query.json"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
PAGE = 500
SEED = 1

# Archives sampled for the cross-archive spread.  Chosen for coverage of the
# two axes the question turns on - how far the arbor reaches, and whether the
# radius column varies - not for size.  MouseLight and Peng are the only
# whole-brain sources; the rest are slice or culture preparations.
ARCHIVES = ["MouseLight", "Peng", "Sjostrom", "Tolias", "Markram", "Chiang",
            "Helmstaedter", "Siegert", "Jacobs", "Yang_XW", "Roysam", "Diniz",
            "Baier", "Franca", "Cox", "FlyEM", "Althammer", "Harder",
            "Narkilahti", "Kuddannaya", "Chklovskii", "Nordman"]

# Only the fields anything downstream reads. The API returns 44; carrying all
# of them made the shipped census 7.0 MB against 1.4 MB for these eleven, and
# an archive nobody downloads is not a provenance record.
CENSUS_COLS = ["neuron_id", "archive", "species", "domain", "attributes",
               "physical_integrity", "protocol", "shrinkage_corrected",
               "cell_type", "brain_region", "doi"]


def fetch(url, raw=False, tries=4, timeout=120):
    for k in range(tries):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=timeout, context=CTX)
            b = r.read()
            return b if raw else json.loads(b)
        except Exception as exc:                                  # noqa: BLE001
            if k == tries - 1:
                return None
            time.sleep(2 * (k + 1))
    return None


# ----------------------------------------------------------------- census ---

def census(path):
    """Page the whole archive.  Complete enumeration, not a sample."""
    allq = quote("neuron_id:[* TO *]", safe=":")
    first = fetch("%s/neuron/select?size=%d&page=0&q=%s" % (NMO, PAGE, allq))
    if not first:
        raise SystemExit("NeuroMorpho census: the API did not answer")
    total, pages = first["page"]["totalElements"], first["page"]["totalPages"]
    print("  census: %d reconstructions in %d pages" % (total, pages))
    t0 = time.time()
    rows = []
    for i in range(pages):
        d = first if i == 0 else fetch("%s/neuron/select?size=%d&page=%d&q=%s" % (NMO, PAGE, i, allq))
        if not d or "_embedded" not in d:
            raise SystemExit("census: page %d failed; refusing to write a partial census" % i)
        for n in d["_embedded"]["neuronResources"]:
            doi = n.get("reference_doi") or []
            rows.append([n.get("neuron_id"), n.get("archive"), n.get("species"),
                         n.get("domain"), n.get("attributes"),
                         n.get("physical_Integrity"), n.get("protocol"),
                         n.get("shrinkage_corrected"),
                         "|".join(n.get("cell_type") or []),
                         "|".join(n.get("brain_region") or []), doi[0] if doi else ""])
        if (i + 1) % 100 == 0:
            print("    page %d/%d  %d rows  %.0fs" % (i + 1, pages, len(rows), time.time() - t0))
    if len(rows) != total:
        raise SystemExit("census: got %d rows for %d expected" % (len(rows), total))
    write_census(path, rows)
    print("  census: %d rows -> %s" % (len(rows), os.path.basename(path)))
    return total


def write_census(path, rows):
    """Write the census, and read it back before trusting it.

    mtime=0 so two runs over the same archive state give the same bytes, and
    the hash in manifest.json means the census rather than the clock.

    The read-back is not ceremony. The first version of this nested a
    TextIOWrapper inside a GzipFile context; the GzipFile closed first, the
    wrapper never flushed its last buffer, and eleven rows of 298,339 went
    missing - a 0.004% loss that changed four of the five cascade counts by
    one and would have been invisible in every figure on the page.
    """
    import io
    with open(path, "wb") as raw:
        gz = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0)
        txt = io.TextIOWrapper(gz, encoding="utf-8", newline="")
        w = csv.writer(txt)
        w.writerow(CENSUS_COLS)
        w.writerows(rows)
        txt.flush()
        txt.detach()
        gz.close()
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        back = sum(1 for _ in csv.DictReader(fh))
    if back != len(rows):
        raise SystemExit("census: wrote %d rows but read back %d" % (len(rows), back))
    return path


# ------------------------------------------------------------ swc sample ---

def nmo_slug(archive):
    return archive.lower().replace(" ", "_")


def swc_url(archive, name):
    return "%s/dableFiles/%s/CNG%%20version/%s.CNG.swc" % (
        "https://neuromorpho.org", nmo_slug(archive), quote(name))


def sample_nmo(per_archive, workdir):
    """Download a spread of reconstructions and take their metrics."""
    rng = random.Random(SEED)
    out = []
    for arch in ARCHIVES:
        d = fetch("%s/neuron/select?size=%d&page=0&q=%s"
                  % (NMO, PAGE, quote("archive:%s" % arch, safe=":")))
        if not d or "_embedded" not in d:
            print("    %-14s no records" % arch)
            continue
        recs = [r for r in d["_embedded"]["neuronResources"]
                if ", 3D," in (r.get("attributes") or "")]
        rng.shuffle(recs)
        got = 0
        for r in recs:
            if got >= per_archive:
                break
            name = r["neuron_name"]
            body = fetch(swc_url(arch, name), raw=True)
            if not body or len(body) < 200:
                continue
            p = os.path.join(workdir, "%s__%s.swc" % (nmo_slug(arch), name.replace("/", "_")))
            with open(p, "wb") as fh:
                fh.write(body)
            try:
                m = swclib.metrics(p, source=nmo_slug(arch))
            except Exception:                                     # noqa: BLE001
                os.remove(p)
                continue
            m["archive"] = arch
            m["neuron_name"] = name
            m["neuron_id"] = r.get("neuron_id")
            m["whole_brain"] = nmo_slug(arch) in swclib.Z_TRUSTWORTHY
            m["nmo_attributes"] = r.get("attributes")
            m["nmo_domain"] = r.get("domain")
            m["species"] = r.get("species")
            out.append(m)
            got += 1
        print("    %-14s %3d cells" % (arch, got))
    return out


def allen_swc(specimen_id):
    """The reconstruction file for one Allen specimen, by specimen id."""
    d = fetch(ALLEN + "?criteria=model::NeuronReconstruction,rma::criteria,"
              "[specimen_id$eq%d],rma::include,well_known_files" % specimen_id)
    if not d or not d.get("msg"):
        return None
    for r in d["msg"]:
        if r.get("superseded"):
            continue
        for f in r.get("well_known_files", []):
            if f.get("well_known_file_type_id") == 303941301:
                return fetch("http://api.brain-map.org" + f["download_link"], raw=True)
    return None


def sample_allen(limit, workdir):
    """Allen Cell Types, from the Allen API: SWC file type 303941301."""
    rows, start = [], 0
    while True:
        d = fetch(ALLEN + "?criteria=model::ApiCellTypesSpecimenDetail,rma::criteria,"
                  "[nr__reconstruction_type$ne'null'],rma::options"
                  "[num_rows$eq200][start_row$eq%d]" % start)
        if not d:
            break
        rows += d["msg"]
        if len(rows) >= d["total_rows"]:
            break
        start += 200
    rec, start = [], 0
    while True:
        d = fetch(ALLEN + "?criteria=model::NeuronReconstruction,rma::include,"
                  "well_known_files,rma::options[num_rows$eq200][start_row$eq%d]" % start)
        if not d:
            break
        rec += d["msg"]
        if len(rec) >= d["total_rows"]:
            break
        start += 200
    by = {r["specimen_id"]: r for r in rec if not r.get("superseded")}
    rng = random.Random(SEED)
    rng.shuffle(rows)
    out = []
    for det in rows:
        if len(out) >= limit:
            break
        sid = det["specimen__id"]
        r = by.get(sid)
        if not r:
            continue
        wf = [f for f in r.get("well_known_files", [])
              if f.get("well_known_file_type_id") == 303941301]
        if not wf:
            continue
        body = fetch("http://api.brain-map.org" + wf[0]["download_link"], raw=True)
        if not body or len(body) < 200:
            continue
        p = os.path.join(workdir, "allen__%d.swc" % sid)
        with open(p, "wb") as fh:
            fh.write(body)
        try:
            m = swclib.metrics(p, source="allen")
        except Exception:                                         # noqa: BLE001
            os.remove(p)
            continue
        m["archive"] = "Allen Cell Types"
        m["neuron_name"] = str(sid)
        m["neuron_id"] = sid
        m["whole_brain"] = False
        m["nmo_attributes"] = None
        m["nmo_domain"] = det.get("nr__reconstruction_type")
        m["species"] = det.get("donor__species")
        m["dendrite_type"] = det.get("tag__dendrite_type")
        m["structure"] = det.get("structure__acronym")
        out.append(m)
    print("    %-14s %3d cells" % ("Allen", len(out)))
    return out


# --------------------------------------------------------------- exemplars ---

def pick_exemplars(metrics, workdir=None):
    """The two reconstructions figure 2 draws, chosen by rule, not by eye.

    One from each method, each the cell closest to its group's median on the
    two quantities the figure is about - how far the arbor reaches and how
    much axon it carries - so that neither is a flattering outlier.  The
    Allen cell must additionally have a measured diameter and the MouseLight
    cell must not, because that contrast is the figure's whole point and it
    has to be true of the individuals drawn, not only of the populations.

    The Allen cell is taken from the spiny cells where there are any.  Spiny
    cells are pyramidal cells, they are the largest group in that database,
    and they are what an image search for a cortical neuron returns; their
    axon is also the one that slicing removes almost entirely, which is the
    contrast the figure is about.  Taking the median of all Allen cells
    instead drew an interneuron carrying 13.9 mm of dense local axon, which
    is a true picture of an interneuron and the wrong picture for this page.

    Files are downloaded here rather than copied out of the sampling run, so
    that this step can be re-run on its own from data/swc_metrics.csv.
    """
    import statistics as st

    def closest(group, want_measured):
        g = [m for m in group
             if m.get("max_radial_um") and m.get("len_axon_um") is not None
             and bool(m.get("diam_measured")) == want_measured]
        if not g:
            return None
        spiny = [m for m in g if (m.get("dendrite_type") or "") == "spiny"]
        g = spiny or g
        mr = st.median([m["max_radial_um"] for m in g])
        ma = st.median([max(m["len_axon_um"], 1.0) for m in g])
        return min(g, key=lambda m: (abs(m["max_radial_um"] - mr) / mr) ** 2
                   + (abs(max(m["len_axon_um"], 1.0) - ma) / ma) ** 2)

    allen = closest([m for m in metrics if m["archive"] == "Allen Cell Types"], True)
    ml = closest([m for m in metrics if m["archive"] == "MouseLight"], False)
    kept = {}
    for m, src in ((allen, "allen"), (ml, "mouselight")):
        if not m:
            print("    no exemplar for %s" % src)
            continue
        d = os.path.join(SWC, src)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, "%s.swc" % str(m["neuron_name"]).replace("/", "_"))
        if src == "allen":
            body = allen_swc(int(m["neuron_id"]))
        else:
            body = fetch(swc_url(m["archive"], m["neuron_name"]), raw=True)
        if not body:
            print("    could not download the %s exemplar" % src)
            continue
        with open(dst, "wb") as b:
            b.write(body)
        kept[src] = {"file": os.path.relpath(dst, HERE).replace("\\", "/"),
                     "neuron": m["neuron_name"], "archive": m["archive"],
                     "reach_um": m["max_radial_um"], "axon_um": m["len_axon_um"],
                     "dend_um": m["len_dend_um"], "diam_measured": m["diam_measured"],
                     "n_distinct_diam": m["n_distinct_diam"],
                     "frac_len_modal_diam": m["frac_len_modal_diam"]}
        print("    exemplar %-11s %-22s reach %7.0f um  axon %8.0f um  diameter %s"
              % (src, m["neuron_name"][:22], m["max_radial_um"], m["len_axon_um"],
                 "measured" if m["diam_measured"] else "PLACEHOLDER"))
    return kept


# ----------------------------------------------------------- complete set ---

def complete_set(workdir):
    """Open every reconstruction that passes all five constraints.

    The cascade counts the complete set from the archive's flags, and a flag
    is the depositor's claim about a file, not a measurement of it.  This
    downloads each of them, measures it with swclib, and keeps the metrics
    in data/complete_metrics.csv beside the census fields that describe it.
    The census carries no neuron_name - it was trimmed to the columns the
    cascade reads - so the name is looked up by id, one API call per cell.

    Returns the metric rows; nothing is kept in data/swc/ here.
    """
    import build_neuron
    rows = build_neuron.read_census()
    _, keep = build_neuron.cascade(rows)
    print("  complete set: %d reconstructions pass all five flags" % len(keep))
    out, missing = [], 0
    for r in keep:
        rec = fetch("%s/neuron/id/%s" % (NMO, r["neuron_id"]))
        if not rec or not rec.get("neuron_name"):
            missing += 1
            continue
        name, arch = rec["neuron_name"], rec["archive"]
        body = fetch(swc_url(arch, name), raw=True)
        if not body or len(body) < 200:
            missing += 1
            continue
        p = os.path.join(workdir, "complete__%s__%s.swc" % (nmo_slug(arch), name.replace("/", "_")))
        with open(p, "wb") as fh:
            fh.write(body)
        try:
            m = swclib.metrics(p, source=nmo_slug(arch))
        except Exception:                                         # noqa: BLE001
            os.remove(p)
            missing += 1
            continue
        m["archive"] = arch
        m["neuron_name"] = name
        m["neuron_id"] = r["neuron_id"]
        m["species"] = r["species"]
        m["cell_type"] = r["cell_type"]
        m["brain_region"] = r["brain_region"]
        m["doi"] = r["doi"]
        m["protocol"] = r["protocol"]
        m["whole_brain"] = nmo_slug(arch) in swclib.Z_TRUSTWORTHY
        m["_path"] = p
        out.append(m)
    if missing:
        # a partial set would let the page state a count that no longer
        # matches the files it was measured on
        raise SystemExit("complete set: %d of %d could not be opened; refusing to "
                         "write a partial file" % (missing, len(keep)))
    print("  complete set: %d files opened, %d pass the width rule"
          % (len(out), sum(1 for m in out if m["diam_measured"])))
    return out


def write_complete(mets):
    cols = ["archive", "neuron_name", "neuron_id", "species", "cell_type", "brain_region",
            "doi", "protocol", "source", "whole_brain"]
    cols += sorted(k for k in {k for m in mets for k in m} if k not in cols and k != "_path")
    mpath = os.path.join(DATA, "complete_metrics.csv")
    with open(mpath, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(mets, key=lambda m: (m["archive"], m["neuron_name"])))
    print("  complete metrics -> %s" % os.path.basename(mpath))
    return mpath


def pick_drawn(mets):
    """The one reconstruction from the complete set that figure 5 draws.

    By rule, not by eye, and every step of the rule is computed from the set
    itself: take the largest single-paper group among the complete set - the
    DOI the page already cites as the one that states its shrinkage
    correction - drop any file that fails the width rule when opened, and
    take the cell closest to that group's median reach and axon length, the
    same distance pick_exemplars() uses.  So the drawn cell is the ordinary
    member of the group the page's correction claim rests on, not the most
    photogenic file in the archive.
    """
    import statistics as st
    doi = Counter(m["doi"] for m in mets if m["doi"])
    top_doi, top_n = doi.most_common(1)[0]
    g = [m for m in mets if m["doi"] == top_doi and m["diam_measured"]
         and m.get("max_radial_um") and m.get("len_axon_um")]
    mr = st.median([m["max_radial_um"] for m in g])
    ma = st.median([m["len_axon_um"] for m in g])
    best = min(g, key=lambda m: (abs(m["max_radial_um"] - mr) / mr) ** 2
               + (abs(m["len_axon_um"] - ma) / ma) ** 2)
    return best, {"doi": top_doi, "n_with_doi": top_n, "n_pass_width": len(g),
                  "median_reach_um": mr, "median_axon_um": ma}


def keep_drawn(mets):
    """Copy the drawn cell's file into data/swc/<archive>/ and describe it."""
    best, rule = pick_drawn(mets)
    src = nmo_slug(best["archive"])
    d = os.path.join(SWC, src)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, "%s.swc" % best["neuron_name"].replace("/", "_"))
    shutil.copyfile(best["_path"], dst)
    print("    drawn  %-22s %-10s reach %6.0f um  axon %8.0f um  %d widths"
          % (best["neuron_name"], best["archive"], best["max_radial_um"],
             best["len_axon_um"], best["n_distinct_diam"]))
    return {"file": os.path.relpath(dst, HERE).replace("\\", "/"),
            "neuron": best["neuron_name"], "neuron_id": best["neuron_id"],
            "archive": best["archive"], "species": best["species"],
            "cell_type": best["cell_type"], "brain_region": best["brain_region"],
            "doi": best["doi"], "protocol": best["protocol"], "rule": rule}


def clear_kept(src):
    d = os.path.join(SWC, src)
    if os.path.isdir(d):
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))


def manifest_hashes(man):
    files = [os.path.join(DATA, "neurons.csv.gz"), os.path.join(DATA, "swc_metrics.csv"),
             os.path.join(DATA, "complete_metrics.csv")]
    files += [os.path.join(HERE, v["file"]) for v in man.get("exemplars", {}).values()]
    if man.get("drawn"):
        files.append(os.path.join(HERE, man["drawn"]["file"]))
    return {os.path.relpath(p, HERE).replace("\\", "/"): sha256(p)
            for p in files if os.path.exists(p)}


# ---------------------------------------------------------------- manifest ---

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-census", action="store_true")
    ap.add_argument("--sample", type=int, default=60, help="cells per archive")
    ap.add_argument("--allen", type=int, default=300)
    ap.add_argument("--exemplars-only", action="store_true",
                    help="re-choose and re-download the two cells figure 2 draws, "
                         "from the metrics already in data/")
    ap.add_argument("--complete-only", action="store_true",
                    help="open the complete set again, rewrite data/complete_metrics.csv "
                         "and re-choose the cell figure 5 draws")
    a = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    os.makedirs(SWC, exist_ok=True)
    workdir = os.path.join(DATA, "_work")
    os.makedirs(workdir, exist_ok=True)
    cpath = os.path.join(DATA, "neurons.csv.gz")
    mpath_man = os.path.join(DATA, "manifest.json")

    if a.exemplars_only:
        import build_neuron
        mets = build_neuron.read_metrics()
        man = json.load(open(mpath_man, encoding="utf-8"))
        for src in man.get("exemplars", {}):
            clear_kept(src)
        kept = pick_exemplars(mets)
        man["exemplars"] = kept
        man["sha256"] = manifest_hashes(man)
        json.dump(man, open(mpath_man, "w", encoding="utf-8"), indent=1)
        print("  manifest updated")
        return 0

    if a.complete_only:
        man = json.load(open(mpath_man, encoding="utf-8"))
        comp = complete_set(workdir)
        write_complete(comp)
        if man.get("drawn"):
            clear_kept(nmo_slug(man["drawn"]["archive"]))
        man["drawn"] = keep_drawn(comp)
        man["sha256"] = manifest_hashes(man)
        json.dump(man, open(mpath_man, "w", encoding="utf-8"), indent=1)
        for f in os.listdir(workdir):
            os.remove(os.path.join(workdir, f))
        os.rmdir(workdir)
        print("  manifest updated")
        return 0

    total = None
    if a.skip_census and os.path.exists(cpath):
        with gzip.open(cpath, "rt", encoding="utf-8") as fh:
            total = sum(1 for _ in fh) - 1
        print("  census: reusing %d rows" % total)
    else:
        total = census(cpath)

    print("  sampling reconstructions across %d archives" % (len(ARCHIVES) + 1))
    mets = sample_nmo(a.sample, workdir)
    mets += sample_allen(a.allen, workdir)
    print("  %d reconstructions parsed" % len(mets))

    cols = sorted({k for m in mets for k in m})
    lead = ["archive", "neuron_name", "neuron_id", "species", "source", "whole_brain"]
    cols = lead + [c for c in cols if c not in lead]
    mpath = os.path.join(DATA, "swc_metrics.csv")
    with open(mpath, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(mets)
    print("  metrics -> %s" % os.path.basename(mpath))

    kept = pick_exemplars(mets)
    comp = complete_set(workdir)
    write_complete(comp)
    drawn = keep_drawn(comp)

    man = {
        "retrieved": time.strftime("%Y-%m-%d", time.gmtime()),
        "sources": {
            "neuromorpho": {"api": NMO, "licence": "CC BY 4.0",
                            "cite": "Ascoli, Donohue & Halavi, J Neurosci 27(35):9247-9251, 2007, "
                                    "doi:10.1523/JNEUROSCI.2055-07.2007; Tecuatl, Ljungquist & "
                                    "Ascoli, FASEB BioAdvances 6(7):207-221, 2024, "
                                    "doi:10.1096/fba.2024-00048",
                            "reconstructions": total},
            "allen": {"api": ALLEN,
                      "licence": "free, non-commercial, journalistic carve-out",
                      "cite": "Allen Cell Types Database (RRID:SCR_014806); Gouwens et al., "
                              "Nat Neurosci 22(7):1182-1195, 2019, doi:10.1038/s41593-019-0417-0"},
        },
        "seed": SEED, "archives_sampled": ARCHIVES, "per_archive": a.sample,
        "n_sampled": len(mets),
        "exemplars": kept,
        "drawn": drawn,
    }
    man["sha256"] = manifest_hashes(man)
    with open(mpath_man, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    print("  manifest -> data/manifest.json")

    for f in os.listdir(workdir):
        os.remove(os.path.join(workdir, f))
    os.rmdir(workdir)
    print("  working files discarded; %d SWC kept" % (len(kept) + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
