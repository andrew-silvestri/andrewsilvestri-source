"""Facts the page quotes from a source rather than computes.

Each is held as the source's own words, and every number the page prints
from it is parsed out of those words here, so the number and the quote cannot
drift apart. Saved copies of each page are in 03 RESEARCH/takeaway/refs/
(not shipped: news text is not ours to redistribute).
"""
import re

EIA_2024 = {
    "cite": "EIA, Today in Energy, 2025-02-03",
    "url": "https://www.eia.gov/todayinenergy/detail.php?id=64445",
    "quote": "prices at the Waha Hub near Permian Basin production activities traded below zero for 42% of "
             "trading days in 2024 as natural gas production from the Permian Basin outpaced available pipeline "
             "takeaway capacity",
}
EIA_T0 = {
    "cite": "EIA, Today in Energy, 2024-09-10",
    "url": "https://www.eia.gov/todayinenergy/detail.php?id=63044",
    "date": "10 September 2024",
    "quote": "Prices at the Waha Hub have been below zero for 46% of trading days in 2024, including every day "
             "since July 26",
}
REUTERS = {
    "cite": "Reuters, in Pipeline & Gas Journal, 2026-05-28",
    "url": "https://pgjonline.com/news/2026/may/waha-gas-prices-hit-16-week-high-as-permian-pipeline-constraints-ease",
    "date": "May 28",
    "quote": "They did so 17 times in 2019, six times in 2020, once in 2023, 49 times in 2024, 39 times in 2025, "
             "and a record 87 times so far this year.",
    "cause": "below zero for a record 78 days in a row as pipeline constraints from spring maintenance trapped gas",
}
RRC_FLARING = {
    "cite": "Railroad Commission of Texas, Flaring Regulation (FAQ)",
    "url": "https://www.rrc.texas.gov/about-us/faqs/oil-gas-faq/flaring-regulation",
    "quote": "In existing production areas, flaring also may be necessary because existing pipelines may have "
             "reached capacity.",
}


def eia_pct():
    m = re.search(r"below zero for (\d+)% of trading days in (\d{4})", EIA_2024["quote"])
    return int(m.group(1)), int(m.group(2))


def reuters_counts():
    q = REUTERS["quote"]
    out = {int(y): int(n) for n, y in re.findall(r"(\d+) times in (\d{4})", q)}
    out[2026] = int(re.search(r"record (\d+) times so far this year", q).group(1))
    return out
