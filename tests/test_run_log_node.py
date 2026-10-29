"""
Acceptance checks of the Run log (N-2.4.3) on recorded lookup runs over the recorded web of the research suite, with a scripted model and no network:
TC-LOG-003 (REQ-LOG-003: a recorded run is replayed offline with an identical result) and TC-LOG-004 (REQ-LOG-004: every statement of an answer links to the query that found its source).
The runs come from `Lab` of tests/test_run_explain.py. Run: python tests/test_run_log_node.py
"""
import copy
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import context_graph as CG                              # noqa: E402
import reproduce as RP                                  # noqa: E402
from markers import mark                                # noqa: E402
from test_run_explain import Lab                        # noqa: E402


def statements(graph):
    """the statements of an answer: its claims and the sentences of its draft"""
    return graph.data("claim") + graph.data("draft")


def queries_behind(graph, node_id):
    """the query nodes that lie on the way back from `node_id` to the question"""
    reached = {node_id}
    for node, _process, used in graph.provenance(node_id):
        reached.add(node)
        reached.update(used)
    return [n for n in reached if graph.nodes[n]["type"] == "query"]


class RunLogOnRecordedRuns(unittest.TestCase):
    def setUp(self):
        """Given a lab with a log folder and a store for the recorded runs"""
        self.lab = Lab()
        self.addCleanup(self.lab.close)

    @mark.req("REQ-LOG-004")
    def test_every_statement_of_a_lookup_answer_links_to_a_query(self):
        """TC-LOG-004: on a recorded lookup run 100 % of the statements link to the query that found their source.
        Example: the baseline lookup of the Rivertown Bridge gives one claim and one draft sentence, and both lead back to the query "Rivertown Bridge ..."."""
        # Given a baseline lookup and a decomposed lookup with two sub-questions
        for record in (self.lab.baseline("reader"), self.lab.decomposed()):
            # When the graph is rebuilt from the logged events
            graph = CG.replay_run(record)
            found = statements(graph)
            linked = [s for s in found if queries_behind(graph, s["id"])]
            # Then there are statements, and every one of them is linked
            self.assertGreaterEqual(len(found), 2, record["pipeline"])
            self.assertEqual(len(linked), len(found), "%s: %d of %d statements link to a query" % (record["pipeline"], len(linked), len(found)))

    @mark.req("REQ-LOG-004")
    def test_the_check_can_fail_a_log_without_its_queries_links_nothing(self):
        """TC-LOG-004 (the other side): when the query events are missing from the log, the statements no longer link to a query, so the check above is not empty.
        Example: the baseline lookup with its `query_issued` events removed: 0 of 2 statements link."""
        # Given a recorded run and a copy of it without the events that issued the queries
        record = self.lab.baseline("reader")
        broken = copy.deepcopy(record)
        broken["events"] = [e for e in broken["events"] if e.get("type") != "query_issued"]
        # When both are replayed
        good, bad = CG.replay_run(record), CG.replay_run(broken)
        # Then the original links every statement and the copy links none
        self.assertTrue(all(queries_behind(good, s["id"]) for s in statements(good)))
        self.assertFalse(any(queries_behind(bad, s["id"]) for s in statements(bad)))

    @mark.req("REQ-LOG-003")
    def test_a_recorded_run_is_replayed_offline_with_an_identical_result(self):
        """TC-LOG-003: the replay of a recorded run needs no network and no model, and gives the same graph and the same status.
        Example: the baseline lookup is replayed from its events and the store: reproduced, no differences, status done / done, 1 model call used of 1 recorded."""
        # Given a baseline lookup and a decomposed lookup, recorded
        for record in (self.lab.baseline("reader"), self.lab.decomposed()):
            # When each is reproduced from its events and the content store
            result = RP.reproduce(record, self.lab.store, self.lab.factory())
            # Then nothing differs and nothing diverged
            self.assertEqual((result["differences"], result["divergences"]), ([], []), record["pipeline"])
            self.assertTrue(result["reproduced"], record["pipeline"])
            self.assertEqual(result["status"], ("done", "done"))
            self.assertEqual(result["model_calls"][0], result["model_calls"][1])

    @mark.req("REQ-LOG-003")
    def test_a_changed_run_is_reported_as_a_difference_and_not_as_a_replay(self):
        """TC-LOG-003 (the other side): a run whose input was changed is not reproduced; the difference is named.
        Example: the baseline lookup with another question diverges: reproduced is False."""
        # Given a recorded run whose input question is changed after the recording
        record = self.lab.baseline("reader")
        changed = copy.deepcopy(record)
        changed["input"] = dict(changed["input"], question="Who designed the Rivertown Bridge?") if isinstance(changed.get("input"), dict) else "Who designed the Rivertown Bridge?"
        # When it is reproduced from the events of the original
        result = RP.reproduce(changed, self.lab.store, self.lab.factory())
        # Then it is not a replay
        self.assertFalse(result["reproduced"])


if __name__ == "__main__":
    unittest.main()
