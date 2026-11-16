# Draft: test requirements for the checks without one (G-V2.CONVERT; `specs/mia/test-requirements.md` is protected: a person applies this)

Two new items and one group row; in the format of the file (Status Draft). The ids of the five renumbered checks follow `test-spec-scenarios-draft.md` (TC-WFM-139 to 143); if the owner keeps other ids, change them here too.

Row for the group table of the CONVERT groups (after `Conversion exact values`):
| 4 | Conversion component checks | The unit and component checks of the converter, the toolbox entries and the descriptors | TR-CONVERT-008 |

### TR-CONVERT-008 – Component checks of the conversion use the shipped library and exact values
- Applies to: TC-WFM-116, TC-WFM-117, TC-WFM-118, TC-WFM-119, TC-WFM-120, TC-WFM-121, TC-WFM-122, TC-WFM-123, TC-WFM-124, TC-WFM-125, TC-WFM-126, TC-WFM-127, TC-WFM-128, TC-WFM-129, TC-WFM-139, TC-WFM-140, TC-WFM-141, TC-WFM-142, TC-WFM-143
- Requirement: REQ-WFM-058
- Group: Conversion component checks
- Kind: unit
- Text: Each check shall run on the shipped nodes and pipelines of `library/` as they are in the commit under test, with a scripted model and scripted tools (no model server, no network), and shall compare exact expected values (counts of nodes and edges, ids, orders, statuses, refusals) that are written out in its scenario.
- Rationale: the conversion is deterministic code; a check that used its own copy of a pipeline would pass while the shipped one changed; a model server would add noise that these checks do not need (the model-dependent equivalence is decided by TC-WFM-110 to 114)
- Credibility aspect: numerical settings
- Verified by: known answer
- Status: Draft

### TR-MODEL-006 – Stage checks use recording stages and fresh graphs
- Applies to: TC-RUN-030, TC-RUN-031, TC-RUN-032, TC-RUN-033, TC-RUN-034, TC-RUN-035
- Requirement: REQ-RUN-030, REQ-RUN-031, REQ-RUN-032, REQ-RUN-033, REQ-RUN-034, REQ-RUN-035
- Group: Stand-ins
- Kind: setup
- Text: The checks shall use recording stages that store the three objects they were called with and graphs written as data in each test, no model server and no shared state between tests, and shall compare the recorded objects exactly.
- Rationale: what a Stage receives and in which order nodes run is observable only by recording it; a graph or stage shared between tests could carry a value from one check into the next
- Credibility aspect: stand-in fidelity
- Verified by: review
- Status: Draft

(Row for the `Stand-ins` group of G-V2.MODEL: add `TR-MODEL-006` to its list.)
