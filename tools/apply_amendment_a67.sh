#!/usr/bin/env bash
# Amendment A-67 (N-3.3 re-verification R1, R2; owner decision D-170, 2026-10-31): IF-302 v7, deletable are exactly `history`, `memory`, `tasks`, `memos`,
# and TC-IF-302-01 checks that whole set (a provider with `history` not deletable or `source_trust` deletable failed no case before); the IF-302 line of
# REAL_NOT_READY gets the reason of A-60's IF-301 line.
# Protected files that change, ALL BUILT FROM THE INSTALLED FILES at run time (A-62 changed contract.py and test-spec.md; A-65 and A-66 may change test-spec.md):
#   contracts/IF-302-record-tables.md                          v7: the deletable note of definitions(), golden example 3, the version line
#   tests/acceptance/contract/test_if_302_record_tables.py     TC-IF-302-01: the set of deletable tables is equal to the four (mock and real)
#   tests/helpers/contract.py                                  the IF-302 line of REAL_NOT_READY: "unused: real_subject gives record_tables" (R1)
#   specs/mia/test-spec.md                                     the row of TC-IF-302-01
# Also (node file): the N-3.3 requirements.md, the History of IF-302. The mock is unchanged: it makes exactly the four deletable already, as record_tables.py does.
# Note: specs/mia/amendments/A-67/A-67-note.md
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a67.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a67.sh --do      install and run the IF-302 suite (mock and real); commit afterwards as "plan: A-67 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 - "$TMP" "$NODE" <<'PY'
import os, re, sys
tmp, node = sys.argv[1], sys.argv[2]


def build(path, name, edits, done):
    """edits: (old, new) pairs that must each occur once; `done` in the text means installed already."""
    text = open(path, encoding="utf-8").read()
    if done not in text:
        for old, new in edits:
            if text.count(old) != 1:
                sys.exit("%s is not what A-67 expects (%r): check it" % (path, old[:80]))
            text = text.replace(old, new)
    open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)


contract = "contracts/IF-302-record-tables.md"
text = open(contract, encoding="utf-8").read()
title = re.search(r"^# IF-302 .*, v(\d+)$", text, re.M)
if not title:
    sys.exit("the title of IF-302 has no version where A-67 expects it: check " + contract)
version = int(title.group(1)) + (0 if "| A-67 |" in text else 1)
history = [l for l in text.split("\n") if re.match(r"\| v\d+ \| ", l)][-1]
build(contract, "IF-302-record-tables.md", [
    (title.group(0), re.sub(r"v\d+$", "v%d" % version, title.group(0))),
    ("| `memory`, `tasks`, `memos` are deletable (a user deletes any record, FR-14); `votes` and `runs` are not |",
     "| **[v%d]** deletable are exactly `history`, `memory`, `tasks`, `memos` (a user deletes any record, FR-14); every other table, `votes`, `runs` and `source_trust` among them, is not |" % version),
    ("3. Edge: `memory` is deletable, `votes` is not;",
     "3. Edge: exactly `history`, `memory`, `tasks` and `memos` are deletable **[v%d]**, `votes` and `source_trust` are not;" % version),
    (history + "\n", history + "\n| v%d | 2026-10-31 | the deletable tables named in full: exactly `history`, `memory`, `tasks`, `memos` (as built and mocked; v0 to v6 named only `memory`, `tasks`, `memos`, `votes`, `runs`); TC-IF-302-01 checks the whole set (owner 2026-10-31: re-verification R2 of N-3.3, D-170) | A-67 |\n" % version),
], "| A-67 |")
build("tests/acceptance/contract/test_if_302_record_tables.py", "test_if_302_record_tables.py", [
    ('"""TC-IF-302-01 golden 3: memory, tasks and memos are deletable, votes and runs are not; every table is versioned."""',
     '"""TC-IF-302-01 golden 3: deletable are exactly history, memory, tasks and memos (v7, A-67), so votes, runs and source_trust are not; every table is versioned."""'),
    ('        self.assertTrue(all(d["versioned"] for d in defs.values()))\n',
     '        self.assertTrue(all(d["versioned"] for d in defs.values()))\n'
     '        self.assertEqual({t for t, d in defs.items() if d["deletable"]}, {"history", "memory", "tasks", "memos"})      # v7 (A-67): the whole set\n'),
], "(v7, A-67)")
build("tests/helpers/contract.py", "contract.py", [
    ('    "IF-302": "N-3.3 Record tables not integrated yet",\n',
     '    "IF-302": "unused: real_subject gives record_tables",       # real_subject since A-02 (record_tables); the reason fixed by A-67 (R1)\n'),
], "the reason fixed by A-67")
build("specs/mia/test-spec.md", "test-spec.md", [
    ("| TC-IF-302-01 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 3: memory, tasks and memos are deletable, votes and runs are not; every table is versioned. | exact |",
     "| TC-IF-302-01 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 3: deletable are exactly history, memory, tasks and memos (A-67), so votes, runs and source_trust are not; every table is versioned. | exact |"),
], "exactly history, memory, tasks and memos (A-67)")
lines = open(node, encoding="utf-8").read().split("\n")
start = lines.index("### IF-302 – Record table definitions and validation")
hist = next(i for i in range(start, len(lines)) if lines[i].startswith("- History: "))
if "A-67" not in lines[hist]:
    lines[hist] += "; 2026-10-31 A-67 (D-170): IF-302 v%d, deletable are exactly history, memory, tasks, memos" % version
open(os.path.join(tmp, "requirements.md"), "w", encoding="utf-8").write("\n".join(lines))
PY
copy "$TMP/IF-302-record-tables.md" contracts/IF-302-record-tables.md
copy "$TMP/test_if_302_record_tables.py" tests/acceptance/contract/test_if_302_record_tables.py
copy "$TMP/contract.py" tests/helpers/contract.py
copy "$TMP/test-spec.md" specs/mia/test-spec.md
copy "$TMP/requirements.md" "$NODE"
finish
echo
python3 tests/acceptance/contract/test_if_302_record_tables.py
