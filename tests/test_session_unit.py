from database import get_connection
from session import session
from user import user


def test_session_validate_and_terminate(temp_db_path):
    user_service = user(temp_db_path)
    session_service = session(temp_db_path, duration_minutes=30)

    user_id = user_service.register("faye", "faye@example.com", "pw")
    token = session_service.create(user_id)

    assert session_service.validate(token) is True
    assert session_service.terminate(token) is True
    assert session_service.validate(token) is False


def test_session_invalid_after_expiry(temp_db_path):
    user_service = user(temp_db_path)
    session_service = session(temp_db_path, duration_minutes=1)

    user_id = user_service.register("gary", "gary@example.com", "pw")
    token = session_service.create(user_id)

    with get_connection(temp_db_path) as conn:
        conn.execute(
            "UPDATE sessions SET expiry_time = '2000-01-01T00:00:00+00:00' WHERE session_id = ?",
            (token,),
        )

    assert session_service.validate(token) is False
