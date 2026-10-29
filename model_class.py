"""
Whether a model is local or paid (REQ-WFM-035), kept per model name in a small json file. A model that is not in the file and does not run on this machine is asked about once
(needs_question); the answer is stored with set() and never asked again. A paid model gets the warning and the slices; the class is changed only by set(), that is by the user's command.
"""
import json
import os

LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
CLASSES = ("local", "paid")


class ModelClasses:
    def __init__(self, path):
        self.path = path

    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return {}

    def class_of(self, name, host=None):
        stored = self._read().get(name)
        if stored in CLASSES:
            return stored
        return "local" if host in LOCAL_HOSTS else None

    def needs_question(self, name, host=None):
        return self._read().get(name) not in CLASSES and host not in LOCAL_HOSTS

    def set(self, name, cls):
        if cls not in CLASSES:
            raise ValueError("the class of a model is local or paid, not %r" % (cls,))
        found = self._read()
        found[name] = cls
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        temp = self.path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(found, handle, indent=1, sort_keys=True)
        os.replace(temp, self.path)
