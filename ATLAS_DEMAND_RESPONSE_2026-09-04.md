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
