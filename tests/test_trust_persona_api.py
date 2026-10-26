"""Trust of sources and the persona for the page (IF-101 v1 trust, set_trust, persona, save_persona): the routes of templates/static/chat/api.js,
the events trust_changed and persona_changed. The persona is a file, trust is the override file of source_trust.py (the default table stays untouched).
Needs flask: bash tools/run_in_image.sh tests/test_trust_persona_api.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, g                                          # noqa: E402
from source_trust import DEFAULT_FILE, TrustTable                   # noqa: E402
from trust_persona_api import create_trust_persona_blueprint        # noqa: E402


class TrustPersonaApiTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.trust_file = os.path.join(self.dir, "data", "source_trust.json")
        self.persona_file = os.path.join(self.dir, "data", "persona.json")
        self.events = []
        self.account = ["anna"]
        app = Flask(__name__)

        @app.before_request
        def who():
            g.account = self.account[0]

        app.register_blueprint(create_trust_persona_blueprint(self.trust_file, self.persona_file, lambda e, p: self.events.append((e, p))))
        self.client = app.test_client()
        self.default = {k: v["prior"] for k, v in TrustTable.load(DEFAULT_FILE).classes.items()}

    def test_trust_lists_the_default_table_as_source_to_value(self):
        got = self.client.get("/api/trust")
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.get_json(), self.default)

    def test_set_trust_returns_old_and_new_announces_and_is_read_back(self):
        old = self.default["blog"]
        got = self.client.post("/api/trust", json={"source": "blog", "value": 0.1})
        self.assertEqual((got.status_code, got.get_json()), (200, {"source": "blog", "old": old, "new": 0.1}))
        self.assertEqual(self.events, [("trust_changed", {"source": "blog", "old": old, "new": 0.1, "author": "anna"})])
        self.assertEqual(self.client.get("/api/trust").get_json()["blog"], 0.1)
        self.assertEqual(self.client.get("/api/trust").get_json()["journal"], self.default["journal"])

    def test_the_change_goes_into_the_override_file_and_the_default_stays(self):
        self.client.post("/api/trust", json={"source": "blog", "value": 0.1})
        with open(self.trust_file, encoding="utf-8") as fp:
            entry = json.load(fp)["classes"]["blog"]
        self.assertEqual(entry["prior"], 0.1)
        self.assertTrue(entry["reason"])                                    # the reason of the default stays with the number
        self.assertEqual(TrustTable.load(DEFAULT_FILE).classes["blog"]["prior"], self.default["blog"])
        self.assertEqual(TrustTable.load(DEFAULT_FILE, self.trust_file).prior("blog")[0], 0.1)   # the pipelines read the new value

    def test_a_second_change_reports_the_value_it_replaced(self):
        self.client.post("/api/trust", json={"source": "blog", "value": 0.1})
        self.events.clear()
        got = self.client.post("/api/trust", json={"source": "blog", "value": 0.7}).get_json()
        self.assertEqual((got["old"], got["new"]), (0.1, 0.7))

    def test_refused_values_and_unknown_sources_store_nothing(self):
        for value in (-0.1, 1.1, "0.5", None, True, float("nan")):
            got = self.client.post("/api/trust", json={"source": "blog", "value": value})
            self.assertEqual((got.status_code, got.get_json()["error"]), (422, "invalid_trust"), value)
        got = self.client.post("/api/trust", json={"source": "no-such-source", "value": 0.5})
        self.assertEqual((got.status_code, got.get_json()["error"]), (404, "not_found"))
        self.assertEqual(self.events, [])
        self.assertFalse(os.path.exists(self.trust_file))

    def test_the_bounds_are_allowed(self):
        for value in (0, 1, 0.0, 1.0):
            self.assertEqual(self.client.post("/api/trust", json={"source": "blog", "value": value}).status_code, 200)

    def test_a_broken_override_file_is_not_a_crash(self):
        os.makedirs(os.path.dirname(self.trust_file))
        with open(self.trust_file, "w", encoding="utf-8") as fp:
            fp.write("{not json")
        self.assertEqual(self.client.get("/api/trust").get_json(), self.default)

    def test_persona_is_empty_at_first_then_saved_byte_for_byte(self):
        self.assertEqual(self.client.get("/api/persona").get_json(), {"text": ""})
        text = "  You are Mia.\n\tShort answers — «ß» é  \n"
        got = self.client.post("/api/persona", json={"doc": {"text": text}})
        self.assertEqual((got.status_code, got.get_json()), (200, {"text": text}))
        self.assertEqual(self.events, [("persona_changed", {"author": "anna"})])
        self.assertEqual(self.client.get("/api/persona").get_json(), {"text": text})
        with open(self.persona_file, encoding="utf-8") as fp:
            self.assertEqual(json.load(fp)["text"], text)

    def test_other_fields_of_the_document_are_kept(self):
        self.client.post("/api/persona", json={"doc": {"text": "x", "name": "Mia"}})
        self.assertEqual(self.client.get("/api/persona").get_json(), {"text": "x", "name": "Mia"})

    def test_a_blank_or_malformed_persona_is_refused_and_the_old_one_stays(self):
        self.client.post("/api/persona", json={"doc": {"text": "keep me"}})
        self.events.clear()
        for body in ({"doc": {"text": " \n"}}, {"doc": {"text": 5}}, {"doc": {}}, {"doc": "text"}, {}, {"doc": None}):
            got = self.client.post("/api/persona", json=body)
            self.assertEqual((got.status_code, got.get_json()["error"]), (422, "invalid_persona"), body)
        self.assertEqual(self.client.get("/api/persona").get_json(), {"text": "keep me"})
        self.assertEqual(self.events, [])

    def test_without_an_account_the_author_is_page(self):
        self.account[0] = None
        self.client.post("/api/persona", json={"doc": {"text": "x"}})
        self.assertEqual(self.events[0][1]["author"], "page")


if __name__ == "__main__":
    unittest.main()
