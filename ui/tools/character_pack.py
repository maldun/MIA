#!/usr/bin/env python3
"""
The 3D character as zip files that travel outside git (for example through a Google Drive): the model is not shared, so it is not in the repository, but a new machine must be able to get it.

  python ui/tools/character_pack.py pack [web|source|all] [--blend path/to/mia.blend]   makes the zip(s) in ui/character/ and writes ui/character/manifest.json (version, SHA-256, size)
  python ui/tools/character_pack.py install [web|source|all] [--folder DIR] [--force]   checks the zip of the manifest (in DIR, default ui/character/) and unpacks it
  python ui/tools/character_pack.py status                                            what the manifest expects, what is in the folder, what is installed

Two packs:  web     the web export (ui/godot/build/web, 48 MB) that MIA serves, without Godot's *.import files: all a machine needs to RUN the character, no Godot and no Blender
            source  mia.blend (13 MB): the only source, needed only where the character is edited (ui/tools/setup_character.sh makes the VRM and the web export from it)

The zips are made the same way every time (sorted, fixed timestamps), so the same content gives the same SHA-256 and the version only grows when the content changes. The manifest is tracked in git, the zips
are not (*.zip in ui/character is ignored): upload them by hand, download them by hand into ui/character/ on the other machine. Install refuses a zip whose SHA-256 is not the one in the manifest, and
a zip with paths outside the expected place, links, or an unreasonable size. Only the standard library is used.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile

UI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(UI, "character")
WEB_DIR = os.path.join(UI, "godot", "build", "web")
KINDS = ("web", "source")
MAX_BYTES = 1 << 30          # unpacked size of a pack at most (the real ones are 48 MB and 13 MB)
MAX_FILES = 1000
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
STAMP = ".pack_sha256"


class PackError(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_path(folder):
    return os.path.join(folder, "manifest.json")


def read_manifest(folder):
    try:
        with open(manifest_path(folder), encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {"format": 1}
    except ValueError as exc:
        raise PackError("manifest.json cannot be read (%s)" % exc)


def write_manifest(folder, data):
    with open(manifest_path(folder), "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=1, sort_keys=True)
        fp.write("\n")


def build_zip(target, entries):
    """a zip with the entries [(name in the zip, path)] in the given order, with fixed timestamps and permissions: the same files give the same bytes"""
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name, path in entries:
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(path, "rb") as src, zf.open(info, "w") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)


def entries_of(kind, blend):
    if kind == "web":
        if not os.path.isdir(WEB_DIR) or not os.listdir(WEB_DIR):
            raise PackError("there is no web export in %s: make it with ui/tools/setup_character.sh first" % WEB_DIR)
        found = []
        for root, _, files in os.walk(WEB_DIR):
            for name in files:
                if name == STAMP or name.endswith(".import"):          # the stamp of an install, and Godot's editor metadata (not used by the browser)
                    continue
                path = os.path.join(root, name)
                found.append(("web/" + os.path.relpath(path, WEB_DIR).replace(os.sep, "/"), path))
        return sorted(found)
    if not os.path.isfile(blend):
        raise PackError("the Blender file is missing: %s (give its path with --blend)" % blend)
    return [("mia.blend", blend)]


def pack(kind, folder=FOLDER, blend=None):
    blend = blend or os.path.join(folder, "mia.blend")
    entries = entries_of(kind, blend)
    os.makedirs(folder, exist_ok=True)
    data = read_manifest(folder)
    previous = data.get(kind) or {}
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        candidate = os.path.join(tmp, "pack.zip")
        build_zip(candidate, entries)
        digest = sha256_file(candidate)
        if previous.get("sha256") == digest:
            version, note = previous["version"], "unchanged"
        else:
            version, note = previous.get("version", 0) + 1, "new version"
        name = "mia-character-%s-%d.zip" % (kind, version)
        target = os.path.join(folder, name)
        if not os.path.exists(target):
            shutil.move(candidate, target)
        size = os.path.getsize(target)
    data[kind] = {"version": version, "file": name, "sha256": digest, "size": size, "files": len(entries)}
    write_manifest(folder, data)
    return {"kind": kind, "file": target, "version": version, "note": note, "sha256": digest, "size": size, "files": len(entries)}


def safe_members(zf, kind):
    """the members of the zip if they are what this pack must contain; raises PackError otherwise"""
    infos = zf.infolist()
    if not infos or len(infos) > MAX_FILES:
        raise PackError("the zip is empty or has too many entries (%d)" % len(infos))
    total = 0
    for info in infos:
        name = info.filename
        parts = name.split("/")
        if name.startswith("/") or "\\" in name or ".." in parts or "" in parts[:-1] or (len(name) > 1 and name[1] == ":"):
            raise PackError("the zip has an unsafe path: %r" % name)
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise PackError("the zip contains a link: %r" % name)
        if kind == "web" and not (name == "web/" or name.startswith("web/")):
            raise PackError("an entry outside web/: %r" % name)
        if kind == "source" and name != "mia.blend":
            raise PackError("an entry other than mia.blend: %r" % name)
        total += info.file_size
    if total > MAX_BYTES:
        raise PackError("the zip would unpack to %d bytes (more than %d)" % (total, MAX_BYTES))
    return infos


def installed_stamp(kind, folder):
    path = os.path.join(WEB_DIR, STAMP) if kind == "web" else os.path.join(folder, "mia.blend")
    if kind == "web":
        return open(path).read().strip() if os.path.exists(path) else None
    return None


def install(kind, folder=FOLDER, force=False, web_dir=None):
    web_dir = web_dir or WEB_DIR
    entry = read_manifest(folder).get(kind)
    if not entry:
        raise PackError("the manifest (%s) has no %s pack: make one with 'pack %s' on the machine that has the character" % (manifest_path(folder), kind, kind))
    zip_path = os.path.join(folder, entry["file"])
    if not os.path.isfile(zip_path):
        raise PackError("the %s pack is not in %s: download %s (version %d, %.1f MB) from where you keep it (your Google Drive) and put it there"
                        % (kind, folder, entry["file"], entry["version"], entry["size"] / 1e6))
    stamp_file = os.path.join(web_dir, STAMP)
    if kind == "web" and not force and os.path.exists(stamp_file) and open(stamp_file).read().strip() == entry["sha256"]:
        return {"kind": kind, "installed": False, "note": "version %d is installed already" % entry["version"]}
    actual = sha256_file(zip_path)
    if actual != entry["sha256"]:
        raise PackError("%s is not the file of the manifest (SHA-256 %s, expected %s): download it again" % (entry["file"], actual[:16], entry["sha256"][:16]))
    with zipfile.ZipFile(zip_path) as zf:
        if zf.testzip() is not None:
            raise PackError("%s is damaged" % entry["file"])
        infos = safe_members(zf, kind)
        if kind == "web":
            parent = os.path.dirname(web_dir)
            os.makedirs(parent, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=parent) as tmp:
                for info in infos:
                    zf.extract(info, tmp)
                fresh = os.path.join(tmp, "web")
                with open(os.path.join(fresh, STAMP), "w") as fp:
                    fp.write(entry["sha256"] + "\n")
                old = os.path.join(tmp, "old")
                if os.path.exists(web_dir):
                    os.rename(web_dir, old)
                os.rename(fresh, web_dir)
            return {"kind": kind, "installed": True, "note": "version %d unpacked to %s" % (entry["version"], web_dir)}
        target = os.path.join(folder, "mia.blend")
        with tempfile.TemporaryDirectory(dir=folder) as tmp:
            zf.extract(infos[0], tmp)
            fresh = os.path.join(tmp, "mia.blend")
            kept = ""
            if os.path.exists(target):
                if sha256_file(target) == sha256_file(fresh):
                    return {"kind": kind, "installed": False, "note": "mia.blend is the same already"}
                os.replace(target, os.path.join(folder, "mia.previous.blend"))
                kept = " (the file that was there is now mia.previous.blend)"
            os.replace(fresh, target)
        return {"kind": kind, "installed": True, "note": "version %d unpacked to %s%s" % (entry["version"], target, kept)}


def status(folder=FOLDER):
    data = read_manifest(folder)
    lines = []
    for kind in KINDS:
        entry = data.get(kind)
        if not entry:
            lines.append("%-7s not in the manifest" % kind)
            continue
        zip_path = os.path.join(folder, entry["file"])
        if os.path.isfile(zip_path):
            here = "in the folder, checksum %s" % ("matches" if sha256_file(zip_path) == entry["sha256"] else "DIFFERS")
        else:
            here = "not in the folder"
        if kind == "web":
            stamp = installed_stamp("web", folder)
            state = "installed" if stamp == entry["sha256"] else ("installed, but another version" if stamp else "not installed")
        else:
            blend = os.path.join(folder, "mia.blend")
            state = ("mia.blend present" + (", same as the pack" if os.path.exists(blend) and _blend_in_zip(zip_path, blend) else "")) if os.path.exists(blend) else "no mia.blend"
        lines.append("%-7s version %d  %s  %.1f MB  %s; %s" % (kind, entry["version"], entry["file"], entry["size"] / 1e6, here, state))
    return lines


def _blend_in_zip(zip_path, blend):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            return hashlib.sha256(zf.read("mia.blend")).hexdigest() == sha256_file(blend)
    except (OSError, KeyError, zipfile.BadZipFile):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["pack", "install", "status"])
    parser.add_argument("what", nargs="?", default="all", choices=list(KINDS) + ["all"])
    parser.add_argument("--folder", default=FOLDER, help="the folder with the zips and manifest.json (default ui/character)")
    parser.add_argument("--blend", default=None, help="mia.blend for the source pack (default: <folder>/mia.blend)")
    parser.add_argument("--force", action="store_true", help="unpack again even if this version is installed")
    args = parser.parse_args(argv)
    kinds = KINDS if args.what == "all" else (args.what,)
    try:
        if args.command == "status":
            print("\n".join(status(args.folder)))
            return 0
        for kind in kinds:
            if args.command == "pack":
                if args.what == "all" and kind == "source" and not os.path.isfile(args.blend or os.path.join(args.folder, "mia.blend")):
                    print("source: skipped (no mia.blend at %s; give --blend)" % (args.blend or os.path.join(args.folder, "mia.blend")))
                    continue
                r = pack(kind, args.folder, args.blend)
                print("%-7s %s: %s (%d files, %.1f MB, SHA-256 %s...)" % (kind, r["note"], os.path.basename(r["file"]), r["files"], r["size"] / 1e6, r["sha256"][:16]))
                print("        upload %s to where you keep it, and commit ui/character/manifest.json" % r["file"])
            else:
                if args.what == "all" and kind == "source" and not os.path.isfile(os.path.join(args.folder, read_manifest(args.folder).get(kind, {}).get("file", "-"))):
                    print("source: skipped (its zip is not in %s; only needed where the character is edited)" % args.folder)
                    continue
                print("%-7s %s" % (kind, install(kind, args.folder, args.force)["note"]))
    except PackError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
