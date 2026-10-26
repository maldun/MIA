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
  GET    /api/gestures           every gesture: built in (kind "keys") and made in the editor (kind "pose", complete in "pose_gestures"), + version
  GET    /api/gestures/<name>    one gesture made in the editor
  POST   /api/gestures           create (409 if it exists or the name is a built in gesture)
  PUT    /api/gestures/<name>    overwrite; a different "name" in the body renames it
  DELETE /api/gestures/<name>    delete (409 for built in ones and ones that presets use, unless ?force=1)
  GET    /api/pose-model         the sliders of the gesture editor: angles, ranges, neutral values, descriptions
  POST   /api/expression/generate   {"description"}: the LLM makes an expression (validated, not saved)
  POST   /api/expression/match      {"description"}: the closest existing preset (no LLM, instant)
  POST   /api/expression/feedback   {"id", "decision": keep|edit|reject, "preset"?}: logged, used as examples later

Writing (POST, PUT, DELETE) needs JSON as content type (no cross-site form posts), an allowed origin if the browser
sends one, and the header X-MIA-Token if "editor_token" is set in setup_cfg.json.
"""
import hashlib
import hmac
import json
import os
import secrets
from urllib.parse import urlparse

from flask import Blueprint, g, jsonify, request

try:
    from .constants import PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR, EDITOR_TOKEN_KEY, EXPRESSION_FILE, TOKEN_HEADER
    from .constants import GESTURES_DIR_KEY, DEFAULT_GESTURES_DIR
    from .constants import EDITOR_TOKEN_FILE_KEY, DEFAULT_EDITOR_TOKEN_FILE
    from .mia_logger import logger
    from .preset_store import PresetStore, PresetError
    from .gesture_store import GestureStore
    from .pose_model import describe as describe_pose_model
    from .expression_llm import ExpressionGenerator
    from .constants import FEEDBACK_LOG_KEY, DEFAULT_FEEDBACK_LOG
except ImportError:  # used as plain script / in tests
    from constants import PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR, EDITOR_TOKEN_KEY, EXPRESSION_FILE, TOKEN_HEADER
    from constants import GESTURES_DIR_KEY, DEFAULT_GESTURES_DIR
    from constants import EDITOR_TOKEN_FILE_KEY, DEFAULT_EDITOR_TOKEN_FILE
    from mia_logger import logger
    from preset_store import PresetStore, PresetError
    from gesture_store import GestureStore
    from pose_model import describe as describe_pose_model
    from expression_llm import ExpressionGenerator
    from constants import FEEDBACK_LOG_KEY, DEFAULT_FEEDBACK_LOG

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


def resolve_token(cfg, root):
    """
    The token that changing presets needs, and where it comes from: (token or None, description).
    "editor_token" in the configuration wins ("" or false switch the token off). If the key is missing, a random
    token is created on the first start and kept in "editor_token_file" (default data/editor_token.txt, only the
    owner can read it): no secret in the configuration file, which is under version control.
    """
    if EDITOR_TOKEN_KEY in cfg:
        value = cfg[EDITOR_TOKEN_KEY]
        if isinstance(value, str) and value.strip():
            return value.strip(), "setup_cfg.json"
        return None, "switched off in setup_cfg.json"
    path = cfg.get(EDITOR_TOKEN_FILE_KEY, DEFAULT_EDITOR_TOKEN_FILE)
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    try:
        with open(path) as fp:
            token = fp.read().strip()
        if token:
            return token, path
    except OSError:
        pass
    token = secrets.token_urlsafe(16)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fp:
        fp.write(token + "\n")
    logger.info(f"preset editor: new token created in {path}")
    return token, path


def create_gesture_store(cfg, root, presets_ref):
    """
    the gesture store as configured (folder "gestures_dir"). presets_ref: a list that holds the preset store once it exists (the gesture
    store asks it which presets use a gesture and which expressions exist; the preset store asks the gesture store for the gesture names)
    """
    folder = cfg.get(GESTURES_DIR_KEY, DEFAULT_GESTURES_DIR)
    if not os.path.isabs(folder):
        folder = os.path.join(root, folder)
    shipped = os.path.join(root, PRESET_FILES)
    return GestureStore(folder, shipped_file=os.path.join(shipped, "gestures.json"),
                        in_use=lambda name: [p["name"] for p in presets_ref[0].list() if p.get("gesture") == name] if presets_ref else [],
                        expression_names=lambda: presets_ref[0].names() if presets_ref else [])


def create_store(cfg, root, gestures=None):
    """the preset store as configured (folder "presets_dir", filled from the library shipped with the character)"""
    folder = cfg.get(PRESETS_DIR_KEY, DEFAULT_PRESETS_DIR)
    if not os.path.isabs(folder):
        folder = os.path.join(root, folder)
    shipped = os.path.join(root, PRESET_FILES)
    return PresetStore(folder,
                       defaults_file=os.path.join(shipped, "library.json"),
                       shape_keys_file=os.path.join(shipped, "shape_keys.json"),
                       gestures_file=os.path.join(shipped, "gestures.json"),
                       protected=lambda: mia_presets(root),
                       gestures_provider=gestures.all_names if gestures is not None else None)


def create_generator(cfg, root, store, llm, model_name=lambda: None, gestures=None):
    """the expression generator (None without a language model function)"""
    if llm is None:
        return None
    shipped = os.path.join(root, PRESET_FILES)
    log = cfg.get(FEEDBACK_LOG_KEY, DEFAULT_FEEDBACK_LOG)
    if not os.path.isabs(log):
        log = os.path.join(root, log)
    return ExpressionGenerator(store, llm, os.path.join(shipped, "shape_keys.json"), os.path.join(shipped, "gestures.json"),
                               log_path=log, model_name=model_name,
                               gestures_provider=gestures.describe_all if gestures is not None else None)


def create_blueprint(store, root, token=None, allowed_origins=None, generator=None, gestures=None):
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

    def account():
        """the logged-in account of this request (accounts_api sets it), or None while the accounts are off: recorded as updated_by (REQ-API-009)"""
        return getattr(g, "account", None)

    def body():
        data = request.get_json(silent=True)
        if data is None:
            raise PresetError("the body is not valid JSON")
        return data

    @bp.errorhandler(PresetError)
    def handle_preset_error(exc):
        return error(exc.message, exc.status, exc.details)

    def version():
        """any change of a preset or of a gesture changes it (other devices poll this one number)"""
        if gestures is None:
            return store.version()
        return hashlib.sha1((store.version() + gestures.version()).encode()).hexdigest()[:12]

    @bp.get("/api/presets")
    def list_presets():
        response = jsonify({"presets": store.list(), "version": version(), "token_required": bool(token),
                            "protected": sorted(store.protected())})
        response.headers["Cache-Control"] = "no-cache"
        return response

    @bp.get("/api/presets/version")
    def presets_version():
        response = jsonify({"version": version()})
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
        preset, corrections = store.create(body(), author=account())
        logger.info(f"preset '{preset['name']}' created")
        response = jsonify({"preset": preset, "corrections": corrections, "version": version()})
        response.status_code = 201
        return response

    @bp.put("/api/presets/<name>")
    def update_preset(name):
        refused = check_write()
        if refused:
            return refused
        preset, corrections = store.update(name, body(), force=request.args.get("force") == "1", author=account())
        logger.info(f"preset '{name}' saved" + (f" as '{preset['name']}'" if preset["name"] != name else ""))
        return jsonify({"preset": preset, "corrections": corrections, "version": version()})

    @bp.delete("/api/presets/<name>")
    def delete_preset(name):
        refused = check_write()
        if refused:
            return refused
        store.delete(name, force=request.args.get("force") == "1")
        logger.info(f"preset '{name}' deleted")
        return jsonify({"deleted": name, "version": version()})

    @bp.get("/api/shape-keys")
    def shape_keys():
        with open(os.path.join(shipped, "shape_keys.json")) as fp:
            return jsonify(json.load(fp))

    if gestures is not None:
        @bp.get("/api/pose-model")
        def pose_model():
            return jsonify(describe_pose_model())

        @bp.get("/api/gestures")
        def list_gestures():
            response = jsonify({"gestures": gestures.describe_all(), "pose_gestures": gestures.list(), "version": gestures.version(),
                                "token_required": bool(token)})
            response.headers["Cache-Control"] = "no-cache"
            return response

        @bp.get("/api/gestures/<name>")
        def get_gesture(name):
            return jsonify(gestures.get(name))

        @bp.post("/api/gestures")
        def create_gesture():
            refused = check_write()
            if refused:
                return refused
            gesture, corrections = gestures.create(body(), author=account())
            logger.info(f"gesture '{gesture['name']}' created")
            response = jsonify({"gesture": gesture, "corrections": corrections, "version": version()})
            response.status_code = 201
            return response

        @bp.put("/api/gestures/<name>")
        def update_gesture(name):
            refused = check_write()
            if refused:
                return refused
            gesture, corrections = gestures.update(name, body(), force=request.args.get("force") == "1", author=account())
            logger.info(f"gesture '{name}' saved" + (f" as '{gesture['name']}'" if gesture["name"] != name else ""))
            return jsonify({"gesture": gesture, "corrections": corrections, "version": version()})

        @bp.delete("/api/gestures/<name>")
        def delete_gesture(name):
            refused = check_write()
            if refused:
                return refused
            gestures.delete(name, force=request.args.get("force") == "1")
            logger.info(f"gesture '{name}' deleted")
            return jsonify({"deleted": name, "version": version()})

    if gestures is None:        # without a gesture store only the gestures that come with the character are listed
        @bp.get("/api/gestures")
        def builtin_gestures():
            with open(os.path.join(shipped, "gestures.json")) as fp:
                data = json.load(fp)["gestures"]
            return jsonify({"gestures": [{"name": g["name"], "description": g.get("description", ""),
                                          "expression": g.get("expression", "")} for g in data]})

    if generator is not None:
        def description_of(data):
            if not isinstance(data, dict):
                raise PresetError("send a JSON object with a description")
            return data.get("description")

        @bp.post("/api/expression/generate")
        def generate_expression():
            refused = check_write()
            if refused:
                return refused
            description = description_of(body())
            logger.info(f"expression requested: {str(description)[:80]!r}")
            return jsonify(generator.generate(description))

        @bp.post("/api/expression/match")
        def match_expression():
            refused = check_write()
            if refused:
                return refused
            return jsonify(generator.match(description_of(body())))

        @bp.post("/api/expression/feedback")
        def expression_feedback():
            refused = check_write()
            if refused:
                return refused
            data = body()
            if not isinstance(data, dict):
                raise PresetError("send a JSON object")
            return jsonify(generator.feedback(data.get("id"), data.get("decision"), data.get("preset")))

    return bp


def init_presets_api(app, cfg, root, allowed_origins=None, llm=None, model_name=lambda: None):
    """creates the stores and registers the API at the Flask app; returns the preset store (llm: function (messages, schema) -> text)"""
    presets_ref = []
    gestures = create_gesture_store(cfg, root, presets_ref)
    store = create_store(cfg, root, gestures)
    presets_ref.append(store)
    generator = create_generator(cfg, root, store, llm, model_name, gestures)
    app.config["EXPRESSION_GENERATOR"] = generator
    app.config["GESTURE_STORE"] = gestures
    token, source = resolve_token(cfg, root)
    app.config["EDITOR_TOKEN_INFO"] = (token, source)
    app.register_blueprint(create_blueprint(store, root, token=token, allowed_origins=allowed_origins, generator=generator, gestures=gestures))
    logger.info("preset editor: changing presets needs the editor token (%s)" % source if token else "preset editor: no token, everyone who can reach the page may change presets")
    return store
