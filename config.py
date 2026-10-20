"""
The configuration of MIA. `setup_cfg.json` is the real configuration of this machine (addresses, paths, models, tokens): it is NOT in version control, so that a deployment on another machine does not
fight with the one in git. `setup_cfg.example.json` is tracked: it lists every option with its default (or, for the options of the development machine, with the values it uses) and is the template.

  ensure(folder)        the path of setup_cfg.json; if the file is missing it is copied from the example (the first start on a new machine), and the caller is told
  default_path(folder)  for tools that only read: setup_cfg.json if it exists, else the example

Every option is documented in README.md ("Configuration"); a test keeps the example complete (every option that the code reads is in it).
"""
import os
import shutil

NAME = "setup_cfg.json"
EXAMPLE = "setup_cfg.example.json"


def paths(folder):
    return os.path.join(folder, NAME), os.path.join(folder, EXAMPLE)


def ensure(folder):
    """(path of setup_cfg.json, created): copies the example if the real file does not exist yet; raises FileNotFoundError when neither exists"""
    real, example = paths(folder)
    if os.path.exists(real):
        return real, False
    if not os.path.exists(example):
        raise FileNotFoundError("neither %s nor %s exists in %s" % (NAME, EXAMPLE, folder))
    shutil.copyfile(example, real)
    return real, True


def default_path(folder):
    real, example = paths(folder)
    return real if os.path.exists(real) else example
