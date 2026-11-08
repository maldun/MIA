"""Skill record and the skill catalog (N-2.3, G-V2.MODEL T-02; REQ-WFM-040 to 042).

A skill record names the command, the workflow graph and the context graph of a skill. A record wins over the old forms of a skill
(skill file, extension manifest, pipeline reference); skills without a record are listed from the old forms unchanged.
"""

from collections import namedtuple

try:
    from .storage import StorageError
except ImportError:  # used as plain script / in tests
    from storage import StorageError

# `named` lists the other skills of a command clash; `rule` and `detail` are those of a StorageError("invalid") of the record checks.
StoreResult = namedtuple("StoreResult", "stored version named rule detail", defaults=(None, None))

SKILLS = "skills"


def normal_command(command):
    """The form in which the loader registers a command and the task registry looks it up: no leading slash, lower case (extension_loader, TaskRegistry.parse)."""
    return str(command).lstrip("/").lower()


def command_problem(command):
    """None for a command the task registry can register and parse, else the reason in words. One optional slash, then a name without space, slash or capital letter."""
    name = command[1:] if isinstance(command, str) and command.startswith("/") else command
    if not isinstance(name, str) or not name:
        return "the command is empty"
    if any(c.isspace() for c in name) or "/" in name:
        return "the command %r has a space or a second slash" % command
    if name != name.lower():
        return "the command %r has capital letters, the task registry looks commands up in lower case" % command
    return None

# The fake tables only know one ID at a time, so the IDs of all skills are kept in one index record; the Storage layer lists them itself.
INDEX = ("skill_index", "all")


class SkillRecords:
    """`tables` is the real Storage layer (IF-102, table `skills` of IF-301 v2) or the minimal fake of the red tests (TR-MODEL-001).
    The Storage layer keeps the fields of a skill under `data` and lists the IDs itself; the caller gives the `author` of a write."""

    def __init__(self, tables, author=None):
        self.tables = tables
        self.author = author
        self.real = hasattr(tables, "ids")

    def ids(self):
        if self.real:
            return self.tables.ids(SKILLS)
        if not self.tables.versions(*INDEX):
            return []
        return list(self.tables.get(*INDEX)["ids"])

    def store(self, record):
        skill_id = record["id"]
        # Another skill with the same command refuses the record; a new version of the same skill does not count.
        # Commands are compared in the form the loader registers them, so `/Lookup` and `lookup` clash with `/lookup`.
        named = [other for other in self.ids() if other != skill_id and normal_command(self.read(other)["command"]) == normal_command(record["command"])]
        if named:
            return StoreResult(False, None, named)
        # A command the task registry cannot register would break chat parsing or register an empty ID (F-03); the rule is that of a document that breaks the schema.
        problem = command_problem(record["command"])
        if problem:
            return StoreResult(False, None, [], "schema", problem)
        if self.real:
            # A record the record checks of the Storage layer refuse is a refused result like the clash, nothing is stored; other errors raise.
            data = {key: value for key, value in record.items() if key != "id"}
            try:
                version = self.tables.put(SKILLS, skill_id, {"id": skill_id, "data": data}, self.author)["version"]
            except StorageError as refusal:
                if refusal.code != "invalid":
                    raise
                return StoreResult(False, None, [], refusal.rule, refusal.detail)
        else:
            version = self.tables.put(SKILLS, skill_id, record)
            if skill_id not in self.ids():
                self.tables.put(*INDEX, {"ids": self.ids() + [skill_id]})
        return StoreResult(True, version, [])

    def read(self, skill_id, version=None):
        if self.real:
            doc = self.tables.get(SKILLS, skill_id, version)["doc"]
            return dict(doc["data"], id=doc["id"])
        return self.tables.get(SKILLS, skill_id, version)


class SkillCatalog:
    def __init__(self, records, legacy=None):
        self.records = records
        self.legacy = legacy or {}

    def list(self):
        skills = {}
        # Old forms first, later ones win; the record wins over all of them.
        for form in ("pipelines", "manifests", "skill_files"):
            skills.update(self.legacy.get(form, {}))
        for skill_id in self.records.ids():
            skills[skill_id] = self.records.read(skill_id)["command"]
        return [{"id": skill_id, "command": command} for skill_id, command in skills.items()]

    def start(self, skill_id):
        """The ID of the workflow graph the run is of; None for a skill without a record (the old runner starts it)."""
        if skill_id not in self.records.ids():
            return None
        return self.records.read(skill_id)["workflow_graph_id"]
