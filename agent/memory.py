"""Simple persistent memory backed by SQLite."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Optional


class Memory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                role TEXT,
                content TEXT
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS store (
                key TEXT PRIMARY KEY,
                value TEXT,
                ts REAL
            )"""
        )
        self.conn.commit()

    def add_message(self, role: str, content: str):
        self.conn.execute(
            "INSERT INTO history (ts, role, content) VALUES (?,?,?)",
            (time.time(), role, content),
        )
        self.conn.commit()

    def recent(self, limit: int = 20) -> list[dict]:
        cur = self.conn.execute(
            "SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear_history(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()

    def put(self, key: str, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO store (key, value, ts) VALUES (?,?,?)",
            (key, json.dumps(value), time.time()),
        )
        self.conn.commit()

    def get(self, key: str, default=None):
        cur = self.conn.execute("SELECT value FROM store WHERE key=?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else default

    def keys(self) -> list[str]:
        cur = self.conn.execute("SELECT key FROM store ORDER BY ts DESC")
        return [r[0] for r in cur.fetchall()]
