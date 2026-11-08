"""Runs inside localhost/mia-browser (tests/browser/Containerfile) in the network of the IF-101 mock server container (ui/tools/chat_mock_server.py,
started with MOCK_SEED_FILES=1): the stage-2 browser checks TC-CLV-023 (status card, TD-01) and TC-CLV-024 (files list, TD-02). Prints one JSON object
{scenario: result}.
    podman run --rm -i --network container:<mock> localhost/mia-browser python - http://127.0.0.1:8686 SCENARIO... < tests/browser/task_files.py
Scenarios: card (a /review of the mock on a phone of 360 px: the card, an update in place, pause, resume, stop, a late status), files (the Files tab:
order, links, redraw after files_changed, no delete).
"""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

BASE = sys.argv[1].rstrip("/")
ACCOUNT = ("anna", "pw-anna")


def browser(mobile=False, extra=()):
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update",
                "--disable-sync", "--no-first-run", "--disable-default-apps", "--window-size=1440,900", *extra):
        options.add_argument(arg)
    if mobile:                       # a phone: 360 px, touch; Chromium then answers `pointer: coarse`
        options.add_experimental_option("mobileEmulation", {"deviceMetrics": {"width": 360, "height": 740, "pixelRatio": 2, "touch": True}})
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    driver.set_script_timeout(30)
    return driver


def until(driver, script, seconds=15):
    """waits until the JavaScript expression is true; returns whether it became true"""
    end = time.time() + seconds
    while time.time() < end:
        if driver.execute_script("return Boolean(%s)" % script):
            return True
        time.sleep(0.1)
    return False


def login(driver, query="?character=0"):
    driver.get(BASE + "/" + query)
    until(driver, "document.getElementById('login').open")
    driver.execute_script("""
        document.getElementById('login-user').value = arguments[0];
        document.getElementById('login-password').value = arguments[1];
        document.getElementById('login-form').requestSubmit();""", *ACCOUNT)
    time.sleep(0.5)
    until(driver, "document.readyState === 'complete' && !document.getElementById('login').open"
                  " && document.getElementById('connection').dataset.state === 'online'")


def send(driver, text):
    driver.execute_script("""
        const input = document.getElementById('input');
        input.value = arguments[0]; input.dispatchEvent(new Event('input', { bubbles: true }));
        document.getElementById('send').click();""", text)




def emit(driver, text):
    """a message on the wire of the page itself (the socket of window.miaChat), also while a dialog covers the composer"""
    driver.execute_script("window.miaChat.socket.emit('chat_send', { text: arguments[0] });", text)


CARDS = "[...document.querySelectorAll('#messages .task-card')]"
CARD_STATE = """
    return [...document.querySelectorAll('#messages .task-card')].map((c) => ({
      id: c.dataset.taskId, state: c.className.replace('task-card', '').trim(), text: c.textContent,
      buttons: [...c.querySelectorAll('button')].map((b) => b.textContent), fits: c.scrollWidth <= c.clientWidth }));"""


def card():
    """TC-CLV-023: one card per task, drawn from task_status, updated in place; Pause sends one /api/pause and shows Resume, Resume one /api/resume;
    the result ends the task with its figures and no buttons; a late status after done changes nothing; Stop ends a second task"""
    driver = browser(mobile=True)
    out = {}
    try:
        login(driver)
        driver.execute_script("""
            window.posts = [];
            const original = window.fetch.bind(window);
            window.fetch = (url, options) => { if (options && options.method === 'POST') window.posts.push(String(url)); return original(url, options); };""")
        emit(driver, "/review contract")
        out["appeared"] = until(driver, CARDS + ".length === 1", 20)
        out["first"] = driver.execute_script(CARD_STATE)
        driver.execute_script(CARDS + "[0].querySelector('button').click()")           # Pause
        out["paused"] = until(driver, CARDS + "[0].classList.contains('paused')", 10)
        out["after_pause"] = driver.execute_script(CARD_STATE)
        driver.execute_script(CARDS + "[0].querySelector('button').click()")           # Resume
        out["resumed"] = until(driver, CARDS + "[0].classList.contains('running')", 10)
        out["after_resume"] = driver.execute_script(CARD_STATE)
        emit(driver, "yes")                                                             # the answer to the question of the review: it ends
        out["done"] = until(driver, CARDS + "[0].classList.contains('done')", 20)
        out["after_done"] = driver.execute_script(CARD_STATE)
        driver.execute_script("""
            const late = { id: arguments[0], task: 'review', phase: 'late', done: false, paused: false, budget: {}, counts: {} };
            window.miaChat.socket.listeners('task_status').forEach((listener) => listener(late));""", out["after_done"][0]["id"])
        out["after_late"] = driver.execute_script(CARD_STATE)
        out["posts"] = driver.execute_script("return window.posts.filter((u) => /\\/api\\/(pause|resume)$/.test(u))")
        emit(driver, "/review again")
        out["second_appeared"] = until(driver, CARDS + ".length === 2", 20)
        driver.execute_script(CARDS + "[1].querySelectorAll('button')[1].click()")      # Stop
        out["stopped"] = until(driver, CARDS + "[1].classList.contains('done')", 20)
        out["after_stop"] = driver.execute_script(CARD_STATE)
        return out
    finally:
        driver.quit()


FILES = """
    return [...document.querySelectorAll('#workspace-body ul.files li')].map((li) => {
      const a = li.querySelector('a'); return { name: a.textContent, href: a.getAttribute('href'), download: a.hasAttribute('download'), text: li.textContent }; });"""


def files():
    """TC-CLV-024: the Files tab lists the volume newest first with a link to /api/files/<name>; a file that a task stores appears without a reload
    after files_changed; the link downloads as an attachment; there is no delete control"""
    driver = browser()
    out = {}
    try:
        login(driver)
        driver.execute_script("window.notReloaded = true; document.getElementById('menu-button').click(); document.getElementById('workspace-button').click();")
        until(driver, "document.getElementById('workspace').open && document.querySelectorAll('#workspace-tabs button').length > 0", 10)
        driver.execute_script("[...document.querySelectorAll('#workspace-tabs button')].find((b) => b.textContent === 'Files').click();")
        out["before"] = until(driver, "document.querySelectorAll('#workspace-body ul.files li').length === 1", 10) and driver.execute_script(FILES)
        emit(driver, "/review contract")                     # while the dialog is open: the task stores its report and sends files_changed
        until(driver, "document.querySelectorAll('#messages .task-card').length === 1", 20)     # the review runs and waits for its answer
        emit(driver, "yes")
        out["redrawn"] = until(driver, "document.querySelectorAll('#workspace-body ul.files li').length === 2", 20)
        out["after"] = driver.execute_script(FILES)
        out["not_reloaded"] = driver.execute_script("return window.notReloaded === true")
        out["controls"] = driver.execute_script("""
            return [...document.querySelectorAll('#workspace-body button, #workspace-body [role=button]')].map((b) => b.textContent);""")
        out["download"] = driver.execute_async_script("""
            const done = arguments[arguments.length - 1];
            fetch(arguments[0]).then(async (r) => done({ status: r.status, disposition: r.headers.get('content-disposition'), body: await r.text() }));""",
                                                       out["after"][0]["href"])
        return out
    finally:
        driver.quit()


SCENARIOS = {"card": card, "files": files}
print(json.dumps({name: SCENARIOS[name]() for name in sys.argv[2:]}))
