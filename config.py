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
LOCAL = "setup_cfg.local.json"        # settings of ONE machine next to a tracked configuration (the compose stack); not in git; wins key by key


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


def local_path(path):
    """the local overlay that belongs to the configuration file `path`"""
    return os.path.join(os.path.dirname(os.path.abspath(path)), LOCAL)


def load(path):
    """the configuration of `path` with setup_cfg.local.json next to it laid over it key by key (shallow: an object in the local file replaces the whole object). A local file that
    is not a json object is an error that names it: a typo in an override must not be ignored silently."""
    with open(path, encoding="utf-8") as fp:
        doc = json.load(fp)
    local = local_path(path)
    if os.path.exists(local):
        try:
            with open(local, encoding="utf-8") as fp:
                extra = json.load(fp)
        except ValueError as exc:
            raise ValueError("%s is not valid json: %s" % (LOCAL, exc))
        if not isinstance(extra, dict):
            raise ValueError("%s must be a json object" % LOCAL)
        doc.update(extra)
    return doc


def set_local(path, key, value):
    """puts one setting into the local file of `path` (made when it is missing) and keeps the others"""
    local = local_path(path)
    try:
        with open(local, encoding="utf-8") as fp:
            extra = json.load(fp)
    except FileNotFoundError:
        extra = {}
    extra[key] = value
    with open(local, "w", encoding="utf-8") as fp:
        json.dump(extra, fp, indent=2)
        fp.write("\n")


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
