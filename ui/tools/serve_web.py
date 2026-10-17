"""
Serves the Godot web export (static files, correct MIME types incl. .wasm).
Phase 3 stand-in; the FastAPI backend (phase 5) takes over this job.
usage: python ui/tools/serve_web.py [port] [dir]
"""
import functools
import http.server
import mimetypes
import os
import sys

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/octet-stream", ".pck")

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8060
root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "godot", "build", "web")

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

handler = functools.partial(Handler, directory=os.path.abspath(root))
with http.server.ThreadingHTTPServer(("0.0.0.0", port), handler) as httpd:
    print(f"serving {os.path.abspath(root)} on http://0.0.0.0:{port}")
    httpd.serve_forever()
