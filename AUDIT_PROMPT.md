# External design & legibility audit — prompt for a fresh session

Paste everything below the line into a new session. It assumes no prior context.

---

You are auditing a live personal site as an outside design critic. I want
judgement, not a checklist — the kind of read a good design editor gives before
something goes in front of an audience that matters.

## The site

**https://andrewsilvestri.com** — the portfolio of an energy-systems modeller.
Hand-written HTML/CSS/JS, no framework, no build step, deliberately so. Dark
theme throughout. Roughly a dozen pages:

| Page | What it is |
|---|---|
| `/` | Home. WebGL globe hero, a mosaic of figure thumbnails |
| `/atlas.html`, `/atlas-app.html` | An 86,622-node model of the world energy system, and the interactive globe that opens it |
| `/model.html` | How the model works |
| `/library.html` | Thirteen figure cards, each tagged with the method that drew it |
| `/heat.html`, `/storage.html`, `/climate-cost.html` | Three quantitative tools, each with figures, prose and a downloadable code bundle |
| `/longevity.html`, `/longevity-app.html` | Body mass vs lifespan across 7,873 species, plus an interactive visualiser |
| `/skyline.html`, `/desktop.html` | Two smaller side projects |
| `/code.html` | Code index |

Most pages carry an animated canvas in the side margins — drifting cards,
strata bands, shipping-route arcs — driven by one shared script.

## What I want

A written critique, organised by **severity of impact on a reader**, not by
page. For each finding: what you observed, why it hurts, and what you would do
instead. Be specific enough to act on — "the axis labels on `heat_fig4` are
9.5pt at a rendered width of 950px, roughly 7px effective, below the ~11px
floor for comfortable reading" beats "text is small".

Cover:

1. **Legibility and hierarchy.** Where does the eye go, and is that where it
   should go? Contrast on the dark ground, type scale, line length, the
   relationship between a figure and the prose that explains it. Does the
   serif body / sans UI split hold up?

2. **The figures specifically.** There are roughly thirty static charts. They
   were built by scripts against a shared palette — violet `#8b7ff2`, blue
   `#5aa8d8`, moss `#4f9d84`, rose `#d86a86`, gold `#c9a227`, slate `#6e8096`
   on a near-black `#070a12`. Judge them as a set: do they read as one system?
   Which individual charts are doing their job badly, and why — wrong chart
   type for the question, an axis that hides the point, labels that collide,
   a legend doing work a direct label should do, colour carrying meaning it
   cannot carry? Say which are the strongest, too, and what makes them work.

3. **What is missing.** This is the part I care most about. What would a
   reader want that isn't there? Where does the site explain something in a
   paragraph that a small diagram would settle in three seconds? Where is
   there a number without a comparison, a claim without a picture, a static
   image where an interaction would teach more? Name specific additions, not
   categories.

4. **Interaction and delight.** The margin animations, the globe, the two
   visualisers. Do they earn their place or are they decoration? Where does
   the site feel inert when it could reward curiosity? What would make it
   more *fun* to move through without making it sillier — this is a technical
   portfolio and it should stay one. Be concrete: name the element, the
   behaviour you'd add, and what it teaches.

5. **Responsive and accessible behaviour.** Check at desktop, tablet and
   phone widths. Motion is togglable — check both states, and check
   `prefers-reduced-motion`. Flag any contrast that fails WCAG AA, any hit
   target under 44px, anything that depends on colour alone.

## How to work

- **Actually visit the pages.** Do not audit from this description. Open them,
  scroll them, resize them, click the interactive things, open a code download.
- Look at the figures at full size (open the image directly) *and* at the size
  the page renders them. Several are legible at one and not the other; that
  gap is itself a finding.
- Where you can, quantify — px, contrast ratios, load weight, counts.

## What I do not need

- Praise that isn't load-bearing. A short note on what genuinely works is
  useful; a paragraph of warm-up is not.
- Advice to adopt a framework, a component library, or a CSS-in-JS anything.
  The no-build-step constraint is deliberate and permanent.
- Generic accessibility boilerplate. Only findings you actually observed on
  this site.
- Copy-editing of the prose, unless the writing is what's damaging the design.

## Output

A single markdown document:

1. **Verdict** — three or four sentences. If a stranger who models energy
   systems landed here, what impression forms, and what undercuts it?
2. **Findings**, ordered by impact. Each: observation → why it matters → the
   fix. Mark each `high` / `medium` / `low`.
3. **What's missing** — a ranked list of specific additions, each with a
   sentence on what it would let a reader understand that they currently
   cannot.
4. **Ten-minute wins** — anything with a large ratio of improvement to effort.
5. **What to leave alone** — the things that are working, so they don't get
   "improved" away.

Assume the reader of your audit is the person who built it and will implement
your suggestions personally. Write accordingly: direct, specific, no hedging.
