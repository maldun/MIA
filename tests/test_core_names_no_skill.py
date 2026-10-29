"""
TC-WFM-039 (REQ-WFM-039), inspection: no file of the core names the id of a skill in code (a string such as "review" or "/lookup"); the skills are the folders of `extensions/`, and the
chat service, the web application and the loader learn them from there. Comments and docstrings may talk about the examples.
Run: python tests/test_core_names_no_skill.py
"""
import ast
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = ("chat_service.py", "chat_api.py", "chat_ops_api.py", "files_api.py", "web_app.py", "task_registry.py", "task_monitor.py", "extension_loader.py", "file_store.py", "model_gate.py")
SKILL_ID = re.compile(r"^/?(lookup|research|search|review)\b", re.I)


def code_strings(path):
    """the string constants of a module that are not docstrings"""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and ast.get_docstring(node, clean=False) is not None:
            docstrings.add(id(node.body[0].value))
    return [(n.lineno, n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]


class CoreNamesNoSkill(unittest.TestCase):
    def test_no_core_file_names_a_skill_id_in_code(self):
        found = [(name, line, value) for name in CORE for line, value in code_strings(os.path.join(REPO, name)) if SKILL_ID.match(value.strip())]
        self.assertEqual(found, [])

    def test_every_skill_with_a_command_is_a_folder_with_a_manifest(self):
        folders = sorted(n for n in os.listdir(os.path.join(REPO, "extensions")) if os.path.isfile(os.path.join(REPO, "extensions", n, "manifest.json")))
        self.assertEqual(folders, ["lookup", "review", "search"])


if __name__ == "__main__":
    unittest.main()
