# RTS Design Notes

Living summary of decisions so far, so any Claude session can pick up where the last one left off.

## Core game (built on JJ's laptop in Unreal Engine)

- Multiplayer RTS. Inspirations: Company of Heroes, Dawn of War, Beyond All Reason, Zero-K, Defilade,
  Call to Arms: Gates of Hell, Homeworld: Deserts of Kharak.
- **Fully deformable terrain** down to an indestructible bedrock layer. Working in the laptop
  project, with a hand-sculpted height map: two big plateaus either player can climb. High ground
  gives visibility, and the plateaus are meant to get bombarded.
- Debug: pressing **C** on the terrain deforms it like a mortar or artillery hit. Gravity is fixed (stand-in
  units used to float).
- 5 blue cylinder stand-in units spawn on Play.
- **Base protection formula:** destruction is reduced near each player's base so a base can't be
  cratered into an unbuildable state.
- **Engineers:** patch terrain at a set rate per second (healing formula), and pile up dirt to build ramps.
  The Unreal project is not on GitHub yet, so cloud sessions can't see that code.

## Setting

- Parallel universe, not real history: alternate-history 1860s with light steampunk tech (brass optics,
  riveted steel, small steam devices, early rockets). This avoids taking sides in the Civil War, slavery
  and the wars against Native nations, and lets us borrow from any era.
- A Native-inspired faction is parked. If it ever happens, it must be a real faction with its own
  strengths (scouting, ambush, mobility), never just targets.

## Factions (working names)

| Faction | Look | Personality |
|---|---|---|
| Meridian Federation | Navy coats, sky blue trousers, gold trim, brass. Emblem: gold compass rose over a gear | Disciplined, industrial, defensive |
| Ashfall Republic | Ash grey coats, tan trousers, crimson trim, blackened leather. Emblem: crimson phoenix over crossed sabers | Aggressive, mobile, daring |

They start as mostly mirror armies with small differences and can grow asymmetric later.

## Squads (COH / Gates of Hell style, 2 to 9 men)

| Squad | Size | Role |
|---|---|---|
| Command Staff | 5 | Colonel, bugler, flag bearer, 2 aides. Rallies nearby troops |
| Line Rifle Company | 8 | Core infantry |
| Sapper Corps | 5 | Engineers: patch craters, build ramps |
| Crank-Gun Team | 4 | Hand-cranked multi-barrel machine gun |
| Mortar Team | 3 | Indirect fire, deforms terrain |
| Heavy Battery | 6 | Field cannon plus limber |
| Iron Horse Cavalry | 5 | Fast shock troops; **courage buff** to friendly infantry nearby |
| Sharpshooter Pair | 2 | Marksman plus spotter |

**Weapon capture:** crew-served weapons (cannon, mortar, crank gun, later flamethrowers) are separate
entities. Kill the crew and the weapon goes neutral; any squad can capture it. Craters can trap guns,
and engineers can dig them out or build a ramp.

## Assets so far (this folder)

- v1 rigged soldier in both team colors, saber, revolver, bronze field cannon. See `README.md`.
- Skeleton uses UE5 mannequin bone names for retargeting. Rigid skinning (upgrade later).
- 2D concept art: `Concept/meridian_federation_lineup.webp` (Gemini). Use as reference for models.

## Next up (pick one)

- Mortar and crank gun models (capturable weapons)
- Engineer with a shovel
- Better skinned base body
- Push the Unreal project to GitHub so cloud sessions can work on squads and capture code
