"""
Tests for who plays MIA's voice (audio_router.py and its use in web_app.py): one page plays, lines have their own files, an old "ended"
cannot delete a newer line, nothing is lost when pages come and go. Run with the MIA virtualenv: python tests/test_audio_router.py
"""
import importlib
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


class RouterTest(unittest.TestCase):
    def setUp(self):
        self.audio_router = importlib.import_module("MIA.audio_router")
        self.sent = []
        self.router = self.audio_router.AudioRouter(lambda event, payload, to=None: self.sent.append((event, payload, to)))

    def lines(self):
        return [(p["serial"], to) for e, p, to in self.sent if e == "audio_reload"]

    def test_nobody_connected_nobody_gets_a_line(self):
        self.assertIsNone(self.router.announce("/audio/a.wav", 1))
        self.assertEqual(self.sent, [])

    def test_a_single_page_gets_the_lines(self):
        self.router.connect("a")
        self.router.announce("/audio/a.wav", 1)
        self.assertEqual(self.lines(), [(1, "a")])

    def test_only_the_page_that_claimed_the_voice_gets_the_lines(self):
        for sid in ("a", "b", "c"):
            self.router.connect(sid)
        self.assertTrue(self.router.claim("b"))
        self.router.announce("/audio/x.wav", 1)
        self.router.announce("/audio/y.wav", 2)
        self.assertEqual(self.lines(), [(1, "b"), (2, "b")])

    def test_everybody_is_told_who_plays(self):
        self.router.connect("a")
        self.router.connect("b")
        self.router.claim("a")
        self.assertIn(("audio_owner", {"sid": "a"}, None), self.sent)

    def test_claiming_again_does_not_repeat_the_announcement(self):
        self.router.connect("a")
        self.router.claim("a")
        self.router.claim("a")
        self.assertEqual(len([e for e, _, _ in self.sent if e == "audio_owner"]), 1)

    def test_the_voice_moves_to_the_page_that_is_used_now(self):
        self.router.connect("a")
        self.router.connect("b")
        self.router.claim("a")
        self.router.claim("b")
        self.router.announce("/audio/x.wav", 1)
        self.assertEqual(self.lines(), [(1, "b")])

    def test_without_a_claim_the_page_that_connected_last_gets_it(self):
        self.router.connect("a")
        self.router.connect("b")
        self.router.announce("/audio/x.wav", 1)
        self.assertEqual(self.lines(), [(1, "b")])

    def test_when_the_owner_leaves_another_page_gets_the_voice(self):
        self.router.connect("a")
        self.router.connect("b")
        self.router.claim("a")
        self.router.disconnect("a")
        self.router.announce("/audio/x.wav", 1)
        self.assertEqual(self.lines(), [(1, "b")])
        self.assertIsNone(self.router.owner)

    def test_a_page_that_is_not_connected_cannot_claim(self):
        self.assertFalse(self.router.claim("ghost"))
        self.assertIsNone(self.router.owner)

    def test_serial_numbers_increase(self):
        self.assertEqual([self.router.next_serial() for _ in range(3)], [1, 2, 3])

    def test_serial_numbers_continue_after_the_lines_on_disk(self):
        self.assertEqual(self.router.next_serial(after=26), 27)
        self.assertEqual(self.router.next_serial(after=5), 28)


class WebAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = (self.wa.AUDIO_FOLDER, self.wa.UPLOAD_FOLDER, self.wa.AUDIO_KEEP, self.wa.AUDIO_DIR)
        self.wa.AUDIO_FOLDER = os.path.join(self.tmp.name, "audio")
        self.wa.AUDIO_DIR = self.wa.AUDIO_FOLDER          # the route serves from here
        self.wa.UPLOAD_FOLDER = os.path.join(self.tmp.name, "upload")
        self.http = self.wa.app.test_client()

    def tearDown(self):
        self.wa.AUDIO_FOLDER, self.wa.UPLOAD_FOLDER, self.wa.AUDIO_KEEP, self.wa.AUDIO_DIR = self.saved
        self.tmp.cleanup()

    def connect(self):
        client = self.wa.socketio.test_client(self.wa.app)
        client.get_received()
        return client

    def upload(self, name="x.wav", data=b"RIFFxxxxWAVE"):
        return self.http.post("/upload", data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data")

    def reloads(self, client):
        return [m["args"][0] for m in client.get_received() if m["name"] == "audio_reload"]

    def test_an_upload_reaches_only_the_page_that_plays(self):
        a, b, c = self.connect(), self.connect(), self.connect()
        b.emit("audio_claim", {})
        for client in (a, b, c):
            client.get_received()
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(len(self.reloads(a)), 0)
        self.assertEqual(len(self.reloads(c)), 0)
        lines = self.reloads(b)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0]["url"].startswith("/audio/line-"))
        self.assertGreater(lines[0]["serial"], 0)
        for client in (a, b, c):
            client.disconnect()

    def test_every_line_has_its_own_file_that_can_be_fetched(self):
        client = self.connect()
        self.upload(data=b"RIFF-first")
        self.upload(data=b"RIFF-second")
        urls = [m["url"] for m in self.reloads(client)]
        self.assertEqual(len(set(urls)), 2)
        self.assertNotEqual(urls[0], urls[1])
        self.assertEqual(self.http.get(urls[0]).data, b"RIFF-first")
        self.assertEqual(self.http.get(urls[1]).data, b"RIFF-second")
        self.assertEqual(self.http.get(urls[0]).headers["Cache-Control"], "no-store")
        client.disconnect()

    def test_a_line_after_a_restart_is_not_removed_by_the_cleanup(self):
        # the files of the run before a restart are still there, the router of the new run counts from 0 again
        os.makedirs(self.wa.AUDIO_FOLDER)
        for serial in range(15, 27):
            with open(os.path.join(self.wa.AUDIO_FOLDER, f"line-{serial:06d}.wav"), "wb") as fp:
                fp.write(b"RIFF-old")
        self.wa.audio_router.serial = 0
        client = self.connect()
        self.upload(data=b"RIFF-new")
        url = self.reloads(client)[0]["url"]
        self.assertEqual(url, "/audio/line-000027.wav")
        response = self.http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"RIFF-new")
        client.disconnect()

    def test_an_ended_message_cannot_remove_a_newer_line(self):
        client = self.connect()
        self.upload(data=b"RIFF-first")
        self.upload(data=b"RIFF-second")
        first, second = [m["url"] for m in self.reloads(client)]
        client.emit("audio_ended", {"serial": 1})
        client.emit("audio_ended", {"serial": 1})
        self.assertEqual(self.http.get(second).data, b"RIFF-second")
        self.assertEqual(self.http.get(first).data, b"RIFF-first")
        client.disconnect()

    def test_old_lines_are_removed_but_the_latest_stay(self):
        self.wa.AUDIO_KEEP = 3
        client = self.connect()
        for number in range(6):
            self.upload(data=b"RIFF%d" % number)
        files = sorted(os.listdir(self.wa.AUDIO_FOLDER))
        self.assertEqual(len(files), 3)
        urls = [m["url"] for m in self.reloads(client)]
        self.assertEqual(self.http.get(urls[-1]).status_code, 200)
        self.assertEqual(self.http.get(urls[0]).status_code, 404)
        client.disconnect()

    def test_the_intro_sound_goes_to_the_page_that_just_loaded(self):
        intro = os.path.join(self.tmp.name, "intro.wav")
        with open(intro, "wb") as fp:
            fp.write(b"RIFF-intro")
        saved = self.wa.cfg["intro_sound"], self.wa.cfg.get("intro_sounds")
        self.wa.cfg["intro_sound"] = intro
        self.wa.cfg["intro_sounds"] = []
        try:
            old, new = self.connect(), self.connect()
            old.emit("audio_claim", {})
            for client in (old, new):
                client.get_received()
            new.emit("audio_claim", {"initial": True})
            self.assertEqual(len(self.reloads(old)), 0)
            lines = self.reloads(new)
            self.assertEqual(len(lines), 1)
            self.assertEqual(self.http.get(lines[0]["url"]).data, b"RIFF-intro")
            old.disconnect()
            new.disconnect()
        finally:
            self.wa.cfg["intro_sound"], self.wa.cfg["intro_sounds"] = saved

    def test_the_intro_is_one_of_the_listed_clips(self):
        clips = []
        for number in range(3):
            path = os.path.join(self.tmp.name, "clip%d.wav" % number)
            with open(path, "wb") as fp:
                fp.write(b"RIFF-clip%d" % number)
            clips.append(path)
        saved = self.wa.cfg["intro_sound"], self.wa.cfg.get("intro_sounds")
        self.wa.cfg["intro_sound"] = "missing.wav"
        self.wa.cfg["intro_sounds"] = clips + ["also-missing.wav"]
        try:
            seen = set()
            for _ in range(40):
                client = self.connect()
                client.emit("audio_claim", {"initial": True})
                seen.add(self.http.get(self.reloads(client)[0]["url"]).data)
                client.disconnect()
            self.assertEqual(seen, {b"RIFF-clip0", b"RIFF-clip1", b"RIFF-clip2"})
        finally:
            self.wa.cfg["intro_sound"], self.wa.cfg["intro_sounds"] = saved

    def test_attention_call_follows_its_chance_and_skips_missing_files(self):
        clip = os.path.join(self.tmp.name, "listen.wav")
        with open(clip, "wb") as fp:
            fp.write(b"RIFF-listen")
        saved = {k: self.wa.cfg.get(k) for k in ("attention_sounds", "attention_chance")}
        client = self.connect()
        client.emit("audio_claim", {})
        client.get_received()
        try:
            self.wa.cfg["attention_sounds"] = [clip, "missing.wav"]
            self.wa.cfg["attention_chance"] = 0.0
            self.assertFalse(self.wa.maybe_call_attention())
            self.wa.cfg["attention_chance"] = 1.0
            self.assertTrue(self.wa.maybe_call_attention())
            lines = self.reloads(client)
            self.assertEqual(self.http.get(lines[0]["url"]).data, b"RIFF-listen")
            self.wa.cfg["attention_sounds"] = ["missing.wav"]
            self.assertFalse(self.wa.maybe_call_attention())
        finally:
            self.wa.cfg.update(saved)
            client.disconnect()

    def test_claiming_without_initial_does_not_play_the_intro(self):
        client = self.connect()
        client.emit("audio_claim", {})
        self.assertEqual(self.reloads(client), [])
        client.disconnect()

    def test_a_closed_page_never_blocks_the_voice(self):
        a, b = self.connect(), self.connect()
        b.emit("audio_claim", {})
        b.disconnect()
        a.get_received()
        self.upload()
        self.assertEqual(len(self.reloads(a)), 1)
        a.disconnect()

    def test_the_upload_needs_a_file(self):
        self.assertEqual(self.http.post("/upload", data={}).status_code, 400)

    def test_the_index_page_does_not_play_anything_by_itself(self):
        client = self.connect()
        original = self.wa.play_intro_sound
        calls = []
        self.wa.play_intro_sound = lambda: calls.append("intro")
        try:
            self.assertEqual(self.http.get("/").status_code, 200)
        finally:
            self.wa.play_intro_sound = original
        self.assertEqual(calls, [])
        client.disconnect()


if __name__ == "__main__":
    unittest.main()
