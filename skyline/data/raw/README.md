# The raw pulls behind data/skylines.json

Kept whole, because the pull behind the payload shipped until October 2026 was
not, and so could never be re-run or checked (DECISIONS D-31).

| File | Written by | What it holds | Licence |
|---|---|---|---|
| `wikidata_<date>.json` | `fetch_wikidata.py` | Every SPARQL query's text, the endpoint, the date, and the answers as they came back from query.wikidata.org | Wikidata: CC0 1.0 |
| `osm_<date>.json.gz` | `fetch_osm.py` | Every Overpass query's text, the date, and the answers as they came back from overpass-api.de | © OpenStreetMap contributors, Open Database Licence (ODbL) 1.0: <https://www.openstreetmap.org/copyright>. This extract is redistributed under the ODbL. |

`build_skylines.py` reads the newest of each and nothing else. A fresh pull
gets a new date in its name; the old one stays until someone removes it on
purpose.
