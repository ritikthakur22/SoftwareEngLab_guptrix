#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory
import tempfile
import os
import json

from database import DEFAULT_DB_PATH, get_connection
from user import user as UserService
from session import session as SessionService
from note import note as NoteService
from category import category as CategoryService
from backup import backup as BackupService

app = Flask(__name__, static_folder="www", static_url_path="")

DB_PATH = os.environ.get("NOTES_DB", DEFAULT_DB_PATH)
DEFAULT_ACCOUNTS = [
    {
        "username": os.environ.get("NOTES_ADMIN_USERNAME", "admin"),
        "email": os.environ.get("NOTES_ADMIN_EMAIL", "admin@example.com"),
        "password": os.environ.get("NOTES_ADMIN_PASSWORD", "admin123"),
    },
    {
        "username": os.environ.get("NOTES_TEST_USERNAME", "test"),
        "email": os.environ.get("NOTES_TEST_EMAIL", "test@example.com"),
        "password": os.environ.get("NOTES_TEST_PASSWORD", "test123"),
    },
]


def json_error(message, code=400):
    return jsonify({"error": message}), code


def ensure_default_accounts():
    svc = UserService(DB_PATH)
    for account in DEFAULT_ACCOUNTS:
        with get_connection(DB_PATH) as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE username = ?",
                (account["username"],),
            ).fetchone()

        if row is None:
            try:
                svc.register(account["username"], account["email"], account["password"])
            except ValueError:
                continue
            continue

        svc.updateProfile(row["user_id"], password=account["password"])


ensure_default_accounts()


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return json_error("username, email and password are required")
    svc = UserService(DB_PATH)
    try:
        user_id = svc.register(username, email, password)
    except ValueError as exc:
        return json_error(str(exc), 409)
    return jsonify({"user_id": user_id, "username": username, "email": email})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return json_error("username and password are required")
    svc = UserService(DB_PATH)
    user = svc.login(username, password)
    if not user:
        return json_error("invalid credentials", 401)
    session_svc = SessionService(DB_PATH)
    token = session_svc.create(user["user_id"])
    return jsonify({"token": token, "user": user})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return json_error("token required")
    svc = SessionService(DB_PATH)
    ok = svc.terminate(token)
    return jsonify({"ok": bool(ok)})


@app.route("/api/notes", methods=["GET", "POST"])
def api_notes():
    if request.method == "GET":
        user_id = request.args.get("user_id")
        q = request.args.get("q", "")
        if not user_id:
            return json_error("user_id required")
        svc = NoteService(DB_PATH)
        results = svc.search(int(user_id), q)
        return jsonify(results)

    data = request.get_json() or {}
    user_id = data.get("user_id")
    title = data.get("title")
    content = data.get("content")
    color = data.get("color", "violet")
    is_pinned = bool(data.get("is_pinned", False))
    if not user_id or not title or content is None:
        return json_error("user_id, title and content required")
    svc = NoteService(DB_PATH)
    note_id = svc.create(int(user_id), title, content, color=color, is_pinned=is_pinned)
    return jsonify({"note_id": note_id})


@app.route("/api/notes/<int:note_id>", methods=["PUT", "DELETE"])
def api_note_detail(note_id):
    if request.method == "PUT":
        data = request.get_json() or {}
        user_id = data.get("user_id")
        title = data.get("title")
        content = data.get("content")
        color = data.get("color")
        is_pinned = data.get("is_pinned")
        if not user_id:
            return json_error("user_id required")
        svc = NoteService(DB_PATH)
        ok = svc.edit(note_id, int(user_id), title=title, content=content, color=color, is_pinned=is_pinned)
        return jsonify({"ok": bool(ok)})

    # DELETE
    user_id = request.args.get("user_id")
    if not user_id:
        return json_error("user_id required")
    svc = NoteService(DB_PATH)
    ok = svc.delete(note_id, int(user_id))
    return jsonify({"ok": bool(ok)})


@app.route("/api/categories", methods=["GET", "POST"])
def api_categories():
    if request.method == "GET":
        note_id = request.args.get("note_id")
        if not note_id:
            return json_error("note_id required")
        svc = CategoryService(DB_PATH)
        return jsonify(svc.listForNote(int(note_id)))

    data = request.get_json() or {}
    note_id = data.get("note_id")
    name = data.get("name")
    if not note_id or not name:
        return json_error("note_id and name required")
    svc = CategoryService(DB_PATH)
    cat_id = svc.assignCategory(int(note_id), name)
    return jsonify({"category_id": cat_id})


@app.route("/api/categories/<int:note_id>", methods=["PUT"])
def api_category_replace(note_id):
    data = request.get_json() or {}
    names = data.get("names", [])
    if not isinstance(names, list):
        return json_error("names must be a list")
    svc = CategoryService(DB_PATH)
    return jsonify({"count": svc.replaceForNote(note_id, [name for name in names if name])})


@app.route("/api/backup/export", methods=["POST"])
def api_backup_export():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return json_error("user_id required")
    svc = BackupService(DB_PATH)
    # export to temp file and return payload
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        svc.exportNotes(int(user_id), path)
        with open(path, "r", encoding="utf-8") as f:
            payload = f.read()
        return app.response_class(payload, mimetype="application/json")
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.route("/api/backup/import", methods=["POST"])
def api_backup_import():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    payload = data.get("payload")
    if not user_id or payload is None:
        return json_error("user_id and payload required")
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload))
        svc = BackupService(DB_PATH)
        imported = svc.importNotes(int(user_id), path)
        return jsonify({"imported": imported})
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
