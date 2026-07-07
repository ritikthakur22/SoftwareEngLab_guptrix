import json
import os
import tempfile

from backup import backup
from category import category
from note import note
from session import session
from user import user


def test_system_end_to_end_multi_user_isolation(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)
    category_service = category(temp_db_path)
    session_service = session(temp_db_path)
    backup_service = backup(temp_db_path)

    alice_id = user_service.register("alice_sys", "alice_sys@example.com", "pw-a")
    bob_id = user_service.register("bob_sys", "bob_sys@example.com", "pw-b")

    alice_session = session_service.create(alice_id)
    bob_session = session_service.create(bob_id)
    assert session_service.validate(alice_session) is True
    assert session_service.validate(bob_session) is True

    alice_note_id = note_service.create(alice_id, "Plan", "Deploy tomorrow")
    bob_note_id = note_service.create(bob_id, "Private", "Bob secret")

    category_service.assignCategory(alice_note_id, "work")
    category_service.assignCategory(bob_note_id, "personal")

    alice_found = note_service.search(alice_id, "Plan")
    bob_found = note_service.search(bob_id, "Private")
    assert len(alice_found) == 1
    assert len(bob_found) == 1

    # Users cannot delete each other's notes.
    assert note_service.delete(alice_note_id, bob_id) is False
    assert note_service.delete(bob_note_id, alice_id) is False

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    handle.close()
    try:
        exported = backup_service.exportNotes(alice_id, handle.name)
        assert exported == 1

        with open(handle.name, "r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
        assert payload[0]["title"] == "Plan"
        assert payload[0]["categories"] == ["work"]

        # Import for alice should duplicate only alice data, never bob data.
        imported = backup_service.importNotes(alice_id, handle.name)
        assert imported == 1
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)

    assert len(note_service.search(alice_id, "Plan")) == 2
    assert len(note_service.search(bob_id, "Private")) == 1

    assert session_service.terminate(alice_session) is True
    assert session_service.validate(alice_session) is False
    assert session_service.validate(bob_session) is True
