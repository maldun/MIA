"""Scenario of N-2.4 (Workflow execution): a lookup with sources through the run log, the tools and the runner (protected).
Code checks come before the model; every tool call is counted against its budget and labelled with its trust class; the log removes secrets,
keeps the order and gives the step-by-step account; the runner ends a run that is too big before it starts. Step 0 runs it on the mocks; steps 1 to 3
swap in the Run log (N-2.4.3), the Tools and sandbox (N-2.4.2) and the Pipeline runner (N-2.4.1). The fake model server stands in for the model."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "helpers", "mocks"))
from errors import ModelServerError, ServiceError  # noqa: E402

MARKS = {0: [], 1: ["REQ-LOG-002", "REQ-LOG-003"], 2: ["REQ-TLS-001", "REQ-TLS-008"], 3: ["REQ-WFX-019", "REQ-WFX-021"]}
RUN = {"id": "r-tools", "limits": {"web_search": 1}}


def code_of(call):
    try:
        call()
    except (ServiceError, ModelServerError) as err:
        return err.code
    raise AssertionError("no error raised")


def run(p, t):
    log, tools, model, runner = p["IF-401"], p["IF-402"], p["IF-103"], p["IF-202"]

    # the log: secrets are removed, the order is kept, the account is a rendering of the events
    log.emit("r1", "run_start", {"workflow": "lookup", "api_key": "abc"}, "anna", plain="Starting the lookup.")
    log.emit("r1", "query_issued", {"query": "height of the tower"}, "anna", actor="search", plain="Asked the web for the height.")
    log.emit("r1", "run_end", {"status": "done"}, "anna")
    t.assertEqual(log.events("r1")[0]["payload"]["api_key"], "[removed]")
    t.assertEqual(log.check_order("r1"), [])
    t.assertEqual([a["plain"] for a in log.account("r1")], ["Starting the lookup.", "Asked the web for the height."])

    # code checks come first: the claim is compared with the evidence before any model call
    check = tools.call(RUN, "number_check", {"claim": "The tower is 330 m high.", "evidence": ["The tower is 330 m high."]})
    t.assertEqual((check["output"]["status"], check["trust"]), ("pass", "code"))
    t.assertEqual(tools.call(RUN, "number_check", {"claim": "The tower is 400 m high.", "evidence": ["330 m"]})["output"]["status"], "fail")
    t.assertEqual(model.calls if hasattr(model, "calls") else [], [])

    # the web is data with a label; the second search is over the budget and is refused with the budget named
    hits = tools.call(RUN, "web_search", {"query": "height of the tower"})
    t.assertEqual(hits["trust"], "web")
    passages = tools.call(RUN, "fetch_passages", {"url": hits["output"][0]["url"], "question": "height"})["output"]["passages"]
    t.assertTrue(tools.call(RUN, "quote_in_source", {"quote": passages[0]["quote"], "source_text": "The tower is 330 m high. It was finished in 1889."})["output"]["status"] == "pass")
    t.assertEqual(code_of(lambda: tools.call(RUN, "web_search", {"query": "again"})), "budget")

    # the model judges what the checks leave open, with a structured answer
    if hasattr(model, "replies"):                      # the mock is scripted; the real server answers by itself
        model.replies.append('{"verdict": "supported"}')
    answer = model.chat([{"role": "user", "content": "Is the claim supported?"}], schema={"required": ["verdict"]})
    t.assertIn("verdict", answer["message"])

    # the runner: a run under budget is done and framed by run_start and run_end; one over budget is refused before any work
    done = runner.run("lookup", 1, {"question": "q"}, {"calls": 15}, "anna")
    t.assertEqual((done["status"], done["events"][0]["type"], done["events"][-1]["type"]), ("done", "run_start", "run_end"))
    refused = runner.run("lookup", 1, {"question": "q"}, {"calls": 1}, "anna")
    t.assertEqual((refused["status"], refused["missing"], refused["cost"]["calls"]), ("refused", ["calls"], 0))
    t.assertEqual(code_of(lambda: runner.run("nothing", 1, {}, {}, "anna")), "unknown_workflow")
