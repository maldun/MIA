# Open labelled benchmarks: licence check (2026-11-05, web search only)

Input for Plan. Nothing adopted. "Confirmed" = a search result states it; "open" = the LICENSE file of the source must still be read before use. Public labels are third-party labels; adopting a set needs a plan decision, fixed splits and a contamination note (Wikipedia-based sets are probably in the model's training data).

| Set | Use for | Licence | Link | State |
|---|---|---|---|---|
| SciFact | claim verification on abstracts (supported / refuted, rationale sentences) | CC BY-NC 2.0 (non-commercial; fine for a personal project) | https://github.com/allenai/scifact , data: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz | confirmed (HF card and repo) |
| SYNERGY | screening decisions of 26 systematic reviews (169 288 records, 2 834 included) | CC0 1.0 (metadata from OpenAlex, CC0) | DOI 10.34894/HE6NAQ (DataverseNL); the Python package `synergy-dataset` builds it | confirmed; the package would be a new dependency, so download the files instead |
| DocRED | document-level relations with evidence sentences | MIT (HF card) | https://github.com/thunlp/DocRED | confirmed for DocRED |
| Re-DocRED | the same, missed relations added (4 053 docs; 3 053 train, 500 dev, 500 test) | not found | https://github.com/tonytan48/re-docred (data in `./data`) | open: read its LICENSE; derives from MIT DocRED |
| SciERC | entities and relations in 500 scientific abstracts | not found | http://nlp.cs.washington.edu/sciIE/ | open |
| AgentDojo | prompt-injection tests for tool agents | not found | https://github.com/ethz-spylab/agentdojo | open |
| InjecAgent | indirect prompt injection | not found | https://github.com/uiuc-kang-lab/InjecAgent | open |
| BIPIA | indirect prompt injection | not found | repo not found by search | open |

Not checked: FEVER, HoVer, Climate-FEVER, HotpotQA, MuSiQue, ALCE, QASPER, MS², LitSearch, CLEF TAR, TruthfulQA.

Notes for Plan
- DocRED's relation set is closed (96 types) and its labels are incomplete: use it for recall and wrong relations, not for the "invented" share.
- SciFact fits the review skill's verification step; SYNERGY its screening step (keep/drop). Neither tests the persona.
- Red-team material (AgentDojo, InjecAgent) belongs to the red-team cases, which the agent never edits.
