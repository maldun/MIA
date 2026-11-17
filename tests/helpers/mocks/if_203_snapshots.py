"""Mock of IF-203 v2, the pointer and the snapshots of the workflow library (G-V2.SNAPSHOT, A-121; protected once installed). Complexity 2: an in-memory library for
the kinds skills, workflows, context_graphs, transforms and snapshots, next to the v0 mock (if_203_workflow_library.py) and the v1 mock (if_203_transforms.py), which stay as
they are (D-241 D-b: `restore` keeps its v0 meaning, a new version with the old content).
One record per item with versions 1..n, and the table `current_versions` as a pointer per item (IF-302 v13): `read` without a version gives the current version, `save`
writes max+1 and moves the pointer, `set_current_version` moves it and creates nothing. The owner is the account that creates accounts (REQ-WFM-066); the mock is
given it. Run against tests/acceptance/contract/test_if_203_v2_snapshots.py (TR-SNAPSHOT-001).
`fail_set_current_version_at = n` is a test seam: the n-th pointer move inside `restore_snapshot` raises (golden example 12)."""
import copy
import itertools

try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

KINDS = ("skills", "workflows", "context_graphs", "transforms")
TRUST = ("untrusted", "trusted")
LIFECYCLE = ("draft", "tested", "retired")
_clock = itertools.count(1)


class SnapshotLibraryMock:
    def __init__(self, owner="anna", pins=None):
        self.owner = owner
        self._pins = dict(pins if pins is not None else {"MP-light": "gemma4:12b-it-qat"})
        self._rows, self._pointer, self._moves = {}, {}, {}      # (kind, id) -> [row per version]; current version; the moves of the pointer (kept, never deleted)
        self._meta = {}                                          # transform id -> {"trust", "lifecycle", "evidence"?}
        self._snapshots = {}                                     # name -> the stored document (written once)
        self.fail_set_current_version_at = None
        self._restoring = 0

    # --- items ---------------------------------------------------------------------------------------------------------------------------
    def _known(self, kind, record_id=None, extra=()):
        if kind not in KINDS + tuple(extra):
            raise ServiceError("not_found", detail=kind)
        if record_id is not None and (kind, record_id) not in self._rows:
            raise ServiceError("not_found", detail=record_id)

    def list_ids(self, kind):
        self._known(kind)
        return sorted(i for (k, i) in self._rows if k == kind)

    def read(self, kind, record_id, version=None):
        self._known(kind, record_id)
        rows = self._rows[(kind, record_id)]
        number = self._pointer[(kind, record_id)] if version is None else version
        if type(number) is not int or not 1 <= number <= len(rows):
            raise ServiceError("not_found", detail=version)
        entry = dict(rows[number - 1], doc=copy.deepcopy(rows[number - 1]["doc"]))
        if kind == "transforms":
            entry.update(trust=self._meta[record_id]["trust"], lifecycle=self._meta[record_id]["lifecycle"])
        return entry

    def save(self, kind, record_id, doc, author, expected_version=None):
        self._known(kind)
        key = (kind, record_id)
        rows = self._rows.setdefault(key, [])
        current = self._pointer.get(key, 0)
        if expected_version is not None and expected_version != current:
            raise ServiceError("conflict", detail={"current": current})      # checked against the current version, not the newest
        rows.append({"id": record_id, "version": len(rows) + 1, "author": author, "time": next(_clock), "doc": copy.deepcopy(doc)})
        self._pointer[key] = len(rows)                                         # a save writes max+1 and moves the pointer
        self._moves.setdefault(key, []).append((len(rows), "save"))
        if kind == "transforms":
            self._meta.setdefault(record_id, {"trust": "untrusted", "lifecycle": "draft"})
        return {"version": len(rows)}

    def history(self, kind, record_id):
        self._known(kind, record_id)
        return [{"version": r["version"], "author": r["author"], "time": r["time"]} for r in self._rows[(kind, record_id)]]

    def restore(self, kind, record_id, version, author):
        """IF-203 v0 meaning, unchanged: a new version with the content of `version`"""
        return self.save(kind, record_id, self.read(kind, record_id, version)["doc"], author)

    def set_current_version(self, kind, record_id, version, author):
        self._known(kind, record_id)
        if type(version) is not int or not 1 <= version <= len(self._rows[(kind, record_id)]):
            raise ServiceError("invalid", rule="schema", detail="version")
        if self._restoring:
            self._restoring += 1
            if self.fail_set_current_version_at == self._restoring - 1:
                raise ServiceError("unavailable", detail="injected")
        self._pointer[(kind, record_id)] = version
        self._moves.setdefault((kind, record_id), []).append((version, "set_current_version"))
        return {"version": version}

    # --- transforms ----------------------------------------------------------------------------------------------------------------------
    def get_meta(self, record_id):
        self._known("transforms", record_id)
        return dict(self._meta[record_id])

    def get_trust(self, record_id):
        return self.get_meta(record_id)["trust"]

    def get_lifecycle(self, record_id):
        return self.get_meta(record_id)["lifecycle"]

    def set_trust(self, record_id, trust, author):
        self._known("transforms", record_id)
        if trust not in TRUST:
            raise ServiceError("invalid", rule="schema", detail="trust")
        self._meta[record_id]["trust"] = trust
        return {"trust": trust}

    def set_lifecycle(self, record_id, lifecycle, author, evidence=None):
        self._known("transforms", record_id)
        if lifecycle not in LIFECYCLE:
            raise ServiceError("invalid", rule="schema", detail="lifecycle")
        self._meta[record_id]["lifecycle"] = lifecycle
        if evidence is not None:
            self._meta[record_id]["evidence"] = evidence
        return {"lifecycle": lifecycle}

    def pins(self):
        return dict(self._pins)

    # --- snapshots -----------------------------------------------------------------------------------------------------------------------
    def _owner_only(self, account):
        if account != self.owner:
            raise ServiceError("forbidden")

    def _write_snapshot(self, name, account):
        if not isinstance(name, str) or not name:
            raise ServiceError("invalid", rule="schema", detail="name")
        if name in self._snapshots:
            raise ServiceError("conflict", detail=name)
        items = []
        for kind in KINDS:
            for record_id in self.list_ids(kind):
                item = {"kind": kind, "id": record_id, "version": self._pointer[(kind, record_id)]}
                if kind == "transforms":
                    item.update(trust=self._meta[record_id]["trust"], lifecycle=self._meta[record_id]["lifecycle"])
                items.append(item)
        doc = {"name": name, "time": next(_clock), "author": account, "items": items, "pins": self.pins(), "format": 1}
        self._snapshots[name] = doc
        return {"name": name, "time": doc["time"], "author": account}

    def snapshot(self, name, account):
        self._owner_only(account)
        return self._write_snapshot(name, account)

    def read_snapshot(self, name):
        if name not in self._snapshots:
            raise ServiceError("not_found", detail=name)
        return copy.deepcopy(self._snapshots[name])

    def list_snapshots(self, account):
        self._owner_only(account)
        return [{"name": d["name"], "time": d["time"], "author": d["author"]} for d in sorted(self._snapshots.values(), key=lambda d: d["time"])]

    def restore_snapshot(self, name, account):
        self._owner_only(account)
        stored = self.read_snapshot(name)
        kept = "before restore of %s" % name
        suffix = itertools.count(2)
        while kept in self._snapshots:
            kept = "before restore of %s (%d)" % (name, next(suffix))
        self._write_snapshot(kept, account)
        before = ({k: v for k, v in self._pointer.items()}, {k: dict(v) for k, v in self._meta.items()})
        self._restoring = 1
        try:
            for item in stored["items"]:
                self.set_current_version(item["kind"], item["id"], item["version"], account)
                if item["kind"] == "transforms":
                    self.set_trust(item["id"], item["trust"], account)
                    self.set_lifecycle(item["id"], item["lifecycle"], account, evidence="restore of %s" % name)
        except Exception:
            self._pointer.clear(); self._pointer.update(before[0])     # the items already changed are changed back; the automatic snapshot stays
            self._meta.clear(); self._meta.update(before[1])
            raise
        finally:
            self._restoring = 0
        return {"kept_as": kept}
