"""
TC-RUN-012, TC-LOG-001 (REQ-RUN-012, REQ-TLS-003, REQ-LOG-001; findings N3 and F9 of the N-2.4.1 re-verification, D-129): the wiring of web_app.py,
read from its source because importing it starts the app. The door of the tools is built by build_tool_calls (every source handed in), and the chat
run passes the user who chatted to the runner. Run with: python tests/test_web_app_wiring.py
"""
import ast
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                       # noqa: E402

TREE = ast.parse(open(os.path.join(REPO, "web_app.py"), encoding="utf-8").read())


def calls_to(name, tree=TREE):
    """the calls of a plain name (build_tool_calls(...)) or of an attribute (core.run(...)), written as 'name' or 'object.attribute'"""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            label = func.id if isinstance(func, ast.Name) else "%s.%s" % (func.value.id, func.attr) if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) else None
            if label == name:
                found.append(node)
    return found


def function(name):
    return next(node for node in ast.walk(TREE) if isinstance(node, ast.FunctionDef) and node.name == name)


def keyword(call, name):
    return next((k.value for k in call.keywords if k.arg == name), None)


class WebAppWiringTests(unittest.TestCase):

    @mark.req("REQ-RUN-012", "REQ-TLS-003")
    def test_the_door_is_built_with_every_source(self):
        """TC-RUN-012: the app builds its door of the tools with build_tool_calls, never with ToolCalls directly (N3).

        Example: web_app.py -> one call build_tool_calls(...), no call ToolCalls(...)
        """
        # Given: the source of web_app.py
        # When: its calls are read
        # Then: the door is built by build_tool_calls only
        self.assertEqual(len(calls_to("build_tool_calls")), 1)
        self.assertEqual(calls_to("ToolCalls"), [])

    @mark.req("REQ-LOG-001")
    def test_the_chat_run_carries_the_user_who_chatted(self):
        """TC-LOG-001: the chat run passes the author of the message to the runner (F9, D-129).

        Example: run_chat_exchange -> core.run(..., user=chat_service.author())
        """
        # Given: the function that runs a chat exchange
        runs = calls_to("core.run", function("run_chat_exchange"))
        # When: its call of the runner is read
        self.assertEqual(len(runs), 1)
        user = keyword(runs[0], "user")
        # Then: the user is the author the chat service reports
        self.assertIsInstance(user, ast.Call)
        self.assertEqual((user.func.value.id, user.func.attr), ("chat_service", "author"))

    @mark.req("REQ-LOG-001")
    def test_the_chat_run_starts_as_a_message(self):
        """TC-LOG-001: the chat run is still started by a message (REQ-RUN-001), next to its user.

        Example: run_chat_exchange -> core.run(..., started_by="message")
        """
        # Given: the call of the runner in run_chat_exchange
        run = calls_to("core.run", function("run_chat_exchange"))[0]
        # When: its keyword started_by is read
        started_by = keyword(run, "started_by")
        # Then: it is the text "message"
        self.assertEqual(started_by.value, "message")

if __name__ == "__main__":
    unittest.main()
