"""
TC-RUN-001 (REQ-RUN-001): a task that reaches the internet (a web tool or the safety reads_web) starts only by a command: started by a chat message the
runner refuses it before any step runs; a skill that reaches the internet may not declare triggers (phrases that would start it from a message); no shipped
skill does. The web tool is a fake that records its calls.
Run with: python tests/test_runner_internet_by_command.py
"""

import glob
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                               # noqa: E402
from pipeline import PipelineError, Runner, Tool, reaches_internet, validate_pipeline  # noqa: E402
from skill_store import parse_skill                                    # noqa: E402

WEB_SKILL = """---
name: webby
version: 1
description: reads the web
tools: [web_search]
budget: {steps: 5, seconds: 60, search_calls: 3}
pipeline: webby
---
"""
TALK_SKILL = """---
name: talky
version: 1
description: no tools
tools: []
budget: {steps: 5, seconds: 60}
pipeline: talky
---
"""
WEB_GRAPH = {"name": "webby", "version": 1, "result": "found", "nodes": [{"id": "s", "kind": "tool", "tool": "web_search", "args": {"query": "$input.text"}, "output": "found"}]}
TALK_GRAPH = {"name": "talky", "version": 1, "result": "said", "nodes": [{"id": "c", "kind": "code", "function": "say", "args": {"text": "$input.text"}, "output": "said"}]}


class Web:
    def __init__(self):
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        return {"results": []}


def runner(web):
    return Runner(tools={"web_search": Tool(web.search, "search_calls")}, functions={"say": lambda text: "ok " + text})


class InternetByCommandTests(unittest.TestCase):

    @mark.req("REQ-RUN-001")
    def test_a_chat_message_starts_no_internet_task(self):
        """TC-RUN-001: a chat message starting an internet task is refused.

        Example: WEB_SKILL + message -> PipelineError with "command"
        """
        # Given: a web skill and a fake web backend
        web = Web()
        # When: the run is started with started_by="message"
        with self.assertRaises(PipelineError) as caught:
            runner(web).run(parse_skill(WEB_SKILL, "webby.md"), WEB_GRAPH, {"text": "tower height"}, started_by="message")
        # Then: the error contains "command" and no query was recorded
        self.assertIn("command", str(caught.exception))
        self.assertEqual(web.queries, [])

    @mark.req("REQ-RUN-001")
    def test_a_command_starts_the_internet_task(self):
        """TC-RUN-001: a command starts the internet task.

        Example: WEB_SKILL + command -> status "done" and query recorded
        """
        # Given: a web skill and a fake web backend
        web = Web()
        # When: the run is started with started_by="command"
        result = runner(web).run(parse_skill(WEB_SKILL, "webby.md"), WEB_GRAPH, {"text": "tower height"}, started_by="command")
        # Then: the run succeeds and the query is recorded
        self.assertEqual(result.status, "done")
        self.assertEqual(web.queries, ["tower height"])

    @mark.req("REQ-RUN-001")
    def test_a_chat_message_runs_a_task_without_internet(self):
        """TC-RUN-001: a chat message can run a task that does not reach the internet.

        Example: TALK_SKILL + message -> status "done", answer "ok hi"
        """
        # Given: a non-internet skill
        result = runner(Web()).run(parse_skill(TALK_SKILL, "talky.md"), TALK_GRAPH, {"text": "hi"}, started_by="message")
        # Then: the run succeeds
        self.assertEqual((result.status, result.answer), ("done", "ok hi"))

    @mark.req("REQ-RUN-001")
    def test_the_safety_reads_web_counts_as_internet(self):
        """TC-RUN-001: max_safety.reads_web counts as internet.

        Example: TALK_SKILL + max_safety.reads_web -> reaches_internet is True
        """
        # Given: a skill with max_safety.reads_web set to True
        skill = dict(parse_skill(TALK_SKILL, "talky.md"), max_safety={"reads_web": True})
        # Then: it is detected as internet, while the base skill is not
        self.assertTrue(reaches_internet(skill))
        self.assertFalse(reaches_internet(parse_skill(TALK_SKILL, "talky.md")))
        # And a message start still fails
        with self.assertRaises(PipelineError):
            runner(Web()).run(skill, TALK_GRAPH, {"text": "hi"}, started_by="message")

    @mark.req("REQ-RUN-001")
    def test_an_internet_skill_may_not_declare_triggers(self):
        """TC-RUN-001: an internet skill with triggers is rejected by validation.

        Example: WEB_SKILL + triggers -> validation error containing "triggers"
        """
        # Given: a skill with triggers
        skill = dict(parse_skill(WEB_SKILL, "webby.md"), triggers=["how high is"])
        # Then: validation reports a problem with "triggers"
        problems = validate_pipeline(WEB_GRAPH, tools={"web_search": Tool(Web().search, "search_calls")}, functions={}, skill=skill)
        self.assertTrue(any("triggers" in p for p in problems))

    @mark.req("REQ-RUN-001")
    def test_no_shipped_internet_skill_declares_triggers(self):
        """TC-RUN-001: no shipped internet skill declares triggers.

        Example: scan all skills -> no internet skill has a non-empty triggers list
        """
        # Given: the set of all shipped skills
        shipped = {}
        for path in sorted(glob.glob(os.path.join(REPO, "skills", "*.md"))):
            with open(path, encoding="utf-8") as fp:
                shipped[os.path.basename(path)] = parse_skill(fp.read(), os.path.basename(path))
        # Then: research.md is an internet skill and no internet skill has triggers
        internet = [name for name, s in shipped.items() if reaches_internet(s)]
        self.assertIn("research.md", internet)
        self.assertEqual([name for name in internet if shipped[name]["triggers"]], [])


if __name__ == "__main__":
    unittest.main()
