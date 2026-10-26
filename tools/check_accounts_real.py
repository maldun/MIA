"""The real MIA backend (web_app + the real light model through Ollama) with the accounts switched on, driven like a browser would.
Run in the image by tools/check_accounts_real.sh (the checkout is mounted at /work)."""
import json
import os
import shutil
import sys
import tempfile
import time

repo = "/work"
link = tempfile.mkdtemp()
os.symlink(repo, os.path.join(link, "MIA"))
sys.path.insert(0, link)
sys.path.insert(0, repo)

data = tempfile.mkdtemp()
cfg = json.load(open(os.path.join(repo, "setup_cfg.example.json")))
cfg.update(
    accounts_enabled=True, accounts_dir=os.path.join(data, "db"), changes_log=os.path.join(data, "changes.jsonl"),
    ollama_managed=False, ollama_pull=False, ollama_host="http://127.0.0.1:11434", default_profile="light",
    chat_log=os.path.join(data, "chat_log.jsonl"), history_file=os.path.join(data, "memories.json"),
    long_time_history_file=os.path.join(data, "long_time_history.json"), feedback_log=os.path.join(data, "feedback.jsonl"),
    presets_dir=os.path.join(data, "presets"), gestures_dir=os.path.join(data, "gestures"), editor_token_file=os.path.join(data, "editor_token.txt"),
    tailscale=False, https_port=None, tts_warmup=False,
)
cfg_path = os.path.join(repo, "setup_cfg.json")
had = os.path.exists(cfg_path)
if had:
    shutil.copy(cfg_path, cfg_path + ".e2e.bak")
json.dump(cfg, open(cfg_path, "w"))


def say(*args):
    print(*args, flush=True)


try:
    import accounts
    from storage import Storage
    from storage_files import FileBackend
    accounts.create(Storage(FileBackend(cfg["accounts_dir"])), "anna", "pw-anna-1", "owner")
    say("importing the real web_app ...")
    from MIA import web_app as w
    w.play_intro_sound = lambda: None
    web = w.app.test_client()

    say("1 no session: history", web.get("/api/chat/history").status_code, "| page", web.get("/").status_code)
    foreign = w.socketio.test_client(w.app, flask_test_client=w.app.test_client())
    say("2 socket without a session connected:", foreign.is_connected())
    say("3 login:", web.post("/api/login", json={"user": "anna", "password": "pw-anna-1"}).status_code, "| whoami", web.get("/api/whoami").get_json())
    sock = w.socketio.test_client(w.app, flask_test_client=web)
    say("4 socket with the session connected:", sock.is_connected())
    ack = sock.emit("chat_send", {"id": "real1", "text": "Say hello to me in five words."}, callback=True)
    say("5 ack:", {k: ack[k] for k in ("ok", "queued") if k in ack}, "| sender of the stored message:", (ack.get("message") or {}).get("sender"))
    deadline, events = time.time() + 240, []
    while time.time() < deadline:
        events += sock.get_received()
        if any(e["name"] == "chat_done" for e in events):
            break
        time.sleep(1)
    names = [e["name"] for e in events]
    done = [e for e in events if e["name"] == "chat_done"]
    say("6 events:", sorted(set(names)), "| deltas:", names.count("chat_delta"))
    answer = (done[-1]["args"][0] if done else {})
    say("7 answer:", str(answer.get("text", answer))[:160])
    history = web.get("/api/chat/history").get_json()["messages"]
    say("8 history:", [(m["role"], m.get("sender")) for m in history])
    rows = [json.loads(line) for line in open(cfg["changes_log"])]
    say("9 changes:", [(r["account"], r["action"]) for r in rows])
    say("10 logout:", web.post("/api/logout").status_code, "| socket still connected:", sock.is_connected(), "| history now", web.get("/api/chat/history").status_code)
    ok = (done and any(m["role"] == "user" and m.get("sender") == "anna" for m in history) and not foreign.is_connected() and not sock.is_connected())
    say("RESULT:", "OK" if ok else "PROBLEM")
finally:
    if had:
        shutil.move(cfg_path + ".e2e.bak", cfg_path)
    elif os.path.exists(cfg_path):
        os.remove(cfg_path)
    sys.stdout.flush()
    os._exit(0)                                          # the scheduler and helper threads of web_app would keep the process alive
