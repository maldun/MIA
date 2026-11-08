"""Skill record and the skill catalog (N-2.3, G-V2.MODEL T-02; REQ-WFM-040 to 042).

A skill record names the command, the workflow graph and the context graph of a skill. A record wins over the old forms of a skill
(skill file, extension manifest, pipeline reference); skills without a record are listed from the old forms unchanged.
"""

from collections import namedtuple

StoreResult = namedtuple("StoreResult", "stored version named")

SKILLS = "skills"
# The tables only know one ID at a time, so the IDs of all skills are kept in one index record.
INDEX = ("skill_index", "all")


class SkillRecords:
    def __init__(self, tables):
        self.tables = tables

    def ids(self):
        if not self.tables.versions(*INDEX):
            return []
        return list(self.tables.get(*INDEX)["ids"])

    def store(self, record):
        skill_id = record["id"]
        # Another skill with the same command refuses the record; a new version of the same skill does not count.
        named = [other for other in self.ids() if other != skill_id and self.read(other)["command"] == record["command"]]
        if named:
            return StoreResult(False, None, named)
        version = self.tables.put(SKILLS, skill_id, record)
        if skill_id not in self.ids():
            self.tables.put(*INDEX, {"ids": self.ids() + [skill_id]})
        return StoreResult(True, version, [])

    def read(self, skill_id, version=None):
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
