"""
Tests for the orderly shutdown of MIA (shutdown.py, __main__.py, /break! and /goodnight!).
Run with the MIA virtualenv: python tests/test_shutdown.py
"""
import importlib
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the code uses relative imports as package "MIA": make the repository importable under that name
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class StopProcess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sd = importlib.import_module("MIA.shutdown")

    def test_a_cooperative_process_ends_on_sigterm(self):
        proc = subprocess.Popen(["sleep", "60"])
        start = time.time()
        self.assertTrue(self.sd.stop_process(proc, "sleeper", timeout=5))
        self.assertLess(time.time() - start, 3)
        self.assertIsNotNone(proc.poll())

    def test_a_stubborn_process_is_killed_after_the_timeout(self):
        proc = subprocess.Popen([sys.executable, "-c",
                                 "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); print('up', flush=True); time.sleep(60)"],
                                stdout=subprocess.PIPE)
        proc.stdout.readline()  # handler installed
        start = time.time()
        self.assertFalse(self.sd.stop_process(proc, "stubborn", timeout=1))
        self.assertGreaterEqual(time.time() - start, 1)
        self.assertIsNotNone(proc.poll())
        proc.stdout.close()

    def test_nothing_to_stop(self):
        self.assertTrue(self.sd.stop_process(None))
        done = subprocess.Popen(["true"])
        done.wait()
        self.assertTrue(self.sd.stop_process(done))

    def test_group_stop_also_ends_the_helpers_of_the_process(self):
        # a helper in its own session that has a child of its own (like the https proxy script)
        proc = subprocess.Popen(["bash", "-c", "sleep 60 & echo $!; wait"], stdout=subprocess.PIPE, start_new_session=True)
        child = int(proc.stdout.readline())
        self.assertTrue(alive(child))
        self.assertTrue(self.sd.stop_process(proc, "helper", timeout=5, group=True))
        time.sleep(0.3)
        self.assertFalse(alive(child))
        proc.stdout.close()


class GracefulShutdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sd = importlib.import_module("MIA.shutdown")

    def test_steps_run_in_order_with_pauses(self):
        times = []
        steps = [(n, lambda n=n: times.append((n, time.time()))) for n in ["a", "b", "c"]]
        self.sd.graceful_shutdown(steps, pause=0.3)
        self.assertEqual([n for n, _ in times], ["a", "b", "c"])
        self.assertGreaterEqual(times[1][1] - times[0][1], 0.28)
        self.assertGreaterEqual(times[2][1] - times[1][1], 0.28)

    def test_a_failing_step_does_not_stop_the_others(self):
        ran = []

        def broken():
            raise RuntimeError("boom")
        self.sd.graceful_shutdown([("a", lambda: ran.append("a")), ("broken", broken), ("c", lambda: ran.append("c"))], pause=0)
        self.assertEqual(ran, ["a", "c"])

    def test_ctrl_c_during_shutdown_does_not_cut_it_short(self):
        ran = []

        def impatient():
            os.kill(os.getpid(), signal.SIGINT)    # a second Ctrl+C
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.1)
            ran.append("impatient")
        self.sd.graceful_shutdown([("impatient", impatient), ("last", lambda: ran.append("last"))], pause=0)
        self.assertEqual(ran, ["impatient", "last"])

    def test_signal_handlers_are_restored_afterwards(self):
        before = signal.getsignal(signal.SIGINT)
        self.sd.graceful_shutdown([], pause=0)
        self.assertEqual(signal.getsignal(signal.SIGINT), before)


class RequestShutdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sd = importlib.import_module("MIA.shutdown")

    def test_request_from_another_thread_interrupts_the_main_thread(self):
        threading.Timer(0.2, self.sd.request_shutdown).start()   # like a web request thread of /break!
        with self.assertRaises(KeyboardInterrupt):
            time.sleep(5)

    def test_sigterm_takes_the_same_path(self):
        old = signal.getsignal(signal.SIGTERM)
        try:
            self.sd.install_term_handler()
            threading.Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
            with self.assertRaises(KeyboardInterrupt):
                time.sleep(5)
        finally:
            signal.signal(signal.SIGTERM, old)


class WholeSequence(unittest.TestCase):
    """The stand-in for MIA's main process (tests/shutdown_harness.py) with real signals."""

    def run_harness(self, how, pause=0.4):
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "log.txt")
            harness = subprocess.Popen([sys.executable, os.path.join(HERE, "shutdown_harness.py"), _LINK_DIR, log, str(pause)],
                                       stdout=subprocess.PIPE, start_new_session=True)
            self.assertEqual(harness.stdout.readline().strip(), b"ready")
            if how == "ctrl-c":     # the terminal sends SIGINT to the whole foreground group of MIA
                os.killpg(harness.pid, signal.SIGINT)
            elif how == "break":    # /break!: only MIA itself is signalled
                os.kill(harness.pid, signal.SIGINT)
            elif how == "sigterm":
                os.kill(harness.pid, signal.SIGTERM)
            self.assertEqual(harness.wait(timeout=20), 0)
            harness.stdout.close()
            return open(log).read()

    def check_order(self, text):
        lines = text.strip().splitlines()
        self.assertIn("harness got the interrupt", text)
        self.assertIn("history saved", text)
        times = {}
        for l in lines:
            m = re.match(r"(proxy|speech) got SIGTERM at ([\d.]+)", l)
            if m:
                times[m.group(1)] = float(m.group(2))
        self.assertEqual(set(times), {"proxy", "speech"}, text)
        self.assertGreaterEqual(times["speech"] - times["proxy"], 0.35, "helpers are stopped one after the other")
        self.assertNotIn("must not happen", text)
        self.assertTrue(lines[-1].startswith("harness done"))

    def test_ctrl_c_in_the_terminal(self):
        # the helpers run in their own session: the group signal reaches only the main process
        self.check_order(self.run_harness("ctrl-c"))

    def test_break_command(self):
        self.check_order(self.run_harness("break"))

    def test_sigterm(self):
        self.check_order(self.run_harness("sigterm"))


class MiaCodeUsesIt(unittest.TestCase):
    def test_main_starts_helpers_in_their_own_session_and_shuts_down_in_order(self):
        with open(os.path.join(REPO, "__main__.py")) as fp:
            source = fp.read()
        self.assertIn("subprocess.Popen(cmd_speak,start_new_session=True)", source)
        self.assertIn("install_term_handler()", source)
        self.assertIn("graceful_shutdown(", source)
        self.assertNotIn("killpg", source)
        self.assertNotIn("exchange_file", source)   # was never defined (NameError on Ctrl+C)
        with open(os.path.join(REPO, "tls_proxy.py")) as fp:
            self.assertIn("start_new_session=True", fp.read())

    def test_commands_ask_for_an_orderly_shutdown(self):
        os.environ.setdefault("MIA_TEST", "1")
        wa = importlib.import_module("MIA.web_app")
        calls = []
        old_request, old_dream = wa.request_shutdown, wa.comm.emulate_dreaming
        wa.request_shutdown = lambda: calls.append("shutdown")
        wa.comm.emulate_dreaming = lambda: calls.append("dream")
        try:
            self.assertTrue(wa.handle_special_commands("/break!"))
            self.assertTrue(wa.handle_special_commands("/goodnight!"))
        finally:
            wa.request_shutdown, wa.comm.emulate_dreaming = old_request, old_dream
        self.assertEqual(calls, ["shutdown", "dream", "shutdown"])   # goodnight dreams first, then shuts down
        # a fully handled command must not be sent to the model as a chat message afterwards
        for command in ["/dream!", "/time!"]:
            wa.comm.emulate_dreaming = lambda: None
            old_time = wa.time_update
            wa.time_update = lambda: None
            try:
                self.assertTrue(wa.handle_special_commands(command), command)
            finally:
                wa.time_update = old_time
                wa.comm.emulate_dreaming = old_dream
        self.assertFalse(wa.handle_special_commands("hello MIA"))
        with open(os.path.join(REPO, "web_app.py")) as fp:
            self.assertNotIn("killpg", fp.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
