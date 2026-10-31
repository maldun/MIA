"""Runs inside localhost/mia-browser (tests/browser/Containerfile): loads the chat page, lets the stub server announce one voice line, and prints
every request of the session from Chromium's performance log as JSON {played, urls, console}. Used by tests/test_page_requests.py (TC-VPB-004).
    podman run --rm -i --network host localhost/mia-browser python - URL < tests/browser/page_requests.py
"""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

url = sys.argv[1]
options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/chromium"
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required",
            "--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run",
            "--disable-default-apps", "--disable-domain-reliability", "--metrics-recording-only"):
    options.add_argument(arg)
options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
try:
    driver.set_script_timeout(20)
    driver.get(url)
    # one voice line: a short wav uploaded as the speech process does; the page plays it (autoplay allowed by the flag above)
    played = driver.execute_async_script("""
const done = arguments[arguments.length - 1];
const audio = document.getElementById('audio');
const seen = [];
for (const name of ['playing', 'ended', 'error']) audio.addEventListener(name, () => seen.push(name));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  await wait(1500);
  const rate = 8000, n = 4000, buffer = new ArrayBuffer(44 + n * 2), v = new DataView(buffer);
  const text = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  text(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); text(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, 1, true); v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  text(36, 'data'); v.setUint32(40, n * 2, true);
  const form = new FormData();
  form.append('file', new Blob([buffer], { type: 'audio/wav' }), 'line.wav');
  await fetch('/upload', { method: 'POST', body: form });
  const start = Date.now();
  while (Date.now() - start < 8000 && !seen.includes('ended') && !seen.includes('error')) await wait(100);
  window.miaChat?.sound?.stop?.();
  done(seen);
})();
""")
    time.sleep(0.5)
    urls = []
    for entry in driver.get_log("performance"):
        message = json.loads(entry["message"])["message"]
        if message["method"] == "Network.requestWillBeSent":
            urls.append(message["params"]["request"]["url"])
        elif message["method"] == "Network.webSocketCreated":
            urls.append(message["params"]["url"])
    console = [entry["message"] for entry in driver.get_log("browser")]
    print(json.dumps({"played": played, "urls": urls, "console": console}))
finally:
    driver.quit()
