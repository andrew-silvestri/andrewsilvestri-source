"""Fetch the Texas industrial price series the heat rework needs, from EIA API v2.

  electricity  electricity/retail-sales, TX, sector IND, monthly price (cents/kWh)
  gas          natural-gas/pri/sum, series N3035TX3 (TX industrial price, $/Mcf), monthly
  heat content natural-gas/cons/heat, TX, annual (Btu per cubic foot), for $/Mcf -> $/MMBtu

The key is read from the environment by name (EIA_API_KEY, via 00 PUBLISH/envfile.py)
and never written: the manifest stores each URL without it.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import envfile  # noqa: E402

KEY = envfile.get("EIA_API_KEY")
if not KEY:
    sys.exit("EIA_API_KEY is not set")
BASE = "https://api.eia.gov/v2/"
RAW = os.path.join(HERE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

Q = {
    "eia_tx_ind_elec_price.json": ("electricity/retail-sales/data/", [
        ("frequency", "monthly"), ("data[0]", "price"), ("facets[stateid][]", "TX"),
        ("facets[sectorid][]", "IND"), ("sort[0][column]", "period"), ("sort[0][direction]", "asc"),
        ("length", "5000")]),
    "eia_tx_ind_gas_price.json": ("natural-gas/pri/sum/data/", [
        ("frequency", "monthly"), ("data[0]", "value"), ("facets[series][]", "N3035TX3"),
        ("sort[0][column]", "period"), ("sort[0][direction]", "asc"), ("length", "5000")]),
    "eia_tx_gas_heat_content.json": ("natural-gas/cons/heat/data/", [
        ("frequency", "annual"), ("data[0]", "value"), ("facets[duoarea][]", "STX"),
        ("sort[0][column]", "period"), ("sort[0][direction]", "asc"), ("length", "5000")]),
}

man_p = os.path.join(HERE, "data", "fetched.json")
man = json.load(open(man_p, encoding="utf-8")) if os.path.exists(man_p) else {}
for name, (route, params) in Q.items():
    public = BASE + route + "?" + urllib.parse.urlencode(params)
    url = BASE + route + "?" + urllib.parse.urlencode([("api_key", KEY)] + params)
    body = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "andrewsilvestri.com heat"}),
                                  timeout=120).read()
    d = json.loads(body)
    d.get("request", {}).get("params", {}).pop("api_key", None)   # EIA echoes the key back; drop it
    body = json.dumps(d, indent=0).encode()
    assert KEY.encode() not in body
    open(os.path.join(RAW, name), "wb").write(body)
    man[name] = {"url": public, "fetched": dt.date.today().isoformat(), "bytes": len(body),
                 "sha1": hashlib.sha1(body).hexdigest(), "rows": len(d["response"]["data"])}
    print(name, len(d["response"]["data"]), "rows")
json.dump(man, open(man_p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
