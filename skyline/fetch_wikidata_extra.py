"""Per-tower facts for drawing, from Wikidata: architectural style (P149),
floors above ground (P1101), every height statement with its part/criterion
qualifiers (so a spire or pinnacle height can be drawn as a needle), the image
(P18, used only as a reference while authoring) and architect (P84).
Archived whole in data/raw/wdextra_<date>.json (not wikidata_*, which build_skylines.load_raw() globs)."""
import json, datetime, urllib.parse, urllib.request, os
HERE = os.path.dirname(os.path.abspath(__file__))
EP = "https://query.wikidata.org/sparql"
UA = "skylines-played/1.0 (andrewsilvestri.com)"
def ask(q):
    req = urllib.request.Request(EP, data=urllib.parse.urlencode({"query": q, "format": "json"}).encode(),
                                 headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    return json.load(urllib.request.urlopen(req, timeout=120))["results"]["bindings"]
P = json.load(open(os.path.join(HERE, "data", "skylines.json"), encoding="utf-8"))
qs = sorted({r[7] for c in P["cities"] for r in c["ring"]})
vals = " ".join("wd:" + q for q in qs)
Q = {
 "style": "SELECT ?b ?s ?sLabel WHERE { VALUES ?b {%s} ?b wdt:P149 ?s . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } }",
 "floors": "SELECT ?b ?f WHERE { VALUES ?b {%s} ?b wdt:P1101 ?f . }",
 "heights": "SELECT ?b ?hm ?rank ?part ?partLabel ?crit ?critLabel WHERE { VALUES ?b {%s} ?b p:P2048 ?st . ?st psn:P2048/wikibase:quantityAmount ?hm . ?st wikibase:rank ?rank . OPTIONAL { ?st pq:P518 ?part } OPTIONAL { ?st pq:P1013 ?crit } SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } }",
 "image": "SELECT ?b ?img WHERE { VALUES ?b {%s} ?b wdt:P18 ?img . }",
 "architect": "SELECT ?b ?aLabel WHERE { VALUES ?b {%s} ?b wdt:P84 ?a . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } }",
}
out = {"fetched": datetime.date.today().isoformat(), "endpoint": EP, "queries": {}, "answers": {}}
for k, q in Q.items():
    out["queries"][k] = q
    out["answers"][k] = ask(q % vals)
    print(k, len(out["answers"][k]))
json.dump(out, open(os.path.join(HERE, "data", "raw", "wdextra_%s.json" % out["fetched"]), "w"), indent=0)
