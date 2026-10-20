"""Tests for Ollama that MIA does not start (compose stack): address, waiting, pulling only what is missing, sandbox_backend none."""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import ollama_remote as O                             # noqa: E402
import sandbox                                        # noqa: E402


class FakeClient:
    def __init__(self, models=(), fail_times=0):
        self.models, self.fail_times, self.pulled, self.calls = list(models), fail_times, [], 0

    def list(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("not yet")
        return {"models": [{"model": m} for m in self.models]}

    def pull(self, model):
        self.pulled.append(model)


class OllamaRemoteTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(O.ollama_url({"ollama_host": "http://ollama:11434/"}), "http://ollama:11434")
        self.assertEqual(O.ollama_url({"address": "box", "port": 5}), "http://box:5")
        self.assertEqual(O.ollama_url({}), "http://localhost:11434")
        self.assertEqual(O.ollama_url({"ollama_host": None, "protocol": "https"}), "https://localhost:11434")

    def test_environment_wins(self):
        os.environ["MIA_OLLAMA_HOST"] = "http://far:1/"
        try:
            self.assertEqual(O.ollama_url({"ollama_host": "http://ollama:11434"}), "http://far:1")
            from communicator import Communicator
            self.assertEqual(Communicator(ollama_host="http://ollama:11434").host, "http://far:1")
        finally:
            del os.environ["MIA_OLLAMA_HOST"]

    def test_pull_switched_off(self):
        client = FakeClient(models=[])
        self.assertTrue(O.prepare({"version": "a:1", "ollama_pull": False}, timeout=1, log=lambda m: None, client=client))
        self.assertEqual(client.pulled, [])

    def test_wait(self):
        clock = [0]
        sleeps = []
        ok = O.wait_for_ollama(FakeClient(fail_times=2), timeout=30, pause=2, sleep=lambda s: (sleeps.append(s), clock.__setitem__(0, clock[0] + s)), now=lambda: clock[0])
        self.assertTrue(ok)
        self.assertEqual(sleeps, [2, 2])
        clock[0] = 0
        late = O.wait_for_ollama(FakeClient(fail_times=99), timeout=5, pause=2, sleep=lambda s: clock.__setitem__(0, clock[0] + s), now=lambda: clock[0])
        self.assertFalse(late)

    def test_pull_only_missing(self):
        client = FakeClient(models=["gemma4:26b", "tiny:latest"])
        pulled = O.pull_missing(client, ["gemma4:26b", "gemma4:12b-it-qat", "tiny", None], log=lambda m: None)
        self.assertEqual(pulled, ["gemma4:12b-it-qat"])
        self.assertEqual(client.pulled, ["gemma4:12b-it-qat"])

    def test_prepare(self):
        client = FakeClient(models=["a:1"])
        self.assertTrue(O.prepare({"version": "a:1", "version_light": "b:2"}, timeout=1, log=lambda m: None, client=client))
        self.assertEqual(client.pulled, ["b:2"])
        self.assertFalse(O.prepare({"version": "a:1"}, timeout=0, log=lambda m: None, client=FakeClient(fail_times=9)))

    def test_sandbox_none(self):
        router = sandbox.create_router({"sandbox_backend": "none"})
        self.assertFalse(router.available)
        self.assertEqual(router.run("print(1)").status, "unavailable")
        self.assertIn("container", router.info()["backends"]["none"]["reason"])

    def test_communicator_host(self):
        from communicator import Communicator
        self.assertEqual(Communicator(ollama_host="http://ollama:11434/").host, "http://ollama:11434")
        self.assertEqual(Communicator(address="box", port=7).host, "http://box:7")


if __name__ == "__main__":
    unittest.main()
