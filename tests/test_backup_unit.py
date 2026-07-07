import json
import os
import tempfile

from backup import backup
from category import category
from note import note
from user import user


def test_export_notes_writes_expected_payload(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)
    category_service = category(temp_db_path)
    backup_service = backup(temp_db_path)

    user_id = user_service.register("jules", "jules@example.com", "pw")
    note_id = note_service.create(user_id, "Report", "Finish by Friday")
    category_service.assignCategory(note_id, "work")

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    handle.close()
    try:
        exported_count = backup_service.exportNotes(user_id, handle.name)
        assert exported_count == 1

        with open(handle.name, "r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)

        assert len(payload) == 1
        assert payload[0]["title"] == "Report"
        assert payload[0]["categories"] == ["work"]
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)


def test_import_notes_creates_notes_and_categories(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)
    category_service = category(temp_db_path)
    backup_service = backup(temp_db_path)

    user_id = user_service.register("kian", "kian@example.com", "pw")

    payload = [
        {
            "title": "One",
            "content": "alpha",
            "created_date": "2026-01-01T00:00:00+00:00",
            "modified_date": "2026-01-01T00:00:00+00:00",
            "categories": ["personal", "todo"],
        },
        {
            "title": "Two",
            "content": "beta",
            "created_date": "2026-01-01T00:00:00+00:00",
            "modified_date": "2026-01-01T00:00:00+00:00",
            "categories": ["todo"],
        },
    ]

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    handle.close()
    try:
        with open(handle.name, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, ensure_ascii=True, indent=2)

        imported_count = backup_service.importNotes(user_id, handle.name)
        assert imported_count == 2

        found_one = note_service.search(user_id, "One")
        found_two = note_service.search(user_id, "Two")
        assert len(found_one) == 1
        assert len(found_two) == 1

        categories_one = category_service.listForNote(found_one[0]["note_id"])
        assert set(categories_one) == {"personal", "todo"}
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)