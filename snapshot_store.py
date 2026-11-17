"""Snapshots of the skill set (part snapshotStore, FR-47, G-V2.SNAPSHOT, task T-SN-01; REQ-WFM-061 to 066).

A snapshot is a named record that is written once: every item of the kinds skills, workflows, context_graphs and transforms with its current version (a transform also
with trust and lifecycle) and the model pins in force. A restore never deletes a version: it first keeps the current state as a snapshot of its own, then moves the
pointer of every item to the stored version (`set_current_version`, A-121, D-241; `restore` of IF-203 keeps its v0 meaning and is not used here).

`library` offers IF-203 v2 as far as snapshots need it: list_ids(kind), read(kind, id, version=None), save(kind, id, doc, author), set_current_version(kind, id, version, author),
get_trust(id), set_trust(id, trust, author), get_lifecycle(id), set_lifecycle(id, lifecycle, author, evidence=None), pins(); the snapshots themselves are records of the kind
`snapshots`. `accounts.is_owner(account)` says whether an account is the owner (the account that creates accounts, REQ-WFM-066).
"""
import time

KINDS = ("skills", "workflows", "context_graphs", "transforms")
FORMAT = 1          # raised when the meaning of the stored record changes (A-121: the record is open, a reader ignores what it does not know)


class Conflict(Exception):
    """a snapshot name that exists (A-121: `conflict`, D-240 O3)"""


class Refused(Exception):
    """a request of an account that is not the owner (REQ-WFM-066)"""


class NotFound(Exception):
    """a snapshot name that does not exist (A-121: `not_found`)"""


class SnapshotStore:
    def __init__(self, library, accounts, clock=time.time):
        self.library, self.accounts, self.clock = library, accounts, clock

    def _owner_only(self, account):
        if not self.accounts.is_owner(account):
            raise Refused(account)

    def _items(self):
        """every item of the four kinds with its current version; a transform also with trust and lifecycle (REQ-WFM-061)"""
        items = []
        for kind in KINDS:
            for record_id in self.library.list_ids(kind):
                item = {"kind": kind, "id": record_id, "version": self.library.read(kind, record_id)["version"]}
                if kind == "transforms":
                    item.update(trust=self.library.get_trust(record_id), lifecycle=self.library.get_lifecycle(record_id))
                items.append(item)
        return items

    def _write(self, name, account):
        if not isinstance(name, str) or not name:
            raise ValueError("a snapshot needs a name")
        if name in self.library.list_ids("snapshots"):
            raise Conflict(name)
        doc = {"name": name, "time": self.clock(), "author": account, "items": self._items(), "pins": self.library.pins(), "format": FORMAT}
        self.library.save("snapshots", name, doc, account)      # written once: the name was free above and nothing else changes a snapshot
        return {"name": name, "time": doc["time"], "author": account}

    def snapshot(self, name, account):
        """REQ-WFM-061, 066: stores the state under `name`; a non-owner is refused with Refused, a name that exists with Conflict"""
        self._owner_only(account)
        return self._write(name, account)

    def read_snapshot(self, name):
        """the record as stored: {"name", "time", "author", "items": [{"kind", "id", "version", ("trust", "lifecycle" for a transform)}], "pins": {...}, ...}"""
        if name not in self.library.list_ids("snapshots"):
            raise NotFound(name)
        return self.library.read("snapshots", name)["doc"]

    def list_snapshots(self, account):
        """REQ-WFM-062: [{"name", "time", "author"}], oldest first, exactly these three fields; owner only"""
        self._owner_only(account)
        docs = [self.read_snapshot(name) for name in self.library.list_ids("snapshots")]
        return [{"name": d["name"], "time": d["time"], "author": d["author"]} for d in sorted(docs, key=lambda d: (d["time"], d["name"]))]

    def restore_snapshot(self, name, account):
        """REQ-WFM-063 to 066: keeps the current state as "before restore of <name>" (` (2)`, ` (3)` ... when that name exists; author: the owner), then gives every item the
        version, trust and lifecycle of the snapshot and deletes no version. If a step fails, the items already changed are changed back, the kept snapshot stays and the
        error is raised. A non-owner is refused and nothing changes."""
        self._owner_only(account)
        stored = self.read_snapshot(name)
        kept = "before restore of %s" % name
        taken, count = set(self.library.list_ids("snapshots")), 1
        while kept in taken:
            count += 1
            kept = "before restore of %s (%d)" % (name, count)
        self._write(kept, account)
        undo = []          # what each item was before, in the order changed: the way back
        try:
            for item in stored["items"]:
                kind, record_id = item["kind"], item["id"]
                undo.append(self._state_of(kind, record_id))
                self.library.set_current_version(kind, record_id, item["version"], account)
                if kind == "transforms":
                    self.library.set_trust(record_id, item["trust"], account)
                    self.library.set_lifecycle(record_id, item["lifecycle"], account, evidence="restore of %s" % name)
        except Exception:
            for before in reversed(undo):
                self._put_back(before, account)
            raise
        return {"kept_as": kept}

    def _state_of(self, kind, record_id):
        state = {"kind": kind, "id": record_id, "version": self.library.read(kind, record_id)["version"]}
        if kind == "transforms":
            state.update(trust=self.library.get_trust(record_id), lifecycle=self.library.get_lifecycle(record_id))
        return state

    def _put_back(self, state, account):
        self.library.set_current_version(state["kind"], state["id"], state["version"], account)
        if state["kind"] == "transforms":
            self.library.set_trust(state["id"], state["trust"], account)
            self.library.set_lifecycle(state["id"], state["lifecycle"], account)
