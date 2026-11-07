"""Readers for the safety-net page's documents. Each reads a hash-checked raw file (netfetch.verified),
so a figure the page takes from a report or a paper is matched in that document's own text at render
time and cannot drift from it. The idiom is ethane/sources.py's.

flat(name)        a document's text, whitespace collapsed; HTML stripped of scripts, styles and tags.
quote(name, pat)  the match of a regular expression in that text; raises if there is none.
"""
import html
import re

from netfetch import verified

_cache = {}


def flat(name):
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            import pymupdf
            t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        else:
            t = p.read_bytes().decode("utf-8", errors="replace")
            t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", t, flags=re.S)
            t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        t = t.replace("–", "-").replace("—", "-").replace("ﬁ", "fi").replace("﻿", "")
        _cache[name] = re.sub(r"\s+", " ", t).strip()
    return _cache[name]


def quote(name, pat):
    m = re.search(pat, flat(name))
    if not m:
        raise SystemExit(f"{name}: no match for {pat!r}")
    return m
