"""Snapshots of the skill set (part snapshotStore, FR-47, G-V2.CONVERT). STUB until task T-CV-05 of plan.md.

Never raises, returns values outside the real vocabulary, so the acceptance tests fail on an assertion. The signatures are the ones the red tests assume.
`library` offers IF-203 v1 as far as snapshots need it: list_ids(kind), read(kind, id, version=None), save(kind, id, doc, author), history(kind, id),
restore(kind, id, version, author) (the item gets that version as its current one, nothing is created or deleted), get_trust(id), set_trust(id, trust, author),
get_lifecycle(id), set_lifecycle(id, lifecycle, author), pins(); kinds skills, workflows, context_graphs, transforms and snapshots. `accounts.is_owner(account)`
says whether an account is the owner (the account that creates accounts, REQ-WFM-066).
"""
import time


class Refused(Exception):
    """a request of an account that is not the owner (REQ-WFM-066)"""


class SnapshotStore:
    def __init__(self, library, accounts, clock=time.time):
        self.library, self.accounts, self.clock = library, accounts, clock

    def snapshot(self, name, account):
        """STUB (REQ-WFM-061): stores every skill, workflow graph, context graph and transform with version (transforms with trust and lifecycle) and the
        model pins under `name`; a non-owner is refused with Refused"""
        return None

    def read_snapshot(self, name):
        """STUB: {"name", "time", "author", "items": [{"kind", "id", "version", ("trust", "lifecycle" for a transform)}], "pins": {...}}"""
        return None

    def list_snapshots(self, account):
        """STUB (REQ-WFM-062): [{"name", "time", "author"}], oldest first"""
        return None

    def restore_snapshot(self, name, account):
        """STUB (REQ-WFM-063 to 066): first stores the current state as "before restore of <name>" (author: the owner), then gives every item the version,
        trust and lifecycle of the snapshot, deletes no version; a non-owner is refused with Refused and nothing changes"""
        return None
