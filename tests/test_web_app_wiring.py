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

    @mark.req("REQ-RUN-012")

    @mark.req("REQ-TLS-003")
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

class ChatAgentWiringTests(unittest.TestCase):
    """the chat agent's wiring in web_app.py, read from its source (D-173, first Verify of N-2.2)"""

    @mark.req("REQ-CHA-003")
    def test_the_queue_holds_five_with_or_without_accounts(self):
        """TC-CHA-003 (F2): the default of the chat queue is 5 whether accounts are enabled or not; only the limit per user needs accounts.

        Example: queue_size=cfg.get(CHAT_QUEUE_KEY, 5 if accounts else 1) -> 1 without accounts, wrong; cfg.get(CHAT_QUEUE_KEY, 5) -> right.
        """
        # Given: the call that builds the chat service
        call = calls_to("ChatService")[0]
        # When: the default of queue_size is read
        queue = keyword(call, "queue_size")
        # Then: it is the constant 5, not a choice that depends on the accounts
        self.assertIsInstance(queue, ast.Call)
        self.assertIsInstance(queue.args[1], ast.Constant)
        self.assertEqual(queue.args[1].value, 5)

    @mark.req("REQ-CHA-009")
    def test_a_connecting_page_greets_after_the_login_guard(self):
        """TC-CHA-009 (F4): handle_connect calls chat_service.greet() after the session guard, so only a logged-in page makes her greet.

        Example: guard_connect(...) then greet() -> right; greet() before the guard or not at all -> wrong.
        """
        # Given: the calls of the connect handler in source order
        order = [(node.lineno, node.func.attr) for node in ast.walk(function("handle_connect")) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        names = [name for _, name in sorted(order)]
        # When: the guard and the greeting are looked up
        # Then: the greeting is there and comes after the guard
        self.assertIn("greet", names)
        self.assertIn("guard_connect", names)
        self.assertLess(names.index("guard_connect"), names.index("greet"))


if __name__ == "__main__":
    unittest.main()
