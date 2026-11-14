"""The public files the night-shift page reads, fetched into nightshift/data/raw/ and recorded in
data/fetched.json.

U.S. Bureau of Labor Statistics, American Time Use Survey (ATUS), public-use microdata
- lvresp-2425.zip: the Leave and Job Flexibilities Module, 2024-25. It asks employed respondents which
  shift they usually work (regular daytime, evening, night, rotating, split, irregular, other); BLS's
  "Job Flexibilities and Work Schedules, 2024-25" tables come from it. lvwgts-2425.zip: its weights.
- atusresp, atusact, atuswho, atussum, atusrost -2024 and -2025: the core ATUS files for the same
  respondents: who they are, each activity of their diary day with start and stop times, and who was
  with them.
- lvmintcodebk2425.pdf, atusintcodebk24.pdf, atusintcodebk25.pdf, lexiconwex2024.pdf: the codebooks
  and the activity lexicon the readers follow.
- a3-2025.htm: BLS ATUS Table A-3, percent of the population doing each activity at each hour, 2025;
  the build reproduces it from the microdata before it uses the microdata (see build_nightshift.py).
- flex-2425.htm: BLS news release tables, Job Flexibilities and Work Schedules 2024-25 (Tables 7, 8);
  the build reproduces the share of workers on a night shift from the module.

Run:  python fetch_public.py [name ...]
"""
import sys
import time

from netfetch import fetch

BLS = "https://www.bls.gov/tus/"
FILES = {f"{n}.zip": BLS + f"datafiles/{n}.zip" for n in (
    "lvresp-2425", "lvwgts-2425",
    "atusresp-2024", "atusresp-2025", "atusact-2024", "atusact-2025", "atuswho-2024", "atuswho-2025",
    "atussum-2024", "atussum-2025", "atusrost-2024", "atusrost-2025")}
FILES.update({f"{n}.pdf": BLS + f"dictionaries/{n}.pdf" for n in (
    "lvmintcodebk2425", "atusintcodebk24", "atusintcodebk25", "lexiconwex2024")})
FILES["a3-2025.htm"] = BLS + "tables/a3-2025.htm"
FILES["flex-2425.htm"] = "https://www.bls.gov/news.release/flex2.htm"


if __name__ == "__main__":
    only = sys.argv[1:]
    for name, url in FILES.items():
        if not only or name in only:
            p = fetch(url, name)
            if p.stat().st_size < 1500:
                raise SystemExit(f"{name}: {p.stat().st_size} bytes, not a document")
            time.sleep(3)
