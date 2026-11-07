"""The page's figures, drawn as SVG strings (no browser, no node).

hero_section(P)  the scroll-driven exploded shoe. Four states:
                 0 the baseline shoe assembled, with its total;
                 1 exploded: each layer apart, each group with its kg CO2e;
                 2 the same groups for LC-1 made on grid power;
                 3 LC-1 as specified (renewable electricity at two sites).
                 Every animated element carries data-k; the page's inline script
                 interpolates the numbers between states as the reader scrolls.
                 Without JS, or with reduced motion, each step shows its own
                 static figure (scrolly.css: .step-fig, .snap-wide/.snap-phone).
waterfall(P)     per-100-km bars: baseline, the design, renewable power,
                 a second sole unit.

Text is 12 px IBM Plex Mono (scrolly.css .chart text) and never sits on a fill.
Character width for the fit check: 0.6 x 12 = 7.2 px (charts.js CW).
"""
import html
import json

CW = 7.2
GROUPS = [  # key, label, fill class
    ("upper", "Upper", "f-acc"),
    ("sock", "Sockliner", "f-rule"),
    ("mid", "Midsole foam", "f-moss"),
    ("out", "Outsole", "f-ink"),
    ("factory", "Factory energy", "f-dim"),
    ("rest", "Box, freight, disposal", "f-rule"),
]
LAYERS = ["upper", "sock", "mid", "out"]

# Schematic side view, heel at left, in a local frame: x 0-282, y 0 = ground, y up negative.
SHAPES = {
    "out": "M0,0 L230,0 Q262,0 282,-15 L283,-20 Q262,-7 230,-5 L0,-5 Z",
    "mid": "M0,-5 L230,-5 Q262,-7 283,-20 L281,-30 Q252,-25 205,-25 L70,-33 L0,-35 Z",
    "sock": "M6,-35 L70,-33 L205,-25 Q250,-25 272,-31 L270,-35 Q250,-29 205,-29 L70,-37 L6,-39 Z",
    "upper": ("M4,-39 C-2,-66 8,-94 30,-101 L66,-96 Q92,-78 118,-82 L158,-73 "
              "Q228,-60 268,-37 Q262,-31 250,-30 L205,-29 L70,-37 Z"),
}
EXPLODE = {"upper": -62, "sock": -38, "mid": -16, "out": 6}
LAYER_MID_Y = {"upper": -60, "sock": -35, "mid": -20, "out": -3}

FORMS = {
    # W, H, drawing origin (x, ground y), rows x, first row y, row step, bar scale px/kg, total y
    "wide": dict(W=720, H=380, ox=40, gy=262, rx=380, ry=58, step=50, scale=150.0, ty=362),
    "phone": dict(W=340, H=600, ox=29, gy=205, rx=20, ry=262, step=50, scale=150.0, ty=578),
}


def _fits(text, x, W):
    if x + CW * len(text) > W - 4:
        raise ValueError(f"label runs off the figure at {W}px: {text!r}")


def state_values(P, s):
    """Numbers for state s: per group kg, explode factor, total line."""
    key = {0: "baseline", 1: "baseline", 2: "lc1_design_only", 3: "lc1"}[s]
    tot = {0: f"Typical trainer: {P['pair']['baseline']:.2f} kg per pair",
           1: f"Typical trainer: {P['pair']['baseline']:.2f} kg per pair",
           2: f"LC-1, grid power: {P['pair']['lc1_design_only']:.2f} kg per pair",
           3: f"LC-1, renewable power: {P['pair']['lc1']:.2f} kg per pair"}[s]
    return dict(kg=P["groups"][key], explode=0.0 if s == 0 else 1.0, show=1.0, total=tot)


def elements(P, s, form):
    f = FORMS[form]
    v = state_values(P, s)
    els = []  # (tag, k or None, attrs, text)
    for name in LAYERS:
        ty = v["explode"] * EXPLODE[name]
        cls = dict(GROUPS_BY[name])["cls"]
        els.append(("path", "L" + name, {"d": SHAPES[name], "class": cls,
                                         "transform": f"translate({f['ox']},{f['gy']})", "ty": ty}, None))
    for i, (key, label, cls) in enumerate(GROUPS):
        y = f["ry"] + i * f["step"]
        kg = v["kg"][key]
        txt = f"{label}  {kg:.2f} kg"
        _fits(txt, f["rx"], f["W"])
        els.append(("text", "t" + key, {"x": f["rx"], "y": y}, txt))
        els.append(("rect", "b" + key, {"x": f["rx"], "y": y + 7, "width": round(kg * f["scale"] * v["show"], 2),
                                        "height": 12, "class": cls}, None))
        if key in LAYERS and form == "wide":
            x1 = f["ox"] + 288
            y1 = f["gy"] + LAYER_MID_Y[key] + v["explode"] * EXPLODE[key]
            els.append(("line", "c" + key, {"x1": x1, "y1": round(y1, 2), "x2": f["rx"] - 8, "y2": y + 13,
                                            "class": "ch-axis"}, None))
    _fits(v["total"], f["rx"] if form == "wide" else 20, f["W"])
    els.append(("text", "total", {"x": f["rx"] if form == "wide" else 20, "y": f["ty"]}, v["total"]))
    return els


GROUPS_BY = {k: {"cls": c, "label": l} for k, l, c in GROUPS}


def svg(P, s, form, title):
    f = FORMS[form]
    out = [f'<svg class="chart" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f["W"]} {f["H"]}" '
           f'width="{f["W"]}" height="{f["H"]}" role="img"><title>{html.escape(title)}</title>',
           f'<text x="{f["rx"] if form == "wide" else 20}" y="22" class="ch-tick">Greenhouse gas, kg CO2e per pair</text>']
    for tag, k, a, text in elements(P, s, form):
        a = dict(a)
        if "ty" in a:
            ty = a.pop("ty")
            a["transform"] = a["transform"][:-1] + f") translate(0,{ty:.2f})"
        attrs = " ".join(f'{n}="{html.escape(str(val))}"' for n, val in a.items())
        dk = f' data-k="{k}"' if k else ""
        if text is None:
            out.append(f"<{tag}{dk} {attrs}/>")
        else:
            out.append(f"<{tag}{dk} {attrs}>{html.escape(text)}</{tag}>")
    out.append("</svg>")
    return "".join(out)


def states_json(P, form):
    """Per state: {k: {attr: number, 'text': str}} for the page's script."""
    st = []
    for s in range(4):
        d = {}
        f = FORMS[form]
        for tag, k, a, text in elements(P, s, form):
            if not k:
                continue
            e = {n: round(float(a[n]), 2) for n in ("ty", "y1", "width") if n in a}
            if text is not None:
                e["text"] = text
            d[k] = e
        st.append(d)
    return dict(ox=FORMS[form]["ox"], gy=FORMS[form]["gy"], states=st)


TITLES = [
    "A typical running shoe, assembled, with the greenhouse gas from each part of one pair.",
    "The typical shoe taken apart: greenhouse gas from each part, from factory energy, and from the box, freight and disposal.",
    "The same parts for the LC-1 design, made on grid power.",
    "LC-1 with renewable electricity at final assembly and at the sole moulder.",
]


def hero_section(P, steps_html):
    """steps_html: four HTML paragraphs, one per state."""
    spec = {form: dict(svg=svg(P, 0, form, TITLES[0]), **states_json(P, form)) for form in ("wide", "phone")}
    js = json.dumps(spec, separators=(",", ":")).replace("</", "<\\/")
    parts = ['<section class="scrolly wide" id="shoe-hero">',
             f'<script type="application/json" class="shoe-spec">{js}</script>',
             '<div class="scrolly-stage" role="img" aria-label="An exploded running shoe. Each part carries its share '
             'of the greenhouse gas from one pair; the shares change from a typical trainer to LC-1."></div>',
             '<div class="scrolly-steps">']
    for s, text in enumerate(steps_html):
        parts.append(f'<div class="step" data-s="{s}">\n{text}\n<figure class="step-fig">'
                     f'<div class="snap-wide">{svg(P, s, "wide", TITLES[s])}</div>'
                     f'<div class="snap-phone">{svg(P, s, "phone", TITLES[s])}</div></figure>\n</div>')
    parts.append("</div>\n</section>")
    return "\n".join(parts)


# ------------------------------------------------------------------ waterfall
def waterfall_svg(P, form):
    """Horizontal bars, kg CO2e per 100 km: four levels and the steps between."""
    W = 720 if form == "wide" else 340
    rows = P["per100_steps"]  # [(label, value, kind)] kind: level | step
    scale = (W - 60) / max(r[1] for r in rows if r[2] == "level")
    y0, step = 40, 44
    H = y0 + step * len(rows) + 10
    out = [f'<svg class="chart" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">'
           '<title>Greenhouse gas per 100 km run, from the typical trainer to LC-1 with a second sole unit.</title>',
           '<text x="20" y="22" class="ch-tick">kg CO2e per 100 km</text>']
    prev = None
    for i, (label, val, kind) in enumerate(rows):
        y = y0 + i * step
        txt = f"{label}  {val:.2f}" if kind == "level" else f"{label}  -{val:.2f}"
        _fits(txt, 20, W)
        out.append(f'<text x="20" y="{y}">{html.escape(txt)}</text>')
        if kind == "level":
            out.append(f'<rect x="20" y="{y + 7}" width="{val * scale:.1f}" height="12" class="f-acc"/>')
            prev = val
        else:
            x = 20 + (prev - val) * scale
            out.append(f'<rect x="{x:.1f}" y="{y + 7}" width="{val * scale:.1f}" height="12" class="f-moss"/>')
            prev = prev - val
    out.append("</svg>")
    return "".join(out)


def figure(P, caption, fn):
    return ('<section class="scrolly wide fig-only">\n<div class="scrolly-steps">\n<div class="step">\n'
            f'{caption}\n<figure class="step-fig"><div class="snap-wide">{fn(P, "wide")}</div>'
            f'<div class="snap-phone">{fn(P, "phone")}</div></figure>\n</div>\n</div>\n</section>')


SCRIPT = r"""<script>
/* The exploded shoe (lowcarbon-shoe page only). The page reads without this:
   each step carries its own static figure. With motion on, the section goes
   live (scrolly.css .is-live): one figure sticks in the stage and its numbers
   follow the reader between the steps' states. Reduced motion: never live. */
(function () {
  'use strict';
  var root = document.documentElement, sec = document.getElementById('shoe-hero');
  if (!sec || !('IntersectionObserver' in window)) return;
  var spec = JSON.parse(sec.querySelector('script.shoe-spec').textContent);
  var stage = sec.querySelector('.scrolly-stage');
  var steps = [].slice.call(sec.querySelectorAll('.step'));
  var live = false, form = null, raf = 0, near = false;
  function motionOn() { return root.dataset.motion !== 'off'; }
  function pick() { return stage.clientWidth >= 720 ? 'wide' : 'phone'; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function apply(p) {
    var F = spec[form], S = F.states, n = S.length;
    var i = Math.max(0, Math.min(n - 1, Math.floor(p))), j = Math.min(n - 1, i + 1), t = Math.max(0, Math.min(1, p - i));
    var A = S[i], B = S[j];
    stage.querySelectorAll('[data-k]').forEach(function (el) {
      var k = el.getAttribute('data-k'), a = A[k], b = B[k];
      if (!a || !b) return;
      Object.keys(a).forEach(function (att) {
        if (att === 'text') { el.textContent = (t < 0.5 ? a : b).text; return; }
        var v = lerp(a[att], b[att], t);
        if (att === 'ty') el.setAttribute('transform', 'translate(' + F.ox + ',' + F.gy + ') translate(0,' + v.toFixed(2) + ')');
        else el.setAttribute(att, v.toFixed(2));
      });
    });
  }
  function progress() {
    var h = window.innerHeight, p = 0;
    for (var n = 1; n < steps.length; n++) {
      var f = (h * 0.85 - steps[n].getBoundingClientRect().top) / (h * 0.6);
      if (f <= 0) break;
      p = n - 1 + Math.min(1, f);
    }
    return p;
  }
  function frame() { raf = 0; if (live && near) apply(progress()); }
  function onScroll() { if (!raf) raf = requestAnimationFrame(frame); }
  function build() { form = pick(); stage.innerHTML = spec[form].svg; apply(progress()); }
  function on() {
    if (live || !motionOn()) return;
    live = true; sec.classList.add('is-live'); build();
    window.addEventListener('scroll', onScroll, { passive: true });
  }
  function off() {
    if (!live) return;
    live = false; sec.classList.remove('is-live'); stage.innerHTML = '';
    window.removeEventListener('scroll', onScroll);
  }
  new IntersectionObserver(function (es) { near = es[0].isIntersecting; if (near) onScroll(); }).observe(sec);
  window.addEventListener('resize', function () { if (live && pick() !== form) build(); });
  document.addEventListener('motionchange', function () { if (motionOn()) on(); else off(); });
  on();
})();
</script>"""
