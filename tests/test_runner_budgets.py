"""
TC-RUN-008 (REQ-RUN-008): the runner counts model calls and tokens against the budget of the skill, as it counts steps and seconds, ends a run that
exceeds one of the four with what it has, names the exceeded budget and returns what the run spent. The model is a fake.
Run with: python tests/test_runner_budgets.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from pipeline import Runner                       # noqa: E402
from pipeline_model import OllamaModel            # noqa: E402
from skill_store import parse_skill               # noqa: E402

SKILL = """---
name: budgeted
version: 1
description: three model steps
budget: {steps: 20, seconds: 60}
model: {profile: light}
pipeline: budgeted
---
## prompts
### ask
Say something about {{input.text}}.
"""
GRAPH = {"name": "budgeted", "version": 1, "result": "c",
         "nodes": [{"id": "a", "kind": "model", "prompt": "ask", "output": "a"},
                   {"id": "b", "kind": "model", "prompt": "ask", "output": "b"},
                   {"id": "c", "kind": "model", "prompt": "ask", "output": "c"}]}


class TextModel:
    """answers 'ok' and reports no token count, like the fakes of the other tests"""
    def __init__(self):
        self.calls = 0

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls += 1
        return "ok"


class CountingModel(TextModel):
    """reports the tokens of every call, like the Ollama server (prompt_eval_count + eval_count)"""
    def __init__(self, tokens):
        super().__init__()
        self.tokens = tokens

    def chat_with_usage(self, messages, schema=None, model=None, profile=None, options=None):
        return self.chat(messages, schema, model, profile, options), {"tokens_in": self.tokens - 1, "tokens_out": 1}


def run(model, **budget):
    skill = parse_skill(SKILL, "budgeted.md")
    skill["budget"].update(budget)
    return Runner(model=model).run(skill, GRAPH, {"text": "towers"})


class RunnerBudgetTests(unittest.TestCase):
    def test_model_calls_over_the_budget_end_the_run_before_the_next_call(self):
        """TC-RUN-008 (calls): with a budget of 2 model calls the third step is not asked; the run ends with budget, names calls and keeps the outputs.
        Example: three model steps, budget {calls: 2} -> 2 calls, status budget, missing ["calls"], output a and b."""
        # Given a pipeline of three model steps and a budget of two calls
        model = TextModel()
        # When it runs
        result = run(model, calls=2)
        # Then the model was asked twice and the run says which budget ended it
        self.assertEqual(model.calls, 2)
        self.assertEqual((result.status, result.missing), ("budget", ["calls"]))
        self.assertEqual((result.context["a"], result.context["b"]), ("ok", "ok"))
        self.assertEqual(result.cost["calls"], 2)

    def test_tokens_reported_by_the_model_end_the_run_when_they_pass_the_budget(self):
        """TC-RUN-008 (tokens): 60 tokens a call and a budget of 100 tokens: the second call passes the budget, the third is not asked.
        Example: tokens 60 + 60 = 120 > 100 -> status budget, missing ["tokens"], cost tokens 120."""
        # Given a model that reports 60 tokens a call
        model = CountingModel(60)
        # When the run has a budget of 100 tokens
        result = run(model, tokens=100)
        # Then it stops after the call that passed the budget
        self.assertEqual(model.calls, 2)
        self.assertEqual((result.status, result.missing), ("budget", ["tokens"]))
        self.assertEqual(result.cost["tokens"], 120)

    def test_a_model_without_a_count_is_estimated_by_characters(self):
        """TC-RUN-008 (estimate): a model that reports no count is estimated at one token for four characters of prompt and answer, rounded up.
        Example: prompt 'Say something about towers.' (27 characters) + 'ok' (2) = 29 characters -> 8 tokens a call, 24 for three."""
        result = run(TextModel())
        self.assertEqual(result.status, "done")
        self.assertEqual(result.cost["tokens"], 24)

    def test_a_run_within_its_budgets_reports_what_it_spent(self):
        """TC-RUN-008 (cost): a done run returns its cost with the four budget names and no missing budget.
        Example: three model steps with 10 tokens each -> steps 3, calls 3, tokens 30, missing []."""
        result = run(CountingModel(10), calls=5, tokens=1000)
        self.assertEqual((result.status, result.missing), ("done", []))
        self.assertEqual(set(result.cost), {"steps", "seconds", "calls", "tokens"})
        self.assertEqual((result.cost["steps"], result.cost["calls"], result.cost["tokens"]), (3, 3, 30))

    def test_steps_and_seconds_are_named_too(self):
        """TC-RUN-008 (steps): the budget of steps ends the run as before and is now named in missing.
        Example: budget {steps: 1} -> one step runs, status budget, missing ["steps"]."""
        result = run(TextModel(), steps=1)
        self.assertEqual((result.status, result.missing, result.cost["steps"]), ("budget", ["steps"], 1))


class OllamaUsageTests(unittest.TestCase):
    def test_the_ollama_model_reports_prompt_and_answer_tokens(self):
        """TC-RUN-008 (Ollama count): the tokens of a call are prompt_eval_count (in) and eval_count (out) of the server's reply; a reply without them gives None
        (the runner estimates). Example: prompt_eval_count 120, eval_count 30 -> tokens_in 120, tokens_out 30."""
        replies = [{"message": {"content": "ok"}, "prompt_eval_count": 120, "eval_count": 30}, {"message": {"content": "ok"}}]

        class Client:
            def chat(self, **kwargs):
                return replies.pop(0)

        model = OllamaModel(Client(), lambda profile: None, lambda: ("gemma4:12b-it-qat", {}))
        self.assertEqual(model.chat_with_usage([{"role": "user", "content": "hi"}]), ("ok", {"tokens_in": 120, "tokens_out": 30}))
        self.assertEqual(model.chat_with_usage([{"role": "user", "content": "hi"}]), ("ok", None))


if __name__ == "__main__":
    unittest.main()
