from user import user


def test_register_and_login_success(temp_db_path):
    service = user(temp_db_path)

    user_id = service.register("alice", "alice@example.com", "secret123")
    result = service.login("alice", "secret123")

    assert user_id > 0
    assert result is not None
    assert result["username"] == "alice"


def test_login_fails_with_bad_password(temp_db_path):
    service = user(temp_db_path)
    service.register("bob", "bob@example.com", "good-pass")

    result = service.login("bob", "wrong-pass")

    assert result is None


def test_update_profile_changes_username_and_password(temp_db_path):
    service = user(temp_db_path)
    user_id = service.register("carol", "carol@example.com", "init-pass")

    updated = service.updateProfile(user_id, username="carol2", password="new-pass")

    assert updated is True
    assert service.login("carol", "init-pass") is None
    assert service.login("carol2", "new-pass") is not None
