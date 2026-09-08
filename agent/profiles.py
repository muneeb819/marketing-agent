"""Multi-account profiles: switch brand voice, niche, handles per account."""
from __future__ import annotations

from typing import Optional


class Profiles:
    def __init__(self, memory):
        self.memory = memory  # agent.memory (SQLite store)

    def _all(self) -> dict:
        return self.memory.get("profiles", {}) or {}

    def _save(self, data: dict):
        self.memory.put("profiles", data)

    def add(self, name: str, niche: str = "", voice: str = "", currency: str = "",
            handles: Optional[dict] = None) -> str:
        data = self._all()
        data[name] = {
            "niche": niche,
            "voice": voice,
            "currency": currency,
            "handles": handles or {},
        }
        self._save(data)
        if self.active() is None:
            self.set_active(name)
        return f"Profile '{name}' created."

    def list(self) -> list[str]:
        return list(self._all().keys())

    def get(self, name: str) -> Optional[dict]:
        return self._all().get(name)

    def remove(self, name: str) -> str:
        data = self._all()
        if name in data:
            del data[name]
            self._save(data)
            return f"Profile '{name}' removed."
        return f"Profile '{name}' not found."

    def set_active(self, name: str) -> str:
        if name not in self._all():
            return f"Profile '{name}' does not exist."
        self.memory.put("active_profile", name)
        return f"Active profile: {name}"

    def active(self) -> Optional[str]:
        return self.memory.get("active_profile")

    def active_dict(self) -> dict:
        a = self.active()
        return self._all().get(a, {}) if a else {}
