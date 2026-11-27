"""PROTOTYPE round 05 CP23 checks (not protected tests): a step is copied only into a graph of the same kind (FR-94, OC-7 of G-V4.EDIT; D-403, D-404).
The copy itself (same content, own history, independence, names, rules, owner only, live store) is round 02's cp10_check.py, rerun with this round.
Run: python proto_checks/cp23_check.py"""
import os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_model, graph_proto_app
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code
from proto_checks.cp22_check_fixtures import ctx, put_unknown

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
be = FileBackend(os.path.join(tmp, "s")); populate(be); add_code(be)
for gid in ("ctx.one", "ctx.two"):
    graph_model.GraphModel(Storage(be), author="cp23").save_graph(ctx(gid))
put_unknown(be, "odd.plan", "plan", 1)
put_unknown(be, "odd.other", "plan", 1)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp23")
app = graph_proto_app.create_app(be, acc)
o = app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)

def versions(gid):
    return o.get("/api/v2/graphs/%s/versions" % gid).get_json()

def copy_step(source, step, target, name="copied"):
    r = o.post("/api/v2/graphs/%s/copy-step" % source, json={"step": step, "target": target, "name": name}, headers=ORIGIN)
    return r.status_code, r.get_json()

# Given steps in graphs of three kinds, when the owner copies across kinds, then the copy is refused naming both kinds and nothing is written
cases = [
    ("sample.code", "var.in", "ctx.one", "workflow", "context"),
    ("sample.code", "var.in", "odd.plan", "workflow", "plan"),
    ("ctx.one", "claim", "cp2.multi", "context", "workflow"),
    ("odd.plan", "n1", "cp2.multi", "plan", "workflow"),
]
for source, step, target, sk, tk in cases:
    before = (versions(source), versions(target))
    status, body = copy_step(source, step, target)
    check("FR-94 a copy from a %s graph into a %s graph is refused naming both kinds" % (sk, tk),
          status == 422 and body.get("error") == "kinds_differ" and body.get("from_kind") == sk and body.get("to_kind") == tk, "%s %s" % (status, body))
    check("FR-94 nothing was written in either graph (%s -> %s)" % (sk, tk), (versions(source), versions(target)) == before)

# Given two graphs of the same kind that the editor cannot change, when a step is copied between them, then the reason of that kind is given
for source, step, target, code, kind in (("ctx.one", "claim", "ctx.two", "not_editable", "context"), ("odd.plan", "n1", "odd.other", "unknown_kind", "plan")):
    before = versions(target)
    status, body = copy_step(source, step, target)
    check("FR-94 a copy between two %s graphs is refused as %s naming the kind" % (kind, code),
          status == 422 and body.get("error") == code and body.get("kind") == kind, "%s %s" % (status, body))
    check("FR-94 nothing was written in the other %s graph" % kind, versions(target) == before)

# Given two workflow graphs, when a step is copied, then the copy is made (the rest of round 02's checks are cp10)
before = versions("cp2.multi")
status, body = copy_step("sample.code", "var.in", "cp2.multi", "var.copied")
check("FR-94 a copy between two workflow graphs is made as a new version of the other graph", status == 200 and body["changed"] is True and len(versions("cp2.multi")) == len(before) + 1, "%s %s" % (status, body))

failed = [r for r in results if not r[1]]
print(f"\n{len(results)} checks, {len(failed)} failed")
sys.exit(1 if failed else 0)
