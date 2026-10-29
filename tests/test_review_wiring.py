"""TC-WFM-019, -028 (A-20): the real web app has the /review task: the chat service gets the review function, the full text source reads through the web client of the app, the scholarly
search is the Scholar of the configuration, and the five review skills exist with their pipelines in the library. No network, no model. Run in the image: bash tools/run_in_image.sh tests/test_review_wiring.py"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
os.environ.update({"ANSWER_DELAY": "0.3", "EVENT_GAP": "0", "MIA_TEST": "1"})

spec = importlib.util.spec_from_file_location("chat_mock_server", os.path.join(REPO, "ui", "tools", "chat_mock_server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
w = server.w                                       # the real web_app, imported by the mock server

SKILLS = ("review_keywords", "review_abstract", "review_section", "review_full", "review_summary")


class ReviewWiring(unittest.TestCase):
    def test_the_chat_service_has_the_review_task_and_the_command_is_listed(self):
        task = w.chat_service._tasks.get("review")               # since A-23 the review is a task of the registry, with its options
        self.assertTrue(task.run.__module__.endswith("extensions.review.entry"))        # since T-11 the review is an extension
        self.assertEqual([o.name for o in task.options], ["slice", "cap_factor"])
        self.assertIn("/review ", [c["command"] for c in w.chat_service.commands()])

    def test_the_full_text_source_reads_through_the_web_client_of_the_app(self):
        self.assertEqual(w._review_full_text.get.__self__, w._web_client)

    def test_the_scholar_is_built_from_the_configuration_and_touches_no_network(self):
        self.assertGreaterEqual(len(w._scholar.clients), 1)
        self.assertTrue(hasattr(w._scholar, "search"))

    def test_the_review_workflow_is_an_entry_of_the_library_of_the_app(self):
        self.assertIn("review", w._workflow_library.list_ids("workflows"))
        self.assertEqual(w._workflow_library.read("workflows", "review")["status"], "draft")

    def test_every_review_skill_names_a_pipeline_that_the_library_resolves(self):
        library = w.core.library
        for name in SKILLS:
            with self.subTest(skill=name):
                text = open(os.path.join(REPO, "skills", name + ".md"), encoding="utf-8").read()
                ref = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("pipeline:")][0]
                self.assertEqual(library.resolve(ref, allow_draft=True)["id"], ref.split("@")[0])

if __name__ == "__main__":
    unittest.main()
