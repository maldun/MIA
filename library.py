"""
The library of nodes and pipelines (ui/REQUIREMENTS_CORE.md 4a): reusable, versioned, documented entries from which a task pulls what it needs.

  library/nodes/<id>/<version>.json        a node: one reusable step with a declared interface (check, view, tool, code ...)
  library/pipelines/<id>/<version>.json    a pipeline: a graph that wires nodes by reference ({"id", "use": "check.x@2", "params", "wire"})
  data/library/...                         the same structure for the entries of the user and of models, plus status.json (decisions about status)
  data/library.sqlite                      the index: searchable fields, dependencies, statistics, cases. Built from the files, can be deleted any time.

Files are the truth. A version is immutable (a changed entry is a new version); what can change is the status (draft, tested, trusted, retired), which is kept in
data/library/status.json, so shipped files never change. expand() turns a pipeline entry into the plain graph the runner executes (pipeline.py).
"""
import difflib
import hashlib
import json
import os
import re
import sqlite3
import threading
import time

NODE_KINDS = ("model", "tool", "code", "script", "ask_user")
STATUSES = ("draft", "tested", "trusted", "retired")
USABLE = ("tested", "trusted")            # what a selection and an unversioned reference may use
COST_CLASSES = ("cheap", "normal", "expensive")
SAFETY_FLAGS = ("reads_web", "runs_code")
ID_RE = re.compile(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*")
LOCAL_ID_RE = re.compile(r"[A-Za-z][\w\-]{0,39}")
NODE_KEYS = {"id", "version", "kind", "title", "description", "tags", "applies_to", "inputs", "outputs", "params", "body", "needs", "cost", "safety", "status", "origin"}
PIPELINE_KEYS = {"id", "version", "title", "description", "goal", "tags", "applies_to", "cost_class", "result", "nodes", "inputs", "needs", "cost", "status", "origin"}
MIN_RUNS_FOR_STATS = 3


class LibraryError(Exception):
    pass


def ref_of(entry_id, version):
    return "%s@%d" % (entry_id, version)


def split_ref(ref):
    """"check.x@2" -> ("check.x", 2); "check.x" -> ("check.x", None)"""
    name, at, version = str(ref).partition("@")
    if not ID_RE.fullmatch(name) or (at and not version.isdigit()):
        raise LibraryError("'%s' is not a valid reference (id or id@version)" % ref)
    return name, int(version) if version else None


# --- validation of entries ----------------------------------------------------------------------------------------------------

def _common_problems(entry, allowed_keys, label):
    problems = []
    if not isinstance(entry, dict):
        return ["%s: an entry must be a JSON object" % label]
    for key in entry:
        if key not in allowed_keys:
            problems.append("%s: unknown field '%s'" % (label, key))
    if not isinstance(entry.get("id"), str) or not ID_RE.fullmatch(entry.get("id", "")):
        problems.append("%s: 'id' must be lower case words separated by dots (for example check.quote_in_source)" % label)
    if not isinstance(entry.get("version"), int) or isinstance(entry.get("version"), bool) or entry.get("version", 0) < 1:
        problems.append("%s: 'version' must be a whole number from 1" % label)
    if not isinstance(entry.get("title"), str) or not entry["title"].strip():
        problems.append("%s: 'title' is needed" % label)
    if not isinstance(entry.get("tags", []), list) or not all(isinstance(t, str) for t in entry.get("tags", [])):
        problems.append("%s: 'tags' must be a list of words" % label)
    applies = entry.get("applies_to", {})
    if not isinstance(applies, dict) or not all(isinstance(v, list) and all(isinstance(i, str) for i in v) for v in applies.values()):
        problems.append("%s: 'applies_to' must map names (claim_types, tasks, ...) to lists of words" % label)
    if entry.get("status", "draft") not in STATUSES:
        problems.append("%s: 'status' must be one of %s" % (label, ", ".join(STATUSES)))
    if not isinstance(entry.get("origin", {}), dict):
        problems.append("%s: 'origin' must be an object" % label)
    cost = entry.get("cost", {})
    if not isinstance(cost, dict) or not all(isinstance(v, (int, float, dict)) and not isinstance(v, bool) for v in cost.values()):
        problems.append("%s: 'cost' must be an object with numbers (tokens, seconds, calls)" % label)
    return problems


def validate_node(entry, label="node"):
    problems = _common_problems(entry, NODE_KEYS, label)
    if problems and not isinstance(entry, dict):
        return problems
    kind, body = entry.get("kind"), entry.get("body")
    if kind not in NODE_KINDS:
        problems.append("%s: 'kind' must be one of %s" % (label, ", ".join(NODE_KINDS)))
    if not isinstance(body, dict):
        problems.append("%s: 'body' is needed" % label)
    else:
        needed = {"model": "template", "tool": "tool", "code": "function", "script": "script", "ask_user": "question"}.get(kind)
        if needed and not isinstance(body.get(needed), str):
            problems.append("%s: a %s node needs body.%s" % (label, kind, needed))
        if kind == "model" and body.get("schema") is not None and not isinstance(body["schema"], dict):
            problems.append("%s: body.schema must be a JSON schema object" % label)
    for io in ("inputs", "outputs"):
        spec = entry.get(io, {})
        if not isinstance(spec, dict) or not isinstance(spec.get("schema", {}), dict):
            problems.append("%s: '%s' must be {\"schema\": {...}}" % (label, io))
    params = entry.get("params", {})
    if not isinstance(params, dict) or not all(isinstance(v, dict) for v in params.values()):
        problems.append("%s: 'params' must map names to {\"default\": ...}" % label)
    safety = entry.get("safety", {})
    if not isinstance(safety, dict) or any(k not in SAFETY_FLAGS or not isinstance(v, bool) for k, v in safety.items()):
        problems.append("%s: 'safety' may only contain true/false for %s" % (label, ", ".join(SAFETY_FLAGS)))
    if kind == "script" and not entry.get("safety", {}).get("runs_code"):
        problems.append("%s: a script node must declare safety.runs_code" % label)
    needs = entry.get("needs", {})
    if not isinstance(needs, dict) or not isinstance(needs.get("tools", []), list):
        problems.append("%s: 'needs' must be an object, 'tools' a list" % label)
    return problems


def validate_pipeline_entry(entry, label="pipeline"):
    problems = _common_problems(entry, PIPELINE_KEYS, label)
    if not isinstance(entry, dict):
        return problems
    if entry.get("cost_class", "normal") not in COST_CLASSES:
        problems.append("%s: 'cost_class' must be one of %s" % (label, ", ".join(COST_CLASSES)))
    if not isinstance(entry.get("nodes"), list) or not entry.get("nodes"):
        problems.append("%s: 'nodes' must be a non-empty list" % label)
    if not entry.get("result"):
        problems.append("%s: 'result' (the context name of the answer) is needed" % label)
    return problems


def _canonical(entry):
    return json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def content_hash(entry):
    return hashlib.sha256(_canonical(entry).encode("utf-8")).hexdigest()[:16]


# --- the library --------------------------------------------------------------------------------------------------------------------

class Library:
    def __init__(self, shipped_dir, user_dir=None, index_path=None, clock=time.time):
        self.shipped_dir, self.user_dir, self.index_path = shipped_dir, user_dir, index_path
        self._clock = clock
        self._lock = threading.RLock()
        self.nodes, self.pipelines = {}, {}          # (id, version) -> entry (with "_path", "_source", "_hash")
        self.errors, self.warnings = {}, []
        self.status_file = os.path.join(user_dir, "status.json") if user_dir else None
        self.reload()

    # -- loading --
    def reload(self):
        with self._lock:
            self.nodes, self.pipelines, self.errors, self.warnings = {}, {}, {}, []
            overrides = self._read_status_file()
            for source, root in (("shipped", self.shipped_dir), ("user", self.user_dir)):
                if root:
                    for entry_type, table, check in (("nodes", self.nodes, validate_node), ("pipelines", self.pipelines, validate_pipeline_entry)):
                        self._load_folder(os.path.join(root, entry_type), source, table, check)
            for table in (self.nodes, self.pipelines):
                for key, entry in table.items():
                    override = overrides.get(ref_of(*key))
                    if override and override.get("status") in STATUSES:
                        entry["status"] = override["status"]
                        entry["_status_note"] = override.get("note", "")
            self._check_references()
            self._index()

    def _read_status_file(self):
        if self.status_file and os.path.exists(self.status_file):
            try:
                with open(self.status_file, encoding="utf-8") as fp:
                    data = json.load(fp)
                return data if isinstance(data, dict) else {}
            except (OSError, ValueError):
                self.warnings.append("%s cannot be read, the status decisions in it are ignored" % self.status_file)
        return {}

    def _load_folder(self, folder, source, table, check):
        if not os.path.isdir(folder):
            return
        for entry_id in sorted(os.listdir(folder)):
            sub = os.path.join(folder, entry_id)
            if not os.path.isdir(sub):
                continue
            for name in sorted(os.listdir(sub)):
                path = os.path.join(sub, name)
                if not name.endswith(".json"):
                    continue
                try:
                    with open(path, encoding="utf-8") as fp:
                        entry = json.load(fp)
                except (OSError, ValueError) as exc:
                    self.errors[path] = "cannot be read (%s)" % exc
                    continue
                problems = check(entry, os.path.relpath(path, os.path.dirname(os.path.dirname(folder))))
                if not problems and (entry["id"] != entry_id or name != "%d.json" % entry["version"]):
                    problems = ["the file must be %s/%d.json" % (entry["id"], entry["version"])]
                if problems:
                    self.errors[path] = "; ".join(problems)
                    continue
                key = (entry["id"], entry["version"])
                if key in table:
                    self.errors[path] = "%s exists already in %s (versions are immutable, give the change a new version)" % (ref_of(*key), table[key]["_path"])
                    continue
                entry.setdefault("status", "draft")
                entry["_path"], entry["_source"], entry["_hash"] = path, source, content_hash(entry)
                table[key] = entry

    def _check_references(self):
        """pipelines whose nodes do not resolve are reported and removed (S1: a broken entry does not stop MIA)"""
        for key in list(self.pipelines):
            entry = self.pipelines[key]
            try:
                self.expand(entry)
            except LibraryError as exc:
                self.errors[entry["_path"]] = str(exc)
                del self.pipelines[key]

    # -- looking up --
    def versions(self, entry_id, entry_type="pipeline"):
        table = self.pipelines if entry_type == "pipeline" else self.nodes
        return sorted(v for (i, v) in table if i == entry_id)

    def resolve(self, ref, entry_type="pipeline", allow_draft=False):
        """the entry for "id" (the highest usable version) or "id@version" (that version, unless it is retired)"""
        table = self.pipelines if entry_type == "pipeline" else self.nodes
        name, version = split_ref(ref)
        if version is not None:
            entry = table.get((name, version))
            if entry is None:
                raise LibraryError("there is no %s '%s'" % (entry_type, ref))
            if entry["status"] == "retired":
                raise LibraryError("%s is retired" % ref)
            return entry
        allowed = USABLE + (("draft",) if allow_draft else ())
        for number in reversed(self.versions(name, entry_type)):
            if table[(name, number)]["status"] in allowed:
                return table[(name, number)]
        known = self.versions(name, entry_type)
        raise LibraryError("there is no usable %s '%s'%s" % (entry_type, name, " (only drafts or retired versions: use id@version)" if known else ""))

    # -- expanding a pipeline entry into the graph of the runner --
    def expand(self, pipeline):
        """(graph, uses, safety): the graph for pipeline.Runner, the node refs it uses, and the safety flags it needs (the maximum of its nodes)"""
        uses, safety = [], {flag: False for flag in SAFETY_FLAGS}

        def leaf(node):
            ref = node["use"]
            if "@" not in str(ref):
                raise LibraryError("%s: node '%s' must pin the version ('%s@1'): runs and evaluations refer to exact versions"
                                   % (ref_of(pipeline["id"], pipeline["version"]), node.get("id"), ref))
            try:
                entry = self.resolve(ref, "node", allow_draft=True)
            except LibraryError as exc:
                raise LibraryError("%s: %s" % (ref_of(pipeline["id"], pipeline["version"]), exc))
            where = "%s, node '%s' (%s)" % (ref_of(pipeline["id"], pipeline["version"]), node.get("id"), ref)
            if not isinstance(node.get("id"), str) or not LOCAL_ID_RE.fullmatch(node["id"]):
                raise LibraryError("%s: every node needs an id" % where)
            if entry["kind"] == "script":
                raise LibraryError("%s: script nodes cannot run yet (the sandbox is not built)" % where)
            for key in node:
                if key not in ("id", "use", "params", "wire", "output", "plain", "on_error", "default"):
                    raise LibraryError("%s: unknown field '%s'" % (where, key))
            declared = (entry.get("params") or {})
            for name in node.get("params", {}):
                if name not in declared:
                    raise LibraryError("%s: the node has no parameter '%s' (it has: %s)" % (where, name, ", ".join(declared) or "none"))
            values = {name: spec.get("default") for name, spec in declared.items()}
            values.update(node.get("params", {}))
            schema = (entry.get("inputs") or {}).get("schema", {})
            inputs = schema.get("properties")
            wire = node.get("wire", {})
            if inputs is not None:
                for name in wire:
                    if name not in inputs:
                        raise LibraryError("%s: the node has no input '%s' (it has: %s)" % (where, name, ", ".join(inputs) or "none"))
            for name in schema.get("required", []):
                if name not in wire and name not in values:
                    raise LibraryError("%s: the required input '%s' is not wired" % (where, name))
            for name in wire:
                if name in values and name in declared:
                    raise LibraryError("%s: '%s' is both a parameter and a wired input" % (where, name))
            variables = {**values, **wire}
            body = entry["body"]
            out = {"id": node["id"], "kind": entry["kind"], "library": ref_of(entry["id"], entry["version"])}
            if entry["kind"] == "model":
                out.update(template=body["template"], inputs=variables)
                for key, target in (("system", "system"), ("schema", "schema_def"), ("retries", "retries")):
                    if body.get(key) is not None:
                        out[target] = body[key]
            elif entry["kind"] == "tool":
                out.update(tool=body["tool"], args=variables)
            elif entry["kind"] == "code":
                out.update(function=body["function"], args=variables)
            elif entry["kind"] == "ask_user":
                out.update(question=body["question"], options=variables.get("options"))
            if "plain" not in node:
                out["plain"] = body.get("plain") or entry["title"]
            for key in ("output", "plain", "on_error", "default"):
                if key in node:
                    out[key] = node[key]
            uses.append(out["library"])
            for flag in SAFETY_FLAGS:
                safety[flag] = safety[flag] or bool((entry.get("safety") or {}).get(flag))
            return out

        def walk(nodes):
            result = []
            for node in nodes:
                if isinstance(node, dict) and "use" in node:
                    result.append(leaf(node))
                elif isinstance(node, dict):
                    copy = dict(node)
                    for key in ("body", "then", "else"):
                        if isinstance(copy.get(key), list):
                            copy[key] = walk(copy[key])
                    result.append(copy)
                else:
                    result.append(node)
            return result

        graph = {"name": pipeline["id"], "version": pipeline["version"], "result": pipeline["result"], "nodes": walk(pipeline["nodes"]),
                 "uses": [], "safety": safety}
        graph["uses"] = sorted(set(uses))
        return graph, graph["uses"], safety

    # -- the index (SQLite): rebuilt from the files, statistics and cases stay --
    def _connect(self):
        connection = sqlite3.connect(self.index_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _index(self):
        if not self.index_path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.index_path)), exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS entries (ref TEXT PRIMARY KEY, id TEXT, version INTEGER, type TEXT, kind TEXT, title TEXT, status TEXT, tags TEXT,
                    applies_to TEXT, cost TEXT, safety TEXT, source TEXT, path TEXT);
                CREATE TABLE IF NOT EXISTS deps (pipeline TEXT, node TEXT);
                CREATE TABLE IF NOT EXISTS seen (ref TEXT PRIMARY KEY, hash TEXT);
                CREATE TABLE IF NOT EXISTS stats (ref TEXT, task TEXT, runs INTEGER, ok INTEGER, errors INTEGER, seconds REAL, PRIMARY KEY (ref, task));
                CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, task TEXT, text TEXT, tags TEXT, applied TEXT, verdict TEXT, outcome TEXT);
            """)
            db.execute("DELETE FROM entries")
            db.execute("DELETE FROM deps")
            seen = {row["ref"]: row["hash"] for row in db.execute("SELECT ref, hash FROM seen")}
            for entry_type, table in (("node", self.nodes), ("pipeline", self.pipelines)):
                for key, entry in sorted(table.items()):
                    ref = ref_of(*key)
                    db.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               (ref, key[0], key[1], entry_type, entry.get("kind", "pipeline"), entry["title"], entry["status"], json.dumps(entry.get("tags", [])),
                                json.dumps(entry.get("applies_to", {})), json.dumps(entry.get("cost", {})), json.dumps(self._entry_safety(entry_type, entry)),
                                entry["_source"], entry["_path"]))
                    if ref in seen and seen[ref] != entry["_hash"]:
                        self.warnings.append("%s changed after it was first indexed: versions are immutable, give the change a new version" % ref)
                    db.execute("INSERT OR REPLACE INTO seen VALUES (?,?)", (ref, entry["_hash"]))
                    if entry_type == "pipeline":
                        for node_ref in self.expand(entry)[1]:
                            db.execute("INSERT INTO deps VALUES (?,?)", (ref, node_ref))

    def _entry_safety(self, entry_type, entry):
        if entry_type == "node":
            return {flag: bool((entry.get("safety") or {}).get(flag)) for flag in SAFETY_FLAGS}
        return self.expand(entry)[2]

    def used_by(self, node_ref):
        """the pipelines that use a node version"""
        if not self.index_path:
            return []
        with self._connect() as db:
            return [row["pipeline"] for row in db.execute("SELECT pipeline FROM deps WHERE node=? ORDER BY pipeline", (node_ref,))]

    # -- searching and selecting --
    def entries(self, entry_type="pipeline"):
        table = self.pipelines if entry_type == "pipeline" else self.nodes
        return [table[k] for k in sorted(table)]

    def search(self, text=None, entry_type="pipeline", tags=(), kind=None, status=None):
        """entries whose title, description, id or tags contain the text and that have all the tags"""
        found = []
        for entry in self.entries(entry_type):
            haystack = " ".join([entry["id"], entry["title"], entry.get("description", ""), " ".join(entry.get("tags", []))]).lower()
            if text and not all(word in haystack for word in text.lower().split()):
                continue
            if any(tag not in entry.get("tags", []) for tag in tags) or (kind and entry.get("kind") != kind) or (status and entry["status"] != status):
                continue
            found.append(entry)
        return found

    def stats(self, ref, task=None):
        """{"runs", "ok", "errors", "seconds" (mean per run)} summed over the tasks (or one task); None when there is nothing yet"""
        if not self.index_path:
            return None
        with self._connect() as db:
            row = db.execute("SELECT SUM(runs) r, SUM(ok) o, SUM(errors) e, SUM(seconds) s FROM stats WHERE ref=?" + (" AND task=?" if task else ""),
                             (ref, task) if task else (ref,)).fetchone()
        if not row or not row["r"]:
            return None
        return {"runs": row["r"], "ok": row["o"], "errors": row["e"], "seconds": row["s"] / row["r"]}

    def select(self, entry_type="pipeline", tags=(), applies_to=None, max_seconds=None, max_tokens=None, tools=None, sandbox=False,
               allow_web=True, allow_code=True, task=None, statuses=USABLE):
        """{"selected": [{"ref", "title", "score", "why"}], "dropped": [{"ref", "reason"}]}: candidates by hard filters first, then specificity, status, measured results and cost.
        tools: names of the tools that exist (None = not checked); sandbox: whether scripts can run; allow_web / allow_code: what the asking skill may use"""
        selected, dropped = [], []
        for entry in self.entries(entry_type):
            ref = ref_of(entry["id"], entry["version"])
            reason = self._reject(entry_type, entry, tags, applies_to or {}, max_seconds, max_tokens, tools, sandbox, allow_web, allow_code, statuses, task)
            if reason:
                dropped.append({"ref": ref, "reason": reason})
                continue
            score, why = 0.0, []
            matched = [k for k in (applies_to or {}) if k in entry.get("applies_to", {})]
            if matched:
                score += len(matched)
                why.append("declares " + ", ".join(matched))
            if entry["status"] == "trusted":
                score += 1
                why.append("trusted")
            measured = self.stats(ref, task)
            if measured and measured["runs"] >= MIN_RUNS_FOR_STATS:
                rate = measured["ok"] / measured["runs"]
                score += 2 * rate
                why.append("%d of %d runs ok, %.1f s" % (measured["ok"], measured["runs"], measured["seconds"]))
            else:
                why.append("no measurements yet")
            seconds = (measured["seconds"] if measured else None) or (entry.get("cost") or {}).get("seconds") or 0
            selected.append({"ref": ref, "title": entry["title"], "score": round(score - min(seconds, 600) / 6000.0, 4), "why": why})
        selected.sort(key=lambda c: (-c["score"], c["ref"]))
        return {"selected": selected, "dropped": dropped}

    def _reject(self, entry_type, entry, tags, applies_to, max_seconds, max_tokens, tools, sandbox, allow_web, allow_code, statuses, task):
        if entry["status"] not in statuses:
            return "status is %s" % entry["status"]
        missing = [t for t in tags if t not in entry.get("tags", [])]
        if missing:
            return "lacks tag " + ", ".join(missing)
        for key, wanted in applies_to.items():
            declared = entry.get("applies_to", {}).get(key)
            if declared is not None and wanted not in declared:
                return "does not apply to %s=%s" % (key, wanted)
        ref = ref_of(entry["id"], entry["version"])
        measured = self.stats(ref, task)
        seconds = (measured["seconds"] if measured else None) or (entry.get("cost") or {}).get("seconds")
        if max_seconds is not None and seconds and seconds > max_seconds:
            return "takes about %.1f s, more than %.1f s" % (seconds, max_seconds)
        tokens = (entry.get("cost") or {}).get("tokens")
        if max_tokens is not None and tokens and tokens > max_tokens:
            return "needs about %d tokens, more than %d" % (tokens, max_tokens)
        safety = self._entry_safety(entry_type, entry)
        if safety["reads_web"] and not allow_web:
            return "reads the web"
        if safety["runs_code"] and not allow_code:
            return "runs code"
        if entry_type == "node":
            needed_tools = (entry.get("needs") or {}).get("tools", [])
            sandboxed = (entry.get("needs") or {}).get("sandbox", False)
        else:
            needed_tools = sorted(set(self._pipeline_tools(entry)))
            sandboxed = safety["runs_code"]
        if tools is not None and any(t not in tools for t in needed_tools):
            return "needs the tool " + ", ".join(t for t in needed_tools if t not in tools)
        if sandboxed and not sandbox:
            return "needs the sandbox, which is not available"
        return None

    def _pipeline_tools(self, pipeline):
        names = []
        for ref in self.expand(pipeline)[1]:
            node = self.resolve(ref, "node", allow_draft=True)
            if node["kind"] == "tool":
                names.append(node["body"]["tool"])
            names += (node.get("needs") or {}).get("tools", [])
        return names

    # -- statistics from the run log --
    def recompute_stats(self, runs):
        """rebuilds the statistics from run records (RunLog.read()): per pipeline and node version and task, runs / ok / errors / seconds"""
        if not self.index_path:
            return
        table = {}

        def add(ref, task, ok, seconds):
            row = table.setdefault((ref, task), [0, 0, 0, 0.0])
            row[0] += 1
            row[1] += 1 if ok else 0
            row[2] += 0 if ok else 1
            row[3] += seconds or 0.0

        for run in runs:
            if run.get("pipeline") and run.get("pipeline_version"):
                add(ref_of(run["pipeline"], run["pipeline_version"]), run.get("task") or "", run.get("status") == "done", run.get("seconds"))
            starts = {}
            for event in run.get("events", []):
                library = event.get("library")
                if not library:
                    continue
                key = (event.get("node"), event.get("item"))
                if event.get("kind") == "start":
                    starts[key] = event.get("at", 0.0)
                elif event.get("kind") in ("done", "error"):
                    add(library, run.get("task") or "", event["kind"] == "done", max(0.0, event.get("at", 0.0) - starts.get(key, event.get("at", 0.0))))
        with self._connect() as db:
            db.execute("DELETE FROM stats")
            db.executemany("INSERT INTO stats VALUES (?,?,?,?,?,?)", [(ref, task, *row) for (ref, task), row in table.items()])

    # -- cases: what was checked and what came out --
    def add_case(self, task, text, tags=(), applied=(), verdict=None, outcome=None):
        with self._connect() as db:
            cursor = db.execute("INSERT INTO cases (at, task, text, tags, applied, verdict, outcome) VALUES (?,?,?,?,?,?,?)",
                                (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock())), task, text, json.dumps(list(tags)), json.dumps(list(applied)), verdict,
                                 json.dumps(outcome)))
            return cursor.lastrowid

    def similar_cases(self, tags, limit=5, task=None):
        """cases with the most tags in common (embeddings come later), newest first among equals"""
        wanted = set(tags)
        with self._connect() as db:
            rows = db.execute("SELECT * FROM cases" + (" WHERE task=?" if task else "") + " ORDER BY id DESC", (task,) if task else ()).fetchall()
        scored = [(len(wanted & set(json.loads(r["tags"]))), r) for r in rows]
        scored = [(s, r) for s, r in scored if s > 0]
        scored.sort(key=lambda p: -p[0])
        return [{"id": r["id"], "task": r["task"], "text": r["text"], "tags": json.loads(r["tags"]), "applied": json.loads(r["applied"]), "verdict": r["verdict"],
                 "outcome": json.loads(r["outcome"]) if r["outcome"] else None, "common": s} for s, r in scored[:limit]]

    # -- status: the decision of the user, kept outside the immutable files --
    def set_status(self, ref, status, note="", by="user"):
        if status not in STATUSES:
            raise LibraryError("status must be one of %s" % ", ".join(STATUSES))
        name, version = split_ref(ref)
        if version is None or ((name, version) not in self.nodes and (name, version) not in self.pipelines):
            raise LibraryError("there is no entry '%s' (use id@version)" % ref)
        if not self.status_file:
            raise LibraryError("this library has no user folder for status decisions")
        data = self._read_status_file()
        data[ref] = {"status": status, "note": note, "by": by, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock()))}
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        with open(self.status_file, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=1, ensure_ascii=False, sort_keys=True)
        self.reload()

    def diff(self, ref_a, ref_b):
        """a unified diff of two entries (same type)"""
        def get(ref):
            name, version = split_ref(ref)
            entry = self.nodes.get((name, version)) or self.pipelines.get((name, version))
            if entry is None:
                raise LibraryError("there is no entry '%s'" % ref)
            return json.dumps({k: v for k, v in entry.items() if not k.startswith("_")}, indent=1, sort_keys=True, ensure_ascii=False).splitlines()
        return "\n".join(difflib.unified_diff(get(ref_a), get(ref_b), ref_a, ref_b, lineterm=""))

    # -- writing drafts (by hand, by a model): always a new version, always a draft --
    def add_draft(self, entry_type, entry, by="user"):
        """stores a new entry as a draft in the user folder; returns its ref"""
        if not self.user_dir:
            raise LibraryError("this library has no user folder")
        entry = json.loads(json.dumps(entry))
        entry["status"] = "draft"
        entry["origin"] = {**entry.get("origin", {}), "by": by, "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock()))}
        problems = (validate_node if entry_type == "node" else validate_pipeline_entry)(entry, entry_type)
        if problems:
            raise LibraryError("; ".join(problems))
        table = self.nodes if entry_type == "node" else self.pipelines
        if (entry["id"], entry["version"]) in table:
            raise LibraryError("%s exists already: versions are immutable, use the next version number" % ref_of(entry["id"], entry["version"]))
        path = os.path.join(self.user_dir, entry_type + "s", entry["id"], "%d.json" % entry["version"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(entry, fp, indent=1, ensure_ascii=False)
            fp.write("\n")
        self.reload()
        if path in self.errors:
            os.remove(path)
            message = self.errors[path]
            self.reload()
            raise LibraryError(message)
        return ref_of(entry["id"], entry["version"])
