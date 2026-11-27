"""
Deliberate defects (implement-phase "Done when", verify-phase): plant each defect in the code, run the checks, restore the file, and report
which checks failed. A defect no check catches is named NOT CAUGHT (exit 1).

  python tools/plant_defects.py DEFECTS.json [--root DIR] [--python PY] [--timeout S]

DEFECTS.json is a list of {"name", "file", "old", "new", "checks": [test files]}: `old` must occur exactly once in `file` (relative to the root),
else nothing is planted and the tool stops (exit 2). Each check runs as `PY <check>` from the root; the failing tests are read from its
"FAIL: <name>" and "ERROR: <name>" lines (unittest), or the check is named when it fails without such a line.

The file is restored byte for byte after every defect, also when a check hangs or the tool is stopped, and its bytecode is removed before and
after each run: a restore of the same size within the same second left stale bytecode once, so a defect ran on in the next checks (TRANSFER
T-06). The checks run with PYTHONDONTWRITEBYTECODE, so no bytecode of a planted defect is ever written.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

FAILED = re.compile(r"^(?:FAIL|ERROR): (\S+)", re.M)


def drop_bytecode(path):
    folder, name = os.path.split(path)
    stem = os.path.splitext(name)[0]
    for pyc in glob.glob(os.path.join(folder, "__pycache__", stem + ".*.pyc")):
        os.remove(pyc)


def run_checks(root, checks, python, timeout):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    failed = []
    for check in checks:
        try:
            done = subprocess.run([python, check], cwd=root, env=env, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            failed.append("%s (timeout)" % check)
            continue
        names = FAILED.findall(done.stdout + done.stderr)
        if names:
            failed += names
        elif done.returncode != 0:
            failed.append("%s (exit %d)" % (check, done.returncode))
    return failed


def plant(root, defect, python, timeout):
    """the failing tests of one defect; the file is restored in every case"""
    path = os.path.join(root, defect["file"])
    with open(path, "rb") as f:
        original = f.read()
    text = original.decode("utf-8")
    drop_bytecode(path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(defect["old"], defect["new"], 1))
        return run_checks(root, defect["checks"], python, timeout)
    finally:
        with open(path, "wb") as f:
            f.write(original)
        drop_bytecode(path)


def refusals(root, defects):
    out = []
    for defect in defects:
        with open(os.path.join(root, defect["file"]), encoding="utf-8") as f:
            found = f.read().count(defect["old"])
        if found != 1:
            out.append("%s: old text found %d times in %s" % (defect["name"], found, defect["file"]))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("defects")
    parser.add_argument("--root", default=".")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args(argv)
    with open(args.defects, encoding="utf-8") as f:
        defects = json.load(f)
    refused = refusals(args.root, defects)
    if refused:
        print("nothing planted:\n  " + "\n  ".join(refused))
        return 2
    print("| Defect | Failing checks |\n|---|---|")
    missed = 0
    for defect in defects:
        failed = plant(args.root, defect, args.python, args.timeout)
        missed += not failed
        print("| %s | %s |" % (defect["name"], ", ".join(failed) if failed else "NOT CAUGHT"), flush=True)
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
