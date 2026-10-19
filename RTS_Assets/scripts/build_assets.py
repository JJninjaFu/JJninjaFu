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

import bpy  # must come before bmesh when using the bpy module
import bmesh
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(args[0] if args else "out")
RENDER = "--no-render" not in args
for sub in ("Models", "Previews", "Blend"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

C = bpy.context
D = bpy.data

# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = C.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01
scene.unit_settings.length_unit = "CENTIMETERS"


def mat(name, color, rough=0.6, metal=0.0):
    m = D.materials.get(name)
    if m:
        return m
    m = D.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


SKIN = mat("M_Skin", (0.62, 0.42, 0.30), 0.55)
LEATHER = mat("M_Leather", (0.035, 0.03, 0.025), 0.45)
BRASS = mat("M_Brass", (0.75, 0.55, 0.20), 0.3, 1.0)
STEEL = mat("M_Steel", (0.60, 0.62, 0.65), 0.25, 1.0)
BLUED = mat("M_BluedSteel", (0.06, 0.07, 0.09), 0.35, 1.0)
WALNUT = mat("M_Walnut", (0.09, 0.04, 0.02), 0.45)
HAIR = mat("M_Hair", (0.10, 0.06, 0.03), 0.8)
EYE = mat("M_Eye", (0.02, 0.02, 0.02), 0.3)
BRONZE = mat("M_Bronze", (0.55, 0.36, 0.17), 0.35, 1.0)
IRON = mat("M_Iron", (0.05, 0.05, 0.05), 0.55, 0.8)
CARRIAGE = mat("M_CarriageWood", (0.20, 0.23, 0.11), 0.7)

TEAMS = {
    # Team colors: coat, trousers, hat, trim. Swap via material instances in UE.
    "Blue": ((0.03, 0.05, 0.16), (0.22, 0.32, 0.50), (0.03, 0.05, 0.16), (0.75, 0.55, 0.20)),
    "Grey": ((0.30, 0.30, 0.31), (0.36, 0.32, 0.24), (0.30, 0.30, 0.31), (0.55, 0.08, 0.06)),
}

# ---------------------------------------------------------------- primitives
UP = Vector((0, 0, 1))


def _finish(obj, name, material):
    obj.name = name
    obj.data.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def cyl(name, p1, p2, r1, r2, material, verts=12):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length,
                                    location=(p1 + p2) / 2)
    o = C.active_object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = UP.rotation_difference(d)
    return _finish(o, name, material)


def box(name, p1, p2, sx, sy, material):
    """Box spanning p1->p2, sx wide and sy thick across that axis."""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(p1 + p2) / 2)
    o = C.active_object
    o.scale = (sx, sy, d.length)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = UP.rotation_difference(d)
    return _finish(o, name, material)


def ball(name, loc, radii, material, segs=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=1, location=loc)
    o = C.active_object
    o.scale = radii
    return _finish(o, name, material)


def ellipsoid_between(name, p1, p2, w, t, material):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    o = ball(name, (p1 + p2) / 2, (w / 2, t / 2, d.length / 2), material)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = UP.rotation_difference(d)
    return o


def torus(name, loc, major, minor, rot, material, segs=32, minor_segs=6):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=segs,
                                     minor_segments=minor_segs, location=loc, rotation=rot)
    return _finish(C.active_object, name, material)


def lathe(name, profile, material, segs=24):
    """Revolve (axial, radius) pairs around the -Y axis (axial 0 at origin)."""
    me = D.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for a, r in profile:
        ring = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(ang), -a, r * math.sin(ang))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = D.objects.new(name, me)
    C.collection.objects.link(o)
    me.materials.append(material)
    return o


def join(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    C.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    o = C.active_object
    o.name = name
    o.data.name = name
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    # Merge identical material slots left over from joining.
    bpy.ops.object.select_all(action="DESELECT")
    return o


def transform_parts(parts, matrix):
    for p in parts:
        p.matrix_world = matrix @ p.matrix_world


# ---------------------------------------------------------------- skeleton
# Bone names follow the UE5 mannequin so the IK Retargeter auto-maps them.
def mirror(p, s):
    return (p[0] * s, p[1], p[2])


SHOULDER, ELBOW, WRIST, HAND_END = (20, 0, 147), (41, 0, 126), (59.4, 0, 107.6), (65.8, 0, 101.2)
HIP, KNEE, ANKLE, BALL, TOE = (10, 0, 95), (10, 0, 50), (10, 0, 9), (10, -10, 2), (10, -18, 2)

BONES = [  # name, head, tail, parent
    ("root", (0, 0, 0), (0, 0, 10), None),
    ("pelvis", (0, 0, 97), (0, 0, 105), "root"),
    ("spine_01", (0, 0, 105), (0, 0, 118), "pelvis"),
    ("spine_02", (0, 0, 118), (0, 0, 132), "spine_01"),
    ("spine_03", (0, 0, 132), (0, 0, 149), "spine_02"),
    ("neck_01", (0, 0, 149), (0, 0, 157), "spine_03"),
    ("head", (0, 0, 157), (0, 0, 178), "neck_01"),
]
for side, s in (("l", 1), ("r", -1)):
    BONES += [
        (f"clavicle_{side}", mirror((3, 0, 147), s), mirror(SHOULDER, s), "spine_03"),
        (f"upperarm_{side}", mirror(SHOULDER, s), mirror(ELBOW, s), f"clavicle_{side}"),
        (f"lowerarm_{side}", mirror(ELBOW, s), mirror(WRIST, s), f"upperarm_{side}"),
        (f"hand_{side}", mirror(WRIST, s), mirror(HAND_END, s), f"lowerarm_{side}"),
        (f"thigh_{side}", mirror(HIP, s), mirror(KNEE, s), "pelvis"),
        (f"calf_{side}", mirror(KNEE, s), mirror(ANKLE, s), f"thigh_{side}"),
        (f"foot_{side}", mirror(ANKLE, s), mirror(BALL, s), f"calf_{side}"),
        (f"ball_{side}", mirror(BALL, s), mirror(TOE, s), f"foot_{side}"),
    ]


def build_armature(name):
    arm_data = D.armatures.new(name)
    arm = D.objects.new(name, arm_data)
    C.collection.objects.link(arm)
    C.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for bname, head, tail, parent in BONES:
        eb = arm_data.edit_bones.new(bname)
        eb.head, eb.tail = head, tail
        eb.roll = 0
        if parent:
            eb.parent = arm_data.edit_bones[parent]
            eb.use_connect = Vector(eb.parent.tail) == Vector(head) and bname != "pelvis"
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


# ---------------------------------------------------------------- soldier
def build_soldier(team):
    coat_c, trou_c, hat_c, trim_c = TEAMS[team]
    COAT = mat(f"M_Coat_{team}", coat_c, 0.85)
    TROU = mat(f"M_Trousers_{team}", trou_c, 0.85)
    HAT = mat(f"M_Hat_{team}", hat_c, 0.8)
    TRIM = mat(f"M_Trim_{team}", trim_c, 0.5)
    parts = []  # (object, bone)

    def add(o, bone):
        parts.append((o, bone))
        return o

    # Torso, coat skirt, belt
    o = add(cyl("coat", (0, 0, 95), (0, 0, 150), 16, 18.5, COAT, 16), "spine_02")
    o.scale.y *= 0.62
    o = add(cyl("chest", (0, 0, 128), (0, 0, 150), 17.6, 18.6, COAT, 16), "spine_03")
    o.scale.y *= 0.625
    o = add(cyl("skirt", (0, 0, 68), (0, 0, 98), 20, 16.5, COAT, 16), "pelvis")
    o.scale.y *= 0.78
    o = add(cyl("belt", (0, 0, 100), (0, 0, 106), 17.2, 17.2, LEATHER, 16), "pelvis")
    o.scale.y *= 0.66
    add(box("buckle", (0, -11.4, 101), (0, -11.4, 105.5), 6.5, 0.8, BRASS), "pelvis")
    for z in range(110, 146, 7):
        for x in (-4.5, 4.5):
            add(ball("button", (x, -11.3 - (z - 110) * 0.012, z), (1.0, 0.6, 1.0), BRASS, 8, 6), "spine_02")
    add(box("strap", (-16, -12.2, 146), (15, -11.8, 101), 5, 0.6, LEATHER), "spine_02")
    add(box("strap_back", (-16, 12.2, 146), (15, 11.8, 101), 5, 0.6, LEATHER), "spine_02")
    add(box("cartridge_box", (17, 6, 96), (17, 6, 108), 9, 5, LEATHER), "pelvis")
    add(cyl("collar", (0, 0, 148), (0, 0, 155), 7.5, 7.0, COAT), "neck_01")
    add(cyl("collar_trim", (0, 0, 153.6), (0, 0, 155.2), 7.2, 7.1, TRIM), "neck_01")

    # Arms
    for side, s in (("l", 1), ("r", -1)):
        sh, el, wr, he = (mirror(p, s) for p in (SHOULDER, ELBOW, WRIST, HAND_END))
        add(ball(f"shoulder_{side}", mirror((18.5, 0, 145), s), (7, 6.2, 6.5), COAT), f"clavicle_{side}")
        add(box(f"epaulette_{side}", mirror((14, 0, 150.5), s), mirror((23, 0, 147), s), 9, 2, TRIM),
            f"clavicle_{side}")
        add(cyl(f"upperarm_{side}", sh, el, 5.6, 4.8, COAT), f"upperarm_{side}")
        add(ball(f"elbow_{side}", el, (4.8, 4.8, 4.8), COAT, 10, 6), f"lowerarm_{side}")
        add(cyl(f"forearm_{side}", el, wr, 4.8, 4.4, COAT), f"lowerarm_{side}")
        cuff = Vector(wr) + (Vector(el) - Vector(wr)).normalized() * 3
        add(cyl(f"cuff_{side}", cuff, wr, 4.9, 4.9, TRIM), f"lowerarm_{side}")
        add(ellipsoid_between(f"hand_{side}", wr, Vector(he) + (Vector(he) - Vector(wr)) * 0.25, 5.4,
                              3.6, SKIN), f"hand_{side}")

        # Legs, boots
        hip, kn, an = (mirror(p, s) for p in (HIP, KNEE, ANKLE))
        add(cyl(f"thigh_{side}", hip, kn, 9, 6.6, TROU), f"thigh_{side}")
        add(ball(f"knee_{side}", kn, (6.6, 6.6, 6.6), TROU, 10, 6), f"calf_{side}")
        add(cyl(f"calf_{side}", kn, mirror((10, 0, 28), s), 6.6, 5.6, TROU), f"calf_{side}")
        add(cyl(f"boot_{side}", mirror((10, 0.5, 0), s), mirror((10, 0, 31), s), 6.0, 6.3, LEATHER),
            f"calf_{side}")
        add(ellipsoid_between(f"foot_{side}", mirror((10, 4, 3.5), s), mirror((10, -16, 3.5), s), 10,
                              7, LEATHER), f"foot_{side}")
        add(box(f"sole_{side}", mirror((10, 5, 0.75), s), mirror((10, -15, 0.75), s), 10, 1.5, LEATHER),
            f"ball_{side}")

    # Head
    add(cyl("neck", (0, 0, 150), (0, 0, 160), 5.6, 5.2, SKIN), "neck_01")
    add(ball("head", (0, -0.5, 166), (9.3, 10.3, 11.3), SKIN, 16, 10), "head")
    add(cyl("nose", (0, -9.6, 166.5), (0, -12.4, 163.6), 1.7, 0.9, SKIN, 8), "head")
    add(ball("eye_l", (3.4, -9.2, 168), (1.1, 0.8, 1.1), EYE, 8, 6), "head")
    add(ball("eye_r", (-3.4, -9.2, 168), (1.1, 0.8, 1.1), EYE, 8, 6), "head")
    add(ball("brow", (0, -9.3, 170.2), (6.2, 1.2, 0.8), HAIR, 10, 6), "head")
    add(ball("moustache", (0, -10.2, 161.4), (4.8, 1.3, 1.1), HAIR, 10, 6), "head")
    add(ball("ear_l", (9.2, 0, 166), (1.3, 2.4, 3.2), SKIN, 8, 6), "head")
    add(ball("ear_r", (-9.2, 0, 166), (1.3, 2.4, 3.2), SKIN, 8, 6), "head")
    add(ball("hair_back", (0, 3.0, 166), (9.4, 8.0, 9.5), HAIR, 14, 8), "head")

    # Kepi: built upright at the origin, then tilted onto the head.
    crown = cyl("kepi_crown", (0, 0, 0), (0, 0, 12.5), 10.4, 9.0, HAT, 20)
    crown.matrix_world = Matrix.Rotation(0.22, 4, "X") @ crown.matrix_world
    band = cyl("kepi_band", (0, 0, 0.6), (0, 0, 3.0), 10.65, 10.55, TRIM, 20)
    visor = cyl("kepi_visor", (0, 0, 0), (0, 0, 0.8), 7.0, 7.0, LEATHER, 16)
    visor.scale = (1.15, 0.75, 1)
    visor.location = (0, -8.8, 0.5)
    visor.matrix_world = Matrix.Translation((0, -8.8, 0.5)) @ Matrix.Rotation(0.35, 4, "X") @ \
        Matrix.Translation((0, 8.8, -0.5)) @ visor.matrix_world
    badge = ball("kepi_badge", (0, -10.6, 5.5), (2.2, 0.6, 1.6), BRASS, 10, 6)
    transform_parts([crown, band, visor, badge],
                    Matrix.Translation((0, -0.3, 170.2)) @ Matrix.Rotation(0.06, 4, "X"))
    for o in (crown, band, visor, badge):
        add(o, "head")

    # Sheathed saber on the left hip, holster with revolver on the right.
    top, bot = Vector((21, -2, 98)), Vector((27, 24, 26))
    dirn = (bot - top).normalized()
    add(cyl("scabbard", top, bot, 1.9, 1.4, STEEL, 8), "pelvis")
    add(cyl("scabbard_throat", top, top + dirn * 3, 2.1, 2.1, BRASS, 8), "pelvis")
    add(cyl("sheathed_grip", top - dirn * 1.5, top - dirn * 12, 1.4, 1.5, LEATHER, 8), "pelvis")
    add(box("sheathed_guard", top - dirn * 1.0, top - dirn * 2.0, 5, 3, BRASS), "pelvis")
    add(ball("sheathed_pommel", top - dirn * 12.5, (1.7, 1.7, 1.7), BRASS, 8, 6), "pelvis")
    add(box("holster", (-19.5, -3, 84), (-19.5, -1, 100), 5, 9, LEATHER), "pelvis")
    add(box("holster_grip", (-19.5, -1.5, 100), (-19.5, 1.5, 106), 2.6, 3.2, WALNUT), "pelvis")

    for o, bone in parts:
        o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)), 1.0, "REPLACE")
    body = join([o for o, _ in parts], f"SK_Soldier_{team}")

    arm = build_armature(f"Armature_{team}")
    body.parent = arm
    body.modifiers.new("Armature", "ARMATURE").object = arm
    return arm, body


# ---------------------------------------------------------------- weapons
def build_saber():
    """Cavalry saber, origin at the grip center, blade along +Z, edge toward -Y."""
    me = D.meshes.new("SM_Saber_blade")
    bm = bmesh.new()
    n, length = 14, 86.0
    stations = []
    for i in range(n + 1):
        t = i / n
        z = 7 + t * length
        y = 5.0 * t * t  # curve back toward the spine
        w = 2.8 * (1 - 0.35 * t) if i < n else 0.25
        th = 0.35 if i < n else 0.08
        stations.append([bm.verts.new((th, y, z)), bm.verts.new((-th, y, z)), bm.verts.new((0, y - w, z))])
    for a, b in zip(stations, stations[1:]):
        bm.faces.new((a[0], b[0], b[2], a[2]))
        bm.faces.new((a[2], b[2], b[1], a[1]))
        bm.faces.new((a[1], b[1], b[0], a[0]))
    bm.faces.new(stations[0])
    bm.faces.new(list(reversed(stations[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    blade = D.objects.new("SM_Saber_blade", me)
    C.collection.objects.link(blade)
    me.materials.append(STEEL)
    parts = [
        blade,
        cyl("grip", (0, 0, -6), (0, 0, 6), 1.5, 1.35, LEATHER, 10),
        box("guard", (0, 1.5, 6), (0, -5.5, 7.2), 1.2, 7.0, BRASS),
        ball("pommel", (0, 0, -6.6), (1.9, 2.2, 1.6), BRASS, 10, 6),
        cyl("knuckle_bow_a", (0, -1.2, -6.8), (0, -5.0, -2.5), 0.45, 0.45, BRASS, 6),
        cyl("knuckle_bow_b", (0, -5.0, -2.5), (0, -5.0, 6.5), 0.45, 0.45, BRASS, 6),
    ]
    return join(parts, "SM_Saber")


def build_revolver():
    """1860-style revolver, origin at the grip, barrel along -Y."""
    parts = [
        box("grip", (0, 3.4, -5), (0, 1.0, 4.8), 2.8, 3.4, WALNUT),
        box("frame", (0, 2.0, 6.5), (0, -6.5, 6.5), 2.4, 4.4, BLUED),
        cyl("drum", (0, -1.8, 7.2), (0, -6.8, 7.2), 2.2, 2.2, BLUED, 12),
        cyl("barrel", (0, -6.8, 8.0), (0, -27, 8.0), 1.05, 0.95, BLUED, 8),
        cyl("rammer", (0, -7.5, 6.2), (0, -22, 6.2), 0.5, 0.5, BLUED, 6),
        box("hammer", (0, 2.2, 8.0), (0, 1.6, 10.5), 1.0, 1.0, BLUED),
        ball("front_sight", (0, -26.2, 9.0), (0.25, 0.4, 0.35), BRASS, 6, 4),
        torus("trigger_guard", (0, -2.2, 3.4), 1.7, 0.25, (0, math.pi / 2, 0), BRASS, 16, 4),
        box("trigger", (0, -1.8, 3.0), (0, -1.4, 5.0), 0.4, 0.5, BLUED),
    ]
    return join(parts, "SM_Revolver")


# ---------------------------------------------------------------- cannon
def build_cannon():
    """12-pdr 'Napoleon'-style bronze field gun. Muzzle toward -Y, trail toward +Y."""
    axle_z, bore_z = 73.0, 101.0
    profile = [  # (distance from breech face, radius) in cm
        (-14, 0), (-14, 2.5), (-12.5, 4.2), (-10.5, 3.6), (-8, 2.2), (-5, 2.4), (-2, 9.0),
        (0, 13.2), (0, 14.4), (4, 14.6), (5, 13.6), (60, 12.4), (140, 9.6), (150, 9.8),
        (156, 10.8), (163, 11.2), (166, 10.6), (168, 10.2), (168, 5.9), (150, 5.9), (150, 0),
    ]
    barrel = lathe("barrel", profile, BRONZE, 28)
    barrel.location = (0, 70, bore_z)
    parts = [barrel, cyl("trunnions", (-25, 0, bore_z), (25, 0, bore_z), 5.8, 5.8, BRONZE, 14)]

    # Carriage
    slope_a, slope_b = Vector((0, -35, 92)), Vector((0, 85, 70))
    for x in (20, -20):
        parts.append(box("cheek", slope_a + Vector((x, 0, 0)), slope_b + Vector((x, 0, 0)), 8, 32, CARRIAGE))
        parts.append(box("cap_square", (x, -6, bore_z + 2), (x, 6, bore_z + 2), 9.5, 3, IRON))
    parts += [
        box("trail", (0, 55, 76), (0, 315, 14), 30, 17, CARRIAGE),
        box("trail_plate", (0, 300, 18.5), (0, 318, 14.5), 31, 3, IRON),
        torus("lunette", (0, 322, 15), 4.0, 1.0, (0, 0, 0), IRON, 16, 4),
        box("axle_tree", (-72, 0, axle_z), (72, 0, axle_z), 13, 13, CARRIAGE),
        cyl("elev_screw", (0, 74, 72), (0, 74, 90), 1.6, 1.6, IRON, 8),
        cyl("elev_handle", (-7, 74, 78), (7, 74, 78), 0.7, 0.7, IRON, 6),
        box("transom", (-20, 30, 82), (20, 30, 82), 10, 14, CARRIAGE),
        box("trail_handle", (-22, 270, 26), (22, 270, 26), 2, 2, IRON),
    ]
    # Wheels
    for x in (80, -80):
        s = 1 if x > 0 else -1
        parts += [
            cyl("axle_arm", (s * 70, 0, axle_z), (s * 94, 0, axle_z), 4.2, 4.2, IRON, 10),
            cyl("hub", (s * 70, 0, axle_z), (s * 92, 0, axle_z), 11, 7.5, CARRIAGE, 14),
            cyl("hub_band", (s * 78, 0, axle_z), (s * 80, 0, axle_z), 11.5, 11.5, IRON, 14),
            torus("felloe", (x, 0, axle_z), 66, 4.5, (0, math.pi / 2, 0), CARRIAGE, 40, 4),
            torus("tire", (x, 0, axle_z), 70.6, 1.9, (0, math.pi / 2, 0), IRON, 40, 4),
        ]
        for i in range(14):
            a = 2 * math.pi * i / 14
            d = Vector((0, math.cos(a), math.sin(a)))
            c = Vector((x, 0, axle_z))
            parts.append(cyl("spoke", c + d * 9, c + d * 63, 2.1, 1.6, CARRIAGE, 6))
    return join(parts, "SM_FieldCannon")


# ---------------------------------------------------------------- export
def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    C.view_layer.objects.active = objs[0]


def export_fbx(objs, path, armature=False):
    select_only(objs)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
        object_types={"ARMATURE", "MESH"}, mesh_smooth_type="FACE", add_leaf_bones=False,
        bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X", axis_forward="-Z", axis_up="Y")


def export_glb(objs, path):
    select_only(objs)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format="GLB", export_animations=False)


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


# ---------------------------------------------------------------- posing + preview renders
def aim(arm, bone, direction):
    pb = arm.pose.bones[bone]
    m = pb.matrix.copy()
    cur = m.col[1].xyz.normalized()
    q = cur.rotation_difference(Vector(direction).normalized()) @ m.to_quaternion()
    pb.matrix = Matrix.Translation(m.translation) @ q.to_matrix().to_4x4()
    C.view_layer.update()


def hand_point(arm, bone):
    pb = arm.pose.bones[bone]
    return arm.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.45)


def place(obj, loc, z_dir, y_dir):
    z = Vector(z_dir).normalized()
    x = Vector(y_dir).cross(z).normalized()
    y = z.cross(x)
    rot = Matrix((x, y, z)).transposed().to_4x4()
    obj.matrix_world = Matrix.Translation(loc) @ rot


def ground(arm, body):
    C.view_layer.update()
    ev = body.evaluated_get(C.evaluated_depsgraph_get())
    low = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    arm.location.z -= low


def pose_charge(arm, body):
    aim(arm, "upperarm_r", (-0.35, -0.35, 0.87))
    aim(arm, "lowerarm_r", (-0.15, -0.55, 0.82))
    aim(arm, "hand_r", (-0.1, -0.6, 0.8))
    aim(arm, "upperarm_l", (0.3, -0.92, -0.25))
    aim(arm, "lowerarm_l", (0.12, -0.99, 0.05))
    aim(arm, "hand_l", (0.05, -1, 0.05))
    aim(arm, "thigh_l", (0, -0.42, -0.91))
    aim(arm, "calf_l", (0, 0.05, -1))
    aim(arm, "foot_l", (0, -0.85, -0.5))
    aim(arm, "thigh_r", (0, 0.3, -0.95))
    aim(arm, "calf_r", (0, 0.55, -0.83))
    aim(arm, "foot_r", (0, -0.75, -0.66))
    aim(arm, "spine_03", (0, -0.12, 1))
    ground(arm, body)


def pose_ready(arm, body):
    aim(arm, "upperarm_r", (-0.2, -0.1, -0.97))
    aim(arm, "lowerarm_r", (-0.05, -0.75, -0.66))
    aim(arm, "hand_r", (0, -0.8, -0.6))
    aim(arm, "upperarm_l", (0.22, 0.05, -0.97))
    aim(arm, "lowerarm_l", (0.15, -0.2, -0.97))
    aim(arm, "thigh_r", (-0.08, 0, -1))
    aim(arm, "thigh_l", (0.08, 0, -1))
    ground(arm, body)


def setup_render():
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    world = D.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = D.objects.new("Sun", D.lights.new("Sun", "SUN"))
    sun.data.energy = 4.5
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    C.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
    _finish(C.active_object, "Ground", mat("M_Ground", (0.24, 0.20, 0.13), 0.95))


def camera(loc, target, lens=50):
    cam = D.objects.get("Cam") or D.objects.new("Cam", D.cameras.new("Cam"))
    if cam.name not in C.collection.objects:
        C.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start, cam.data.clip_end = 1, 100000
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam


def render(name):
    scene.render.filepath = os.path.join(OUT, "Previews", name)
    bpy.ops.render.render(write_still=True)


def clone_soldier(arm, body, loc, yaw):
    a2 = arm.copy()
    a2.data = arm.data
    b2 = body.copy()
    b2.data = body.data
    C.collection.objects.link(a2)
    C.collection.objects.link(b2)
    b2.parent = a2
    b2.modifiers["Armature"].object = a2
    a2.location = loc
    a2.rotation_euler = (0, 0, yaw)
    return a2, b2


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
    render("hero_shot.png")
    camera((-60, -190, 150), (-55, 0, 120), 60)
    render("closeup_blue.png")

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
    render("rts_view.png")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Blend", "rts_assets.blend"))
print("done")
