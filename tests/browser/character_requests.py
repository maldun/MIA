"""Runs inside localhost/mia-browser (tests/browser/Containerfile): opens each page given on the command line, waits 3 s and prints, as JSON
{page: {urls, secure, src, hidden}}, every request of that page (Chromium's performance log) and the state of the character iframe.
Used by tests/test_character_requests.py (TC-CHV-001, TC-CHV-012).
    podman run --rm -i --network host --add-host mia-lan:127.0.0.1 localhost/mia-browser python - URL... < tests/browser/character_requests.py
"""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/chromium"
# SwiftShader gives headless Chromium WebGL 2, so a secure page really loads the character (the control case)
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--enable-unsafe-swiftshader", "--disable-background-networking",
            "--disable-component-update", "--disable-sync", "--no-first-run", "--disable-default-apps"):
    options.add_argument(arg)
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
pages = {}
try:
    for page in sys.argv[1:]:
        driver.get_log("performance")                       # drop what the page before sent
        driver.get(page)
        time.sleep(3)
        urls = []
        for entry in driver.get_log("performance"):
            message = json.loads(entry["message"])["message"]
            if message["method"] == "Network.requestWillBeSent":
                urls.append(message["params"]["request"]["url"])
        state = driver.execute_script("const f = document.getElementById('character');"
                                      "return {secure: window.isSecureContext, src: f.getAttribute('src'), hidden: f.hidden};")
        pages[page] = dict(state, urls=urls)
finally:
    driver.quit()
print(json.dumps(pages))
