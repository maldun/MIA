"""The stage-2 browser checks of the chat and login views (N-1.1; D-163 F3, F6): TC-CLV-016 (touch targets, layout), TC-CLV-006 (chat with the
character blocked), TC-CLV-013 (variant label), TC-CLV-018 (no password over plain HTTP), TC-CLV-021 (only IF-101 on the wire) and TC-CLV-004
(connection cut and back), in one click-through of every view (ui/tools/chat_views_e2e.js).
The real page on the IF-101 mock server (ui/tools/chat_mock_server.py) in its own container of the MIA image with `--network none`, and headless
Chromium of localhost/mia-browser (tests/browser/Containerfile, D-141) in that container's network: loopback only, nothing else reachable.
The container names are unique per run (never a stage of tools/start_testing.sh), both are removed afterwards. Skipped, never passed, where
podman or one of the images is missing.  Run on the host with: python3 tests/test_chat_views_browser.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

BROWSER_IMAGE = "localhost/mia-browser"
MIA_IMAGE = "localhost/mia:latest"
DRIVER = os.path.join(HERE, "browser", "chat_views.py")
CONTRACT = os.path.join(ROOT, "contracts", "IF-101-chat-api.md")
BASE = "http://127.0.0.1:8686"
OWN_HOST = "127.0.0.1:8686"
TOUCH_PX = 44                                  # REQ-CLV-016 AC-1
# the page itself, its files, the character page (IF-111, N-1.2) and the transport of the socket: not operations of IF-101
PAGE_PATHS = ("/", "/favicon.ico")
PAGE_PREFIXES = ("/static/", "/character/", "/socket.io/")
# used by the page and the backend, but not yet in IF-101 v13 (D-163 F4): amendment A-62 adds them to IF-101 v14 and empties this set
PENDING_A62 = set()      # A-62 installed: IF-101 names the whole wire


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def start_mock():
    """the mock server in a container of its own, without network; returns its name once the page answers"""
    name = "n11-views-%s" % uuid.uuid4().hex[:8]
    subprocess.run(["podman", "run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-e", "ANSWER_DELAY=1", "-e", "EVENT_GAP=0.05",
                    "-v", "%s:/opt/mia/MIA:O" % ROOT, MIA_IMAGE, "python", "MIA/ui/tools/chat_mock_server.py"], check=True, capture_output=True)
    probe = "import urllib.request; urllib.request.urlopen('%s/')" % BASE
    for _ in range(60):
        if subprocess.run(["podman", "exec", name, "python", "-c", probe], capture_output=True).returncode == 0:
            return name
        time.sleep(0.5)
    logs = subprocess.run(["podman", "logs", name], capture_output=True, text=True).stdout[-500:]
    stop_mock(name)
    raise AssertionError("the mock server did not answer in 30 s: " + logs)


def stop_mock(name):
    subprocess.run(["podman", "rm", "-f", "-t", "0", name], capture_output=True)


def browse(container, *scenarios):
    """one run of the driver in the network of `container` (the click-through script mounted read-only); returns its JSON {scenario: result}"""
    with open(DRIVER, encoding="utf-8") as driver:
        run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "container:" + container, "-v", "%s:/tools:ro,z" % os.path.join(ROOT, "ui", "tools"),
                              BROWSER_IMAGE, "python", "-", BASE, *scenarios], stdin=driver, capture_output=True, text=True, timeout=400)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-800:])
    return json.loads(run.stdout.strip().splitlines()[-1])


def too_small(controls, least=TOUCH_PX):
    """the controls narrower or lower than `least` px"""
    return [c for c in controls if c["w"] < least or c["h"] < least]


def contract_wire(text):
    """the names IF-101 gives the wire: (REST paths, socket events). An operation `name(...)` is at /api/<name>; a name in brackets after it,
    `(chat_send)`, is its socket event, and so is a name after the word event (`connect`: event `chat_status` first); an address in
    backquotes is a path; the first column of the events table is an event"""
    paths, events = set(), set()
    in_events = False
    for line in text.splitlines():
        in_events = in_events or line.startswith("Events (")
        if not line.startswith("| `"):
            continue
        cell = line.split("|")[1]
        if in_events:
            events.update(re.findall(r"`([a-z_]+)`", cell)[:1])
            continue
        paths.update("/api/" + name for name in re.findall(r"`([a-z_]+)\(", cell))
        events.update(re.findall(r"\(`([a-z_]+)`\)", cell) + re.findall(r"event `([a-z_]+)`", line))
        paths.update(path.split("<")[0] for path in re.findall(r"`(/[a-z_/.<>-]+)`", cell))
    return paths, events


def off_contract(urls, events, wire, pending=frozenset()):
    """what the session used outside IF-101: requests to another host, paths and socket events the contract does not name"""
    paths, known = wire
    wrong = []
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme in ("data", "blob"):
            continue
        if parts.netloc != OWN_HOST:
            wrong.append(url)
        elif parts.path not in PAGE_PATHS and not parts.path.startswith(PAGE_PREFIXES) and parts.path not in pending \
                and not any(parts.path == p or (p.endswith("/") and parts.path.startswith(p)) for p in paths):
            wrong.append(parts.path)
    return sorted(set(wrong)) + sorted(e for e in events if e not in known and e not in pending)


class CheckRules(unittest.TestCase):
    def test_the_rule_finds_a_narrow_control(self):
        """The check itself: a control of 32 x 44 px is too small, 44 x 44 is not.

        Example: [{"name": "up", "w": 32, "h": 44}, {"name": "send", "w": 44, "h": 44}] -> only "up".
        """
        # Given: one narrow and one big enough control
        controls = [{"name": "up", "w": 32, "h": 44}, {"name": "send", "w": 44, "h": 44}]
        # When: the small ones are picked
        found = too_small(controls)
        # Then: only the narrow one
        self.assertEqual([c["name"] for c in found], ["up"])

    def test_the_wire_is_read_from_the_contract(self):
        """TC-CLV-021: operations, their socket events, addresses in backquotes and the events table are read from the contract text.

        Example: "| `send(session)` (`chat_send`) |" -> /api/send and chat_send; "| `file(session, name)` (`/api/files/<name>`) |" -> /api/files/.
        """
        # Given: rows of the operations table and of the events table
        text = ("| `send(session, text)` (`chat_send`) | text | ack |\n| `file(session, name)` (`/api/files/<name>`) | name | bytes |\n"
                "| `connect(session)` | session | event `chat_status` first | |\n"
                "| `history(session, limit)` (`/api/chat/history`) | | list |\nEvents (server to every connected page):\n| `chat_start` | `{id}` |\n")
        # When: the wire is read
        paths, events = contract_wire(text)
        # Then: the paths and events of the rows, nothing else
        self.assertEqual(paths, {"/api/send", "/api/file", "/api/files/", "/api/connect", "/api/history", "/api/chat/history"})
        self.assertEqual(events, {"chat_send", "chat_status", "chat_start"})

    def test_the_check_finds_a_path_an_event_and_a_host_outside_the_contract(self):
        """TC-CLV-021: the check itself reports an unknown path, an unknown event and another host, and accepts the page's own files.

        Example: /api/secret, event "spy" and https://cdn.example.org/x.js -> reported; /static/chat/app.js, /api/files/a.pdf -> not.
        """
        # Given: a session with good and bad requests and events
        wire = ({"/api/login", "/api/files/"}, {"chat_send"})
        urls = [BASE + "/", BASE + "/static/chat/app.js", BASE + "/api/login", BASE + "/api/files/a.pdf", BASE + "/api/secret",
                "https://cdn.example.org/x.js", "data:,"]
        # When: what is outside the contract is picked
        found = off_contract(urls, ["chat_send", "spy"], wire)
        # Then: the bad path, the other host and the unknown event
        self.assertEqual(found, ["/api/secret", "https://cdn.example.org/x.js", "spy"])


class ChatViewsInBrowser(unittest.TestCase):
    results = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        container = start_mock()
        cls.addClassCleanup(stop_mock, container)
        cls.results = browse(container, "touch", "layout", "lan", "offline", "views")

    @mark.req("REQ-CLV-016")
    def test_every_visible_control_on_a_phone_is_44_px_or_more(self):
        """TC-CLV-016 (F3): with a coarse pointer at 360 px every visible control, the five answer actions included, is at least 44 x 44 px.

        Example: speak, up, down, how, regenerate 32 x 44 px -> too small; 44 x 44 px -> [].
        """
        # Given: the chat on a phone with one written answer
        touch = self.results["touch"]
        self.assertTrue(touch["coarse"], "the browser does not emulate a coarse pointer")
        self.assertEqual(touch["width"], 360)
        self.assertTrue({"speak", "up", "down", "how", "regenerate"} <= set(touch["actions"]), touch["actions"])
        # When: the controls below 44 px are picked
        found = too_small(touch["controls"])
        # Then: there are none
        self.assertEqual(found, [])

    @mark.req("REQ-CLV-016")
    def test_no_viewport_scrolls_sideways_in_either_theme(self):
        """TC-CLV-016: at 360, 768 and 1440 px, in the dark and the light theme, the page is never wider than the window.

        Example: {"dark-360": {"sideways": false}, ..., "light-1440": {"sideways": false}} -> [].
        """
        # Given: the six measurements of the layout run
        layout = self.results["layout"]
        # When: the ones that scroll sideways or show another theme are picked
        wrong = [key for key, value in layout.items() if value["sideways"] or value["theme"] != key.split("-")[0]]
        # Then: all six were measured and none is wrong
        self.assertEqual(len(layout), 6)
        self.assertEqual(wrong, [])

    @mark.req("REQ-CLV-006", "REQ-CLV-001", "REQ-CLV-005", "REQ-CLV-008", "REQ-CLV-009", "REQ-CLV-010", "REQ-CLV-011", "REQ-CLV-012", "REQ-CLV-014")
    def test_every_view_works_with_the_character_blocked(self):
        """TC-CLV-006: with the request of the character iframe blocked, the click-through of every view finds no problem: messages are sent
        and answered, the five actions, regenerate, the seven workspace tabs, persona, score and the account dialog.

        Example: attempted == "/character/" (the page tried to load the character), problems == [], tabs has 7 entries.
        """
        # Given: the click-through run with */character/* blocked
        views = self.results["views"]
        # When: its problems are read
        problems = views["problems"]
        # Then: the character was tried and blocked, and the chat and every view worked anyway
        self.assertEqual(views["attempted"], "/character/")
        self.assertEqual(problems, [])
        self.assertEqual(len(views["tabs"]), 7)

    @mark.req("REQ-CLV-013")
    def test_the_variant_label_comes_with_a_variant_and_goes_without(self):
        """TC-CLV-013: the third answer of the mock comes from a workflow with the variant summer: its label is shown; the next answer has no
        variant: the label goes and the chat's variant stays.

        Example: label_after_variant == "Outfit: summer", label_after_plain is None.
        """
        # Given: the click-through and one more answer
        views = self.results["views"]
        # When / Then: the label after the variant answer and after the plain one
        self.assertEqual(views["label_after_variant"], "Outfit: summer")
        self.assertIsNone(views["label_after_plain"])

    @mark.req("REQ-CLV-021", "REQ-CLV-017")
    def test_the_session_uses_only_the_wire_of_if_101(self):
        """TC-CLV-021: every request of the click-through goes to the page's host, and every path and socket event it used is named in
        contracts/IF-101-chat-api.md (until A-62 is installed, plus the names of PENDING_A62).

        Example: /api/vote, chat_send, item_changed -> named; /api/secret or a CDN -> reported.
        """
        # Given: the requests and websocket events of the click-through, and the wire of the contract
        views = self.results["views"]
        with open(CONTRACT, encoding="utf-8") as handle:
            wire = contract_wire(handle.read())
        # When: what is outside the contract is picked
        found = off_contract(views["urls"], views["events"], wire, PENDING_A62)
        # Then: nothing, and the session really used the wire
        self.assertEqual(found, [])
        self.assertIn("chat_send", views["events"])
        self.assertTrue(any(urlsplit(u).path == "/api/vote" for u in views["urls"]))

    @mark.req("REQ-CLV-018", "REQ-CLV-014")
    def test_over_plain_http_by_a_home_network_name_the_login_sends_nothing(self):
        """TC-CLV-018: opened as http://mia-lan:8686 the login form is switched off with its reason, and even a forced submit sends no request.

        Example: submitDisabled is True, error names HTTPS, logins == [].
        """
        # Given: the run on the home-network name
        lan = self.results["lan"]
        # When / Then: the form is off, says why, and nothing went to /api/login
        self.assertEqual(lan["host"], "mia-lan:8686")
        self.assertTrue(lan["submitDisabled"])
        self.assertIn("HTTPS", lan["error"] or "")
        self.assertEqual(lan["logins"], [])

    @mark.req("REQ-CLV-004")
    def test_a_cut_connection_keeps_the_draft_and_comes_back_without_a_reload(self):
        """TC-CLV-004: with the socket's transport closed the page shows offline with a banner, Send is off, the draft stays; the page is
        online again without a reload and the draft is still there.

        Example: cut == {state: offline, banner: true, send: true, draft: "my unsent draft"}, back is True, after.notReloaded is True.
        """
        # Given: the run with the cut connection
        offline = self.results["offline"]
        # When / Then: the state while cut, and after the reconnect
        self.assertIn(offline["cut"]["state"], ("offline", "reconnecting"))
        self.assertTrue(offline["cut"]["banner"])
        self.assertTrue(offline["cut"]["send"])
        self.assertEqual(offline["cut"]["draft"], "my unsent draft")
        self.assertTrue(offline["back"])
        self.assertEqual(offline["after"], {"draft": "my unsent draft", "notReloaded": True})


if __name__ == "__main__":
    unittest.main()
