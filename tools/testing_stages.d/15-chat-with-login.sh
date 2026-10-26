#!/usr/bin/env bash
# Stage: the chat page against the MOCK of the Backend interface IF-101: login with accounts, messages with their sender, queue positions, scripted answers.
# Node status: the Web Frontend (N-1.1 slice: login, sender, queue position) on the IF-101 mock. Several browsers (or private windows) = several users.
# Runs as a container of the MIA image with this checkout mounted; without podman or the image it falls back to a python with flask (MIA_PYTHON).
. "$(dirname "$0")/_common.sh"
NAME=mia-test-chat-login
URL="http://127.0.0.1:8686/?character=0"
case "${1:-}" in
    describe) echo "chat page with login on the IF-101 v1 mock (accounts anna/pw-anna, ben/pw-ben, carl/pw-carl): senders, queue places, 👍👎 🔊 ↻ ⓘ under an answer, menu: Workspace (tasks, memos, memory, sources, persona, score) and Account  ->  $URL" ;;
    available) have_image || find_python >/dev/null || { echo "neither the image $IMAGE (podman build -f deploy/Containerfile -t mia .) nor a python with flask; set MIA_PYTHON"; exit 1; } ;;
    auto) exit 0 ;;
    start) if have_image; then
               MIA_CONTAINER_ENV="MIA_STUB_HOST=0.0.0.0" start_container "$NAME" 8686 8686 python MIA/ui/tools/chat_mock_server.py
           else
               py=$(find_python) || { echo "no python with flask; set MIA_PYTHON"; exit 1; }
               start_background chat-with-login "$py" ui/tools/chat_mock_server.py
           fi && echo "open $URL   (log in as anna / pw-anna; a second browser as ben / pw-ben)" ;;
    stop) stop_container "$NAME"; is_running chat-with-login && stop_background chat-with-login ;;
    status) if container_running "$NAME" || is_running chat-with-login; then echo "running: $URL"; else echo "stopped"; fi ;;
    *) echo "usage: $0 describe|available|auto|start|stop|status"; exit 2 ;;
esac
