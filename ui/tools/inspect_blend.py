"""
Writes an inventory of a .blend file as markdown (Phase 1 of ui/REQUIREMENTS.md).
Run headless:
  flatpak run org.blender.Blender -b <file.blend> --python ui/tools/inspect_blend.py -- <out.md>
"""
import sys, os, re, collections
import bpy

out_path = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "asset_inventory.md"
L = []
def w(s=""): L.append(s)

w(f"# Asset inventory: `{os.path.basename(bpy.data.filepath)}`")
w(f"\nBlender {bpy.app.version_string}\n")
problems = []

# --- objects / meshes
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
w("## Meshes\n")
w("| Object | Vertices | Faces | Shape keys | Materials | Parent |")
w("|---|---|---|---|---|---|")
total_v = 0
for o in meshes:
    d = o.data
    sk = len(d.shape_keys.key_blocks) if d.shape_keys else 0
    total_v += len(d.vertices)
    w(f"| {o.name} | {len(d.vertices)} | {len(d.polygons)} | {sk} | {len(o.material_slots)} | {o.parent.name if o.parent else ''} |")
w(f"\nTotal vertices: **{total_v}**; other object types: " +
  ", ".join(f"{t}={n}" for t, n in collections.Counter(o.type for o in bpy.data.objects if o.type != 'MESH').items()))
if total_v > 100000:
    problems.append(f"High vertex count ({total_v}) - heavy for mobile web.")

# --- shape keys
w("\n## Shape keys\n")
all_names = collections.defaultdict(list)
for o in meshes:
    sk = o.data.shape_keys
    if not sk:
        continue
    names = [kb.name for kb in sk.key_blocks]
    w(f"### {o.name} ({len(names)} keys, reference: `{sk.reference_key.name}`)\n")
    groups = collections.defaultdict(list)
    for n in names:
        m = re.match(r"^([A-Za-z]+_[A-Za-z]+)_", n)
        groups[m.group(1) if m else "(no prefix)"].append(n)
    for g in sorted(groups):
        w(f"- **{g}** ({len(groups[g])}): " + ", ".join(f"`{n}`" for n in groups[g]))
    w()
    for n in names:
        all_names[n].append(o.name)
dups = {n: os_ for n, os_ in all_names.items() if len(os_) > 1}
if dups:
    w(f"Shape-key names present on several meshes: {len(dups)}.\n")
    w("<details><summary>list</summary>\n\n" + "\n".join(f"- `{n}`: {', '.join(v)}" for n, v in sorted(dups.items())) + "\n\n</details>\n")
    problems.append("Same shape-key names exist on multiple meshes; the engine must drive every mesh that carries a key.")
w(f"Unique shape-key names: **{len(all_names)}**")

# --- armature
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
w("\n## Armatures\n")
for a in arms:
    bones = a.data.bones
    w(f"### {a.name}: {len(bones)} bones\n")
    key = [b.name for b in bones if re.search(r"head|neck|jaw|eye|chest|spine", b.name, re.I)]
    w("Key bones (head/neck/jaw/eye/spine/chest): " + ", ".join(f"`{n}`" for n in key))
    w("\n<details><summary>all bones</summary>\n\n" + ", ".join(f"`{b.name}`" for b in bones) + "\n\n</details>\n")
    if not any(re.search(r"jaw", b.name, re.I) for b in bones):
        problems.append(f"{a.name}: no jaw bone (jaw_open must be done via a mouth shape key).")
if not arms:
    problems.append("No armature found.")

# --- materials
w("\n## Materials\n")
w("| Material | Shader nodes | Image textures | Blend mode | Backface culling |")
w("|---|---|---|---|---|")
for m in bpy.data.materials:
    nodes = m.node_tree.nodes if m.use_nodes and m.node_tree else []
    kinds = collections.Counter(
        n.bl_idname.replace("ShaderNode", "") + (f"({n.node_tree.name})" if n.bl_idname == "ShaderNodeGroup" and n.node_tree else "")
        for n in nodes)
    imgs = [n.image.name for n in nodes if n.bl_idname == "ShaderNodeTexImage" and n.image]
    bm = getattr(m, "surface_render_method", getattr(m, "blend_method", "?"))
    w(f"| {m.name} | {', '.join(f'{k}x{v}' if v > 1 else k for k, v in kinds.items())} | {', '.join(imgs)} | {bm} | {m.use_backface_culling} |")
groups_used = {n.node_tree.name for m in bpy.data.materials if m.use_nodes and m.node_tree
               for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeGroup" and n.node_tree}
if groups_used:
    w("\nNode groups used by materials: " + ", ".join(f"`{g}`" for g in sorted(groups_used)))
    problems.append("Materials use custom node groups: " + ", ".join(sorted(groups_used)) + ". Not directly portable to Godot.")

# --- images
w("\n## Images\n")
w("| Image | Size | Packed | Source / path |")
w("|---|---|---|---|")
for im in bpy.data.images:
    if im.name in ("Render Result", "Viewer Node"):
        continue
    packed = im.packed_file is not None
    path = im.filepath
    missing = (not packed) and im.source == 'FILE' and not os.path.exists(bpy.path.abspath(path))
    w(f"| {im.name} | {im.size[0]}x{im.size[1]} | {packed} | {im.source} {path}{' **MISSING**' if missing else ''} |")
    if missing:
        problems.append(f"Texture not packed and file missing: {im.name} ({path})")
    elif not packed and im.source == 'FILE':
        problems.append(f"Texture not packed: {im.name} (File > External Data > Pack Resources)")
    if max(im.size) > 2048:
        problems.append(f"Large texture {im.name} {im.size[0]}x{im.size[1]} - compress for mobile.")

# --- VRM metadata
w("\n## VRM metadata\n")
vrm = []
for a in arms:
    for key in a.data.keys():
        vrm.append(f"{a.name}.data[{key}]")
    for key in a.keys():
        vrm.append(f"{a.name}[{key}]")
for key in bpy.context.scene.keys():
    vrm.append(f"scene[{key}]")
w("Custom properties: " + (", ".join(vrm) or "none"))
props = [f"{a.name}.data.{p}" for a in arms for p in ("vrm0", "vrm1", "vrm_addon_extension") if hasattr(a.data, p)]
w("\nVRM add-on property groups: " + (", ".join(props) or "none")
  + " (the VRM add-on is probably not installed in this Blender, so absence here is not conclusive)")
w(f"\nText blocks: {list(bpy.data.texts.keys()) or 'none'}")

import json
for t in bpy.data.texts:
    if t.name.startswith("vrm"):
        try:
            j = json.loads(t.as_string())
        except ValueError:
            continue
        ext = j.get("extensions", {})
        w(f"\n`{t.name}` (original glTF JSON): extensions = {sorted(ext)}; extensionsUsed = {j.get('extensionsUsed')}")
        v1 = ext.get("VRMC_vrm")
        if v1:
            w(f"\n- **VRM 1.0** (specVersion {v1.get('specVersion')})")
            w(f"- license: {v1.get('meta', {}).get('licenseUrl')}, avatarPermission: {v1.get('meta', {}).get('avatarPermission')}")
            expr = v1.get("expressions", {})
            for kind in ("preset", "custom"):
                for name, e in expr.get(kind, {}).items():
                    binds = [f"{b.get('index')}:{j['meshes'][j['nodes'][b['node']]['mesh']]['extras']['targetNames'][b['index']]}"
                             if 'extras' in j['meshes'][j['nodes'][b['node']]['mesh']] else f"{b.get('index')}"
                             for b in e.get("morphTargetBinds", [])]
                    w(f"  - {kind} expression `{name}`: {', '.join(binds) or 'no morph binds'}"
                      + (f" (overrideBlink={e.get('overrideBlink')}, overrideMouth={e.get('overrideMouth')})" if e.get("overrideBlink") or e.get("overrideMouth") else ""))
            w(f"- lookAt: {v1.get('lookAt')}")
        if ext.get("VRM"):
            w("\n- **VRM 0.x** extension present")
        for k in ("VRMC_springBone", "VRMC_node_constraint", "VRMC_materials_mtoon"):
            if k in ext or any(k in m.get("extensions", {}) for m in j.get("materials", [])):
                w(f"- uses `{k}`")
        spring = ext.get("VRMC_springBone", {})
        if spring:
            w(f"- spring bone: {len(spring.get('springs', []))} springs, {len(spring.get('colliders', []))} colliders")
        mt = [m for m in j.get("materials", []) if "VRMC_materials_mtoon" in m.get("extensions", {})]
        if mt:
            w(f"- MToon materials in glTF: {len(mt)}; alphaMode counts: {dict(collections.Counter(m.get('alphaMode', 'OPAQUE') for m in mt))}")

# --- extra checks
if any(im.name == "Thumbnail" for im in bpy.data.images):
    problems.append("`Thumbnail` (2048x2048) is the VRM preview image, not used for rendering - drop it from the web export.")
if bpy.data.materials.get("Material") and not bpy.data.materials["Material"].users:
    problems.append("Default `Material` is unused.")
outlines = [m.name for m in bpy.data.materials if m.name.startswith("MToon Outline")]
if outlines:
    problems.append(f"{len(outlines)} separate `MToon Outline` materials (inverted-hull outline pass); in Godot use one outline pass instead.")
for t in bpy.data.texts:
    if t.name.startswith("vrm") and '"avatarPermission": "onlyAuthor"' in t.as_string().replace('":"', '": "'):
        problems.append("VRM license avatarPermission is `onlyAuthor` - fine for personal use; check before sharing the model publicly.")

# --- problems
w("\n## Flagged problems\n")
for p in problems or ["none"]:
    w(f"- {p}")

os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
open(out_path, "w").write("\n".join(L) + "\n")
print("WROTE", out_path)
