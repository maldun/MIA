"""The toolbox of the Workflow management (N-2.3, G-V2.TOOLBOX T-01 to T-05): one entry per transform ID, with a trust status and a lifecycle.

The toolbox keeps no state of its own: entries, versions, trust and lifecycle live in the library part `transforms` of IF-203 v1 (tests: tests/helpers/mocks/if_203_transforms.py),
so the real library of T-06 replaces the mock without a change here. T-01 is done; T-02 to T-05 add their rules (marked below) to this module.
- Toolbox(library, is_owner, events): `is_owner(account)` says whether an account is the owner (REQ-WFM-066), `events.record(event)` takes the event of REQ-WFM-093 (IF-401).
- import_transform(text, author) -> the transform ID; the exchange form is one JSON text with id, version, inputs, outputs and code (a field `status` in it is ignored);
  a text that fails the exchange schema raises ToolboxError("invalid_file") naming the first problem and stores nothing; an ID that exists with an equal or lower version raises ToolboxError("duplicate_id") naming the ID; a higher version replaces the code and keeps trust and lifecycle
  (REQ-WFM-092); the code text is never compiled or run here (REQ-WFM-053).
- export_transform(id) -> the exchange text.
- look_up(id) -> {"id", "version", "trust", "lifecycle", "reason", "evidence", "baseline_allowed", "shipped"}; `reason` says why a transform is untrusted.
- set_trust(id, value, account), set_lifecycle(id, value, account, evidence=None, allow_baseline=False): a value outside the lists raises ToolboxError("invalid_trust" or
  "invalid_lifecycle") and the status stays as it was.
- run(id, args) -> the result of the code text's run(args); an untrusted transform raises ToolboxError("untrusted").
ToolboxError has `code` and `why` (a text for the person).
Still stubs or minimal until their task: owner-only rules (T-03), evidence, retired and baseline (T-04), seed_shipped and shipped export (T-05).
"""
import json

import jsonschema

TRUST = ("untrusted", "trusted")
LIFECYCLE = ("draft", "tested", "retired")
# Why a transform is untrusted (REQ-WFM-090): every import is untrusted, so this is the one reason that exists.
REASON_IMPORTED = "It came from outside MIA and was not reviewed."
# The exchange form (REQ-WFM-055). Extra fields such as `status` are allowed and dropped on import.
EXCHANGE_SCHEMA = {
    "type": "object",
    "required": ["id", "version", "inputs", "outputs", "code"],
    "properties": {"id": {"type": "string", "minLength": 1}, "version": {"type": "integer", "minimum": 1},
                   "inputs": {"type": "object"}, "outputs": {"type": "object"}, "code": {"type": "string"}},
}


class ToolboxError(Exception):
    def __init__(self, code, why=""):
        super().__init__("%s: %s" % (code, why))
        self.code, self.why = code, why


class Toolbox:
    def __init__(self, library, is_owner, events):
        self.library, self.is_owner, self.events = library, is_owner, events

    def _latest(self, tid):
        return self.library.read("transforms", tid)

    @staticmethod
    def _checked(text):
        """The parsed exchange file, or ToolboxError("invalid_file") naming the first problem; nothing is compiled or run (REQ-WFM-053)."""
        try:
            file = json.loads(text)
        except ValueError as error:
            raise ToolboxError("invalid_file", "The file is not JSON: %s" % error)
        problems = sorted(jsonschema.Draft202012Validator(EXCHANGE_SCHEMA).iter_errors(file), key=lambda e: list(map(str, e.path)))
        if problems:
            raise ToolboxError("invalid_file", problems[0].message)
        return file

    def import_transform(self, text, author):
        file = self._checked(text)
        tid, version = file["id"], file["version"]
        # `status` of the file is dropped: what a file says about its own trust never counts (REQ-WFM-052).
        doc = {key: file[key] for key in ("id", "version", "inputs", "outputs", "code")}
        if tid not in self.library.list_ids("transforms"):
            self.library.save("transforms", tid, doc, author)
            self.library.set_meta(tid, author, reason=REASON_IMPORTED)
            return tid
        old = self._latest(tid)
        old_version = old["doc"]["version"]
        if version <= old_version:
            raise ToolboxError("duplicate_id", "%s exists in version %s; version %s is not newer." % (tid, old_version, version))
        self.library.save("transforms", tid, doc, author)       # trust and lifecycle stay with the meta record (REQ-WFM-092)
        if old["trust"] == "trusted":
            self.events.record({"id": tid, "old_version": old_version, "new_version": version, "author": author})
        return tid

    def export_transform(self, tid):
        return json.dumps(self._latest(tid)["doc"], sort_keys=True)

    def look_up(self, tid):
        entry, meta = self._latest(tid), self.library.get_meta(tid)
        untrusted = entry["trust"] == "untrusted"
        return {"id": tid, "version": entry["doc"]["version"], "trust": entry["trust"], "lifecycle": entry["lifecycle"],
                "reason": meta.get("reason", "") if untrusted else "", "evidence": meta.get("evidence"),
                "baseline_allowed": meta.get("baseline_allowed", False), "shipped": meta.get("shipped", False)}

    def offer(self):
        return sorted(self.library.list_ids("transforms"))       # retired ones are left out in T-04

    def set_trust(self, tid, value, account):
        if value not in TRUST:
            raise ToolboxError("invalid_trust", "Trust is untrusted or trusted, not %r." % (value,))
        self.library.set_trust(tid, value, account)

    def set_lifecycle(self, tid, value, account, evidence=None, allow_baseline=False):
        if value not in LIFECYCLE:
            raise ToolboxError("invalid_lifecycle", "Lifecycle is draft, tested or retired, not %r." % (value,))
        self.library.set_lifecycle(tid, value, account, evidence)

    def run(self, tid, args, as_baseline=False):
        if self._latest(tid)["trust"] != "trusted":
            raise ToolboxError("untrusted", "%s is not trusted and does not run." % tid)
        namespace = {}
        exec(self._latest(tid)["doc"]["code"], namespace)       # trusted code runs in the MIA process (SC-09 accepted); only here, never on import
        return namespace["run"](args)

    def seed_shipped(self, nodes_dir):
        return None
