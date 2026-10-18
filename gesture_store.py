#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Gestures made with the gesture editor (angles of the final pose, see pose_model.py), one JSON file per gesture in the folder "gestures_dir"
(default data/gestures), shared by all devices like the expression presets.

The gestures that come with the character (ui/godot/presets/gestures.json, made of keyframes) stay as they are: they are listed (kind "keys",
"builtin": true), can be used by presets and the model, but cannot be changed or deleted here, and their names cannot be reused.

  {"name": "cheer_v", "kind": "pose", "description": "...", "expression": "happy", "reach": 0.6, "hold": 1.5,
   "pose": {"R": {"upper_raise": 150, "upper_direction": 20, "fingers": "open"}, "L": {...}, "torso": {"torso_lean": -5}},
   "source": "manual", "updated": "2026-10-18T10:00:00Z"}
"""
import datetime
import hashlib
import json
import os
import tempfile
import threading

try:
    from .mia_logger import logger
    from .preset_store import PresetError, NAME_RE, SOURCES, MAX_DESCRIPTION
    from .pose_model import normalize_pose, normalize_timing
except ImportError:  # used as plain script / in tests
    from mia_logger import logger
    from preset_store import PresetError, NAME_RE, SOURCES, MAX_DESCRIPTION
    from pose_model import normalize_pose, normalize_timing

KIND = "pose"


class GestureStore:
    def __init__(self, folder, shipped_file=None, in_use=None, expression_names=None):
        """
        folder: where the gesture files live (created)
        shipped_file: {"gestures": [...]}, the gestures that come with the character (names, descriptions; read only)
        in_use: function(gesture name) -> names of the presets that use it (a gesture in use is not deleted by accident)
        expression_names: function() -> names of the expression presets (None: the "expression" of a gesture is not checked)
        """
        self.folder = folder
        self._in_use = in_use or (lambda name: [])
        self._expression_names = expression_names
        self._lock = threading.RLock()
        self._shipped = self._read_shipped(shipped_file)
        os.makedirs(folder, exist_ok=True)

    # --- what comes with the character ---------------------------------------------------------------------------------------
    @staticmethod
    def _read_shipped(path):
        if not path or not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as fp:
            gestures = json.load(fp)["gestures"]
        return [{"name": g["name"], "kind": "keys", "builtin": True, "description": g.get("description", ""), "expression": g.get("expression", "")}
                for g in gestures]

    def shipped(self):
        return [dict(g) for g in self._shipped]

    def shipped_names(self):
        return {g["name"] for g in self._shipped}

    # --- helpers ------------------------------------------------------------------------------------------------------------------
    def _path(self, name):
        if not isinstance(name, str) or not NAME_RE.match(name):
            raise PresetError(f"invalid gesture name {name!r}: use 1-40 letters, digits, - or _", 400)
        return os.path.join(self.folder, name + ".json")

    def _write(self, gesture):
        """atomic: a crash while writing never leaves a half written gesture"""
        stored = dict(gesture, updated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        fd, tmp = tempfile.mkstemp(dir=self.folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                json.dump(stored, fp, indent=2, ensure_ascii=False)
                fp.write("\n")
            os.replace(tmp, self._path(gesture["name"]))
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return stored

    # --- validation -------------------------------------------------------------------------------------------------------------
    def normalize(self, raw):
        """checks a gesture like the character does; returns (gesture, corrections); raises PresetError if it is unusable"""
        if not isinstance(raw, dict):
            raise PresetError("a gesture must be a JSON object")
        corrections = []
        name = raw.get("name")
        self._path(name)

        description = raw.get("description", "")
        if not isinstance(description, str):
            corrections.append("description is not text, removed")
            description = ""
        if len(description) > MAX_DESCRIPTION:
            corrections.append(f"description shortened to {MAX_DESCRIPTION} characters")
            description = description[:MAX_DESCRIPTION]

        expression = raw.get("expression", "")
        if not isinstance(expression, str):
            corrections.append("expression is not text, removed")
            expression = ""
        elif expression and self._expression_names is not None and expression not in set(self._expression_names()):
            corrections.append(f"unknown expression '{expression}' removed")
            expression = ""

        reach, hold, timing_corrections = normalize_timing(raw)
        corrections += timing_corrections

        pose, pose_corrections = normalize_pose(raw.get("pose", {}))
        corrections += pose_corrections
        if not pose:
            raise PresetError("the pose is empty: set at least one angle", 400, pose_corrections)

        source = raw.get("source", "manual")
        if source not in SOURCES:
            corrections.append(f"unknown source '{source}' set to manual")
            source = "manual"

        return {"name": name, "kind": KIND, "description": description, "expression": expression, "reach": reach, "hold": hold,
                "pose": pose, "source": source}, corrections

    # --- reading ------------------------------------------------------------------------------------------------------------------
    def names(self):
        """the gestures made in the editor"""
        with self._lock:
            return sorted(f[:-5] for f in os.listdir(self.folder) if f.endswith(".json") and NAME_RE.match(f[:-5]))

    def all_names(self):
        """every gesture a preset or the model may use: the built in ones and the ones made in the editor"""
        return sorted(self.shipped_names() | set(self.names()))

    def get(self, name):
        with self._lock:
            path = self._path(name)
            if not os.path.exists(path):
                raise PresetError(f"no gesture '{name}'", 404)
            with open(path, encoding="utf-8") as fp:
                return json.load(fp)

    def list(self):
        """the gestures made in the editor, complete"""
        gestures = []
        with self._lock:
            for name in self.names():
                try:
                    gestures.append(self.get(name))
                except (OSError, ValueError) as exc:
                    logger.error(f"gesture {name} is unreadable: {exc}")
        return gestures

    def describe_all(self):
        """name, description and expression of every gesture (what a menu or a prompt needs)"""
        return [{"name": g["name"], "description": g.get("description", ""), "expression": g.get("expression", ""), "kind": g["kind"],
                 "builtin": g.get("builtin", False)} for g in self._shipped + [dict(g, builtin=False) for g in self.list()]]

    def version(self):
        """changes whenever a gesture is added, changed or removed (other devices poll it)"""
        with self._lock:
            parts = []
            for name in self.names():
                stat = os.stat(self._path(name))
                parts.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
        return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]

    # --- changing ---------------------------------------------------------------------------------------------------------------
    def _check_free(self, name):
        if name in self.shipped_names():
            raise PresetError(f"'{name}' is a gesture that comes with the character and cannot be used as a name", 409)
        if os.path.exists(self._path(name)):
            raise PresetError(f"gesture '{name}' exists already, change it instead", 409)

    def create(self, raw):
        gesture, corrections = self.normalize(raw)
        with self._lock:
            self._check_free(gesture["name"])
            return self._write(gesture), corrections

    def update(self, name, raw, force=False):
        """overwrites the gesture `name`; a different "name" in the body renames it"""
        if name in self.shipped_names():
            raise PresetError(f"'{name}' comes with the character and cannot be changed", 409)
        gesture, corrections = self.normalize(raw)
        with self._lock:
            old_path = self._path(name)
            if not os.path.exists(old_path):
                raise PresetError(f"no gesture '{name}'", 404)
            if gesture["name"] != name:
                users = self._in_use(name)
                if users and not force:
                    raise PresetError(f"'{name}' is used by the presets {', '.join(users)} and cannot be renamed (they would lose the gesture)", 409)
                self._check_free(gesture["name"])
            stored = self._write(gesture)
            if gesture["name"] != name:
                os.remove(old_path)
            return stored, corrections

    def delete(self, name, force=False):
        if name in self.shipped_names():
            raise PresetError(f"'{name}' comes with the character and cannot be deleted", 409)
        with self._lock:
            path = self._path(name)
            if not os.path.exists(path):
                raise PresetError(f"no gesture '{name}'", 404)
            users = self._in_use(name)
            if users and not force:
                raise PresetError(f"'{name}' is used by the presets {', '.join(users)}: change them first or delete with force", 409)
            os.remove(path)
