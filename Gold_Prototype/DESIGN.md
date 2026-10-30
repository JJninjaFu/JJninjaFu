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
