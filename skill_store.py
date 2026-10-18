"""
Skill files (ui/REQUIREMENTS_CORE.md 3): one Markdown file per skill in `skills/`, YAML front matter for the settings, sections for the texts:

  ## prompts    ### <stage>   the prompt of a model node (variables as {{name}})
  ## schemas    ### <name>    a fenced ```json block with the JSON schema of a structured answer
  ## lines      ### <node id or node kind>   bullets: playful status lines (the accurate text is added by the runner)
  ## examples   ### <stage>   short examples that are appended to the prompt of the stage

SkillStore loads the folder, remembers broken files in `errors` (they do not stop MIA) and reloads files that changed (S1).
"""
import json
import os
import re

import yaml

DEFAULT_BUDGET = {"steps": 50, "seconds": 600}


class SkillError(Exception):
    pass


def parse_skill(text, path=""):
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not match:
        raise SkillError("%s: the file must start with a front matter block between --- lines" % path)
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise SkillError("%s: front matter is not valid YAML (%s)" % (path, exc))
    if not isinstance(meta, dict) or not meta.get("name") or not meta.get("pipeline"):
        raise SkillError("%s: the front matter needs 'name' and 'pipeline'" % path)
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", str(meta["name"])):
        raise SkillError("%s: the name must be lower case letters, digits and _" % path)
    sections = _sections(match.group(2))
    skill = dict(meta)
    skill["name"] = str(meta["name"])
    skill["version"] = meta.get("version", 1)
    skill["triggers"] = list(meta.get("triggers") or [])
    skill["tools"] = list(meta.get("tools") or [])
    skill["budget"] = {**DEFAULT_BUDGET, **(meta.get("budget") or {})}
    skill["model"] = meta.get("model") or {}
    skill["status_block"] = bool(meta.get("status_block", True))
    skill["prompts"] = {k: v.strip() for k, v in sections.get("prompts", {}).items()}
    skill["examples"] = {k: v.strip() for k, v in sections.get("examples", {}).items()}
    skill["lines"] = {k: _bullets(v) for k, v in sections.get("lines", {}).items()}
    skill["schemas"] = {}
    for key, block in sections.get("schemas", {}).items():
        found = re.search(r"```(?:json)?\s*\n(.*?)```", block, re.S)
        if not found:
            raise SkillError("%s: schema '%s' needs a fenced json block" % (path, key))
        try:
            skill["schemas"][key] = json.loads(found.group(1))
        except ValueError as exc:
            raise SkillError("%s: schema '%s' is not valid JSON (%s)" % (path, key, exc))
    skill["path"] = path
    return skill


def _sections(body):
    """{"prompts": {"plan": text, ...}, ...}: ## starts a section, ### a part of it (fenced blocks are skipped for headings)"""
    result, section, part, fenced = {}, None, None, False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            section, part = line[3:].strip().lower(), None
            result.setdefault(section, {})
        elif not fenced and line.startswith("### ") and section:
            part = line[4:].strip()
            result[section][part] = ""
        elif section and part:
            result[section][part] += line + "\n"
    return result


def _bullets(text):
    return [m.group(1).strip() for m in re.finditer(r"^\s*[-*]\s+(.*\S)\s*$", text, re.M)]


def load_skill(path):
    with open(path, encoding="utf-8") as fp:
        return parse_skill(fp.read(), path)


class SkillStore:
    def __init__(self, folder):
        self.folder = folder
        self.skills = {}
        self.errors = {}          # path -> message of files that could not be loaded
        self._stamps = {}
        self.reload()

    def _paths(self):
        if not os.path.isdir(self.folder):
            return []
        return sorted(os.path.join(self.folder, n) for n in os.listdir(self.folder) if n.endswith(".md"))

    def reload(self):
        """loads new and changed files, forgets removed ones; returns True when something changed"""
        paths, changed = self._paths(), False
        for path in list(self._stamps):
            if path not in paths:
                self._stamps.pop(path)
                self.errors.pop(path, None)
                for name in [n for n, s in self.skills.items() if s["path"] == path]:
                    del self.skills[name]
                changed = True
        for path in paths:
            stamp = os.stat(path).st_mtime_ns
            if self._stamps.get(path) == stamp:
                continue
            self._stamps[path] = stamp
            changed = True
            for name in [n for n, s in self.skills.items() if s["path"] == path]:
                del self.skills[name]
            try:
                skill = load_skill(path)
                self.skills[skill["name"]] = skill
                self.errors.pop(path, None)
            except (SkillError, OSError) as exc:
                self.errors[path] = str(exc)
        return changed

    def get(self, name):
        self.reload()
        return self.skills.get(name)

    def names(self):
        return sorted(self.skills)
