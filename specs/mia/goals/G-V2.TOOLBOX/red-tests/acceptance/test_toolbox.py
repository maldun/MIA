"""
Acceptance tests of the toolbox (N-2.3, G-V2.TOOLBOX): TC-WFM-050 to 056, 067, 068, 070, 090 to 095 (REQ-WFM-050..056, 067, 068, 070, 090..095) against Toolbox
on the mock of the library part for transforms, a fixed lookup of accounts, a marker folder per test and a stand-in for the event record (TR-TOOLBOX-001..006).
Every refusal is checked together with an accepted twin (TR-TOOLBOX-005). No model, no network.
Run with: python tests/acceptance/test_toolbox.py
"""

import glob
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers", "mocks"))

from markers import mark                                                          # noqa: E402
from if_203_transforms import TransformLibraryMock                                # noqa: E402
from toolbox_fakes import GUEST, OWNER, Accounts, EventRecord, Marker, exchange_file, shipped_copy   # noqa: E402
from toolbox import Toolbox, ToolboxError                                         # noqa: E402


class ToolboxAcceptance(unittest.TestCase):
    def setUp(self):
        self.accounts, self.events, self.marker = Accounts(), EventRecord(), Marker()
        self.addCleanup(self.marker.cleanup)
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, self.accounts.is_owner, self.events)

    def refused(self, code, call):
        """The call raises ToolboxError with this code and a reason for the person."""
        with self.assertRaises(ToolboxError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)
        self.assertTrue(caught.exception.why)
        return caught.exception

    def imported(self, tid, version=1, code=None, author=OWNER, **options):
        return self.box.import_transform(exchange_file(tid, version, code or self.marker.code(), **options), author)

    def trusted(self, tid, version=1, code=None):
        self.imported(tid, version, code)
        self.box.set_trust(tid, "trusted", OWNER)

    # --- the entries ----------------------------------------------------------------------------------------------------------------------------------

    @mark.req("REQ-WFM-050")
    def test_an_equal_or_lower_version_of_an_existing_id_is_refused(self):
        """TC-WFM-050: `t.one` in version 2 exists; version 2 again and version 1 are refused naming the ID and leave the entry unchanged; another ID is accepted."""
        # Given: a toolbox with `t.one` in version 2
        self.imported("t.one", 2)
        before = self.box.export_transform("t.one")
        # When: `t.one` in version 2 and in version 1 is added
        # Then: both are refused naming the ID
        for version in (2, 1):
            self.assertIn("t.one", self.refused("duplicate_id", lambda: self.imported("t.one", version)).why)
        # And: `t.one` is unchanged
        self.assertEqual((self.box.look_up("t.one")["version"], self.box.export_transform("t.one")), (2, before))
        # And: the twin, another ID, is accepted
        self.assertEqual(self.imported("t.two", 1), "t.two")

    @mark.req("REQ-WFM-051", "REQ-WFM-067")
    def test_trust_and_lifecycle_are_two_statuses_with_exact_values(self):
        """TC-WFM-051: trust takes untrusted and trusted, lifecycle draft, tested and retired; `fine` is refused for both; each status changes without the other."""
        # Given: one transform
        self.imported("t.one")
        # When: trust is set to each of its two values and lifecycle to each of its three, and to `fine`
        # Then: every listed value is accepted
        for value in ("trusted", "untrusted"):
            self.box.set_trust("t.one", value, OWNER)
            self.assertEqual(self.box.look_up("t.one")["trust"], value)
        for value in ("draft", "tested", "retired"):
            self.box.set_lifecycle("t.one", value, OWNER, evidence="run-1")
            self.assertEqual(self.box.look_up("t.one")["lifecycle"], value)
        # And: `fine` is refused for both and nothing changes
        self.refused("invalid_trust", lambda: self.box.set_trust("t.one", "fine", OWNER))
        self.refused("invalid_lifecycle", lambda: self.box.set_lifecycle("t.one", "fine", OWNER))
        self.assertEqual({k: self.box.look_up("t.one")[k] for k in ("trust", "lifecycle")}, {"trust": "untrusted", "lifecycle": "retired"})
        # And: each status changes while the other stays
        self.box.set_trust("t.one", "trusted", OWNER)
        self.assertEqual(self.box.look_up("t.one")["lifecycle"], "retired")
        self.box.set_lifecycle("t.one", "draft", OWNER)
        self.assertEqual(self.box.look_up("t.one")["trust"], "trusted")

    # --- importing and exchanging -----------------------------------------------------------------------------------------------------------------------

    @mark.req("REQ-WFM-052")
    def test_an_imported_transform_is_untrusted_whatever_the_file_says(self):
        """TC-WFM-052: an exchange file whose field status says `trusted` is stored untrusted."""
        # Given: an exchange file whose field status says trusted
        text = exchange_file("t.one", status="trusted")
        self.assertEqual(json.loads(text)["status"], "trusted")
        # When: it is imported
        self.box.import_transform(text, OWNER)
        # Then: the transform is stored as untrusted
        self.assertEqual(self.box.look_up("t.one")["trust"], "untrusted")

    @mark.req("REQ-WFM-053")
    def test_importing_runs_no_code_of_the_transform(self):
        """TC-WFM-053: the code text writes a marker file when it is run; after the import there is none; after the owner trusts it and it runs, there is one (twin)."""
        # Given: an exchange file whose code text writes a marker file when it is compiled or run
        # When: it is imported
        self.imported("t.one")
        # Then: the marker file does not exist
        self.assertFalse(self.marker.ran())
        # And: the twin: once trusted and run, the marker exists and the result is the code's
        self.box.set_trust("t.one", "trusted", OWNER)
        self.assertEqual(self.box.run("t.one", {"x": 1}), 2)
        self.assertTrue(self.marker.ran())

    @mark.req("REQ-WFM-054")
    def test_only_the_owner_trusts_but_anyone_may_untrust(self):
        """TC-WFM-054: the second account's trusted is refused with a reason and the status stays; the owner's change shows trusted; the second account may set untrusted."""
        # Given: an imported transform, the owner's account and a second account
        self.imported("t.one")
        # When: the second account sets trusted
        # Then: refused with a reason, the status stays untrusted
        self.refused("owner_only", lambda: self.box.set_trust("t.one", "trusted", GUEST))
        self.assertEqual(self.box.look_up("t.one")["trust"], "untrusted")
        # When: the owner does
        self.box.set_trust("t.one", "trusted", OWNER)
        # Then: it shows trusted
        self.assertEqual(self.box.look_up("t.one")["trust"], "trusted")
        # When: the second account sets untrusted
        self.box.set_trust("t.one", "untrusted", GUEST)
        # Then: it shows untrusted
        self.assertEqual(self.box.look_up("t.one")["trust"], "untrusted")

    @mark.req("REQ-WFM-055")
    def test_export_and_import_give_the_same_transform_and_an_incomplete_file_is_refused(self):
        """TC-WFM-055: export, import into an empty toolbox: same ID, version, schemas and code; a file without `code` is refused naming the field."""
        # Given: an imported transform, an empty toolbox and an exchange file without its code field
        self.imported("t.one", 3)
        exported = self.box.export_transform("t.one")
        other = Toolbox(TransformLibraryMock(), self.accounts.is_owner, EventRecord())
        # When: the transform is exported, the file is imported into the empty toolbox
        other.import_transform(exported, OWNER)
        # Then: ID, version, schemas and code are equal to the first
        self.assertEqual(json.loads(other.export_transform("t.one")), json.loads(exported))
        self.assertTrue({"id", "version", "inputs", "outputs", "code"} <= set(json.loads(exported)))
        # When: the incomplete file is imported
        # Then: it is refused naming the missing field, and nothing is stored
        self.assertIn("code", self.refused("invalid_file", lambda: other.import_transform(exchange_file("t.bad", drop="code"), OWNER)).why)
        self.assertEqual(other.offer(), ["t.one"])

    # --- the shipped nodes ------------------------------------------------------------------------------------------------------------------------------

    @mark.req("REQ-WFM-056")
    def test_the_shipped_nodes_are_seeded_once_trusted_and_marked_shipped(self):
        """TC-WFM-056: three shipped nodes (one ID in versions 1 and 2, one whose version 2 is retired): three entries, trusted, shipped, in the highest version that is not retired."""
        # Given: a fixed copy of three shipped nodes and an empty toolbox
        folder = tempfile.mkdtemp(prefix="toolbox-nodes-")
        self.addCleanup(shutil.rmtree, folder, True)
        expected = shipped_copy(folder)
        # When: the toolbox is seeded
        self.box.seed_shipped(folder)
        # Then: it holds three entries, each trusted and marked shipped, in the expected version
        self.assertEqual(self.library.list_ids("transforms"), sorted(expected))
        for tid, version in expected.items():
            entry = self.box.look_up(tid)
            self.assertEqual((entry["trust"], entry["shipped"], entry["version"]), ("trusted", True, version), tid)

    @mark.req("REQ-WFM-056")
    def test_every_id_of_the_shipped_nodes_of_the_checkout_is_seeded_once(self):
        """TC-WFM-056 (TR-TOOLBOX-004): the folder library/nodes of the checkout: every ID once, trusted, shipped, in its highest version that is not retired."""
        # Given: the real folder of shipped nodes
        folder = os.path.join(REPO, "library", "nodes")
        latest = {}
        for path in glob.glob(os.path.join(folder, "*", "*.json")):
            with open(path, encoding="utf-8") as handle:
                doc = json.load(handle)
            if doc.get("status") != "retired" and doc["version"] > latest.get(doc["id"], 0):
                latest[doc["id"]] = doc["version"]
        self.assertTrue(latest)
        # When: the toolbox is seeded
        self.box.seed_shipped(folder)
        # Then: every ID is there once, trusted and shipped, in the expected version
        self.assertEqual(self.library.list_ids("transforms"), sorted(latest))
        for tid, version in latest.items():
            entry = self.box.look_up(tid)
            self.assertEqual((entry["trust"], entry["shipped"], entry["version"]), ("trusted", True, version), tid)

    @mark.req("REQ-WFM-094")
    def test_a_shipped_transform_is_not_exported_but_an_imported_one_is(self):
        """TC-WFM-094: the export of a shipped transform is refused saying it has no code text; an imported transform exports."""
        # Given: one shipped transform and one imported transform
        folder = tempfile.mkdtemp(prefix="toolbox-nodes-")
        self.addCleanup(shutil.rmtree, folder, True)
        shipped_copy(folder)
        self.box.seed_shipped(folder)
        self.imported("t.one")
        # When: both are exported
        # Then: the shipped one is refused and the answer says it has no code text
        self.assertIn("no code text", self.refused("not_exportable", lambda: self.box.export_transform("check.plain")).why)
        # And: the imported one is exported
        self.assertEqual(json.loads(self.box.export_transform("t.one"))["id"], "t.one")

    # --- lifecycle ---------------------------------------------------------------------------------------------------------------------------------------

    @mark.req("REQ-WFM-067")
    def test_tested_needs_a_named_evidence_and_leaves_the_trust_as_it_is(self):
        """TC-WFM-067: `tested` without evidence is refused; with the evidence `run-17` it is accepted and the trust is still untrusted."""
        # Given: an imported transform
        self.imported("t.one")
        # When: its lifecycle is set to tested without evidence
        # Then: refused, the lifecycle stays draft
        self.refused("evidence_missing", lambda: self.box.set_lifecycle("t.one", "tested", OWNER))
        self.assertEqual(self.box.look_up("t.one")["lifecycle"], "draft")
        # When: then with the evidence run-17
        self.box.set_lifecycle("t.one", "tested", OWNER, evidence="run-17")
        # Then: accepted, the evidence is shown and the trust is still untrusted
        entry = self.box.look_up("t.one")
        self.assertEqual((entry["lifecycle"], entry["evidence"], entry["trust"]), ("tested", "run-17", "untrusted"))

    @mark.req("REQ-WFM-068")
    def test_a_retired_trusted_transform_runs_as_the_baseline_of_a_check(self):
        """TC-WFM-068: a trusted, retired transform runs when a check names it as baseline; in a graph (not as baseline) it is refused (twin)."""
        # Given: a trusted transform that is retired
        self.trusted("t.one")
        self.box.set_lifecycle("t.one", "retired", OWNER)
        # When: a check names it as its baseline
        # Then: the transform runs
        self.assertEqual(self.box.run("t.one", {"x": 1}, as_baseline=True), 2)
        # And: used as a step of a graph it is refused
        self.refused("retired", lambda: self.box.run("t.one", {"x": 1}))

    @mark.req("REQ-WFM-070")
    def test_a_retired_transform_is_not_offered_for_a_new_graph(self):
        """TC-WFM-070: with a live and a retired transform the list for a new graph holds the live one only; before the retirement it held both (twin)."""
        # Given: a live transform and a retired one
        self.imported("t.live")
        self.imported("t.old")
        self.assertEqual(self.box.offer(), ["t.live", "t.old"])
        self.box.set_lifecycle("t.old", "retired", OWNER)
        # When: the list for a new graph is read
        # Then: it holds the live one only
        self.assertEqual(self.box.offer(), ["t.live"])

    # --- the additions of the toolbox goal ---------------------------------------------------------------------------------------------------------------

    @mark.req("REQ-WFM-090")
    def test_the_look_up_of_an_untrusted_transform_shows_the_reason(self):
        """TC-WFM-090: an imported transform shows untrusted and says it came from outside MIA and was not reviewed; a trusted one shows no reason (twin)."""
        # Given: an imported transform
        self.imported("t.one")
        # When: it is looked up
        entry = self.box.look_up("t.one")
        # Then: it shows untrusted and says it came from outside MIA and was not reviewed
        self.assertEqual(entry["trust"], "untrusted")
        self.assertIn("outside MIA", entry["reason"])
        self.assertIn("not reviewed", entry["reason"])
        # And: after the owner trusts it there is no reason
        self.box.set_trust("t.one", "trusted", OWNER)
        self.assertFalse(self.box.look_up("t.one")["reason"])

    @mark.req("REQ-WFM-091")
    def test_an_untrusted_retired_transform_runs_as_baseline_only_with_the_owners_allowance_and_never_in_a_graph(self):
        """TC-WFM-091: with the allowance the check runs it, without it the check is refused, the graph step is refused in both cases."""
        # Given: two retired untrusted transforms, one with the owner's allowance and one without
        self.imported("t.allowed")
        self.imported("t.plain")
        self.box.set_lifecycle("t.allowed", "retired", OWNER, allow_baseline=True)
        self.box.set_lifecycle("t.plain", "retired", OWNER)
        # When: a check names each as its baseline
        # Then: with the allowance the check runs it; without it the check is refused
        self.assertEqual(self.box.run("t.allowed", {"x": 1}, as_baseline=True), 2)
        self.refused("untrusted", lambda: self.box.run("t.plain", {"x": 1}, as_baseline=True))
        # When: a graph names each as a step
        # Then: both are refused
        for tid in ("t.allowed", "t.plain"):
            self.assertIn(self.refusal_code(lambda: self.box.run(tid, {"x": 1})), ("untrusted", "retired"))

    def refusal_code(self, call):
        with self.assertRaises(ToolboxError) as caught:
            call()
        return caught.exception.code

    @mark.req("REQ-WFM-092")
    def test_a_newer_version_replaces_the_code_and_keeps_trust_and_lifecycle(self):
        """TC-WFM-092: a trusted, tested version 1 and a version 2 with other code: the entry is version 2, still trusted and tested, and runs the new code."""
        # Given: a trusted transform in version 1 with the lifecycle tested, and a version 2 with different code
        self.trusted("t.one", 1, self.marker.code("args['x'] + 1"))
        self.box.set_lifecycle("t.one", "tested", OWNER, evidence="run-1")
        self.assertEqual(self.box.run("t.one", {"x": 1}), 2)
        # When: version 2 is imported
        self.imported("t.one", 2, self.marker.code("args['x'] + 10"), author=GUEST)
        # Then: the entry is version 2, still trusted and tested, and a run gives the result of the new code
        entry = self.box.look_up("t.one")
        self.assertEqual((entry["version"], entry["trust"], entry["lifecycle"]), (2, "trusted", "tested"))
        self.assertEqual(self.box.run("t.one", {"x": 1}), 11)

    @mark.req("REQ-WFM-093")
    def test_replacing_a_trusted_transform_leaves_one_event_and_an_untrusted_one_none(self):
        """TC-WFM-093: one event for the trusted transform with its ID, both versions and the author `guest`; none for the untrusted one."""
        # Given: a trusted and an untrusted transform
        self.trusted("t.trusted")
        self.imported("t.untrusted")
        # When: each is replaced by a newer version, by the account guest
        self.imported("t.trusted", 2, author=GUEST)
        self.imported("t.untrusted", 2, author=GUEST)
        # Then: one event exists, for the trusted one, with its ID, both versions and the author; none for the untrusted one
        self.assertEqual(len(self.events.events), 1)
        event = self.events.events[0]
        self.assertEqual((event["id"], event["old_version"], event["new_version"], event["author"]), ("t.trusted", 1, 2, GUEST))

    @mark.req("REQ-WFM-095")
    def test_only_the_owner_allows_a_baseline(self):
        """TC-WFM-095: the second account's allowance is refused and stays unset; the owner's is set."""
        # Given: a retired untrusted transform, the owner's account and a second account
        self.imported("t.one")
        self.box.set_lifecycle("t.one", "retired", OWNER)
        # When: the second account sets the allowance
        # Then: refused, the allowance stays unset
        self.refused("owner_only", lambda: self.box.set_lifecycle("t.one", "retired", GUEST, allow_baseline=True))
        self.assertFalse(self.box.look_up("t.one")["baseline_allowed"])
        # When: the owner does
        self.box.set_lifecycle("t.one", "retired", OWNER, allow_baseline=True)
        # Then: the allowance is set
        self.assertTrue(self.box.look_up("t.one")["baseline_allowed"])


if __name__ == "__main__":
    unittest.main()
