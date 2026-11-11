"""Fakes and builders for the acceptance tests of G-V2.TOOLBOX (N-2.3 toolbox and trust, TC-WFM-050..056, 067, 068, 070, 090..095).

Test requirements (specs/mia/test-requirements.md):
- TR-TOOLBOX-002: Marker gives a new, empty folder per test and a code text that writes a marker file the moment it is run (compiled code that runs at import writes it too).
- TR-TOOLBOX-003: Accounts is a fixed lookup with the owner and a second account of the same rights otherwise.
- TR-TOOLBOX-004: shipped_copy builds a fixed copy of three shipped nodes (one ID with versions 1 and 2, one ID whose version 2 is retired).
- TR-TOOLBOX-006: EventRecord keeps every event with all its fields in the order recorded (stand-in for IF-401).
Every exchange file and every shipped node of a test is built here, so a change of a field name is a change in this one file.
"""
import json
import os
import shutil
import tempfile

OWNER, GUEST = "anna", "guest"


class Accounts:
    """The owner and a second account; `is_owner` is the lookup the toolbox gets (the accounts of IF-101 are not part of this goal)."""
    def __init__(self):
        self.names = (OWNER, GUEST)

    def is_owner(self, account):
        return account == OWNER


class EventRecord:
    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


class Marker:
    """A fresh folder per test; `code(result)` is a code text that writes a line into the folder when it is run and defines run(args) with the given result expression."""
    def __init__(self):
        self.folder = tempfile.mkdtemp(prefix="toolbox-marker-")
        self.path = os.path.join(self.folder, "ran.txt")

    def code(self, result="args['x'] + 1"):
        return "open(%r, 'a').write('ran\\n')\n\n\ndef run(args):\n    return %s\n" % (self.path, result)

    def ran(self):
        return os.path.exists(self.path)

    def cleanup(self):
        shutil.rmtree(self.folder, True)


def exchange_file(tid, version=1, code="def run(args):\n    return args['x']\n", status="untrusted", drop=None):
    """The exchange form (REQ-WFM-055): one JSON text with ID, version, input and output schemas and the code text; `drop` removes a field."""
    doc = {"id": tid, "version": version, "inputs": {"type": "object"}, "outputs": {"type": "number"}, "code": code, "status": status}
    if drop:
        del doc[drop]
    return json.dumps(doc, sort_keys=True)


def shipped_copy(folder):
    """A fixed copy of three shipped nodes in the layout of library/nodes: <id>/<version>.json. `double` has versions 1 and 2, `gone` has a version 2 that is retired, `plain` has version 1."""
    nodes = (("check.plain", 1, "trusted"), ("check.double", 1, "trusted"), ("check.double", 2, "trusted"), ("check.gone", 1, "trusted"), ("check.gone", 2, "retired"))
    for tid, version, status in nodes:
        os.makedirs(os.path.join(folder, tid), exist_ok=True)
        with open(os.path.join(folder, tid, "%d.json" % version), "w", encoding="utf-8") as handle:
            json.dump({"id": tid, "version": version, "kind": "code", "status": status, "inputs": {"type": "object"}, "outputs": {"type": "object"}}, handle)
    return {"check.plain": 1, "check.double": 2, "check.gone": 1}      # the version each ID must be seeded in
