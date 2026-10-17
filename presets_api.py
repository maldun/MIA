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
REST API for the character's expression presets (ui/REQUIREMENTS.md 4.7), part of MIA's Flask app
(one server for the page, the character and the presets; the preset files live in "presets_dir").

  GET    /api/presets            all presets + version + whether writing needs a token + protected names
  GET    /api/presets/version    {"version": ...}, changes when any preset changes (other devices poll it)
  GET    /api/presets/<name>     one preset
  POST   /api/presets            create (409 if it exists)
  PUT    /api/presets/<name>     overwrite; a different "name" in the body renames it
  DELETE /api/presets/<name>     delete (409 for presets MIA's emotions use, unless ?force=1)
  GET    /api/shape-keys         shape keys with categories and descriptions
  GET    /api/gestures           gestures

Writing (POST, PUT, DELETE) needs JSON as content type (no cross-site form posts), an allowed origin if the browser
sends one, and the header X-MIA-Token if "editor_token" is set in setup_cfg.json.
"""
import hmac
import json
import os
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request

try:
    from .constants import PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR, EDITOR_TOKEN_KEY, EXPRESSION_FILE, TOKEN_HEADER
    from .mia_logger import logger
    from .preset_store import PresetStore, PresetError
except ImportError:  # used as plain script / in tests
    from constants import PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR, EDITOR_TOKEN_KEY, EXPRESSION_FILE, TOKEN_HEADER
    from mia_logger import logger
    from preset_store import PresetStore, PresetError

MAX_BODY = 64 * 1024
PRESET_FILES = os.path.join("ui", "godot", "presets")


def mia_presets(root):
    """names of the presets MIA's expressions use (they must not be deleted by accident)"""
    path = os.path.join(root, EXPRESSION_FILE)
    try:
        with open(path) as fp:
            expressions = json.load(fp)
    except (OSError, ValueError):
        return set()
    return {entry.get("preset", key) for key, entry in expressions.items() if isinstance(entry, dict)}


def create_store(cfg, root):
    """the preset store as configured (folder "presets_dir", filled from the library shipped with the character)"""
    folder = cfg.get(PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR)
    if not os.path.isabs(folder):
        folder = os.path.join(root, folder)
    shipped = os.path.join(root, PRESET_FILES)
    return PresetStore(folder,
                       defaults_file=os.path.join(shipped, "library.json"),
                       shape_keys_file=os.path.join(shipped, "shape_keys.json"),
                       gestures_file=os.path.join(shipped, "gestures.json"),
                       protected=lambda: mia_presets(root))


def create_blueprint(store, root, token=None, allowed_origins=None):
    bp = Blueprint("presets_api", __name__)
    shipped = os.path.join(root, PRESET_FILES)

    def error(message, status, details=None):
        response = jsonify({"error": message, "details": details or []})
        response.status_code = status
        return response

    def check_write():
        """returns an error response if this write request is not allowed, else None"""
        if token and not hmac.compare_digest(request.headers.get(TOKEN_HEADER, ""), token):
            return error("a valid token is needed to change presets", 401)
        origin = request.headers.get("Origin")
        # the page we served ourselves is always fine (whatever name it was reached by: LAN address, https proxy, tailscale ...)
        if origin and urlparse(origin).netloc != request.host and (allowed_origins is None or origin not in allowed_origins()):
            return error("request from an unknown origin", 403)
        if request.method in ("POST", "PUT"):
            if not request.is_json:
                return error("send the preset as application/json", 415)
            if request.content_length is not None and request.content_length > MAX_BODY:
                return error("preset too large", 413)
        return None

    def body():
        data = request.get_json(silent=True)
        if data is None:
            raise PresetError("the body is not valid JSON")
        return data

    @bp.errorhandler(PresetError)
    def handle_preset_error(exc):
        return error(exc.message, exc.status, exc.details)

    @bp.get("/api/presets")
    def list_presets():
        response = jsonify({"presets": store.list(), "version": store.version(), "token_required": bool(token),
                            "protected": sorted(store.protected())})
        response.headers["Cache-Control"] = "no-cache"
        return response

    @bp.get("/api/presets/version")
    def presets_version():
        response = jsonify({"version": store.version()})
        response.headers["Cache-Control"] = "no-cache"
        return response

    @bp.get("/api/presets/<name>")
    def get_preset(name):
        return jsonify(store.get(name))

    @bp.post("/api/presets")
    def create_preset():
        refused = check_write()
        if refused:
            return refused
        preset, corrections = store.create(body())
        logger.info(f"preset '{preset['name']}' created")
        response = jsonify({"preset": preset, "corrections": corrections, "version": store.version()})
        response.status_code = 201
        return response

    @bp.put("/api/presets/<name>")
    def update_preset(name):
        refused = check_write()
        if refused:
            return refused
        preset, corrections = store.update(name, body(), force=request.args.get("force") == "1")
        logger.info(f"preset '{name}' saved" + (f" as '{preset['name']}'" if preset["name"] != name else ""))
        return jsonify({"preset": preset, "corrections": corrections, "version": store.version()})

    @bp.delete("/api/presets/<name>")
    def delete_preset(name):
        refused = check_write()
        if refused:
            return refused
        store.delete(name, force=request.args.get("force") == "1")
        logger.info(f"preset '{name}' deleted")
        return jsonify({"deleted": name, "version": store.version()})

    @bp.get("/api/shape-keys")
    def shape_keys():
        with open(os.path.join(shipped, "shape_keys.json")) as fp:
            return jsonify(json.load(fp))

    @bp.get("/api/gestures")
    def gestures():
        with open(os.path.join(shipped, "gestures.json")) as fp:
            data = json.load(fp)["gestures"]
        return jsonify({"gestures": [{"name": g["name"], "description": g.get("description", ""),
                                      "expression": g.get("expression", "")} for g in data]})

    return bp


def init_presets_api(app, cfg, root, allowed_origins=None):
    """creates the store and registers the API at the Flask app; returns the store"""
    store = create_store(cfg, root)
    token = cfg.get(EDITOR_TOKEN_KEY) or None
    app.register_blueprint(create_blueprint(store, root, token=token, allowed_origins=allowed_origins))
    if token:
        logger.info("preset editor: changing presets needs the editor token")
    return store
