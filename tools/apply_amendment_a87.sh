#!/usr/bin/env bash
# Amendment A-87 (merge gate of G-V1, 2026-11-01; owner decision D-181): TD records for the remaining deviations of the goal Verify, and the strict expected failure that keeps
# the two known red tests from turning the gate red without hiding them.
#   TD-23  the contract suites IF-103, IF-404, IF-405 have only the mock side executed (D-5, F-03); the JS real cases of IF-104 name a reason that is no longer true
#   TD-24  `sandbox_backend: none` in the deployed stack: the script check is off (D-8, F-15), REQ-TLS-005 holds by refusing
#   F-08   the stage step `quality` failed with 7 errors because the ids live in the node files
#   TD-16  its target also names the baseline of BM-GATE-001, which tests/acceptance/test_benchmarks.py waits for (known failing file)
#   mark.deferred(TD) in tests/helpers/markers.py: a unittest expectedFailure that names its record; it fails when the check starts to pass (M26, strict xfail)
# Note: specs/mia/amendments/A-87/A-87-note.md
# Made from the INSTALLED files at run time, each edit refused when its anchor is not found as expected:
#   specs/mia/deferred.md                          TD-23 and TD-24 appended; the Target line of TD-16 extended
#   specs/mia/nodes/.../requirements.md (3 files)  IF-103, IF-404, IF-405 (TD-23) and REQ-TLS-005 (TD-24) get `Relaxed`, `Target`, History
#   tests/helpers/markers.py                       mark.deferred
#   tests/acceptance/test_benchmarks.py            the test carries mark.deferred("TD-16")
#   tests/helpers/contract.mjs                     the skip reason of the IF-104 real cases
#   stages.yaml                                    the step `quality` passes the requirement files of all nodes (F-08), not only the root file
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-86 installed).
#   bash tools/apply_amendment_a87.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a87.sh --do      install and run the trace check; commit afterwards as "plan: A-87 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
N2=specs/mia/nodes/N-2-backend/requirements.md
STAGES=stages.yaml
N24=specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.2-tools-and-sandbox/requirements.md
python3 - specs/mia/deferred.md "$N2" "$N24" tests/helpers/markers.py tests/acceptance/test_benchmarks.py tests/helpers/contract.mjs stages.yaml "$WORK" <<'PY'
import os
import re
import sys
deferred, n2, n24, markers, bench, contract, stages, work = sys.argv[1:9]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)
OWNER = "Stefan Reiterer"
TRIGGER = "the Plan of the next iteration, or 2026-12-31, whichever first"
T23 = ("TD-23", "Real sides of the contract suites IF-103, IF-404, IF-405", ["IF-404", "IF-405", "IF-103"],
       "the mock side of each suite is green and the providers are covered by node tests (`tests/test_tool_calls*.py`, `tests/test_scholar.py`, the fake model server of the chat and runner tests); IF-111 has `ui/godot/tools/test_bridge.gd` as its real side (D-155, D-175), IF-102 on PostgreSQL is in TD-21",
       "the three suites run their real side: IF-404 against the web client and SearXNG, IF-405 against the scholarly APIs, IF-103 against a real model-server provider (stage 2, decomposition rule 3); the IF-104 JS real cases name `tests/test_graph_api.py` as their real side or run against the routes",
       "the real sides need the network, the search engine or the model server, and the IF-103 suite cannot hand its scripted replies to a real provider (REQ-RUN-011 out, D-118); found at the goal Verify (D-5, F-03); the owner chose to give them a record (D-181)",
       "about 2 days (the IF-103 provider and a suite amendment included)",
       "a mock that differs from the real service goes unnoticed; the node tests and the owner's use are the check")
T24 = ("TD-24", "Sandbox backend in the deployed stack", ["REQ-TLS-005"],
       "REQ-TLS-005 holds by its refuse branch: with `sandbox_backend: none` a script check reports unavailable and nothing runs (the sandbox tests, `tests/test_sandbox*.py`, pass with bubblewrap on the host); the PDF wall and the tool door do not depend on it",
       "the deployed stack has a sandbox backend (bubblewrap or podman) so that the script checks run there, and the red-team cases for scripts (THR-005) are run against it",
       "`deploy/setup_cfg.compose.json` sets `sandbox_backend` to `none`, so the script check is off in the stack; found at the goal Verify (D-8, F-15); the owner chose to give it a record (D-181)",
       "about 1 day (a backend in the image or next to it, the config, a smoke test)",
       "the checks that run model-written code are not available in the deployed system, MIA refuses them; nothing unsafe runs")
RECORDS = [T23, T24]


def td_block(td, title, reqs, interim, target, reason, effort, risk):
    return ("## %s – %s\n- Kind: defer\n- Requirement: %s\n- Interim criterion: %s\n- Target: %s\n- Reason: %s\n- Effort: %s (proposed)\n- Risk of the gap: %s\n- Owner: %s\n"
            "- Trigger: %s\n- Target check: specified only\n- Decision: D-181, 2026-11-01, %s\n- Status: open\n" % (td, title, ", ".join(reqs), interim, target, reason, effort, risk, OWNER, TRIGGER, OWNER))


text = read(deferred)
if "## TD-23 " not in text:
    if text.count("## TD-22 ") != 1:
        sys.exit("%s: TD-22 is not found exactly once; install A-87 by hand (A-86 must be installed)" % deferred)
    text = text.rstrip("\n") + "\n\n" + "\n".join(td_block(*r) for r in RECORDS)
EXTRA = "; and the baseline of BM-GATE-001 (seconds per claim of the number gate on MP-light, `benchmarks/baseline.json`) is measured, so that `tests/acceptance/test_benchmarks.py` turns green"
m = re.search(r"^## TD-16 [^\n]*\n(?:(?!^## ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TD-16 is not found; install A-87 by hand" % deferred)
block = m.group(0)
if "BM-GATE-001" not in block:
    lines = re.findall(r"^- Target: .*$", block, re.M)
    if len(lines) != 1:
        sys.exit("%s: TD-16 has no single Target line; install A-87 by hand" % deferred)
    text = text.replace(block, block.replace(lines[0], lines[0] + EXTRA, 1), 1)
out("deferred.md", text)


def relax_all(path, name, pairs):
    req = read(path)
    for rid, td, target in pairs:
        m = re.search(r"^### %s – [^\n]*\n(?:(?!^### ).*\n)*" % re.escape(rid), req, re.M)
        if not m:
            sys.exit("%s: the block of %s is not found; install A-87 by hand" % (path, rid))
        block = m.group(0)
        if "- Relaxed: %s\n" % td in block:
            continue
        if "- Relaxed:" in block or block.count("\n- Status: Approved\n") != 1:
            sys.exit("%s: %s has a Relaxed line already or no single 'Status: Approved' line; install A-87 by hand" % (path, rid))
        new = block.replace("\n- Status: Approved\n", "\n- Status: Approved\n- Relaxed: %s\n- Target: %s\n" % (td, target), 1)
        if re.search(r"^- History: –$", new, re.M):
            new = re.sub(r"^- History: –$", "- History: A-87 (2026-11-01): Relaxed %s (D-181)" % td, new, flags=re.M)
        else:
            new = re.sub(r"^(- History: .*)$", lambda mm: mm.group(1) + "; A-87 (2026-11-01): Relaxed %s (D-181)" % td, new, count=1, flags=re.M)
        req = req.replace(block, new, 1)
    out(name, req)


relax_all(n2, "n2.md", [("IF-103", "TD-23", T23[4])])
relax_all(n24, "n24.md", [("IF-404", "TD-23", T23[4]), ("IF-405", "TD-23", T23[4]), ("REQ-TLS-005", "TD-24", T24[4])])

text = read(markers)
if "def deferred" not in text:
    if text.count("class _Mark:\n") != 1 or text.count("    @staticmethod\n    def statistical(fn):") != 1:
        sys.exit("%s: anchors not found; install A-87 by hand" % markers)
    text = text.replace("\n\nclass _Mark:\n", "\n\nimport unittest  # noqa: E402\n\n\nclass _Mark:\n", 1)
    text = text.replace("    @staticmethod\n    def statistical(fn):", '''    @staticmethod
    def deferred(td):
        """a check whose target is deferred (M26, deferred.md): a strict expected failure that names its record; it fails (an unexpected success) as soon as the check passes"""
        def decorate(fn):
            fn.deferred_td = td
            return unittest.expectedFailure(fn)
        return decorate

    @staticmethod
    def statistical(fn):''', 1)
out("markers.py", text)

text = read(bench)
new = '    @mark.deferred("TD-16")\n    @mark.req("NFR-BUD-001")\n'
if 'mark.deferred("TD-16")' not in text:
    if text.count('    @mark.req("NFR-BUD-001")\n') != 1:
        sys.exit("%s: the marker line is not found exactly once; install A-87 by hand" % bench)
    text = text.replace('    @mark.req("NFR-BUD-001")\n', new, 1)
out("test_benchmarks.py", text)

text = read(contract)
old = "  'IF-104': 'N-2 Backend does not serve the routes of IF-104 yet',\n"
new = "  'IF-104': 'real side: tests/test_graph_api.py in the image (A-60, A-66); the JS real cases skip (TD-23)',\n"
if new not in text:
    if text.count(old) != 1:
        sys.exit("%s: the IF-104 line is not found exactly once; install A-87 by hand" % contract)
    text = text.replace(old, new, 1)
out("contract.mjs", text)

text = read(stages)
OLD = "--requirements specs/mia/requirements.md\""
NEW = "--requirements specs/mia/requirements.md specs/mia/nodes/*/requirements.md specs/mia/nodes/*/nodes/*/requirements.md specs/mia/nodes/*/nodes/*/nodes/*/requirements.md\""
if NEW not in text:
    if text.count(OLD) != 1:
        sys.exit("%s: the requirements argument of the quality step is not found exactly once; install A-87 by hand" % stages)
    text = text.replace(OLD, NEW, 1)
out("stages.yaml", text)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/n2.md" "$N2"
copy "$WORK/n24.md" "$N24"
copy "$WORK/markers.py" tests/helpers/markers.py
copy "$WORK/test_benchmarks.py" tests/acceptance/test_benchmarks.py
copy "$WORK/contract.mjs" tests/helpers/contract.mjs
copy "$WORK/stages.yaml" stages.yaml
finish
echo
echo "== trace_check, errors about TD-23, TD-24 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*TD-2[34]" || echo none
echo "== test_benchmarks (an expected failure)"
python3 tests/acceptance/test_benchmarks.py 2>&1 | tail -3
