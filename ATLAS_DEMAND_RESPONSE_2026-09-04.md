# Demand response never manifests (2026-09-04)

A model bug, not a copy bug. Found by the read-only claims pass in
`DESLOP_3C_2026-09-04.md` §3; nothing has been changed.

## What the pages say

`model.html` line 158: consumers use less when costs rise. `atlas.html`:
"a negative link carries relief rather than stress." The payload holds
1,144 negative links (weights −0.670 to −0.009), and the engine preserves
their sign: forward and backward passes are normalised by |w| and a
positive push does arrive as relief where a negative link carries it
(NAO +1.0 → GBR grid −0.205, `atlas-app.js` lines 118–135).

## What actually happens

1,142 of the 1,144 negative links are consumer→district at −0.009 to
−0.011. Every one is paired with a two-way district→consumer edge at
+0.50. In the relaxation the +0.50 back-channel swamps the −0.01 forward
one: pushing a consumer +1.0 moves its district **+0.128**. So the
documented behaviour — demand falls, the district feels relief — is in
the payload and never in an outcome. The other two negative links (the
NAO pair) behave as described.

## Where it comes from

The weights are set in `build_atlas_global.py` (consumer→district) and
`build_atlas_brain.py` (district→consumer, through the behaviour layer):
the elasticity that sizes the −0.01 is two orders of magnitude below the
demand share that sizes the +0.50, and the engine's normalisation by |w|
does not rescue a link that small. Either the elasticity is meant to be
that small (then the prose is wrong and demand response is not in this
model) or it is meant to matter (then the weight, or the pairing, is
wrong).

## What a pass would do

1. Decide which of the two the model intends; write it down in
   `model.html` §5 next to the weight table.
2. If demand response is meant to matter: re-derive the consumer→district
   weight from the elasticity so that a unit push on a consumer moves its
   district in the documented direction, re-run `build_atlas_global.py`,
   `prune_atlas_edges.py`, `build_atlas_space.py`, `build_atlas_brain.py`,
   `build_scenarios.py` (the `reach` numbers will move), the figures, and
   `update_atlas_pages.py --apply`.
3. Add the check that would have caught it to `tests/`: push one consumer,
   assert its district moves down. Run it over the payload the way the
   claims pass did (the engine runs headlessly in node with a `vm`
   context).
4. Re-read the prose that leans on it: `model.html` §4 and §5,
   `atlas.html`'s "relief rather than stress", and the scenario bases that
   push consumers.

## Findings (2026-09-05, PHASE5 Part 4): nothing changed

**The pairing is intentional and the sign convention is right. The fault is
structural, and it was introduced by the fix for fault TWO.** Traced on one
consumer group (ABW district 1 household) through the figures' engine, which
`tests/test_parity.py` holds equal to the browser's:

- The consumer has one outgoing edge, consumer→district at −0.011 (the
  response), and two incoming: district→consumer at +0.50 (demand) and
  psych→consumer at +0.28. Both are inherited from the July build
  (`build_atlas_global.py` line 341 remaps the old edge list), and the July
  throughlines figure labels the negative link "demand response" by name.
- Under the July engine influence travelled only from an edge's source to
  its target (the comment at `atlas-app.js` line 78, fault TWO). The
  consumer's only path into its district was the −0.011 edge, so the
  documented behaviour held: push a consumer, the district feels relief.
- The fix for fault TWO made every edge within a rank two-way. The +0.50
  demand edge gained a back-channel, consumer→district at +0.50, and the
  engine files it in the same fan-in bucket as the response edge: both are
  "influence arriving at the district from a consumer". The bucket holds
  −0.011 + 0.50 = +0.489, so the operator's coefficient from this consumer to
  its district is +0.183, and pushing the consumer +1.0 moves the district
  +0.128. The elasticity was never meant to beat 0.50; it was meant to be
  the only channel, and it stopped being the only channel on the day the
  engine became bidirectional. So the answer to the question asked: it is
  not that the negative edge is too small to matter, and not that its sign
  is wrong. It is that a second, positive channel was created alongside it
  by a rule that was right everywhere else.

**Counterfactuals, run, not proposed:**

- A. Make district→consumer edges one-way (no back-channel), everything
  else as it is: the same push moves the district **−0.009**. Small, since
  the elasticity is small, and correctly signed. Pushing a behaviour
  channel then moves its consumer +0.29 and the district −0.004 instead of
  +0.053.
- B. Leave the pairing and scale the response weight ×55 to −0.55, past the
  demand edge: the district moves −0.021. It works and it is a number chosen
  to win, not a value from the literature. Rejected on those grounds.

**What A changes in published numbers**, measured over the six behaviour
scenarios (16 of the 60 push behaviour channels; none pushes a consumer
directly): reach falls by 6 to 45 per cent ("Fear becomes salient" 3,004 →
2,708 nodes, "Attention is exhausted" 314 → 172), mean district effects
move by under ten per cent, and no sign flips, because most of what
behaviour does to districts arrives through the 66,264 district↔behaviour
edges, not through the consumer groups. The §6 table on `model.html`, the
model chart's reach panel and the scenario `reach` fields would all move.

**Recommendation**, for a decision, not a change: A, as a kind-pair rule in
both engines, "a district→consumer edge is one-way", beside the rank rule.
It is the smallest change that restores the documented behaviour, it needs
no payload rebuild and no new weight, and it is honest about what it is: a
demand edge whose consumer does not talk back except through its response.
It touches the implementation of HANDOFF §6 property 2 (rank decides
direction) without changing its meaning for any other edge, and the parity
test is the check that both engines took it. Then the test the earlier
note asked for: push one consumer, assert its district moves down. The
alternative is to drop the 1,142 response edges and the claim, which is
smaller still and makes the model say less; A makes it say what the pages
already say.
