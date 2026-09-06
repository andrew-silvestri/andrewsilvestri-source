"""
The failure modes this project is exposed to.

1. A z coordinate from a slice reconstruction reaches a figure. Distributed
   Allen files are not shrinkage-corrected: the archive ships no per-cell
   correction, Gouwens et al. 2019 handled the compression by excluding
   z-derived features rather than fixing coordinates, and the correction
   exists only downstream in Lee et al. 2021. A 3D rendering from those files
   would be wrong by roughly a factor of two in one axis and would look
   entirely plausible. This is the characteristic failure of this project, so
   it is closed structurally - load_xy() returns two columns and load_xyz()
   reads its provenance from the file's directory - and asserted here.

2. A fabricated thickness is drawn as if it varied. The whole-brain files
   carry a single radius for the entire arbor. Any figure that varies their
   line width is drawing a number nobody measured.

3. The cascade does not reproduce. Every count on the page and all 32 subset
   counts in the app must fall out of the frozen census again.

4. The complete set stops being what the page says it is. The page makes a
   specific claim about the 104: how many laboratories, whether any human
   cell is among them, and that nearly half carry one DOI.

5. The page over-claims the gradient. Stage 1 measured a rank correlation of
   0.88 across two datasets whose reach ranges barely overlap, so the
   relationship was indistinguishable from the boundary between two methods;
   within one archive it was 0.078. The verdict rule was fixed before the
   answer was known, and the page's sentence must follow from it.

6. The page and the payload disagree.

7. The parser is unpinned. This is the one that would invalidate everything
   else, and it is the one a plausible check misses. Reproducing a published
   summary statistic does not pin a parser: a mis-summed segment, a
   double-counted soma or a dropped root can still land near a published
   mean, because a mean is a loose target and is usually not even the same
   statistic. So the arithmetic is pinned twice, and neither way is an
   aggregate: against tests/fixture.swc, whose every quantity was worked out
   by hand, and - with --network - against L-Measure's independent
   computation of the same quantities on the same bytes.

8. The drawn cell drifts from its file, or the complete set from its
   measurements. The page draws one of the complete set at three scales and
   states what each window holds; the file is hashed in the manifest, the
   selection rule must re-pick it from data/complete_metrics.csv, the
   windows and the "under one pixel" shares must fall out of the file again,
   and the opened-set summary the page quotes must fall out of the CSV.

9. An alt attribute makes a claim the prose no longer makes. Alt text is a
   claim the page makes - a screen reader gets nothing else - and on
   2026-09-06 figure 5's caption was corrected ("the thinnest calibre in
   the literature" became the electron-microscopy figure reference 2
   supplies) while its alt text kept the old wording and shipped. So: every
   figure has an alt; no alt carries a digit, because a number in alt text
   is typed rather than generated and will drift from the caption under it;
   and neither the page nor the app carries a phrase the page has retired,
   listed in RETIRED below with the date it went.

Run:  python3 test_neuron.py [--network]
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swclib                                                    # noqa: E402
import build_neuron as B                                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PAYLOAD = os.path.join(HERE, "outputs", "neuron_payload.json")
PAGE = os.path.join(HERE, "..", "site", "neuron.html")

fails = []

# Phrases the page once made and has withdrawn, with when. A retired claim
# that comes back - in prose, in alt text, in the app's note - fails here.
RETIRED = [
    ("thinnest calibre in the literature", "2026-09-06: nobody measured a literature-wide "
                                            "minimum; the 0.17 um is one electron-microscopy figure"),
    ("almost all cells whose axon never leaves the neighbourhood",
     "2026-09-06: fifteen of the 104 are projection cells reaching 2-6 mm"),
    ("each at its own scale", "2026-09-06: figure 2 draws both cells at one scale"),
    ("every width in the file is under a pixel",
     "2026-09-06: the soma and the widest dendrite exceed a pixel in panel A"),
]


def check(label, ok, detail=""):
    print("  %-4s %s%s" % ("ok" if ok else "FAIL", label, ("  " + detail) if detail else ""))
    if not ok:
        fails.append(label + ((": " + detail) if detail else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", action="store_true",
                    help="also cross-check the parser against NeuroMorpho's morphometry API")
    a = ap.parse_args()

    P = json.load(open(PAYLOAD, encoding="utf-8"))

    # -- 7. the parser, first, because everything else rests on it ----------
    print("7. the parser, against ground truth rather than an aggregate")
    check("hand-computed fixture reproduces exactly", swclib._self_check() == 0)

    m = swclib.metrics(swclib.FIXTURE, source="fixture")
    check("the fixture's diameter rule is the far end, not the mean",
          abs(m["diam_max_um"] - 2.0) < 1e-9,
          "a soma-parented segment must not inherit the soma's radius")

    if a.network:
        import urllib.request, ssl                              # noqa: E401
        from urllib.parse import quote
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        def api(u):
            try:
                r = urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
                    timeout=90, context=ctx)
                return json.loads(r.read())
            except Exception:                                    # noqa: BLE001
                return None

        worst, n = 0.0, 0
        for src, d in P["pair"].items():
            rec = api("https://neuromorpho.org/api/neuron/name/%s" % quote(d["neuron"]))
            if not rec:
                continue
            mo = api("https://neuromorpho.org/api/morphometry/id/%d" % rec["neuron_id"])
            if not mo or not mo.get("length"):
                continue
            mine = swclib.metrics(os.path.join(HERE, d["file"]))["len_total_um"]
            worst = max(worst, abs(mine - mo["length"]) / mo["length"])
            n += 1
        if n:
            check("total length agrees with L-Measure on %d cell(s)" % n, worst < 1e-3,
                  "worst difference %.5f%%" % (100 * worst))
        else:
            check("L-Measure cross-check reachable", False, "the API did not answer")

    # -- 1. z provenance ----------------------------------------------------
    print("1. no slice-derived z reaches a figure")
    drawn_files = dict(P["pair"])
    if P.get("drawn"):
        drawn_files["drawn"] = P["drawn"]
    slice_files = []
    for src, d in drawn_files.items():
        p = os.path.join(HERE, d["file"])
        drawable = swclib.source_of(p) in swclib.Z_TRUSTWORTHY
        check("payload's z_drawable for %s matches its directory" % src,
              d["z_drawable"] == drawable, "declared %s, path says %s"
              % (d["z_drawable"], drawable))
        if not drawable:
            slice_files.append((src, p))
    for src, p in slice_files:
        try:
            swclib.load_xyz(p)
            check("load_xyz refuses the %s slice reconstruction" % src, False, "it returned data")
        except swclib.ZProvenanceError:
            check("load_xyz refuses the %s slice reconstruction" % src, True)
    if not slice_files:
        check("a slice reconstruction is present to test the guard with", False)

    check("load_xy returns two columns", swclib.load_xy(swclib.FIXTURE).shape[1] == 2)

    src_txt = open(os.path.join(HERE, "fig_neuron.py"), encoding="utf-8").read()
    check("no figure calls load_xyz", "load_xyz" not in src_txt,
          "fig_neuron.py must reach for z through no route at all")

    # -- 2. diameter provenance --------------------------------------------
    print("2. no fabricated thickness is drawn as if it varied")
    for src, d in drawn_files.items():
        mm = swclib.metrics(os.path.join(HERE, d["file"]))
        want = swclib.measured_diameter(mm["n_distinct_diam"], mm["frac_len_modal_diam"])
        check("%s: diam_measured matches the file" % src, d["diam_measured"] == want,
              "%d distinct values, %.1f%% of length at one"
              % (mm["n_distinct_diam"], 100 * mm["frac_len_modal_diam"]))
    ml = P["pair"].get("mouselight")
    if ml:
        check("the whole-brain exemplar is not credited with a measured width",
              ml["diam_measured"] is False,
              "%d distinct value(s) in the file" % ml["n_distinct_diam"])

    # -- 3. the cascade -----------------------------------------------------
    print("3. the cascade and the app's 32 subsets reproduce")
    with gzip.open(os.path.join(DATA, "neurons.csv.gz"), "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    casc, keep = B.cascade(rows)
    check("total", casc["n_total"] == P["cascade"]["n_total"],
          "%s" % f'{casc["n_total"]:,}')
    check("every step", [s["n"] for s in casc["steps"]] == [s["n"] for s in P["cascade"]["steps"]],
          " -> ".join(f'{s["n"]:,}' for s in casc["steps"]))
    check("all 32 subsets", casc["subsets"] == P["cascade"]["subsets"],
          "%d combinations" % len(casc["subsets"]))
    app = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                               open(os.path.join(HERE, "neuron-app.html"),
                                    encoding="utf-8").read(), re.S).group(1))
    check("the app ships the same subsets", app["subsets"] == casc["subsets"])
    check("the app ships the same total", app["total"] == casc["n_total"])

    # -- 4. the complete set ------------------------------------------------
    print("4. the complete set is still what the page says")
    got = B.describe_104(keep)
    want = P["the_complete"]
    check("count", got["n"] == want["n"], "%d" % got["n"])
    check("laboratories", got["n_labs"] == want["n_labs"], "%d" % got["n_labs"])
    check("no human cell among them", got["has_human"] is False)
    check("the commonest DOI and its share", got["top_doi"] == want["top_doi"]
          and got["top_doi_n"] == want["top_doi_n"],
          "%d of %d carry %s" % (got["top_doi_n"], got["n"], got["top_doi"]))

    # -- 8. the complete set, opened, and the drawn cell --------------------
    print("8. the opened set and the drawn cell reproduce from their files")
    import hashlib
    import fetch_data
    comp = B.read_complete()
    check("one measured row per file the cascade leaves", len(comp) == casc["n_complete"],
          "%d rows for %d" % (len(comp), casc["n_complete"]))
    check("the opened-set summary reproduces", B.opened(comp) == want["opened"],
          "%d pass the width rule, %d hold one width"
          % (want["opened"]["n_pass_width"], want["opened"]["n_single_width"]))

    def sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    for rel in ("data/complete_metrics.csv",) + tuple(d["file"] for d in drawn_files.values()):
        check("%s matches its hash in the manifest" % rel,
              sha(os.path.join(HERE, rel)) == P["manifest_sha256"].get(rel))
    d = P.get("drawn")
    if not d:
        check("a drawn cell is in the payload", False)
    else:
        best, rule = fetch_data.pick_drawn(comp)
        check("the selection rule re-picks the drawn cell",
              best["neuron_name"] == d["neuron"] and best["archive"] == d["archive"],
              "%s from %s; %d of %d with the DOI pass the width rule"
              % (best["neuron_name"], best["archive"], rule["n_pass_width"], rule["n_with_doi"]))
        p = os.path.join(HERE, d["file"])
        mm = swclib.metrics(p)
        check("the drawn cell's metrics reproduce from its file",
              all(abs(mm[a] - d[b]) < 1e-6 for a, b in
                  (("max_radial_um", "reach_um"), ("len_axon_um", "axon_um"),
                   ("len_dend_um", "dend_um"), ("soma_diam_um", "soma_diam_um")))
              and mm["n_distinct_diam"] == d["n_distinct_diam"])
        check("the drawn cell passes the width rule", d["diam_measured"] is True
              and swclib.measured_diameter(mm["n_distinct_diam"], mm["frac_len_modal_diam"]))
        check("the three windows and their under-a-pixel shares reproduce",
              B.ladder_windows(p) == d["windows"],
              "; ".join("%s %.0f%%" % (k, 100 * w["share_under_one_px"])
                        for k, w in d["windows"].items()))
        boxes = [tuple(w["box_css"]) for w in d["windows"].values()]
        check("the windows are drawn from the boxes the shares were computed at",
              boxes == [tuple(B.LADDER_CSS[k]) for k in ("A", "B", "C")])
        check("the pair's shared frame reproduces",
              B.pair_geometry(P["pair"]) == P["pair_geometry"],
              "%.1fx; the slice cell is %.0f px wide"
              % (P["pair_geometry"]["extent_ratio"], P["pair_geometry"]["allen_px_in_shared"]))

    # -- 5. the gradient verdict -------------------------------------------
    print("5. the page's gradient sentence follows from the rule")
    mets = B.read_metrics()
    # Recompute the way build() does, through the unit filter. An earlier
    # version of this check ran the test on the unfiltered sample: it passed,
    # because the medians happened to agree, while reporting 21 qualifying
    # archives against the payload's 19. A check that does not reproduce the
    # pipeline is not checking the pipeline.
    units, trusted = B.unit_check(mets)
    um = [m for m in mets if m["archive"] in trusted]
    check("the unit filter reproduces",
          sorted(u["archive"] for u in units if not u["micrometres"])
          == sorted(P["units"]["rejected"]),
          "%d of %d archives in micrometres; rejected %s"
          % (len(trusted), len(units), ", ".join(P["units"]["rejected"]) or "none"))
    check("the same cells reach the gradient test",
          len(um) == P["units"]["n_cells_kept"], "%d cells" % len(um))
    g = B.gradient_test(um)
    check("verdict reproduces", g["held"] == P["gradient"]["held"], P["gradient"]["verdict"])
    check("median within-archive rho reproduces",
          g["median_within_rho"] == P["gradient"]["median_within_rho"],
          "%s over %d qualifying archives"
          % (g["median_within_rho"], g["n_qualifying_archives"]))
    check("the qualifying-archive count reproduces",
          g["n_qualifying_archives"] == P["gradient"]["n_qualifying_archives"],
          "%d" % g["n_qualifying_archives"])
    check("the pooled figure is recorded too, and is not the one quoted",
          P["gradient"]["pooled_rho"] is not None,
          "pooled %s, within %s" % (P["gradient"]["pooled_rho"], g["median_within_rho"]))
    if P["gradient"]["held"]:
        check("a held gradient met both halves of the rule",
              g["median_within_rho"] > B.GRADIENT_RHO
              and g["share_above_threshold"] >= B.GRADIENT_SHARE)

    # -- 6. page and payload ------------------------------------------------
    print("6. the page is the template rendered from the payload")
    if not os.path.exists(PAGE):
        check("site/neuron.html exists", False, "not built yet")
    else:
        import update_page
        rendered, _ = update_page.cite(update_page.render(P))
        shipped = open(PAGE, encoding="utf-8").read()
        check("site/neuron.html matches", rendered == shipped)

        # -- 9. alt text ----------------------------------------------------
        print("9. alt text claims only what the page claims")
        imgs = re.findall(r"<img\b[^>]*>", shipped)
        figs = [m for m in imgs if 'class="fig' in m]
        alts = [re.search(r'alt="([^"]*)"', m) for m in figs]
        n_png = len([f for f in os.listdir(os.path.join(HERE, "..", "site", "assets"))
                     if re.match(r"neuron_fig\d+_.*\.png$", f)])
        check("every figure is on the page with an alt",
              len(figs) == n_png and all(a and a.group(1).strip() for a in alts),
              "%d figures, %d built" % (len(figs), n_png))
        digits = [a.group(1)[:50] for a in alts if a and re.search(r"\d", a.group(1))]
        check("no alt text carries a digit", not digits,
              "; ".join(digits) if digits else "numbers live in the generated captions")
        app = open(os.path.join(HERE, "neuron-app.html"), encoding="utf-8").read()
        low = (shipped + app).lower()
        back = [f"{ph!r} ({why})" for ph, why in RETIRED if ph.lower() in low]
        check("no retired claim is back, in prose, alt text or the app", not back,
              "; ".join(back) if back else "%d retired phrases checked" % len(RETIRED))

    print()
    if fails:
        print("%d failure(s):" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
