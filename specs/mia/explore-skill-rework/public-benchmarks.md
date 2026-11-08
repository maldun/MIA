# Open labelled benchmarks: licence check (2026-11-05, web search, then LICENSE files read)

Input for Plan. Nothing adopted. "Confirmed" = a search result states it; "open" = no licence found. Public labels are third-party labels; adopting a set needs a plan decision, fixed splits and a contamination note (Wikipedia-based sets are probably in the model's training data).

| Set | Use for | Licence | Link | State |
|---|---|---|---|---|
| SciFact | claim verification on abstracts (supported / refuted, rationale sentences) | **Two sources disagree:** the HF dataset card says CC BY-NC 2.0 (non-commercial); the repo's `LICENSE.md` says claims and evidence annotations CC BY 4.0, abstracts ODC-By 1.0 (S2ORC), code Apache-2.0. Take the stricter (non-commercial) until the maintainers' statement is clear; fine for a personal project | https://github.com/allenai/scifact , data: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz | confirmed, conflict between card and repo file (re-read 2026-11-08) |
| SYNERGY | screening decisions of 26 systematic reviews (169 288 records, 2 834 included) | CC0 1.0 (metadata from OpenAlex, CC0) | DOI 10.34894/HE6NAQ (DataverseNL); the Python package `synergy-dataset` builds it | confirmed; the package would be a new dependency, so download the files instead |
| DocRED | document-level relations with evidence sentences | MIT (HF card; repo `LICENSE` is MIT and the repo holds the `data` folder) | https://github.com/thunlp/DocRED | confirmed (repo and card, 2026-11-08) |
| Re-DocRED | the same, missed relations added (4 053 docs; 3 053 train, 500 dev, 500 test) | repo `LICENSE` MIT (GitHub API, 2026-11-08), and the repo holds the `data` folder; no separate data licence stated | https://github.com/tonytan48/re-docred (data in `./data`) | confirmed for the repo and its data folder; the texts are Wikipedia-based and Wikipedia text is CC BY-SA, which the MIT file does not mention: open question, harmless for personal use, to settle before any sharing |
| SciERC | entities and relations in 500 scientific abstracts | none stated on the project page (page read 2026-11-08, status 200, no licence or terms text). HF copies by third parties carry no licence or an unrelated one (one derivative says CC BY-NC 2.0); none is authoritative | http://nlp.cs.washington.edu/sciIE/ | open: no licence stated anywhere; ask the authors before use |
| AgentDojo | prompt-injection tests for tool agents | MIT (repo `LICENSE`, GitHub API 2026-11-08; the README only shows the licence badge) | https://github.com/ethz-spylab/agentdojo | confirmed for the code and the repo |
| InjecAgent | indirect prompt injection | MIT (file is named LICENCE; no separate data licence) | https://github.com/uiuc-kang-lab/InjecAgent | confirmed |
| BIPIA | indirect prompt injection | code MIT; parts of the data CC BY-SA 4.0 (WikiTableQuestions, Stack Exchange); Web QA and summarization data may not be redistributed, fetch from the source with their scripts | https://github.com/microsoft/BIPIA | confirmed from its LICENSE and README |

Not checked: FEVER, HoVer, Climate-FEVER, HotpotQA, MuSiQue, ALCE, QASPER, MS², LitSearch, CLEF TAR, TruthfulQA.

Notes for Plan
- DocRED's relation set is closed (96 types) and its labels are incomplete: use it for recall and wrong relations, not for the "invented" share.
- SciFact fits the review skill's verification step; SYNERGY its screening step (keep/drop). Neither tests the persona.
- Red-team material (AgentDojo, InjecAgent) belongs to the red-team cases, which the agent never edits.

Re-check 2026-11-08 (primary sources: GitHub licence API and LICENSE files, HF dataset API, project page): the open rows are SciERC (still no licence anywhere authoritative, ask the authors or leave it out), the SciFact conflict, and the Wikipedia text under DocRED / Re-DocRED. InjecAgent and BIPIA were not re-read. Plan decides what is adopted; nothing is adopted here.
