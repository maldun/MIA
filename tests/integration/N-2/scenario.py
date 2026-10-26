"""Scenario of N-2 (Backend): a shared chat turn, speech, the workflow library and the graph API behind one session (protected).
Two users share one MIA; an answer streams to both; every sentence can be spoken without markup; the library refuses a broken workflow and an
unproven promotion; the graph API works with the same session and the same refusals; a run ends in budget. Step 0 runs it on the mocks; steps 1 to 5 swap in
the Voice synthesis (N-2.5), the Workflow management (N-2.3), the Workflow execution (N-2.4), the Chat agent (N-2.2) and the API and accounts (N-2.1)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "helpers", "mocks"))
from errors import ApiError, ServiceError  # noqa: E402

LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}]}
CYCLE = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}

MARKS = {0: [], 1: ["REQ-BE-016", "REQ-BE-017"], 2: ["REQ-BE-035", "REQ-BE-036", "REQ-BE-039"], 3: ["REQ-BE-070"],
         4: ["REQ-BE-002", "REQ-BE-003", "REQ-BE-004"], 5: ["REQ-BE-001", "REQ-BE-008", "REQ-BE-012", "REQ-BE-076"]}


def err_of(call, kind=(ServiceError, ApiError)):
    try:
        call()
    except kind as err:
        return getattr(err, "status", None) or err.code, err.rule if hasattr(err, "rule") else None
    raise AssertionError("no error raised")


def run(p, t):
    speech, library, runner, turn, api, graph = p["IF-204"], p["IF-203"], p["IF-202"], p["IF-201"], p["IF-101"], p["IF-104"]

    # speech: only what is meant to be heard; a missing voice line is named
    spoken = speech.synthesize("*smiles* Hello <b>there</b>.")
    t.assertEqual((spoken["spoken_text"], spoken["format"]), ("Hello there.", "wav"))
    t.assertEqual(err_of(lambda: speech.voice_line("no-such-line"))[0], "no_line")

    # the library: a broken workflow is refused with the rule; promotion needs a specification and a benchmark
    t.assertEqual(err_of(lambda: library.save("workflows", "bad", CYCLE, "anna")), ("invalid", "cycle"))
    library.save("workflows", "lookup", LOOKUP, "anna")
    t.assertEqual(err_of(lambda: library.set_status("lookup", "trusted", "anna"))[0], "not_promotable")
    library.attach("lookup", "specification", {"text": "answer with a source"})
    library.attach("lookup", "benchmark", {"suite": "lookup"})
    t.assertEqual(library.set_status("lookup", "trusted", "anna"), {"status": "trusted"})

    # one shared MIA: a turn from anna reaches the stream that ben watches, with the sender
    seen = []
    stop = turn.subscribe(seen.append)
    ack = turn.send("anna", "hello MIA")
    turn.settle()
    stop()
    names = [e["event"] for e in seen]
    t.assertEqual((ack["position"], names[0]), (1, "chat_message"))
    t.assertIn("chat_done", names)
    t.assertEqual([(m["role"], m["sender"]) for m in turn.history()[-2:]], [("user", "anna"), ("assistant", "MIA")])
    t.assertEqual(err_of(lambda: turn.send("anna", "   "))[0], "empty_text")

    # a run ends in budget with what is missing
    refused = runner.run("lookup", 1, {"question": "q"}, {"calls": 1}, "anna")
    t.assertEqual((refused["status"], refused["missing"]), ("refused", ["calls"]))

    # the API: no session, no access; the same session works for the chat and for the graph API
    t.assertEqual(err_of(lambda: api.history("none"), ApiError)[0], 401)
    t.assertEqual(err_of(lambda: api.login("anna", "wrong"), ApiError)[0], 401)
    session = graph.login("anna", "pw-anna")
    graph.save(session, "workflows", "lookup", LOOKUP)
    t.assertEqual(err_of(lambda: graph.save(session, "workflows", "bad", CYCLE), ApiError), (422, "cycle"))
    t.assertEqual(graph.list_ids(session, "workflows"), ["lookup"])
