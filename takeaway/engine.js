/* The takeaway scenario engine: a line-for-line port of takeaway/model.py's
   scenario path (add_months, capacity_added, headroom, grow, scenario).

   Months are [year, month] pairs, as model.py's tuples are; compared through
   idx() = year * 12 + (month - 1), so ordering is the tuples' ordering.
   tests/test_parity_takeaway.py holds this file to model.py at 1e-12; change
   one, change both. Loads in a browser (window.TakeawayEngine) and in node
   (module.exports). */
(function (root) {
  'use strict';

  function idx(m) { return m[0] * 12 + (m[1] - 1); }
  function fromIdx(k) { return [Math.floor(k / 12), (k % 12) + 1]; }
  function addMonths(m, n) { return fromIdx(idx(m) + n); }
  function monthsBetween(a, b) { return idx(b) - idx(a); }
  function key(m) { return m[0] + '-' + (m[1] < 10 ? '0' : '') + m[1]; }
  function parse(s) { const p = s.split('-'); return [+p[0], +p[1]]; }

  function monthRange(a, b) {
    const out = [];
    for (let k = idx(a); k <= idx(b); k++) out.push(fromIdx(k));
    return out;
  }

  // Capacity that entered service in months (t0, t]; additions: [[month, bcfd]].
  // Summed in list order, as Python's sum() over the same list is.
  function capacityAdded(additions, t0, t) {
    let s = 0;
    if (idx(t) >= idx(t0)) {
      for (const [m, b] of additions) if (idx(t0) < idx(m) && idx(m) <= idx(t)) s += b;
      return s;
    }
    for (const [m, b] of additions) if (idx(t) < idx(m) && idx(m) <= idx(t0)) s += b;
    return -s;
  }

  // H(t) = [C(t) - C(t0)] - k [P(t) - P(t0)]; P: {key: Bcf/d}. Returns {key: H}.
  function headroom(P, additions, k, t0, months) {
    const p0 = P[key(t0)], out = {};
    for (const t of months) {
      const kt = key(t);
      if (kt in P) out[kt] = capacityAdded(additions, t0, t) - k * (P[kt] - p0);
    }
    return out;
  }

  // P(T + n) = P(T) * (1 + r) ** (n / 12). A scenario, not a forecast.
  function grow(P, last, r, until) {
    const out = Object.assign({}, P), pT = P[key(last)];
    for (const t of monthRange(addMonths(last, 1), until)) {
      out[key(t)] = pT * Math.pow(1.0 + r, monthsBetween(last, t) / 12.0);
    }
    return out;
  }

  // entries: [{month, bcfd, status, key}]; include: Set of keys, or null for all.
  function scenario(P, last, entries, k, t0, r, delay, until, include) {
    const adds = [];
    for (const e of entries) {
      let m = e.month;
      if (e.status === 'expected') {
        if (include && !include.has(e.key)) continue;
        m = addMonths(m, delay);
      }
      adds.push([m, e.bcfd]);
    }
    const Pg = grow(P, last, r, until);
    const H = headroom(Pg, adds, k, t0, monthRange(t0, until));
    let first = null;
    for (const kt of Object.keys(H).sort()) {
      if (idx(parse(kt)) > idx(last) && H[kt] < 0) { first = kt; break; }
    }
    return { H: H, first: first };
  }

  const api = { idx, fromIdx, addMonths, monthsBetween, monthRange, key, parse,
                capacityAdded, headroom, grow, scenario };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TakeawayEngine = api;
})(typeof window !== 'undefined' ? window : this);
