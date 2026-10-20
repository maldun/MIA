"""
Tests for searxng_control.py: is SearXNG running, what MIA says when it is not, and the opt-in start of the container that tools/searxng/run.sh made (with fakes: nothing real is started or probed),
and the note that /search adds when the first backend did not answer. Run with the MIA virtualenv: python tests/test_searxng_control.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import research_chat as RC                            # noqa: E402
import searxng_control as S                           # noqa: E402


class Response:
    def __init__(self, code=200):
        self.status_code = code


class Probe:
    """a get() that does not answer the first `down` times"""
    def __init__(self, down=0):
        self.down, self.calls = down, []

    def __call__(self, url, timeout=None):
        self.calls.append(url)
        if len(self.calls) <= self.down:
            raise ConnectionError("Connection refused")
        return Response()


class Run:
    def __init__(self, code=0, stderr="", boom=None):
        self.code, self.stderr, self.boom, self.commands = code, stderr, boom, []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        if self.boom:
            raise self.boom

        class Done:
            returncode, stdout = self.code, ""
            stderr = self.stderr
        return Done()


def which(name):
    return "/usr/bin/" + name if name == "podman" else None


class Probing(unittest.TestCase):
    def test_wanted_follows_the_configured_backends(self):
        self.assertTrue(S.wanted({}))
        self.assertTrue(S.wanted({"search_backends": ["searxng"]}))
        self.assertFalse(S.wanted({"search_backends": ["duckduckgo"]}))

    def test_a_running_searxng(self):
        probe = Probe()
        state = S.probe({"searxng_port": 8590}, get=probe)
        self.assertEqual((state["reachable"], state["url"]), (True, "http://localhost:8590"))
        self.assertEqual(probe.calls, ["http://localhost:8590/healthz"])

    def test_a_searxng_that_does_not_answer(self):
        state = S.probe({}, get=Probe(down=9))
        self.assertFalse(state["reachable"])
        self.assertIn("ConnectionError", state["detail"])

    def test_another_address_is_used_when_configured(self):
        self.assertEqual(S.probe({"searxng_url": "http://other:9999"}, get=Probe())["url"], "http://other:9999")


class Ensuring(unittest.TestCase):
    def test_running_needs_nothing(self):
        run = Run()
        out = S.ensure_searxng({}, get=Probe(), run=run, which=which)
        self.assertEqual((out["reachable"], out["started"], run.commands), (True, False, []))

    def test_not_wanted_is_not_even_probed(self):
        probe = Probe()
        out = S.ensure_searxng({"search_backends": ["duckduckgo"]}, get=probe)
        self.assertEqual((out["wanted"], probe.calls), (False, []))

    def test_without_autostart_the_person_is_told_what_to_do(self):
        run = Run()
        out = S.ensure_searxng({}, get=Probe(down=99), run=run, which=which)
        self.assertEqual((out["reachable"], out["started"], run.commands), (False, False, []))
        for part in ("does not answer", "tools/searxng/run.sh start", "podman start mia-searxng", "searxng_autostart"):
            self.assertIn(part, out["message"])

    def test_with_autostart_the_existing_container_is_started_and_awaited(self):
        run, waits = Run(), []
        out = S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=3), run=run, which=which, sleep=waits.append)
        self.assertEqual((out["reachable"], out["started"]), (True, True))
        self.assertEqual(run.commands, [["/usr/bin/podman", "start", "mia-searxng"]])
        self.assertEqual(len(waits), 3)                                    # the first probe fails, then three more tries until it answers
        self.assertIn("was started", out["message"])

    def test_a_container_that_does_not_exist_is_not_created(self):
        run = Run(code=125, stderr="Error: no container with name or ID \"mia-searxng\" found")
        out = S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=99), run=run, which=which, sleep=lambda s: None)
        self.assertEqual((out["reachable"], out["started"]), (False, False))
        self.assertIn("no container", out["message"])
        self.assertIn("tools/searxng/run.sh start", out["message"])
        self.assertEqual(len(run.commands), 1)                              # only `start`: never `run`, `rm` or `create`

    def test_no_container_engine(self):
        out = S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=99), run=Run(), which=lambda name: None, sleep=lambda s: None)
        self.assertIn("neither podman nor docker", out["message"])

    def test_docker_is_used_when_there_is_no_podman(self):
        run = Run()
        S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=1), run=run, which=lambda name: "/usr/bin/docker" if name == "docker" else None, sleep=lambda s: None)
        self.assertEqual(run.commands[0][0], "/usr/bin/docker")

    def test_a_start_that_blows_up_or_never_answers_is_reported(self):
        out = S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=99), run=Run(boom=OSError("denied")), which=which, sleep=lambda s: None)
        self.assertIn("denied", out["message"])
        out = S.ensure_searxng({"searxng_autostart": True}, get=Probe(down=99), run=Run(), which=which, sleep=lambda s: None, waits=3)
        self.assertEqual((out["started"], out["reachable"]), (True, False))
        self.assertIn("does not answer", out["message"])


class SearchNote(unittest.TestCase):
    RESULT = {"query": "starcraft", "backend": "duckduckgo", "results": [{"title": "StarCraft", "url": "https://starcraft.example/", "snippet": "a game"}],
              "errors": ["searxng: SearXNG cannot be reached at http://localhost:8590 (Connection refused)"]}

    def test_the_fallback_is_named_with_its_reason(self):
        text = RC.format_results(self.RESULT)
        self.assertIn("(duckduckgo):\nNote: searxng: SearXNG cannot be reached at http://localhost:8590", text)
        self.assertIn("1. StarCraft", text)

    def test_no_note_when_nothing_failed(self):
        self.assertNotIn("Note:", RC.format_results(dict(self.RESULT, backend="searxng", errors=[])))
        self.assertNotIn("Note:", RC.format_results({k: v for k, v in self.RESULT.items() if k != "errors"}))

    def test_a_reason_from_the_web_cannot_inject_markup(self):
        text = RC.format_results(dict(self.RESULT, errors=["x <script>alert(1)</script> **bold**"]))
        self.assertNotIn("<script>", text)
        self.assertIn("\\*\\*bold\\*\\*", text)


if __name__ == "__main__":
    unittest.main()
