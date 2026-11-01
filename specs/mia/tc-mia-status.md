# TC-MIA status (root checks of specs/mia/test-spec.md)

Written 2026-11-01 for A-82. An **inventory by the coding agent**, not a verification: the test files are those whose `mark.req` ids lead, through the `Parent:` lines of the node requirements, to the FR/NFR of the row (`tools/tc_mia_inventory.py`). It says which tests exist near each root check, not that each row's scenario is met by them. The root Verify (and the owner) decide that.

Kinds: **A** a root-level test written for the row; **B** the parts of the scenario are held by node and integration tests, no single system test; **C** stage 4 (eval, benchmark, statistical), decided on the pinned model by the owner's suites; **D** out of G-V1 or after the field test.

| Check | Requirements | Stage | Kind | Closest tests (requirement chain) or reason |
|---|---|---|---|---|
| TC-MIA-001 | FR-1, FR-2, NFR-1 | 3 | B | api_events, character_integration, character_requests, character_stack, chat-page, chat_backend, chat_mock_server, chat_regenerate_speak ... (14 files) |
| TC-MIA-002 | FR-9, FR-10, FR-17 | 4 | C | eval on the holdout with the pinned model: `eval_decide.py` against the baseline, Verify only; the holdout is the owner's |
| TC-MIA-003 | FR-11, FR-12, NFR-4 | 4 | C | review benchmark per tier; the review entry is out of G-V1 (REQ-RUN-013 partly, D-128/D-130) |
| TC-MIA-004 | FR-16 | 3 | B | accounts_api, accounts_wiring, author_in_records, if_202_run_workflow, if_401_run_events, run_log_node |
| TC-MIA-005 | NFR-5 | 3 | B | character_stack, chat_views_browser, check_free, database_stack, if_404_web, no-outside-requests, page_requests, tool_calls_web_log |
| TC-MIA-006 | NFR-3 | 3 | B (red-team half deferred, TD-22) | if_101_chat_api, if_402_tool_calls, if_404_web, memory_records, memory_write_skill, tool_calls, tool_calls_sandbox, tool_calls_untrusted |
| TC-MIA-007 | FR-19 | 3 | B | backup, first_account, first_account_up, missing_options, runbook, shutdown_database, up_backup, up_fresh |
| TC-MIA-008 | FR-25 | 4 | D | AC-8 comes after the field test (TD-10, D-173); persona mechanism tests stay in |
| TC-MIA-009 | FR-20, FR-10, FR-11 | 4 | C | inspection of the skill path and time stamps; the review part (VAL-002) moved to the next goal (D-134) |
| TC-MIA-010 | FR-26, FR-30, FR-7 | 3 | B | accounts_wiring, check_baselines, eval_cli, eval_platform, graph_api, graph_rules, graph_tables, if_102_storage ... (22 files) |
| TC-MIA-011 | FR-29 | 4 | C | statistical run (1000 opportunities, fixed seeds) and finding F-1 of the table (0.5 % implemented, not 1 %) |
| TC-MIA-012 | FR-28 | 2 | B | api, chat_mock_server, chat_recitation, chat_views_browser, if_101_chat_api, if_102_storage, if_302_record_tables, panels ... (10 files) |
| TC-MIA-013 | FR-3, FR-31 | 3 | B | character_integration, chat_answers, converse_behaviours, if_112_voice_player, if_204_speech, page_requests, presets_api, speech_stop ... (12 files) |
| TC-MIA-014 | FR-21, NFR-6, CON-4, CON-5 | 3 | B | accounts, accounts_api, accounts_wiring, api_sessions, author_in_records, character_requests, chat_mock_server, chat_views_browser ... (17 files) |
| TC-MIA-015 | NFR-8, CON-7, FR-5, CON-6 | 3 | B (NFR-8 not met in the product, deferred, TD-21) | accounts_api, accounts_wiring, api_events, api_storage_imports, author_in_records, backup, chat_mock_server, chat_views_browser ... (18 files) |
| TC-MIA-016 | FR-22 | 3 | D | FR-22 and the Graph app N-5 are out of G-V1 (D-177); N-0 step_05 stays a skip |
| TC-MIA-017 | FR-24, FR-32, FR-2, FR-23, FR-5 | 3 | B | accounts_api, accounts_wiring, api_events, author_in_records, character_integration, character_requests, chat_mock_server, chat_mood_wiring ... (21 files) |
| TC-MIA-018 | FR-27 | 3 | B | chat_answers, chat_behaviour, chat_mock_server, chat_views_browser, if_101_chat_api, if_201_chat_turn, if_302_record_tables, mood_score ... (9 files) |
| TC-MIA-019 | NFR-7, CON-2 | 4 | C | benchmarks BM-MIA-001/-002 on the reference hardware; the 10 s part is out (REQ-RUN-009 partly, D-128) |
| TC-MIA-020 | CON-1, CON-3, CON-6 | 2 | A | new `tests/test_system_inspection.py` (chat page without build step, login notice) next to `tools/check_free.py` (licence, paid packages, web log), TC-API-011, TC-CHV-013, TC-API-010 |
| TC-MIA-021 | FR-4 | 3 | B | chat-page, chat_mock_server, chat_views_browser, if_101_chat_api, page-wiring, web_app_wiring |
| TC-MIA-022 | NFR-2, FR-17, FR-18 | 4 | C | measurement over the lookup suites; the AC-22 measurement is out (REQ-RUN-005 partly, D-128) |
| TC-MIA-023 | FR-8, FR-6, FR-10 | 3 | B | chat_tasks, extension_loader, if_101_chat_api, if_103_model_server, if_105_evaluation_access, review_chat, runner_internet_by_command, runner_model_server ... (12 files) |
| TC-MIA-024 | FR-14 | 4 | C | memory test set against today's summary-based dreaming; set when FR-14 is planned (later, Should) |
| TC-MIA-025 | FR-15 | 4 | C | behaviour suite with the detectors against the recorded precision and recall |
| TC-MIA-026 | FR-13 | 4 | D | FR-13 is off by default and REQ-WFM-022 is out of G-V1 (D-173); the retro-discovery cases are the owner's |
| TC-MIA-027 | FR-7 | 2 | B | accounts_wiring, graph_api, graph_rules, if_102_storage, if_104_graph_api, if_203_workflow_library, if_301_graph_tables, if_302_record_tables ... (15 files) |
| TC-MIA-028 | FR-33 | 4 | C | estimate against measured time on recorded lookup runs (factor 3); needs the recorded runs |
| TC-MIA-029 | NFR-9 | 3 | B | character_stack, compose_stack, container_alone, container_alone_step, database_stack, delivery_on_stack, frontend_delivery, python_version ... (9 files) |

Count: A 1, B 16, C 9, D 3 (TC-MIA-016 moved to D by D-177).

Not yet decided by anyone: the C rows need approved criteria, holdouts and recorded baselines (`specs/mia/eval-spec.md` and `specs/number-gate/eval-spec.md` exist as drafts with the pins MP-light and MP-full; they cover TC-MIA-002, -003, -019 and -022 in part and say nothing on -011, -024, -025, -028); the B rows need a root Verify that reads their scenario against the node evidence. N-0 step_05 (FR-22, TC-MIA-016) waits for N-5 and FB-02.
