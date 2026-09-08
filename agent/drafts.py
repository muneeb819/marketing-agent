"""Draft workspace: generated gigs/posts/proposals saved for your review & posting."""
from __future__ import annotations

import time
from typing import Optional


class Drafts:
    def __init__(self, memory):
        self.memory = memory

    def _all(self) -> list:
        return self.memory.get("drafts", []) or []

    def _save(self, data: list):
        self.memory.put("drafts", data)

    def add(self, kind: str, title: str, content: str, profile: str = "",
            status: str = "draft") -> int:
        data = self._all()
        draft_id = int(time.time() * 1000)
        data.append(
            {
                "id": draft_id,
                "kind": kind,
                "title": title,
                "content": content,
                "profile": profile,
                "status": status,
                "created": time.time(),
            }
        )
        self._save(data)
        return draft_id

    def set_status(self, draft_id: int, status: str) -> str:
        data = self._all()
        for d in data:
            if d["id"] == draft_id:
                d["status"] = status
                self._save(data)
                return f"Draft {draft_id} -> {status}."
        return f"Draft {draft_id} not found."

    def list(self, kind: Optional[str] = None) -> list:
        data = self._all()
        if kind:
            data = [d for d in data if d["kind"] == kind]
        return sorted(data, key=lambda d: d["created"], reverse=True)

    def get(self, draft_id: int) -> Optional[dict]:
        for d in self._all():
            if d["id"] == draft_id:
                return d
        return None

    def delete(self, draft_id: int) -> str:
        data = self._all()
        new = [d for d in data if d["id"] != draft_id]
        self._save(new)
        return f"Draft {draft_id} deleted." if len(new) != len(data) else "Not found."
