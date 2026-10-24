"""
Smoke tests of the number gate on the target environment (specs/number-gate/test-spec.md: SMOKE-GATE-001, SMOKE-GATE-002), run in Phase 6.

SMOKE-GATE-001: the 5 cases tagged `smoke` (3 from verdicts_wikidata dev, 2 from verdicts_vitaminc dev, chosen at task T-06 by the owner) give the same verdict as in the release run.
SMOKE-GATE-002: the run header names the digest of the model that the server really holds (REQ-EVAL-001): the digest in the header equals the digest of /api/tags.

RED BY DESIGN: it needs a running Ollama, the gate pipeline and the pin of the harness. Protected: change only through a plan amendment.
Run on the target with: python tests/smoke/smoke_gate.py [http://localhost:11434]
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

PIN_DIGEST = "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3"


def server_digest(url, name="gemma4:12b-it-qat"):
    tags = json.load(urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=10))
    for model in tags["models"]:
        if model["name"] == name:
            return "sha256:" + model["digest"].replace("sha256:", "")
    return None


def main(url="http://localhost:11434"):
    try:
        digest = server_digest(url)
    except Exception as exc:
        print("SMOKE-GATE: Ollama not reachable at %s (%s)" % (url, exc))
        return 2
    if digest != PIN_DIGEST:
        print("SMOKE-GATE-002 would fail: the server holds %s, the pin is %s" % (digest, PIN_DIGEST))
        return 1
    print("SMOKE-GATE-001 and -002 are not runnable yet: they need verify.number_gate@1 and the pin header of the harness (plan.md tasks). Red by design.")
    return 2


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
