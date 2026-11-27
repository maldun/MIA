"""
TRANSFER's copy of VIEW's WebAppProbe and checkout_with (tests/acceptance/test_view_backend.py, D-470): TRANSFER's checks never import VIEW's
protected test file (TR-VIEW-015). One addition, `run_main`: the script runs after `from MIA import __main__ as main`, so a check starts and stops
the backend through the same start function and orderly-stop list as `python -m MIA` (TR-TRANSFER-009).
"""
import json
import os
import subprocess
import sys

HELPERS = os.path.dirname(os.path.abspath(__file__))
REPO = HELPERS
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
TESTS = os.path.join(REPO, "tests")          # checkout_copy.py, also when this file is read from its draft folder
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)


def checkout_with(settings, drop=("store",)):
    """a copy of the checkout (tests/checkout_copy.py) whose configuration has `settings` over the example and none of the keys in `drop`
    unless `settings` names them; returns the folder holding MIA/"""
    import checkout_copy
    folder = checkout_copy.make(settings)
    path = os.path.join(folder, "MIA", "setup_cfg.json")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in drop:
        if key not in settings:
            cfg.pop(key, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return folder


def data_folder(folder):
    """the folder of the file store MIA uses today: `accounts_dir` of the configuration, default data/db (web_app.py)"""
    with open(os.path.join(folder, "MIA", "setup_cfg.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    return os.path.join(folder, "MIA", cfg.get("accounts_dir", "data/db"))


class WebAppProbe:
    """imports MIA.web_app of `folder` in a separate process (so module state of other tests cannot leak in) and runs `script` there;
    the script sees `wa` (the web_app module) and prints one JSON line"""

    PRELUDE = ("import json, os, sys\nsys.path[:0] = [%r, %r]\nos.environ.setdefault('MIA_TEST', '1')\n%s"
               "from MIA import web_app as wa\nfrom MIA import accounts\nsys.path.append(%r)\n")

    @staticmethod
    def run(folder, script, env=None, main=False):
        prelude = WebAppProbe.PRELUDE % (folder, os.path.join(folder, "MIA"), "from MIA import __main__ as main\n" if main else "", HELPERS)
        environment = {k: v for k, v in os.environ.items() if k != "MIA_DATABASE_URL"}      # only what the check gives (TR-VIEW-007)
        environment.update(env or {})
        done = subprocess.run([sys.executable, "-c", prelude + script], cwd=folder, env=environment, capture_output=True, text=True, timeout=180)
        return done


def run_main(folder, script, env=None):
    """WebAppProbe.run with `main` (MIA's __main__ module of `folder`) imported before web_app (TR-TRANSFER-009)"""
    return WebAppProbe.run(folder, script, env=env, main=True)


def last_json(done):
    """the JSON line the script printed last"""
    return json.loads(done.stdout.strip().splitlines()[-1])
