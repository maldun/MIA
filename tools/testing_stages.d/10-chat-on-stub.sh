#!/usr/bin/env bash
# Stage: the chat page on a fake model with a seeded history. The UI to click around, no Ollama needed.
# Node status: the Web Frontend (N-1) on the mocks of the Backend. Replaced by the real Backend when N-2 is integrated (stage 20 then covers it).
# Runs as a container of the MIA image with this checkout mounted; without podman or the image it falls back to a python with flask (MIA_PYTHON).
. "$(dirname "$0")/_common.sh"
NAME=mia-test-chat-on-stub
URL="http://127.0.0.1:8685/?character=0"
case "${1:-}" in
    describe) echo "chat page on a fake model, 130 seeded messages; try: say 'slow' for a slow answer, 'error' for an error, stop button, queue, reload  ->  $URL" ;;
    available) have_image || find_python >/dev/null || { echo "neither the image $IMAGE (podman build -f deploy/Containerfile -t mia .) nor a python with flask; set MIA_PYTHON"; exit 1; } ;;
    auto) exit 0 ;;
    start) if have_image; then
               MIA_CONTAINER_ENV="MIA_STUB_HOST=0.0.0.0" start_container "$NAME" 8685 8685 python MIA/ui/tools/chat_stub_server.py
           else
               py=$(find_python) || { echo "no python with flask; set MIA_PYTHON"; exit 1; }
               start_background chat-on-stub "$py" ui/tools/chat_stub_server.py
           fi && echo "open $URL (without ?character=0 the character loads if its web export is built)" ;;
    stop) stop_container "$NAME"; is_running chat-on-stub && stop_background chat-on-stub ;;
    status) if container_running "$NAME" || is_running chat-on-stub; then echo "running: $URL"; else echo "stopped"; fi ;;
    *) echo "usage: $0 describe|available|auto|start|stop|status"; exit 2 ;;
esac
