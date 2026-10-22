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

## Setting direction (evolving, latest wins)

- Fully invented world, Dawn of War-style freedom. Brass-era look is a starting point, not a commitment.
- Story frame: a civil war that keeps escalating for a century into a world war, eventually reaching orbit
  (space elevator, orbital bases that fund the ground armies).
- Inspirations: Dawn of War, the Foundation TV series (a long-ruling Empire vs. a society that comes to
  worship its founder). Borrow themes, not names, characters or specific designs.
- Faction idea: the Empire (professional soldiers, an Emperor hero whose presence buffs nearby troops ~15%)
  vs. the Faithful (cheaper militia who arm themselves and grow into zealots, Manor Lords-style).
- Vehicle idea: open-sided hover transport, armored glass front, carries ~2 squads, passengers can fire out
  the sides; hovers over craters that block wheels and feet.
- Game name candidates: Spittin' Brass (tagline "...and kickin' ass"), Mountains & Molehills, Dig In.
- Faction names below are placeholders ("Ashfall" is dropped).

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
- Sapper (engineer) in both team colors, shovel, pickaxe, sandbag prop. Shares the soldier skeleton.
- Skeleton uses UE5 mannequin bone names for retargeting. Rigid skinning (upgrade later).
- 2D concept art (Gemini): `Concept/meridian_federation_lineup.webp` (full roster) and `Concept/meridian_unit_select_mockup.webp` (Commander, Sapper, Crank-Gun Gunner on a unit-select screen). Use as reference for models and UI. `Concept/meridian_turntable_video.mp4` is an AI video of the same three: the target art style. `Concept/apose_*.jpg` are clean front A-pose images of the Gunner, Sapper and Commander, made as image-to-3D input.

## Image-to-3D pipeline (in progress)

1. Gemini makes a clean front A-pose image (see `Concept/apose_*.jpg`).
2. Meshy (free tier, Meshy 6 Lite, about 15k triangles) turns it into a textured `.glb`.
   Make sure the model shows colors before downloading: a file ending in `_generate` is the untextured shape.
3. `scripts/rig_meshy.py <in.glb> <out_dir> <Name>` reduces it, scales it to 180 cm, fits our UE5-named
   skeleton and binds it. Tested on the untextured Meshy Sapper: works (`Previews/meshy_sapper_rig_test.png`).
   Commander and Gunner also rigged (`Previews/meshy_gunner_commander_rig_test.png`).
4. Meshy's free tier would not give textured downloads, so `scripts/texture_project.py <in.glb> <front_image> <out.glb>`
   projects the A-pose image onto the mesh from the front and bakes a 2048 texture (arms are re-aligned to the
   image, edge colors bled outward, back of the head gets solid hair/cap colors). Then rig_meshy.py rigs it.
   **Done:** textured + rigged `Models/Meshy/SK_{Sapper,Gunner,Commander}.fbx` (+ .glb), previews
   `Previews/meshy_*_textured.png`. Known limit: backs mirror front details (buttons, apron).
   **Commander now uses Meshy's own texture** (downloaded as `..._texture.glb`, proper back): `Previews/meshy_commander_meshytex.png`.
   Sapper and Gunner still use the projected texture until their Meshy-textured files arrive.
5. Still to do: Ashfall (grey/crimson) versions, a back-view image per character to fix the backs.

## Next up (pick one)

- Mortar and crank gun models (capturable weapons)
- Better skinned base body
- Push the Unreal project to GitHub so cloud sessions can work on squads and capture code
