"""
The file backend of the Storage layer (stage 0 of deploy/REQUIREMENTS_DB.md: the default, no database, no new dependency).

One JSON file per record, <root>/<table>/<quoted id>.json, holding the list of its versions. The id is quoted so that an id with a slash or a dot
cannot leave its folder. A file is replaced atomically (written to a temporary file, then renamed), as content_store.py does.
"""
import json
import os
import tempfile
from urllib.parse import quote, unquote


class FileBackend:
    def __init__(self, root):
        self.root = root

    def _folder(self, table):
        return os.path.join(self.root, table)

    def _path(self, table, record_id):
        return os.path.join(self._folder(table), quote(record_id, safe="") + ".json")

    def versions(self, table, record_id):
        try:
            with open(self._path(table, record_id), encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError:
            return []

    def append(self, table, record_id, entry):
        entries = self.versions(table, record_id) + [entry]
        folder = self._folder(table)
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(entries, handle, ensure_ascii=False)
            os.replace(tmp, self._path(table, record_id))
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def ids(self, table):
        try:
            return [unquote(name[:-5]) for name in os.listdir(self._folder(table)) if name.endswith(".json")]
        except FileNotFoundError:
            return []

    def remove(self, table, record_id):
        try:
            os.remove(self._path(table, record_id))
        except FileNotFoundError:
            pass
