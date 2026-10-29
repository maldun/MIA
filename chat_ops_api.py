"""The routes of the operations on answers and votes (IF-101 v1, provided by the chat agent over IF-201): vote, score, regenerate, speak_again, account, counters, reset_counter (REQ-CHA-018).
The guard of accounts_api has put the account into g.account; without accounts the author is "page". The change log records the POSTs there."""
from flask import Blueprint, g, jsonify, request

try:
    from .chat_service import ChatError
except ImportError:
    from chat_service import ChatError

STATUS = {"not_found": 404, "not_the_last_answer": 422, "invalid_vote": 422, "queue_full": 503}


def create_chat_ops_blueprint(chat):
    bp = Blueprint("chat_ops_api", __name__)

    def answer(call):
        try:
            return jsonify(call())
        except ChatError as err:
            body = {"error": err.code}
            if err.rule:
                body["rule"] = err.rule
            return jsonify(body), STATUS.get(err.code, 400)

    def data():
        body = request.get_json(silent=True)
        return body if isinstance(body, dict) else {}

    def account():
        return getattr(g, "account", None) or "page"

    @bp.post("/api/vote")
    def vote():
        body = data()
        return answer(lambda: chat.vote(account(), body.get("subject"), body.get("category"), body.get("value")))

    @bp.get("/api/score")
    def score():
        return answer(chat.score)

    @bp.post("/api/regenerate")
    def regenerate():
        return answer(lambda: chat.regenerate(account(), data().get("message_id")))

    @bp.post("/api/speak_again")
    def speak_again():
        return answer(lambda: chat.speak_again(data().get("message_id")))

    @bp.get("/api/account")
    def account_of():
        return answer(lambda: chat.account(request.args.get("message_id")))

    @bp.post("/api/pause")
    def pause():
        return jsonify({"paused": chat.pause()})          # False when nothing runs (IF-101 v8)

    @bp.post("/api/resume")
    def resume():
        chat.resume()
        return jsonify({"paused": False})

    @bp.get("/api/counters")
    def counters():
        return answer(chat.counters)

    @bp.post("/api/reset_counter")
    def reset_counter():
        return answer(lambda: chat.reset_counter(account(), data().get("name")))

    return bp
