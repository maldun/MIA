#!/usr/bin/env bash
# Amendment A-93 (G-V2.STORE, Verify finding F-01, decided 2026-11-07): a node with an extra field in its JSON field, or with a key `id` inside `data`,
# is refused as schema_break naming that field, on write and on read.
#   REQ-GTB-022 (new, Draft until the owner has reviewed it), TC-GTB-023 (Storage side), TC-IF-301-21 (contract suite), IF-301 v2: the fixed types
#   forbid additional fields (v2 is not merged yet, so it stays v2), task T-07.
# Note: specs/mia/amendments/A-93-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing, F-04):
#   N-3.2 requirements.md, test-spec.md, test-requirements.md (TR-GTB-001 applies to TC-GTB-023)   goal.md of G-V2.STORE (scope row)   plan.md (T-07)
#   contracts/IF-301-graph-tables.md                                  the fixed-types text, golden 16, decision 13, clarification, version history
#   tests/helpers/mocks/if_301_graph_tables_v2.py                     TYPE_SCHEMAS get additionalProperties: false; _broken_path names the extra field
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py          case TC-IF-301-21
#   tests/acceptance/test_graph_node_fields.py                        new, TC-GTB-023 (staged in specs/mia/amendments/A-93/)
# After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# Independent of A-94 (the removal of the A-92 duplicates): the anchors work with and without the duplicates, in either order.
# THE OWNER REVIEWS REQ-GTB-022 FIRST (python ~/.claude/skills/plan-phase/scripts/req_review.py ..., rating in plausibility.yaml), then installs.
#   bash tools/apply_amendment_a93.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a93.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-93 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
GOAL=specs/mia/goals/G-V2.STORE/goal.md
PLAN=specs/mia/goals/G-V2.STORE/plan.md
CONTRACT=contracts/IF-301-graph-tables.md
MOCK=tests/helpers/mocks/if_301_graph_tables_v2.py
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$NODE" "$GOAL" "$PLAN" "$CONTRACT" "$MOCK" "$SUITE" "$WORK" <<'PY'
import os
import re
import sys
node, goal, plan, contract, mock, suite, work = sys.argv[1:8]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once. The edit counts as done when `new` is in the text already (checked FIRST: `new`
    often still contains `old`, so testing the anchor alone would apply the edit a second time); anything else is refused."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    sys.exit("%s: anchor not found exactly once (%s); install A-93 by hand" % (where, old[:70]))


def after_line(text, pattern, addition, where, last=False):
    """Insert `addition` (full lines) after the line that matches `pattern`; done when `addition` is in the text; `last` takes the last match."""
    if addition in text:
        return text
    found = list(re.finditer(pattern, text, re.M))
    if (len(found) != 1 and not last) or not found:
        sys.exit("%s: the line %r is not found exactly once; install A-93 by hand" % (where, pattern[:60]))
    end = found[-1].end()
    return text[:end] + addition + text[end:]


# --- requirements.md: REQ-GTB-022 after REQ-GTB-021, and in the group TY
path = os.path.join(node, "requirements.md")
text = read(path)
if "### REQ-GTB-022 " not in text:
    if text.count("### REQ-GTB-021 ") != 1 or not text.rstrip().endswith("(A-92, proposed)"):
        sys.exit("%s: REQ-GTB-021 is not the last block; install A-93 by hand" % path)
    text = text.rstrip("\n") + """

### REQ-GTB-022 – Fixed fields of a node
- Level: low   Subject: Persistence
- Text: If a node is written or read with a field in its JSON field that its type's schema does not list, then the Graph tables shall refuse the node as `schema_break` naming that field.
- Rationale: refines FR-40, REQ-GTB-009, REQ-GTB-011 and REQ-GTB-014; the list of types is fixed, a node that passes the write check but cannot be rebuilt breaks the round trip, and dropping the field would lose data; found in G-V2.STORE Verify (F-01, decided 2026-11-07, A-93)
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a data node with a field `foo` and a data node with a key `id` inside its JSON field are refused as `schema_break` naming `foo` and `id`, when written and when read; the same nodes without the field are accepted (exact)
- Verified by: TC-GTB-023
- Status: Draft
- History: G-V2.STORE Verify F-01, 2026-11-07, new (A-93, proposed)
"""
text = once(text, "| REQ-GTB-009, REQ-GTB-010, REQ-GTB-011, REQ-GTB-012 |", "| REQ-GTB-009, REQ-GTB-010, REQ-GTB-011, REQ-GTB-012, REQ-GTB-022 |", path)
out("requirements.md", text)

# --- test-spec.md: the row after TC-GTB-022, the scenario before TC-GTB-015
path = os.path.join(node, "test-spec.md")
text = read(path)
row = ("| TC-GTB-023 | REQ-GTB-022 | Unit | 1 | a node of each type with an extra field `foo`, and a data node with a key `id` in its JSON field, each written and, "
       "put past the check, read; the same nodes without the field | the first group is refused on write and on read naming the field; the twins are accepted | exact |\n")
text = after_line(text, r"^\| TC-GTB-022 \|[^\n]*\n", row, path)
scenario = """### TC-GTB-023 – A node with an extra field is refused
- Verifies: REQ-GTB-022
- Given: one node of each type with an extra field `foo`, and a data node with a key `id` inside its JSON field
- When: each is written, and each is read as a record already in storage
- Then: each write is refused and each read is refused, both as `schema_break` naming the extra field (`foo`, `id`)
- And: the refused writes store nothing; the same nodes without the extra field are accepted, and a context-graph node keeps the fields its category allows (the twins differ only in the broken rule)

"""
text = once(text, "### TC-GTB-015 – The document form still works\n", scenario + "### TC-GTB-015 – The document form still works\n", path)
out("test-spec.md", text)

# --- test-requirements.md: TR-GTB-001 applies to TC-GTB-023
path = os.path.join(node, "test-requirements.md")
text = read(path)
m = re.search(r"^### TR-GTB-001 [^\n]*\n(?:(?!^### ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TR-GTB-001 is not found; install A-93 by hand" % path)
block = m.group(0)
if "TC-GTB-023" not in block:
    new = re.sub(r"^(- Applies to: [^\n]*TC-GTB-022)\n", r"\1, TC-GTB-023\n", block, count=1, flags=re.M)
    if new == block:
        sys.exit("%s: the Applies-to line of TR-GTB-001 does not end with TC-GTB-022; install A-93 by hand" % path)
    text = text.replace(block, new, 1)
out("test-requirements.md", text)

# --- goal.md: the scope row (after the last row of REQ-GTB-021: A-92 may have written it twice, A-94 removes that)
text = read(goal)
text = after_line(text, r"^\| REQ-GTB-021 \| in \| A-92 \|\n", "| REQ-GTB-022 | in | A-93 |\n", goal, last=True)
out("goal.md", text)

# --- plan.md: table row, task T-07, size check, order, the owner's decision
text = read(plan)
text = once(text, "Six small tasks (T-06 added with A-92)", "Seven small tasks (T-06 added with A-92, T-07 with A-93)", plan)
text = after_line(text, r"^\| T-06 Record under its own ID[^\n]*\n",
                  "| T-07 Fixed fields of a node | REQ-GTB-022 | TC-GTB-023; real side of TC-IF-301-21; new unit tests of `check_record` and `to_object` | T-06; amendment A-93 (installed) |\n", plan)
task = """### T-07: Fixed fields of a node
- Implements: REQ-GTB-022 (A-93, F-01 of the verification report)
- Tests to turn green: TC-GTB-023 (`tests/acceptance/test_graph_node_fields.py`); the real side of TC-IF-301-21 (`test_a_node_with_an_extra_field_is_refused_naming_it_real`); new unit tests in `tests/test_graph_record_checks.py` that fail first: `check_record` and `to_object` of `{"type": "data", "foo": 1}` and of `{"type": "data", "id": "x"}`, and `Storage.put` of the first (refused as `invalid`, `schema_break`, `foo`, nothing stored)
- Touches: `graph_tables.py` (the three schemas of `TYPE_SCHEMAS` get `"additionalProperties": False`; `_broken_path` names an additional field by its own key, the first in sorted order when several, and orders the errors by these paths as text, so a missing key at the same level is named first); `tests/test_graph_record_checks.py`
- Must not touch: protected material, `contracts/` (A-93 changed IF-301 already), `storage.py` (it calls `check_record` already), `graph_rules.py`, the schemas of `graphs`, `skills` and `graph_edges`, the schemas of context-graph nodes (they come from the caller's categories)
- Depends on: T-06; A-93 installed
- Done when: the listed tests are green, all other tests unchanged (the three contract suites, `test_graph_records.py`, `test_graph_record_identity.py`, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, TC-GTB-014 with N = 1000)
- Notes: `to_object` needs no change of its own: it calls `check_record` first, so a node with an extra field is refused before `CLASSES[type_id](id, **data)` is reached. The schemas that `types()` returns carry the setting (TC-IF-301-21 checks it). `_STOP`, the member lists and the edge schema are not changed. No new part, interface or dependency.

"""
text = once(text, "## Order and checks\n", task + "## Order and checks\n", plan)
text = once(text, "T-06 after T-04.", "T-06 after T-04; T-07 after T-06 and the install of A-93.", plan)
text = once(text, "17 requirements and one interface, six tasks of one session each, two nodes (N-3.2 in T-01 to T-03, T-05 and T-06, N-3.1 in T-04 and T-06)",
            "18 requirements and one interface, seven tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-07, N-3.1 in T-04 and T-06)", plan)
text = after_line(text, r"^5\. A-92 [^\n]*\n",
                  "6. A-93 (fixed fields of a node, REQ-GTB-022, TC-GTB-023, TC-IF-301-21, IF-301 v2) follows the decision of F-01 on 2026-11-07, which the owner delegated to the reviewer "
                  "and may overrule; T-07 is added to this plan on that decision, the owner installs the amendment after a look-only review.\n", plan)
out("plan.md", text)

# --- contract
text = read(contract)
text = after_line(text, r"^The graph description \(ID, context graph ID, testbench ID, description\) is not a node field[^\n]*\n", """
The list is closed for the fields of a type too (A-93, REQ-GTB-022): the schema of each type sets `additionalProperties: false`, so the JSON field of a node holds `type`, the fields of the table above and nothing else. A node with another field, or with a key `id` inside `data`, is `{"rule": "schema_break", "detail": "<that field>"}` in `check_record` and in `to_object` (a stored node is refused on read; `to_object` never raises). This holds for workflow nodes only: the schema of a context-graph node comes from its categories (decision 5). The schemas that `types()` returns carry the setting.
""", contract)
text = after_line(text, r"^15\. Record identity \(v2\)[^\n]*\n",
                  '16. Extra field (v2): a node record `{"id": "d1", "data": {"type": "data", "foo": 1}}` gives `{"rule": "schema_break", "detail": "foo"}` in `check_record`, and `to_object` of it gives `{"refused": {"rule": "schema_break", "detail": "foo"}}`; a key `id` inside `data` is named `id`; the same node without the extra field gives `None`.\n', contract)
text = after_line(text, r"^12\. \*\*A-92 [^\n]*\n",
                  "13. **A-93 (Verify finding F-01, 2026-11-07; the owner delegated the choice to the reviewer and may overrule):** the fixed list is closed for the fields of a type too: a node with a field its type does not list is refused as `schema_break` naming the field, on write and on read. Before, such a node was stored and then `to_object` raised (the mock silently dropped the field). Why: the list of types is fixed (decision 4), REQ-GTB-014 needs the round trip exact, and a silent drop would lose data. Context-graph nodes are not affected (decision 5). Several breaks in one record: the detail is the first path in text order, a missing key counting at the path of its object and an extra field at its own path, so a missing `toolbox_id` is named before an extra `foo`. v2 is not merged yet, so this is part of v2.\n", contract)
text = after_line(text, r"^- The detail of `schema_break` is the path of the field with dots[^\n]*\n",
                  "- An additional field of a node's JSON field is named by its own key (`foo`; `id` for a key `id` inside `data`); when several are extra, the first in sorted order is named (decision 13).\n", contract)
text = once(text, "golden 5 to 15, `record_id` of `check_record` | A-90 (D-188, D-262 to D-266), A-92 |",
            "golden 5 to 16, `record_id` of `check_record`, the fixed types forbid additional fields | A-90 (D-188, D-262 to D-266), A-92, A-93 |", contract)
out("contract.md", text)

# --- mock
text = read(mock)
text = after_line(text, r'^- the type of a context-graph node is in `data\["type"\]`, as for a workflow node\.\n',
                  "- a field of a node's JSON field that the schema of its type does not list is schema_break naming that field, in check_record and in to_object (A-93); the\n"
                  "  detail is the first path in text order, a missing key counting at the path of its object, an extra field at its own path.\n", mock)
text = once(text, '"parameters": {"type": "object"}}, "required": ["type"]},', '"parameters": {"type": "object"}}, "required": ["type"],\n             "additionalProperties": False},', mock)
text = once(text, '"required": ["type", "toolbox_id", "stop"]},', '"required": ["type", "toolbox_id", "stop"], "additionalProperties": False},', mock)
text = once(text, '"required": ["type", "toolbox_id"]},', '"required": ["type", "toolbox_id"], "additionalProperties": False},', mock)
old_function = '''def _broken_path(schema, data):
    """The path of the first field that breaks the schema, or None. The path is the validator's error path (TR-GTB-003); for a missing
    required key it is that key, appended to the path of the object that lacks it."""
    errors = sorted(_validator(schema).iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    if not errors:
        return None
    error = errors[0]
    path = list(error.absolute_path)
    if error.validator == "required":
        path.append([k for k in error.validator_value if k not in error.instance][0])
    return ".".join(str(p) for p in path) or "data"
'''
new_function = '''def _extra(error):
    """The first additional field of an additionalProperties error, in sorted order (REQ-GTB-022)."""
    return min(k for k in error.instance if k not in error.schema.get("properties", {}))


def _broken_path(schema, data):
    """The path of the first field that breaks the schema, or None. The path is the validator's error path (TR-GTB-003); for a missing
    required key it is that key, appended to the path of the object that lacks it; for an additional field it is that field (A-93). The
    first is the first in the order of these paths as text, a missing key counting at the path of its object."""
    def order(error):
        return [str(p) for p in error.absolute_path] + ([_extra(error)] if error.validator == "additionalProperties" else [])

    errors = sorted(_validator(schema).iter_errors(data), key=order)
    if not errors:
        return None
    error = errors[0]
    path = list(error.absolute_path)
    if error.validator == "required":
        path.append([k for k in error.validator_value if k not in error.instance][0])
    elif error.validator == "additionalProperties":
        path.append(_extra(error))
    return ".".join(str(p) for p in path) or "data"
'''
text = once(text, old_function, new_function, mock)
out("mock.py", text)

# --- suite: the case TC-IF-301-21 before the case of TC-IF-301-08 (an anchor that exists once, with or without the A-92 duplicates)
text = read(suite)
case = '''    @mark.req("IF-301", "REQ-GTB-022")
    @each_provider(IF, make=subject)
    def test_a_node_with_an_extra_field_is_refused_naming_it(self, tables):
        """TC-IF-301-21 golden 16: a node with a field its type does not list gives schema_break naming that field, in check_record and in to_object.

        Example: {"id": "d1", "data": {"type": "data", "foo": 1}} -> {"rule": "schema_break", "detail": "foo"}; a key id inside data -> detail "id".
        """
        # Given: one node per type with an extra field foo, and a data node with a key id inside its JSON field
        stop = {"max_repetitions": 1}
        cases = [(node("d1", "data", foo=1), "foo"),
                 (node("t1", "transform", toolbox_id="t", foo=1), "foo"),
                 (node("m1", "master", toolbox_id="t", stop=stop, foo=1), "foo"),
                 (node("d2", "data", id="x"), "id")]
        for record, field in cases:
            with self.subTest(record=record):
                # When/Then: the check and the rebuild both refuse it as schema_break naming the field, and the rebuild does not raise
                refusal = {"rule": "schema_break", "detail": field}
                self.assertEqual(tables.check_record("graph_nodes", record), refusal)
                self.assertEqual(tables.to_object(record), {"refused": refusal})
        # And: the twins without the extra field are accepted
        for record in (node("d1", "data"), node("t1", "transform", toolbox_id="t"), node("m1", "master", toolbox_id="t", stop=stop)):
            self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: a missing required key is named before an extra field (decision 13)
        self.assertEqual(tables.check_record("graph_nodes", node("t1", "transform", foo=1)), {"rule": "schema_break", "detail": "toolbox_id"})
        # And: the schemas of the fixed list say so, and the node of a context graph keeps the fields of its own category
        for type_id, schema in tables.types().items():
            self.assertIs(schema.get("additionalProperties"), False, type_id)
        self.assertIsNone(tables.check_record("graph_nodes", node("c1", "entity", foo=1), categories={"entity": {"type": "object"}}))

'''
anchor = '''    @mark.req("IF-301", "REQ-GTB-010")
    @each_provider(IF, make=subject)
    def test_an_unknown_type_is_refused_naming_it(self, tables):
'''
text = once(text, anchor, case + anchor, suite)
out("suite.py", text)
PY
copy "$WORK/requirements.md"      "$NODE/requirements.md"
copy "$WORK/test-spec.md"         "$NODE/test-spec.md"
copy "$WORK/test-requirements.md" "$NODE/test-requirements.md"
copy "$WORK/goal.md"              "$GOAL"
copy "$WORK/plan.md"              "$PLAN"
copy "$WORK/contract.md"          "$CONTRACT"
copy "$WORK/mock.py"              "$MOCK"
copy "$WORK/suite.py"             "$SUITE"
copy specs/mia/amendments/A-93/test_graph_node_fields.py tests/acceptance/test_graph_node_fields.py
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check, errors about REQ-GTB-022 and TC-GTB-023 (the owner's review of REQ-GTB-022 is open: none about structure expected)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "GTB-022|GTB-023|IF-301-21" || echo none
    echo "== the new checks (the _mock side and the old checks must pass; the real side and TC-GTB-023 are red until T-07)"
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k extra_field 2>&1 | tail -1 || true
    python tests/acceptance/test_graph_node_fields.py 2>&1 | tail -1 || true
    python tests/acceptance/test_graph_records.py 2>&1 | tail -1
fi
