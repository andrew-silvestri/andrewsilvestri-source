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
        # Q11, 2026-10-25. Disabled: the page is archived (D-60, Andrew: "make a note on the
        # top/near the top that its an (Archived) page"). It is a dated record of EIA's figures
        # and articles and says it is not updated; a refresh would move its numbers under prose
        # written against them.
        "page": "ethane",
        "cwd": "ethane",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_ethane.py"]],
        "keys": [],
        "enabled": False,
        "why": "Archived page (D-60): a dated record of EIA's figures and articles, not updated.",
    },
    {
        # safety-nets lane, 2026-11-07. Disabled: the data is annual, and the year the page reports is
        # LAST in fetch_public.py. Moving it is a change with its own review (the prose names years and
        # the build's method check must hold for the new year), not a monthly refresh. The BLS API is
        # also keyless here, with a daily quota a monthly run could exhaust.
        "page": "safetynet",
        "cwd": "safetynet",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_safetynet.py"]],
        "keys": [],
        "enabled": False,
        "why": "Annual data; the reported year moves by a reviewed change to LAST in fetch_public.py.",
    },
    {
        # Lane lost-einsteins, 2026-11-07. Disabled: the page is built on a published estimate for the
        # people alive in 2015 and on closed historical series; nothing in it is refreshed on a schedule.
        "page": "lead",
        "cwd": "lead",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_lead.py"]],
        "keys": [],
        "enabled": False,
        "why": "A published 2015 estimate and closed historical series; the page says it does not update.",
    },
    {
        # chain-reactions lane, 2026-11-07. Disabled: the page traces a finished policy chain
        # (1990-2006) and says its data does not update; a refresh would move its numbers under
        # prose written against them. update_page.claims() would stop a rebuild that contradicts it.
        "page": "oxygen",
        "cwd": "oxygen",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "build_oxygen.py"]],
        "keys": [],
        "enabled": False,
        "why": "A finished policy chain, 1990-2006, stated on the page as not updated.",
    },
    {
        # origins-of-life lane, 2026-11-13. Disabled: the page reads two fixed database versions
        # (ASHRAE II v2.1.0, MARHYS 3.0) and says its data does not update; build_origins.checks()
        # would stop a rebuild that contradicts the page's words.
        "page": "origins",
        "cwd": "origins",
        "fetch": [["python", "fetch_public.py"]],
        "build": [["python", "analyse_ashrae.py"], ["python", "build_origins.py"]],
        "keys": [],
        "enabled": False,
        "why": "Fixed database versions, stated on the page as not updated.",
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
