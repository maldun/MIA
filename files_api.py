"""The routes of the files volume (IF-101 v8, REQ-WFM-037): `files` lists the files, `file` sends one as an attachment. There is no route to delete: the user deletes in the volume.
The guard of accounts_api has already checked the session; every user sees all files (CON-6)."""
from flask import Blueprint, jsonify, send_file

try:
    from .file_store import FileStoreError
except ImportError:
    from file_store import FileStoreError

STATUS = {"invalid_file_name": 422, "not_found": 404}
TYPES = {".md": "text/markdown", ".tex": "application/x-tex", ".txt": "text/plain", ".json": "application/json", ".csv": "text/csv", ".pdf": "application/pdf"}


def create_files_blueprint(store):
    bp = Blueprint("files_api", __name__)

    @bp.get("/api/files")
    def files():
        return jsonify(store.list())

    @bp.get("/api/files/<name>")
    def file(name):
        try:
            path = store.path(name)
        except FileStoreError as err:
            return jsonify({"error": err.code}), STATUS.get(err.code, 400)
        extension = name[name.rfind("."):].lower()
        return send_file(path, mimetype=TYPES.get(extension, "application/octet-stream"), as_attachment=True, download_name=name)

    return bp
