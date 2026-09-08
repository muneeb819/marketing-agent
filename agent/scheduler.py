"""Draft reminder scheduler (stores due reminders, surfaces what's pending)."""
from __future__ import annotations

import time
from typing import Optional


def parse_when(spec: str) -> float:
    """Parse a 'when' spec into an epoch timestamp.

    Accepts: '30m', '2h', '3d', or 'HH:MM' (today, or tomorrow if already past).
    """
    spec = spec.strip().lower()
    now = time.time()
    if spec.endswith("m"):
        return now + float(spec[:-1]) * 60
    if spec.endswith("h"):
        return now + float(spec[:-1]) * 3600
    if spec.endswith("d"):
        return now + float(spec[:-1]) * 86400
    if ":" in spec:  # HH:MM local time
        import datetime

        h, _, mm = spec.partition(":")
        target = datetime.datetime.now().replace(
            hour=int(h), minute=int(mm), second=0, microsecond=0
        )
        if target.timestamp() < now:
            target = target + datetime.timedelta(days=1)
        return target.timestamp()
    # plain minutes fallback
    try:
        return now + float(spec) * 60
    except ValueError:
        raise ValueError(f"Cannot parse time spec: {spec}")


class Reminders:
    def __init__(self, memory):
        self.memory = memory

    def _all(self) -> list:
        return self.memory.get("reminders", []) or []

    def _save(self, data: list):
        self.memory.put("reminders", data)

    def add(self, draft_id: int, due_ts: float, note: str = "") -> int:
        data = self._all()
        rid = int(time.time() * 1000)
        data.append(
            {
                "id": rid,
                "draft_id": draft_id,
                "due": float(due_ts),
                "note": note,
                "done": False,
                "created": time.time(),
            }
        )
        self._save(data)
        return rid

    def list(self, include_done: bool = False) -> list:
        data = self._all()
        if not include_done:
            data = [d for d in data if not d["done"]]
        return sorted(data, key=lambda d: d["due"])

    def due(self, now: Optional[float] = None) -> list:
        now = now or time.time()
        return [d for d in self.list() if d["due"] <= now]

    def complete(self, rid: int) -> str:
        data = self._all()
        for d in data:
            if d["id"] == rid:
                d["done"] = True
        self._save(data)
        return "ok"


def to_ics(summary: str, dtstart: float, description: str = "", uid: str = "marketingops") -> str:
    """Build a minimal VCALENDAR string for a reminder (imports into phone calendars)."""
    import datetime

    def fmt(ts):
        return datetime.datetime.utcfromtimestamp(ts).strftime("%Y%m%dT%H%M%SZ")

    def esc(s):
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//MarketingOps//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}-{int(dtstart)}\r\n"
        f"DTSTAMP:{fmt(dtstart)}\r\n"
        f"DTSTART:{fmt(dtstart)}\r\n"
        f"SUMMARY:{esc(summary)}\r\n"
        f"DESCRIPTION:{esc(description)}\r\n"
        "END:VEVENT\r\nEND:VCALENDAR\r\n"
    )
