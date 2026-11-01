# Verification report: node N-2.5 Voice synthesis, first Verify (2026-11-01)

**Verifier:** fresh session, branch `v1-n25-verify` from goal/v1 `1293c7e` (round 4 and the N-2.2, N-2.3 reports merged). I did not implement N-2.5. I changed no code, test, skill or suite; I ran no model and no TTS engine (the tests use a fake engine). Mutants ran on a scratch copy in my scratchpad. I did not listen to any audio.
**Scope:** REQ-VOI-001 to -004 and IF-204. `goals/G-V1/goal.md` has no scope row for them, so all five are in G-V1.

**Verdict proposal: Verified with accepted deviations, once the owner decides V1.** Each requirement has a passing test that can fail (6 of 8 mutants killed, the 2 survivors are low), the IF-204 provider passes its contract suite, and the protected files are the approved ones. The deviation is that the provider is not part of the running app yet. If the owner does not accept it: **Not verified.**

## Automated results
| Check | Result |
|---|---|
| 11 Python files in the image, from this worktree | all OK: `test_speech_service` 9, `test_speech_text` 18, `test_speech_repair` 3, `test_speech_stop` 4, `test_voice_lines` 8, `test_make_voice_lines` 4, `test_voice_effects` 22, `test_workflow_voice` 5, protected `acceptance/test_voice_synthesis` 3 (TC-VOI-001 to -003), contract `test_if_204_speech` 6 (mock and real provider), integration `N-2/step_01` 1 (skipped, see V1) |
| JS contract IF-112 (voice player, N-1.3) | 5 pass, 0 fail |
| Round-4 trial run (earlier today) | all these files were OK |
| `trace_check.py` | no ERROR or WARN for REQ-VOI-001 to -004 |
| Protected material | `test_voice_synthesis.py`, the IF-204 contract suite, its mock and the adapter in `contract.py`: changed only by A-13 (`055c475`, `44783a8`) since the baseline; `contracts/IF-204-speech.md`: unchanged since the plan |
| Code against architecture | `speech_service.py` imports the engine only through `Speaker`; no storage or database import |
| Static analysis, security scan, `test_doc_check` | not run (no checker configured; not counted per node) |

## Mutants (scratch copy, the 6 test files of the module)
Killed (6): markup not removed before synthesis; empty text sent to the engine; an engine failure not turned into `unavailable`; a silent mood not answered with `no_line`; a missing line file not skipped (`VoiceLines.pick`); html tags spoken (`speech_text.TAG`).
**Survived (2):** an empty audio result is accepted (`if not audio:` removed); a voice line name that leaves the folder is accepted in the fallback mode without a mood map (`os.path.basename(name) != name` removed).

## Verification matrix
| Requirement | Method | Evidence | Result |
|---|---|---|---|
| REQ-VOI-001 sentence by sentence, with the voice effect | Test | `test_tc_voi_001`: a 5-sentence answer yields 5 chunks, one per sentence; `test_speech_service`; the effect is inside `Speaker.render_voice` (`test_voice_effects` 22) | verified for the provider; in the app the sentences go through `SpeechStreamer` and the same `render_voice` (V1) |
| REQ-VOI-002 only what is meant to be heard | Test | `test_tc_voi_002`: 10 answers with markup, synthesis input has none (exact); `test_speech_text` 18 (html tags, markdown marks, `*actions*`); the app path filters with the same `speech_text` (`speech_stream.py:62`); markup mutants killed | verified |
| REQ-VOI-003 voice lines | Test | `test_tc_voi_003`: every mood has a line or is declared silent, a missing file is logged and skipped; `test_voice_lines` 8; the mutant of the skip is killed | verified |
| REQ-VOI-004 default lines generated | Inspection | `tools/make_voice_lines.py` renders `library/voice_line_texts.json` (12 texts) with `Speaker`; `library/voice_lines.json` lists exactly 12 files `<mood>_default.wav`, all present in the owner's stack (`goal-v1/voice/expressions`, made 2026-10-31); no listed file is an old clip (the older recordings in the folder are not listed); the tool's docstring says no third-party recording is used | verified by inspection of tool, texts and list; I cannot tell by ear that no clip is a recording (V3) |
| IF-204 | Test | contract suite 6 OK against the mock and the real `SpeechService` (A-13) | verified |

## Agent checks
No eval criterion, prompt or skill belongs to this node. The node's input is text from the chat model; `speech_text` strips markup and stage directions before the engine (REQ-VOI-002), and the engine has no tools or network.

## Findings
| ID | Severity | Finding | Destination |
|---|---|---|---|
| V1 | medium | `SpeechService`, the provider of IF-204, is called by no part of the app. The live path is `SpeechStreamer` → `Speaker` (same `speech_text` filter, same `render_voice`), so the behaviour reaches the user, but through the older route. The N-2 integration step 1 ("N-2.5 real") is skipped, and the `audio_chunk` event of an answer is not built, which is why the IF-201 contract keeps 1 skip and the IF-101 contract 2 (one of them REQ-CHV-008, out of G-V1). | Owner/N-2 integration: wire the chat agent's audio through IF-204, or record the older route as the accepted G-V1 form (scope row "partly" for REQ-VOI-001 and the integration step) |
| V2 | low | Two mutants survive: empty audio accepted; a line name may leave the folder in the fallback mode (no mood map; unused in the app). | Implement: two small tests |
| V3 | info | The default lines are untracked files (`voice/` is not in git). Their provenance is the texts file and the tool; a fresh checkout has none until `tools/make_voice_lines.py` runs (the RUNBOOK names it; the owner's stack has all 12). The main checkout lacks `shocked_default.wav`. | Deploy (RUNBOOK) |
| V4 | info | Whether the voice sounds right (anime effect, Kokoro) is the owner's judgement (decision of 2026-10-18); nothing in this node measures it. | Phase 7 |

No blocker. Only V2 goes back to Implement.

## What I could not check
Audio quality and the absence of third-party recordings by ear; a real TTS run; the sound server path (`test_speech_stop` covers the streamer with a fake); IF-204 against a real chat turn (V1).

## For the team
Decide V1. After that, V2 is two tests.
