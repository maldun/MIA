"""Fakes and a small lab for the acceptance tests of the number gate (no Ollama, no network).

Scripted           a model that answers from a function and remembers every prompt and every option it was called with
gate_run           runs the skill verify_claim with a given pipeline over a Scripted model and returns (result, model)
vote, points       the replies of the judge and of an argue step
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core import Core                                   # noqa: E402
from library import Library                             # noqa: E402
from pipeline import PipelineError                      # noqa: E402

GATE = "verify.number_gate@1"


class Scripted:
    """chat(messages, schema, model, profile, options) like the real adapter; `answer(prompt, n)` returns a dict or a string"""

    def __init__(self, answer):
        self.answer, self.prompts, self.options = answer, [], []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        prompt = messages[-1]["content"]
        self.prompts.append(prompt)
        self.options.append(options)
        reply = self.answer(prompt, len(self.prompts))
        return reply if isinstance(reply, str) else json.dumps(reply)


def vote(word, reason="because the evidence says so", confidence=0.8):
    return {"verdict": word, "reason": reason, "confidence": confidence}


def points(*texts):
    return {"points": list(texts) or ["a point"]}


def cops_answer(verdict="supported"):
    """argue for, argue against and judge, told apart by the text of the prompt as in the existing tests of the styles"""
    def answer(prompt, n):
        if "Your side: for" in prompt:
            return points("PRO-POINT")
        if "Your side: against" in prompt:
            return points("CON-POINT")
        return vote(verdict)
    return answer


class Failed:
    """what gate_run returns when the pipeline cannot even be built (it is not in the library yet): the tests then fail on the assertion that the run is done"""
    status, answer, events = "error", None, []

    def __init__(self, error):
        self.error = error


def gate_run(answer, claim, evidence, pipeline=GATE, **inputs):
    """one claim through the gate; the skill verify_claim is read from the repository, the pipeline from its library"""
    folder = tempfile.mkdtemp()
    model = Scripted(answer)
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), folder, model=model)
    try:
        result = core.run("verify_claim", dict({"claim": claim, "evidence": evidence}, **inputs), pipeline=pipeline)
    except PipelineError as exc:
        return Failed(str(exc)), model
    return result, model


def events_of(result, type_):
    return [e for e in result.events if e.get("kind") == "event" and e.get("type") == type_]
