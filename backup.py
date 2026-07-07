#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from category import category
from database import DEFAULT_DB_PATH, get_connection, init_db
from note import note

class backup:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)
        self.backupId = None
        self.backupDate = None

    def exportNotes(self, user_id, output_file):
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT note_id, title, content, color, is_pinned, created_date, modified_date FROM notes WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            payload = []
            for row in rows:
                category_rows = conn.execute(
                    """
                    SELECT c.name
                    FROM categories c
                    JOIN note_categories nc ON c.category_id = nc.category_id
                    WHERE nc.note_id = ?
                    ORDER BY c.name ASC
                    """,
                    (row["note_id"],),
                ).fetchall()
                payload.append(
                    {
                        "title": row["title"],
                        "content": row["content"],
                        "color": row["color"],
                        "is_pinned": bool(row["is_pinned"]),
                        "created_date": row["created_date"],
                        "modified_date": row["modified_date"],
                        "categories": [c["name"] for c in category_rows],
                    }
                )

        with open(output_file, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, ensure_ascii=True, indent=2)

        return len(payload)

    def importNotes(self, user_id, input_file):
        with open(input_file, "r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)

        note_service = note(self.db_path)
        category_service = category(self.db_path)

        imported = 0
        for item in payload:
            note_id = note_service.create(
                user_id,
                item["title"],
                item["content"],
                color=item.get("color", "violet"),
                is_pinned=item.get("is_pinned", False),
            )
            for category_name in item.get("categories", []):
                category_service.assignCategory(note_id, category_name)
            imported += 1

        return imported
