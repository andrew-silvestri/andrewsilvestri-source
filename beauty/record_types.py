"""
Which OpenAlex record types count as research (D-32, R5 2026-10-24).

The page used to count every OpenAlex work whose title or abstract names a
species. QA found most of those are not research: GBIF occurrence downloads
(type `dataset`) and IUCN Red List assessments and Birds of the World
accounts (type `reference-entry`) name the species in their text. The list
below was fixed in 03 RESEARCH/beauty-r5/PLAN.md before any model was fitted
on the typed counts. Every type not in it is not research, including types
OpenAlex adds later, so a new type cannot silently inflate the count.
"""

RESEARCH = ("article", "review", "preprint", "letter", "book", "book-chapter",
            "dissertation", "conference-paper", "report")
JOURNAL = ("article", "review")
DATASET = ("dataset",)
REFERENCE = ("reference-entry",)


def parse(by_type):
    """'article:3;dataset:5' -> {'article': 3, 'dataset': 5}."""
    out = {}
    for kv in filter(None, (by_type or "").split(";")):
        t, c = kv.rsplit(":", 1)
        out[t] = out.get(t, 0) + int(c)
    return out


def total(counts, types):
    return sum(c for t, c in counts.items() if t in types)
