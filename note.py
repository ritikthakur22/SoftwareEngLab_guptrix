#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timezone

from database import DEFAULT_DB_PATH, get_connection, init_db

class note:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)
        self.noteId = None
        self.title = None
        self.content = None
        self.createdDate = None
        self.modifiedDate = None

    def create(self, user_id, title, content, color="violet", is_pinned=False):
        now = datetime.now(timezone.utc).isoformat()
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (user_id, title, content, color, is_pinned, created_date, modified_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, content, color, int(bool(is_pinned)), now, now),
            )
            self.noteId = cursor.lastrowid
            self.title = title
            self.content = content
            self.createdDate = now
            self.modifiedDate = now
            return self.noteId

    def edit(self, note_id, user_id, title=None, content=None, color=None, is_pinned=None):
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(int(bool(is_pinned)))
        if not updates:
            return False

        updates.append("modified_date = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.extend([note_id, user_id])

        sql = f"UPDATE notes SET {', '.join(updates)} WHERE note_id = ? AND user_id = ?"
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(sql, tuple(params))
            return cursor.rowcount > 0

    def delete(self, note_id, user_id):
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM notes WHERE note_id = ? AND user_id = ?",
                (note_id, user_id),
            )
            return cursor.rowcount > 0

    def search(self, user_id, query):
        pattern = f"%{query}%"
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT note_id, title, content, color, is_pinned, created_date, modified_date
                FROM notes
                WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY is_pinned DESC, modified_date DESC
                """,
                (user_id, pattern, pattern),
            ).fetchall()

        return [
            {
                "note_id": row["note_id"],
                "title": row["title"],
                "content": row["content"],
                "color": row["color"],
                "is_pinned": bool(row["is_pinned"]),
                "created_date": row["created_date"],
                "modified_date": row["modified_date"],
            }
            for row in rows
        ]
