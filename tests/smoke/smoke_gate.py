"""
Smoke tests of the number gate on the target environment (specs/number-gate/test-spec.md: SMOKE-GATE-001, SMOKE-GATE-002), run in Phase 6.

SMOKE-GATE-001: the 5 cases tagged `smoke` (3 from verdicts_wikidata dev, 2 from verdicts_vitaminc dev, chosen by the owner at T-06) run through verify.number_gate@4 on the
real server with the pin MP-light. Expected: the Wikidata cases (a number, no evidence) answer unclear (REQ-GATE-006); the VitaminC cases give the verdict that the dev
baselines gave in every run and style (a true claim passes, a false claim fails). Until a release run exists, that baseline is the "release run".
SMOKE-GATE-002: the run header names the digest of the model that the server really holds (REQ-EVAL-001): the digest in the header equals the digest of /api/tags.

Needs a running Ollama and the labelled suites (the folder of tools/eval.py, or MIA_SUITES). Protected: change only through a plan amendment.
Run on the target with the MIA virtualenv (it needs the ollama client): python tests/smoke/smoke_gate.py [http://localhost:11434]   (exit 0 = green, 1 = red, 2 = cannot run)
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

MODEL = "gemma4:12b-it-qat"
PIN_DIGEST = "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3"
SUITES = ("verdicts_vitaminc", "verdicts_wikidata")


def server_digest(url, name=MODEL):
    tags = json.load(urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=10))
    for model in tags["models"]:
        if model["name"] == name:
            return "sha256:" + model["digest"].replace("sha256:", "")
    return None


def run_smoke_cases(suite, results):
    """the cases tagged smoke of a suite through the gate; returns (header, records) of the saved run"""
    command = [sys.executable, os.path.join(REPO, "tools", "eval.py"), "run", suite, "--tag", "smoke", "--variant", "smoke-gate", "--pipeline", "verify.number_gate@4",
               "--model", MODEL, "--pin", "MP-light", "--results", results, "--quiet"]
    done = subprocess.run(command, capture_output=True, text=True, timeout=900)
    saved = sorted(glob.glob(os.path.join(results, "%s__smoke-gate__*.jsonl" % suite)))
    if done.returncode != 0 or not saved:
        raise RuntimeError("the run of %s failed: %s" % (suite, (done.stderr or done.stdout)[-300:]))
    rows = [json.loads(line) for line in open(saved[-1], encoding="utf-8") if line.strip()]
    return rows[0], rows[1:]


def main(url="http://localhost:11434"):
    try:
        digest = server_digest(url)
    except Exception as exc:
        print("SMOKE-GATE: Ollama not reachable at %s (%s)" % (url, exc))
        return 2
    if digest != PIN_DIGEST:
        print("SMOKE-GATE-002 fails: the server holds %s, the pin is %s" % (digest, PIN_DIGEST))
        return 1
    failures, seen = [], 0
    with tempfile.TemporaryDirectory() as results:
        for suite in SUITES:
            try:
                header, records = run_smoke_cases(suite, results)
            except Exception as exc:
                print("SMOKE-GATE: %s" % exc)
                return 2
            if header.get("pin", {}).get("digest") != digest:
                failures.append("SMOKE-GATE-002: the header of %s names %s, the server holds %s" % (suite, header.get("pin", {}).get("digest"), digest))
            for record in records:
                seen += 1
                expected = "inconclusive" if suite == "verdicts_wikidata" else ("pass" if record["truth"] else "fail")
                if record["status"] != expected:
                    failures.append("SMOKE-GATE-001: %s said %s, expected %s" % (record["case"], record["status"], expected))
    if seen != 5:
        failures.append("SMOKE-GATE-001: %d cases are tagged smoke, 5 expected" % seen)
    for line in failures:
        print(line)
    print("SMOKE-GATE: %s (%d cases)" % ("RED" if failures else "green", seen))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
