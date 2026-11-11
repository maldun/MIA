"""Mock of the part `transforms` of IF-203 v1 (G-V2.TOOLBOX, proposal A-111; protected once installed). Complexity 2: an in-memory library for the kind `transforms`.
One record per transform ID with versions 1..n (a version is a new immutable save), and next to it one meta record per ID (the table transform_meta of IF-302 v8):
trust (untrusted | trusted), lifecycle (draft | tested | retired) and the optional reason, evidence, baseline_allowed, shipped and changed_by.
A new version of the code leaves the meta record as it is (REQ-WFM-092). It does not run any code and does not know who the owner is (that is a rule of the Workflow management).
Run against the contract suite tests/acceptance/contract/test_if_203_v1_transforms.py (TR-TOOLBOX-001)."""
import copy
import itertools

try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

TRUST = ("untrusted", "trusted")
LIFECYCLE = ("draft", "tested", "retired")
OPTIONAL = {"reason": str, "evidence": str, "baseline_allowed": bool, "shipped": bool, "changed_by": str}
_clock = itertools.count(1)


class TransformLibraryMock:
    def __init__(self):
        self._versions, self._meta = {}, {}

    def _known(self, kind, record_id=None):
        if kind != "transforms":
            raise ServiceError("not_found", detail=kind)
        if record_id is not None and record_id not in self._versions:
            raise ServiceError("not_found", detail=record_id)

    def list_ids(self, kind):
        self._known(kind)
        return sorted(self._versions)

    def read(self, kind, record_id, version=None):
        self._known(kind, record_id)
        rows = self._versions[record_id]
        number = len(rows) if version is None else version
        if not isinstance(number, int) or not 1 <= number <= len(rows):
            raise ServiceError("not_found", detail=version)
        entry = dict(rows[number - 1], doc=copy.deepcopy(rows[number - 1]["doc"]))
        entry.update(trust=self._meta[record_id]["trust"], lifecycle=self._meta[record_id]["lifecycle"])
        return entry

    def save(self, kind, record_id, doc, author, expected_version=None):
        self._known(kind)
        rows = self._versions.setdefault(record_id, [])
        if expected_version is not None and expected_version != len(rows):
            raise ServiceError("conflict", detail={"current": len(rows)})
        rows.append({"id": record_id, "version": len(rows) + 1, "author": author, "time": next(_clock), "doc": copy.deepcopy(doc)})
        self._meta.setdefault(record_id, {"trust": "untrusted", "lifecycle": "draft"})      # a new transform starts untrusted and draft; a new version keeps the meta record
        return {"version": len(rows)}

    def history(self, kind, record_id):
        self._known(kind, record_id)
        return [{"version": r["version"], "author": r["author"], "time": r["time"]} for r in self._versions[record_id]]

    def get_meta(self, record_id):
        self._known("transforms", record_id)
        return dict(self._meta[record_id])

    def get_trust(self, record_id):
        return self.get_meta(record_id)["trust"]

    def get_lifecycle(self, record_id):
        return self.get_meta(record_id)["lifecycle"]

    def set_meta(self, record_id, author, **fields):
        """Sets trust, lifecycle and the optional fields in one new version of the meta record; an unknown field or value is invalid/schema with the field as detail."""
        self._known("transforms", record_id)
        for name, value in fields.items():
            if (name == "trust" and value not in TRUST) or (name == "lifecycle" and value not in LIFECYCLE) \
                    or (name in OPTIONAL and type(value) is not OPTIONAL[name]) or (name not in OPTIONAL and name not in ("trust", "lifecycle")):
                raise ServiceError("invalid", rule="schema", detail=name)
        self._meta[record_id].update(fields, changed_by=author)
        return dict(self._meta[record_id])

    def set_trust(self, record_id, trust, author):
        return {"trust": self.set_meta(record_id, author, trust=trust)["trust"]}

    def set_lifecycle(self, record_id, lifecycle, author, evidence=None):
        fields = {"lifecycle": lifecycle}
        if evidence is not None:
            fields["evidence"] = evidence
        return {"lifecycle": self.set_meta(record_id, author, **fields)["lifecycle"]}
