"""
The configuration of MIA. `setup_cfg.json` is the real configuration of this machine (addresses, paths, models, tokens): it is NOT in version control, so that a deployment on another machine does not
fight with the one in git. `setup_cfg.example.json` is tracked: it lists every option with its default (or, for the options of the development machine, with the values it uses) and is the template.

  ensure(folder)        the path of setup_cfg.json; if the file is missing it is copied from the example (the first start on a new machine), and the caller is told
  default_path(folder)  for tools that only read: setup_cfg.json if it exists, else the example
  missing(folder)       the options of the example that this machine's file does not have (after an update that brought new options): {name: value in the example}

From a shell:  python config.py [folder]   lists them (it changes nothing; your file keeps its own formatting and values).

Every option is documented in README.md ("Configuration"); a test keeps the example complete (every option that the code reads is in it).
"""
import json
import os
import shutil
import sys

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


def missing(folder):
    real, example = paths(folder)
    with open(example, encoding="utf-8") as fp:
        template = json.load(fp)
    if not os.path.exists(real):
        return dict(template)
    with open(real, encoding="utf-8") as fp:
        mine = json.load(fp)
    return {key: value for key, value in template.items() if key not in mine}


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    found = missing(folder)
    if not found:
        print("%s has every option of %s." % (NAME, EXAMPLE))
    else:
        print("%s lacks %d option(s) of %s (the defaults apply until you add them; README.md describes them):" % (NAME, len(found), EXAMPLE))
        for key, value in found.items():
            print('  "%s": %s,' % (key, json.dumps(value)))
