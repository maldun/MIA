"""Runs inside localhost/mia-browser (tests/browser/Containerfile) in the network of the IF-101 mock server container (ui/tools/chat_mock_server.py):
the stage-2 browser checks of N-1.1 (TC-CLV-006, -013, -016, -018, -021; D-163 F3, F6). Prints one JSON object {scenario: result}.
    podman run --rm -i --network container:<mock> -v <checkout>/ui/tools:/tools:ro,z localhost/mia-browser python - http://127.0.0.1:8686 SCENARIO... < tests/browser/chat_views.py
Scenarios: touch (360 px, coarse pointer: size of every visible control), layout (360/768/1440 px in dark and light: horizontal scroll),
views (the click-through /tools/chat_views_e2e.js with the character blocked; requests and socket events), lan (login over plain HTTP by a
home-network name), offline (connection cut and back).
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


def requests_and_events(driver):
    """every request of the session (Chromium's performance log) and the Socket.IO events in the websocket frames, both directions
    (the first events before the upgrade from polling to the websocket are not in the log)"""
    urls, events = [], set()
    for entry in driver.get_log("performance"):
        message = json.loads(entry["message"])["message"]
        if message["method"] == "Network.requestWillBeSent":
            urls.append(message["params"]["request"]["url"])
        elif message["method"] == "Network.webSocketCreated":
            urls.append(message["params"]["url"])
        elif message["method"] in ("Network.webSocketFrameSent", "Network.webSocketFrameReceived"):
            payload = message["params"]["response"]["payloadData"]
            if payload.startswith("42"):                         # Engine.IO message + Socket.IO event, maybe with an ack id: 42[...] or 4217[...]
                events.add(json.loads(payload[2:].lstrip("0123456789"))[0])
    return urls, sorted(events)


def views():
    """TC-CLV-006, -013, -021: the click-through of every view (ui/tools/chat_views_e2e.js) with the character iframe blocked, then one more
    answer without a variant; every request and socket event of the session is recorded"""
    driver = browser(extra=("--enable-unsafe-swiftshader",))   # WebGL, so the page really tries to load the character
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*/character/*"]})
        login(driver, query="")
        attempted = driver.execute_script("return document.getElementById('character').getAttribute('src')")
        with open("/tools/chat_views_e2e.js", encoding="utf-8") as handle:
            script = handle.read()
        driver.set_script_timeout(180)
        result = json.loads(driver.execute_async_script(
            "const done = arguments[arguments.length - 1];\n(\n" + script + "\n).then(done, (e) => done(JSON.stringify({problems: ['error: ' + e]})));"))
        label_after_variant = driver.execute_script("const v = document.getElementById('variant'); return v.hidden ? null : v.textContent")
        answers = driver.execute_script("return %s.length" % ANSWERS)
        send(driver, "one more")
        until(driver, WRITTEN + ".length > %d" % answers, 20)
        time.sleep(0.5)
        label_after_plain = driver.execute_script("const v = document.getElementById('variant'); return v.hidden ? null : v.textContent")
        urls, events = requests_and_events(driver)
        return {"problems": result["problems"], "tabs": result.get("tabs"), "attempted": attempted,
                "label_after_variant": label_after_variant, "label_after_plain": label_after_plain, "urls": urls, "events": events}
    finally:
        driver.quit()


def lan():
    """TC-CLV-018: the page reached over plain HTTP by a name of the home network (mapped to loopback): the login form is switched off
    with its reason, and a submit sends nothing"""
    driver = browser(extra=("--host-resolver-rules=MAP mia-lan 127.0.0.1",))
    try:
        driver.get(BASE.replace("127.0.0.1", "mia-lan") + "/?character=0")
        until(driver, "document.getElementById('login').open")
        state = driver.execute_script("""
            const $ = (id) => document.getElementById(id);
            $('login-user').disabled = false; $('login-password').disabled = false;          // even if a user forces the fields open
            $('login-user').value = 'anna'; $('login-password').value = 'pw-anna';
            $('login-form').requestSubmit();
            return { host: location.host, submitDisabled: $('login-submit').disabled, error: $('login-error').hidden ? null : $('login-error').textContent };""")
        time.sleep(1.0)
        urls, _ = requests_and_events(driver)
        return dict(state, logins=[url for url in urls if "/api/login" in url])
    finally:
        driver.quit()


def offline():
    """TC-CLV-004: the connection is cut (the socket's transport is closed): the page shows the state, keeps the draft, switches Send off and
    comes back online without a reload"""
    driver = browser()
    try:
        login(driver)
        driver.execute_script("""
            window.notReloaded = true;
            const input = document.getElementById('input');
            input.value = 'my unsent draft'; input.dispatchEvent(new Event('input', { bubbles: true }));
            window.miaChat.socket.io.engine.close();""")
        until(driver, "document.getElementById('connection').dataset.state !== 'online'", 5)
        cut = driver.execute_script("""
            const $ = (id) => document.getElementById(id);
            return { state: $('connection').dataset.state, banner: !$('banner').hidden, send: $('send').disabled, draft: $('input').value };""")
        back = until(driver, "document.getElementById('connection').dataset.state === 'online'", 20)
        after = driver.execute_script("return { draft: document.getElementById('input').value, notReloaded: window.notReloaded === true }")
        return {"cut": cut, "back": back, "after": after}
    finally:
        driver.quit()


SCENARIOS = {"touch": touch, "layout": layout, "views": views, "lan": lan, "offline": offline}
print(json.dumps({name: SCENARIOS[name]() for name in sys.argv[2:]}))
