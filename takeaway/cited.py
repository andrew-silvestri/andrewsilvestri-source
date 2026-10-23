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
    "mechanism": "When regional growth in natural gas production outpaces pipeline takeaway capacity additions, "
                 "capacity constraints exert downward pressure on spot natural gas prices at the Waha Hub, which is "
                 "near Permian Basin production.",
}
REUTERS = {
    "cite": "Reuters, in Pipeline & Gas Journal, 2026-05-28",
    "url": "https://pgjonline.com/news/2026/may/waha-gas-prices-hit-16-week-high-as-permian-pipeline-constraints-ease",
    "date": "May 28",
    "quote": "They did so 17 times in 2019, six times in 2020, once in 2023, 49 times in 2024, 39 times in 2025, "
             "and a record 87 times so far this year.",
    "cause": "below zero for a record 78 days in a row as pipeline constraints from spring maintenance trapped gas",
}
# The same Reuters article, three more sentences (R2, re-read 2026-10-23).
REUTERS_MORE = {
    "first": "Daily Waha prices first averaged below zero in 2019.",
    "losses": "Energy firms in the Permian have been willing to take some losses on gas because they can make up "
              "for those with profits from selling oil.",
    "flare": "Negative gas prices were not very common a decade ago when environmental rules were less strict and "
             "many drillers could flare or burn off some of their unwanted gas.",
    "pay": "negative prices, which force some energy firms to pay others to take gas associated with their oil production",
}
EIA_2019 = {
    "cite": "EIA, Today in Energy, 2019-09-06",
    "url": "https://www.eia.gov/todayinenergy/detail.php?id=41213",
    "quote": "Limited natural gas pipeline takeaway capacity from the region has kept prices very low, or even "
             "negative, in recent months.",
    "gcx": "Deliveries into the pipeline began on August 8.",
}
EIA_2021 = {
    "cite": "EIA, Today in Energy, 2021-06-08",
    "url": "https://www.eia.gov/todayinenergy/detail.php?id=48276",
    "quote": "Over the past few years, constrained takeaway capacity in the Permian Basin kept Waha prices "
             "consistently at $1 per million British thermal units (MMBtu) or more below the Henry Hub price.",
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


def reuters_run():
    return int(re.search(r"record (\d+) days in a row", REUTERS["cause"]).group(1))


WORDS = {"once": 1, "six": 6}


def reuters_counts():
    """Every year the quote names, with its count (words or digits). Years it
    does not name are absent, not zero: the page says so where it draws them."""
    q = REUTERS["quote"]
    out = {int(y): int(n) for n, y in re.findall(r"(\d+) times in (\d{4})", q)}
    out.update({int(y): WORDS[w] for w, y in re.findall(r"\b(once|six)(?: times)? in (\d{4})", q)})
    out[2026] = int(re.search(r"record (\d+) times so far this year", q).group(1))
    return out


def reuters_first_year():
    return int(re.search(r"first averaged below zero in (\d{4})", REUTERS_MORE["first"]).group(1))
