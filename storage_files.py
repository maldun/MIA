"""
The file backend of the Storage layer (stage 0 of deploy/REQUIREMENTS_DB.md: the default, no database, no new dependency).

One JSON file per record, <root>/<table>/<quoted id>.json, holding the list of its versions. The id is quoted so that an id with a slash or a dot
cannot leave its folder. A file is replaced atomically and durably (REQ-SLY-023): written to a temporary file that is flushed to disk, renamed,
then the folder is flushed, so after a power cut a record file is either the old one or the complete new one.

Beyond IF-102, for the sync of G-V4.GRAPHSTORE.TRANSFER only: cut (a record cut back to a version, REQ-SLY-038) and put_file (a plain file below
the root, e.g. the aside file of REQ-SLY-026).

A set of files carries its format in <root>/mia-store.json, {"format": 1} (REQ-SLY-032): every write into a set without one writes it first,
durably. A set whose marker names a later format is not opened, so an older MIA never writes into a set it cannot read completely (REQ-SLY-035).
A set without a marker is read as format 1 (REQ-SLY-033); graph_store_transfer refuses such a set when it holds old unscoped IDs (REQ-SLY-034).
"""
import json
import os
import tempfile
from urllib.parse import quote, unquote

try:
    from .storage import StorageError
except ImportError:  # used as plain script / in tests
    from storage import StorageError

FORMAT = 1                     # the format of a set of files this code writes and reads (REQ-SLY-032)
MARKER = "mia-store.json"      # the format marker in the root of a set of files


class FileBackend:
    def __init__(self, root):
        self.root = root
        found = self.format()
        if found is not None and found > FORMAT:
            raise StorageError("format", detail={"found": found, "known": FORMAT})

    def format(self):
        """The format the set's marker names, None for a set without one."""
        try:
            with open(os.path.join(self.root, MARKER), encoding="utf-8") as handle:
                return json.load(handle).get("format")
        except FileNotFoundError:
            return None

    def _mark(self):
        """Writes the marker into a set that has none, before the first write of a record or file (REQ-SLY-032)."""
        if not os.path.exists(os.path.join(self.root, MARKER)):
            self._replace(os.path.join(self.root, MARKER), json.dumps({"format": FORMAT}))

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
        self._mark()
        self._replace(self._path(table, record_id), json.dumps(self.versions(table, record_id) + [entry], ensure_ascii=False))

    def cut(self, table, record_id, version):
        """Keeps the versions 1 to `version`; a record without versions above it is not written, one cut to 0 is gone."""
        entries = self.versions(table, record_id)
        if len(entries) <= version:
            return
        self._mark()
        if version == 0:
            self.remove(table, record_id)
            return
        self._replace(self._path(table, record_id), json.dumps(entries[:version], ensure_ascii=False))

    def put_file(self, path, text):
        """Writes text durably to `path`, relative to the root."""
        self._mark()
        self._replace(os.path.join(self.root, path), text)

    @staticmethod
    def _replace(path, text):
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        folder_fd = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(folder_fd)
        finally:
            os.close(folder_fd)

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

    def close(self):
        """Nothing to release; every backend can be closed, so the callers need not know which one they have."""
