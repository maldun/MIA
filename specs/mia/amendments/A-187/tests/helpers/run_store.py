"""Stand-ins and data of the checks of G-V4.GRAPHAPI.RUN (TR-RUN-002, -004, -005, -006, -009; protected, changed only by an amendment).

- oracle(): the file tests/helpers/run_oracle.json, after the checks of TR-RUN-002: its commit is an ancestor of the tested code and the file is the committed one.
- INPUTS, SIX: the scripted inputs of the six skills with an equivalence suite (the same as TC-WFM-058 of G-V2).
- old_run(skill, folder) -> (RunResult, Recording): the old runner on scripted replies and scripted tool results (as the oracle was recorded).
- ThrowAwayStore: a new files store in a temporary folder with GraphModel on it, a counted read (`reads`), and `save(graph)` through CORE's save path.
- stored_run(skill, store, folder) -> (RunResult, Recording, core): the skill run by Core with `graph_store=` the counted model, on the same scripted replies.
"""
import json
import os
import shutil
import subprocess
import tempfile

from call_recording import Recording, RecordingModel, RecordingTool, ScriptedModel

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")
ORACLE = os.path.join(HERE, "run_oracle.json")

TEXT = "Quick check of the budget: 12 * 1.5 + 3 = 21, so we stay within limits."
INPUTS = {"research": {"question": "When did the Rivertown Bridge open to traffic?"},
          "plan_question": {"question": "Which is older, the Tarn Museum or the company that built the Rivertown Bridge?"},
          "verify_claim": {"claim": "The Pacific is the largest ocean on Earth.", "evidence": "", "rounds": 3, "experts": []},
          "verify_computable": {"claim": "1628.89 euros is what 1000 euros grow to at 5 percent interest per year in 10 years", "data_description": "principal, rate, years, claimed",
                                "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}},
          "extract_claims": {"text": TEXT}, "extract_claims_rules": {"text": TEXT}}
SIX = sorted(INPUTS)


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def oracle():
    """The oracle of TR-RUN-002; fails when its commit is not an ancestor of the tested code or the file differs from its committed version."""
    with open(ORACLE, encoding="utf-8") as fp:
        recorded = json.load(fp)
    commit = recorded["header"]["commit"]
    if git("merge-base", "--is-ancestor", commit, "HEAD").returncode != 0:
        raise AssertionError("the oracle's commit %s is not an ancestor of the tested code (TR-RUN-002)" % commit[:8])
    relative = os.path.relpath(ORACLE, REPO)
    if git("ls-files", "--error-unmatch", relative).returncode != 0 or git("diff", "--quiet", "HEAD", "--", relative).returncode != 0:
        raise AssertionError("the oracle file %s is not the committed one (TR-RUN-002)" % relative)
    return recorded


def scripted_tools(rec):
    return {"web_search": RecordingTool("web_search", lambda **kw: [], rec), "fetch_page": RecordingTool("fetch_page", lambda **kw: {"text": ""}, rec)}


def old_run(skill, folder):
    """the old runner (a Core without a store) on the scripted replies; returns (result, recording)"""
    from core import Core
    from library import Library
    rec = Recording()
    core = Core(SKILLS, Library(LIBRARY), folder, model=RecordingModel(ScriptedModel(), rec), tools=scripted_tools(rec))
    return core.run(skill, INPUTS[skill], started_by="command"), rec


class ThrowAwayStore:
    """TR-RUN-009: a new files store in a temporary folder, GraphModel on it (CORE's save path and the read of N-2.3), a counted read; `close()` deletes it."""

    def __init__(self):
        from graph_model import GraphModel
        from storage import Storage
        from storage_files import FileBackend
        self.folder = tempfile.mkdtemp(prefix="run-store-")
        self.model = GraphModel(Storage(FileBackend(self.folder)), "anna")
        self.reads = []
        self.planted = {}       # {graph id: change(graph) -> graph}: what the NEWEST version reads as, a defect no save path would let in (TC-RUN-047)

    def plant(self, graph_id, change):
        self.planted[graph_id] = change

    def save(self, graph):
        result = self.model.save_graph(graph)
        assert result.saved, "the graph %s was not saved: %s" % (graph.get("id"), result.rules or result.rule)
        return result.version

    def read_graph(self, graph_id, version=None):
        self.reads.append((graph_id, version))
        stored = self.model.read_graph(graph_id, version)
        return self.planted[graph_id](stored) if version is None and graph_id in self.planted else stored

    def __getattr__(self, name):        # everything else of GraphModel is passed on
        return getattr(self.model, name)

    def close(self):
        shutil.rmtree(self.folder, True)


def stored_run(skill, store, folder, inputs=None):
    """Core with `graph_store=` the counted model, on the same scripted replies; returns (result, recording, core)"""
    from core import Core
    from library import Library
    rec = Recording()
    core = Core(SKILLS, Library(LIBRARY), folder, model=RecordingModel(ScriptedModel(), rec), tools=scripted_tools(rec), graph_store=store)
    return core.run(skill, inputs or INPUTS[skill], started_by="command"), rec, core


def run_record(core, result):
    """the run log record of a run (the dict the Core wrote), found by the run id"""
    return next(r for r in core.run_log.read() if r.get("id") == result.run_id)
