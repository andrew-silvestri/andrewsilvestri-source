"""
The one HTTP helper the fetch scripts share: a GET with a descriptive
User-Agent (Wikimedia and IUCN both refuse generic ones), a retry with
backoff on transient failures, and a clean stop on 429, which for OpenAlex
means the day's budget is spent and for IUCN means the token is being
throttled. Nothing here reads a key from disk; keys come from the
environment only.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

UA = "andrewsilvestri.com-beauty/1.0 (https://andrewsilvestri.com; dasilvestri@utexas.edu) python-urllib"


class Budget(Exception):
    """HTTP 429: stop, keep what was written, say why."""


class Lock:
    """A heartbeat a fetch script holds while it is appending to a table.

    build_beauty.py refuses to run while one is live, because the manifest
    it writes is a claim about files as they are at that instant: hash a
    table that is still growing and the digest describes something that
    stops existing a second later, so the one number a reader is given to
    check their own fetch against is a number nobody can reproduce. The
    fetch-then-build order used to be a line in the README; this makes the
    build enforce it.

    The heartbeat, rather than a process id, is what lets a crashed fetch
    be recovered without asking the operating system anything: a lock
    nobody has touched for STALE seconds is dead, and the build says which
    one and what to do. Locks live under data/raw/, so they inherit that
    folder's exclusion from git and from the code archive.
    """

    STALE = 120

    def __init__(self, name, here):
        self.name = name
        self.dir = os.path.join(here, "data", "raw", ".locks")
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, name + ".lock")

    def __enter__(self):
        self.beat()
        return self

    def beat(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(f"{os.getpid()} {time.time():.0f} {self.name}\n")

    def __exit__(self, *exc):
        try:
            os.remove(self.path)
        except OSError:
            pass
        return False


def locks(here):
    """[(name, seconds since its last heartbeat, live?)] for every lock."""
    d = os.path.join(here, "data", "raw", ".locks")
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".lock"):
            age = time.time() - os.path.getmtime(os.path.join(d, f))
            out.append((f[:-5], age, age <= Lock.STALE))
    return out


def get_json(url, headers=None, retries=4, timeout=60, wait_429=0):
    """wait_429: seconds to sleep and retry on 429 (Wikimedia throttles a
    burst and recovers); 0 raises Budget, which is what a spent OpenAlex
    day or a throttled IUCN token should do."""
    hdr = {"User-Agent": UA, "Accept": "application/json"}
    hdr.update(headers or {})
    delay = 2.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if wait_429 and attempt < retries - 1:
                    time.sleep(wait_429)
                    continue
                raise Budget(f"429 from {url.split('?')[0]}")
            if e.code == 404:
                return None
            if e.code >= 500 and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return None


def need_key(name, where, turnaround):
    """Exit without writing when a required key is not in the environment."""
    sys.exit(f"  {name} is not set.\n  Request one at {where}\n  ({turnaround}), then run:\n"
             f"    set {name}=...   (PowerShell: $env:{name}='...')\n  Nothing was written.")
