"""Runs inside localhost/mia-browser (tests/browser/Containerfile) in the network of the stub server container (ui/tools/chat_stub_server.py):
the stage-2 browser check TC-CLV-053 (REQ-CLV-053, 054, A-158). Prints one JSON object {scenario: result}.
    podman run --rm -i --network container:<stub> localhost/mia-browser python - http://127.0.0.1:8685 live_line < tests/browser/run_line.py
Scenario live_line: the page sends `run` (a scripted skill run of the stub: phases, a question, the end message), and 3 s later a second message while the run works.
The result is a list of samples taken every 0.25 s: the text of the status line (or null), whether it is the last element of #messages, and the last row's text."""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

BASE = sys.argv[1].rstrip("/")
SAMPLE_JS = """
  const list = document.getElementById('messages');
  const line = list.querySelector('.run-line');
  const rows = list.querySelectorAll('.row');
  const last = rows.length ? rows[rows.length - 1] : null;
  return {line: line ? line.querySelector('.run-line-text').textContent : null,
          link: line ? line.querySelector('a').getAttribute('href') : null,
          lineIsLast: line ? list.lastElementChild === line : null,
          lastRow: last ? last.textContent.slice(0, 80) : null};"""


def browser():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update",
                "--disable-sync", "--no-first-run", "--disable-default-apps", "--window-size=1440,900"):
        options.add_argument(arg)
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    driver.set_script_timeout(30)
    return driver


def until(driver, script, seconds=15):
    end = time.time() + seconds
    while time.time() < end:
        if driver.execute_script("return Boolean(%s)" % script):
            return True
        time.sleep(0.1)
    return False


def send(driver, text):
    driver.execute_script("""
        const input = document.getElementById('input');
        input.value = arguments[0]; input.dispatchEvent(new Event('input', { bubbles: true }));
        document.getElementById('send').click();""", text)


def live_line(driver):
    driver.get(BASE + "/?character=0")
    until(driver, "document.readyState === 'complete' && document.getElementById('connection').dataset.state === 'online'")
    send(driver, "run")
    samples, started, second = [], time.time(), False
    while time.time() - started < 16:
        samples.append(driver.execute_script(SAMPLE_JS))
        if not second and time.time() - started > 3:
            send(driver, "hello")
            second = True
        time.sleep(0.25)
        if samples[-1]["line"] is None and time.time() - started > 12 and samples[-1]["lastRow"] and "Skill run view" in samples[-1]["lastRow"]:
            break
    return samples


def main():
    results = {}
    for name in sys.argv[2:]:
        driver = browser()
        try:
            results[name] = {"live_line": live_line}[name](driver)
        finally:
            driver.quit()
    print(json.dumps(results))


main()
