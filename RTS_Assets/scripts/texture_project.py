"""Textures an untextured AI mesh by projecting its front reference image onto it.

    python texture_project.py <in.glb> <front_image> <out.glb> [--tris 15000] [--size 2048]

The mesh is normalized (180 cm, feet at origin, facing -Y), reduced, UV unwrapped, and the
image is projected straight from the front and baked into a texture. Surfaces facing away
from the camera reuse the front colors at the same height, except the back of the head,
which samples the hair/cap instead of the face. Output is a textured .glb for rig_meshy.py.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rts_common import *  # noqa: E402,F403  (resets the scene)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, IMG, OUT = (os.path.abspath(a) for a in args[:3])
TRIS = int(args[args.index("--tris") + 1]) if "--tris" in args else 15000
SIZE = int(args[args.index("--size") + 1]) if "--size" in args else 2048
HEIGHT = 180.0

# ---------------------------------------------------------------- mesh
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in C.scene.objects if o.type == "MESH"]
select_only(meshes)
if len(meshes) > 1:
    bpy.ops.object.join()
body = C.active_object
body.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(C.scene.objects):
    if o is not body:
        D.objects.remove(o)
body.name = body.data.name = os.path.splitext(os.path.basename(OUT))[0]

vs = [v.co for v in body.data.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
s = HEIGHT / (hi.z - lo.z)
body.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
if tris > TRIS:
    mod = body.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = TRIS / tris
    bpy.ops.object.modifier_apply(modifier=mod.name)
body.data.materials.clear()

# ---------------------------------------------------------------- image silhouette
photo = D.images.load(IMG)
W, H = photo.size
px = list(photo.pixels)  # RGBA floats, bottom row first


def pixel(x, y):
    i = (int(y) * W + int(x)) * 4
    return px[i:i + 3]


bg = [sum(c) / 4 for c in zip(pixel(2, H - 3), pixel(W - 3, H - 3), pixel(2, H // 2), pixel(W - 3, H // 2))]


def is_fg(x, y, threshold=0.12):
    return sum(abs(a - b) for a, b in zip(pixel(x, y), bg)) > threshold


def lum(x, y):
    r, g, b_ = pixel(x, y)
    return 0.3 * r + 0.59 * g + 0.11 * b_


# Height: from the cap top down to the lowest row of dark boot pixels (the floor shadow is lighter).
rows = [y for y in range(0, H, 2) if any(is_fg(x, y) for x in range(0, W, 3))]
top = max(rows)
bg_lum = 0.3 * bg[0] + 0.59 * bg[1] + 0.11 * bg[2]
bottom = next(y for y in range(0, H) if sum(1 for x in range(0, W, 2) if lum(x, y) < bg_lum - 0.25) > 20)
ppc = (top - bottom) / HEIGHT  # image pixels per centimeter
mid_y = bottom + int(0.62 * HEIGHT * ppc)
mid = [x for x in range(0, W) if is_fg(x, mid_y)]
cx = (min(mid) + max(mid)) / 2
print(f"image {W}x{H}, figure rows {bottom}..{top}, {ppc:.2f} px/cm, center x {cx:.0f}")


# Arms: Meshy rarely keeps the exact arm angle of the image, so each arm is rotated and scaled
# around the shoulder until its hand tip lands on the image's hand tip.
V = [v.co for v in body.data.vertices]
fg_cols = {}
for y in range(int(bottom + 0.45 * HEIGHT * ppc), top, 3):
    for x in range(0, W, 2):
        if is_fg(x, y):
            fg_cols.setdefault(x, y)
arms = {}
for sgn in (1, -1):
    tip_m = max((v for v in V if v.z > 0.45 * HEIGHT), key=lambda v: v.x * sgn)
    col = max(fg_cols, key=lambda x: x * sgn)
    tip_i = Vector(((col - cx) / ppc, (fg_cols[col] - bottom) / ppc))
    sh = Vector((sgn * 19, 0.81 * HEIGHT))
    a_m, a_i = Vector((tip_m.x, tip_m.z)) - sh, tip_i - sh
    ang = math.atan2(a_i.y, a_i.x) - math.atan2(a_m.y, a_m.x)
    arms[sgn] = (sh, a_m, Matrix.Rotation(ang, 2) * (a_i.length / a_m.length))
    print(f"arm {sgn:+d}: rotate {math.degrees(ang):.1f} deg, scale {a_i.length / a_m.length:.2f}")


# Bleed the figure's colors outward over the background so samples that land on or just past
# the silhouette edge (sides of the body) pick up clothing instead of the grey backdrop.
import numpy as np  # noqa: E402

arr = np.array(photo.pixels[:], dtype=np.float32).reshape(H, W, 4)
mask = np.abs(arr[:, :, :3] - np.array(bg, dtype=np.float32)).sum(axis=2) > 0.12
mask[:bottom, :] = False  # the floor shadow is not part of the figure
# Shrink the mask a few pixels to drop the anti-aliased edge, then grow colors back out.
for _ in range(3):
    m = mask.copy()
    m[1:, :] &= mask[:-1, :]
    m[:-1, :] &= mask[1:, :]
    m[:, 1:] &= mask[:, :-1]
    m[:, :-1] &= mask[:, 1:]
    mask = m
col = np.where(mask[:, :, None], arr, 0.0)
for _ in range(60):
    acc = np.zeros_like(col)
    cnt = np.zeros((H, W, 1), dtype=np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh_col = np.roll(col, (dy, dx), axis=(0, 1))
        sh_m = np.roll(mask, (dy, dx), axis=(0, 1))[:, :, None]
        acc += sh_col * sh_m
        cnt += sh_m
    grow = (~mask) & (cnt[:, :, 0] > 0)
    col[grow] = acc[grow] / cnt[grow]
    mask = mask | grow
col[:, :, 3] = 1.0
photo.pixels[:] = col.ravel()


def to_uv(x, z):
    p = Vector((x, z))
    sgn = 1 if x > 0 else -1
    sh, a_m, xf = arms[sgn]
    t = max(0.0, min(1.0, (p - sh).dot(a_m) / a_m.length_squared))
    dist = (p - (sh + a_m * t)).length
    if x * sgn > 15 and dist < 10:
        w = min(1.0, (x * sgn - 15) / 8) * min(1.0, (10 - dist) / 3)
        p = p.lerp(sh + xf @ (p - sh), w)
    return ((cx + p.x * ppc) / W, (bottom + p.y * ppc) / H)


# Back of the head gets one solid hair color and one solid cap color, taken from the side of
# the head just above the ear and from the side of the cap (away from the front badge).
CAP_Z = 0.93 * HEIGHT
hair_uv = to_uv(-8.2, 0.918 * HEIGHT)
cap_uv = to_uv(-6.0, 0.965 * HEIGHT)

# ---------------------------------------------------------------- UVs
select_only([body])
bake_uv = body.data.uv_layers.new(name="UVMap")
proj_uv = body.data.uv_layers.new(name="Projection")
body.data.uv_layers.active = bake_uv
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")

me = body.data
proj_uv = me.uv_layers["Projection"]  # re-fetch: edit mode invalidates the old reference
for poly in me.polygons:
    back = poly.normal.y > 0.35
    for li in poly.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        if back and co.z > 0.86 * HEIGHT:
            proj_uv.data[li].uv = cap_uv if co.z > CAP_Z else hair_uv
        else:
            proj_uv.data[li].uv = to_uv(co.x, co.z)

# ---------------------------------------------------------------- bake
baked = D.images.new(f"T_{body.name}", SIZE, SIZE)
m = D.materials.new(f"M_{body.name}")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
emit = nt.nodes.new("ShaderNodeEmission")
src_tex = nt.nodes.new("ShaderNodeTexImage")
src_tex.image = photo
src_tex.extension = "EXTEND"
src_uv = nt.nodes.new("ShaderNodeUVMap")
src_uv.uv_map = "Projection"
nt.links.new(src_uv.outputs["UV"], src_tex.inputs["Vector"])
nt.links.new(src_tex.outputs["Color"], emit.inputs["Color"])
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
target = nt.nodes.new("ShaderNodeTexImage")
target.image = baked
nt.nodes.active = target
me.materials.append(m)

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 1
scene.render.bake.margin = 8
select_only([body])
bpy.ops.object.bake(type="EMIT", uv_layer="UVMap")
baked.filepath_raw = os.path.splitext(OUT)[0] + "_basecolor.png"
baked.file_format = "PNG"
baked.save()

# Final material: plain PBR using the baked texture.
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.75
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = baked
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
me.uv_layers.remove(me.uv_layers["Projection"])

select_only([body])
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format="GLB")
print(f"wrote {OUT} ({len(me.polygons)} faces)")
