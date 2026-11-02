# Combat spec for Unreal (from the browser build, Bedrock Claim v7)

The browser code can't be copied into Unreal, but every mechanic below is a small Blueprint built from
pieces the RTS already has (hitscan rifles blocked by terrain, the Crater function, Character movement).
Build them in this order; each one is playable on its own. Numbers are the browser's tuned values.

## 1. Cursor aim (SYNTHETIK style)
- Each tick: `Get Hit Result Under Cursor by Channel` (Visibility) gives the aim point on the terrain.
- Rotate the hero to face it (yaw only): `Find Look at Rotation`, zero pitch and roll, `Set Actor Rotation`
  (or `Set Control Rotation` with `Use Controller Rotation Yaw`).
- Show a crosshair cursor (Show Mouse Cursor, crosshair type) while on foot.
- Movement stays on WASD relative to the camera, independent of aim (twin-stick feel).

## 2. Revolver (left mouse, hold to keep firing)
- Fire interval 0.28 s (a timer or a "next shot time" float).
- Direction = aim point minus muzzle, flattened, plus random yaw spread: 0.02 rad standing,
  0.07 rad sprinting.
- `Line Trace by Channel` from muzzle (about 1.6 m up) along that direction, 40 m. Terrain chunks block it,
  so dirt and berms are cover for free (same as the RTS rifles).
- Hit a pawn: `Apply Damage` 25. Health 100, so 4 hits. Regenerate 2 health per second.
- Tracer: a short-lived Niagara beam or a spline mesh from muzzle to hit point (about 0.09 s).
- Miss into dirt: a small dust puff at the hit point.

## 3. Sprint (hold Shift, no cooldown)
- `Character Movement > Max Walk Speed`: walk 600 cm/s, sprint 1100 cm/s.
- Spread goes up while sprinting (above).

## 4. Gold weight
- Carried gold: 1 lb per gram (black-sand concentrate until the Assay Office cleans it).
- Speed multiplier: 1.0 up to 40 lb, then falls linearly by 0.6 per 100 lb, never below 0.35.
- No sprint above 100 lb.

## 5. Satchel charge (right mouse or G, 8 s cooldown)
- Throw at the aim point, clamped to 20 m. An actor with `Projectile Movement` (lob it), or
  `Suggest Projectile Velocity` to land exactly on the point. About 0.9 s flight.
- On landing: call the existing `Crater_0` (radius 3.2 m, depth 1.3 m, smooth falloff; clamp at bedrock
  once bedrock exists), then `Apply Radial Damage with Falloff`: 90 at the center to 0 at 5.5 m, hurting the
  thrower too.
- Camera shake, smoke and dust Niagara, a big boom sound.

## 6. Berm (B, 9 s cooldown)
- The inverse of the crater: raise terrain in 5 bumps across a 5 m line, 2.6 m in front of the hero,
  each bump about 4.2 cubic meters with a soft falloff. Aim for about 1.5 m tall so it blocks shots.
- Needs a `Raise` version of the crater code (same function with the sign flipped) plus the slope
  slump pass from `CLOUD_REPLY.md` so it settles like a dirt pile. The same code later gives engineers ramps.

## 7. Death and dropped gold
- At 0 health: ragdoll (already built for soldiers), drop half the carried gold as a pickup actor
  (overlap sphere 2.2 m adds it to whoever walks over it), respawn at your claim after 6 s.

## 8. Bandits (for solo testing)
- Two AI hero clones spawn about 24 m away when the player carries more than 3 lb near town.
- Behavior Tree or simple tick: approach until within 18 m with line of sight, back off under 10 m,
  strafe sideways (switch direction every 0.8 to 1.8 s), shoot every 0.9 to 1.5 s from up to 32 m
  with hit chance `clamp(0.9 - distance_m * 0.016, 0.08, 0.92) * 0.55`, lower if the target is sprinting.
- 75 health, 14 damage per hit, $400 bounty.

## Later (multiplayer)
- On a listen server, the shooter's line trace runs on the server (Server RPC with aim direction),
  damage is applied there, and health is replicated. The browser trusts the shooter; Unreal can do better.
