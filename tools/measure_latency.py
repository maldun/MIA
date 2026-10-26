"""
Time to the first text of a chat answer (REQ-EVL-007, benchmark BM-MIA-001): the median of repeated runs after some warm-up runs.

  python tools/measure_latency.py --url http://127.0.0.1:8686 --user anna --password pw-anna [--runs 20] [--warmup 3] [--text "Hello"]

One run = send a chat message over the socket and wait for the first `chat_delta`. The server is the one of the page (IF-101); the login gives the session cookie.
`measure` does not know the server: it times any function that returns when the first text has arrived, so the tests use a fake one.
"""
import argparse
import json
import statistics
import time


def measure(ask, clock=time.monotonic, runs=20, warmup=3):
    """ask(): blocks until the first text of an answer has arrived. Failed runs are counted and not timed."""
    for _ in range(warmup):
        try:
            ask()
        except Exception:                                   # a warm-up that fails is no result
            pass
    times, failed = [], 0
    for _ in range(runs):
        started = clock()
        try:
            ask()
        except Exception:
            failed += 1
            continue
        times.append(clock() - started)
    result = {"runs": len(times), "failed": failed}
    if times:
        result.update(median=statistics.median(times), min=min(times), max=max(times))
    return result


def chat_ask(url, user, password, text, timeout=120):
    """a function for `measure` that talks to a running page: login, one socket, one message per call"""
    import socketio                                        # only the live mode needs it
    import requests
    session = requests.Session()
    reply = session.post(url.rstrip("/") + "/api/login", json={"user": user, "password": password}, timeout=10)
    reply.raise_for_status()
    client = socketio.Client(http_session=session)
    client.connect(url, headers={"Cookie": "; ".join("%s=%s" % (c.name, c.value) for c in session.cookies)}, wait_timeout=10)
    first = {"seen": None}
    client.on("chat_delta", lambda *_: first.update(seen=True) if first["seen"] is None else None)

    def ask():
        first["seen"] = None
        client.emit("chat_send", {"id": "latency-%d" % time.monotonic_ns(), "text": text})
        deadline = time.monotonic() + timeout
        while first["seen"] is None:
            if time.monotonic() > deadline:
                raise TimeoutError("no first text in %d s" % timeout)
            time.sleep(0.01)
    return ask


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--text", default="Hello")
    args = parser.parse_args()
    print(json.dumps(measure(chat_ask(args.url, args.user, args.password, args.text), runs=args.runs, warmup=args.warmup), indent=2))


if __name__ == "__main__":
    main()
