# The 3D character: the files that travel outside git

The model is not shared, so it is not in the repository (`*.blend` and `ui/character/*.zip` are git-ignored). Two zip files carry it from one machine to another, for example through your own Google Drive.
`manifest.json` (tracked) says which version of each zip is the right one and its SHA-256; it contains no model data.

| pack | what is in it | size | needed for |
|---|---|---|---|
| `mia-character-web-N.zip` | the web export, 9 files: `index.html`, `index.js`, `index.wasm` (Godot's engine), `index.pck` (the character and the scene), the two audio worklets and three PNGs (splash, icons) | 20.5 MB | **running** the character on any machine: no Godot, no Blender |
| `mia-character-source-N.zip` | `mia.blend` | 13 MB | only where the character is **edited** (then `ui/tools/setup_character.sh` makes the VRM and the web export from it) |

`mia.vrm` is not packed: it is made from the `.blend` (identical byte for byte), and the browser does not need it, the character is inside `index.pck`.

## On the machine that has the character

1. After a change of the character: `ui/tools/setup_character.sh path/to/mia.blend` (VRM and web export).
2. `python ui/tools/character_pack.py pack all --blend path/to/mia.blend` makes the zips here and updates `manifest.json` (the version grows only when the content changed; the same content gives the same file).
3. Upload the new zip(s) to your Drive, commit `manifest.json`.

## On another machine

1. Download the zip named in `manifest.json` (`python ui/tools/character_pack.py status` shows the name) from your Drive into this folder.
2. `python ui/tools/character_pack.py install web` checks the SHA-256 and unpacks to `ui/godot/build/web`, which MIA serves under `/character/`. (`install source` puts `mia.blend` here; a `mia.blend` that was here is kept as `mia.previous.blend`.)

A zip that is not the one of the manifest, or has paths outside its place, links or an unreasonable size, is refused (`tests/test_character_pack.py`). Without the `character_dir` option the default is `ui/godot/build/web`.

## What was tested (2026-10-20)

Packed, unpacked into a folder of a "new machine" (no Godot, no Blender used), served with `ui/tools/serve_web.py` and loaded in headless Chromium: the character appears, all nine files are requested and found.
Rebuilding from the same `.blend` gives an identical VRM (SHA-256) and an identical web export, so a pack can always be made again.

**Keep a copy of `mia.blend` somewhere else too** (the source pack in your Drive is that copy). It is the one file of the character that exists only once.

## Rights

Before the model or the zips go anywhere public, check the rights of what is inside (VRoid Studio parts, bought hair or clothes, textures): see the notes in the commit history of this file and the license fields of the VRM (`allowRedistribution`, `modification`, `avatarPermission`).
