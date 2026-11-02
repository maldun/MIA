#!/usr/bin/env bash
# Recovery check of a running stack (deploy-phase 3, "recovery"): kill the mia container in the middle of an answer, restart it, check state and data.
#   bash tools/recovery_check.sh            the stack of project MIA_PROJECT (default mia)
# What it does: (1) a chat message with a unique marker is answered, (2) the data folder is listed, (3) a long answer is requested and the container is
# killed (SIGKILL, like a power loss) as soon as text streams, (4) the container is started again and the page must answer, (5) the marker is still in
# the stored data, no file that had content is gone or empty, every line of a *.jsonl but the last is JSON, the database container still answers,
# (6) a new message is answered. Needs a stack without the login (accounts_enabled false; the chat client does not log in).
# It adds two short exchanges to the real chat history. Safe to repeat. MIA_RECOVERY_WAIT (seconds, default 300) is the wait for text and for the page.
set -u
project="${MIA_PROJECT:-mia}"
wait="${MIA_RECOVERY_WAIT:-300}"
engine="$(command -v podman || command -v docker)"
failed=0
fail() { echo "FAIL: $*"; failed=1; }
ok() { echo "ok:   $*"; }
finish() { [ "$failed" = 0 ] && { echo "Recovery check OK"; exit 0; } || { echo "Recovery check FAILED"; exit 1; }; }

find_container() { $engine ps -aq --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$1" | head -1; }
mia="$(find_container mia)"
[ -n "$mia" ] || { fail "no mia container in project $project (start the stack: deploy/up.sh)"; finish; }
db="$(find_container db)"
mark="recovery-$(date +%s)"
work="$(mktemp -d)"; trap 'rm -rf "$work"; [ -n "${long_pid:-}" ] && kill "$long_pid" 2>/dev/null' EXIT

# the chat client inside the container: ROLE chat waits for the whole answer; long prints STREAMING at the first text and then waits (the kill ends it)
client() {   # role, text
    cat <<PY
# role: $1
import socketio, sys, time, os
got = {"text": "", "done": False, "error": None, "shown": False}
c = socketio.Client()
def delta(d):
    got["text"] = d.get("text", "")
    if "$1" == "long" and not got["shown"] and got["text"].strip():
        got["shown"] = True; print("STREAMING", flush=True)
c.on("chat_delta", delta)
c.on("chat_done", lambda *_: got.update(done=True))
c.on("chat_error", lambda d: got.update(error=d))
c.connect("http://127.0.0.1:8585", transports=["polling"], wait_timeout=20)
c.call("chat_send", {"id": "recovery-$1-$mark", "text": os.environ["TEXT"]}, timeout=20)
end = time.time() + $wait
while not (got["done"] or got["error"]) and time.time() < end:
    time.sleep(0.5)
c.disconnect()
print("done=%s error=%s text=%r" % (got["done"], got["error"], got["text"][:60]), flush=True)
sys.exit(0 if got["done"] and got["text"].strip() and not got["error"] else 1)
PY
}

echo "-- 1. a message with the marker $mark"
if client chat | $engine exec -i -e "TEXT=Reply with the single word OK. Reference: $mark" "$mia" python -; then ok "answered"; else fail "the first message was not answered (login on? model server down?)"; finish; fi

echo "-- 2. the data folder before the kill"
$engine exec -i "$mia" python - <<'PY' || { fail "snapshot"; finish; }
# role: snapshot
import json, os
root = "/opt/mia/MIA/data"
snap = {}
for base, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ("cache", "eval", "eval-external")]
    for f in files:
        p = os.path.join(base, f)
        if os.path.getsize(p) > 0 and f != ".recovery_snapshot.json":
            snap[os.path.relpath(p, root)] = os.path.getsize(p)
json.dump(snap, open(os.path.join(root, ".recovery_snapshot.json"), "w"))
print("snapshot %d files" % len(snap))
PY

echo "-- 3. a long answer, then the kill"
client long | $engine exec -i -e "TEXT=Write about 400 words on volcanoes. Reference: $mark" "$mia" python -u - > "$work/long.out" 2>&1 &
long_pid=$!
streaming=0
for _ in $(seq 1 "$wait"); do
    if grep -q STREAMING "$work/long.out" 2>/dev/null; then streaming=1; break; fi
    sleep 1
done
if [ "$streaming" = 1 ]; then ok "text is streaming"; else fail "no text streamed within ${wait}s: $(tail -c 300 "$work/long.out")"; finish; fi
$engine kill "$mia" >/dev/null && ok "mia killed in the middle of the answer" || { fail "kill"; finish; }
kill "$long_pid" 2>/dev/null; long_pid=""

echo "-- 4. restart"
$engine start "$mia" >/dev/null || { fail "start"; finish; }
up=0
for _ in $(seq 1 "$wait"); do
    if curl -fs -o /dev/null http://127.0.0.1:8585/; then up=1; break; fi
    sleep 1
done
if [ "$up" = 1 ]; then ok "the page answers again"; else fail "the page does not answer within ${wait}s ($engine logs --tail 30 $mia)"; finish; fi

echo "-- 5. state and data"
$engine exec -i -e "MARK=$mark" "$mia" python - <<'PY' | tee "$work/verify.out"
# role: verify
import json, os
root = "/opt/mia/MIA/data"
snap_file = os.path.join(root, ".recovery_snapshot.json")
snap = json.load(open(snap_file))
bad = 0
for rel, size in snap.items():
    p = os.path.join(root, rel)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        print("FAIL: %s was %d bytes and is gone or empty" % (rel, size)); bad = 1
    elif rel.endswith(".jsonl"):
        lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
        for n, line in enumerate(lines, 1):
            try:
                json.loads(line)
            except ValueError:
                if n == len(lines):
                    print("WARN: %s ends in a torn line (the answer that was cut)" % rel)
                else:
                    print("FAIL: %s line %d is not JSON" % (rel, n)); bad = 1
mark = os.environ["MARK"]
found = False
for base, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ("cache", "eval", "eval-external")]
    for f in files:
        p = os.path.join(base, f)
        if f.endswith((".jsonl", ".json", ".txt")) and os.path.getsize(p) < 50_000_000 and mark in open(p, encoding="utf-8", errors="replace").read():
            found = True
if not found:
    print("FAIL: the marker %s is not in the stored data" % mark); bad = 1
if not bad:
    print("ok:   marker stored, %d files with content are intact" % len(snap))
os.remove(snap_file)
PY
grep -q '^FAIL' "$work/verify.out" && failed=1
if [ -n "$db" ]; then
    if $engine exec "$db" pg_isready -U mia -d mia >/dev/null 2>&1; then ok "database answers"; else fail "database does not answer"; fi
fi

echo "-- 6. a new message"
if client chat | $engine exec -i -e "TEXT=Reply with the single word OK. Reference: $mark-after" "$mia" python -; then ok "answered after the restart"; else fail "no answer after the restart"; fi
finish
