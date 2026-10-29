#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
REST API of the chat (ui/REQUIREMENTS_CHAT.md 6.3), next to the socket.io events of chat_service.py:

  GET  /api/chat/history?before=<id>&limit=50   visible messages, newest last, {"messages", "older"}
  GET  /api/chat/status                         the same payload as the chat_status event (with the mood)
  GET  /api/chat/commands                       the slash commands (page and server use the same list)
  POST /api/chat/clear   {"scope": "log"}       deletes the chat log; needs the token (X-MIA-Token) when one is set
"""
import hmac
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request

try:
    from .constants import TOKEN_HEADER
except ImportError:  # used as plain script / in tests
    from constants import TOKEN_HEADER


def create_blueprint(service, token=None, allowed_origins=None):
    bp = Blueprint("chat_api", __name__)

    def error(message, status):
        response = jsonify({"error": message})
        response.status_code = status
        return response

    @bp.get("/api/chat/history")
    def history():
        try:
            limit = int(request.args.get("limit", 50))
        except ValueError:
            return error("limit must be a number", 400)
        messages, older = service.log.history(before=request.args.get("before") or None, limit=limit)
        response = jsonify({"messages": messages, "older": older})
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.get("/api/chat/status")
    def status():
        response = jsonify(service.status())
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.get("/api/chat/commands")
    def commands():
        return jsonify({"commands": service.commands()})      # the fixed ones and one for each task of the registry (REQ-WFM-029)

    @bp.post("/api/chat/clear")
    def clear():
        if token and not hmac.compare_digest(request.headers.get(TOKEN_HEADER, ""), token):
            return error("a valid token is needed to delete the conversation", 401)
        origin = request.headers.get("Origin")
        if origin and urlparse(origin).netloc != request.host and (allowed_origins is None or origin not in allowed_origins()):
            return error("request from an unknown origin", 403)
        if not request.is_json:
            return error("send {\"scope\": \"log\"} as application/json", 415)
        data = request.get_json(silent=True) or {}
        if data.get("scope") != "log":
            return error("scope must be \"log\"", 400)
        service.log.clear()
        return jsonify({"cleared": True})

    return bp
