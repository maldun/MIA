"""
Opens a page in headless Chromium (Flatpak), waits in real time, prints the console output and saves a screenshot.
Real-time waiting matters: with --virtual-time-budget network connections (socket.io) do not get the time they need.
Run it with the MIA virtualenv (it has simple_websocket):
  python ui/tools/browser_check.py <url> <out.png> [--wait 60] [--size 1280x900] [--eval "js expression"] [--port 9333]
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

import simple_websocket

parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("out")
parser.add_argument("--wait", type=float, default=60.0, help="seconds to wait after loading")
parser.add_argument("--size", default="1280x900")
parser.add_argument("--eval", default=None, help="JavaScript expression evaluated after the wait")
parser.add_argument("--port", type=int, default=9333)
parser.add_argument("--dark", action="store_true", help="emulate a dark system theme")
parser.add_argument("--light", action="store_true", help="emulate a light system theme")
parser.add_argument("--mobile", action="store_true", help="emulate a phone (touch, device pixel ratio 2)")
parser.add_argument("--insecure", action="store_true", help="accept self-signed certificates")
args = parser.parse_args()

out_dir = os.path.dirname(os.path.abspath(args.out))
width, height = args.size.split("x")
browser = subprocess.Popen(
    ["flatpak", "run", f"--filesystem={out_dir}", "--share=network", "org.chromium.Chromium", "--headless=new",
     "--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
     f"--remote-debugging-port={args.port}", f"--window-size={width},{height}"]
    + (["--ignore-certificate-errors"] if args.insecure else []) + ["about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    target = None
    for _ in range(60):
        try:
            targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{args.port}/json", timeout=2))
            target = next(t for t in targets if t.get("type") == "page")
            break
        except Exception:
            time.sleep(0.5)
    if target is None:
        sys.exit("browser did not start")
    ws = simple_websocket.Client(target["webSocketDebuggerUrl"])
    next_id = [0]
    console = []
    requests = []

    def handle(message):
        if message.get("method") == "Network.requestWillBeSent":
            requests.append(message["params"]["request"]["url"])
        if message.get("method") == "Runtime.consoleAPICalled":
            console.append(" ".join(str(a.get("value", a.get("description", ""))) for a in message["params"]["args"]))
        elif message.get("method") == "Runtime.exceptionThrown":
            console.append("EXCEPTION " + json.dumps(message["params"]["exceptionDetails"].get("exception", {}).get("description", "")))

    def call(method, params=None, timeout=30):
        next_id[0] += 1
        ws.send(json.dumps({"id": next_id[0], "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            raw = ws.receive(timeout=1)
            if raw is None:
                continue
            message = json.loads(raw)
            if message.get("id") == next_id[0]:
                return message.get("result", {})
            handle(message)
        raise TimeoutError(method)

    def pump(seconds):
        end = time.time() + seconds
        while time.time() < end:
            raw = ws.receive(timeout=1)
            if raw:
                handle(json.loads(raw))

    print("connected", flush=True)
    call("Runtime.enable")
    call("Page.enable")
    call("Network.enable")
    if args.mobile:
        call("Emulation.setDeviceMetricsOverride", {"width": int(width), "height": int(height), "deviceScaleFactor": 2, "mobile": True})
        call("Emulation.setTouchEmulationEnabled", {"enabled": True})
    if args.dark or args.light:
        call("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": "dark" if args.dark else "light"}]})
    call("Page.navigate", {"url": args.url})
    print("navigated", flush=True)
    pump(args.wait)
    print("waited", flush=True)
    if args.eval:
        result = call("Runtime.evaluate", {"expression": args.eval, "returnByValue": True, "awaitPromise": True})
        print("EVAL", json.dumps(result.get("result", {}).get("value")))
    origin = args.url.split("/", 3)[:3]
    origin = "/".join(origin)
    external = sorted({u for u in requests if not u.startswith((origin, "data:", "blob:", "about:"))})
    print("EXTERNAL REQUESTS", json.dumps(external))
    shot = call("Page.captureScreenshot", {"format": "png"}, timeout=60)
    with open(args.out, "wb") as fp:
        fp.write(base64.b64decode(shot["data"]))
    for line in console:
        print("CONSOLE", line[:300])
    print("WROTE", args.out)
finally:
    browser.terminate()
