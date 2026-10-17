"""
Tests for the preset storage and the REST API (preset_store.py, presets_api.py).
Run with the MIA virtualenv: python tests/test_presets_api.py
"""
import importlib
import json
import os
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the code uses relative imports as package "MIA": make the repository importable under that name
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

SHIPPED = os.path.join(REPO, "ui", "godot", "presets")


def smug(**changes):
    preset = {"name": "test_smug", "description": "confident", "weights": {"Fcl_MTH_Fun": 0.6, "Fcl_EYE_Joy": 0.3},
              "bones": {"head_roll": 3.0}, "gesture": "hand_on_hip", "speaking": False, "tags": ["smug"], "source": "manual"}
    preset.update(changes)
    return preset


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.ps = importlib.import_module("MIA.preset_store")
        self.tmp = tempfile.TemporaryDirectory()
        self.protected = {"idle"}
        self.store = self.ps.PresetStore(
            os.path.join(self.tmp.name, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
            shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_file=os.path.join(SHIPPED, "gestures.json"),
            protected=lambda: self.protected)

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_folder_is_filled_with_the_shipped_presets(self):
        names = self.store.names()
        self.assertEqual(len(names), 14)
        for expected in ["greet", "no", "annoyed", "talk", "yes", "idle", "neutral", "happy", "sad", "angry", "surprised",
                         "embarrassed", "smug", "thinking"]:
            self.assertIn(expected, names)
        talk = self.store.get("talk")
        self.assertTrue(talk["speaking"])
        self.assertEqual(talk["gesture"], "explain")
        self.assertIn("updated", talk)

    def test_existing_presets_are_not_overwritten_by_the_defaults(self):
        changed = self.store.get("smug")
        changed["description"] = "my own"
        self.store.update("smug", changed)
        again = self.ps.PresetStore(self.store.folder, defaults_file=os.path.join(SHIPPED, "library.json"))
        self.assertEqual(again.get("smug")["description"], "my own")

    def test_create_get_update_delete(self):
        created, corrections = self.store.create(smug())
        self.assertEqual(corrections, [])
        self.assertEqual(self.store.get("test_smug")["weights"]["Fcl_MTH_Fun"], 0.6)
        with self.assertRaises(self.ps.PresetError) as ctx:
            self.store.create(smug())
        self.assertEqual(ctx.exception.status, 409)
        self.store.update("test_smug", smug(description="changed"))
        self.assertEqual(self.store.get("test_smug")["description"], "changed")
        self.store.delete("test_smug")
        with self.assertRaises(self.ps.PresetError) as ctx:
            self.store.get("test_smug")
        self.assertEqual(ctx.exception.status, 404)

    def test_rename(self):
        self.store.create(smug())
        stored, _ = self.store.update("test_smug", smug(name="test_proud"))
        self.assertEqual(stored["name"], "test_proud")
        self.assertNotIn("test_smug", self.store.names())
        self.assertIn("test_proud", self.store.names())
        self.store.create(smug(name="test_other"))
        with self.assertRaises(self.ps.PresetError) as ctx:   # target exists
            self.store.update("test_proud", smug(name="test_other"))
        self.assertEqual(ctx.exception.status, 409)
        self.assertIn("test_proud", self.store.names())      # nothing was lost

    def test_presets_used_by_mia_are_protected(self):
        with self.assertRaises(self.ps.PresetError) as ctx:
            self.store.delete("idle")
        self.assertEqual(ctx.exception.status, 409)
        with self.assertRaises(self.ps.PresetError):
            self.store.update("idle", smug(name="calm"))
        self.assertIn("idle", self.store.names())
        self.store.update("idle", dict(self.store.get("idle"), description="edited"))   # editing is fine
        self.store.delete("idle", force=True)                                            # explicit force
        self.assertNotIn("idle", self.store.names())

    def test_values_are_corrected_and_reported(self):
        stored, corrections = self.store.create(smug(
            weights={"Fcl_MTH_Fun": 1.7, "Fcl_EYE_Joy": -2, "Not_A_Key": 0.5, "Fcl_BRW_Joy": "x", "Fcl_EYE_Fun": True},
            bones={"head_yaw": 99, "tail": 1}, gesture="dance", tags=["a", "a", " b ", "", "x" * 50],
            source="alien", description="d" * 400))
        self.assertEqual(stored["weights"], {"Fcl_MTH_Fun": 1.0, "Fcl_EYE_Joy": 0.0})
        self.assertEqual(stored["bones"], {"head_yaw": 45.0})
        self.assertEqual(stored["gesture"], "")
        self.assertEqual(stored["tags"], ["a", "b", "x" * 30])
        self.assertEqual(stored["source"], "manual")
        self.assertEqual(len(stored["description"]), 300)
        text = " ".join(corrections)
        for expected in ["clamped", "unknown shape key 'Not_A_Key'", "not a number", "unknown bone parameter 'tail'",
                         "unknown gesture 'dance'", "unknown source", "description shortened"]:
            self.assertIn(expected, text)

    def test_bad_names_and_bad_bodies_are_rejected(self):
        for bad in ["", "a b", "../evil", "x" * 41, "ü", None, 5, "a/b", ".hidden"]:
            with self.assertRaises(self.ps.PresetError, msg=repr(bad)):
                self.store.create(smug(name=bad))
        for body in [[], "text", 5, None]:
            with self.assertRaises(self.ps.PresetError):
                self.store.create(body)
        self.assertEqual(len(self.store.names()), 14)   # nothing was written

    def test_no_path_traversal_through_names(self):
        with self.assertRaises(self.ps.PresetError):
            self.store.get("../../setup_cfg")
        with self.assertRaises(self.ps.PresetError):
            self.store.delete("../x")

    def test_version_changes_with_every_change(self):
        v0 = self.store.version()
        self.assertEqual(v0, self.store.version())
        self.store.create(smug())
        v1 = self.store.version()
        self.assertNotEqual(v0, v1)
        self.store.update("test_smug", smug(description="x"))
        v2 = self.store.version()
        self.assertNotEqual(v1, v2)
        self.store.delete("test_smug")
        self.assertNotEqual(v2, self.store.version())

    def test_files_are_valid_json_one_per_preset_and_no_temp_files_remain(self):
        self.store.create(smug())
        files = os.listdir(self.store.folder)
        self.assertEqual(len([f for f in files if f.endswith(".json")]), 15)
        self.assertEqual([f for f in files if f.endswith(".tmp")], [])
        with open(os.path.join(self.store.folder, "test_smug.json")) as fp:
            self.assertEqual(json.load(fp)["name"], "test_smug")

    def test_parallel_writes_do_not_corrupt_anything(self):
        def worker(i):
            for j in range(10):
                self.store.create(smug(name=f"par_{i}_{j}"))
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(self.store.list()), 14 + 50)


class ApiTest(unittest.TestCase):
    TOKEN = "s3cret"

    def make_client(self, token=None):
        from flask import Flask
        pa = importlib.import_module("MIA.presets_api")
        self.pa = pa
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        app = Flask("test")
        cfg = {"presets_dir": os.path.join(tmp.name, "presets"), "editor_token": token or "",   # "" = no token
               "editor_token_file": os.path.join(tmp.name, "token.txt")}
        self.store = pa.init_presets_api(app, cfg, REPO, allowed_origins=lambda: ["http://good.example:8585"])
        return app.test_client()

    def test_list_and_read(self):
        http = self.make_client()
        data = http.get("/api/presets").get_json()
        self.assertEqual(len(data["presets"]), 14)
        self.assertEqual(data["token_required"], False)
        self.assertEqual(data["version"], self.store.version())
        self.assertIn("idle", data["protected"])        # used by MIA's expressions.json
        self.assertEqual(http.get("/api/presets/smug").get_json()["name"], "smug")
        self.assertEqual(http.get("/api/presets/nope").status_code, 404)
        self.assertEqual(http.get("/api/presets/version").get_json()["version"], data["version"])

    def test_metadata(self):
        http = self.make_client()
        keys = http.get("/api/shape-keys").get_json()
        self.assertEqual(len(keys["shape_keys"]), 57)
        self.assertEqual(keys["categories"], ["eyes", "brows", "mouth", "other"])
        gestures = http.get("/api/gestures").get_json()["gestures"]
        self.assertIn("wave", [g["name"] for g in gestures])
        self.assertEqual(len(gestures), 13)

    def test_create_update_rename_delete_over_http(self):
        http = self.make_client()
        r = http.post("/api/presets", json=smug())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["preset"]["name"], "test_smug")
        self.assertEqual(http.post("/api/presets", json=smug()).status_code, 409)
        r = http.put("/api/presets/test_smug", json=smug(description="new"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(http.get("/api/presets/test_smug").get_json()["description"], "new")
        r = http.put("/api/presets/test_smug", json=smug(name="test_renamed"))
        self.assertEqual(r.get_json()["preset"]["name"], "test_renamed")
        self.assertEqual(http.get("/api/presets/test_smug").status_code, 404)
        self.assertEqual(http.delete("/api/presets/test_renamed").status_code, 200)
        self.assertEqual(http.delete("/api/presets/test_renamed").status_code, 404)

    def test_corrections_are_reported(self):
        http = self.make_client()
        r = http.post("/api/presets", json=smug(weights={"Fcl_MTH_Fun": 5, "Bogus": 1}))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.get_json()["corrections"]), 2)

    def test_protected_presets_need_force(self):
        http = self.make_client()
        r = http.delete("/api/presets/idle")
        self.assertEqual(r.status_code, 409)
        self.assertIn("MIA", r.get_json()["error"])
        self.assertEqual(http.delete("/api/presets/idle?force=1").status_code, 200)

    def test_errors_are_json(self):
        http = self.make_client()
        for r in [http.post("/api/presets", json=smug(name="bad name")), http.get("/api/presets/nope"),
                  http.post("/api/presets", data="not json", content_type="application/json")]:
            self.assertGreaterEqual(r.status_code, 400)
            self.assertIn("error", r.get_json())

    def test_writes_need_json_not_form_posts(self):
        http = self.make_client()
        r = http.post("/api/presets", data=json.dumps(smug()), content_type="text/plain")
        self.assertEqual(r.status_code, 415)
        r = http.post("/api/presets", data={"name": "x"})      # a plain html form from another site
        self.assertEqual(r.status_code, 415)
        self.assertEqual(len(self.store.names()), 14)

    def test_origin_rules(self):
        http = self.make_client()
        evil = http.post("/api/presets", json=smug(), headers={"Origin": "http://evil.example"})
        self.assertEqual(evil.status_code, 403)
        listed = http.post("/api/presets", json=smug(name="test_a"), headers={"Origin": "http://good.example:8585"})
        self.assertEqual(listed.status_code, 201)
        # same origin as the host that was asked (works for any name the page was reached by)
        same = http.post("/api/presets", json=smug(name="test_b"), headers={"Origin": "https://mia.tailnet.example", "Host": "mia.tailnet.example"})
        self.assertEqual(same.status_code, 201)
        none = http.post("/api/presets", json=smug(name="test_c"))   # no Origin: Godot on the desktop, scripts
        self.assertEqual(none.status_code, 201)
        self.assertEqual(http.delete("/api/presets/test_a", headers={"Origin": "http://evil.example"}).status_code, 403)

    def test_token(self):
        http = self.make_client(token=self.TOKEN)
        self.assertTrue(http.get("/api/presets").get_json()["token_required"])
        self.assertEqual(len(http.get("/api/presets").get_json()["presets"]), 14)      # reading is open
        self.assertEqual(http.post("/api/presets", json=smug()).status_code, 401)
        self.assertEqual(http.post("/api/presets", json=smug(), headers={"X-MIA-Token": "wrong"}).status_code, 401)
        self.assertEqual(http.post("/api/presets", json=smug(), headers={"X-MIA-Token": self.TOKEN}).status_code, 201)
        self.assertEqual(http.put("/api/presets/test_smug", json=smug(), headers={"X-MIA-Token": "x"}).status_code, 401)
        self.assertEqual(http.delete("/api/presets/test_smug").status_code, 401)
        self.assertEqual(http.delete("/api/presets/test_smug", headers={"X-MIA-Token": self.TOKEN}).status_code, 200)

    def test_oversized_body_is_refused(self):
        http = self.make_client()
        r = http.post("/api/presets", json=smug(description="x" * 100000))
        self.assertEqual(r.status_code, 413)


class TokenDefaultTest(unittest.TestCase):
    """without "editor_token" in the configuration a token is generated and kept outside of it"""

    def make(self, **cfg_extra):
        from flask import Flask
        pa = importlib.import_module("MIA.presets_api")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        token_file = os.path.join(tmp.name, "data", "token.txt")
        cfg = {"presets_dir": os.path.join(tmp.name, "presets"), "editor_token_file": token_file}
        cfg.update(cfg_extra)
        app = Flask("test")
        pa.init_presets_api(app, cfg, REPO)
        return app, app.test_client(), token_file, cfg

    def test_a_token_is_generated_and_required(self):
        app, http, token_file, _ = self.make()
        token, source = app.config["EDITOR_TOKEN_INFO"]
        self.assertGreaterEqual(len(token), 16)
        self.assertEqual(source, token_file)
        with open(token_file) as fp:
            self.assertEqual(fp.read().strip(), token)
        self.assertEqual(oct(os.stat(token_file).st_mode & 0o777), "0o600")          # only the owner can read it
        self.assertTrue(http.get("/api/presets").get_json()["token_required"])
        self.assertEqual(http.post("/api/presets", json=smug()).status_code, 401)
        self.assertEqual(http.post("/api/presets", json=smug(), headers={"X-MIA-Token": token}).status_code, 201)

    def test_the_token_stays_the_same_after_a_restart(self):
        app, _, token_file, cfg = self.make()
        first = app.config["EDITOR_TOKEN_INFO"][0]
        from flask import Flask
        pa = importlib.import_module("MIA.presets_api")
        again = Flask("again")
        pa.init_presets_api(again, cfg, REPO)
        self.assertEqual(again.config["EDITOR_TOKEN_INFO"][0], first)

    def test_configured_token_wins_over_the_file(self):
        app, http, token_file, _ = self.make(editor_token="from-config")
        self.assertEqual(app.config["EDITOR_TOKEN_INFO"], ("from-config", "setup_cfg.json"))
        self.assertFalse(os.path.exists(token_file))                                      # nothing is generated
        self.assertEqual(http.post("/api/presets", json=smug(), headers={"X-MIA-Token": "from-config"}).status_code, 201)

    def test_the_token_can_be_switched_off(self):
        for off in ["", "  ", False, None]:
            app, http, token_file, _ = self.make(editor_token=off)
            self.assertIsNone(app.config["EDITOR_TOKEN_INFO"][0], repr(off))
            self.assertFalse(http.get("/api/presets").get_json()["token_required"])
            self.assertEqual(http.post("/api/presets", json=smug()).status_code, 201)
            self.assertFalse(os.path.exists(token_file))

    def test_the_token_file_is_not_under_version_control(self):
        ignore = open(os.path.join(REPO, ".gitignore")).read()
        self.assertIn("data/", ignore)    # data/editor_token.txt is the default place


class WebAppWiring(unittest.TestCase):
    def test_the_real_app_serves_the_api(self):
        os.environ.setdefault("MIA_TEST", "1")
        wa = importlib.import_module("MIA.web_app")
        r = wa.app.test_client().get("/api/presets/version")
        self.assertEqual(r.status_code, 200)
        self.assertIn("version", r.get_json())

    def test_defaults_are_the_same_presets_the_character_ships(self):
        with open(os.path.join(SHIPPED, "library.json")) as fp:
            shipped = {p["name"] for p in json.load(fp)["presets"]}
        with open(os.path.join(REPO, "expressions.json")) as fp:
            expressions = json.load(fp)
        used = {e.get("preset", k) for k, e in expressions.items()}
        self.assertTrue(used <= shipped, used - shipped)


if __name__ == "__main__":
    unittest.main(verbosity=2)
