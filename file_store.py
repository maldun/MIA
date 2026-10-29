"""
The files volume (REQ-WFM-037): a folder that tasks put generated files into (a report as .md and .tex, later more). The folder is a volume of its own (config `files_dir`, by default on the disk
of MIA), the limits for one file and for the whole volume come from the configuration, and nothing here deletes a file: the user deletes in the volume and the list, which is read from the folder,
follows. Who made a file (task, message, account) lies in a small sidecar under `.meta/`. A task that cannot store a file says so; its report stays in the database.
"""
import datetime
import json
import os
import re

ALLOWED = (".md", ".tex", ".txt", ".json", ".csv", ".pdf")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}")
META = ".meta"


class FileStoreError(Exception):
    def __init__(self, code, text=""):
        super().__init__(text or code)
        self.code = code


class FileStore:
    def __init__(self, folder, max_file_bytes=1 << 30, max_total_bytes=50 << 30):
        self.folder, self.max_file, self.max_total = folder, max_file_bytes, max_total_bytes

    def _check_name(self, name):
        if not isinstance(name, str) or not NAME.fullmatch(name) or ".." in name:
            raise FileStoreError("invalid_file_name", "A file name has letters, digits, dot, dash and underscore only, no path.")
        return name

    def _total(self):
        return sum(os.path.getsize(os.path.join(self.folder, n)) for n in self._names())

    def _names(self):
        try:
            return [n for n in os.listdir(self.folder) if not n.startswith(".") and os.path.isfile(os.path.join(self.folder, n))]
        except FileNotFoundError:
            return []

    def put(self, name, data, task=None, message_id=None, account=None):
        name = self._check_name(name)
        stem, extension = os.path.splitext(name)
        if extension.lower() not in ALLOWED:
            raise FileStoreError("type_not_allowed", "Files of the type %s are not stored (allowed: %s)." % (extension or "without extension", ", ".join(ALLOWED)))
        raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        if len(raw) > self.max_file:
            raise FileStoreError("too_large", "The file is %d bytes, the limit for one file is %d." % (len(raw), self.max_file))
        if self._total() + len(raw) > self.max_total:
            raise FileStoreError("volume_full", "The files volume would pass its limit of %d bytes." % self.max_total)
        os.makedirs(os.path.join(self.folder, META), exist_ok=True)
        unique, number = name, 1
        while os.path.exists(os.path.join(self.folder, unique)):
            number += 1
            unique = "%s-%d%s" % (stem, number, extension)
        path = os.path.join(self.folder, unique)
        with open(path + ".part", "wb") as handle:
            handle.write(raw)
        os.replace(path + ".part", path)
        meta = {"task": task, "message_id": message_id, "account": account}
        with open(os.path.join(self.folder, META, unique + ".json"), "w", encoding="utf-8") as handle:
            json.dump(meta, handle)
        return self._info(unique)

    def _info(self, name):
        path = os.path.join(self.folder, name)
        try:
            with open(os.path.join(self.folder, META, name + ".json"), encoding="utf-8") as handle:
                meta = json.load(handle)
        except (OSError, ValueError):
            meta = {}
        stamp = datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"name": name, "size": os.path.getsize(path), "created": stamp, "task": meta.get("task"), "message_id": meta.get("message_id")}

    def list(self):
        found = [(os.path.getmtime(os.path.join(self.folder, n)), n) for n in self._names()]
        return [self._info(n) for _, n in sorted(found, reverse=True)]

    def path(self, name):
        name = self._check_name(name)
        path = os.path.join(self.folder, name)
        if not os.path.isfile(path):
            raise FileStoreError("not_found", "There is no file %s in the volume." % name)
        return path
