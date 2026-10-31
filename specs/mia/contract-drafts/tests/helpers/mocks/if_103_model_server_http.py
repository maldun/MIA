"""HTTP stand-in of IF-103, the model server (protected; amendment A-52, D-147). An Ollama-shaped server for tests that start a whole MIA
process or container without a GPU: it answers the routes MIA calls at start and in a chat with deterministic replies. Standard library only.
It does not reproduce the quality of a real model: eval criteria are decided on the pinned model, never on this stand-in.

  python if_103_model_server_http.py [--host 127.0.0.1] [--port 11434] [--model NAME ...] [--reply TEXT]

Routes (the shapes of the Ollama API that the client `ollama` 0.6 reads):
  GET  /  and  GET /api/version           "Ollama is running", {"version"}
  GET  /api/tags,  GET /api/ps            the models given with --model (default the pins MP-full and MP-light), none loaded
  POST /api/show                          details of a listed model; 404 {"error"} for another one
  POST /api/pull                          {"status": "success"} (a stream of one line by default); the model is listed afterwards
  POST /api/chat                          the reply as a stream of NDJSON lines (one per word, then one with done: true), or one object with
                                          "stream": false; with "format" (a JSON schema or "json") the content is a JSON object with the schema's
                                          required keys, each a fixed value of its type (the first item of an enum)
  POST /api/generate                      the same for a prompt ("response" instead of "message"); an empty prompt only loads or unloads
  GET  /_calls                            the requests so far, [{"method", "path", "model"}]: for the test, not part of Ollama
"""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.0.0-mia-stand-in"
MODELS = ("gemma4:26b", "gemma4:12b-it-qat")
REPLY = "Hello. I am the stand-in of the model server."
CREATED = "2026-01-01T00:00:00Z"
FIXED = {"string": "", "number": 0, "integer": 0, "boolean": False, "array": [], "object": {}, "null": None}


def structured(schema):
    """a JSON object with the required keys of the schema, each a fixed value of its type"""
    if not isinstance(schema, dict):
        return {}
    reply = {}
    for key in schema.get("required", []):
        spec = schema.get("properties", {}).get(key, {})
        if spec.get("enum"):
            reply[key] = spec["enum"][0]
        else:
            kind = spec.get("type", "string")
            reply[key] = FIXED.get(kind[0] if isinstance(kind, list) else kind, "")
    return reply


class StandIn:
    def __init__(self, models=MODELS, reply=REPLY):
        self.models = list(models)
        self.reply = reply
        self.calls = []
        self.lock = threading.Lock()

    def model_entry(self, name):
        details = {"format": "gguf", "family": "stand-in", "parameter_size": "0B", "quantization_level": "none"}
        return {"name": name, "model": name, "modified_at": CREATED, "size": 0, "digest": "0" * 64, "details": details}

    def answer_text(self, body):
        if body.get("format"):
            return json.dumps(structured(body["format"]))
        return self.reply


class Handler(BaseHTTPRequestHandler):
    stand_in = None                                   # set by make_server

    def log_message(self, *args):                     # quiet: the test prints what it needs
        pass

    def send_json(self, value, status=200):
        data = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_lines(self, values):
        data = b"".join(json.dumps(value).encode("utf-8") + b"\n" for value in values)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            value = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            value = {}
        return value if isinstance(value, dict) else {}

    def record(self, body=None):
        with self.stand_in.lock:
            self.stand_in.calls.append({"method": self.command, "path": self.path, "model": (body or {}).get("model")})

    def do_HEAD(self):
        self.record()
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        stand_in = self.stand_in
        if self.path == "/_calls":
            with stand_in.lock:
                return self.send_json(list(stand_in.calls))
        self.record()
        if self.path == "/":
            data = b"Ollama is running"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        if self.path == "/api/version":
            return self.send_json({"version": VERSION})
        if self.path == "/api/tags":
            return self.send_json({"models": [stand_in.model_entry(name) for name in stand_in.models]})
        if self.path == "/api/ps":
            return self.send_json({"models": []})
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        body = self.body()
        self.record(body)
        route = {"/api/show": self.show, "/api/pull": self.pull, "/api/chat": self.chat, "/api/generate": self.generate}.get(self.path)
        if route is None:
            return self.send_json({"error": "not found"}, 404)
        route(body)

    def show(self, body):
        name = body.get("model") or body.get("name")
        if name not in self.stand_in.models:
            return self.send_json({"error": "model '%s' not found" % name}, 404)
        entry = self.stand_in.model_entry(name)
        self.send_json({"modelfile": "", "parameters": "", "template": "{{ .Prompt }}", "details": entry["details"],
                        "model_info": {}, "capabilities": ["completion"], "modified_at": CREATED})

    def pull(self, body):
        name = body.get("model") or body.get("name")
        with self.stand_in.lock:
            if name and name not in self.stand_in.models:
                self.stand_in.models.append(name)
        if body.get("stream", True):
            return self.send_lines([{"status": "success"}])
        self.send_json({"status": "success"})

    def answer(self, body, wrap):
        """the reply as stream lines or one object; wrap(text) is the part that differs between chat and generate"""
        model = body.get("model", "")
        text = self.stand_in.answer_text(body)
        tokens_in = sum(len(str(m.get("content", "")).split()) for m in body.get("messages", []) if isinstance(m, dict))
        tokens_in += len(str(body.get("prompt", "")).split())
        done = {"model": model, "created_at": CREATED, "done": True, "done_reason": "stop", "total_duration": 0, "load_duration": 0,
                "prompt_eval_count": tokens_in, "prompt_eval_duration": 0, "eval_count": len(text.split()), "eval_duration": 0}
        if not body.get("stream", True):
            return self.send_json(dict(done, **wrap(text)))
        words = text.split(" ")
        pieces = [word if i == 0 else " " + word for i, word in enumerate(words)]
        lines = [dict({"model": model, "created_at": CREATED, "done": False}, **wrap(piece)) for piece in pieces]
        self.send_lines(lines + [dict(done, **wrap(""))])

    def chat(self, body):
        if body.get("model") not in self.stand_in.models:
            return self.send_json({"error": "model '%s' not found" % body.get("model")}, 404)
        self.answer(body, lambda text: {"message": {"role": "assistant", "content": text}})

    def generate(self, body):
        if body.get("model") not in self.stand_in.models:
            return self.send_json({"error": "model '%s' not found" % body.get("model")}, 404)
        if not body.get("prompt"):                    # load or unload (keep_alive 0): no text
            reason = "unload" if body.get("keep_alive") in (0, "0", "0s") else "load"
            return self.send_json({"model": body.get("model"), "created_at": CREATED, "response": "", "done": True, "done_reason": reason})
        self.answer(body, lambda text: {"response": text})


def make_server(host="127.0.0.1", port=11434, models=MODELS, reply=REPLY):
    """a ThreadingHTTPServer with its own stand-in (port 0 picks a free one: server.server_address[1]); call serve_forever in a thread"""
    handler = type("StandInHandler", (Handler,), {"stand_in": StandIn(models, reply)})
    return ThreadingHTTPServer((host, port), handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ollama-shaped stand-in of the model server (IF-103, A-52)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--model", action="append", help="a model the stand-in lists (repeat; default the pins)")
    parser.add_argument("--reply", default=REPLY)
    args = parser.parse_args(argv)
    server = make_server(args.host, args.port, args.model or MODELS, args.reply)
    print("model server stand-in on http://%s:%d" % server.server_address[:2], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
