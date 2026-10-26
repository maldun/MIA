# Shared helpers of the test stages (sourced by the stage files; not a stage itself).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="${MIA_TESTING_DIR:-${XDG_RUNTIME_DIR:-/tmp}/mia-testing}"
mkdir -p "$STATE"

# A python that can run the MIA web app: $MIA_PYTHON, the active virtualenv, then python3.12 and python3.
find_python() {
    local candidate
    for candidate in "${MIA_PYTHON:-}" "${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python}" python3.12 python3; do
        [ -n "$candidate" ] || continue
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import flask, flask_socketio" >/dev/null 2>&1; then
            command -v "$candidate"; return 0
        fi
    done
    return 1
}

# Containers: every node that can be tried runs as a container of the MIA image with the CURRENT code mounted over it (writable layer, nothing reaches
# the folder), so the stage always tests this checkout and needs no virtualenv. The user is root of the rootless container (= you on the host).
IMAGE="${MIA_IMAGE:-localhost/mia:latest}"
have_image() { command -v podman >/dev/null 2>&1 && podman image exists "$IMAGE" 2>/dev/null; }
container_running() { [ "$(podman inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" = "true" ]; }
start_container() {              # name host-port container-port command... (extra environment: MIA_CONTAINER_ENV="A=1 B=2")
    local name="$1" hport="$2" cport="$3"; shift 3
    if container_running "$name"; then echo "$name is running already"; return 0; fi
    podman rm -f "$name" >/dev/null 2>&1
    local env=() e; for e in ${MIA_CONTAINER_ENV:-}; do env+=(-e "$e"); done
    podman run -d --name "$name" --user 0:0 -p "127.0.0.1:$hport:$cport" "${env[@]}" -v "$ROOT:/opt/mia/MIA:O" "$IMAGE" "$@" >/dev/null || return 1
    local waited=0
    until curl -s -o /dev/null "http://127.0.0.1:$hport/" || [ $waited -ge 30 ]; do sleep 1; waited=$((waited + 1)); done
    if curl -s -o /dev/null "http://127.0.0.1:$hport/"; then echo "$name started (port $hport, logs: podman logs $name)"
    else echo "$name did not answer in 30 s; last lines:"; podman logs "$name" 2>&1 | tail -5; return 1; fi
}
stop_container() { podman rm -f "$1" >/dev/null 2>&1 && echo "$1 stopped" || echo "$1 is not running"; }

# Background processes of a stage (the fallback without containers): <state>/<name>.pid and <name>.log
start_background() {            # name command...
    local name="$1"; shift
    if is_running "$name"; then echo "$name is running already (pid $(cat "$STATE/$name.pid"))"; return 0; fi
    (cd "$ROOT" && nohup "$@" >"$STATE/$name.log" 2>&1 & echo $! >"$STATE/$name.pid")
    sleep 2
    if is_running "$name"; then echo "$name started (pid $(cat "$STATE/$name.pid"), log $STATE/$name.log)"
    else echo "$name did not start; last lines of $STATE/$name.log:"; tail -5 "$STATE/$name.log"; return 1; fi
}
is_running() { [ -f "$STATE/$1.pid" ] && kill -0 "$(cat "$STATE/$1.pid")" 2>/dev/null; }
stop_background() {
    if is_running "$1"; then kill "$(cat "$STATE/$1.pid")" && echo "$1 stopped"; else echo "$1 is not running"; fi
    rm -f "$STATE/$1.pid"
}
