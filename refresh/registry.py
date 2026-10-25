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
        # R3, 2026-10-23: meter.html became a redirect stub; its entry is the
        # lost-gas page's now. Still disabled, and not by oversight: the page's
        # data is annual (PHMSA reports, EIA annual series) and PHMSA's file
        # needs a visible browser window, so nothing here runs unattended. The
        # page carries insight.stamp_annual(), which names the year and PHMSA's
        # as-of date rather than a month.
        "page": "lostgas",
        "cwd": "lostgas",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_lostgas.py"]],
        "keys": [],
        "enabled": False,
        "why": "Annual data. PHMSA's distribution file needs a visible Chrome window "
               "(fetch_phmsa.py), so a new year is fetched and built by hand; the page's "
               "stamp says which year and the file's as-of date.",
    },
    {
        # Q12, 2026-10-24. Disabled: the bond schedules are fixed when the bonds are sold, and
        # the charges move only when a utility files a true-up (Texas each autumn, Oklahoma
        # twice a year), as PDFs at addresses that change with each filing. A new filing is
        # added to uri/fetch_public.py by hand; the page says it does not update itself.
        "page": "uri",
        "cwd": "uri",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_uri.py"]],
        "keys": [],
        "enabled": False,
        "why": "Fixed bond schedules; charges change only by new filings at new addresses, "
               "added by hand. The page states which filings it shows.",
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
    {
        # R4 (2026-10-23): ERCOT replaces the current year's DAM and RTM files
        # in place under a new name; fetch_ercot.py reads the listing and
        # fetches only files whose ERCOT name it has not recorded. The build
        # re-solves every year (about twenty minutes) because the cache is
        # keyed by each file's SHA-1, so unchanged years are read from the
        # cache and only the dispatch runs again. update_page.claims() stops
        # the page if a new year contradicts its words.
        "page": "storage",
        "cwd": "storage",
        "fetch": [["python", "fetch_ercot.py"]],
        "build": [["python", "build_storage.py"]],
        "keys": [],
        "enabled": True,
        "why": "",
    },
    {
        # R4 (2026-10-23): EIA's monthly Texas industrial prices. The build also
        # reads ERCOT's files under storage/data/raw for the flexible case, so
        # it runs after the storage entry's fetch; heat/update_page.claims()
        # stops the page if a new month contradicts its words.
        "page": "heat",
        "cwd": "heat",
        "fetch": [["python", "fetch_eia.py"]],
        "build": [["python", "build_heat.py"]],
        "keys": ["EIA_API_KEY"],
        "enabled": True,
        "why": "",
    },
]
