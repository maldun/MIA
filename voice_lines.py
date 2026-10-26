"""Voice lines of the moods (REQ-CHA-007, FR-31): which sound files MIA may say at a mood or event.

library/voice_lines.json: {"lines": {"annoyed": ["annoyed.wav", "grr.wav"]}, "silent": ["neutral", ...]}. pick(mood) chooses one of the lines at random, gives None for a mood
without a line (it stays silent), and skips a file that is missing (and says so in the log). A mood must have an entry in "lines" (an empty list = silent, owner 2026-10-27; the old list "silent" still counts): uncovered() names those that have
neither, so that a new mood in moods.json cannot be forgotten. The file is read at every call, like the list of behaviours: it may change while MIA runs.
"""
import json
import os
import random


def mood_names(moods_path):
    """the moods of the mood map (moods.json): its emotions and activities"""
    with open(moods_path, encoding="utf-8") as fp:
        data = json.load(fp)
    return sorted(set(data.get("emotions", {})) | set(data.get("activities", {})))


class VoiceLines:
    def __init__(self, path, folder, moods, rng=None, log=None):
        self.path, self.folder, self.moods = path, folder, list(moods)
        self._rng = rng or random.Random()
        self._log = log or (lambda message: None)

    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as fp:
                data = json.load(fp)
            lines = {str(mood).lower(): [f for f in files if isinstance(f, str)] for mood, files in data.get("lines", {}).items() if isinstance(files, list)}
            return lines, {str(mood).lower() for mood in data.get("silent", [])}
        except (OSError, ValueError, AttributeError):
            return {}, set()                      # a missing or broken file is silence, not a crash

    def pick(self, mood):
        """the path of one existing line of the mood, chosen at random, or None (silent)"""
        lines, _ = self._read()
        candidates = []
        for name in lines.get(str(mood).lower(), []):
            path = os.path.join(self.folder, name)
            if os.path.isfile(path):
                candidates.append(path)
            else:
                self._log("voice line %s of the mood %s is missing: skipped" % (path, mood))
        return self._rng.choice(candidates) if candidates else None

    def uncovered(self):
        """the moods of the map that have no line and are not declared silent"""
        lines, silent = self._read()
        return [mood for mood in self.moods if mood.lower() not in lines and mood.lower() not in silent]
