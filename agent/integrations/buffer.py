"""Official Buffer integration (schedule approved posts to connected social accounts).

Buffer is built for this: you connect your social accounts to Buffer once, then push
APPROVED drafts and Buffer publishes them on your schedule. This is the legitimate,
ToS-safe way to reduce your manual posting load.

Setup:
  1. Create an app at https://buffer.com/developers and generate an access token, OR
     grab a token from the Buffer dashboard.
  2. Set BUFFER_ACCESS_TOKEN in .env.
  3. Connect the social profiles you want inside Buffer.
"""
from __future__ import annotations

import os

import requests

BASE = "https://api.bufferapp.com/1"


def list_profiles(token: str) -> list:
    if not token:
        return [{"error": "BUFFER_ACCESS_TOKEN not set."}]
    try:
        r = requests.get(f"{BASE}/profiles.json", params={"access_token": token}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return [{"error": f"Buffer request failed: {e}"}]


def create_post(token: str, text: str, profile_ids: list, scheduled_at: int | None = None) -> dict:
    """Schedule a post on the given Buffer profile ids. User-approved only."""
    if not token:
        return {"error": "BUFFER_ACCESS_TOKEN not set."}
    params = {
        "access_token": token,
        "profile_ids[]": profile_ids,
        "text": text,
    }
    if scheduled_at:
        params["scheduled_at"] = scheduled_at
    try:
        r = requests.post(f"{BASE}/updates/create.json", data=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"Buffer post failed: {e}"}
