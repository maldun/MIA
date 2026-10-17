"""
Tests for the 3D character integration (PresetExpressor, configuration files, web app events).
Run with the MIA virtualenv from the folder that contains this repository:
    python -m unittest discover -s tests -t . -v      (inside the repository)
or simply: python tests/test_character_integration.py
"""
import importlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the code uses relative imports as package "MIA": make the repository importable under that name
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


def load_json(name):
    with open(os.path.join(REPO, name)) as fp:
        return json.load(fp)


class ConfigFiles(unittest.TestCase):
    def setUp(self):
        self.emotions = load_json("emotion_map.json")
        self.expressions = load_json("expressions.json")
        self.presets = {p["name"] for p in load_json("ui/godot/presets/library.json")["presets"]}

    def test_every_emotion_maps_to_an_expression(self):
        for emotion, expression in self.emotions.items():
            self.assertIn(expression, self.expressions, f"emotion {emotion}")

    def test_every_expression_has_a_preset(self):
        for key, entry in self.expressions.items():
            self.assertIn(entry.get("preset", key), self.presets, f"expression {key}")

    def test_old_emotions_are_still_there(self):
        for emotion in ["agree", "disagree", "neutral", "annoyed", "happy", "MIA"]:
            self.assertIn(emotion, self.emotions)

    def test_new_emotions_are_there(self):
        for emotion in ["sad", "angry", "surprised", "embarrassed", "smug", "thinking"]:
            self.assertEqual(self.emotions[emotion], emotion)

    def test_old_expressions_keep_their_voice(self):
        for key in ["greet", "no", "annoyed", "talk", "yes", "idle"]:
            self.assertTrue(self.expressions[key]["voice"].endswith(".wav"))

    def test_no_video_entries_left(self):
        for key, entry in self.expressions.items():
            self.assertNotIn("vid", entry, key)

    def test_all_14_required_presets_exist(self):
        required = {"greet", "no", "annoyed", "talk", "yes", "idle", "neutral", "happy", "sad", "angry",
                    "surprised", "embarrassed", "smug", "thinking"}
        self.assertEqual(required, self.presets)


class PresetExpressorTest(unittest.TestCase):
    def setUp(self):
        self.expressor_module = importlib.import_module("MIA.expressor")
        self.sent = []
        self.expressor = self.expressor_module.PresetExpressor(
            expressions=os.path.join(REPO, "expressions.json"), send=self.sent.append)

    def test_express_sends_the_preset(self):
        self.assertEqual(self.expressor.express("yes"), "yes")
        self.assertEqual(self.sent, ["yes"])
        self.assertEqual(self.expressor.current, "yes")

    def test_preset_can_differ_from_the_key(self):
        expressor = self.expressor_module.PresetExpressor(
            expressions={"hello": {"preset": "greet"}, "plain": {}}, send=self.sent.append)
        self.assertEqual(expressor.express("hello"), "greet")
        self.assertEqual(expressor.express("plain"), "plain")  # default: the key itself

    def test_unknown_expression_does_not_crash_and_keeps_the_current_one(self):
        self.expressor.express("yes")
        self.assertIsNone(self.expressor.express("nonsense"))
        self.assertEqual(self.expressor.current, "yes")
        self.assertEqual(self.sent, ["yes"])

    def test_works_without_a_send_function(self):
        expressor = self.expressor_module.PresetExpressor(expressions=os.path.join(REPO, "expressions.json"))
        self.assertEqual(expressor.express("idle"), "idle")

    def test_no_video_expressor_anymore(self):
        self.assertFalse(hasattr(self.expressor_module, "VideoExpressor"))

    def test_voice_expressor_skips_expressions_without_voice(self):
        voice = self.expressor_module.VoiceExpressor(web_url=None)
        played = []
        self.expressor_module.play_sound = lambda *a, **k: played.append(a)
        voice.express("sad")      # no voice clip: silently nothing
        self.assertEqual(played, [])


class WebAppEvents(unittest.TestCase):
    """The Flask app: expression events, current expression for new pages, serving the character."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.web_app = importlib.import_module("MIA.web_app")

    def test_express_and_reload_emits_an_expression_event(self):
        wa = self.web_app
        client = wa.socketio.test_client(wa.app)
        client.get_received()
        wa.express_and_reload("surprised", sound=False)
        events = [e for e in client.get_received() if e["name"] == "expression"]
        self.assertEqual(events[-1]["args"][0], {"name": "surprised"})

    def test_new_pages_get_the_current_expression(self):
        wa = self.web_app
        wa.express_and_reload("smug", sound=False)
        client = wa.socketio.test_client(wa.app)
        client.get_received()
        client.emit("character_ready")
        events = [e for e in client.get_received() if e["name"] == "expression"]
        self.assertEqual(events[-1]["args"][0], {"name": "smug"})

    def test_unknown_expression_is_ignored(self):
        wa = self.web_app
        wa.express_and_reload("smug", sound=False)
        client = wa.socketio.test_client(wa.app)
        client.get_received()
        wa.express_and_reload("does_not_exist", sound=False)  # must not raise
        self.assertEqual([e for e in client.get_received() if e["name"] == "expression"], [])

    def test_character_files_are_served_with_the_right_types(self):
        wa = self.web_app
        with tempfile.TemporaryDirectory() as folder:
            for name, data in [("index.html", b"<html></html>"), ("index.wasm", b"\0asm"), ("index.pck", b"GDPC")]:
                with open(os.path.join(folder, name), "wb") as fp:
                    fp.write(data)
            old = wa.CHARACTER_FOLDER
            wa.CHARACTER_FOLDER = folder
            try:
                http = wa.app.test_client()
                self.assertEqual(http.get("/character/").status_code, 200)
                self.assertEqual(http.get("/character/index.wasm").mimetype, "application/wasm")
                self.assertEqual(http.get("/character/index.pck").status_code, 200)
                self.assertEqual(http.get("/character/nothing.js").status_code, 404)
            finally:
                wa.CHARACTER_FOLDER = old

    def test_missing_character_build_gives_a_helpful_message(self):
        wa = self.web_app
        old = wa.CHARACTER_FOLDER
        wa.CHARACTER_FOLDER = "/nonexistent/folder"
        try:
            response = wa.app.test_client().get("/character/")
            self.assertEqual(response.status_code, 404)
            self.assertIn(b"build_web.sh", response.data)
        finally:
            wa.CHARACTER_FOLDER = old

    def test_allowed_origins_cover_localhost_lan_and_https_proxy(self):
        origins = self.web_app.build_allowed_origins("http://192.168.1.5:8585", "localhost", 8585, 8586, "192.168.1.5")
        for expected in ["http://192.168.1.5:8585", "http://localhost:8585", "http://127.0.0.1:8585",
                         "https://192.168.1.5:8586", "https://localhost:8586"]:
            self.assertIn(expected, origins)
        self.assertEqual(len(origins), len(set(origins)))
        without_https = self.web_app.build_allowed_origins("http://192.168.1.5:8585", "localhost", 8585, None, "192.168.1.5")
        self.assertFalse([o for o in without_https if o.startswith("https://")])

    def test_page_connects_to_its_own_origin(self):
        html = open(os.path.join(REPO, "templates", "index.html")).read()
        self.assertIn("io(window.location.origin", html)

    def test_page_embeds_the_character_and_has_no_video(self):
        html = open(os.path.join(REPO, "templates", "index.html")).read()
        self.assertIn('id="character"', html)
        self.assertNotIn("<video", html)
        self.assertNotIn("video_updated", html)
        self.assertIn("toCharacter({type: 'speaking'", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
