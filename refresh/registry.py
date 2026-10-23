"""Which pages the monthly refresh updates, and how (R1 section 5, D-42).

One entry per page whose source updates. An entry is DISABLED until its page
carries the "Data through <month>" stamp (insight.stamp(), _INSIGHT rule 5)
and its fetchers run unattended: no visible browser window, no file name with
a month baked into it, nothing a person has to click. The packet that reworks
the page (R2, R3, R4) turns its entry on and says so in its STATE.md.

    page     the site page the entry refreshes (site/<page>.html)
    cwd      the project folder the commands run in
    fetch    commands that download new source data
    build    commands that rebuild the payload from it (the page generator
             itself runs in the ordering step, from tests/test_generators.py)
    keys     environment variable NAMES the fetchers read through envfile.py;
             a missing one stops the run and names the variable, never a value
    enabled  False until the page is ready, see above
    why      what stops it, while it is disabled

A dry run may include a disabled entry with --with <page>; a real run never
does.
"""

ENTRIES = [
    {
        "page": "meter",
        "cwd": "meter",
        "fetch": [["python", "fetch_henry_hub.py"]],
        "build": [],
        "keys": [],
        "enabled": False,
        "why": "R3 reworks the page. Henry Hub is monthly and fetches unattended; "
               "PHMSA (annual) needs a visible Chrome window and stays out of the "
               "monthly run. Enable once the reworked page shows its stamp, and add "
               "the payload builder here.",
    },
    {
        "page": "takeaway",
        "cwd": "takeaway",
        # R2 (2026-10-23): production only. The pipeline tracker carries
        # hand-checked overlays and the PDQ dump is 3.8 GB, so both stay at the
        # editions the page names beside its stamp; a new edition is a change
        # with its own review. update_page.claims() stops the build if a new
        # month contradicts the page's words, and the suite then publishes
        # nothing.
        "fetch": [["python", "fetch_eia.py", "--monthly"]],
        "build": [["python", "build_takeaway.py"]],
        "keys": [],
        "enabled": True,
        "why": "",
    },
]
