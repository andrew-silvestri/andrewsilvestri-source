"""Write neuron-app.html from template-app.html and the payload.

The app is the cascade made reorderable.  It ships the 32 subset counts - one
per combination of the five constraints - and does no filtering of its own, so
there is no second implementation of the rule to drift from the first.  At
~700 bytes of data it is the smallest app on the site by three orders of
magnitude, which is the right size for what it has to say.

Called by build_neuron.py --build.
"""
import json
import os


def payload_for_app(p):
    c = p["cascade"]
    k = p["the_complete"]
    return {
        "total": c["n_total"],
        "constraints": [{"key": a["key"], "label": a["label"], "n": a["n"]}
                        for a in c["alone"]],
        "subsets": c["subsets"],
        "all_note": ("These %d come from %d laboratories, contain no human cell, and are "
                     "almost all cells whose axon never leaves the neighbourhood."
                     % (k["n"], k["n_labs"])),
        "foot": ("Every reconstruction in NeuroMorpho.Org v8.x, retrieved %s, counted from the "
                 "archive's own metadata. The counts are the archive's claims about its files, "
                 "not measurements of them. "
                 "<a href=\"neuron.html\">Back to the page</a>." % p["retrieved"]),
    }


def write(p, here):
    tpl = open(os.path.join(here, "template-app.html"), encoding="utf-8").read()
    data = json.dumps(payload_for_app(p), separators=(",", ":"), sort_keys=True)
    if "{{data}}" not in tpl:
        raise SystemExit("template-app.html has no {{data}} placeholder")
    out = tpl.replace("{{data}}", data)
    path = os.path.join(here, "neuron-app.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print("  app -> neuron-app.html (%.1f KB, data %d bytes)"
          % (len(out.encode("utf-8")) / 1024, len(data)))
    return path
