"""The structured memory of the Chat agent without a model (REQ-CHA-011, -012; design in specs/mia/eval-drafts/memory-design.md, D-78).

A record is {text, kind, source, subject, status, created, updated} in the table `memory` (IF-302 v2). `add` takes the candidates of the writer step (a model step, measured on the dev
cases of the memory sample) and decides what may be stored: only candidates that came from the user's own message, never text of the web, a file or a tool (REQ-CHA-012, a structural
rule that does not depend on the model). `retrieve` picks the most relevant active records within a token budget; it gives nothing when no record shares a word with the question
(abstention). Texts are kept word for word: a record is left out, never cut. Storage only through the Storage layer (IF-102)."""
import math
import os
import re
import time

try:
    from .storage import StorageError
except ImportError:
    from storage import StorageError

KINDS = ("fact", "preference", "commitment")
WORD = re.compile(r"\w+", re.UNICODE)
STOPWORDS = frozenset("a an the and or but of to in on at for with by from is are was were be been am do does did my your our me you i we it its this that these those what which who whom "
                      "how when where why can could will would should please about as if so not no yes".split())
HALF_LIFE_DAYS = 30            # a record loses half of its recency weight in a month
RECENCY_WEIGHT = 0.25          # relevance (0..1) dominates; recency decides between records of equal relevance
KIND_WEIGHT = {"commitment": 0.05}
DEFAULT_BUDGET = 400           # tokens of the memory block in the prompt (num_ctx is 8192)


class MemoryRefused(Exception):
    """the candidates came from a source that may not create memory"""


def tokens(text):
    """a rough count (4 characters a token): enough to keep a block within a budget without a tokenizer of the model"""
    return -(-len(text) // 4)


def _stem(word):
    """dogs -> dog, lives -> live: a trailing s is cut from words of more than three letters, so that a question matches a record without a stemmer library"""
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _words(text):
    return {_stem(w) for w in (m.lower() for m in WORD.findall(text or "")) if w not in STOPWORDS}


def _seconds(stamp):
    return time.mktime(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone


def _stamp(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


class MemoryRecords:
    def __init__(self, storage, clock=time.time, budget_tokens=DEFAULT_BUDGET):
        self._storage, self._clock, self.budget_tokens = storage, clock, budget_tokens

    def add(self, account, message_id, candidates, source_kind):
        """stores the valid candidates {kind, text, replaces?} as records about `account` that came from the message `message_id`; returns their ids.
        Refuses everything unless source_kind is exactly "user". A candidate with an unknown kind or a blank text is dropped; a `replaces` that is not an active record is ignored and the record is stored."""
        if not isinstance(source_kind, str) or source_kind != "user":
            raise MemoryRefused("memory records come from the user's own message, not from %r" % (source_kind,))
        now = _stamp(self._clock())
        ids = []
        for item in candidates if isinstance(candidates, (list, tuple)) else ():
            if not isinstance(item, dict) or item.get("kind") not in KINDS or not isinstance(item.get("text"), str) or not item["text"].strip():
                continue
            old_id = item.get("replaces")
            old = self._active(old_id) if isinstance(old_id, str) and old_id else None
            if old is not None:                        # an unknown, empty or already replaced id replaces nothing: the model invents ids, the statement itself is kept
                self._storage.put("memory", old_id, dict(old, status="replaced", updated=now), account)
            record_id = "%017d-%s" % (int(self._clock() * 1_000_000), os.urandom(2).hex())
            self._storage.put("memory", record_id, {"text": item["text"], "kind": item["kind"], "source": message_id, "subject": account, "status": "active",
                                                    "created": now, "updated": now}, account)
            ids.append(record_id)
        return ids

    def remember(self, account, message_id, text, source_kind, ask):
        """one message of the user into the memory: ask(text, known) is the writer step (a model) and gives the candidates, add() stores the valid ones; returns the new ids.
        The source is checked FIRST: text of the web, a file or a tool is never shown to the writer, so nothing in it can steer it (REQ-CHA-012). A writer that fails or answers
        nonsense stores nothing; a blank message is not asked about. `known` lists the records that match the message as `id: text`, so that a correction can name what it replaces."""
        if not isinstance(source_kind, str) or source_kind != "user":
            raise MemoryRefused("memory records come from the user's own message, not from %r" % (source_kind,))
        if not isinstance(text, str) or not text.strip():
            return []
        try:
            candidates = ask(text, self.known(text))
        except Exception:
            return []
        return self.add(account, message_id, candidates, source_kind)

    def known(self, text):
        """the active records that match the text, one `id: text` line each, within the budget (what the writer may name in `replaces`)"""
        lines, left = [], self.budget_tokens
        for record_id, doc in self._ranked(text):
            line = "%s: %s" % (record_id, doc["text"])
            if tokens(line) + 1 <= left:
                lines.append(line)
                left -= tokens(line) + 1
        return "\n".join(lines)

    def _active(self, record_id):
        try:
            doc = self._storage.get("memory", record_id)["doc"]
        except StorageError:
            return None
        return doc if doc.get("status", "active") == "active" else None

    def line(self, doc):
        return "- %s: %s (%s)" % (doc.get("kind", "fact"), doc["text"], doc.get("source", "?"))

    def _ranked(self, question):
        """(id, record) of the active records that share a word with the question, best first; nothing for a question without words or without a match"""
        wanted = _words(question)
        if not wanted:
            return []
        now, scored = self._clock(), []
        for record_id in self._storage.ids("memory"):
            doc = self._storage.get("memory", record_id)["doc"]
            if doc.get("status", "active") != "active":
                continue
            overlap = len(wanted & _words(doc["text"]))
            if not overlap:
                continue
            age_days = max(0.0, (now - _seconds(doc.get("updated") or doc["created"])) / 86400)
            score = overlap / len(wanted) + RECENCY_WEIGHT * math.pow(0.5, age_days / HALF_LIFE_DAYS) + KIND_WEIGHT.get(doc.get("kind"), 0)
            scored.append((score, doc.get("updated", ""), record_id, doc))
        scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        return [(record_id, doc) for _score, _updated, record_id, doc in scored]

    def retrieve(self, question, budget_tokens=None):
        """the active records that share a word with the question, best first, as many as fit the budget; [] when none shares a word"""
        left, found = self.budget_tokens if budget_tokens is None else budget_tokens, []
        for _record_id, doc in self._ranked(question):
            cost = tokens(self.line(doc)) + 1                      # the line break
            if cost <= left:
                found.append(doc)
                left -= cost
        return found

    def block(self, records):
        """the text for the prompt: one line per record with its kind and source; "" for none"""
        return "\n".join(self.line(doc) for doc in records)
