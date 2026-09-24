"""
SQL Memory Repository for MonArch AI (SQLite / PostgreSQL compatible).
Manages chat sessions, episodic messages, semantic long-term user memories, and summaries.
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from utils.logger import log

DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "monarch_memory.db"))


class MemoryRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            log.info("Initialized MonArch SQLite Memory Database at %s", self.db_path)

    # Memories (Semantic)
    def add_memory(self, fact: str, user_id: Optional[str] = "default_user", category: str = "sre_policy") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_memories (user_id, fact, category) VALUES (?, ?, ?)",
                (user_id, fact, category)
            )
            conn.commit()
            return cursor.lastrowid

    def get_memories(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM user_memories WHERE user_id = ? ORDER BY id DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM user_memories ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_memory(self, memory_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0


memory_repo = MemoryRepository()
