"""
Tests for gestures made of angles: the pose model (ranges, clamping), the gesture store (files, names, rules), the REST API (token, origin,
errors, the shared version) and the link to presets and the expression generator. Run with the MIA virtualenv: python tests/test_gestures_api.py
"""
import importlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

SHIPPED = os.path.join(REPO, "ui", "godot", "presets")


def cheer(**changes):
    gesture = {"name": "cheer_v", "description": "arms up in a V", "expression": "happy", "reach": 0.5, "hold": 1.0,
               "pose": {"R": {"upper_raise": 150, "upper_direction": 20, "elbow_bend": 20, "hand_turn": 90, "fingers": "open"},
                        "L": {"upper_raise": 150, "upper_direction": 20, "elbow_bend": 20, "hand_turn": 90, "fingers": "open"},
                        "torso": {"torso_lean": -5}}}
    gesture.update(changes)
    return gesture


class PoseModelTest(unittest.TestCase):
    def setUp(self):
        self.pm = importlib.import_module("MIA.pose_model")

    def test_neutral_values_are_inside_their_ranges(self):
        for table in (self.pm.ARM_PARAMS, self.pm.TORSO_PARAMS):
            for name, (_, _, low, high, neutral, text) in table.items():
                self.assertLessEqual(low, neutral, name)
                self.assertLessEqual(neutral, high, name)
                self.assertTrue(text)

    def test_the_description_is_what_the_editor_needs(self):
        d = self.pm.describe()
        self.assertEqual(d["sides"], ["R", "L"])
        self.assertEqual([p["name"] for p in d["arm"]], ["upper_raise", "upper_direction", "elbow_bend", "elbow_turn", "hand_turn", "wrist"])
        self.assertEqual([p["name"] for p in d["torso"]], ["torso_lean", "torso_side", "torso_turn"])
        self.assertEqual(d["fingers"]["keys"], ["thumb", "index", "middle", "ring", "little"])
        self.assertEqual(d["timing"]["reach"]["default"], 0.6)
        json.dumps(d)

    def test_the_copy_for_the_character_is_current(self):
        """ui/godot/presets/pose_model.json is what the editor builds its sliders from: python tools/export_pose_model.py writes it"""
        with open(os.path.join(SHIPPED, "pose_model.json"), encoding="utf-8") as fp:
            self.assertEqual(json.load(fp), json.loads(json.dumps(self.pm.describe())))

    def test_only_what_is_given_is_kept(self):
        pose, corrections = self.pm.normalize_pose({"R": {"upper_raise": 90}})
        self.assertEqual(pose, {"R": {"upper_raise": 90.0}})
        self.assertEqual(corrections, [])

    def test_values_are_clamped_and_unknown_things_removed_with_messages(self):
        pose, corrections = self.pm.normalize_pose({"R": {"upper_raise": 400, "elbow_bend": -5, "wiggle": 3, "wrist": "high"},
                                                    "torso": {"torso_lean": 99, "dance": 1}, "legs": {"x": 1}, "L": 5})
        self.assertEqual(pose, {"R": {"upper_raise": 180.0, "elbow_bend": 0.0}, "torso": {"torso_lean": 30.0}})
        text = " | ".join(corrections)
        for expected in ("R.upper_raise clamped", "R.elbow_bend clamped", "unknown setting 'R.wiggle'", "R.wrist is not a number", "torso.torso_lean clamped",
                         "torso.dance", "unknown part 'legs'", "L is not an object"):
            self.assertIn(expected, text)

    def test_fingers_as_a_name_or_as_curls(self):
        pose, corrections = self.pm.normalize_pose({"R": {"fingers": "fist"}, "L": {"fingers": {"index": 0, "thumb": 140, "toe": 5, "ring": "x"}}})
        self.assertEqual(pose["R"], {"fingers": "fist"})
        self.assertEqual(pose["L"], {"fingers": {"index": 0.0, "thumb": 100.0}})
        self.assertTrue(any("toe" in c for c in corrections))
        pose, corrections = self.pm.normalize_pose({"R": {"fingers": "claw", "upper_raise": 10}, "L": {"fingers": 5}})
        self.assertEqual(pose, {"R": {"upper_raise": 10.0}})
        self.assertEqual(len(corrections), 2)

    def test_garbage_does_not_raise(self):
        for raw in (None, 5, "pose", [], {"R": None}):
            pose, corrections = self.pm.normalize_pose(raw)
            self.assertEqual(pose, {})
            self.assertTrue(corrections or raw == {"R": None})

    def test_timing_defaults_and_limits(self):
        self.assertEqual(self.pm.normalize_timing({})[:2], (0.6, 1.5))
        reach, hold, corrections = self.pm.normalize_timing({"reach": 0.01, "hold": 99})
        self.assertEqual((reach, hold), (0.2, 8.0))
        self.assertEqual(len(corrections), 2)
        self.assertEqual(self.pm.normalize_timing({"reach": "fast"})[0], 0.6)


class StoreBase(unittest.TestCase):
    def setUp(self):
        self.gs = importlib.import_module("MIA.gesture_store")
        self.ps = importlib.import_module("MIA.preset_store")
        self.tmp = tempfile.TemporaryDirectory()
        self.users = []
        self.store = self.gs.GestureStore(os.path.join(self.tmp.name, "gestures"), shipped_file=os.path.join(SHIPPED, "gestures.json"),
                                          in_use=lambda name: self.users if name == "cheer_v" else [],
                                          expression_names=lambda: ["happy", "sad", "idle"])

    def tearDown(self):
        self.tmp.cleanup()


class StoreTest(StoreBase):
    def test_the_gestures_of_the_character_are_listed_but_read_only(self):
        shipped = self.store.shipped_names()
        self.assertIn("wave", shipped)
        self.assertIn("hands_behind_back", shipped)
        self.assertEqual(len(shipped), 14)
        for name in ("wave", "cheer"):
            with self.assertRaises(self.ps.PresetError) as raised:
                self.store.delete(name)
            self.assertEqual(raised.exception.status, 409)
            with self.assertRaises(self.ps.PresetError):
                self.store.update(name, cheer(name=name))
            with self.assertRaises(self.ps.PresetError):
                self.store.create(cheer(name=name))

    def test_create_read_list(self):
        stored, corrections = self.store.create(cheer())
        self.assertEqual(corrections, [])
        self.assertEqual(stored["kind"], "pose")
        self.assertEqual(stored["source"], "manual")
        self.assertIn("updated", stored)
        self.assertEqual(self.store.get("cheer_v")["pose"]["torso"], {"torso_lean": -5.0})
        self.assertEqual(self.store.names(), ["cheer_v"])
        self.assertEqual(len(self.store.all_names()), 15)
        self.assertEqual([g["name"] for g in self.store.list()], ["cheer_v"])
        described = {g["name"]: g for g in self.store.describe_all()}
        self.assertTrue(described["wave"]["builtin"])
        self.assertFalse(described["cheer_v"]["builtin"])
        self.assertEqual(described["cheer_v"]["kind"], "pose")

    def test_a_name_is_used_once(self):
        self.store.create(cheer())
        with self.assertRaises(self.ps.PresetError) as raised:
            self.store.create(cheer())
        self.assertEqual(raised.exception.status, 409)

    def test_names_are_checked_like_presets(self):
        for name in ("", "has space", "../x", "a" * 41, None, 5):
            with self.assertRaises(self.ps.PresetError):
                self.store.create(cheer(name=name))

    def test_an_empty_pose_is_refused(self):
        for pose in ({}, {"R": {}}, {"R": {"nonsense": 1}}, None):
            with self.assertRaises(self.ps.PresetError) as raised:
                self.store.create(cheer(pose=pose))
            self.assertEqual(raised.exception.status, 400)

    def test_corrections_are_reported_and_the_gesture_is_still_saved(self):
        stored, corrections = self.store.create(cheer(reach=0.0, hold=50, expression="nope", source="robot",
                                                      pose={"R": {"upper_raise": 999}}))
        self.assertEqual(stored["reach"], 0.2)
        self.assertEqual(stored["hold"], 8.0)
        self.assertEqual(stored["expression"], "")
        self.assertEqual(stored["source"], "manual")
        self.assertEqual(stored["pose"], {"R": {"upper_raise": 180.0}})
        self.assertGreaterEqual(len(corrections), 4)

    def test_update_and_rename(self):
        self.store.create(cheer())
        stored, _ = self.store.update("cheer_v", cheer(description="changed"))
        self.assertEqual(stored["description"], "changed")
        stored, _ = self.store.update("cheer_v", cheer(name="cheer_w"))
        self.assertEqual(self.store.names(), ["cheer_w"])
        with self.assertRaises(self.ps.PresetError) as raised:
            self.store.update("nothing", cheer(name="nothing"))
        self.assertEqual(raised.exception.status, 404)

    def test_a_gesture_in_use_is_not_renamed_or_deleted_by_accident(self):
        self.store.create(cheer())
        self.users = ["happy"]
        with self.assertRaises(self.ps.PresetError) as raised:
            self.store.delete("cheer_v")
        self.assertEqual(raised.exception.status, 409)
        self.assertIn("happy", raised.exception.message)
        with self.assertRaises(self.ps.PresetError):
            self.store.update("cheer_v", cheer(name="cheer_w"))
        self.store.delete("cheer_v", force=True)
        self.assertEqual(self.store.names(), [])

    def test_the_version_changes_with_every_change(self):
        versions = {self.store.version()}
        self.store.create(cheer())
        versions.add(self.store.version())
        self.store.update("cheer_v", cheer(description="x"))
        versions.add(self.store.version())
        self.store.delete("cheer_v")
        versions.add(self.store.version())
        self.assertEqual(len(versions), 3)           # empty again = the first version
        self.assertEqual(self.store.version(), self.store.version())

    def test_no_half_written_files_and_unreadable_files_are_skipped(self):
        self.store.create(cheer())
        self.assertEqual([f for f in os.listdir(self.store.folder) if f.endswith(".tmp")], [])
        with open(os.path.join(self.store.folder, "broken.json"), "w") as fp:
            fp.write("{not json")
        self.assertEqual([g["name"] for g in self.store.list()], ["cheer_v"])


class PresetLinkTest(StoreBase):
    def test_a_preset_may_use_a_gesture_of_the_editor_as_long_as_it_exists(self):
        presets = self.ps.PresetStore(os.path.join(self.tmp.name, "presets"), shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"),
                                      gestures_provider=self.store.all_names)
        raw = {"name": "joy", "weights": {"Fcl_MTH_Joy": 0.8}, "gesture": "cheer_v"}
        preset, corrections = presets.normalize(raw)
        self.assertEqual(preset["gesture"], "")
        self.assertTrue(any("unknown gesture" in c for c in corrections))
        self.store.create(cheer())
        preset, corrections = presets.normalize(raw)
        self.assertEqual(preset["gesture"], "cheer_v")
        self.assertEqual(corrections, [])
        self.assertEqual(presets.normalize(dict(raw, gesture="wave"))[0]["gesture"], "wave")


class GeneratorLinkTest(StoreBase):
    def test_the_model_may_choose_the_gestures_of_the_editor(self):
        llm = importlib.import_module("MIA.expression_llm")
        presets = self.ps.PresetStore(os.path.join(self.tmp.name, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
                                      shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_provider=self.store.all_names)
        generator = llm.ExpressionGenerator(presets, lambda m, s: "{}", os.path.join(SHIPPED, "shape_keys.json"), None,
                                            gestures_provider=self.store.describe_all)
        self.assertNotIn("cheer_v", generator.schema()["properties"]["gesture"]["enum"])
        self.store.create(cheer())
        self.assertIn("cheer_v", generator.schema()["properties"]["gesture"]["enum"])
        self.assertIn("cheer_v", generator.messages("happy")[0]["content"])


class ApiTest(unittest.TestCase):
    def make_client(self, token="s3cret"):
        from flask import Flask
        pa = importlib.import_module("MIA.presets_api")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        app = Flask("test")
        cfg = {"presets_dir": os.path.join(self.tmp.name, "presets"), "gestures_dir": os.path.join(self.tmp.name, "gestures"),
               "editor_token": token, "editor_token_file": os.path.join(self.tmp.name, "token.txt")}
        self.store = pa.init_presets_api(app, cfg, REPO, allowed_origins=lambda: ["http://good.example:8585"])
        self.headers = {"X-MIA-Token": token}
        return app.test_client()

    def test_the_pose_model_is_served(self):
        http = self.make_client()
        data = http.get("/api/pose-model").get_json()
        self.assertEqual(len(data["arm"]), 6)
        self.assertEqual(len(data["torso"]), 3)

    def test_list_has_both_kinds(self):
        http = self.make_client()
        data = http.get("/api/gestures").get_json()
        self.assertEqual(len(data["gestures"]), 14)
        self.assertEqual(data["pose_gestures"], [])
        self.assertTrue(data["token_required"])
        self.assertEqual(http.post("/api/gestures", json=cheer(), headers=self.headers).status_code, 201)
        data = http.get("/api/gestures").get_json()
        self.assertEqual(len(data["gestures"]), 15)
        self.assertEqual([g["name"] for g in data["pose_gestures"]], ["cheer_v"])
        self.assertEqual(data["pose_gestures"][0]["pose"]["R"]["upper_raise"], 150.0)

    def test_create_update_rename_delete_over_http(self):
        http = self.make_client()
        response = http.post("/api/gestures", json=cheer(pose={"R": {"upper_raise": 999}}), headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["gesture"]["pose"], {"R": {"upper_raise": 180.0}})
        self.assertTrue(response.get_json()["corrections"])
        self.assertEqual(http.get("/api/gestures/cheer_v").get_json()["name"], "cheer_v")
        self.assertEqual(http.put("/api/gestures/cheer_v", json=cheer(description="new"), headers=self.headers).get_json()["gesture"]["description"], "new")
        renamed = http.put("/api/gestures/cheer_v", json=cheer(name="cheer_w"), headers=self.headers)
        self.assertEqual(renamed.get_json()["gesture"]["name"], "cheer_w")
        self.assertEqual(http.get("/api/gestures/cheer_v").status_code, 404)
        self.assertEqual(http.delete("/api/gestures/cheer_w", headers=self.headers).status_code, 200)
        self.assertEqual(http.get("/api/gestures").get_json()["pose_gestures"], [])

    def test_writing_needs_token_json_and_a_known_origin(self):
        http = self.make_client()
        self.assertEqual(http.post("/api/gestures", json=cheer()).status_code, 401)
        self.assertEqual(http.post("/api/gestures", json=cheer(), headers={"X-MIA-Token": "wrong"}).status_code, 401)
        self.assertEqual(http.post("/api/gestures", data="x", headers=self.headers).status_code, 415)
        foreign = dict(self.headers, Origin="http://evil.example")
        self.assertEqual(http.post("/api/gestures", json=cheer(), headers=foreign).status_code, 403)
        self.assertEqual(http.delete("/api/gestures/x").status_code, 401)
        self.assertEqual(http.put("/api/gestures/x", json=cheer()).status_code, 401)
        self.assertEqual(http.get("/api/gestures").status_code, 200)         # reading is open

    def test_errors_are_json_with_the_right_status(self):
        http = self.make_client()
        self.assertEqual(http.post("/api/gestures", json=cheer(name="wave"), headers=self.headers).status_code, 409)
        self.assertEqual(http.delete("/api/gestures/wave", headers=self.headers).status_code, 409)
        self.assertEqual(http.put("/api/gestures/wave", json=cheer(name="wave"), headers=self.headers).status_code, 409)
        self.assertEqual(http.post("/api/gestures", json=cheer(pose={}), headers=self.headers).status_code, 400)
        self.assertEqual(http.post("/api/gestures", json=cheer(name="bad name"), headers=self.headers).status_code, 400)
        self.assertEqual(http.get("/api/gestures/nope").status_code, 404)
        self.assertEqual(http.delete("/api/gestures/nope", headers=self.headers).status_code, 404)
        self.assertIn("error", http.get("/api/gestures/nope").get_json())

    def test_the_shared_version_covers_presets_and_gestures(self):
        http = self.make_client()
        before = http.get("/api/presets/version").get_json()["version"]
        self.assertEqual(http.get("/api/presets").get_json()["version"], before)
        http.post("/api/gestures", json=cheer(), headers=self.headers)
        after_gesture = http.get("/api/presets/version").get_json()["version"]
        self.assertNotEqual(after_gesture, before)
        http.post("/api/presets", json={"name": "joy", "weights": {"Fcl_MTH_Joy": 0.8}}, headers=self.headers)
        self.assertNotEqual(http.get("/api/presets/version").get_json()["version"], after_gesture)
        self.assertEqual(http.get("/api/presets").get_json()["version"], http.get("/api/presets/version").get_json()["version"])

    def test_a_preset_with_the_new_gesture_and_the_protection_of_gestures_in_use(self):
        http = self.make_client()
        http.post("/api/gestures", json=cheer(), headers=self.headers)
        created = http.post("/api/presets", json={"name": "joy", "weights": {"Fcl_MTH_Joy": 0.8}, "gesture": "cheer_v"}, headers=self.headers)
        self.assertEqual(created.get_json()["preset"]["gesture"], "cheer_v")
        refused = http.delete("/api/gestures/cheer_v", headers=self.headers)
        self.assertEqual(refused.status_code, 409)
        self.assertIn("joy", refused.get_json()["error"])
        self.assertEqual(http.delete("/api/gestures/cheer_v?force=1", headers=self.headers).status_code, 200)


if __name__ == "__main__":
    unittest.main()
