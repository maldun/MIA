"""
Exports the character from a .blend file to VRM 1.0 using the VRM Add-on for Blender.
Run headless (the Flatpak needs absolute paths and access to them):
  flatpak run --filesystem=<dir> org.blender.Blender -b <file.blend> \
      --python ui/tools/export_character.py -- <out.vrm>
Or use ui/tools/export_character.sh, which fills in the paths.
"""
import sys, os
import addon_utils
import bpy

out_path = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else "mia.vrm"

# the extension is installed with `blender --command extension install-file -r user_default --enable <zip>`
for mod in ("bl_ext.blender_org.vrm", "bl_ext.user_default.vrm"):
    try:
        addon_utils.enable(mod, default_set=False, persistent=False)
        break
    except Exception:
        continue
if not hasattr(bpy.ops.export_scene, "vrm"):
    raise SystemExit("VRM add-on is not enabled/installed in this Blender")

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm

os.makedirs(os.path.dirname(out_path), exist_ok=True)
result = bpy.ops.export_scene.vrm(filepath=out_path, ignore_warning=True)
print("EXPORT", result, out_path, os.path.getsize(out_path) if os.path.exists(out_path) else "missing")
