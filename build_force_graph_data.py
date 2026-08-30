"""
Real graph data for the force-graph-driven background used on the
atlas/model page cluster.

Don't reinvent build_bg_graph.py's own real BFS walk (same seed-and-hop
logic that already produces the sitewide static SVG wash) - reuse it, just
sample more nodes and write plain node/edge JSON instead of a hand-projected
SVG, since force-graph (a real physics engine, loaded from a CDN) does its
own live layout client-side and needs real connectivity, not real
coordinates.

Run:  python3 build_force_graph_data.py
"""
import json
import os

import build_bg_graph as bg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site", "assets", "force-graph-data.js")

TARGET_NODES = 70
HOPS = 5


def main():
    D = bg.load()
    adj = bg.build_adjacency(D)
    seed = bg.pick_seed(D, adj)
    bg.HOPS = HOPS  # walk() reads this as a module global, not a parameter
    nodes = bg.walk(adj, seed, TARGET_NODES)
    node_set = set(nodes)

    kinds, kind, name = D["kinds"], D["kind"], D["name"]
    out_nodes = [{"id": i, "kind": kinds[kind[i]], "name": name[i]}
                 for i in nodes]

    edges, seen_pairs = [], set()
    for a, b in zip(D["es"], D["et"]):
        if a in node_set and b in node_set and a != b:
            pair = (min(a, b), max(a, b))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                edges.append({"source": a, "target": b})

    payload = {"nodes": out_nodes, "links": edges}
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("window.FORCE_GRAPH_DATA=" + json.dumps(payload) + ";\n")

    print(f"  seed: node {seed} ({kinds[kind[seed]]}), walked {HOPS} hops "
          f"to {len(nodes)} real nodes, {len(edges)} real edges among them")
    print(f"  wrote {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
