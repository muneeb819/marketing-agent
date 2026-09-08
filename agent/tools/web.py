"""Live web research: search + page text extraction (no API key required)."""
from __future__ import annotations

import re
import time

import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MarketingOpsAgent/1.0; +https://example.com)"
}


def _bs(html):
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser")


def search(query: str, n: int = 8, timeout: int = 15) -> list[dict]:
    """Search via DuckDuckGo HTML and return [{title, url, snippet}]."""
    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=_HEADERS,
            timeout=timeout,
        )
        r.raise_for_status()
    except Exception as e:
        return [{"error": f"search failed: {e}"}]

    soup = _bs(r.text)
    results = []
    for row in soup.select(".result")[:n]:
        a = row.select_one("a.result__a")
        snippet = row.select_one(".result__snippet")
        if not a:
            continue
        url = a.get("href", "")
        # DuckDuckGo wraps urls in /l/?uddg=...
        m = re.search(r"uddg=([^&]+)", url)
        if m:
            from urllib.parse import unquote

            url = unquote(m.group(1))
        results.append(
            {
                "title": a.get_text(strip=True),
                "url": url,
                "snippet": snippet.get_text(strip=True) if snippet else "",
            }
        )
    return results


def fetch_text(url: str, max_chars: int = 4000, timeout: int = 20) -> str:
    """Fetch a URL and return cleaned readable text."""
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        return f"[fetch failed: {e}]"
    soup = _bs(r.text)
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text[:max_chars]


def research_brief(topic: str, llm_chat, n: int = 5) -> str:
    """Run a live search and return a synthesized brief using the provided llm.chat."""
    results = search(topic, n=n)
    if not results or "error" in results[0]:
        return "Live search unavailable: " + str(results[0] if results else "no results")

    snippets = "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
    sys = (
        "You are a market research analyst. Using the search results below, write a concise "
        "brief on the topic: key findings, notable trends, and 3 actionable takeaways. "
        "Cite source titles where useful."
    )
    user = f"Topic: {topic}\n\nSearch results:\n{snippets}"
    return llm_chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.4,
        max_tokens=1500,
    )
