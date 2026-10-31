"""Runs inside localhost/mia-browser (tests/browser/Containerfile) in the network of the IF-101 mock server container (ui/tools/chat_mock_server.py):
the stage-2 browser checks of N-1.1 (TC-CLV-006, -013, -016, -018, -021; D-163 F3, F6). Prints one JSON object {scenario: result}.
    podman run --rm -i --network container:<mock> localhost/mia-browser python - http://127.0.0.1:8686 SCENARIO... < tests/browser/chat_views.py
Scenarios: touch (360 px, coarse pointer: size of every visible control), layout (360/768/1440 px in dark and light: horizontal scroll).
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


ANSWERS = "[...document.querySelectorAll('#messages .row.assistant')]"
WRITTEN = ANSWERS + ".filter((r) => !r.querySelector('[data-action=up]').hidden)"


def touch():
    """TC-CLV-016 AC-1: on a phone (coarse pointer, 360 px) every visible control of the chat, the answer actions included, is 44 x 44 px or more"""
    driver = browser(mobile=True)
    try:
        login(driver)
        send(driver, "hello")
        until(driver, WRITTEN + ".length >= 1", 20)
        return driver.execute_script("""
            const shown = (e) => e.getClientRects().length > 0 && !e.closest('dialog:not([open])') && getComputedStyle(e).visibility !== 'hidden';
            const name = (e) => e.id || e.dataset.action || e.getAttribute('aria-label') || e.textContent.trim().slice(0, 20) || e.tagName;
            return {
              coarse: matchMedia('(pointer: coarse)').matches,
              width: innerWidth,
              controls: [...document.querySelectorAll('button, select, summary, [role=button]')].filter(shown)
                .map((e) => { const r = e.getBoundingClientRect(); return { name: name(e), w: Math.round(r.width), h: Math.round(r.height) }; }),
              actions: [...document.querySelectorAll('#messages .row.assistant [data-action]')].filter(shown).map((e) => e.dataset.action),
            };""")
    finally:
        driver.quit()


def layout():
    """TC-CLV-016 AC-1: 360, 768 and 1440 px in dark and light theme: the page never scrolls sideways"""
    driver = browser()
    found = {}
    try:
        login(driver)
        for theme in ("dark", "light"):
            driver.get(BASE + "/?character=0&theme=" + theme)
            until(driver, "document.getElementById('connection').dataset.state === 'online'")
            for width in (360, 768, 1440):
                driver.set_window_size(width, 900)
                time.sleep(0.3)
                found["%s-%d" % (theme, width)] = driver.execute_script(
                    "const s = document.scrollingElement; return {theme: document.documentElement.dataset.theme, inner: innerWidth,"
                    " scroll: s.scrollWidth, sideways: s.scrollWidth > innerWidth};")
        return found
    finally:
        driver.quit()


SCENARIOS = {"touch": touch, "layout": layout}
print(json.dumps({name: SCENARIOS[name]() for name in sys.argv[2:]}))
