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
Expressions from a text description (ui/REQUIREMENTS.md 4.6). The user writes "surprised but trying to hide it", the local LLM
answers with shape key weights, the server checks the answer like any preset and the character shows it.

  generate(description)   prompt (shape keys, bones, gestures, examples) -> LLM with a JSON schema -> validated preset (not saved)
  match(description)      the closest existing preset by name, tags and description (no LLM, instant: shown while the LLM works)
  feedback(id, decision)  keep / edit / reject, appended to data/feedback_log.jsonl; the next prompts use it as examples

The LLM is given as a function chat(messages, schema) -> text, so the model, the server and the provider are decided in one place
(web_app.py) and tests can use a fake. Nothing leaves the host unless that function talks to a cloud provider.
"""
import datetime
import json
import os
import re
import threading
import time

try:
    from .mia_logger import logger
    from .preset_store import PresetError, BONE_PARAMS, BONE_LIMIT, MAX_DESCRIPTION
except ImportError:  # used as plain script / in tests
    from mia_logger import logger
    from preset_store import PresetError, BONE_PARAMS, BONE_LIMIT, MAX_DESCRIPTION

MAX_REQUEST = 300
MAX_KEYS = 8            # shape keys in one expression: a face is a few keys, not all of them
DECISIONS = ("keep", "edit", "reject")
PENDING_LIMIT = 100
# when nothing in the library resembles the request, these hand made presets show the style (a mouth, a brow and an eye key, small turns)
DEFAULT_EXAMPLES = ("smug", "embarrassed", "happy", "sad", "surprised", "thinking")
STOP_WORDS = {"a", "an", "the", "and", "or", "but", "with", "of", "to", "in", "on", "very", "slightly", "a", "bit", "little", "trying",
              "is", "are", "looks", "look", "like", "her", "his", "she", "he", "it"}
BONE_HELP = {
    "head_pitch": "nod: positive looks down, negative looks up",
    "head_yaw": "turn: positive turns to the character's left",
    "head_roll": "tilt: positive tilts the head to the character's right",
    "eye_pitch": "eyes: positive looks down",
    "eye_yaw": "eyes: positive looks to the character's left",
}


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", str(text).lower()) if w not in STOP_WORDS and len(w) > 1]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ExpressionGenerator:
    def __init__(self, store, chat, shape_keys_file, gestures_file=None, log_path=None, examples=4, model_name=lambda: None, gestures_provider=None):
        """
        store: the PresetStore (validation, examples, closest preset)
        chat: function (messages, schema) -> the model's answer as text; raises if the model cannot be reached
        shape_keys_file / gestures_file: what the character can do (shown to the model)
        log_path: feedback log (JSON lines)
        """
        self.store = store
        self._chat = chat
        self.log_path = log_path
        self.examples = examples
        self._model_name = model_name
        self._busy = threading.Lock()
        self._lock = threading.RLock()
        self._pending = {}
        with open(shape_keys_file, encoding="utf-8") as fp:
            data = json.load(fp)
        self.categories = data.get("categories", [])
        self.shape_keys = data["shape_keys"]
        self._gestures = []
        self._gestures_provider = gestures_provider      # function() -> [{"name", "description"}]: the built in gestures and the ones of the editor
        if gestures_file and os.path.exists(gestures_file):
            with open(gestures_file, encoding="utf-8") as fp:
                self._gestures = json.load(fp).get("gestures", [])

    @property
    def gestures(self):
        return list(self._gestures_provider()) if self._gestures_provider is not None else self._gestures

    # --- the schema the model must answer with -----------------------------------------------------------------
    def schema(self):
        """
        The weights are a short list of {key, value}: the key can only be one of the shape keys (an enum), the value a number from 0 to 1, and
        at most MAX_KEYS entries. (A schema with one property per shape key makes models walk through all of them and write zeros.)
        """
        entry = {"type": "object", "properties": {"key": {"type": "string", "enum": [k["name"] for k in self.shape_keys]},
                                                  "value": {"type": "number", "minimum": 0, "maximum": 1}},
                 "required": ["key", "value"]}
        bone = {"type": "number", "minimum": -BONE_LIMIT, "maximum": BONE_LIMIT}
        return {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "one short sentence describing the expression"},
                "weights": {"type": "array", "items": entry, "minItems": 1, "maxItems": MAX_KEYS},
                "bones": {"type": "object", "properties": {b: bone for b in BONE_PARAMS}},
                "tags": {"type": "array", "items": {"type": "string"}},
                "gesture": {"type": "string", "enum": [""] + [g["name"] for g in self.gestures]},
            },
            "required": ["description", "weights"],
        }

    # --- the prompt -------------------------------------------------------------------------------------------------
    def _keys_text(self):
        lines = []
        for category in self.categories:
            lines.append(f"{category}:")
            for key in self.shape_keys:
                if key["category"] == category:
                    lines.append(f"  {key['name']}: {key.get('description', '')}")
        return "\n".join(lines)

    def _example_text(self, preset, note=""):
        # the same format as the answer the schema asks for: a list of {key, value}
        weights = [{"key": k, "value": v} for k, v in sorted(preset.get("weights", {}).items(), key=lambda kv: -kv[1]) if v]
        data = {"description": preset.get("description", ""), "weights": weights, "bones": preset.get("bones", {}),
                "tags": preset.get("tags", [])}
        return f"{note}Request: {preset.get('_request', preset.get('name', ''))}\nAnswer: {json.dumps(data, ensure_ascii=False)}"

    def _read_log(self, limit=300):
        if not self.log_path or not os.path.exists(self.log_path):
            return []
        entries = []
        with open(self.log_path, encoding="utf-8") as fp:
            for line in fp.readlines()[-limit:]:
                try:
                    entries.append(json.loads(line))
                except ValueError:
                    continue
        return entries

    def examples_for(self, description):
        """examples for the prompt: what the user kept or edited (good), what was rejected (bad), then similar presets"""
        good, bad = [], []
        for entry in reversed(self._read_log()):
            preset = entry.get("preset")
            if not preset or entry.get("event") not in DECISIONS:
                continue
            item = dict(preset, _request=entry.get("description", ""))
            if entry["event"] == "reject":
                bad.append(item)
            else:
                good.append(item)
        chosen = good[: self.examples]
        taken = {p.get("name") for p in chosen}
        ranked = self._ranked(description)
        by_name = {preset["name"]: preset for _, preset in ranked}
        similar = [preset for score, preset in ranked if score > 0]
        typical = [by_name[name] for name in DEFAULT_EXAMPLES if name in by_name]
        for preset in similar + typical:
            if len(chosen) >= self.examples:
                break
            if preset["name"] not in taken and preset.get("weights"):
                chosen.append(dict(preset, _request=preset.get("description") or preset["name"]))
                taken.add(preset["name"])
        return chosen, bad[:2]

    def messages(self, description, problem=None):
        good, bad = self.examples_for(description)
        system = (
            "You control the face of an anime style 3D character. You answer with the facial expression for a description as JSON.\n\n"
            "Rules:\n"
            "- \"weights\": a list of {\"key\": shape key name, \"value\": 0.0 to 1.0}, at most 8 entries, only keys from the list below. "
            "Everything you do not name is 0, so never list a key with value 0.\n"
            "- Build the face like the examples: one or two MOUTH keys (Fcl_MTH_*), one BROW key (Fcl_BRW_*) and one or two EYE keys (Fcl_EYE_*), "
            "with strengths between 0.2 and 0.9, plus small head or eye turns. Subtle is better than extreme.\n"
            "- The keys Fcl_HA_* are teeth and fangs: use them only when the description asks for teeth, fangs or a toothy grin, never for moods like shy, "
            "sad or sleepy. The keys Fcl_ALL_* change the whole face at once: avoid them, the specific eye, brow and mouth keys are better.\n"
            "- Keys with _L and _R belong to the character's left and right side (use them for asymmetric looks, winks, a smirk).\n"
            "- Do not use the vowel keys (Fcl_MTH_A, I, U, E, O) unless the mouth should be open as in speaking; use the mouth shapes (smile, sad, angry, ...) for the mood.\n"
            "- \"bones\": optional small head and eye turns in degrees (-45 to 45): "
            + "; ".join(f"{k} ({v})" for k, v in BONE_HELP.items()) + ".\n"
            "- \"tags\": 2 to 5 lowercase words for the mood. \"description\": one short sentence.\n"
            + ("- \"gesture\": optional, one of: " + ", ".join(g["name"] for g in self.gestures) + ". Leave it empty unless the description asks for a body movement.\n" if self.gestures else "")
            + "\nShape keys:\n" + self._keys_text()
        )
        if good:
            system += "\n\nExamples the user liked:\n" + "\n\n".join(self._example_text(p) for p in good)
        if bad:
            system += "\n\nAnswers the user rejected (do not repeat them):\n" + "\n\n".join(self._example_text(p) for p in bad)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": f"Request: {description}"}]
        if problem:
            messages.append({"role": "user", "content": f"Your last answer could not be used: {problem}. Answer again with valid JSON."})
        return messages

    # --- the closest existing preset ------------------------------------------------------------------------------------
    def _ranked(self, description):
        wanted = set(words(description))
        ranked = []
        for preset in self.store.list():
            name_words = set(words(preset["name"].replace("_", " ").replace("-", " ")))
            tag_words = set(w for t in preset.get("tags", []) for w in words(t))
            description_words = set(words(preset.get("description", "")))
            score = 3 * len(wanted & name_words) + 3 * len(wanted & tag_words) + len(wanted & description_words)
            ranked.append((score, preset))
        ranked.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
        return ranked

    def match(self, description):
        """the closest preset (no LLM, instant); "neutral" when nothing fits"""
        description = self._clean_request(description)
        ranked = self._ranked(description)
        if ranked and ranked[0][0] > 0:
            return {"name": ranked[0][1]["name"], "score": ranked[0][0], "preset": ranked[0][1]}
        names = {p["name"]: p for _, p in ranked}
        fallback = names.get("neutral") or names.get("idle") or (ranked[0][1] if ranked else None)
        return {"name": fallback["name"] if fallback else None, "score": 0, "preset": fallback}

    # --- generating -------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _clean_request(description):
        if not isinstance(description, str):
            raise PresetError("the description must be text")
        text = re.sub(r"[\x00-\x1f\x7f]+", " ", description).strip()
        if not text:
            raise PresetError("describe the expression you want")
        if len(text) > MAX_REQUEST:
            raise PresetError(f"the description is too long (at most {MAX_REQUEST} characters)")
        return text

    def _new_name(self, description):
        slug = "-".join(words(description)[:4])[:30].strip("-") or "expression"
        names = set(self.store.names())
        name, number = f"llm-{slug}", 2
        while name in names:
            name = f"llm-{slug}-{number}"
            number += 1
        return name[:40]

    @staticmethod
    def _weights(raw):
        """{key: value} from the answer: a list of {"key", "value"} (what the schema asks for) or an object; zeros are dropped"""
        if isinstance(raw, list):
            weights = {}
            for entry in raw:
                if isinstance(entry, dict) and isinstance(entry.get("key"), str):
                    weights[entry["key"]] = entry.get("value", 0)
        elif isinstance(raw, dict):
            weights = dict(raw)
        else:
            return {}
        return {k: v for k, v in weights.items() if not (isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0)}

    def _attempt(self, description, problem):
        reply = self._chat(self.messages(description, problem), self.schema())
        try:
            data = json.loads(reply)
        except (TypeError, ValueError):
            return None, "the answer was not valid JSON"
        if not isinstance(data, dict):
            return None, "the answer was not a JSON object"
        raw = {"name": self._new_name(description), "description": data.get("description", ""), "weights": self._weights(data.get("weights", {})),
               "bones": data.get("bones", {}), "tags": data.get("tags", []), "gesture": data.get("gesture", ""), "source": "llm"}
        preset, corrections = self.store.normalize(raw)
        if not preset["weights"] and not preset["bones"]:
            return None, "no usable shape key weights (" + ("; ".join(corrections[:3]) or "empty") + ")"
        return (preset, corrections), None

    def generate(self, description):
        """returns {"id", "preset", "corrections", "closest", "seconds", "model"}; the preset is not saved"""
        description = self._clean_request(description)
        if not self._busy.acquire(blocking=False):
            raise PresetError("MIA is already working on an expression, please wait a moment", 429)
        started = time.time()
        try:
            problem = None
            for _attempt in range(2):
                try:
                    result, problem = self._attempt(description, problem)
                except PresetError:
                    raise
                except Exception as exc:
                    logger.warning(f"expression LLM not reachable: {exc}")
                    raise PresetError(f"the language model could not be reached: {exc}", 503)
                if result:
                    break
            else:
                raise PresetError(f"the language model did not give a usable expression: {problem}", 502)
            preset, corrections = result
            request_id = f"{int(started * 1000):x}"
            seconds = round(time.time() - started, 2)
            with self._lock:
                self._pending[request_id] = {"description": description, "preset": preset}
                while len(self._pending) > PENDING_LIMIT:
                    self._pending.pop(next(iter(self._pending)))
            self._log({"event": "generated", "id": request_id, "description": description, "preset": preset, "corrections": corrections,
                       "model": self._model_name(), "seconds": seconds})
            return {"id": request_id, "preset": preset, "corrections": corrections, "closest": self.match(description)["name"],
                    "seconds": seconds, "model": self._model_name()}
        finally:
            self._busy.release()

    # --- what the user decided --------------------------------------------------------------------------------------------------------
    def feedback(self, request_id, decision, preset=None):
        """keep / edit / reject; the preset of an edit is what the user saved (the next prompts learn from it)"""
        if decision not in DECISIONS:
            raise PresetError("decision must be keep, edit or reject")
        with self._lock:
            pending = self._pending.get(request_id)
        if pending is None:
            raise PresetError("unknown request (the server was restarted or the request is too old)", 404)
        result = pending["preset"]
        if decision == "edit" and isinstance(preset, dict):
            try:
                result, _ = self.store.normalize(dict(preset, name=pending["preset"]["name"], source="llm_edited"))
            except PresetError:
                result = pending["preset"]
        self._log({"event": decision, "id": request_id, "description": pending["description"], "preset": result})
        return {"logged": decision}

    def _log(self, entry):
        if not self.log_path:
            return
        entry = dict(entry, time=now())
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with self._lock, open(self.log_path, "a", encoding="utf-8") as fp:
                fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.error(f"feedback log not written: {exc}")
