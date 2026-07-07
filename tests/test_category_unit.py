from category import category
from note import note
from user import user


def test_assign_and_list_categories_for_note(temp_db_path):
    user_service = user(temp_db_path)
    note_service = note(temp_db_path)
    category_service = category(temp_db_path)

    user_id = user_service.register("ivy", "ivy@example.com", "pw")
    note_id = note_service.create(user_id, "Task", "Do laundry")

    category_service.assignCategory(note_id, "home")
    category_service.assignCategory(note_id, "urgent")
    # Duplicate assignment should not create duplicate rows.
    category_service.assignCategory(note_id, "urgent")

    categories = category_service.listForNote(note_id)
    assert categories == ["home", "urgent"]


def test_create_reuses_existing_category_name(temp_db_path):
    category_service = category(temp_db_path)

    first_id = category_service.create("study")
    second_id = category_service.create("study")

    assert first_id == second_id