"""The test server of the graph viewer's browser checks (G-V4.VIEW, protected; TR-VIEW-009, page-interface-note.md section 4).

One origin on 127.0.0.1 at a free port: the real provider `graph_api_v2.create_app` (the account routes and IF-104 v2 under /api/) and the page
`graph_app/` at /graph/, on a throw-away file store seeded with the fixture graphs (TR-VIEW-002) and a throw-away accounts store with anna (made
first, the owner) and ben (TR-VIEW-003). The allowed origin is the server's own. Used by tests/acceptance/test_graph_view_browser.py and by the
opening-time smoke check (SMOKE-VIEW-002, with `ids` limited to chain.fifty).

    server = graph_view_server.start()       # raises RuntimeError naming the missing provider until Track A has built it
    ... server.url, server.origin ...
    server.stop()
"""
import os
import shutil
import socket
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for path in (REPO, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import graph_view_data  # noqa: E402

PASSWORDS = {"anna": "pw-anna", "ben": "pw-ben"}


class Server:
    def __init__(self, url, http, thread, folders):
        self.url, self.origin, self._http, self._thread, self._folders = url, url, http, thread, folders

    def stop(self):
        self._http.shutdown()
        self._thread.join(5)
        for folder in self._folders:
            shutil.rmtree(folder, True)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start(ids=None, page_folder=None):
    """the server on a new seeded store; `ids` limits the fixture graphs, `page_folder` serves another copy of graph_app/ (a planted defect)"""
    try:
        import graph_api_v2
    except ImportError as err:
        raise RuntimeError("the real provider graph_api_v2.create_app (N-2.1, Track A of G-V4.VIEW) is not built yet: %s" % err)
    import accounts
    from flask import send_from_directory
    from storage import Storage
    from storage_files import FileBackend
    from werkzeug.serving import make_server

    graphs, people = tempfile.mkdtemp(prefix="view-graphs-"), tempfile.mkdtemp(prefix="view-accounts-")
    backend = FileBackend(graphs)
    graph_view_data.seed(backend, ids=ids)
    accounts_store = Storage(FileBackend(people))
    for name in ("anna", "ben"):
        accounts.create(accounts_store, name, PASSWORDS[name], "view-tests")
    port = _free_port()
    url = "http://127.0.0.1:%d" % port
    app = graph_api_v2.create_app(backend, accounts_store, "files", allowed_origins=(url,))
    page = page_folder or os.path.join(REPO, "graph_app")
    app.add_url_rule("/graph/", "graph_view_index", lambda: send_from_directory(page, "index.html"))
    app.add_url_rule("/graph/<path:name>", "graph_view_file", lambda name: send_from_directory(page, name))
    http = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    return Server(url, http, thread, (graphs, people))
