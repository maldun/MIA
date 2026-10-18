"""
Tests for expressions from a description: generator (prompt, validation, retry, errors, busy), closest preset, feedback log, REST API.
A fake function stands in for the language model. Run with the MIA virtualenv: python tests/test_expression_llm.py
"""
import importlib
import json
import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

SHIPPED = os.path.join(REPO, "ui", "godot", "presets")


def answer(**changes):
    data = {"description": "surprised but hiding it", "weights": {"Fcl_EYE_Surprised": 0.5, "Fcl_MTH_Fun": 0.3},
            "bones": {"head_roll": 4}, "tags": ["surprised", "calm"], "gesture": ""}
    data.update(changes)
    return json.dumps(data)


class Base(unittest.TestCase):
    def setUp(self):
        self.ps = importlib.import_module("MIA.preset_store")
        self.llm = importlib.import_module("MIA.expression_llm")
        self.tmp = tempfile.TemporaryDirectory()
        self.store = self.ps.PresetStore(
            os.path.join(self.tmp.name, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
            shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_file=os.path.join(SHIPPED, "gestures.json"))
        self.calls = []
        self.replies = [answer()]
        self.log = os.path.join(self.tmp.name, "feedback.jsonl")
        self.gen = self.llm.ExpressionGenerator(self.store, self.chat, os.path.join(SHIPPED, "shape_keys.json"),
                                                os.path.join(SHIPPED, "gestures.json"), log_path=self.log, model_name=lambda: "fake-model")

    def tearDown(self):
        self.tmp.cleanup()

    def chat(self, messages, schema):
        self.calls.append((messages, schema))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return reply

    def log_entries(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fp:
            return [json.loads(line) for line in fp]


class GeneratorTest(Base):
    def test_generates_a_valid_preset_that_is_not_saved(self):
        result = self.gen.generate("surprised but trying to hide it")
        preset = result["preset"]
        self.assertEqual(preset["source"], "llm")
        self.assertEqual(preset["weights"], {"Fcl_EYE_Surprised": 0.5, "Fcl_MTH_Fun": 0.3})
        self.assertEqual(preset["bones"], {"head_roll": 4.0})
        self.assertTrue(preset["name"].startswith("llm-surprised-hide"))
        self.assertNotIn(preset["name"], self.store.names())
        self.assertEqual(result["model"], "fake-model")
        self.assertTrue(result["id"])
        self.assertEqual([e["event"] for e in self.log_entries()], ["generated"])

    def test_the_prompt_knows_every_shape_key_bone_and_gesture(self):
        self.gen.generate("smug")
        messages, schema = self.calls[0]
        system = messages[0]["content"]
        with open(os.path.join(SHIPPED, "shape_keys.json")) as fp:
            keys = [k["name"] for k in json.load(fp)["shape_keys"]]
        for key in keys:
            self.assertIn(key, system)
            self.assertIn(key, schema["properties"]["weights"]["items"]["properties"]["key"]["enum"])
        for bone in self.ps.BONE_PARAMS:
            self.assertIn(bone, system)
        self.assertIn("wave", system)
        self.assertEqual(messages[-1]["content"], "Request: smug")
        self.assertEqual(schema["required"], ["description", "weights"])
        self.assertEqual(schema["properties"]["weights"]["maxItems"], self.llm.MAX_KEYS)
        self.assertEqual(schema["properties"]["weights"]["type"], "array")
        self.assertIn("wave", schema["properties"]["gesture"]["enum"])

    def test_unknown_keys_and_out_of_range_values_are_corrected(self):
        self.replies = [answer(weights={"Fcl_EYE_Joy": 1.7, "Made_Up_Key": 0.5, "Fcl_BRW_Angry": "lots"})]
        result = self.gen.generate("joy")
        self.assertEqual(result["preset"]["weights"], {"Fcl_EYE_Joy": 1.0})
        self.assertTrue(any("Made_Up_Key" in c for c in result["corrections"]))

    def test_the_list_format_of_the_schema_is_understood_and_zeros_are_dropped(self):
        weights = [{"key": "Fcl_MTH_Fun", "value": 0.5}, {"key": "Fcl_EYE_Joy", "value": 0.3}, {"key": "Fcl_HA_Hide", "value": 0},
                   {"key": "Not_A_Key", "value": 0.9}, {"value": 0.4}, "junk"]
        self.replies = [answer(weights=weights)]
        result = self.gen.generate("smug")
        self.assertEqual(result["preset"]["weights"], {"Fcl_MTH_Fun": 0.5, "Fcl_EYE_Joy": 0.3})
        self.assertTrue(any("Not_A_Key" in c for c in result["corrections"]))

    def test_an_object_of_weights_still_works(self):
        self.replies = [answer(weights={"Fcl_MTH_Fun": 0.5, "Fcl_EYE_Joy": 0.0})]
        self.assertEqual(self.gen.generate("smug")["preset"]["weights"], {"Fcl_MTH_Fun": 0.5})

    def test_the_prompt_warns_about_teeth_and_explains_the_style(self):
        self.gen.generate("shy")
        system = self.calls[0][0][0]["content"]
        self.assertIn("Fcl_HA_*", system)
        self.assertIn("teeth", system)
        self.assertIn("MOUTH", system)
        self.assertIn("never list a key with value 0", system)

    def test_without_similar_presets_typical_ones_are_the_examples(self):
        self.gen.generate("zzzz qqqq")
        system = self.calls[0][0][0]["content"]
        for text in ("confident half-smile", "shy, looking away", "broad happy smile"):      # smug, embarrassed, happy
            self.assertIn(f"Request: {text}", system)
        self.assertNotIn("Request: angry", system)
        self.assertIn('"weights": [{"key": "Fcl_MTH_Fun", "value": 0.6}', system)       # examples look like the answer that is asked for

    def test_one_retry_on_an_unusable_answer(self):
        self.replies = ["this is not json", answer()]
        result = self.gen.generate("smug")
        self.assertEqual(len(self.calls), 2)
        self.assertIn("could not be used", self.calls[1][0][-1]["content"])
        self.assertEqual(result["preset"]["source"], "llm")

    def test_empty_weights_count_as_unusable(self):
        self.replies = [answer(weights={"Nope": 1}, bones={}), answer()]
        self.gen.generate("smug")
        self.assertEqual(len(self.calls), 2)

    def test_two_bad_answers_give_a_clear_error(self):
        self.replies = ["nonsense"]
        with self.assertRaises(self.ps.PresetError) as raised:
            self.gen.generate("smug")
        self.assertEqual(raised.exception.status, 502)
        self.assertEqual(len(self.calls), 2)

    def test_model_offline_gives_503(self):
        self.replies = [ConnectionError("connection refused")]
        with self.assertRaises(self.ps.PresetError) as raised:
            self.gen.generate("smug")
        self.assertEqual(raised.exception.status, 503)
        self.assertIn("connection refused", raised.exception.message)
        self.assertEqual(len(self.calls), 1)

    def test_request_validation(self):
        for bad in ["", "   ", None, 5, "x" * 301]:
            with self.assertRaises(self.ps.PresetError):
                self.gen.generate(bad)
        self.assertEqual(self.calls, [])

    def test_only_one_request_at_a_time(self):
        gate = threading.Event()
        started = threading.Event()

        def slow(messages, schema):
            started.set()
            gate.wait(5)
            return answer()

        self.gen._chat = slow
        thread = threading.Thread(target=lambda: self.gen.generate("first"))
        thread.start()
        self.assertTrue(started.wait(5))
        with self.assertRaises(self.ps.PresetError) as raised:
            self.gen.generate("second")
        self.assertEqual(raised.exception.status, 429)
        gate.set()
        thread.join(5)
        self.assertEqual(self.gen.generate("third")["preset"]["source"], "llm")

    def test_names_do_not_collide(self):
        first = self.gen.generate("smug look")["preset"]
        self.store.create(first)
        second = self.gen.generate("smug look")["preset"]
        self.assertNotEqual(first["name"], second["name"])
        self.assertTrue(self.ps.NAME_RE.match(second["name"]))


class MatchTest(Base):
    def test_closest_preset_by_name_tags_and_description(self):
        self.assertEqual(self.gen.match("very sad and crying")["name"], "sad")
        self.assertEqual(self.gen.match("so happy")["name"], "happy")
        self.assertEqual(self.gen.match("thinking hard")["name"], "thinking")

    def test_nothing_fits_gives_neutral(self):
        result = self.gen.match("zzzzzz qqqq")
        self.assertEqual(result["name"], "neutral")
        self.assertEqual(result["score"], 0)

    def test_the_match_comes_without_the_model(self):
        self.gen.match("angry")
        self.assertEqual(self.calls, [])


class FeedbackTest(Base):
    def test_decisions_are_logged_with_the_request(self):
        first = self.gen.generate("smug look")
        self.gen.feedback(first["id"], "keep")
        second = self.gen.generate("sleepy")
        self.gen.feedback(second["id"], "reject")
        events = self.log_entries()
        self.assertEqual([e["event"] for e in events], ["generated", "keep", "generated", "reject"])
        self.assertEqual(events[1]["description"], "smug look")
        self.assertEqual(events[3]["preset"]["name"], second["preset"]["name"])

    def test_an_edit_logs_what_the_user_saved(self):
        result = self.gen.generate("smug look")
        edited = dict(result["preset"], weights={"Fcl_MTH_Fun": 0.9})
        self.gen.feedback(result["id"], "edit", edited)
        entry = self.log_entries()[-1]
        self.assertEqual(entry["event"], "edit")
        self.assertEqual(entry["preset"]["weights"], {"Fcl_MTH_Fun": 0.9})
        self.assertEqual(entry["preset"]["source"], "llm_edited")

    def test_unknown_request_and_decision_are_refused(self):
        with self.assertRaises(self.ps.PresetError) as raised:
            self.gen.feedback("nope", "keep")
        self.assertEqual(raised.exception.status, 404)
        result = self.gen.generate("smug")
        with self.assertRaises(self.ps.PresetError):
            self.gen.feedback(result["id"], "maybe")

    def test_kept_and_rejected_results_become_examples(self):
        good = self.gen.generate("smug look")
        self.gen.feedback(good["id"], "keep")
        self.replies = [answer(weights={"Fcl_EYE_Close": 1.0}, description="all closed")]
        bad = self.gen.generate("sleepy")
        self.gen.feedback(bad["id"], "reject")
        self.replies = [answer()]
        self.gen.generate("something new")
        system = self.calls[-1][0][0]["content"]
        self.assertIn("Examples the user liked", system)
        self.assertIn("Request: smug look", system)
        self.assertIn("rejected", system)
        self.assertIn("Request: sleepy", system)

    def test_a_damaged_log_line_does_not_break_the_prompt(self):
        with open(self.log, "w", encoding="utf-8") as fp:
            fp.write("{broken\n")
        self.assertEqual(self.gen.generate("smug")["preset"]["source"], "llm")


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")
        cls.http = cls.wa.app.test_client()
        cls.gen = cls.wa.app.config["EXPRESSION_GENERATOR"]
        cls.token = cls.wa.app.config["EDITOR_TOKEN_INFO"][0]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gen.log_path = os.path.join(self.tmp.name, "feedback.jsonl")
        self.reply = answer()
        self.original = self.gen._chat
        self.gen._chat = lambda messages, schema: self.reply
        self.headers = {"X-MIA-Token": self.token or ""}

    def tearDown(self):
        self.gen._chat = self.original
        self.tmp.cleanup()

    def test_generate_match_feedback_over_http(self):
        response = self.http.post("/api/expression/generate", json={"description": "surprised"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["preset"]["source"], "llm")
        match = self.http.post("/api/expression/match", json={"description": "surprised"}, headers=self.headers)
        self.assertEqual(match.get_json()["name"], "surprised")
        done = self.http.post("/api/expression/feedback", json={"id": data["id"], "decision": "keep"}, headers=self.headers)
        self.assertEqual(done.get_json(), {"logged": "keep"})

    def test_needs_the_token_json_and_a_known_origin(self):
        if self.token:
            self.assertEqual(self.http.post("/api/expression/generate", json={"description": "x"}).status_code, 401)
        self.assertEqual(self.http.post("/api/expression/generate", data="description=x", headers=self.headers).status_code, 415)
        foreign = dict(self.headers, Origin="http://evil.example")
        self.assertEqual(self.http.post("/api/expression/generate", json={"description": "x"}, headers=foreign).status_code, 403)

    def test_errors_are_json_with_the_right_status(self):
        self.assertEqual(self.http.post("/api/expression/generate", json={}, headers=self.headers).status_code, 400)
        self.assertEqual(self.http.post("/api/expression/feedback", json={"id": "zz", "decision": "keep"}, headers=self.headers).status_code, 404)
        self.gen._chat = lambda m, s: (_ for _ in ()).throw(ConnectionError("down"))
        response = self.http.post("/api/expression/generate", json={"description": "x"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertIn("down", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
