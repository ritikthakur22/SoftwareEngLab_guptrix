from note import note
from user import user


def test_create_edit_delete_note(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)

    user_id = user_service.register("dina", "dina@example.com", "pw")
    note_id = note_service.create(user_id, "First", "initial content")

    assert note_id > 0

    edited = note_service.edit(note_id, user_id, title="First Updated", content="changed")
    assert edited is True

    results = note_service.search(user_id, "Updated")
    assert len(results) == 1
    assert results[0]["title"] == "First Updated"

    deleted = note_service.delete(note_id, user_id)
    assert deleted is True
    assert note_service.search(user_id, "Updated") == []


def test_search_matches_title_and_content(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)

    user_id = user_service.register("eric", "eric@example.com", "pw")
    note_service.create(user_id, "Shopping", "Buy apples")
    note_service.create(user_id, "Work", "Prepare shopping report")

    results = note_service.search(user_id, "shop")

    assert len(results) == 2
