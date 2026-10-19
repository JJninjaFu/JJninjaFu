"""Builds the first RTS unit assets: a rigged 1860s-style soldier (two team colors),
a drawn cavalry saber, a revolver and a bronze field cannon.

Run with the Blender Python module (pip install bpy) or Blender itself:
    python build_assets.py <output_dir>
    blender -b -P build_assets.py -- <output_dir>

All modelling is in centimeters (scene unit scale 0.01) so FBX files import into
Unreal at the right size with a scale of 1.0. Characters face -Y (Blender front).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rts_common import *  # noqa: E402,F403  (resets the scene)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0] if args else "out")
RENDER = "--no-render" not in args
for sub in ("Models", "Previews", "Blend"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

soldiers = {team: build_soldier(team) for team in TEAMS}
saber = build_saber()
revolver = build_revolver()
cannon = build_cannon()

models = os.path.join(OUT, "Models")
for team, (arm, body) in soldiers.items():
    # UE strips an armature object named "Armature", leaving "root" as the top bone.
    others = [a for t, (a, _) in soldiers.items() if t != team]
    for a in others:
        a.name = a.name + "_tmp"
    arm.name = "Armature"
    export_fbx([arm, body], os.path.join(models, f"SK_Soldier_{team}.fbx"))
    export_glb([arm, body], os.path.join(models, f"SK_Soldier_{team}.glb"))
    arm.name = f"Armature_{team}"
    for a in others:
        a.name = a.name[:-4]
for o in (saber, revolver, cannon):
    export_fbx([o], os.path.join(models, f"{o.name}.fbx"))
    export_glb([o], os.path.join(models, f"{o.name}.glb"))

for team, (arm, body) in soldiers.items():
    print(f"{body.name}: {len(body.data.polygons)} faces, {len(body.data.vertices)} verts")
for o in (saber, revolver, cannon):
    print(f"{o.name}: {len(o.data.polygons)} faces, {len(o.data.vertices)} verts")


if RENDER:
    setup_render()
    blue_arm, blue_body = soldiers["Blue"]
    grey_arm, grey_body = soldiers["Grey"]
    blue_arm.location = (-55, 0, 0)
    blue_arm.rotation_euler.z = math.radians(-15)
    grey_arm.location = (55, 20, 0)
    grey_arm.rotation_euler.z = math.radians(15)
    C.view_layer.update()
    pose_charge(blue_arm, blue_body)
    pose_ready(grey_arm, grey_body)

    saber.location = (0, 0, 0)
    place(saber, hand_point(blue_arm, "hand_r"), (-0.1, 0.35, 1), (0, -1, 0))
    revolver_hero = revolver.copy()
    C.collection.objects.link(revolver_hero)
    fwd = blue_arm.matrix_world.to_3x3() @ Vector((0, -1, 0))
    place(revolver_hero, hand_point(blue_arm, "hand_l") + Vector((0, 0, -2)), (0, 0, 1), fwd)
    grey_saber = saber.copy()
    C.collection.objects.link(grey_saber)
    gfwd = grey_arm.matrix_world.to_3x3() @ Vector((0, -1, 0))
    place(grey_saber, hand_point(grey_arm, "hand_r"), gfwd * 0.85 + Vector((0, 0, -0.5)), (0, 0, 1))

    cannon.location = (40, 330, 0)
    cannon.rotation_euler.z = math.radians(-28)
    revolver.location = (0, 0, -1000)  # keep the export copy out of frame

    camera((210, -470, 175), (0, 40, 95), 45)
    render(os.path.join(OUT, "Previews", "hero_shot.png"))
    camera((-60, -190, 150), (-55, 0, 120), 60)
    render(os.path.join(OUT, "Previews", "closeup_blue.png"))

    # RTS camera: a squad of each side plus the gun.
    cannon.location = (0, 0, 0)
    cannon.rotation_euler.z = 0
    blue_arm.location, blue_arm.rotation_euler.z = (-60, -260, 0), 0
    grey_arm.location, grey_arm.rotation_euler.z = (40, -900, 0), math.pi
    saber.matrix_world = Matrix.Translation((0, 0, -1000))
    revolver_hero.matrix_world = Matrix.Translation((0, 0, -1000))
    grey_saber.matrix_world = Matrix.Translation((0, 0, -1000))
    for i, (x, y) in enumerate([(-170, -200), (-120, -330), (60, -300), (140, -210), (190, -340)]):
        clone_soldier(blue_arm, blue_body, (x, y, 0), math.radians((i * 23) % 40 - 20))
    for i, (x, y) in enumerate([(-150, -980), (-60, -1060), (130, -1000), (210, -1080), (-210, -1090)]):
        clone_soldier(grey_arm, grey_body, (x, y, 0), math.pi + math.radians((i * 17) % 30 - 15))
    camera((900, -1500, 1300), (0, -550, 0), 40)
    render(os.path.join(OUT, "Previews", "rts_view.png"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Blend", "rts_assets.blend"))
print("done")
