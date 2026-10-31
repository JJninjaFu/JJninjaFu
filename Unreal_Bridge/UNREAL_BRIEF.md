# Unreal brief: JJ's RTS project (IsometricWarfare)

Written by the Claude Code session on JJ's laptop, 2026-10-31, for the cloud session building
Bedrock Claim. Facts below come from reading the project and its git history, not from memory of
plans. Where something is only designed and not built, it says so.

## Corrections first

`RTS_Assets/DESIGN.md` says bedrock, base protection and engineers are working in the laptop
project. **They are not built.** They were discussed and written down as design on 2026-10-19,
and no code exists for any of them yet:

- **Bedrock:** not built. Craters can currently dig down without limit. The agreed design is a fixed
  world-height floor per point, so mountains can be shelled all the way down.
- **Base protection:** not built. Design: hardened zones where bedrock sits about 0.5 m under the
  surface, so craters there only leave a scar.
- **Engineers (patch craters, build ramps):** not built. Design: "crater in reverse" at a
  dirt-per-second rate (roughly 20 s to fill a shell crater, 1 to 2 minutes per ramp).

What is built and works is the deformable terrain itself, the units, combat and the camera, below.

## Engine and project

- **Unreal Engine 5.8.** Blueprint-only: there is no C++ module (`Source/` does not exist).
- **How I (laptop Claude) work in it:** through the editor's Model Context Protocol toolsets plus editor
  Python. I can create and rewrite Blueprint graphs, import assets, place actors, run Play-in-Editor
  and read logs. **I cannot compile C++.** If we add a C++ module, JJ has to build it on the laptop
  (Visual Studio or Live Coding). So "port as C++ components" is possible but costs JJ a build step
  per change. Blueprints first, C++ only where performance demands it, is my suggestion.
- **Started from** Epic's Cropout sample (village map, island generator plugin). All our own work
  lives in `/Game/RTS/`; the Cropout content is unused leftovers.
- **Plugins on:** GeometryScripting (the terrain depends on it), EnhancedInput, CommonUI, IKRig,
  AnimationLocomotionLibrary, AnimationWarping, AnimationBudgetAllocator, AudioModulation, modeling
  tools, plus the editor-only ModelContextProtocol / AllToolsets. Project plugins from the sample:
  IconBaker, IslandGenerator (unused by us).
- **Git:** local repository only, 46 commits, **no remote**. Nothing is on GitHub yet.
- **Size:** `Content/` is 844 MB, but our own folder `/Game/RTS` is 64 MB. Most of the rest is Cropout
  (`Environment` 551 MB, `Audio` 76 MB) plus the migrated mannequin and animations (`Characters`
  135 MB). Deleting unused Cropout content before any GitHub/LFS push would shrink it a lot.

## Deformable terrain (built, working)

- **Type:** chunked runtime heightfield made of Geometry Script dynamic meshes. Not voxels, not a
  Landscape at runtime.
- **Classes:** `BP_TerrainManager` (one per map) and `BP_TerrainChunk` (a DynamicMeshActor).
- **Authoring:** JJ hand-sculpts a normal Unreal Landscape in the editor (two plateaus, cliffs, gullies).
  At match start the manager spawns 32 m chunks over the Landscape's bounds (256 chunks on the
  current ~504 m map), and each chunk copies heights from it by line traces. Then the Landscape is
  destroyed. Chunks are built one per frame so Blueprint's loop limit isn't hit.
- **Chunk mesh:** 35 x 35 vertices at 1 m spacing, including an outer skirt ring lowered 4 m so seams
  between chunks never show gaps.
- **Data per vertex:** height only. There are **no ground layers, no material types, no grade values**
  yet. Bedrock Claim's overburden / pay gravel / bedrock layers and gold grade would be new data
  stored per chunk vertex.
- **Deformation:** `Crater_0` lowers vertices in a radius (radius 6 m, depth 2.5 m, smooth falloff),
  touching only the vertices inside the crater (about 8 ms per chunk). It then recomputes normals,
  rebuilds collision and re-registers the chunk with navigation. Debug key: C craters under the
  cursor. There is **no raise or pile function yet**, but raising is the same code with the sign flipped.
- **Navigation:** navmesh with dynamic runtime generation. After a crater, the affected chunk's navmesh
  rebuilds in about 2.5 s on worker threads. Units path into and out of shallow craters, and
  stacked craters get too steep to walk.
- **Cost to watch for Bedrock Claim:** every edit currently triggers a collision rebuild plus a
  navmesh rebuild for that chunk. A crater is one big edit. An excavator taking a bucket every few
  seconds is many small edits, so we would batch them (update the visible mesh per bucket, collision
  and navmesh every few seconds) rather than rebuild per bucket.
- **Material:** a placeholder slope-based grass/dirt material.

## Units and camera (built, working)

- **Soldiers:** `BP_Unit` (Character class) with the Meshy Gunner body. It uses a 23-bone skeleton with
  UE5 mannequin bone names and 14 retargeted GASP animations: idle, walk, run, sprint, crouch and ragdoll
  clips through a speed blend. There is also a tested pipeline for ActionForge clips fitted to the Gunner.
- **Orders:** box/click select (own team only), right-click move, double-right-click sprint
  (4 s burst, 10 s cooldown), right-click an enemy to attack it, hold right-click and drag to draw a
  formation line (Beyond All Reason / Zero-K style).
- **Combat:** hitscan rifles blocked by terrain, so craters and ridges are cover. Units auto-fire at the
  nearest visible enemy within 40 m, health 125, 4 hits to kill, ragdoll on death. Two teams, 6 vs 12
  on the test map.
- **Camera:** RTS pawn with a spring arm. WASD pan, Q/E rotate, wheel zoom, middle-drag pan,
  Alt+mouse tilt. It opens on a view JJ framed by hand, and holding Space switches to editor-style free fly.

## Multiplayer

**None built.** No replication and no RPCs. Commands are guarded by `HasAuthority`, so it's
single-machine only today. The planned first step was a listen-server test (one player hosts). Terrain
sync was designed but never built: replicate the list of terrain edit events, and every machine
re-applies them to the same base heights. Your v5 presence approach (stream rolling terrain edits)
is the same idea.

## Vehicles

**None in this project.** JJ has a separate Unreal project on the laptop with Chaos Vehicles: an
off-road and derby game, aiming at SnowRunner-style terrain deformation. So vehicle physics experience
exists, but nothing is in IsometricWarfare.

## How Bedrock Claim maps onto this

| Bedrock Claim (browser) | Unreal today | Gap |
|---|---|---|
| Heightfield terrain, 400 m map | Chunked heightfield, ~504 m map, hand-sculpted | Re-sculpt or generate the mesa, ring of claims and ridges |
| Ground layers + gold grade per cell | Height only | New per-vertex data (layer depths, grade) |
| Bedrock (undiggable) | Not built | Clamp digging at the bedrock height (small change) |
| Excavator digging buckets | Crater function (lowers a radius) | Smaller, bucket-sized cuts plus volume accounting |
| Piles with angle of repose | Not built | Raise function plus a slump pass |
| Water table / flooding | Not built | Water plane plus a "below water" check |
| Machines path around pits | Navmesh with dynamic rebuilds | Batch rebuilds; vehicle nav agent with a stricter slope limit |
| Crew, wages, wash plant, economy | Not built | New (Blueprints or GameState) |
| Click orders, boss view | RTS controller and camera | Reusable as is |
| Drive mode (Jimbo, 4x4) | Not built here | Chaos Vehicles (JJ has experience) |
| Shared world, 8 players | Not built | Listen server first; replicate terrain edit events |

## What I'd build first in Unreal

1. **Make a copy of the project for Bedrock Claim** (a git clone into its own folder) rather than
   re-pointing the RTS in place. The RTS stays playable, and both keep their history.
2. **Ground layers:** store layer depths and gold grade per chunk vertex, then add bedrock clamping
   to digging. This is the core data everything else uses.
3. **Bucket digging:** a small, volume-tracked cut with batched collision and nav rebuilds.
4. **Piles:** a raise function plus angle-of-repose slumping. The inverse also gives the RTS its
   engineers for free.
5. **Excavator as a unit:** click "dig here" like the browser's boss view, before any driving.
6. **Economy:** wash plant, crew and selling.
7. **Driving:** Chaos Vehicles for the 4x4 and loader.
8. **Listen-server multiplayer** with replicated terrain edits.

The browser build stays the design lab: try ideas there, then build the ones that work in Unreal.

## Getting the project to the cloud

Recommended before any push:

- Delete the unused Cropout content.
- Add a `.gitignore` for Binaries, Intermediate, Saved, DerivedDataCache and SourceArt (raw source files).
- Put `.uasset`/`.umap` under Git LFS.

Our own content is about 64 MB plus about 135 MB of mannequin and animations, which should fit the free LFS
quota. Not done yet: waiting on JJ.
