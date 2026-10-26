"""TC-CHA-008 (REQ-CHA-008), the part that code can check: the shared persona file reaches the model as the system message of every call, with the default form of address
(master, unless the persona says otherwise); a change of the file counts from the next call on. Whether the model then behaves as the persona says is the eval of
AC-8 (check dialogues against a baseline fixed in Plan) and is not decided here. Run with: python tests/test_persona_prompt.py"""
import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()                              # the package is imported as MIA (relative imports of communicator.py), like in test_chat_backend.py
os.symlink(ROOT, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from persona import ADDRESS_ALONE, ADDRESS_RULE, persona_block, read_persona   # noqa: E402

TEXT = "You are Mia, dry and calm.\n\tShe says «ß» and \"quotes\".  \n"


class PersonaTextTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.path = os.path.join(self.dir, "persona.json")

    def write(self, doc):
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump(doc, fp)

    @mark.req("REQ-CHA-008")
    def test_the_text_is_read_as_it_was_saved(self):
        self.write({"text": TEXT, "name": "Mia"})
        self.assertEqual(read_persona(self.path), TEXT)

    @mark.req("REQ-CHA-008")
    def test_a_missing_broken_or_blank_file_is_no_persona(self):
        self.assertEqual(read_persona(self.path), "")
        with open(self.path, "w", encoding="utf-8") as fp:
            fp.write("{broken")
        self.assertEqual(read_persona(self.path), "")
        self.write({"text": 5})
        self.assertEqual(read_persona(self.path), "")

    @mark.req("REQ-CHA-008")
    def test_the_block_has_the_persona_unchanged_and_the_default_address(self):
        block = persona_block(TEXT)
        self.assertIn(TEXT, block)
        self.assertTrue(block.rstrip().endswith(ADDRESS_RULE))
        self.assertIn("master", ADDRESS_RULE)

    @mark.req("REQ-CHA-008")
    def test_without_a_persona_the_block_is_the_default_address_alone(self):
        self.assertEqual(persona_block(""), ADDRESS_ALONE)
        self.assertEqual(persona_block("  \n"), ADDRESS_ALONE)
        self.assertNotIn("above", ADDRESS_ALONE)                       # there is no persona above to refer to

    @mark.req("REQ-CHA-008")
    def test_the_old_calibration_text_is_the_fallback(self):
        self.assertIn("be playful", persona_block("", fallback="be playful"))
        self.assertNotIn("be playful", persona_block(TEXT, fallback="be playful"))


class CommunicatorSystemMessageTest(unittest.TestCase):
    """Communicator.chat() with a fake Ollama client that records the messages of each call"""

    def setUp(self):
        communicator = importlib.import_module("MIA.communicator")
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.path = os.path.join(self.dir, "persona.json")
        self.sent = []
        outer = self

        class Client:
            def chat(self, model, messages, **kwargs):
                outer.sent.append([dict(m) for m in messages])
                return iter(())

        comm = communicator.Communicator.__new__(communicator.Communicator)
        comm._history, comm.version, comm.llm_options, comm.think, comm.keep_alive = [], "m", None, None, None
        comm.client, comm._addtional_calibration = Client(), ""
        comm.persona_provider = lambda: read_persona(self.path)
        self.comm = comm

    def save(self, text):
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump({"text": text}, fp)

    @mark.req("REQ-CHA-008")
    def test_the_persona_is_the_system_message_of_the_call(self):
        self.save(TEXT)
        self.comm.chat("hi")
        first = self.sent[0][0]
        self.assertEqual(first["role"], "system")
        self.assertIn(TEXT, first["content"])
        self.assertIn(ADDRESS_RULE, first["content"])
        self.assertEqual(self.sent[0][1:], [{"role": "user", "content": "hi"}])

    @mark.req("REQ-CHA-008")
    def test_the_system_message_is_not_kept_in_the_history(self):
        self.save(TEXT)
        self.comm.chat("hi")
        self.comm.chat("again")
        self.assertEqual([m["role"] for m in self.comm._history], ["user", "user"])
        self.assertEqual([m["role"] for m in self.sent[1]], ["system", "user", "user"])

    @mark.req("REQ-CHA-008")
    def test_a_change_of_the_file_counts_from_the_next_call(self):
        self.save("first persona")
        self.comm.chat("one")
        self.save("second persona, calls everybody captain")
        self.comm.chat("two")
        self.assertIn("first persona", self.sent[0][0]["content"])
        self.assertIn("second persona, calls everybody captain", self.sent[1][0]["content"])
        self.assertNotIn("first persona", self.sent[1][0]["content"])

    @mark.req("REQ-CHA-008")
    def test_without_a_file_the_default_address_still_applies(self):
        self.comm.chat("hi")
        self.assertEqual(self.sent[0][0], {"role": "system", "content": ADDRESS_ALONE})

    @mark.req("REQ-CHA-008")
    def test_the_old_calibration_file_still_works_when_there_is_no_persona(self):
        self.comm._addtional_calibration = "be playful"
        self.comm.chat("hi")
        self.assertIn("be playful", self.sent[0][0]["content"])

    # --- the structured memory in the system message (REQ-CHA-011) ----------------------------------------------------------------------
    @mark.req("REQ-CHA-011")
    def test_the_memory_block_follows_the_persona_and_the_address_rule(self):
        self.save(TEXT)
        asked = []
        self.comm.memory_provider = lambda text: asked.append(text) or "- fact: lives in Graz (m1)"
        self.comm.chat("where do I live?")
        content = self.sent[0][0]["content"]
        self.assertEqual(asked, ["where do I live?"])
        self.assertIn("- fact: lives in Graz (m1)", content)
        self.assertLess(content.index(TEXT), content.index(ADDRESS_RULE))
        self.assertLess(content.index(ADDRESS_RULE), content.index("lives in Graz"))
        self.assertEqual([m["role"] for m in self.comm._history], ["user"])                          # the block is not kept in the history

    @mark.req("REQ-CHA-011")
    def test_no_records_no_block_and_a_failing_provider_changes_nothing(self):
        self.comm.memory_provider = lambda text: ""
        self.comm.chat("hi")
        self.assertEqual(self.sent[0][0], {"role": "system", "content": ADDRESS_ALONE})

        def broken(text):
            raise RuntimeError("memory down")

        self.comm.memory_provider = broken
        self.comm.chat("again")
        self.assertEqual(self.sent[1][0], {"role": "system", "content": ADDRESS_ALONE})

    @mark.req("REQ-CHA-011")
    def test_persona_block_with_a_memory_only_adds_it_at_the_end(self):
        self.assertEqual(persona_block(TEXT, memory=""), persona_block(TEXT))
        block = persona_block(TEXT, memory="- fact: x (m1)")
        self.assertTrue(block.startswith(persona_block(TEXT)))
        self.assertTrue(block.endswith("- fact: x (m1)"))
        self.assertTrue(persona_block("", memory="- fact: x (m1)").startswith(ADDRESS_ALONE))


if __name__ == "__main__":
    unittest.main()
