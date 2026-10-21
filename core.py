"""
The core of MIA's tasks (ui/REQUIREMENTS_CORE.md): skills (skills/*.md), the library of nodes and pipelines (library.py), the runner and the run log together.
`Core.run("research", {"text": ...})` loads the skill, takes its pipeline from the library (the highest tested or trusted version, or the one the skill pins as "id@version"),
expands it into the graph of the runner, checks that the skill may use what the pipeline needs (web access, code), runs it and logs the run with the library entries it used.
"""
try:
    from . import behaviour, checks, extraction, research, verification
    from .library import LibraryError
    from .pipeline import PipelineError, Runner, Tool, validate_pipeline
    from .run_log import RunLog
    from .skill_store import SkillStore
except ImportError:  # used as plain script / in tests
    import checks
    import extraction
    import behaviour
    import research
    import verification
    from library import LibraryError
    from pipeline import PipelineError, Runner, Tool, validate_pipeline
    from run_log import RunLog
    from skill_store import SkillStore


class Core:
    def __init__(self, skills_dir, library, runs_dir, model=None, tools=None, functions=None, rng=None, sandbox=None, broker_factory=None, environment=None):
        """sandbox: a sandbox.SandboxRouter (None = no scripts can run); broker_factory: makes a web broker per script (broker.WebBroker), None = scripts have no web"""
        self.skills = SkillStore(skills_dir)
        self.library = library
        self.run_log = RunLog(runs_dir)
        tools = dict(tools or {})
        tools.setdefault("library_select", Tool(self._select, None))
        tools.setdefault("library_describe", Tool(self._describe, None))
        self.sandbox = sandbox
        functions = {**checks.OFFLINE_FUNCTIONS, **extraction.FUNCTIONS, **behaviour.FUNCTIONS, **verification.FUNCTIONS, **research.FUNCTIONS, **checks.build_script_checks(sandbox, broker_factory), **(functions or {})}
        self.runner = Runner(model=model, tools=tools, functions=functions, run_log=self.run_log, rng=rng, sandbox=sandbox, broker_factory=broker_factory,
                             environment=environment)
        # the hard checks of the library, picked per claim (checks.CheckRunner); the web variant needs a skill that may read the web
        self.checks = checks.CheckRunner(library, lambda: self.runner.functions, lambda: list(self.runner.tools), sandbox=sandbox)
        self.runner.functions.setdefault("hard_checks_offline", lambda claim, fail_fast=True: self.checks.run(claim, include_web=False, fail_fast=fail_fast))
        self.runner.functions.setdefault("hard_checks_web", lambda claim, fail_fast=True: self.checks.run(claim, include_web=True, fail_fast=fail_fast))

    # -- the library as tools for planning steps (reading only; new entries are drafts made by people or on request) --
    def _select(self, entry_type="pipeline", tags=(), applies_to=None, max_seconds=None, task=None):
        return self.library.select(entry_type, tags=tags, applies_to=applies_to, max_seconds=max_seconds, task=task, tools=self.runner.tools,
                                   sandbox=self.sandbox is not None and self.sandbox.available)

    def _describe(self, ref, entry_type="pipeline"):
        entry = self.library.resolve(ref, entry_type, allow_draft=True)
        return {k: v for k, v in entry.items() if not k.startswith("_")}

    def graph(self, skill):
        """(graph, uses, safety) of the pipeline the skill names; raises PipelineError"""
        try:
            entry = self.library.resolve(skill["pipeline"], "pipeline")
            graph, uses, safety = self.library.expand(entry)
        except LibraryError as exc:
            raise PipelineError(str(exc))
        allowed = skill.get("max_safety") or {}
        for flag, needed in safety.items():
            if needed and not allowed.get(flag):
                raise PipelineError("the pipeline '%s' needs '%s', which the skill '%s' does not allow (max_safety)" % (skill["pipeline"], flag, skill["name"]))
        return graph, uses, safety

    def check(self, functions=None):
        """the problems of every skill with its pipeline: {skill name: [problems]} (skills without problems are left out); file errors under their path"""
        self.skills.reload()
        found = {path: [message] for path, message in self.skills.errors.items()}
        found.update({path: [message] for path, message in self.library.errors.items()})
        all_functions = {**self.runner.functions, **(functions or {})}
        for name in self.skills.names():
            skill = self.skills.skills[name]
            try:
                graph = self.graph(skill)[0]
                problems = validate_pipeline(graph, tools=self.runner.tools, functions=all_functions, skill=skill)
            except PipelineError as exc:
                problems = [str(exc)]
            if problems:
                found[name] = problems
        return found

    def run(self, task, inputs, pipeline=None, **kwargs):
        """runs the skill of the task; `pipeline` ("research.decompose@1") runs another pipeline of the library under the skill's settings"""
        skill = self.skills.get(task)
        if skill is None:
            raise PipelineError("there is no skill '%s'" % task)
        if pipeline:
            skill = dict(skill, pipeline=pipeline)
        graph = self.graph(skill)[0]
        return self.runner.run(skill, graph, inputs, task=task, **kwargs)
