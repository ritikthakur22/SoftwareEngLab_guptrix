#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from database import DEFAULT_DB_PATH, get_connection, init_db

class session:
    def __init__(self, db_path=DEFAULT_DB_PATH, duration_minutes=60):
        self.db_path = db_path
        self.duration_minutes = duration_minutes
        init_db(self.db_path)
        self.sessionId = None
        self.loginTime = None
        self.expirytime = None

    def create(self, user_id):
        token = str(uuid4())
        login_time = datetime.now(timezone.utc)
        expiry_time = login_time + timedelta(minutes=self.duration_minutes)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, user_id, login_time, expiry_time, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (token, user_id, login_time.isoformat(), expiry_time.isoformat()),
            )

        self.sessionId = token
        self.loginTime = login_time.isoformat()
        self.expirytime = expiry_time.isoformat()
        return token

    def validate(self, session_id):
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT expiry_time, is_active FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

        if row is None or row["is_active"] == 0:
            return False

        return datetime.fromisoformat(row["expiry_time"]) > datetime.now(timezone.utc)

    def terminate(self, session_id):
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
                (session_id,),
            )
            return cursor.rowcount > 0
