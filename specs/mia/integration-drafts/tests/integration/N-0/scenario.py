"""Scenario of N-0 (MIA): the example workflow lookup from the chat to the stored record, on the interfaces (protected).
The thinnest end-to-end path (D-50): a user asks, the answer streams, the lookup runs under a budget, the evaluation harness reaches the same workflow
with a pinned model, the shared history is stored. Step 0 runs it on the mocks; the later steps swap in the real nodes in the order of decomposition.yaml."""
QUESTION = "What is the boiling point of water at sea level?"
LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"},
                    {"id": "judge", "kind": "process"}, {"id": "verdict", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}, {"from": "hits", "to": "judge"}, {"from": "judge", "to": "verdict"}]}
OPTIONS = {"model_pin": "MP-light", "seed": 7, "temperature": 0, "budget": {"calls": 15}}

# requirements decided by the steps (step 0 decides none: it only proves the wiring)
MARKS = {0: [], 1: ["NFR-8"], 2: ["FR-16"], 3: ["FR-1"], 4: ["FR-1", "FR-9", "FR-21"], 5: ["FR-22"]}


def run(p, t):
    api, library, runner, storage, evaluation = p["IF-101"], p["IF-203"], p["IF-202"], p["IF-102"], p["IF-105"]

    # the example workflow is library data, promoted only with a specification and a benchmark
    library.save("workflows", "lookup", LOOKUP, "owner")
    t.assertEqual(library.read("workflows", "lookup")["status"], "draft")
    library.attach("lookup", "specification", {"text": "answer with a source or say unknown"})
    library.attach("lookup", "benchmark", {"suite": "lookup"})
    t.assertEqual(library.set_status("lookup", "tested", "owner"), {"status": "tested"})

    # chat: two users, one asks, both see the sender and the streamed answer
    anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
    api.connect(anna)
    api.connect(ben)
    api.send(anna, QUESTION)
    api.settle()
    events = [e["event"] for e in api.events(ben)]
    t.assertEqual(events[events.index("chat_message")], "chat_message")
    t.assertIn("chat_done", events)
    history = api.history(anna)
    t.assertEqual([(m["role"], m["sender"]) for m in history[-2:]], [("user", "anna"), ("assistant", "MIA")])

    # the lookup runs under a budget; every event carries the run id and the account
    result = runner.run("lookup", 1, {"question": QUESTION}, {"calls": 15}, "anna")
    t.assertEqual(result["status"], "done")
    t.assertEqual((result["events"][0]["type"], result["events"][-1]["type"]), ("run_start", "run_end"))
    t.assertTrue(all(e["run_id"] == result["run_id"] and e["user"] == "anna" for e in result["events"]))

    # the shared history is stored through the one door, with author and version
    answer = history[-1]
    t.assertEqual(storage.put("history", answer["id"], {"role": answer["role"], "sender": answer["sender"], "text": answer["text"]}, "anna"), {"version": 1})
    t.assertEqual(storage.get("history", answer["id"])["doc"]["sender"], "MIA")

    run_record = {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}
    t.assertEqual(storage.put("runs", result["run_id"], run_record, "anna"), {"version": 1})
    t.assertEqual(storage.get("runs", result["run_id"])["doc"]["model_pin"], "MP-light")

    # the evaluation harness reaches the same workflow with a pinned model, a seed and a temperature
    first = evaluation.run_case("lookup", 1, {"question": QUESTION}, OPTIONS)
    again = evaluation.run_case("lookup", 1, {"question": QUESTION}, OPTIONS)
    t.assertEqual(first["status"], "done")
    t.assertEqual(first["events"][0]["options"], {"model_pin": "MP-light", "seed": 7, "temperature": 0})
    t.assertEqual(first["outputs"], again["outputs"])
