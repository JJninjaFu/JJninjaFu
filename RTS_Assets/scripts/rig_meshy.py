"""Rigs an AI-generated (Meshy/Tripo) A-pose character with our UE5-mannequin skeleton.

    python rig_meshy.py <input.glb> <output_dir> <Name> [--tris 15000] [--no-render]

Steps: import, scale to 180 cm with the feet at the origin, reduce to the target triangle
count, measure the joints from the mesh itself, build the skeleton, bind with automatic
weights, export FBX + GLB, and render a clay test pose to check the deformation.
Assumes the character faces -Y (front) in A-pose, which is how Meshy exports glTF.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rts_common import *  # noqa: E402,F403  (resets the scene)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, OUT, NAME = os.path.abspath(args[0]), os.path.abspath(args[1]), args[2]
TRIS = int(args[args.index("--tris") + 1]) if "--tris" in args else 15000
RENDER = "--no-render" not in args
HEIGHT = 180.0
for sub in ("Models", "Previews"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

# ---------------------------------------------------------------- import + normalize
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in C.scene.objects if o.type == "MESH"]
select_only(meshes)
if len(meshes) > 1:
    bpy.ops.object.join()
body = C.active_object
body.parent = None
body.name = body.data.name = f"SK_{NAME}"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(C.scene.objects):
    if o is not body:
        D.objects.remove(o)

vs = [v.co for v in body.data.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
s = HEIGHT / (hi.z - lo.z)
body.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
body.data.update()

tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
if tris > TRIS:
    mod = body.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = TRIS / tris
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
print(f"{body.name}: {tris} -> {len(body.data.polygons)} faces")

# ---------------------------------------------------------------- measure joints
V = [v.co.copy() for v in body.data.vertices]


def centroid(pred, fallback):
    pts = [v for v in V if pred(v)]
    if not pts:
        return Vector(fallback)
    return sum(pts, Vector()) / len(pts)


def near(p, r):
    p = Vector(p)
    return centroid(lambda v: (v - p).length < r, p)


H = HEIGHT
joints = {}
for side, sgn in (("l", 1), ("r", -1)):
    # The hand tip is the farthest point out to the side; split the arm by human proportions.
    tip = max((v for v in V if v.x * sgn > 0 and v.z > 0.45 * H), key=lambda v: v.x * sgn)
    sh = Vector((sgn * 0.105 * H, 0, 0.81 * H))
    sh.y = near(sh, 6).y
    arm = tip - sh
    el = near(sh + arm * (30 / 74), 6)
    wr = near(sh + arm * (56 / 74), 5)
    hand_end = wr + (tip - wr) * 0.6
    ankle_slice = centroid(lambda v: v.x * sgn > 2 and 0.04 * H < v.z < 0.10 * H, (sgn * 10, 0, 9))
    toe = min((v for v in V if v.x * sgn > 2 and v.z < 0.04 * H), key=lambda v: v.y)
    ank = Vector((ankle_slice.x, ankle_slice.y + 2, 0.05 * H))
    hip = Vector((ank.x, near((ank.x, 0, 0.52 * H), 8).y, 0.52 * H))
    knee = Vector((ank.x, near((ank.x, 0, 0.28 * H), 7).y, 0.28 * H))
    ball = Vector((ank.x, (ank.y + toe.y) / 2 - 2, 0.012 * H))
    toe_pt = Vector((ank.x, toe.y + 2, 0.012 * H))
    joints[side] = dict(sh=sh, el=el, wr=wr, he=hand_end, hip=hip, knee=knee, ank=ank, ball=ball, toe=toe_pt)

cy = near((0, 0, 0.62 * H), 10).y
z = lambda f: f * H  # noqa: E731
spine = [Vector((0, cy, z(f))) for f in (0.54, 0.585, 0.655, 0.73, 0.82, 0.86, 0.985)]
bones = [
    ("root", (0, 0, 0), (0, 0, 10), None),
    ("pelvis", spine[0], spine[1], "root"),
    ("spine_01", spine[1], spine[2], "pelvis"),
    ("spine_02", spine[2], spine[3], "spine_01"),
    ("spine_03", spine[3], spine[4], "spine_02"),
    ("neck_01", spine[4], spine[5], "spine_03"),
    ("head", spine[5], spine[6], "neck_01"),
]
for side, sgn in (("l", 1), ("r", -1)):
    j = joints[side]
    bones += [
        (f"clavicle_{side}", Vector((sgn * 3, j["sh"].y, j["sh"].z)), j["sh"], "spine_03"),
        (f"upperarm_{side}", j["sh"], j["el"], f"clavicle_{side}"),
        (f"lowerarm_{side}", j["el"], j["wr"], f"upperarm_{side}"),
        (f"hand_{side}", j["wr"], j["he"], f"lowerarm_{side}"),
        (f"thigh_{side}", j["hip"], j["knee"], "pelvis"),
        (f"calf_{side}", j["knee"], j["ank"], f"thigh_{side}"),
        (f"foot_{side}", j["ank"], j["ball"], f"calf_{side}"),
        (f"ball_{side}", j["ball"], j["toe"], f"foot_{side}"),
    ]

arm_data = D.armatures.new(f"Armature_{NAME}")
arm = D.objects.new(f"Armature_{NAME}", arm_data)
C.collection.objects.link(arm)
C.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for bname, head, tail, parent in bones:
    eb = arm_data.edit_bones.new(bname)
    eb.head, eb.tail, eb.roll = head, tail, 0
    if parent:
        eb.parent = arm_data.edit_bones[parent]
        eb.use_connect = (Vector(eb.parent.tail) - Vector(head)).length < 0.01 and bname != "pelvis"
bpy.ops.object.mode_set(mode="OBJECT")
for bname, head, tail, _ in bones:
    print(f"  {bname:12s} {tuple(round(c, 1) for c in head)} -> {tuple(round(c, 1) for c in tail)}")

# ---------------------------------------------------------------- bind
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
arm.select_set(True)
C.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
unweighted = sum(1 for v in body.data.vertices if not any(g.weight > 0.01 for g in v.groups))
print(f"unweighted verts: {unweighted} / {len(body.data.vertices)}")

# Clean tiny weights and keep at most 4 influences per vertex (what game engines expect).
select_only([body])
bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)

models = os.path.join(OUT, "Models")
old = arm.name
arm.name = "Armature"
select_only([arm, body])
bpy.ops.export_scene.fbx(
    filepath=os.path.join(models, f"{body.name}.fbx"), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_NONE", object_types={"ARMATURE", "MESH"}, mesh_smooth_type="FACE",
    add_leaf_bones=False, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X",
    axis_forward="-Z", axis_up="Y", path_mode="COPY", embed_textures=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(models, f"{body.name}.glb"), use_selection=True,
                          export_format="GLB", export_animations=False)
arm.name = old

# ---------------------------------------------------------------- deformation test render
if RENDER:
    if not body.data.materials:
        body.data.materials.append(mat("M_Clay", (0.72, 0.70, 0.66), 0.6))
    setup_render()
    scene.cycles.samples = 32
    poses = {
        "rest": {},
        "stride": {"thigh_l": (0.05, -0.45, -0.89), "calf_l": (0, 0.05, -1), "thigh_r": (-0.05, 0.35, -0.94),
                   "calf_r": (0, 0.6, -0.8), "upperarm_r": (-0.3, -0.5, 0.81), "lowerarm_r": (-0.1, -0.85, 0.5),
                   "upperarm_l": (0.15, 0.3, -0.94)},
    }
    clones = []
    for i, (pname, pose) in enumerate(poses.items()):
        a2, b2 = (arm, body) if i == 0 else clone_soldier(arm, body, (0, 0, 0), 0)
        a2.location = (-55 + i * 110, 0, 0)
        C.view_layer.update()
        for bname, d in pose.items():
            aim(a2, bname, d)
        ground(a2, b2)
    camera((80, -420, 150), (0, 0, 90), 40)
    render(os.path.join(OUT, "Previews", f"{NAME}_rig_test_front.png"))
    camera((420, -160, 140), (0, 0, 90), 40)
    render(os.path.join(OUT, "Previews", f"{NAME}_rig_test_side.png"))
print("done")
