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
Storage of the character's expression presets (ui/REQUIREMENTS.md 4.4 and 4.7): one JSON file per preset in a folder,
shared by all devices. Preset format:

  {"name": "smug", "description": "...", "weights": {"Fcl_MTH_Fun": 0.6}, "bones": {"head_roll": 3.0},
   "gesture": "hand_on_hip", "speaking": false, "tags": ["smug"], "source": "manual", "updated": "2026-10-18T10:00:00Z"}

Presets that MIA's emotions use (expressions.json) cannot be deleted or renamed by accident.
"""
import datetime
import hashlib
import json
import os
import re
import tempfile
import threading

try:
    from .mia_logger import logger
except ImportError:  # used as plain script / in tests
    from mia_logger import logger

NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
KEY_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
BONE_PARAMS = ("head_pitch", "head_yaw", "head_roll", "eye_pitch", "eye_yaw")
BONE_LIMIT = 45.0
SOURCES = ("manual", "llm", "llm_edited")
MAX_DESCRIPTION = 300
MAX_TAGS = 12
MAX_TAG_LENGTH = 30


class PresetError(Exception):
    """An error that is reported to the client with an HTTP status."""
    def __init__(self, message, status=400, details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details or []


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class PresetStore:
    def __init__(self, folder, defaults_file=None, shape_keys_file=None, gestures_file=None, protected=None):
        """
        folder: where the preset files live (created, and filled from defaults_file when empty)
        defaults_file: {"presets": [...]} used to fill an empty folder (the library shipped with the character)
        shape_keys_file / gestures_file: names that are accepted (None: no check)
        protected: function returning the preset names that must not be deleted or renamed
        """
        self.folder = folder
        self._protected = protected or (lambda: set())
        self._lock = threading.RLock()
        self.known_shape_keys = self._read_names(shape_keys_file, "shape_keys")
        self.known_gestures = self._read_names(gestures_file, "gestures")
        os.makedirs(folder, exist_ok=True)
        if defaults_file and not self.names():
            self._seed(defaults_file)

    # --- helpers -----------------------------------------------------------------------------

    @staticmethod
    def _read_names(path, key):
        if not path or not os.path.exists(path):
            return None
        with open(path) as fp:
            return {entry["name"] for entry in json.load(fp)[key]}

    def _seed(self, defaults_file):
        with open(defaults_file) as fp:
            presets = json.load(fp)["presets"]
        for raw in presets:
            try:
                preset, _ = self.normalize(raw)
                self._write(preset)
            except PresetError as exc:
                logger.error(f"default preset {raw.get('name')} skipped: {exc.message}")
        logger.info(f"preset folder {self.folder} filled with {len(self.names())} default presets")

    def _path(self, name):
        if not isinstance(name, str) or not NAME_RE.match(name):
            raise PresetError(f"invalid preset name {name!r}: use 1-40 letters, digits, - or _", 400)
        return os.path.join(self.folder, name + ".json")

    def _write(self, preset):
        """atomic: a crash while writing never leaves a half written preset"""
        stored = dict(preset, updated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        fd, tmp = tempfile.mkstemp(dir=self.folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as fp:
                json.dump(stored, fp, indent=2, ensure_ascii=False)
                fp.write("\n")
            os.replace(tmp, self._path(preset["name"]))
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return stored

    # --- validation ----------------------------------------------------------------------------

    def normalize(self, raw):
        """
        Checks a preset like the character does: unknown shape keys, bones and gestures are removed, values are clamped.
        Returns (preset, corrections); raises PresetError if the preset is unusable (no valid name, not an object).
        """
        if not isinstance(raw, dict):
            raise PresetError("a preset must be a JSON object")
        corrections = []
        name = raw.get("name")
        self._path(name)  # raises for invalid names

        description = raw.get("description", "")
        if not isinstance(description, str):
            corrections.append("description is not text, removed")
            description = ""
        if len(description) > MAX_DESCRIPTION:
            corrections.append(f"description shortened to {MAX_DESCRIPTION} characters")
            description = description[:MAX_DESCRIPTION]

        weights = {}
        raw_weights = raw.get("weights", {})
        if not isinstance(raw_weights, dict):
            corrections.append("weights is not an object, ignored")
            raw_weights = {}
        for key, value in raw_weights.items():
            if not KEY_RE.match(str(key)) or (self.known_shape_keys is not None and key not in self.known_shape_keys):
                corrections.append(f"unknown shape key '{key}' removed")
            elif not _is_number(value):
                corrections.append(f"weight '{key}' is not a number, removed")
            else:
                clamped = min(1.0, max(0.0, float(value)))
                if clamped != float(value):
                    corrections.append(f"weight '{key}' clamped from {value} to {clamped}")
                weights[key] = round(clamped, 4)

        bones = {}
        raw_bones = raw.get("bones", {})
        if not isinstance(raw_bones, dict):
            corrections.append("bones is not an object, ignored")
            raw_bones = {}
        for key, value in raw_bones.items():
            if key not in BONE_PARAMS:
                corrections.append(f"unknown bone parameter '{key}' removed")
            elif not _is_number(value):
                corrections.append(f"bone '{key}' is not a number, removed")
            else:
                clamped = min(BONE_LIMIT, max(-BONE_LIMIT, float(value)))
                if clamped != float(value):
                    corrections.append(f"bone '{key}' clamped from {value} to {clamped}")
                bones[key] = round(clamped, 3)

        gesture = raw.get("gesture", "")
        if not isinstance(gesture, str):
            corrections.append("gesture is not text, removed")
            gesture = ""
        elif gesture and self.known_gestures is not None and gesture not in self.known_gestures:
            corrections.append(f"unknown gesture '{gesture}' removed")
            gesture = ""

        tags = []
        raw_tags = raw.get("tags", [])
        if not isinstance(raw_tags, list):
            corrections.append("tags is not a list, ignored")
            raw_tags = []
        for tag in raw_tags:
            tag = str(tag).strip()[:MAX_TAG_LENGTH]
            if tag and tag not in tags:
                tags.append(tag)
        if len(tags) > MAX_TAGS:
            corrections.append(f"only the first {MAX_TAGS} tags are kept")
            tags = tags[:MAX_TAGS]

        source = raw.get("source", "manual")
        if source not in SOURCES:
            corrections.append(f"unknown source '{source}' set to manual")
            source = "manual"

        preset = {"name": name, "description": description, "weights": weights, "bones": bones, "gesture": gesture,
                  "speaking": bool(raw.get("speaking", False)), "tags": tags, "source": source}
        return preset, corrections

    # --- reading ----------------------------------------------------------------------------------

    def names(self):
        with self._lock:
            return sorted(f[:-5] for f in os.listdir(self.folder) if f.endswith(".json") and NAME_RE.match(f[:-5]))

    def get(self, name):
        with self._lock:
            path = self._path(name)
            if not os.path.exists(path):
                raise PresetError(f"no preset '{name}'", 404)
            with open(path) as fp:
                return json.load(fp)

    def list(self):
        presets = []
        with self._lock:
            for name in self.names():
                try:
                    presets.append(self.get(name))
                except (OSError, ValueError) as exc:
                    logger.error(f"preset {name} is unreadable: {exc}")
        return presets

    def version(self):
        """changes whenever a preset is added, changed or removed (other devices poll it)"""
        with self._lock:
            parts = []
            for name in self.names():
                stat = os.stat(self._path(name))
                parts.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
        return hashlib.sha1("|".join(parts).encode()).hexdigest()[:12]

    def protected(self):
        return set(self._protected())

    # --- changing ---------------------------------------------------------------------------------------

    def create(self, raw):
        preset, corrections = self.normalize(raw)
        with self._lock:
            if os.path.exists(self._path(preset["name"])):
                raise PresetError(f"preset '{preset['name']}' exists already, change it instead", 409)
            return self._write(preset), corrections

    def update(self, name, raw, force=False):
        """overwrites the preset; a different name in the data renames it"""
        preset, corrections = self.normalize(raw)
        with self._lock:
            self.get(name)  # 404 if it does not exist
            if preset["name"] != name:
                if name in self.protected() and not force:
                    raise PresetError(f"'{name}' is used by MIA's emotions and cannot be renamed", 409)
                if os.path.exists(self._path(preset["name"])):
                    raise PresetError(f"preset '{preset['name']}' exists already", 409)
                stored = self._write(preset)
                os.remove(self._path(name))
                return stored, corrections
            return self._write(preset), corrections

    def delete(self, name, force=False):
        with self._lock:
            self.get(name)  # 404 if it does not exist
            if name in self.protected() and not force:
                raise PresetError(f"'{name}' is used by MIA's emotions and cannot be deleted", 409)
            os.remove(self._path(name))
