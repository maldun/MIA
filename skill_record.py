"""Skill record and the skill catalog (N-2.3, G-V2.MODEL T-02): STUB, written in Plan step 4 so the red tests import.

Real behaviour comes with plan task T-02 (REQ-WFM-040 to 042). The tests in tests/acceptance/test_graph_model.py fix this interface:
- SkillRecords(tables).store(record) -> StoreResult(stored, version, named); read(skill_id, version=None) -> the stored record dict.
- SkillCatalog(records, legacy).list() -> [{"id", "command"}, ...]; start(skill_id) -> the ID of the workflow graph the run is of.
  `legacy` = {"skill_files": {id: command}, "manifests": {id: command}, "pipelines": {id: command}}: the old forms of a skill.
"""

from collections import namedtuple

StoreResult = namedtuple("StoreResult", "stored version named")


class SkillRecords:
    def __init__(self, tables):
        self.tables = tables

    def store(self, record):
        return StoreResult(False, None, [])

    def read(self, skill_id, version=None):
        return {}


class SkillCatalog:
    def __init__(self, records, legacy=None):
        self.records = records
        self.legacy = legacy or {}

    def list(self):
        return []

    def start(self, skill_id):
        return None
