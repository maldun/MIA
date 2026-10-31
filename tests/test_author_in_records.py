"""
The account of a change goes into the record itself (REQ-API-009; owner decision 2026-10-27): presets and gestures get `updated_by` next to `updated`, a chat
message gets `sender`. Without an account (the old, open backend) nothing is added, and a client cannot write the field itself.
Run in the image: bash tools/run_in_image.sh tests/test_author_in_records.py
"""
import importlib
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
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                              # noqa: E402

SHIPPED = os.path.join(REPO, "ui", "godot", "presets")


def preset(**changes):
    data = {"name": "test_smug", "description": "confident", "weights": {"Fcl_MTH_Fun": 0.6}, "bones": {"head_roll": 3.0}, "gesture": "hand_on_hip",
            "speaking": False, "tags": ["smug"], "source": "manual"}
    data.update(changes)
    return data


def gesture(**changes):
    data = {"name": "cheer_v", "description": "arms up", "expression": "happy", "reach": 0.5, "hold": 1.0,
            "pose": {"R": {"upper_raise": 150, "upper_direction": 20, "elbow_bend": 20, "hand_turn": 90, "fingers": "open"},
                     "L": {"upper_raise": 150, "upper_direction": 20, "elbow_bend": 20, "hand_turn": 90, "fingers": "open"}, "torso": {"torso_lean": -5}}}
    data.update(changes)
    return data


class Presets(unittest.TestCase):
    def setUp(self):
        self.ps = importlib.import_module("MIA.preset_store")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = self.ps.PresetStore(os.path.join(self.tmp.name, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
                                         shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_file=os.path.join(SHIPPED, "gestures.json"))

    @mark.req("REQ-API-009")
    def test_create_and_update_record_who_did_it(self):
        """TC-API-009: a preset records the account that made it and the account that changed it last, in the file and in the answer.

        Example: anna creates test_smug -> updated_by anna; ben updates it -> updated_by ben, description warmer.
        """
        # When / Then: anna creates it
        stored, _ = self.store.create(preset(), author="anna")
        self.assertEqual(stored["updated_by"], "anna")
        self.assertEqual(self.store.get("test_smug")["updated_by"], "anna")                       # it is in the file, not only in the answer
        # When / Then: ben changes it
        stored, _ = self.store.update("test_smug", preset(description="warmer"), author="ben")
        self.assertEqual((stored["updated_by"], self.store.get("test_smug")["description"]), ("ben", "warmer"))

    def test_without_an_account_nothing_is_added_and_a_client_cannot_write_the_field(self):
        """TC-API-009: without an account a preset gets no updated_by, even when the client sends one; with an account the field names the account, not what the client sent.

        Example: create with updated_by mallory and no account -> no updated_by; update by anna with updated_by mallory -> updated_by anna.
        """
        # When / Then: a client's own updated_by is dropped without an account
        stored, _ = self.store.create(preset(updated_by="mallory"))
        self.assertNotIn("updated_by", stored)
        self.assertNotIn("updated_by", self.store.get("test_smug"))
        # When / Then: with an account the account wins
        stored, _ = self.store.update("test_smug", dict(preset(), updated_by="mallory"), author="anna")
        self.assertEqual(stored["updated_by"], "anna")                                              # the account, not what the client sent

    def test_a_rename_keeps_the_new_author(self):
        """TC-API-009: a preset renamed by another account names that account as its author under the new name.

        Example: anna creates test_smug, ben renames it test_smug2 -> name test_smug2, updated_by ben.
        """
        # Given: anna's preset
        self.store.create(preset(), author="anna")
        # When: ben renames it
        stored, _ = self.store.update("test_smug", preset(name="test_smug2"), author="ben")
        # Then: the new name carries ben
        self.assertEqual((stored["name"], stored["updated_by"]), ("test_smug2", "ben"))


class Gestures(unittest.TestCase):
    def setUp(self):
        self.gs = importlib.import_module("MIA.gesture_store")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = self.gs.GestureStore(os.path.join(self.tmp.name, "gestures"), shipped_file=os.path.join(SHIPPED, "gestures.json"),
                                          in_use=lambda name: [], expression_names=lambda: ["happy", "sad", "idle"])

    @mark.req("REQ-API-009")
    def test_create_and_update_record_who_did_it(self):
        """TC-API-009: a gesture records the account that made it and the account that changed it last.

        Example: anna creates cheer_v -> updated_by anna; ben updates it -> updated_by ben.
        """
        # When / Then: anna creates it, ben changes it
        stored, _ = self.store.create(gesture(), author="anna")
        self.assertEqual(stored["updated_by"], "anna")
        stored, _ = self.store.update("cheer_v", gesture(description="arms way up"), author="ben")
        self.assertEqual(stored["updated_by"], "ben")

    def test_without_an_account_nothing_is_added(self):
        """TC-API-009: without an account a gesture gets no updated_by, also when the client sends one.

        Example: create cheer_v with updated_by mallory and no account -> no updated_by.
        """
        stored, _ = self.store.create(gesture(updated_by="mallory"))
        self.assertNotIn("updated_by", stored)


class Api(unittest.TestCase):
    """the blueprint passes the account of the request (g.account, set by the accounts guard) to the stores"""

    def setUp(self):
        from flask import Flask, g, request
        pa = importlib.import_module("MIA.presets_api")
        ps = importlib.import_module("MIA.preset_store")
        gs = importlib.import_module("MIA.gesture_store")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        presets = ps.PresetStore(os.path.join(self.tmp.name, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
                                 shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_file=os.path.join(SHIPPED, "gestures.json"))
        gestures = gs.GestureStore(os.path.join(self.tmp.name, "gestures"), shipped_file=os.path.join(SHIPPED, "gestures.json"),
                                   in_use=lambda name: [], expression_names=lambda: ["happy", "sad", "idle"])
        self.app = Flask(__name__)
        self.app.register_blueprint(pa.create_blueprint(presets, os.path.join(REPO, "ui", "godot"), gestures=gestures))

        @self.app.before_request
        def who():                                           # what accounts_api does after the session check
            if request.headers.get("X-Test-Account"):
                g.account = request.headers["X-Test-Account"]

    @mark.req("REQ-API-009")
    def test_the_account_of_the_request_is_recorded_in_the_preset_and_the_gesture(self):
        """TC-API-009: the routes pass the account of the request (g.account) to the stores: the preset and the gesture made by anna and saved by ben name each of them.

        Example: POST /api/presets as anna -> updated_by anna; PUT as ben -> updated_by ben; the same for /api/gestures.
        """
        # Given: a browser that names its account per request
        client = self.app.test_client()
        # When / Then: anna makes the preset, ben saves it
        made = client.post("/api/presets", json=preset(), headers={"X-Test-Account": "anna"}).get_json()["preset"]
        self.assertEqual(made["updated_by"], "anna")
        saved = client.put("/api/presets/test_smug", json=preset(description="softer"), headers={"X-Test-Account": "ben"}).get_json()["preset"]
        self.assertEqual(saved["updated_by"], "ben")
        # When / Then: anna makes the gesture, ben saves it
        gesture_made = client.post("/api/gestures", json=gesture(), headers={"X-Test-Account": "anna"}).get_json()["gesture"]
        self.assertEqual(gesture_made["updated_by"], "anna")
        gesture_saved = client.put("/api/gestures/cheer_v", json=gesture(description="more"), headers={"X-Test-Account": "ben"}).get_json()["gesture"]
        self.assertEqual(gesture_saved["updated_by"], "ben")

    def test_without_an_account_the_record_is_as_before(self):
        """TC-API-009: a preset made without an account (the open backend) has no updated_by, as before.

        Example: POST /api/presets {name: plain} without an account -> no updated_by.
        """
        made = self.app.test_client().post("/api/presets", json=preset(name="plain")).get_json()["preset"]
        self.assertNotIn("updated_by", made)


class Messages(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.service_module = importlib.import_module("MIA.chat_service")
        self.moods = importlib.import_module("MIA.moods")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = self.chat_log.ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.gate = threading.Event()
        self.service = self.service_module.ChatService(
            lambda event, payload: None, self.log, self.moods.MoodTracker(os.path.join(self.tmp.name, "moods.json")),
            lambda text, on_delta, on_emotion, should_stop: (on_delta("ok"), "ok")[1], model_info=lambda: ("test-model", "full"), clock=time.monotonic)

    def user_records(self):
        return [r for r in self.log.history(limit=100)[0] if r["role"] == "user"]

    @mark.req("REQ-API-009")
    def test_a_message_carries_the_sender_account_and_the_rate_key_is_separate(self):
        """TC-API-009: a chat message names its account as sender in the acknowledgement and in the log; the connection id is only the rate key and is not stored.

        Example: send(hello, sender sid-1, author anna) -> message.sender anna; the stored record has sender anna and no sid-1.
        """
        # When: anna sends over the connection sid-1
        ack = self.service.send("hello", client_id="c1", sender="sid-1", author="anna")
        # Then: the acknowledgement and the log name anna, never the connection
        self.assertTrue(ack["ok"])
        self.assertEqual(ack["message"]["sender"], "anna")
        stored = [r for r in self.user_records() if r["text"] == "hello"][0]
        self.assertEqual(stored["sender"], "anna")                                                 # in the log
        self.assertNotIn("sid-1", str(stored))                                                     # the connection id is a rate key, not a name

    def test_without_an_account_the_message_has_no_sender(self):
        """TC-API-009: without an account a chat message has no sender.

        Example: send(hello again, sender sid-1) -> the message has no sender.
        """
        ack = self.service.send("hello again", sender="sid-1")
        self.assertNotIn("sender", ack["message"])


if __name__ == "__main__":
    unittest.main()
