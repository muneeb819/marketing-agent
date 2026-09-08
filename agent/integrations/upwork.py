"""Read-only Upwork API integration (job feed). No posting — ToS-safe.

Setup:
  1. Create an app at https://www.upwork.com/developer/api (API v2 / OAuth2).
  2. Set in .env:
       UPWORK_CLIENT_ID=...
       UPWORK_CLIENT_SECRET=...
       UPWORK_REDIRECT_URI=http://localhost:8000/callback
       UPWORK_ACCESS_TOKEN=...   # after completing the OAuth flow
  3. Use `python cli.py upwork-auth` for the one-time token exchange, or paste a
     token generated from the Upwork developer console.

This only READS the job feed; it never applies or messages on your behalf.
"""
from __future__ import annotations

import os

import requests

BASE = "https://www.upwork.com/api/profiles/v2"


def auth_url(client_id: str, redirect_uri: str, state: str = "marketingops") -> str:
    scope = "jobs:read"
    return (
        "https://www.upwork.com/oauth/v2/authorize"
        f"?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&state={state}&scope={scope}"
    )


def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    r = requests.post(
        "https://www.upwork.com/oauth/v2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def search_jobs(query: str, token: str, count: int = 10) -> dict:
    """Return raw Upwork job-search JSON for a query. Read-only."""
    if not token:
        return {"error": "UPWORK_ACCESS_TOKEN not set. Run `python cli.py upwork-auth`."}
    try:
        r = requests.get(
            f"{BASE}/search/jobs.json",
            params={"q": query, "limit": count},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"Upwork request failed: {e}"}


def summarize_jobs(payload: dict) -> list[dict]:
    """Extract a clean list of jobs from the API response."""
    if "error" in payload:
        return []
    jobs = payload.get("results") or []
    out = []
    for j in jobs:
        out.append(
            {
                "title": j.get("title", ""),
                "budget": j.get("budget", {}),
                "skills": j.get("skills", []),
                "url": j.get("url", ""),
                "country": j.get("client", {}).get("country", ""),
            }
        )
    return out
