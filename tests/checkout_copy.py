"""
The shared setup of every test that imports MIA's code (D-169): MIA is imported from a temporary folder whose `MIA/` holds links to the files of
the checkout, with its own `data/`, `setup_cfg.json` (the tracked example) and `mia.log`. web_app, mia_logger and the stores write next to their own
file, so a test run writes nothing into the checkout. tests/test_checkout_untouched.py guards it.

    import checkout_copy
    _LINK_DIR = checkout_copy.use()          # `import MIA.x` and the plain `import x` now load from the copy; returns the folder that holds MIA/
    folder = checkout_copy.make({"accounts_enabled": True})   # a separate copy with these settings over the example (not put on sys.path)
"""
import atexit
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWN = ("data", "setup_cfg.json", "setup_cfg.local.json", "mia.log")      # made fresh in the copy, never the checkout's
_used = None


def make(settings=None):
    """a new folder holding MIA/: links to the checkout's files, an empty data/ and setup_cfg.json = the example with `settings` laid over it;
    removed when the process ends"""
    folder = tempfile.mkdtemp(prefix="mia-tests-")
    atexit.register(shutil.rmtree, folder, True)
    package = os.path.join(folder, "MIA")
    os.makedirs(os.path.join(package, "data"))
    for name in os.listdir(REPO):
        if name not in OWN:
            os.symlink(os.path.join(REPO, name), os.path.join(package, name))
    with open(os.path.join(REPO, "setup_cfg.example.json"), encoding="utf-8") as fp:
        cfg = json.load(fp)
    cfg.update(settings or {})
    with open(os.path.join(package, "setup_cfg.json"), "w", encoding="utf-8") as fp:
        json.dump(cfg, fp)
    return folder


def use():
    """the copy of this process (made once), first on sys.path for `import MIA.x` and for the plain `import x`; returns the folder that holds MIA/"""
    global _used
    if _used is None:
        _used = make()
    for path in (os.path.join(_used, "MIA"), _used):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    return _used


def package():
    """the MIA/ folder of the copy of this process (for subprocesses: cwd or sys.path)"""
    return os.path.join(use(), "MIA")
