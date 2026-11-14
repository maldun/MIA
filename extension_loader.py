"""
Skills as extensions (REQ-WFM-039): a skill that runs as a task is a folder `extensions/<id>/` with a `manifest.json` and an entry module. The loader reads every manifest, calls the
entry's function with the services of the application and registers the task; the chat service, the web application and the page need no change for a new skill. id = folder name =
command. An extension that is broken, or whose id is already taken, is skipped and named in the list of problems; the others still load.

manifest.json: {"id", "text", "argument", "example", "entry": "module:function", "aliases": [], "needs": [], "phases": [], "options": [{"name", "kind", "default", "text"}], "version"}
  needs: what the core hands to the run function besides the question (see task_registry.Task): ask, options, monitor, files, reports
  entry: the function is called as function(services) and returns run(argument, on_delta, on_emotion, should_stop, **what it needs); an optional register(services) of the same
         module is called afterwards (a failure there is a problem, the task stays)
"""
import importlib
import json
import os

try:
    from .skill_record import command_problem, normal_command
    from .task_registry import Option, Task
except ImportError:  # used as plain script / in tests
    from skill_record import command_problem, normal_command
    from task_registry import Option, Task

NEEDS = ("ask", "options", "monitor", "files", "reports")
REQUIRED = ("id", "text", "argument", "example", "entry")


def read_manifest(folder):
    """the manifest of the extension in `folder`, checked; ValueError names the folder and what is wrong"""
    name = os.path.basename(os.path.normpath(folder))
    try:
        with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as handle:
            doc = json.load(handle)
    except ValueError as exc:
        raise ValueError("%s: manifest.json is not valid json (%s)" % (name, exc))
    missing = [key for key in REQUIRED if not doc.get(key)]
    if missing:
        raise ValueError("%s: the manifest lacks %s" % (name, ", ".join(missing)))
    if doc["id"] != name:
        raise ValueError("%s: the id %r of the manifest is not the name of the folder (id = folder = command)" % (name, doc["id"]))
    unknown = [n for n in doc.get("needs", []) if n not in NEEDS]
    if unknown:
        raise ValueError("%s: unknown need %s (known: %s)" % (name, ", ".join(unknown), ", ".join(NEEDS)))
    phases = doc.get("phases", [])
    if not isinstance(phases, list) or not all(isinstance(n, str) and n for n in phases):
        raise ValueError("%s: phases must be a list of names" % name)
    if ":" not in doc["entry"]:
        raise ValueError("%s: entry must be module:function" % name)
    return doc


def task_from_manifest(doc, run):
    options = [Option(o["name"], o["kind"], o.get("default"), o.get("text", "")) for o in doc.get("options", [])]
    return Task(doc["id"], run, doc["text"], doc["argument"], doc["example"], options=options, aliases=doc.get("aliases", []), needs=doc.get("needs", []), version=str(doc.get("version", "1")), phases=doc.get("phases", []))


def load_extensions(package, folder, registry, services, catalog=None):
    """registers every extension of `folder` (the importable package `package`) in `registry`; returns the problems as plain texts.
    With a `catalog` (skill_record.SkillCatalog) a skill that has a record is registered under the command of the record and its task carries the record's workflow graph ID
    (REQ-WFM-041); a skill without a record is registered as the manifest says. A record without an extension is not made runnable here."""
    problems = []
    try:
        names = sorted(n for n in os.listdir(folder) if os.path.isfile(os.path.join(folder, n, "manifest.json")))
    except FileNotFoundError:
        return ["the extensions folder %s does not exist" % folder]
    # One lookup per skill: its record (graph ID and command) or None. A catalog that fails for a skill (storage down) does not stop the loader: the skill is
    # registered as the manifest says and the failure is a problem; the other skills are not affected.
    records = {}
    if catalog is not None:
        for name in names:
            try:
                graph_id = catalog.start(name)
                records[name] = None if graph_id is None else (graph_id, catalog.records.read(name)["command"])
            except Exception as exc:
                records[name] = None
                problems.append("%s: the record could not be looked up, the skill is registered as the manifest says: %s" % (name, exc))
    # The record store does not know skills that exist only as manifest, nor the aliases of a manifest, so the loader refuses a record command that is the
    # folder name of a skill without a record or an alias of ANOTHER skill (REQ-WFM-042); a skill never clashes with its own alias (F-17). Names are compared
    # in the form the registry looks them up; `taken` maps such a name to the skills that hold it, with the reason for the problem text.
    taken = {}
    for name in names:
        if records.get(name) is None:
            taken.setdefault(normal_command(name), []).append((name, "the name of the skill %s" % name))
        try:
            for alias in read_manifest(os.path.join(folder, name)).get("aliases", []):
                taken.setdefault(normal_command(alias), []).append((name, "an alias of the skill %s" % name))
        except Exception:       # a broken manifest is a problem of its own below
            pass
    for name in names:
        try:
            doc = read_manifest(os.path.join(folder, name))
            module, _, function = doc["entry"].partition(":")
            loaded = importlib.import_module("%s.%s.%s" % (package, name, module))
            task = task_from_manifest(doc, getattr(loaded, function)(services))
            if records.get(name) is not None:
                graph_id, command = records[name]
                problem = command_problem(command)      # records are data from outside: a command that cannot be registered skips the skill (F-03)
                if problem is None:
                    clash = [why for holder, why in taken.get(normal_command(command), []) if holder != name]
                    if clash:
                        problem = "the command %r is already %s" % (command, " and ".join(clash))
                if problem is not None:
                    raise ValueError("%s: the record is not used: %s" % (name, problem))
                task.id, task.workflow_graph_id = normal_command(command), graph_id
            registry.register(task)
        except Exception as exc:
            problems.append(str(exc) if str(exc).startswith(name + ":") else "%s: %s" % (name, exc))
            continue
        hook = getattr(loaded, "register", None)         # optional: the extension puts something of its own where the core keeps it (the review: its entry in the workflow library)
        if hook is not None:
            try:
                hook(services)
            except Exception as exc:
                problems.append("%s: register failed: %s" % (name, exc))
    return problems
