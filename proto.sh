#!/bin/bash
# PROTOTYPE helper: runs the shared test venv's python from inside this worktree, so every command is one line
cd "$(dirname "$0")" && exec /home/maldun/prog/Python/venvs/mia312/bin/python "$@"
