# Bedrock Claim (gold-mining spin-off)

Forked from the Plateau Sandbox terrain code (`RTS_Prototype/plateau_sandbox.html`). All combat removed.
Single file: `bedrock_claim.html`, published as its own artifact.

Inspirations: Paystreak (wages, diesel, wash plant economy), Groundwork Simulator (dig, haul, wash, soil and water),
Hydroneer, Captain of Industry. Focus on 1 to 2 claims, not a sprawling map.

## Working now (v1)

- Isometric orthographic camera. Drag pan, pinch zoom and rotate, wheel zoom, Q/E rotate, WASD.
- 200 m claim with a creek. Ground layers per cell: overburden, pay gravel, bedrock (undiggable).
  Gold follows a buried ancient channel plus a few rich pockets, and is richest in the last 0.5 m above bedrock.
- Water table at -1.4 m: dig below it and the pit floods. Machines avoid water and steep pit walls.
- Excavator: "Dig here" site. Digs top down, sorts each bucket by grade into a waste pile or pay dirt pile.
  Piles slump to the angle of repose (loose dirt tracked per cell).
- Loaders auto-haul from the best pay pile to the wash plant hopper. Tap a pile to haul from just that one.
- Wash plant needs an operator, power (generator, 40 kW of 60) and water (pump, 100 needed, each pump gives 60).
  Recovery 85%. Tailings pile behind it.
- Crew: 1 per machine or plant, auto-assigned. Bunkhouse gives 4 beds. Wages and diesel tick every second.
- Gold goes to the safe; sell at a drifting price. Geologist survey ($1,500) shows a grade heat map.
- Shop: excavator, loader, pump, generator, wash plant, bunkhouse.
- 20 minute season with an end report and "keep digging".
- Synthesized sound: engine hum, dig scrape, dump thud, plant rattle, gold ding, cash register.
- Tune drawer with "Copy my tuning", saved per browser.

## Next (tomorrow list)

- Excavator digs into a truck/loader directly; dozer to push waste and build ramps into the pit.
- Pumps that drain a flooded pit; pond for plant water recycling.
- Medium vs small pump, the big generator as separate sizes.
- Rival claims, 15 to 30 minute match timer.
- Town square with a saloon; hire cowboys as militia from buildings; small shootouts instead of armies.
- Real models (excavator, bobcat) through the Meshy to Blender pipeline.

## v3: drive it yourself (Road Crew style)

- You are Jimbo, on foot. Hop into the excavator, loaders or the Crew 4x4 (X / F, or the Hop in button).
  Excavator: WASD tracks, Q/E swing, Space digs and dumps; buckets sort into pay or waste piles, or straight
  into the plant hopper. Loader: Space scoops a pile and dumps. Machines you are not driving keep their jobs.
- Drive view follows Jimbo; Tab (or the button) switches to the boss view for click orders.
- Phone: left thumb stick plus Hop / Dig / swing buttons.
- Terrain has height now: a mesa with the town on top, an east ridge, a south bluff, a knoll, and a graded
  hill road from the claim up to town.
- Town: Assay Office (the only place gold sells, so you drive the 4x4 up), Equipment Dealer (deliveries
  arrive there and drive down), Saloon (placeholder for the cowboy militia).
- In a race each player has their own copy of this map. One shared map with 4 claims around the town
  needs terrain sync, which is the next big multiplayer step.

## v4: the big map (step 1 of the 8-player plan)

- 400 m map (4x the area). Town on a mesa in the exact center, 8 graded roads up it, one per claim.
- 8 claim slots in a ring at 120 m, rotationally identical (same geology, pond, gold channel and pockets in
  local coordinates), separated by ridges with a pass at 150 m. You hold slot 0; red stakes mark open slots.
- Rich gold pockets at the foot of the mesa between claims: the contested middle.
- Minimap in the ledger panel; tap it to look somewhere (switches to boss view).

## Plan (agreed with JJ)

1. Big map (done, v4).
2. Shared world (first version done, v5): 2 to 4 players in one world, one browser hosts the simulation and streams state.
3. Shootouts: revolvers, saloon hires a posse of 2 to 4 cowboys, carried gold drops on death, town control
   pays the best gold price.
4. Scale to 8 (4v4) with bots for empty slots.
Long term the real game lives in JJ's Unreal project; this browser build is the design lab.

## v5: shared world

- Starting a race hands out claim slots: free for all spreads players around the ring, Team Gold takes
  slots 0 to 3 side by side, Team Silver 4 to 7.
- Each player simulates only their own claim. Presence (about 6 updates a second, under 4 KB) carries
  Jimbo, every machine, the buildings and a rolling chunk of terrain edits. Other pages draw them as
  ghosts with name tags and apply the terrain edits, so you see each other's pits and piles.
- Old edits are resent slowly in rotation, so dropped updates and late arrivals catch up.
- Uses presence only (no event topics), so invited Viewers can play too.
- Not yet: other players' machines don't block your pathfinding, and selling in town has no contest yet
  (that is step 3, shootouts).

## v6: hero combat (step 3, first part)

Jimbo is the hero unit. Abilities reuse terrain physics, matching the laptop session's advice (no magic):
- Revolver (Space on foot): auto-aims at the nearest enemy, accuracy falls with distance and dashing
  targets, terrain and berms block shots. 25 damage, 4 hits to drop someone. Health regenerates slowly.
- Dash (Shift), 4 s cooldown. Satchel (G): lobbed charge, blows a crater (stops at bedrock), damages
  everyone within 5.5 m including you, 8 s cooldown. Berm (B): throws up a dirt wall for cover, 9 s cooldown.
- Down: half your carried gold drops as a sack anyone can grab; you respawn at your claim after 6 s.
- Bandits: pairs show up near town when you carry more than 3 g; $400 bounty each.
- Multiplayer: the shooter reports hits, the victim applies them; teammates can't hurt each other.
  Sack owners grant pickups first come, first served.
- Next: hire a posse at the saloon, and town control (best gold price for whoever holds it).

## v7: twitch combat and heavy gold (JJ's notes)

- Aim is SYNTHETIK-style with a mouse: Jimbo faces the cursor, left click (hold) fires exactly along that line
  with a little spread (more while sprinting), right click throws the satchel at the cursor (20 m max).
  Touch keeps aim assist. Fire rate 0.28 s, range 40 m. Dirt and berms stop bullets.
- Sprint: hold Shift (or Run on touch), no cooldown. Not possible above 100 lb.
- Gold has weight: the plant fills the claim safe; Space next to the plant loads it onto Jimbo, or into the
  4x4 while driving it. About 1 lb per gram (black-sand concentrate until the Assay Office cleans it).
  Jimbo slows above 40 lb. Only carried gold sells, and only in town. Death drops half of what Jimbo carries.
- 4x4: anyone not on your team can rob gold out of a 4x4 nobody is driving (X next to it).
  Teammates can ride in the back (X next to it) and shoot while their buddy drives.
- Bandits strafe, shoot from 32 m, and fire faster.
- Later: hire employees to run gold routes in the 4x4 (and protect them).

## v8: bulldozer

- In the starting kit and the shop ($16,000). Drive it yourself; Space drops or lifts the blade.
- Blade down while moving: cuts ground that sits above the tracks (8 cm below them, never past bedrock),
  carries up to 6 m³, fills ground that dips below the tracks from that load, spills extra ahead as a pile.
  Lifting the blade dumps the load. That pushes overburden, fills pits and builds ramps.
- JJ: dozing should never destroy gold. The blade cuts no deeper than the top of the pay gravel and never
  pushes pay piles; it strips overburden and moves waste/fill only (that is also how real placer mines use dozers).
