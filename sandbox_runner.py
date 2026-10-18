"""
The part of the sandbox that runs INSIDE it (started by sandbox.py through bubblewrap; trusted code, not the script). It sets the resource limits, builds the namespace of the script
(data, a restricted set of builtins and imports, optionally `web`), runs the script, captures what it prints and reports one JSON envelope on the real stdout:

  \\x01MIA\\x01{"status": "ok" | "error", "result": ..., "stdout": "...", "truncated": bool, "error": {"type", "message", "line"} | null}

Only the standard library is available here, and only what the allowed-modules list names can be imported by the script. This restriction is a convenience and a second line of
defence; the wall is the namespaces, the missing files and the seccomp filter around this process (sandbox.py).
"""
import builtins
import io
import json
import os
import resource
import sys
import traceback

MARK = "\x01MIA\x01"
REQUEST = "\x01MIA-REQ\x01"
ANSWER = "\x01MIA-RES\x01"
SAFE_BUILTINS = (
    "abs all any ascii bin bool bytearray bytes callable chr classmethod complex dict divmod enumerate filter float format frozenset hasattr hash hex id int isinstance issubclass "
    "iter len list map max min next object oct ord pow property range repr reversed round set slice sorted staticmethod str sum super tuple type zip "
    "ArithmeticError AssertionError AttributeError BaseException Exception FloatingPointError IndexError KeyError LookupError NameError NotImplementedError OverflowError "
    "RecursionError RuntimeError StopIteration TypeError UnicodeError ValueError ZeroDivisionError ImportError ModuleNotFoundError OSError EOFError SystemExit "
    "UnicodeDecodeError UnicodeEncodeError True False None "
    "__build_class__"
).split()


class Capped(io.TextIOBase):
    """what the script prints: kept up to a limit, the rest is counted and dropped"""

    def __init__(self, limit):
        self.limit, self.parts, self.size, self.dropped = limit, [], 0, 0

    def writable(self):
        return True

    def write(self, text):
        text = str(text)
        room = self.limit - self.size
        if room > 0:
            self.parts.append(text[:room])
            self.size += min(len(text), room)
        self.dropped += max(0, len(text) - max(room, 0))
        return len(text)

    def value(self):
        return "".join(self.parts)


class WebError(RuntimeError):
    pass


class Web:
    """the only way out for a script: asks the broker outside the sandbox (GET and search, with the same safety rules and budgets as MIA's own web tools).
    The request is a line on the real stdout, the answer a line on stdin: the sandbox needs no network, no socket and no mounted file for it."""

    def __init__(self, out):
        self.out = out

    def _ask(self, request):
        try:
            self.out.write(REQUEST + json.dumps(request) + "\n")
            self.out.flush()
            line = sys.stdin.readline()
        except (OSError, ValueError) as exc:
            raise WebError("the web broker cannot be reached (%s)" % exc)
        if not line.startswith(ANSWER):
            raise WebError("the web broker did not answer")
        try:
            answer = json.loads(line[len(ANSWER):])
        except ValueError:
            raise WebError("the web broker sent an unreadable answer")
        if "error" in answer:
            raise WebError(answer["error"])
        return answer

    def get(self, url, mode="text"):
        """{"url", "status", "content_type", "title", "text", "clipped", "signals"}; mode 'text' extracts the readable text of a page, 'raw' returns the body as it is (JSON of an API)"""
        return self._ask({"op": "get", "url": str(url), "mode": mode})

    def search(self, query, count=8):
        """{"backend", "results": [{title, url, snippet}], ...}"""
        return self._ask({"op": "search", "query": str(query), "count": int(count)})


def set_limits(spec):
    memory = int(spec["memory_mb"]) * 1024 * 1024
    for name, value in (("RLIMIT_AS", memory), ("RLIMIT_CPU", int(spec["cpu_seconds"])), ("RLIMIT_FSIZE", int(spec["fsize_mb"]) * 1024 * 1024),
                        ("RLIMIT_NOFILE", 64), ("RLIMIT_CORE", 0)):
        resource.setrlimit(getattr(resource, name), (value, value))


def build_namespace(spec, data, out, real_stdout):
    allowed = set(spec["allowed_modules"])
    real_import = builtins.__import__

    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level != 0 or (name not in allowed and name.partition(".")[0] not in allowed):
            raise ImportError("importing '%s' is not allowed here" % name)
        return real_import(name, globals, locals, fromlist, level)

    if spec["raw"]:
        namespace = {"__builtins__": builtins, "__name__": "__script__"}
    else:
        safe = {name: getattr(builtins, name) for name in SAFE_BUILTINS if hasattr(builtins, name)}
        safe["__import__"] = restricted_import
        safe["print"] = lambda *args, sep=" ", end="\n", **kw: out.write(sep.join(str(a) for a in args) + end)
        namespace = {"__builtins__": safe, "__name__": "__script__"}
    namespace["data"] = data
    if spec.get("broker"):
        namespace["web"] = Web(real_stdout)
    return namespace


def run(spec):
    out = Capped(int(spec["max_output"]))
    envelope = {"status": "ok", "result": None, "stdout": "", "truncated": False, "error": None}
    real_stdout = sys.stdout
    try:
        with open("/sandbox/input.json", encoding="utf-8") as fp:
            data = json.load(fp)
        with open("/sandbox/script.py", encoding="utf-8") as fp:
            code = fp.read()
        set_limits(spec)
        namespace = build_namespace(spec, data, out, real_stdout)
        sys.stdout = out
        try:
            exec(compile(code, "<script>", "exec"), namespace)
        finally:
            sys.stdout = real_stdout
        result = namespace.get("result")
        try:
            json.dumps(result)
        except (TypeError, ValueError) as exc:
            raise ValueError("`result` must be JSON data (numbers, text, lists, dicts): %s" % exc)
        envelope["result"] = result
    except BaseException as exc:                                            # also SystemExit and MemoryError: the script's failure is a report, not a crash
        sys.stdout = real_stdout
        line = None
        for frame in traceback.extract_tb(exc.__traceback__):
            if frame.filename == "<script>":
                line = frame.lineno
        envelope["status"] = "error"
        envelope["error"] = {"type": type(exc).__name__, "message": str(exc)[:500], "line": line}
    envelope["stdout"] = out.value()
    envelope["truncated"] = out.dropped > 0
    sys.stdout = real_stdout
    real_stdout.write(MARK + json.dumps(envelope, ensure_ascii=False) + "\n")
    real_stdout.flush()


if __name__ == "__main__":
    run(json.loads(sys.argv[1]))
