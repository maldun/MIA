"""The trust of sources and the persona for the page (IF-101 v1 trust, set_trust, persona, save_persona).
Trust is the table of source_trust.py: the sources are its classes, a change goes into the override file (the default table stays as shipped, RV14 T2)
and the pipelines read it from there. The persona is a JSON file with a `text`, shared by all users (CON-6), stored as written.
Each change is announced as `trust_changed` / `persona_changed`; the account comes from g.account, "page" without accounts."""
import json
import math
import os
import tempfile
import threading
import time

from flask import Blueprint, g, jsonify, request

try:
    from .source_trust import DEFAULT_FILE, TrustTable
except ImportError:
    from source_trust import DEFAULT_FILE, TrustTable


def _write(path, data):
    """whole file or nothing: a crash must not leave half a table that the pipelines then skip"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _read(path):
    try:
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def create_trust_persona_blueprint(trust_file, persona_file, emit):
    bp = Blueprint("trust_persona_api", __name__)
    lock = threading.Lock()

    def refuse(status, code):
        return jsonify({"error": code}), status

    def author():
        return getattr(g, "account", None) or "page"

    def table():
        return TrustTable.load(DEFAULT_FILE, trust_file).classes

    @bp.get("/api/trust")
    def trust():
        return jsonify({name: float(entry["prior"]) for name, entry in table().items()})

    @bp.post("/api/trust")
    def set_trust():
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        source, value = body.get("source"), body.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            return refuse(422, "invalid_trust")
        with lock:
            classes = table()
            if not isinstance(source, str) or source not in classes:
                return refuse(404, "not_found")
            old = float(classes[source]["prior"])
            user = _read(trust_file)
            entry = dict(classes[source], prior=value, set=time.strftime("%Y-%m-%d"))     # the reason of the default stays with the number
            user.setdefault("classes", {})[source] = entry
            _write(trust_file, user)
        emit("trust_changed", {"source": source, "old": old, "new": value, "author": author()})
        return jsonify({"source": source, "old": old, "new": value})

    @bp.get("/api/persona")
    def persona():
        doc = _read(persona_file)
        return jsonify(doc if isinstance(doc.get("text"), str) else {"text": ""})

    @bp.post("/api/persona")
    def save_persona():
        body = request.get_json(silent=True)
        doc = body.get("doc") if isinstance(body, dict) else None
        if not isinstance(doc, dict) or not isinstance(doc.get("text"), str) or not doc["text"].strip():
            return refuse(422, "invalid_persona")
        with lock:
            _write(persona_file, doc)
        emit("persona_changed", {"author": author()})
        return jsonify(doc)

    return bp
