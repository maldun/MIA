#!/usr/bin/env bash
# Amendment A-92 (G-V2.STORE, found in T-04 on 2026-11-07): a graph record written under a record ID that differs from the ID inside it is refused.
#   REQ-GTB-021 (new, Draft until the owner has reviewed it), TC-GTB-022, IF-301 v2: the argument `record_id` of check_record (v2 is not merged yet, so it stays v2).
# Note: specs/mia/amendments/A-92-note.md
# Files that change (made from the INSTALLED files at run time, each edit refused when its anchor is not found exactly once; done edits are skipped):
#   N-3.2 requirements.md, test-spec.md, test-requirements.md (TR-GTB-001 applies to TC-GTB-022)   goal.md of G-V2.STORE (scope row)
#   contracts/IF-301-graph-tables.md                                  the argument, the rule, golden 15, decision 12, version history
#   tests/helpers/mocks/if_301_graph_tables_v2.py                     the mock follows the contract
#   tests/helpers/graph_store_standin.py                              put passes the record ID to check_record
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py          case TC-IF-301-20
#   tests/acceptance/test_graph_record_identity.py                    new, TC-GTB-022 (staged in specs/mia/amendments/A-92/)
# After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# THE OWNER REVIEWS REQ-GTB-021 FIRST (python ~/.claude/skills/plan-phase/scripts/req_review.py ..., rating in plausibility.yaml), then installs.
#   bash tools/apply_amendment_a92.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a92.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-92 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
GOAL=specs/mia/goals/G-V2.STORE/goal.md
CONTRACT=contracts/IF-301-graph-tables.md
MOCK=tests/helpers/mocks/if_301_graph_tables_v2.py
STANDIN=tests/helpers/graph_store_standin.py
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$NODE" "$GOAL" "$CONTRACT" "$MOCK" "$STANDIN" "$SUITE" "$WORK" <<'PY'
import os
import re
import sys
node, goal, contract, mock, standin, suite, work = sys.argv[1:8]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where, done=None):
    """Replace `old` by `new` when `old` occurs exactly once; skip when the edit is done already; refuse otherwise."""
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    if text.count(done or new) >= 1:
        return text
    sys.exit("%s: anchor not found exactly once (%s); install A-92 by hand" % (where, old[:70]))


# --- requirements.md: REQ-GTB-021 after REQ-GTB-020
path = os.path.join(node, "requirements.md")
text = read(path)
if "### REQ-GTB-021 " not in text:
    if text.count("### REQ-GTB-020 ") != 1 or not text.rstrip().endswith("(D-266)"):
        sys.exit("%s: REQ-GTB-020 is not the last block; install A-92 by hand" % path)
    text = text.rstrip("\n") + """

### REQ-GTB-021 – Record under its own ID
- Level: low   Subject: Persistence
- Text: If a record of a graph table is written under a record ID that differs from the ID inside the record, then the Graph tables shall refuse the record and name the field `id`.
- Rationale: refines FR-40 and REQ-GTB-005; a graph header pins its members by the ID inside the record while the storage finds them by the record ID, so a record under another ID cannot be found again (REQ-GTB-014); found in G-V2.STORE Implement T-04 (A-92)
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node whose own ID is n1, written under the record ID x, is refused naming `id` and nothing is stored under x; written under n1 it is accepted (exact)
- Verified by: TC-GTB-022
- Status: Draft
- History: G-V2.STORE Implement T-04, 2026-11-07, new (A-92, proposed)
"""
out("requirements.md", text)

# --- test-spec.md: the row after TC-GTB-021 and the scenario after its scenario
path = os.path.join(node, "test-spec.md")
text = read(path)
row = "| TC-GTB-022 | REQ-GTB-021 | Unit | 1 | a node with its own ID n1, written under the record ID n1 and under the record ID x | the first is accepted; the second is refused naming `id`; nothing is stored under x | exact |\n"
m = re.search(r"^\| TC-GTB-021 \|[^\n]*\n", text, re.M)
if not m:
    sys.exit("%s: the row of TC-GTB-021 is not found; install A-92 by hand" % path)
if "| TC-GTB-022 |" not in text:
    text = text.replace(m.group(0), m.group(0) + row, 1)
scenario = """### TC-GTB-022 – A record under another ID is refused
- Verifies: REQ-GTB-021
- Given: a node whose own ID is `n1`
- When: it is written under the record ID `x`, and then under the record ID `n1`
- Then: the write under `x` is refused and names `id`
- And: nothing is stored under `x`; the write under `n1` is accepted (the twin differs only in the broken rule)

"""
text = once(text, "### TC-GTB-015 – The document form still works\n", scenario + "### TC-GTB-015 – The document form still works\n", path,
            done="### TC-GTB-022 – ")
out("test-spec.md", text)

# --- test-requirements.md: TR-GTB-001 applies to TC-GTB-022
path = os.path.join(node, "test-requirements.md")
text = read(path)
m = re.search(r"^### TR-GTB-001 [^\n]*\n(?:(?!^### ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TR-GTB-001 is not found; install A-92 by hand" % path)
block = m.group(0)
if "TC-GTB-022" not in block:
    new = re.sub(r"^(- Applies to: [^\n]*TC-GTB-021)\n", r"\1, TC-GTB-022\n", block, count=1, flags=re.M)
    if new == block:
        sys.exit("%s: the Applies-to line of TR-GTB-001 does not end with TC-GTB-021; install A-92 by hand" % path)
    text = text.replace(block, new, 1)
out("test-requirements.md", text)

# --- goal.md: the scope row
text = read(goal)
text = once(text, "| REQ-GTB-020 | in | |\n", "| REQ-GTB-020 | in | |\n| REQ-GTB-021 | in | A-92 |\n", goal)
out("goal.md", text)

# --- contract
text = read(contract)
text = once(text, "`check_record(table, record, categories=None, stored=None)`", "`check_record(table, record, categories=None, stored=None, record_id=None)`", contract)
text = once(text, "what the caller has stored |", "what the caller has stored; `record_id` = the record ID the caller writes the record under (optional) |", contract)
text = once(text, "`record_identity` (detail: the field)", "`record_identity` (detail: the field; `id` also when `record_id` is given and differs from the `id` inside the record, REQ-GTB-021)", contract)
m = re.search(r"^14\. Document form \(v2\)[^\n]*\n", text, re.M)
if not m:
    sys.exit("%s: golden 14 is not found; install A-92 by hand" % contract)
if "\n15. Record identity (v2)" not in text:
    text = text.replace(m.group(0), m.group(0) + '15. Record identity (v2): a node record whose `id` is `n1`, checked with `record_id="x"`, gives `{"rule": "record_identity", "detail": "id"}`; with `record_id="n1"` or without `record_id` it gives `None`.\n', 1)
m = re.search(r"^11\. \*\*Plan step 4[^\n]*\n", text, re.M)
if not m:
    sys.exit("%s: decision 11 is not found; install A-92 by hand" % contract)
if "\n12. **A-92" not in text:
    text = text.replace(m.group(0), m.group(0) + "12. **A-92 (found in Implement T-04, 2026-11-07):** a record written under a record ID that differs from the `id` inside it is refused; the rule stays in the Graph tables (REQ-GTB-021), so `check_record` takes the optional `record_id` and the Storage layer passes the ID it writes under. v2 is not merged yet, so the argument is part of v2.\n", 1)
text = once(text, "golden 5 to 14 | A-90 (D-188, D-262 to D-266) |", "golden 5 to 15, `record_id` of `check_record` | A-90 (D-188, D-262 to D-266), A-92 |", contract)
out("contract.md", text)

# --- mock
text = read(mock)
text = once(text, "def _check(table, record, categories, stored):", "def _check(table, record, categories, stored, record_id=None):", mock)
text = once(text, '''    if not isinstance(record.get("id"), str) or not record["id"]:
        return {"rule": "record_identity", "detail": "id"}
''', '''    if not isinstance(record.get("id"), str) or not record["id"]:
        return {"rule": "record_identity", "detail": "id"}
    if record_id is not None and record_id != record["id"]:      # the record is stored under the ID it carries (REQ-GTB-021)
        return {"rule": "record_identity", "detail": "id"}
''', mock)
text = once(text, "    def check_record(self, table, record, categories=None, stored=None):", "    def check_record(self, table, record, categories=None, stored=None, record_id=None):", mock)
text = once(text, "            return _check(table, record, categories, stored)\n", "            return _check(table, record, categories, stored, record_id)\n", mock)
out("mock.py", text)

# --- stand-in
text = read(standin)
text = once(text, "categories=categories, stored=self.stored())", "categories=categories, stored=self.stored(), record_id=record_id)", standin)
out("standin.py", text)

# --- suite
text = read(suite)
case = '''
    @mark.req("IF-301", "REQ-GTB-021")
    @each_provider(IF, make=subject)
    def test_a_record_under_another_id_is_refused(self, tables):
        """TC-IF-301-20 golden 15: a record whose id is n1, checked with record_id x, gives record_identity naming id; with record_id n1, or without, it gives None.

        Example: {"id": "n1", "data": {"type": "data"}} with record_id="x" -> {"rule": "record_identity", "detail": "id"}.
        """
        # Given: a node record with its own ID n1
        record = node("n1", "data")
        # When/Then: under another record ID it is refused naming the field id; the twin under its own ID and the call without record_id are accepted
        self.assertEqual(tables.check_record("graph_nodes", record, record_id="x"), {"rule": "record_identity", "detail": "id"})
        self.assertIsNone(tables.check_record("graph_nodes", record, record_id="n1"))
        self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: the same holds for the other three tables
        for table, other in (("graph_edges", edge("e1", "n1", "n2")), ("skills", {"id": "s1", "data": {"command": "/s", "workflow_graph_id": "w", "context_graph_id": "c"}})):
            self.assertEqual(tables.check_record(table, other, record_id="x"), {"rule": "record_identity", "detail": "id"})
            self.assertIsNone(tables.check_record(table, other, record_id=other["id"]))
'''
text = once(text, "        self.assertLessEqual(min(timings), 0.5)\n", "        self.assertLessEqual(min(timings), 0.5)\n" + case, suite, done="def test_a_record_under_another_id_is_refused")
out("suite.py", text)
PY
copy "$WORK/requirements.md"      "$NODE/requirements.md"
copy "$WORK/test-spec.md"         "$NODE/test-spec.md"
copy "$WORK/test-requirements.md" "$NODE/test-requirements.md"
copy "$WORK/goal.md"              "$GOAL"
copy "$WORK/contract.md"          "$CONTRACT"
copy "$WORK/mock.py"              "$MOCK"
copy "$WORK/standin.py"           "$STANDIN"
copy "$WORK/suite.py"             "$SUITE"
copy specs/mia/amendments/A-92/test_graph_record_identity.py tests/acceptance/test_graph_record_identity.py
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check, errors about REQ-GTB-021 and TC-GTB-022 (the owner's review of REQ-GTB-021 is open: none about structure expected)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "GTB-021|GTB-022" || echo none
    echo "== the new checks (red until T-06 builds REQ-GTB-021; the mock side and everything else must pass)"
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
    python tests/acceptance/test_graph_record_identity.py 2>&1 | tail -1
    python tests/acceptance/test_graph_records.py 2>&1 | tail -1
fi
