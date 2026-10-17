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

    def test_happy_uses_the_happy_preset_and_neutral_a_calm_one(self):
        self.assertEqual(self.emotions["happy"], "happy")
        self.assertEqual(self.expressions["happy"]["preset"], "happy")
        self.assertEqual(self.emotions["neutral"], "neutral")
        self.assertEqual(self.expressions["neutral"]["preset"], "neutral")
        # the calm preset has no gesture and does not move the mouth by itself
        library = {p["name"]: p for p in load_json("ui/godot/presets/library.json")["presets"]}
        self.assertFalse(library["neutral"].get("gesture"))
        self.assertFalse(library["neutral"].get("speaking"))
        # neutral answers are the most common ones: no "Listen!" clip for them
        self.assertIsNone(self.expressions["neutral"]["voice"])

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

    def _with_backgrounds(self, files):
        """runs a block with a temporary backgrounds folder holding the given file names"""
        import contextlib

        @contextlib.contextmanager
        def ctx():
            wa = self.web_app
            with tempfile.TemporaryDirectory() as folder:
                for name in files:
                    with open(os.path.join(folder, name), "wb") as fp:
                        fp.write(b"fake picture " + name.encode())
                os.mkdir(os.path.join(folder, "sub.png"))  # a folder named like a picture is no picture
                old = wa.BACKGROUND_FOLDER
                wa.BACKGROUND_FOLDER = folder
                try:
                    yield wa.app.test_client()
                finally:
                    wa.BACKGROUND_FOLDER = old
        return ctx()

    def test_backgrounds_are_listed_sorted_and_only_pictures(self):
        with self._with_backgrounds(["b.jpg", "a.PNG", "notes.txt", "c.webp", "video.mp4"]) as http:
            data = http.get("/character-backgrounds.json").get_json()
            self.assertEqual(data["files"], ["a.PNG", "b.jpg", "c.webp"])
            self.assertEqual(data["default"], "a.PNG")  # the first one

    def test_configured_background_is_the_default(self):
        wa = self.web_app
        wa.cfg["background_image"] = "b.jpg"
        try:
            with self._with_backgrounds(["a.png", "b.jpg"]) as http:
                self.assertEqual(http.get("/character-backgrounds.json").get_json()["default"], "b.jpg")
            wa.cfg["background_image"] = "missing.jpg"  # unknown name: fall back to the first picture
            with self._with_backgrounds(["a.png", "b.jpg"]) as http:
                self.assertEqual(http.get("/character-backgrounds.json").get_json()["default"], "a.png")
        finally:
            wa.cfg.pop("background_image", None)

    def test_background_files_are_served_but_nothing_else(self):
        with self._with_backgrounds(["room.png", "notes.txt"]) as http:
            ok = http.get("/character-backgrounds/room.png")
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(ok.data, b"fake picture room.png")
            ok.close()
            self.assertEqual(http.get("/character-backgrounds/notes.txt").status_code, 404)   # not a picture
            self.assertEqual(http.get("/character-backgrounds/missing.png").status_code, 404)
            self.assertEqual(http.get("/character-backgrounds/../setup_cfg.json").status_code, 404)  # no way out of the folder
            self.assertEqual(http.get("/character-backgrounds/%2e%2e/setup_cfg.json").status_code, 404)
            self.assertEqual(http.get("/character-backgrounds/sub.png").status_code, 404)

    def test_missing_background_folder_gives_an_empty_list(self):
        wa = self.web_app
        old = wa.BACKGROUND_FOLDER
        wa.BACKGROUND_FOLDER = "/nonexistent/backgrounds"
        try:
            self.assertEqual(wa.app.test_client().get("/character-backgrounds.json").get_json(), {"files": [], "default": ""})
        finally:
            wa.BACKGROUND_FOLDER = old

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


class TlsProxyTest(unittest.TestCase):
    """python -m MIA starts the https proxy when "https_port" is set."""

    @classmethod
    def setUpClass(cls):
        cls.tls = importlib.import_module("MIA.tls_proxy")

    @staticmethod
    def free_port():
        import socket
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def test_nothing_started_without_https_port(self):
        self.assertIsNone(self.tls.start_https_proxy({}, REPO, 8585))
        self.assertIsNone(self.tls.start_https_proxy({"https_port": None}, REPO, 8585))

    def test_missing_tools_do_not_crash_mia(self):
        old = self.tls.shutil.which
        self.tls.shutil.which = lambda tool: None
        try:
            self.assertIsNone(self.tls.start_https_proxy({"https_port": 8586}, REPO, 8585))
        finally:
            self.tls.shutil.which = old

    def test_missing_script_does_not_crash_mia(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(self.tls.start_https_proxy({"https_port": 8586}, empty, 8585))

    def test_https_on_localhost_reaches_the_web_app(self):
        import http.server
        import socket
        import ssl
        import threading
        import time
        import urllib.request
        if not all(self.tls.shutil.which(tool) for tool in ("socat", "openssl")):
            self.skipTest("socat and openssl are needed")

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"hello from the web app"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        web_port, https_port = self.free_port(), self.free_port()
        backend = http.server.ThreadingHTTPServer(("127.0.0.1", web_port), Handler)
        threading.Thread(target=backend.serve_forever, daemon=True).start()
        proc = self.tls.start_https_proxy({"https_port": https_port}, REPO, web_port)
        try:
            self.assertIsNotNone(proc)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE   # self-signed certificate
            answer = None
            for _ in range(40):
                try:
                    answer = urllib.request.urlopen(f"https://localhost:{https_port}/", timeout=3, context=context).read()
                    break
                except Exception:
                    time.sleep(0.25)
            self.assertEqual(answer, b"hello from the web app")
            # the certificate is valid for localhost and the LAN addresses
            cert = ssl.get_server_certificate(("127.0.0.1", https_port))
            self.assertIn("BEGIN CERTIFICATE", cert)
            # https on the plain http port does not work (this is what a wrong port looks like)
            with self.assertRaises(Exception):
                urllib.request.urlopen(f"https://localhost:{web_port}/", timeout=3, context=context)
        finally:
            if proc is not None:
                proc.terminate()
                proc.wait(timeout=5)
            backend.shutdown()
        with self.assertRaises(Exception):   # stopped with MIA
            urllib.request.urlopen(f"https://localhost:{https_port}/", timeout=2, context=context)

    def test_main_binds_all_addresses_and_starts_the_proxy(self):
        source = open(os.path.join(REPO, "__main__.py")).read()
        self.assertIn('cfg.get("host","0.0.0.0")', source)
        self.assertIn("start_https_proxy(cfg,fpath,WEB_PORT)", source)
        self.assertIn("stop_process(https_proc", source)   # the proxy lives and dies with MIA


if __name__ == "__main__":
    unittest.main(verbosity=2)
