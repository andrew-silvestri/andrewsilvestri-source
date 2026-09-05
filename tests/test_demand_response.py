"""Demand response happens.

The pages say consumers use less when costs rise and that a negative link
carries relief. The payload has carried 1,142 negative consumer->district
edges since the July build, and from the day the engine became
bidirectional until 2026-09-05 pushing a consumer moved its district UP,
because the +0.50 demand edge's back-channel outweighed the -0.01 response
(HANDOFF section 6, property 5; ATLAS_DEMAND_RESPONSE_2026-09-04.md). This
is the check that would have caught it: push a consumer group, and its
district must move down - by however little the elasticity says, but down.

Runs the figures' engine (build_throughlines.engine(), which
tests/test_parity.py holds equal to the browser's) over a deterministic
sample of consumer groups, and every one of them when --all is given.

Run:  python tests/test_demand_response.py          # 40 consumer groups
      python tests/test_demand_response.py --all    # all 1,142
Exit status 1 if any district moves up, or fails to move at all.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

SAMPLE = 40


def main():
    from build_throughlines import engine
    raw = open(os.path.join(ROOT, "site", "assets", "atlas-data.js"), encoding="utf-8").read()
    D = json.loads(raw[raw.index("=") + 1:raw.rindex(";")])
    kind = [D["kinds"][k] for k in D["kind"]]
    # the consumer groups are the consumers with a response edge into a district
    district_of = {}
    for s, t, w in zip(D["es"], D["et"], D["ew"]):
        if kind[s] == "consumer" and kind[t] == "district" and w < 0:
            district_of[s] = t
    groups = sorted(district_of)
    if not groups:
        print("  no consumer->district response edges in the payload")
        return 1
    picked = groups if "--all" in sys.argv else groups[::max(1, len(groups) // SAMPLE)][:SAMPLE]
    run, _ = engine(D)
    bad, moves = 0, []
    for c in picked:
        d = district_of[c]
        st, _ = run({c: 1.0})
        moves.append(st[d])
        if not st[d] < 0:
            bad += 1
            print(f"  FAIL {D['name'][c][:40]:40s} -> district {st[d]:+.4f} (wants < 0)")
    print(f"  {len(picked) - bad}/{len(picked)} consumer groups pushed +1 move their district down "
          f"(range {min(moves):+.4f} to {max(moves):+.4f}); {len(groups)} response edges in the payload")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
