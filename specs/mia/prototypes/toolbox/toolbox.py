"""PROTOTYPE (Status: Prototype, not verified): the toolbox of G-V2.TOOLBOX in one file, in memory.

Answers the question: do the outcomes OC-1..OC-3 of the goal hold with a small, plain design? Everything is a draft for the developer's carry-over table.
Reuses: library/nodes/<id>/<version>.json (shipped nodes, REQ-WFM-056) and jsonschema (already pinned). No storage, no graph, no model.
Trust (may it run) and lifecycle (draft, tested, retired) are two separate fields (REQ-WFM-051, -067).
"""
import json
import pathlib

import jsonschema

OWNER = "owner"
TRUST = ("untrusted", "trusted")
LIFECYCLE = ("draft", "tested", "retired")
EXCHANGE_SCHEMA = {
    "type": "object", "required": ["id", "version", "inputs", "outputs", "code"],
    "properties": {"id": {"type": "string", "minLength": 1}, "version": {"type": "integer", "minimum": 1},
                   "inputs": {"type": "object"}, "outputs": {"type": "object"}, "code": {"type": "string"}},
}


class ToolboxError(Exception):
    def __init__(self, code, why):
        super().__init__("%s: %s" % (code, why))
        self.code, self.why = code, why


class Toolbox:
    def __init__(self):
        self._items = {}

    # --- filling the toolbox -------------------------------------------------
    def seed_shipped(self, nodes_dir):
        """REQ-WFM-056: MIA's own nodes are trusted. They carry no code text here (they are modules of MIA), only their record."""
        latest = {}
        for path in sorted(pathlib.Path(nodes_dir).glob("*/*.json")):
            doc = json.loads(path.read_text())
            if doc.get("status") != "retired" and doc["version"] > latest.get(doc["id"], {"version": 0})["version"]:
                latest[doc["id"]] = doc          # finding: a node ID has several versions; the toolbox ID is unique, so one version per ID is seeded
        for doc in latest.values():
            self._add(doc["id"], doc["version"], doc.get("inputs", {}), doc.get("outputs", {}), None, "trusted", "shipped", "tested")

    def import_transform(self, text):
        """REQ-WFM-052/053: stored untrusted whatever the file claims; the code text is never compiled or run here."""
        try:
            doc = json.loads(text)
            jsonschema.validate(doc, EXCHANGE_SCHEMA)
        except (ValueError, jsonschema.ValidationError) as err:
            raise ToolboxError("invalid_file", str(err).splitlines()[0])
        self._add(doc["id"], doc["version"], doc["inputs"], doc["outputs"], doc["code"], "untrusted", "imported", "draft")
        return doc["id"]

    def _add(self, tid, version, inputs, outputs, code, trust, origin, lifecycle):
        old = self._items.get(tid)
        if old and version <= old["version"]:
            raise ToolboxError("duplicate_id", "%s version %s is not newer than %s" % (tid, version, old["version"]))   # REQ-WFM-050
        if old:      # decision 1 and 5 (owner 2026-11-08): one entry per ID, a newer version replaces the code, trust and lifecycle carry over
            old.update(version=version, inputs=inputs, outputs=outputs, code=code)
            return
        self._items[tid] = {"id": tid, "version": version, "inputs": inputs, "outputs": outputs, "code": code,
                            "trust": trust, "origin": origin, "lifecycle": lifecycle, "evidence": None, "baseline_ok": False,
                            "reason": "imported from outside MIA, not reviewed" if trust == "untrusted" else None}

    def export_transform(self, tid):
        item = self.look_up(tid)
        if item["code"] is None:
            raise ToolboxError("not_exportable", "a shipped node is a module of MIA, it has no code text")
        return json.dumps({k: item[k] for k in ("id", "version", "inputs", "outputs", "code")}, sort_keys=True)

    # --- looking up ----------------------------------------------------------
    def look_up(self, tid):
        if tid not in self._items:
            raise ToolboxError("not_found", tid)
        return dict(self._items[tid])                                    # OC-1: shows trust and the reason

    def offer(self):
        """REQ-WFM-070 / OC-3: what a new graph may pick; retired items are left out."""
        return sorted(i for i, t in self._items.items() if t["lifecycle"] != "retired")

    # --- changing status -----------------------------------------------------
    def set_trust(self, tid, value, account):
        if value not in TRUST:
            raise ToolboxError("invalid_trust", value)
        item = self._items[self.look_up(tid)["id"]]
        if value == "trusted" and account != OWNER:
            raise ToolboxError("owner_only", "only the owner marks a transform trusted; the status stays %s" % item["trust"])   # OC-2
        item["trust"], item["reason"] = value, (None if value == "trusted" else "set untrusted by %s" % account)

    def set_lifecycle(self, tid, value, account, evidence=None, allow_baseline=False):
        if value not in LIFECYCLE:
            raise ToolboxError("invalid_lifecycle", value)
        if value == "tested" and not evidence:
            raise ToolboxError("evidence_missing", "a change to tested names the check or run that justifies it")   # REQ-WFM-067
        item = self._items[self.look_up(tid)["id"]]
        if allow_baseline and account != OWNER:
            raise ToolboxError("owner_only", "only the owner lets an untrusted transform run as a baseline")
        item["lifecycle"], item["evidence"] = value, evidence or item["evidence"]
        item["baseline_ok"] = item["baseline_ok"] or allow_baseline      # decision 3: the owner's one-time flag, given when retiring

    # --- running -------------------------------------------------------------
    def run(self, tid, args, as_baseline=False):
        """Only here is code of a transform executed: trusted transforms for a graph, any transform (even retired) when a check names it
        as its baseline (REQ-WFM-068). PROTOTYPE: exec in the MIA process, unsandboxed, as SC-09 / TD-24 accept for trusted code."""
        item = self.look_up(tid)
        if item["trust"] != "trusted" and not (as_baseline and item["baseline_ok"]):
            raise ToolboxError("untrusted", "%s is %s: %s" % (tid, item["trust"], item["reason"]))
        if item["lifecycle"] == "retired" and not as_baseline:
            raise ToolboxError("retired", "%s is retired and runs only as the baseline of a check" % tid)
        if item["code"] is None:
            raise ToolboxError("no_code", "shipped nodes run through the old runner in this prototype")
        scope = {}
        exec(compile(item["code"], tid, "exec"), scope)
        return scope["run"](args)
