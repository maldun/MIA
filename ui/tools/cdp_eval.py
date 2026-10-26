"""Drives a headless Chromium that is already running with a debugging port, for the click-throughs of the chat page (ui/tools/*_e2e.js).

  1. start the browser once (it keeps running; the page and its cookies stay between calls):
       flatpak run --share=network org.chromium.Chromium --headless=new --no-sandbox --disable-gpu --remote-debugging-port=9333 about:blank &
  2. python ui/tools/cdp_eval.py JSFILE [URL] [wait_seconds_after_load]
       navigates to URL (if given), waits, then evaluates the JavaScript of JSFILE (an expression or an async function that is called at once)
       and prints its value. A page that reloads during the script (the login does) ends the call with "Execution context was destroyed": that is
       normal, run the next script.
  Example: a mock server (ANSWER_DELAY=1 EVENT_GAP=0.05 python ui/tools/chat_mock_server.py), then
       python ui/tools/cdp_eval.py ui/tools/chat_login_e2e.js "http://127.0.0.1:8686/?character=0" 3   (fills and submits the login form)
       python ui/tools/cdp_eval.py ui/tools/chat_views_e2e.js                        (the click-through; prints {"problems": []} when all is well)
Why not browser_check.py: it starts its own browser and waits for the debugging port; when an older headless Chromium still holds the port it hangs.
Needs simple_websocket (in the MIA virtualenv). The port is MIA_CDP_PORT (default 9333)."""
import json
import os
import sys
import time
import urllib.request

import simple_websocket

port = int(os.environ.get("MIA_CDP_PORT", "9333"))
js_file = sys.argv[1]
url = sys.argv[2] if len(sys.argv) > 2 else None
wait = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

targets = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=5))
page = next(t for t in targets if t.get("type") == "page")
ws = simple_websocket.Client(page["webSocketDebuggerUrl"])
counter = [0]


def call(method, params=None, timeout=60):
    counter[0] += 1
    ws.send(json.dumps({"id": counter[0], "method": method, "params": params or {}}))
    end = time.time() + timeout
    while time.time() < end:
        raw = ws.receive(timeout=1)
        if raw is None:
            continue
        message = json.loads(raw)
        if message.get("id") == counter[0]:
            return message.get("result", message.get("error"))
    raise TimeoutError(method)


call("Page.enable")
call("Runtime.enable")
if url:
    call("Page.navigate", {"url": url})
    time.sleep(wait)
code = open(js_file, encoding="utf-8").read()
result = call("Runtime.evaluate", {"expression": code, "awaitPromise": True, "returnByValue": True}, timeout=90)
value = result.get("result", {}).get("value", result)
print(value if isinstance(value, str) else json.dumps(value))
ws.close()
