"""The takeaway model: capacity by month, headroom since a reference month,
and the scenario the app runs (03 RESEARCH/takeaway/PLAN.md sections 2-3).

Months are (year, month) tuples and every quantity is Bcf/d.

    H(t) = [C(t) - C(t0)] - k * [P(t) - P(t0)]

C is the capacity step function, P is EIA's marketed production for the
Permian region, k is the share of an increment of marketed gas that must
leave the basin by pipe, and t0 is a month the pipes are assumed full. H is
the headroom gained (positive) or lost (negative) since t0. It is a
statement about whether the pipes are full only if they were full at t0;
nothing in this file makes that true.

The JavaScript port in engine.js must agree with this file to 1e-12
(tests/test_parity_takeaway.py); change one, change both.
"""


def add_months(ym, n):
    y, m = ym
    k = y * 12 + (m - 1) + n
    return (k // 12, k % 12 + 1)


def months_between(a, b):
    """Whole months from a to b (b later is positive)."""
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def month_range(a, b):
    """Every month from a to b inclusive."""
    out, t = [], a
    while t <= b:
        out.append(t)
        t = add_months(t, 1)
    return out


def capacity_added(additions, t0, t):
    """Capacity that entered service in months (t0, t], from additions [(month, bcfd)]."""
    if t >= t0:
        return sum(b for m, b in additions if t0 < m <= t)
    return -sum(b for m, b in additions if t < m <= t0)


def headroom(P, additions, k, t0, months):
    """H(t) for each month in `months` that P covers. P: {(y, m): Bcf/d}."""
    p0 = P[t0]
    return {t: capacity_added(additions, t0, t) - k * (P[t] - p0) for t in months if t in P}


def grow(P, last, r, until):
    """P extended past its last month at r per year, compounded monthly as
    P(T + n) = P(T) * (1 + r) ** (n / 12). A scenario, not a forecast."""
    out = dict(P)
    for t in month_range(add_months(last, 1), until):
        out[t] = P[last] * (1.0 + r) ** (months_between(last, t) / 12.0)
    return out


def scenario(P, last, entries, k, t0, r, delay, until, include=None):
    """The app's run. entries: [{"month", "bcfd", "status", "key"}]. Expected
    entries move `delay` months later; `include` (a set of keys) drops any
    expected entry not in it. Returns (H by month, first month after `last`
    with H < 0 or None)."""
    adds = []
    for e in entries:
        m = e["month"]
        if e["status"] == "expected":
            if include is not None and e["key"] not in include:
                continue
            m = add_months(m, delay)
        adds.append((m, e["bcfd"]))
    Pg = grow(P, last, r, until)
    H = headroom(Pg, adds, k, t0, month_range(t0, until))
    first = next((t for t in sorted(H) if t > last and H[t] < 0), None)
    return H, first


def growth(P, a, b):
    """Change in P from month a to month b."""
    return P[b] - P[a]


def event_clusters(starts, gap=12):
    """Group start months: a start less than `gap` months after the previous
    one joins its cluster. Returns [(first, last, [starts])]."""
    out = []
    for m in sorted(starts):
        if out and months_between(out[-1][1], m) < gap:
            out[-1] = (out[-1][0], m, out[-1][2] + [m])
        else:
            out.append((m, m, [m]))
    return out


def before_after(series, clusters, window=12):
    """Mean of `series` over the `window` months before each cluster's first
    start and the `window` months after its last. A cluster is computed only
    when both windows are complete in the series and hold no other cluster's
    start; otherwise its reason is returned instead."""
    out = []
    for i, (a, b, ms) in enumerate(clusters):
        pre = month_range(add_months(a, -window), add_months(a, -1))
        post = month_range(add_months(b, 1), add_months(b, window))
        others = [m for j, c in enumerate(clusters) if j != i for m in c[2]]
        row = {"first": a, "last": b, "starts": ms}
        if any(m in pre or m in post for m in others):
            row["skip"] = "another start inside its windows"
        elif not all(t in series for t in pre + post):
            row["skip"] = "series does not cover both windows"
        else:
            row["before"] = sum(series[t] for t in pre) / window
            row["after"] = sum(series[t] for t in post) / window
            row["diff"] = row["after"] - row["before"]
        out.append(row)
    return out


def placebo(series, clusters, window=12):
    """The same after-minus-before difference at every month whose windows are
    complete and lie wholly clear of every cluster's windows: the spread an
    event's difference is ranked within."""
    blocked = set()
    for a, b, _ in clusters:
        blocked.update(month_range(add_months(a, -window), add_months(b, window)))
    out = {}
    for m in sorted(series):
        pre = month_range(add_months(m, -window), add_months(m, -1))
        post = month_range(add_months(m, 1), add_months(m, window))
        span = pre + [m] + post
        if all(t in series for t in span) and not any(t in blocked for t in span):
            out[m] = sum(series[t] for t in post) / window - sum(series[t] for t in pre) / window
    return out
