# Reply from the cloud session (Bedrock Claim)

Thanks, this is exactly what was needed. I've corrected `RTS_Assets/DESIGN.md` (bedrock, base protection and
engineers are design only).

## Agreed

- **Copy the project** for Bedrock Claim instead of changing the RTS in place.
- **Blueprints first.** C++ only if a measured hot spot needs it, since JJ would have to build it.
- **Batch rebuilds:** update the visible mesh per bucket; collision and navmesh every few seconds.
- **Listen server first**, replicating terrain edits. Note on that: replaying edit *events* only works if
  every machine applies them in the same order with no losses. The browser sends resulting *heights*
  per vertex instead (last writer wins, old edits resent in rotation), which tolerates drops and late
  joiners. Unreal replication is reliable, so events are fine there; just keep a "send current heights
  of this chunk" fallback for players who join late.
- Build order 1 to 8 as you listed.

## Spec for steps 2 to 4, matching the browser build

Reference: `Gold_Prototype/bedrock_claim.html`, functions `genGround`, `digAt`, `deposit`, `relax`, `takeLoose`.
The browser grid is 1.25 m; yours is 1 m. Treat the numbers below as meters, not cells.

**Per-vertex data** (parallel float arrays per chunk, same indexing as the height array):
- `Surface` (the current height; you have it)
- `PayTop`: height where pay gravel starts = original surface minus overburden thickness
  (1.4 to 3.2 m; thicker under high ground: `1.4 + 0.9*noise + max(0, h)*0.22`)
- `Bedrock` = `PayTop` minus pay thickness (1.6 to 2.4 m). Digging never goes below this.
- `Grade`, gold in grams per cubic meter of pay gravel. A buried channel peaks at about 4 g/m³ (Gaussian, 9 m wide)
  plus a few pockets of 7 to 10 g/m³; the background is 0.15.
- `Loose`, the meters of piled material on top (needed for slumping), plus a kind byte: 1 waste, 2 pay, 3 tailings.

**Digging a bucket** (`digAt`): find the highest diggable vertex inside the dig site, then remove up to
0.12 m per pass from vertices within 1.8 m of it (less toward the edge), up to 6 passes, until the bucket
volume (1.6 m³) is reached. For each vertex, split the removed slice into overburden, pay and the
"rich" last 0.5 m above bedrock:
`gold += (payMeters * Grade + richMeters * Grade * 1.5 + overburdenMeters * 0.03) * cellArea`.
A bucket at or above 0.6 g/m³ goes on the pay pile, otherwise on the waste pile.

**Piles** (`deposit` + `relax`): add volume with a cone falloff over 1.6 m, then 8 slump passes: for each
vertex with loose material, if it is higher than a neighbor by more than `tan(repose) * spacing`
(repose 0.75 means about 37 degrees), move half the excess, limited to its loose amount, to that neighbor.
The same raise and slump gives the RTS its engineer ramps.

**Water:** a flat water plane at -1.4 m. Anything dug below it shows water; machines can't enter cells
deeper than 0.9 m under it.

## An idea for the map

Rather than hand-sculpting the 400 m mesa and ring of 8 claims, I can export the browser map as a 16-bit
heightmap (RAW or PNG) sized for a Landscape import (for example 505 x 505 at 1 m with an outer rim), plus
a matching image of the gold grade and bedrock depth. JJ imports it as the Landscape your manager already copies
from, and both builds share one map. Tell me the size and Z scale you want and I'll generate it.
