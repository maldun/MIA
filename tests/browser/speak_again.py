"""Runs inside localhost/mia-browser (tests/browser/Containerfile) in the network of the IF-101 mock server container (ui/tools/chat_mock_server.py):
the stage-2 browser check TC-VPB-007 (REQ-VPB-006, A-132 TD-11). Prints one JSON object {scenario: result}.
    podman run --rm -i --network container:<mock> localhost/mia-browser python - http://127.0.0.1:8686 stop_then_button stop_then_late_line < tests/browser/speak_again.py
Scenarios (each in its own browser): an answer is shown, the voice is stopped, and 1 s later
  stop_then_button     the speaker button under the answer is pressed (the mock answers it with an audio_reload, as the backend does);
  stop_then_late_line  an audio_reload comes without any request (the mock is told to send one).
The result is the list of urls the page's audio element was asked to play (HTMLMediaElement.play is wrapped to record `src`)."""
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

BASE = sys.argv[1].rstrip("/")
ACCOUNT = ("anna", "pw-anna")
AFTER_STOP_S = 1.0          # the Stop was this long ago when the request or the line comes (inside the 3 s of STOP_DROP_MS)
LISTEN_S = 1.2              # how long a dropped line is waited for (1.0 + 1.2 stays inside the 3 s window)


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


def start(driver):
    """logs in, records every play() of an audio element, sends a message and waits until its answer shows the speaker button"""
    driver.get(BASE + "/?character=0")
    until(driver, "document.getElementById('login').open")
    driver.execute_script("""
        document.getElementById('login-user').value = arguments[0];
        document.getElementById('login-password').value = arguments[1];
        document.getElementById('login-form').requestSubmit();""", *ACCOUNT)
    time.sleep(0.5)
    until(driver, "document.readyState === 'complete' && !document.getElementById('login').open"
                  " && document.getElementById('connection').dataset.state === 'online'")
    # the history of earlier runs shows answers at once, so the end of the NEW answer is awaited by its chat_done: its chat_start would end a Stop
    driver.execute_script("""
        window.played = [];
        window.done = 0;
        window.reloads = 0;
        window.miaChat.socket.on('chat_done', () => { window.done += 1; });
        window.miaChat.socket.on('audio_reload', () => { window.reloads += 1; });
        const play = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function () { window.played.push(this.getAttribute('src') || this.src); return play.call(this); };
        const input = document.getElementById('input');
        input.value = 'hello'; input.dispatchEvent(new Event('input', { bubbles: true }));
        document.getElementById('send').click();""")
    if not until(driver, "window.done >= 1", 30):
        raise AssertionError("the answer did not end")
    time.sleep(0.5)          # the page has drawn the answer and its actions
    driver.execute_script("window.played = []; window.reloads = 0;")


def outcome(driver):
    """what the page did: the urls it was asked to play, and how many audio_reload events reached it (so that "nothing played" is not "nothing sent")"""
    return {"played": driver.execute_script("return window.played;"), "reloads": driver.execute_script("return window.reloads;")}


def stop_the_voice(driver):
    """the Stop of the composer silences the voice of the page by this call (app.js onStop)"""
    driver.execute_script("window.miaChat.sound.stop();")
    time.sleep(AFTER_STOP_S)


def stop_then_button():
    driver = browser()
    try:
        start(driver)
        stop_the_voice(driver)
        driver.execute_script("[...document.querySelectorAll('#messages .row.assistant [data-action=speak]')].pop().click();")
        until(driver, "window.played.length > 0", LISTEN_S + 2)
        return outcome(driver)
    finally:
        driver.quit()


def stop_then_late_line():
    driver = browser()
    try:
        start(driver)
        stop_the_voice(driver)
        driver.execute_script("fetch('/mock/audio_reload', {method: 'POST', credentials: 'same-origin'});")
        time.sleep(LISTEN_S)
        return outcome(driver)
    finally:
        driver.quit()


SCENARIOS = {"stop_then_button": stop_then_button, "stop_then_late_line": stop_then_late_line}
print(json.dumps({name: SCENARIOS[name]() for name in sys.argv[2:]}))
