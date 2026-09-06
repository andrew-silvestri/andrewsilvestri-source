"""The payload is what it was last recorded to be.

site/assets/atlas-data.js is 10 MB, gitignored, and outside every other
check: the generator check cannot rebuild it (the pipeline needs the raw
data and a day), so nothing noticed when its content and its builder drifted
apart. atlas_payload.json records the SHA-1 of the last known state, when,
and what that state is (as of 2026-09-05: the last full build plus two
hand-patched tab subtitles that build_atlas_global.py now writes itself).
This compares the file to the record and fails on any difference, so a
changed payload is a change someone has to re-record on purpose:

    python tests/test_payload.py            # check
    python tests/test_payload.py --record   # after a deliberate change, with a note

HANDOFF section 8, trap 23, is the reason.
"""
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAYLOAD = os.path.join(ROOT, "site", "assets", "atlas-data.js")
RECORD = os.path.join(ROOT, "atlas_payload.json")


def main():
    if not os.path.exists(PAYLOAD):
        print("  no payload at site/assets/atlas-data.js")
        return 1
    h = hashlib.sha1(open(PAYLOAD, "rb").read()).hexdigest()
    n = os.path.getsize(PAYLOAD)
    if "--record" in sys.argv:
        note = input("  what is this state of the payload? ").strip()
        json.dump({"sha1": h, "bytes": n, "recorded": datetime.date.today().isoformat(),
                   "note": note}, open(RECORD, "w", encoding="utf-8"), indent=1)
        print(f"  recorded {h[:12]} ({n:,} bytes)")
        return 0
    rec = json.load(open(RECORD, encoding="utf-8"))
    if rec["sha1"] == h:
        print(f"  payload is the recorded state of {rec['recorded']} ({n:,} bytes): {rec['note'][:80]}")
        return 0
    print(f"  FAIL payload differs from the state recorded on {rec['recorded']}: "
          f"{rec['sha1'][:12]} -> {h[:12]}, {rec['bytes']:,} -> {n:,} bytes.")
    print("       If this change is deliberate, re-record it: python tests/test_payload.py --record")
    print(f"       The record says: {rec['note']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
