#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os


DEFAULT_DB_PATH = "data/notes_app.db"


def get_connection(db_path=DEFAULT_DB_PATH):
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DEFAULT_DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                login_time TEXT NOT NULL,
                expiry_time TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT 'violet',
                is_pinned INTEGER NOT NULL DEFAULT 0,
                created_date TEXT NOT NULL,
                modified_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        note_columns = {row["name"] for row in conn.execute("PRAGMA table_info(notes)").fetchall()}
        if "color" not in note_columns:
            conn.execute("ALTER TABLE notes ADD COLUMN color TEXT NOT NULL DEFAULT 'violet'")
        if "is_pinned" not in note_columns:
            conn.execute("ALTER TABLE notes ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS note_categories (
                note_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (note_id, category_id),
                FOREIGN KEY (note_id) REFERENCES notes(note_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
            )
            """
        )
