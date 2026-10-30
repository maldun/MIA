#!/usr/bin/env python3
"""
One workflow of the library (IF-203) per skill, so that the runner can run it by id and version (D-112, run_workflow.sync_skills).

  python3 tools/sync_workflows.py                 show what would be saved (changes nothing)
  python3 tools/sync_workflows.py --do            save a new version of every workflow whose document changed
  options: --dir data/db   the folder of the file storage (config key accounts_dir)

A workflow that was not made from a skill (the review draft) is kept as it is. No model is called.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from core import Core                                  # noqa: E402
from library import Library                            # noqa: E402
from run_workflow import sync_skills                   # noqa: E402
from storage import Storage                            # noqa: E402
from storage_files import FileBackend                  # noqa: E402
from workflow_library import WorkflowLibrary           # noqa: E402


class _DryRun:
    """the library as it is, with save left out: what --do would save"""
    def __init__(self, library):
        self._library = library

    def __getattr__(self, name):
        return getattr(self._library, name)

    def save(self, *args, **kwargs):
        return {"version": None}


def main(argv=None, show=print):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--dir", default=os.path.join(REPO, "data", "db"))
    parser.add_argument("--do", action="store_true")
    args = parser.parse_args(argv)
    library = WorkflowLibrary(Storage(FileBackend(args.dir)))
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library"), os.path.join(REPO, "data", "library")), os.path.join(REPO, "data", "runs"))
    report = sync_skills(library if args.do else _DryRun(library), core)
    show(("saved: " if args.do else "would save: ") + (", ".join(report["saved"]) or "nothing"))
    show("unchanged: " + (", ".join(report["unchanged"]) or "none"))
    show("kept (not made from a skill): " + (", ".join(report["kept"]) or "none"))
    for name, problem in sorted(report["problems"].items()):
        show("problem %s: %s" % (name, problem))
    return 0


if __name__ == "__main__":
    sys.exit(main())
