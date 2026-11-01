"""Run every test file of a folder in its own process (the stage `unit` of stages.yaml, D-182).

    python tools/run_tests_per_file.py [tests folder]       (default: tests next to this tool's repository)
Environment: MIA_UNIT_JOBS parallel files (default 4), MIA_UNIT_PATTERN file pattern (default test_*.py), MIA_UNIT_TIMEOUT seconds per file (default 900).

Why: the web_app module of MIA is a singleton. The first test that imports it fixes its configuration (accounts on or off, the account store, the routes of the mock
server), so tests with different configurations pass alone and fail together in one `python -m unittest discover` process. Each file runs here with the same
`unittest discover -p <file>` the stage used, only isolated. A file that runs no tests, fails or times out is a failure; an empty folder is an error.
Output is small: one summary line, and for each failing file its last lines. Exit 0 only when every file passed.
"""
import concurrent.futures
import glob
import os
import subprocess
import sys
import time


def run_file(folder, name, timeout):
    start = time.time()
    try:
        done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", folder, "-p", name, "-q"], capture_output=True, text=True, timeout=timeout,
                              cwd=os.path.dirname(os.path.abspath(folder)))
        tail = (done.stdout + done.stderr).strip().splitlines()[-15:]
        return name, done.returncode, time.time() - start, tail
    except subprocess.TimeoutExpired:
        return name, "timed out", time.time() - start, ["timed out after %d s" % timeout]


def main():
    folder = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
    pattern = os.environ.get("MIA_UNIT_PATTERN", "test_*.py")
    jobs = max(1, int(os.environ.get("MIA_UNIT_JOBS", "4")))
    timeout = int(os.environ.get("MIA_UNIT_TIMEOUT", "900"))
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(folder, pattern)))
    if not names:
        print("no test file matches %s in %s: nothing run is not a pass" % (pattern, folder))
        return 1
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(lambda n: run_file(folder, n, timeout), names))
    failed = [r for r in results if r[1] != 0]
    for name, code, seconds, tail in failed:
        print("== FAILED %s (%s, %.0f s)" % (name, "timed out" if code == "timed out" else "exit %s" % code, seconds))
        print("\n".join("   " + line for line in tail))
    slowest = sorted(results, key=lambda r: -r[2])[:3]
    print("%d file(s), %d failed, %.0f s with %d worker(s); slowest: %s" % (len(results), len(failed), time.time() - start, jobs, ", ".join("%s %.0f s" % (r[0], r[2]) for r in slowest)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
