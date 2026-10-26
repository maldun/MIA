"""The records of tasks, memos and memory for the page (IF-101 v1 items), kept in the tables of the Storage layer (IF-102, IF-302).
Every user sees and changes all of them (CON-6); a text is stored and returned as it was written (FR-28), only a blank text is refused.
The account comes from g.account (the guard of accounts_api); without accounts the author is "page". Each change is announced as `item_changed`."""
import os
import re
import time

from flask import Blueprint, g, jsonify, request

try:
    from .storage import StorageError
except ImportError:
    from storage import StorageError

KINDS = ("tasks", "memos", "memory")
DUE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"          # what the chat service compares at the time check (recite_due)
DUE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def valid_due(due):
    """an ISO time in UTC with a Z, to the second; strptime alone would accept 2026-1-2T9:0:0Z, and the comparison is one of strings"""
    if not isinstance(due, str) or not DUE_SHAPE.fullmatch(due):
        return False
    try:
        time.strptime(due, DUE_FORMAT)
    except ValueError:
        return False
    return True


def _new_id(created):
    return "%017d-%s" % (int(created * 1_000_000), os.urandom(2).hex())          # sorts like the creation


def create_items_blueprint(storage, emit, clock=time.time):
    bp = Blueprint("items_api", __name__)

    def refuse(status, code, rule=None):
        body = {"error": code}
        if rule:
            body["rule"] = rule
        return jsonify(body), status

    def author():
        return getattr(g, "account", None) or "page"

    def record_of(entry):
        doc = entry["doc"]
        record = {"id": entry["id"], "text": doc["text"], "author": entry["author"], "created": doc["created"]}
        for field in ("source", "due"):
            if doc.get(field):
                record[field] = doc[field]
        return record

    @bp.get("/api/items")
    def items():
        kind = request.args.get("kind")
        if kind not in KINDS:
            return refuse(404, "unknown_kind")
        entries = [storage.get(kind, i) for i in storage.ids(kind)]
        return jsonify([record_of(e) for e in sorted(entries, key=lambda e: e["id"])])

    @bp.post("/api/items")
    def save():
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        kind, item_id, text, source, due = body.get("kind"), body.get("id"), body.get("text"), body.get("source"), body.get("due")
        if kind not in KINDS:
            return refuse(404, "unknown_kind")
        if not isinstance(text, str) or not text.strip():
            return refuse(422, "empty_text")
        if kind == "memory" and not source:
            return refuse(422, "invalid_item", "source")
        if due is not None and (kind != "tasks" or not valid_due(due)):
            return refuse(422, "invalid_item", "due")                        # only a task falls due (IF-101 v6)
        old = {}
        if item_id is None:
            item_id, created = _new_id(clock()), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock()))
        else:
            try:
                old = storage.get(kind, item_id)["doc"]
                created = old["created"]
            except StorageError:
                return refuse(404, "not_found")
        doc = {"text": text, "created": created}
        if source:
            doc["source"] = source
        if due:
            doc["due"] = due
            if old.get("recited") and old.get("due") == due:
                doc["recited"] = old["recited"]               # a change of the text does not say it again; a new due time does
        storage.put(kind, item_id, doc, author())
        emit("item_changed", {"kind": kind, "id": item_id, "author": author(), "deleted": False})
        return jsonify(record_of(storage.get(kind, item_id)))

    @bp.delete("/api/items")
    def delete():
        kind, item_id = request.args.get("kind"), request.args.get("id")
        if kind not in KINDS:
            return refuse(404, "unknown_kind")
        try:
            storage.delete(kind, item_id, author())
        except StorageError:
            return refuse(404, "not_found")
        emit("item_changed", {"kind": kind, "id": item_id, "author": author(), "deleted": True})
        return jsonify({"deleted": True})

    return bp
