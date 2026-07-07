#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import hmac
import os

from database import DEFAULT_DB_PATH, get_connection, init_db

class user:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)
        self.userId = None
        self.username = None
        self.email = None
        self.password = None

    @staticmethod
    def _hash_password(password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return f"{salt.hex()}${hashed.hex()}"

    @staticmethod
    def _verify_password(password, stored_hash):
        salt_hex, expected_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return hmac.compare_digest(candidate.hex(), expected_hex)

    def register(self, username, email, password):
        password_hash = self._hash_password(password)
        try:
            with get_connection(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash),
                )
                self.userId = cursor.lastrowid
                self.username = username
                self.email = email
                self.password = password_hash
                return self.userId
        except Exception as exc:
            raise ValueError("Username or email already exists") from exc

    def login(self, username, password):
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT user_id, username, email, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if row is None:
            return None

        if not self._verify_password(password, row["password_hash"]):
            return None

        self.userId = row["user_id"]
        self.username = row["username"]
        self.email = row["email"]
        self.password = row["password_hash"]
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "email": row["email"],
        }

    def updateProfile(self, user_id, username=None, email=None, password=None):
        updates = []
        params = []

        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if password is not None:
            updates.append("password_hash = ?")
            params.append(self._hash_password(password))

        if not updates:
            return False

        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"

        with get_connection(self.db_path) as conn:
            cursor = conn.execute(sql, tuple(params))
            return cursor.rowcount > 0
