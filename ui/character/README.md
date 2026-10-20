# The source of the 3D character

`mia.blend` (13 MB) is the only source of the character. It is **not in version control** (the model is not shared; `*.blend` is git-ignored, so it cannot be committed by accident). Put it here, or give its path
to the scripts.

Everything else is derived from it and can be made again at any time:

| file | made by | in git |
|---|---|---|
| `ui/godot/assets/mia.vrm` (12 MB) | `ui/tools/export_character.sh mia.blend` (Blender with the VRM add-on, textures shrunk to 1024 px) | ignored |
| `ui/godot/build/web` (48 MB, served by MIA) | `ui/tools/build_web.sh` (Godot headless export) | ignored |

Both steps in one command: `ui/tools/setup_character.sh [path/to/mia.blend]` (the argument, else `$MIA_BLEND`, else `ui/character/mia.blend`). Measured on 2026-10-20: the VRM from the same `.blend` is identical byte for byte
(SHA-256), the export takes 13 s; the web export takes 8 s and two builds are identical. One time per machine: the flatpaks of Blender 5.0 and Godot 4.6.1, the VRM add-on and the Godot export templates (`ui/README.md`).

**Keep a copy of `mia.blend` somewhere else too.** It is the one file of the character that exists only once.
