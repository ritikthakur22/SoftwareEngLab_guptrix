#!/usr/bin/python
# -*- coding: utf-8 -*-

from database import DEFAULT_DB_PATH, get_connection, init_db

class category:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)
        self.categoryId = None
        self.name = None

    def create(self, name):
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT category_id FROM categories WHERE name = ?",
                (name,),
            ).fetchone()
            if row is not None:
                self.categoryId = row["category_id"]
                self.name = name
                return self.categoryId

            cursor = conn.execute(
                "INSERT INTO categories (name) VALUES (?)",
                (name,),
            )
            self.categoryId = cursor.lastrowid
            self.name = name
            return self.categoryId

    def assignCategory(self, note_id, category_name):
        category_id = self.create(category_name)
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO note_categories (note_id, category_id) VALUES (?, ?)",
                (note_id, category_id),
            )
        return category_id

    def listForNote(self, note_id):
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.name
                FROM categories c
                JOIN note_categories nc ON c.category_id = nc.category_id
                WHERE nc.note_id = ?
                ORDER BY c.name ASC
                """,
                (note_id,),
            ).fetchall()
        return [row["name"] for row in rows]

    def replaceForNote(self, note_id, category_names):
        with get_connection(self.db_path) as conn:
            conn.execute("DELETE FROM note_categories WHERE note_id = ?", (note_id,))

        for category_name in category_names:
            self.assignCategory(note_id, category_name)

        return len(category_names)
