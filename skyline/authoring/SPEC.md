# Authoring tower massing specs

You are drawing city towers for "Skylines, played", a data-honest skyline
visualisation. Each tower is rendered as a stack of extruded plan shapes
("tiers") with roofs, lit by the real sun. Your job: for every tower in
your input file, research what the building actually looks like and write a
massing spec that reproduces its silhouette and massing as accurately as
possible. Accuracy matters more than flourish. Never invent features you
have no evidence for.

## Inputs (your packet JSON)

Per tower: `qid`, `name`, `city`, `height_m` (Wikidata height, the height
the app uses, architectural incl. spire where Wikidata says so), `year`,
`floors`, `style`, `architect`, `image` (Wikimedia Commons file name),
`wd_heights` (all Wikidata height statements), `osm_source`
(`parts` = OpenStreetMap has a 3D model; `outline` = only the footprint;
`podium` = the footprint covers a whole complex; `generated` = nothing),
`osm_outline` (min-area rectangle of the footprint: `long_m`, `short_m`,
`long_axis_bearing` = compass bearing of the long side, `area_m2`,
`plan` round/rectangular/irregular), `osm_outline_points_m` (the footprint
polygon in metres, x = east, y = north, origin at the tower's Wikidata
coordinate), and for 3D-modelled towers `osm_3d_parts` (each part's
bottom z0, wall top, roof height/type, size, centroid).

## Research

IMPORTANT: WebSearch is rationed. Your task message gives your cap on
WebSearch calls for the whole batch; never exceed it. Do as much as you can
with WebFetch on direct URLs first, which is not rationed:
- the `wikipedia` field in your packet lists the tower's Wikipedia
  article URLs (English first, then local languages): WebFetch those
  directly. (wikidata.org pages may not fetch; don't rely on them.)
- `https://commons.wikimedia.org/wiki/File:<image>` for the photo page;
- `https://www.skyscrapercenter.com/` building pages if you know the URL.
Spend searches on the tallest / most distinctive towers whose pages say
nothing about their form. If an image search tool is available, use it.
If a tower has `previous_attempt`, that is an earlier low-confidence
drawing made without search: improve it, keep what was right.

Use web search and fetch (Wikipedia, CTBUH Skyscraper Center,
SkyscraperPage, Emporis archives, architects' pages, Wikimedia Commons file
pages and descriptions). If an image search tool is available, look at
photos. Find: overall plan shape, setbacks (at which heights/floors), tapers,
twists, crowns, roof shape, spires/masts and their heights, distinctive
features (e.g. sky bridges, cantilevers, slanted tops). Use real heights
where published (roof height, spire height, setback floors x ~3.6-4 m per
floor if only floors are known). Within your search cap, favour famous towers; obscure 55-90 m slabs get
none if their Wikipedia page or footprint suffices. Work fast: no long essays.

## Decide per tower

- If `osm_source` is `parts` and the 3D parts already match what you find
  (same setbacks/taper/crown within reason), set `"keep_osm": true` and give
  no tiers. Measured beats drawn.
- Otherwise write tiers. For `outline` towers, the footprint is real: build
  on it with `"plan": "outline"` and scale it for setbacks. For `podium` or
  `generated`, or where the outline is clearly a whole block/complex, use
  explicit shapes (rect/circle/etc.) sized from your research.

## Output: write ONE JSON file

Path given in your task. A JSON object keyed by qid:

```json
{
  "Q9188": {
    "name": "Empire State Building",
    "keep_osm": false,
    "confidence": "high",
    "sources": ["https://en.wikipedia.org/wiki/Empire_State_Building"],
    "notes": "setbacks at 5th, 21st, 25th, 72nd, 81st floors; mast from 320 m",
    "tiers": [
      {"z0": 0,   "z1": 25,  "plan": "outline", "scale": 1.0},
      {"z0": 25,  "z1": 90,  "plan": "rect", "w": 95, "d": 70, "rot": 29},
      {"z0": 90,  "z1": 255, "plan": "rect", "w": 60, "d": 45, "rot": 29},
      {"z0": 255, "z1": 320, "plan": "rect", "w": 40, "d": 30, "rot": 29,
       "roof": {"type": "stepped", "h": 0}},
      {"z0": 320, "z1": 381, "plan": "octagon", "w": 18, "rot": 29}
    ],
    "needle": {"z0": 381, "z1": 443, "w": 4}
  }
}
```

### Tier fields

- `z0`, `z1`: bottom and top of the walls, metres above ground. Required.
- `plan`: one of
  - `"outline"` – the tower's OSM footprint (only if it has one), scaled by
    `scale` about its centroid (`scale` may be `[bottom, top]` for a linear
    taper across the tier).
  - `"rect"` – `w` (along `rot`), `d` (across), `rot` = compass bearing of
    the `w` side, degrees.
  - `"square"` – `w`, `rot`.
  - `"circle"` – `w` = diameter.
  - `"ellipse"` – `w`, `d`, `rot`.
  - `"octagon"` – `w`, `rot` (regular octagon across flats).
  - `"triangle"` – `w` (side), `rot` (bearing one vertex points to).
  - `"chamfered"` – rect with corners cut: `w`, `d`, `rot`, `c` (chamfer m).
  - `"polygon"` – `points`: [[x_east, y_north], ...] metres around the
    tower's coordinate (use this for L/Y/crescent shapes; you may derive it
    from `osm_outline_points_m`).
- `taper`: `[bottom_scale, top_scale]` for any plan (alternative to scale
  list), e.g. a tower narrowing 100% -> 60% across the tier.
- `twist`: degrees of rotation from bottom to top of the tier.
- `offset`: `[east_m, north_m]` shift of the tier's centre from the tower
  coordinate (for twin towers, side wings, church towers, off-centre cores).
- `roof` (optional, on any tier): `{"type": T, "h": metres above z1}` with T
  in `flat | pyramid | dome | spire | gable | hip | skillion | stepped |
  crown | onion | mansard`. `skillion` also takes `"dir"` = compass bearing
  the slope falls toward. `stepped` and `crown` take `"steps"` (int) for an
  Art Deco wedding-cake crown inside the roof height. `spire` = slender
  pyramid. Omit or `flat` for flat.
- `facade` (optional): `masonry | ribbon | grid` to override window style.

### Tower fields

- `needle` (optional): `{"z0", "z1", "w"}` a mast or spire rod. It stands
  on the centre of your highest tier unless you give `"offset": [east_m,
  north_m]`.
- `keep_osm`, `confidence` (high/medium/low), `sources` (urls), `notes`
  (one line).
- The highest point you draw (top of highest roof or needle) should equal
  `height_m` unless you have strong evidence Wikidata is wrong; then still
  draw the real building and say so in `notes` (the app rescales to
  `height_m`).
- Separate buildings in one item (e.g. a twin-tower complex recorded as one
  Wikidata item) use `offset` to place each tower.
- Low-confidence obscure towers: a single outline tier to the right height
  with the right roof is fine; say `"confidence": "low"`.

## Rules

- Write valid JSON (no comments, no trailing commas). Validate it by
  reading it back with `python3 -c "import json;json.load(open(PATH))"`.
- Write incrementally: after every few towers, rewrite the whole file so
  progress survives if you are interrupted.
- Cover every tower in your packet, in order.
- Do not edit any other file. Many agents share this machine: put any
  helper scripts or scratch files ONLY in
  `/home/claude/sky/authoring/scratch/<your batch name>/`, never run or
  edit another agent's files, and never write to `out/` except your own
  output file.
- When done, reply with one line: count written, count keep_osm, and any
  towers you could not identify.
