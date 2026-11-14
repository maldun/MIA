"""Runs inside localhost/mia-browser in the network of the container of ui/tools/real_backend_stub.py: TC-CLV-038 (G-V3.PANEL). Logs in as the seeded account, loads the page, reads the Skill run view,
reloads the page and reads it again. Prints one JSON object {"first": view, "reloaded": view}; a view is {"header", "state", "counts", "result"} or {"error": "<text>"}.
    podman run --rm -i --network container:<stub> localhost/mia-browser python - http://127.0.0.1:8686 < tests/browser/skill_run_restart.py
"""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

BASE = sys.argv[1].rstrip("/")
ACCOUNT = ("anna", "pw-anna-1234")


def browser():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update",
                "--disable-sync", "--no-first-run", "--disable-default-apps", "--window-size=1440,900"):
        options.add_argument(arg)
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    driver.set_script_timeout(30)
    return driver


def until(driver, script, seconds=8):
    end = time.time() + seconds
    while time.time() < end:
        if driver.execute_script("return Boolean(%s)" % script):
            return True
        time.sleep(0.1)
    return False


def login(driver):
    driver.get(BASE + "/?character=0")
    until(driver, "document.getElementById('login').open", 15)
    driver.execute_script("""
        document.getElementById('login-user').value = arguments[0];
        document.getElementById('login-password').value = arguments[1];
        document.getElementById('login-form').requestSubmit();""", *ACCOUNT)
    time.sleep(0.5)
    until(driver, "document.readyState === 'complete' && !document.getElementById('login').open && document.getElementById('connection').dataset.state === 'online'", 15)


def view(driver):
    try:
        until(driver, "document.getElementById('srv-header') && document.getElementById('srv-header').textContent.trim() !== ''")
        driver.execute_script("const d = document.getElementById('srv-full'); if (d && !d.open) d.querySelector('summary').click();")
        time.sleep(0.3)
        return driver.execute_script("""
            const text = (selector) => { const e = document.querySelector(selector); return e ? e.textContent.trim() : null; };
            return { header: text('#srv-header'), state: text('#srv-state'), result: text('#srv-result'),
                     counts: [...document.querySelectorAll('#skill-run-view .srv-count')].map((e) => e.textContent.trim()) };""")
    except Exception as error:
        return {"error": "%s: %s" % (type(error).__name__, str(error)[:300])}


if __name__ == "__main__":
    driver = browser()
    try:
        login(driver)
        out = {"first": view(driver)}
        driver.refresh()
        until(driver, "document.readyState === 'complete'", 15)
        out["reloaded"] = view(driver)
        print(json.dumps(out))
    finally:
        driver.quit()
