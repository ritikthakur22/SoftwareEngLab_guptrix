import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backup import backup
from category import category
from note import note
from session import session
from user import user


def test_full_app_flow_integration(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)
    category_service = category(temp_db_path)
    session_service = session(temp_db_path)
    backup_service = backup(temp_db_path)

    user_id = user_service.register("hana", "hana@example.com", "pw123")
    logged_in = user_service.login("hana", "pw123")

    assert logged_in is not None

    token = session_service.create(user_id)
    assert session_service.validate(token) is True

    note_id = note_service.create(user_id, "Integration title", "Integration content")
    category_service.assignCategory(note_id, "work")
    category_service.assignCategory(note_id, "urgent")

    found = note_service.search(user_id, "Integration")
    assert len(found) == 1
    assert set(category_service.listForNote(note_id)) == {"urgent", "work"}

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    handle.close()
    try:
        exported = backup_service.exportNotes(user_id, handle.name)
        assert exported == 1

        with open(handle.name, "r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
        assert payload[0]["title"] == "Integration title"

        imported = backup_service.importNotes(user_id, handle.name)
        assert imported == 1

        all_found = note_service.search(user_id, "Integration")
        assert len(all_found) == 2
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)

    assert session_service.terminate(token) is True
    assert session_service.validate(token) is False
