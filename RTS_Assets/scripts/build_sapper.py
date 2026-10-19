"""Builds the Sapper (engineer) squad member in both team colors plus his tools:
shovel, pickaxe and a sandbag prop for the ramp/patch abilities.

    python build_sapper.py <output_dir> [--no-render]
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
models = os.path.join(OUT, "Models")

sappers = {team: build_soldier(team, "Sapper") for team in TEAMS}
shovel = build_shovel()
pickaxe = build_pickaxe()
sandbag = build_sandbag()

for arm, body in sappers.values():
    export_character(arm, body, models)
    print(f"{body.name}: {len(body.data.polygons)} faces")
for o in (shovel, pickaxe, sandbag):
    export_prop(o, models)
    print(f"{o.name}: {len(o.data.polygons)} faces")


def pose_carry(arm, body):
    """Shovel over the right shoulder, pickaxe hanging from the left hand, mid-stride."""
    aim(arm, "upperarm_r", (-0.2, -0.3, -0.93))
    aim(arm, "lowerarm_r", (0.25, -0.55, 0.8))
    aim(arm, "upperarm_l", (0.2, 0.08, -0.98))
    aim(arm, "lowerarm_l", (0.12, -0.25, -0.96))
    aim(arm, "thigh_l", (0, -0.3, -0.95))
    aim(arm, "calf_l", (0, 0.05, -1))
    aim(arm, "thigh_r", (0, 0.22, -0.97))
    aim(arm, "calf_r", (0, 0.4, -0.92))
    aim(arm, "foot_r", (0, -0.8, -0.6))
    ground(arm, body)


def pose_haul(arm, body):
    """Shovel hanging from the right hand, left hand steadying the sandbag."""
    aim(arm, "upperarm_r", (-0.18, 0.02, -0.98))
    aim(arm, "lowerarm_r", (-0.08, -0.3, -0.95))
    aim(arm, "upperarm_l", (0.86, -0.43, 0.29))
    aim(arm, "lowerarm_l", (-0.81, 0.57, 0.15))
    aim(arm, "thigh_r", (-0.08, 0, -1))
    aim(arm, "thigh_l", (0.08, 0, -1))
    ground(arm, body)


if RENDER:
    setup_render()
    blue_arm, blue_body = sappers["Blue"]
    grey_arm, grey_body = sappers["Grey"]
    blue_arm.location, blue_arm.rotation_euler.z = (-50, 0, 0), math.radians(-12)
    grey_arm.location, grey_arm.rotation_euler.z = (60, 30, 0), math.radians(18)
    C.view_layer.update()
    pose_carry(blue_arm, blue_body)
    pose_haul(grey_arm, grey_body)

    bfwd = blue_arm.matrix_world.to_3x3() @ Vector((0, -1, 0))
    place(shovel, hand_point(blue_arm, "hand_r"), (0.15, -0.55, -0.82), (1, 0, 0))
    place(pickaxe, hand_point(blue_arm, "hand_l"), (0, 0, -1), -bfwd)
    grey_shovel = shovel.copy()
    C.collection.objects.link(grey_shovel)
    place(grey_shovel, hand_point(grey_arm, "hand_r"), (0, 0, 1), (0, 1, 0))

    # A small sandbag wall: the start of a ramp.
    for i, (x, y, z, yaw) in enumerate([(-30, 140, 0, 5), (20, 142, 0, -4), (70, 138, 0, 8),
                                       (-5, 140, 14, -6), (45, 141, 14, 3), (20, 139, 28, 0)]):
        bag = sandbag.copy()
        C.collection.objects.link(bag)
        bag.location = (x - 80, y, z)
        bag.rotation_euler.z = math.radians(yaw)
    sandbag.location = (0, 0, -1000)

    camera((170, -430, 170), (0, 40, 85), 42)
    render(os.path.join(OUT, "Previews", "sapper_hero.png"))
    camera((-25, -210, 160), (-45, 0, 130), 55)
    render(os.path.join(OUT, "Previews", "sapper_closeup.png"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Blend", "rts_sapper.blend"))
print("done")
