"""
The core of MIA's tasks (ui/REQUIREMENTS_CORE.md): skills (skills/*.md), their pipelines (pipelines/*.json), the runner and the run log together.
`Core.run("research", {"text": ...})` loads the skill and its pipeline (changed files are reloaded), validates them, runs the pipeline and logs the run.
"""
import json
import os

try:
    from .pipeline import PipelineError, Runner, validate_pipeline
    from .run_log import RunLog
    from .skill_store import SkillStore
except ImportError:  # used as plain script / in tests
    from pipeline import PipelineError, Runner, validate_pipeline
    from run_log import RunLog
    from skill_store import SkillStore


class Core:
    def __init__(self, skills_dir, pipelines_dir, runs_dir, model=None, tools=None, functions=None, rng=None):
        self.skills = SkillStore(skills_dir)
        self.pipelines_dir = pipelines_dir
        self.run_log = RunLog(runs_dir)
        self.runner = Runner(model=model, tools=tools, functions=functions, run_log=self.run_log, rng=rng)

    def pipeline(self, name):
        path = os.path.join(self.pipelines_dir, name + ".json")
        try:
            with open(path, encoding="utf-8") as fp:
                return json.load(fp)
        except OSError:
            raise PipelineError("there is no pipeline file %s" % path)
        except ValueError as exc:
            raise PipelineError("%s is not valid JSON (%s)" % (path, exc))

    def check(self, functions=None):
        """the problems of every skill with its pipeline: {skill name: [problems]} (skills without problems are left out); file errors under their path"""
        self.skills.reload()
        found = {path: [message] for path, message in self.skills.errors.items()}
        all_functions = {**self.runner.functions, **(functions or {})}
        for name in self.skills.names():
            skill = self.skills.skills[name]
            try:
                problems = validate_pipeline(self.pipeline(skill["pipeline"]), tools=self.runner.tools, functions=all_functions, skill=skill)
            except PipelineError as exc:
                problems = [str(exc)]
            if problems:
                found[name] = problems
        return found

    def run(self, task, inputs, **kwargs):
        skill = self.skills.get(task)
        if skill is None:
            raise PipelineError("there is no skill '%s'" % task)
        return self.runner.run(skill, self.pipeline(skill["pipeline"]), inputs, task=task, **kwargs)
