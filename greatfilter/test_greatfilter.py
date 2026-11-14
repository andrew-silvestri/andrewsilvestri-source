"""The Great Filter page (greatfilter.html)'s own failure modes. Each check has a --break that reproduces the fault
it names, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Model checks rerun the model with fresh
seeds rather than reading the payload they are checking (trap 20).

 1. equal     n equally hard steps each take T/(n+1) of the window, for n = 3, 4, 5 (exact answer).
              --break equal keeps every history, finished or not.
 2. reject    The cut-off sampler agrees with plain rejection where rejection is affordable (means 1, 2 and 3
              in a window of 2): conditional means within 3%. --break reject cuts the waits off at T/2.
 3. watson    Known answer from the literature: four hard steps in Watson's 5-billion-year window leave about
              1 billion years at the end, his figures. --break watson uses three steps.
 4. sdo       The Sandberg-Drexler-Ord prior, redrawn with a new seed, gives P(N<1) within one point of the
              paper's 52%. --break sdo reads the 50-orders spread as natural-log units.
 5. waits     The payload's waits are the differences of the dates in sources.py, and the longest is the
              complex cell. --break waits moves life to its clock date.
 6. page      The page is exactly what update_page.py renders. --break page changes one figure.
 7. cards     Every order drawn in the timeline (0-6) has a step card, and every card an order.
              --break cards drops a card.
 8. nojs      The shipped page draws every row: no element carries the live-only class "off". --break nojs adds one.
 9. cites     Every anchor in add_citations.PAGES["greatfilter.html"] placed a marker.
              --break cites removes one anchor phrase from the page before counting.
10. employer  The internship employer is not named. --break employer checks for a word that is on the page.

Run:  python test_greatfilter.py [--break equal|reject|watson|sdo|waits|page|cards|nojs|cites|employer]
"""
import hashlib
import html
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import sources as S              # noqa: E402
import build_greatfilter as B    # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "greatfilter.html")
# the internship employer, by the SHA-1 of its lower-cased name (the name may not appear in this tree)
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def page_text(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def sample(means, T, n, seed, cap_at=None, keep_all=False):
    """The builder's sampler, written again here so a fault in one copy shows against the other."""
    rng = np.random.default_rng(seed)
    means = np.asarray(means, float)
    c = cap_at if cap_at is not None else T
    cap = -np.expm1(-c / means)
    out = []
    while sum(len(o) for o in out) < n:
        w = -means * np.log1p(-rng.random((200_000, len(means))) * cap)
        out.append(w if keep_all else w[w.sum(1) <= T])
    w = np.concatenate(out)[:n]
    return w.mean(0), (T - w.sum(1)).mean()


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    raw = open(PAGE, encoding="utf-8").read()
    # 1 equal
    errs = []
    for n in (3, 4, 5):
        d, left = sample([1e4] * n, 1.0, 80_000, 100 + n, keep_all=BREAK == "equal")
        errs += [abs(x - 1 / (n + 1)) * (n + 1) for x in list(d) + [left]]
    check("1 equal", max(errs) < 0.03, f"largest relative error from 1/(n+1): {100 * max(errs):.1f}%")
    # 2 reject
    means, T = [1.0, 2.0, 3.0], 2.0
    rng = np.random.default_rng(5)
    w = rng.exponential(means, (3_000_000, 3))
    w = w[w.sum(1) <= T]
    d, _ = sample(means, T, len(w), 6, cap_at=T / 2 if BREAK == "reject" else None)
    err = np.max(np.abs(d - w.mean(0)) / w.mean(0))
    check("2 reject", err < 0.03, f"{len(w):,} rejection histories; largest difference {100 * err:.1f}%")
    # 3 watson
    k = 3 if BREAK == "watson" else S.WATSON["n"]
    _, left = sample([1e4] * k, S.WATSON["T"], 80_000, 9)
    check("3 watson", abs(left - S.WATSON["left"]) / S.WATSON["left"] < 0.03,
          f"{k} hard steps in {S.WATSON['T']} Gyr leave {left:.2f} Gyr (Watson: {S.WATSON['left']})")
    # 4 sdo
    d0 = dict(S.SDO)
    S.SDO.update(seed=11, n=600_000)
    if BREAK == "sdo":
        S.SDO["lnR_sd_dex"] = 50 / np.log(10)
    p = B.sdo()["p_alone"]
    S.SDO.clear()
    S.SDO.update(d0)
    check("4 sdo", abs(p - S.SDO["paper_p_alone"]) < 0.01 and abs(p - P["sdo"]["p_alone"]) < 0.01,
          f"P(N<1) = {100 * p:.1f}% (paper {100 * S.SDO['paper_p_alone']:.0f}%)")
    # 5 waits
    dates = [S.WINDOW["start_ga"]] + [s["early"] if (BREAK == "waits" and s["key"] == "life") else s["best"]
                                      for s in S.STEPS]
    waits = [round(a - b, 3) for a, b in zip(dates, dates[1:])]
    got = [r["wait"] for r in P["chain"]["rows"]]
    longest = S.STEPS[int(np.argmax(waits))]["key"]
    check("5 waits", waits == got and longest == "cell", f"waits {waits}; longest {longest}")
    # 6 page
    import update_page as UP
    t, _ = UP.cite(UP.render(P))
    if BREAK == "page":
        t = t.replace(">once<", ">twice<", 1)
    check("6 page", t == raw, "the page is exactly what update_page.py renders")
    # 7 cards
    fig = re.search(r'<figure class="chain.*?</figure>', raw, re.S).group(0)
    orders = sorted({int(o) for o in re.findall(r'data-o="(\d+)"', fig)})
    cards = sorted(int(s) for s in re.findall(r'class="step" data-step="(\d+)"', fig))
    if BREAK == "cards":
        cards = cards[:-1]
    check("7 cards", orders == cards == list(range(len(S.STEPS) + 2)), f"orders {orders}; cards {cards}")
    # 8 nojs
    f8 = fig.replace('class="row"', 'class="row off"', 1) if BREAK == "nojs" else fig
    offs = re.findall(r'class="[^"]*\boff\b[^"]*"', f8)
    check("8 nojs", not offs, "no row is hidden in the shipped markup" + (f"; {offs[:2]}" if offs else ""))
    # 9 cites
    import add_citations
    refs = add_citations.PAGES["greatfilter.html"][1:]
    r9 = raw
    if BREAK == "cites":
        r9 = re.sub(r'<sup class="cite" id="cr1">.*?</sup>', "", raw, count=1)
    placed = len(re.findall(r'<sup class="cite"', r9))
    listed = len(re.findall(r'<li id="ref\d+">', r9))
    check("9 cites", placed == listed == len(refs), f"{placed} markers, {listed} sources, {len(refs)} anchors")
    # 10 employer
    target = hashlib.sha1(b"filter").hexdigest() if BREAK == "employer" else EMPLOYER_SHA1
    words = set(re.findall(r"[a-z]+", page_text(raw).lower()))
    emp = any(hashlib.sha1(w.encode()).hexdigest() == target for w in words)
    check("10 employer", not emp, f"{len(words)} distinct words; employer not named")
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
