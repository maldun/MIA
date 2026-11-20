"""PROTOTYPE CP5 checks (not protected tests): the graph backend behind the login and the list of graphs (FR-48, FR-49, NFR-12 of G-V4.VIEW).
Run: python proto_checks/cp5_check.py   (starts a throwaway postgres:16 under podman for the database half)"""
import json, os, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
import accounts, graph_model, graph_proto_app, graph_store_move
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_broken

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def client_for(backend, accounts_dir):
    acc = Storage(FileBackend(accounts_dir))
    accounts.create(acc, "owner", "secret", "cp5")
    app = graph_proto_app.create_app(backend, acc)
    return app.test_client(), app

def login(c):
    # like a browser: the page of this host sends its Origin with the login
    return c.post("/api/login", json={"user": "owner", "password": "secret"}, headers={"Origin": "http://127.0.0.1:8801"})

def run(kind, backend, tmp):
    c, app = client_for(backend, os.path.join(tmp, "acc_" + kind))
    r = c.get("/api/v2/graphs")
    check(f"[{kind}] NFR-12 without a login the list of graphs is not shown", r.status_code == 401 and b"cp2" not in r.data and b"lookup" not in r.data)
    check(f"[{kind}] NFR-12 a graph is not shown without a login either", c.get("/api/v2/graphs/sample.broken").status_code == 401)
    foreign = c.post("/api/login", json={"user": "owner", "password": "secret"}, headers={"Origin": "http://evil.example"})
    check(f"[{kind}] a login from another address is refused with its reason (bad_origin)", foreign.status_code == 403 and foreign.get_json()["error"] == "bad_origin")
    bad = c.post("/api/login", json={"user": "owner", "password": "wrong"}, headers={"Origin": "http://127.0.0.1:8801"})
    check(f"[{kind}] a wrong password gives no session", bad.status_code == 401 and c.get("/api/v2/graphs").status_code == 401)
    check(f"[{kind}] the right password logs in once", login(c).status_code == 200 and c.get("/api/v2/graphs").status_code == 200)
    listing = c.get("/api/v2/graphs").get_json()
    return c, listing

def main():
    import test_storage_postgres as tp
    from storage_postgres import PostgresBackend
    tmp = tempfile.mkdtemp()
    url = tp.start_database()
    try:
        files = FileBackend(os.path.join(tmp, "files")); populate(files); add_broken(files)
        pg = PostgresBackend(url)
        graph_store_move.move_store(files, pg)
        cf, lf = run("files", files, tmp)
        cp, lp = run("database", pg, tmp)
        check("FR-48 the list has every stored graph with id, kind, version, author, time, description and size", len(lf) == 17 and all({"id", "kind", "version", "author", "time", "description", "steps", "connections"} <= set(g) for g in lf), f"{len(lf)} graphs")
        check("FR-48 the list from the files and the list from the database are the same", lf == lp)
        ids = [g["id"] for g in lf]
        same = all(cf.get("/api/v2/graphs/" + i).get_json() == cp.get("/api/v2/graphs/" + i).get_json() for i in ids)
        check("FR-48 every graph read from the files and from the database is the same", same)
        model = graph_model.GraphModel(Storage(files), author="x")
        r = cf.get("/api/v2/graphs/cp2.multi").get_json()
        check("FR-48 a graph comes with local IDs, its version, author and time, and equals what was stored", r["graph"] == model.read_graph("cp2.multi") and r["version"] == 4 and r["current"] == 4 and r["author"] == "author4")
        v2 = cf.get("/api/v2/graphs/cp2.multi?version=2").get_json()
        check("FR-48 an earlier version can be asked for", v2["version"] == 2 and v2["graph"] == model.read_graph("cp2.multi", 2) and v2["graph"] != r["graph"])
        check("FR-48 the versions of a graph are listed with author and time", [(v["version"], v["author"]) for v in cf.get("/api/v2/graphs/cp2.multi/versions").get_json()] == [(1, "owner"), (2, "author2"), (3, "author3"), (4, "author4")])
        check("an unknown graph is a clean not-found", cf.get("/api/v2/graphs/nope").status_code == 404 and cf.get("/api/v2/graphs/nope/versions").status_code == 404)
        b = cf.get("/api/v2/graphs/sample.broken").get_json()
        check("FR-49 a connection to a missing step is named by the backend, not dropped", b["problems"] == [{"problem": "missing_step", "connection": "e2", "step": "var.gone", "end": "to"}], json.dumps(b["problems"]))
        check("FR-49 a graph without a problem has none", cf.get("/api/v2/graphs/cp2.multi").get_json()["problems"] == [])
        check("FR-49 the same problem is named from the database", cp.get("/api/v2/graphs/sample.broken").get_json()["problems"] == b["problems"])
        out = cf.post("/api/logout", headers={"Origin": "http://127.0.0.1:8801"})
        check("after the log-out the graphs are not shown again", out.status_code in (200, 204) and cf.get("/api/v2/graphs").status_code == 401)
    finally:
        tp.stop_database()

if __name__ == "__main__":
    main()
    failed = [n for n, ok, _ in results if not ok]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    sys.exit(1 if failed else 0)
