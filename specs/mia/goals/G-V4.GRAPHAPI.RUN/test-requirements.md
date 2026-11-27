# Test requirements: G-V4.GRAPHAPI.RUN

**Test spec:** `test-spec.md`   **Status:** Draft (2026-11-24, written by the agent, for the owner's review by group)

At the merge TR-RUN-001 to 012 go unchanged into the protected `specs/mia/test-requirements.md` (new section at the end, groups as rows of its `## Groups` table), through an owner's script as for RULES. TR-CONVERT-001 to 007 of G-V2 stay where they are; TR-RUN-011 adopts TR-CONVERT-001 to 005 for the stored-graph path, TR-RUN-005 adopts TR-CONVERT-006.

<!-- Requirements on the checks, apart from the product requirements: under which conditions a measurement counts. Setup kind: the verdict depends on the setup; written out and reviewed in detail. Unit kind: exact expected values; grouped and signed off as a group. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | EX | Exact values: expected IDs, orders, lists of calls and outputs, signed off as a group | TR-RUN-001 |
| 2 | DA | Data: the oracle, the random graphs and the converted skills the checks run on | TR-RUN-002, TR-RUN-003, TR-RUN-004 |
| 3 | EP | Entry points and stand-ins: the fake model server, the markers, the throw-away store, the clock | TR-RUN-005, TR-RUN-006, TR-RUN-009, TR-RUN-012 |
| 4 | CR | Ability to fail, inspections and protected material | TR-RUN-007, TR-RUN-008, TR-RUN-010 |
| 5 | EV | The equivalence runs on the stored-graph path | TR-RUN-011 |

### TR-RUN-001 – Exact values
- Applies to: TC-GTB-048, TC-GTB-049, TC-GTB-050, TC-GTB-053, TC-IF-301-35, TC-IF-301-36, TC-IF-301-37, TC-IF-301-38, TC-IF-301-39, TC-WFM-186, TC-RUN-041, TC-RUN-046, TC-WFM-115
- Requirement: REQ-GTB-053
- Group: EX
- Kind: unit
- Text: The expected values of these checks shall be written as exact values: IDs, keys, attributes, orders, field values and outputs, with no tolerance and no check by "contains".
- Rationale: every outcome is an ID, an order or an equality (test spec, limit column); a check that ignored the order or allowed extra nodes or edges would hide a loader that keeps a malformed item or loses a parallel connection.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Approved

### TR-RUN-002 – The oracle is recorded before any code changes
- Applies to: TC-GTB-052, TC-WFM-186, TC-RUN-045, TC-RUN-048
- Requirement: HR-006
- Group: DA
- Kind: setup
- Text: The oracle shall be recorded by one script at a named commit of `goal/v4` before the first code change of RUN, hold the `rule_report` and `run_check` answers, the orders of `order_of` and the model calls and answers of the six skills on scripted replies, and the checks shall fail when that commit is not an ancestor of the tested code or the file differs from its committed version.
- Rationale: "the same as before" (OC-2, HR-006) needs a record of before that the change cannot touch; recorded after a change it would confirm the change; the oracle file is protected material (a helper under `tests/helpers/`), changed only by an amendment.
- Credibility aspect: reference accuracy
- Verified by: inspection (git log of the oracle file, the commit named in its header)
- Status: Approved

### TR-RUN-003 – The 500 random graphs
- Applies to: TC-GTB-052, TC-WFM-185, TC-WFM-186
- Requirement: REQ-GTB-060
- Group: DA
- Kind: setup
- Text: The random graphs shall come from one generator in `tests/helpers/` with `random.Random(7)`: 500 workflow graphs of 2 to 8 steps of the types data, transform and master, connections drawn between any two steps including self loops and parallel connections, and the check shall fail when fewer than 500 graphs or another count of acyclic graphs than the oracle's is produced.
- Rationale: the networkx spike used 500 random graphs with seed 7 and self loops, but as scratch code; the generator is now fixed in the repository and its acyclic count is stored with the oracle, so a silently changed generator cannot make the check easier; the seed is fixed in Plan and never changed to make a check pass.
- Credibility aspect: validity domain
- Verified by: known answer (the counts stored with the oracle)
- Status: Approved

### TR-RUN-004 – The converted skills
- Applies to: TC-GTB-048, TC-GTB-049, TC-GTB-052, TC-WFM-185
- Requirement: HR-006
- Group: DA
- Kind: setup
- Text: The converted skill graphs shall be built at test time with `tests/helpers/rules_graphs.converted_skills`, as TR-RULES-004 requires, and the check shall fail when fewer than 15 graphs are built or `review_full`, `research` or `verify_computable` is missing.
- Rationale: built, not copied, so a change of a skill shows up; the three named skills carry the cases OC-3 names (six named inputs, master steps); a check over zero graphs passes.
- Credibility aspect: reference accuracy
- Verified by: known answer (15 skills on 2026-11-24)
- Status: Approved

### TR-RUN-005 – The fake model server
- Applies to: TC-WFM-187, TC-RUN-044, TC-RUN-045, TC-RUN-046, TC-RUN-047, TC-RUN-048
- Requirement: REQ-WFM-168
- Group: EP
- Kind: setup
- Text: These checks shall meet TR-CONVERT-006 (the fake model server of `pipeline.py` passes the contract suite of the model server interface and never decides an eval criterion) and use the scripted replies of REQ-WFM-058 unchanged.
- Rationale: the checks compare lists of calls, so the fake must record prompt and options as the real client sends them; the same scripted replies as G-V2 make a difference come from the stored-graph path, not from new replies.
- Credibility aspect: stand-in fidelity
- Verified by: contract suite
- Status: Approved

### TR-RUN-006 – No step ran, shown by markers that can fire
- Applies to: TC-RUN-047, TC-RUN-041
- Requirement: REQ-RUN-045
- Group: EP
- Kind: setup
- Text: "No step ran" and the run order shall be shown by a marker function per step that records its calls, and in the same check a sound twin shall call each of its markers.
- Rationale: as TR-RULES-005: a count of zero proves nothing if the markers cannot be called.
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (a runner that falls back to version 1 or runs the first step before the run check must fail TC-RUN-047)
- Status: Approved

### TR-RUN-007 – Each check is shown able to fail
- Applies to: TC-GTB-048, TC-GTB-050, TC-GTB-051, TC-GTB-052, TC-GTB-053, TC-WFM-185, TC-WFM-186, TC-RUN-042, TC-RUN-044, TC-RUN-046, TC-RUN-047, TC-RUN-048, TC-RUN-049, TC-WFM-187
- Requirement: REQ-GTB-060
- Group: CR
- Kind: setup
- Text: Each of these checks shall be shown able to fail by running it once against a deliberate defect of the unit it checks, before the check is trusted.
- Rationale: the defects: the loader keeps a second `d1` or drops a parallel connection; data shared, not copied; one rule answering from its old view with one changed branch; ties by ID instead of position; two steps run in a thread pool; the stored graph ignored (the in-memory converted graph runs); version 1 run instead of the newest; the run record without `graph_version`; one prompt changed in the stored graph; the answer taken from the last data step of the stored form (A-190); `graph_run.py` importing `graph_model` (A-190).
- Credibility aspect: reviewer independence
- Verified by: mutation
- Status: Approved

### TR-RUN-008 – What the inspections check
- Applies to: TC-GTB-051, TC-RUN-043
- Requirement: REQ-GTB-059
- Group: CR
- Kind: setup
- Text: The inspections shall be done by the owner or the verifying reviewer with a written checklist, one line per function of `graph_rule_set.py` and `graph_run.py`, backed by a search that finds no `["nodes"]`, `["edges"]`, adjacency map or cycle finder outside the loader.
- Rationale: REQ-GTB-059 and REQ-RUN-041 are about where the graph is read, which a test of the answers cannot see (the answers stay the same by TC-GTB-052); the search makes the inspection repeatable, the checklist covers what a search misses (a view built under another name).
- Credibility aspect: reviewer independence
- Verified by: inspection
- Status: Approved

### TR-RUN-009 – The throw-away store and the counted read
- Applies to: TC-RUN-044, TC-RUN-045, TC-RUN-046, TC-RUN-047, TC-RUN-048, TC-WFM-187, TC-WFM-115, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114, SMOKE-RUN-001
- Requirement: REQ-RUN-042
- Group: EP
- Kind: setup
- Text: Each of these checks shall save its graphs through CORE's save path into a new files store in a temporary folder, read them through N-2.3 wrapped to count its calls, and delete the store at the end.
- Rationale: D-476: RUN's checks do not wait for MIGRATION's import; the save path, not a hand-written file, so a stored graph is one the rules accepted; a count proves the graph was read from the store and not taken from memory; a fresh store per check, so one check cannot feed another.
- Credibility aspect: stand-in fidelity
- Verified by: inspection
- Status: Approved

### TR-RUN-010 – The contract suites, both sides, older suites untouched
- Applies to: TC-IF-301-35, TC-IF-301-36, TC-IF-301-37, TC-IF-301-38, TC-IF-301-39, TC-RUN-043
- Requirement: REQ-GTB-053
- Group: CR
- Kind: setup
- Text: The IF-301 v5 mock shall pass the same contract cases as the real module, and the suites of IF-301 v1 to v4 and TC-RUN-016 to 019 and 030 to 039 shall run from files that `git diff goal/v4` shows unchanged.
- Rationale: EDIT, CONTEXT, VIEW and the runner test against the mock, so it must agree with the real side on every golden example (A-187 is a joint amendment); a suite edited to pass would hide a changed answer.
- Credibility aspect: stand-in fidelity
- Verified by: contract suite on both sides; inspection (git diff)
- Status: Approved

### TR-RUN-011 – The equivalence runs on the stored-graph path
- Applies to: TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: EV
- Kind: setup
- Text: These checks shall meet TR-CONVERT-001 to TR-CONVERT-005 with the skill run from its stored graph in place of the converted skill, use the old-runner baselines of commit `1fb0c35` unchanged, and write into the run header the stored-graph path, the graph ID and its version.
- Rationale: the rule of G-V2 (pin, repeats, fresh seeds for the one re-run, power, dev cases) stays as it was, only the path changes (D-473 (3)); the baselines were recorded at 3 repeats before any converted run (A-122), so TR-CONVERT-004 is met without a new baseline; the header proves which path ran.
- Credibility aspect: repetitions and seeds
- Verified by: inspection of the run header and `eval_decide.py --rerun`
- Status: Approved

### TR-RUN-012 – One step at a time, measured on a monotonic clock
- Applies to: TC-RUN-042
- Requirement: REQ-RUN-040
- Group: EP
- Kind: setup
- Text: The check shall take start and end of each step from `time.monotonic()`, let each step sleep 0.05 s, and compare start with the end of the step before it with no tolerance.
- Rationale: a monotonic clock cannot step back; 0.05 s is long enough that two steps run at the same time overlap by far more than the clock's resolution, so the defect of TR-RUN-007 (a thread pool) fails the check on every run, and the check costs about 0.3 s.
- Credibility aspect: numerical settings
- Verified by: mutation
- Status: Approved
