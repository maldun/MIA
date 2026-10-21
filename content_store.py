"""
The content store (ui/REQUIREMENTS_CORE.md CG14, LG3, LG7): big texts (pages, abstracts, prompts, model answers) are stored once, by hash, and the events carry the hash and an
excerpt. The run line stays small, the same page is stored once, and a run can be reproduced offline from the stored texts (CG15).

  C1  the key is events.digest(): the hash of the text after the removal of secrets (events.clean_text), so the hash in an event and the key in the store are the same function
      of the same content, and nothing the log must not hold (LG4) is in the store either
  C2  put() is idempotent and atomic (write to a temporary file, then rename); storing a text again renews its age
  C3  a store that cannot write (disk full, folder not writable) never breaks a run: put() still returns the hash and counts the failure
  C4  retention: prune() removes texts older than a number of days (by the time they were last stored) except the ones named in keep; the events and their hashes stay
"""
import json
import os
import tempfile
import threading
import time

try:
    from . import events
except ImportError:  # used as plain script / in tests
    import events


class ContentStore:
    def __init__(self, folder, clock=time.time):
        self.folder = folder
        self._clock = clock
        self._lock = threading.Lock()
        self.failures = 0

    def _path(self, hash_):
        name = str(hash_).split(":", 1)[-1]
        if not name or not all(c in "0123456789abcdef" for c in name):
            raise ValueError("not a hash of this store: %r" % (hash_,))
        return os.path.join(self.folder, name[:2], name[2:] + ".txt")

    def put(self, value):
        """store a text (or any JSON-able value, as canonical JSON) and return its hash"""
        text = events.clean_text(value)
        hash_ = events.digest(text)
        if not self.folder:
            return hash_
        path = self._path(hash_)
        try:
            if os.path.exists(path):
                os.utime(path, (self._clock(), self._clock()))                      # C2: stored again, so it is young again
                return hash_
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                fp.write(text)
            os.replace(tmp, path)
            os.utime(path, (self._clock(), self._clock()))
        except OSError:
            with self._lock:
                self.failures += 1                                                  # C3
        return hash_

    def get(self, hash_):
        """the text, or None if the store does not have it (never stored, or pruned)"""
        if not self.folder:
            return None
        try:
            with open(self._path(hash_), encoding="utf-8") as fp:
                return fp.read()
        except (OSError, ValueError):
            return None

    def get_json(self, hash_):
        text = self.get(hash_)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError:
            return None

    def has(self, hash_):
        try:
            return bool(self.folder) and os.path.exists(self._path(hash_))
        except ValueError:
            return False

    def stats(self):
        files = size = 0
        for root, _, names in os.walk(self.folder or "."):
            if not self.folder:
                break
            for name in names:
                if name.endswith(".txt"):
                    files += 1
                    try:
                        size += os.path.getsize(os.path.join(root, name))
                    except OSError:
                        pass
        return {"files": files, "bytes": size, "failures": self.failures}

    def prune(self, max_age_days, keep=()):
        """C4: remove texts last stored more than max_age_days ago, except the hashes in keep; returns the number removed"""
        if not self.folder or not os.path.isdir(self.folder):
            return 0
        limit = self._clock() - max_age_days * 86400
        protected = set()
        for hash_ in keep:
            try:
                protected.add(self._path(hash_))
            except ValueError:
                pass
        removed = 0
        for root, _, names in os.walk(self.folder):
            for name in names:
                path = os.path.join(root, name)
                if not name.endswith(".txt") or path in protected:
                    continue
                try:
                    if os.path.getmtime(path) < limit:
                        os.remove(path)
                        removed += 1
                except OSError:
                    pass
        return removed
