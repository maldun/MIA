#!/usr/bin/env python3
"""
Every shipped workflow with status tested or trusted has a recorded baseline (REQ-EVL-005).

  python3 tools/check_baselines.py [--library library] [--baselines eval/baselines] [--registry library/baselines.json]

The baseline of a workflow is the file <baselines>/<suite>__<variant>__baseline.jsonl. Which suite and variant belong to a workflow is written in
library/baselines.json: {"verify.computable": {"suite": "computable", "variant": "gemma4-12b"}, "chat": null}. null says that the workflow has no suite
(and it is still named as missing). Read-only: it never writes in eval/. Exit code 1 if a workflow lacks its baseline.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import library as lib                                  # noqa: E402


def missing_baselines(library_dir, baselines_dir, registry_path):
    """[{"workflow", "reason"}] for each workflow id that has a tested or trusted version and no baseline file"""
    registry = {}
    if os.path.exists(registry_path):
        with open(registry_path, encoding="utf-8") as fp:
            registry = json.load(fp)
    checked = sorted({e["id"] for e in lib.Library(library_dir).entries("pipeline") if e.get("status") in lib.USABLE})
    missing = []
    for workflow in checked:
        link = registry.get(workflow, "unregistered")
        if link == "unregistered":
            reason = "not in library/baselines.json (which suite and variant is its baseline?)"
        elif not link:
            reason = "registered with no suite"
        else:
            name = "%s__%s__baseline.jsonl" % (link["suite"], link["variant"])
            reason = None if os.path.exists(os.path.join(baselines_dir, name)) else "missing file %s" % os.path.join(baselines_dir, name)
        if reason:
            missing.append({"workflow": workflow, "reason": reason})
    return missing


def main(argv=None):
    root = os.path.dirname(HERE)
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--library", default=os.path.join(root, "library"))
    parser.add_argument("--baselines", default=os.path.join(root, "eval", "baselines"))
    parser.add_argument("--registry", default=os.path.join(root, "library", "baselines.json"))
    args = parser.parse_args(argv)
    missing = missing_baselines(args.library, args.baselines, args.registry)
    for m in missing:
        print("%-22s %s" % (m["workflow"], m["reason"]))
    print("%d workflow(s) without a baseline" % len(missing))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
