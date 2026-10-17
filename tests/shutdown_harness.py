"""
Stand-in for MIA's main process in tests/test_shutdown.py: starts two helper processes in their own sessions
(like speech process and https proxy) and then waits for a signal. On shutdown it uses the real shutdown module,
in the same order as __main__.py: save history, stop proxy, stop speech.
usage: python shutdown_harness.py <package dir with MIA> <log file> <pause>
Each helper appends "<name> got SIGTERM at <time>" to the log file; the harness logs its own steps.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, sys.argv[1])
log_file, pause = sys.argv[2], float(sys.argv[3])
from MIA.shutdown import install_term_handler, stop_process, graceful_shutdown  # noqa: E402

HELPER = """
import signal, sys, time
name, log = sys.argv[1], sys.argv[2]
def on_term(*args):
    with open(log, "a") as fp:
        fp.write(f"{name} got SIGTERM at {time.time():.3f}\\n")
    sys.exit(0)
def on_int(*args):
    with open(log, "a") as fp:
        fp.write(f"{name} got SIGINT (must not happen)\\n")
signal.signal(signal.SIGTERM, on_term)
signal.signal(signal.SIGINT, on_int)
time.sleep(120)
"""

def note(text):
    with open(log_file, "a") as fp:
        fp.write(f"{text} at {time.time():.3f}\n")

speak = proxy = None
install_term_handler()
try:
    speak = subprocess.Popen([sys.executable, "-c", HELPER, "speech", log_file], start_new_session=True)
    proxy = subprocess.Popen([sys.executable, "-c", HELPER, "proxy", log_file], start_new_session=True)
    note("ready")
    print("ready", flush=True)
    time.sleep(120)
except KeyboardInterrupt:
    note("harness got the interrupt")
finally:
    graceful_shutdown([("save history", lambda: note("history saved")),
                       ("stop proxy", lambda: stop_process(proxy, "proxy", group=True)),
                       ("stop speech", lambda: stop_process(speak, "speech", group=True))], pause=pause)
    note("harness done")
