"""IF-203 v1, the part `transforms` of the workflow library (G-V2.TOOLBOX, proposal A-111): the contract suite runs against the mock (stage 1) and the real Workflow
management (stage 2, skipped until the part is built in task T-06 of G-V2.TOOLBOX). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_203_v1_transforms.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402
from errors import ServiceError                             # noqa: E402
from if_203_transforms import TransformLibraryMock          # noqa: E402

IF = "IF-203"
ONE = {"id": "t.one", "version": 1, "inputs": {"type": "object"}, "outputs": {"type": "number"}, "code": "def run(args):\n    return args['x']\n"}


def make(kind):
    return TransformLibraryMock() if kind == "mock" else subject_for(IF, kind)      # the real library of IF-203 v0 refuses the kind transforms until T-06 builds it: red


def error_of(call):
    try:
        call()
    except ServiceError as err:
        return err
    raise AssertionError("no ServiceError raised")


@contract
class TransformsContract(unittest.TestCase):
    @mark.req("IF-203", "REQ-WFM-050", "REQ-WFM-051")
    @each_provider(IF, make)
    def test_a_new_transform_is_untrusted_and_draft_and_versions_count_up(self, lib):
        """TC-IF-203-05 (v1) golden 1: save gives version 1, a second save version 2; the new transform is untrusted and draft; read gives both statuses; history names the authors."""
        self.assertEqual(lib.save("transforms", "t.one", ONE, "anna"), {"version": 1})
        self.assertEqual((lib.get_trust("t.one"), lib.get_lifecycle("t.one")), ("untrusted", "draft"))
        self.assertEqual(lib.save("transforms", "t.one", dict(ONE, version=2), "ben"), {"version": 2})
        entry = lib.read("transforms", "t.one")
        self.assertEqual((entry["version"], entry["doc"]["version"], entry["trust"], entry["lifecycle"]), (2, 2, "untrusted", "draft"))
        self.assertEqual(lib.read("transforms", "t.one", 1)["doc"], ONE)
        self.assertEqual([h["author"] for h in lib.history("transforms", "t.one")], ["anna", "ben"])
        lib.save("transforms", "t.a", dict(ONE, id="t.a"), "anna")
        self.assertEqual(lib.list_ids("transforms"), ["t.a", "t.one"])

    @mark.req("IF-203", "REQ-WFM-054", "REQ-WFM-067", "REQ-WFM-092")
    @each_provider(IF, make)
    def test_trust_and_lifecycle_survive_a_new_version(self, lib):
        """TC-IF-203-06 (v1) golden 2: trust trusted and lifecycle tested with the evidence run-1 stay when version 2 is saved; version 1 still reads its own document."""
        lib.save("transforms", "t.one", ONE, "anna")
        self.assertEqual(lib.set_trust("t.one", "trusted", "anna"), {"trust": "trusted"})
        self.assertEqual(lib.set_lifecycle("t.one", "tested", "anna", evidence="run-1"), {"lifecycle": "tested"})
        lib.save("transforms", "t.one", dict(ONE, version=2, code="def run(args):\n    return 0\n"), "ben")
        meta = lib.get_meta("t.one")
        self.assertEqual((meta["trust"], meta["lifecycle"], meta["evidence"]), ("trusted", "tested", "run-1"))
        self.assertEqual(lib.read("transforms", "t.one", 1)["doc"], ONE)

    @mark.req("IF-203", "REQ-WFM-051", "REQ-WFM-067")
    @each_provider(IF, make)
    def test_only_the_listed_values_are_accepted_and_nothing_changes_on_a_refusal(self, lib):
        """TC-IF-203-07 (v1): trust takes untrusted and trusted, lifecycle draft, tested and retired; any other value is invalid/schema with the field as detail and the statuses stay."""
        lib.save("transforms", "t.one", ONE, "anna")
        for value in ("trusted", "untrusted"):
            self.assertEqual(lib.set_trust("t.one", value, "anna"), {"trust": value})
        for value in ("draft", "tested", "retired"):
            self.assertEqual(lib.set_lifecycle("t.one", value, "anna"), {"lifecycle": value})
        for call, field in ((lambda: lib.set_trust("t.one", "fine", "anna"), "trust"), (lambda: lib.set_lifecycle("t.one", "fine", "anna"), "lifecycle")):
            err = error_of(call)
            self.assertEqual((err.code, err.rule, err.detail), ("invalid", "schema", field))
        self.assertEqual((lib.get_trust("t.one"), lib.get_lifecycle("t.one")), ("untrusted", "retired"))

    @mark.req("IF-203", "REQ-WFM-056", "REQ-WFM-090", "REQ-WFM-091")
    @each_provider(IF, make)
    def test_the_optional_meta_fields_are_kept_and_checked(self, lib):
        """TC-IF-203-08 (v1): reason, evidence, baseline_allowed (boolean), shipped (boolean) and changed_by are kept in the meta record; a boolean field with another type is invalid/schema."""
        lib.save("transforms", "t.one", ONE, "anna")
        lib.set_meta("t.one", "anna", reason="came from outside MIA and was not reviewed", baseline_allowed=True, shipped=False)
        meta = lib.get_meta("t.one")
        self.assertEqual((meta["reason"], meta["baseline_allowed"], meta["shipped"], meta["changed_by"]), ("came from outside MIA and was not reviewed", True, False, "anna"))
        err = error_of(lambda: lib.set_meta("t.one", "anna", baseline_allowed="yes"))
        self.assertEqual((err.code, err.rule, err.detail), ("invalid", "schema", "baseline_allowed"))
        self.assertTrue(lib.get_meta("t.one")["baseline_allowed"])

    @mark.req("IF-203", "REQ-WFM-050")
    @each_provider(IF, make)
    def test_unknown_ids_kinds_and_stale_versions(self, lib):
        """TC-IF-203-09 (v1): an unknown id, version or kind is not_found; a stale expected_version is conflict with detail.current; nothing changes."""
        lib.save("transforms", "t.one", ONE, "anna")
        for call in (lambda: lib.read("transforms", "t.none"), lambda: lib.read("transforms", "t.one", 7), lambda: lib.list_ids("skills_x"), lambda: lib.set_trust("t.none", "trusted", "anna"),
                     lambda: lib.get_meta("t.none")):
            self.assertEqual(error_of(call).code, "not_found")
        err = error_of(lambda: lib.save("transforms", "t.one", dict(ONE, version=2), "anna", expected_version=0))
        self.assertEqual((err.code, err.detail), ("conflict", {"current": 1}))
        self.assertEqual(lib.history("transforms", "t.one")[-1]["version"], 1)


if __name__ == "__main__":
    unittest.main()
