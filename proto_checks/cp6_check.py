"""PROTOTYPE CP6 checks (not protected tests): what the backend tells the viewer about the steps (kind, trust, lifecycle, code) - FR-50, FR-54 of G-V4.VIEW.
Run: python proto_checks/cp6_check.py"""
import json, os, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

tmp = tempfile.mkdtemp()
be = FileBackend(os.path.join(tmp, "s")); populate(be); add_code(be)
acc = Storage(FileBackend(os.path.join(tmp, "a"))); accounts.create(acc, "owner", "secret", "cp6")
c = graph_proto_app.create_app(be, acc).test_client()
c.post("/api/login", json={"user": "owner", "password": "secret"}, headers={"Origin": "http://127.0.0.1:8801"})

conv = c.get("/api/v2/graphs/chat@1").get_json()
steps = conv["steps"]
processing = [i for i in steps.values() if i["kind"] == "transform"]
check("FR-50 the steps of a converted graph tell their kind, and the shipped processing steps are trusted with a lifecycle",
      {i["kind"] for i in steps.values()} == {"data", "transform"} and processing and all(i["trust"] == "trusted" and i["lifecycle"] for i in processing),
      str({k: (v["kind"], v.get("trust"), v.get("lifecycle")) for k, v in steps.items()}))
code = c.get("/api/v2/graphs/sample.code").get_json()
hostile = '<img src=x onerror=alert(1)> step "quoted" & more'
info = code["steps"]
check("FR-50 a loop-controlling step is told apart from a processing and a data step", info["loop.review"]["kind"] == "master" and info["var.in"]["kind"] == "data" and info[hostile]["kind"] == "transform")
check("FR-50 a step that is not in the toolbox is untrusted and says why", info[hostile]["trust"] == "untrusted" and "toolbox" in info[hostile]["reason"])
check("FR-50 the loop-controlling step is trusted through its shipped controller", info["loop.review"]["trust"] == "trusted" and info["loop.review"]["lifecycle"] == "tested")
check("FR-54 a step with an input connection of the role code is marked as holding code, the others are not", info[hostile]["code"] is True and info["step.check"]["code"] is False and info["loop.review"]["code"] is False)
check("FR-54 names that look like markup and an instruction come back unchanged, as JSON text",
      hostile in code["graph"]["nodes"][2]["id"] and "Ignore all previous instructions" in code["graph"]["nodes"][0]["data"]["value"] and c.get("/api/v2/graphs/sample.code").content_type == "application/json")
check("FR-50 no step in the 16 converted and the sample graphs lacks a kind", all(i["kind"] in ("data", "transform", "master") for g in c.get("/api/v2/graphs").get_json() for i in c.get("/api/v2/graphs/" + g["id"]).get_json()["steps"].values()))
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
