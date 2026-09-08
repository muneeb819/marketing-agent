"""Market research module (analysis & briefs — live web optional)."""
from __future__ import annotations

import os

from ..config import Config
from ..llm import LLM
from ..tools.web import search, fetch_text, research_brief


class Research:
    def __init__(self, llm: LLM, config: Config):
        self.llm = llm
        self.config = config

    def competitor_brief(self, competitor: str, what: str = "offerings and positioning") -> str:
        sys = (
            "You are a market research analyst. Given a competitor name, produce a structured "
            "brief: who they serve, their likely pricing model, strengths, weaknesses, and 3 "
            "opportunities to differentiate. Note: base this on general knowledge; flag what "
            "should be verified manually on their live profile."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Competitor: {competitor}\nFocus: {what}"},
            ],
            temperature=0.4,
            max_tokens=1800,
        )

    def keyword_gaps(self, niche: str = "") -> str:
        niche = niche or self.config.business_niche or "your niche"
        sys = (
            "You are an SEO & marketplace keyword strategist. For the given niche, list 15 "
            "high-intent buyer keywords (Fiverr/Upwork style search terms), group them by "
            "intent (informational/transactional), and suggest 3 underserved angles."
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": f"Niche: {niche}"}],
            temperature=0.5,
        )

    def pricing_analysis(self, service: str, tier: str = "mid") -> str:
        sys = (
            "You are a pricing strategist for freelance services. Given a service and market "
            "tier, recommend a pricing range in " + self.config.currency + ", rationale based on "
            "value vs. hourly, and how to present it to avoid race-to-the-bottom."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Service: {service}\nMarket tier: {tier}"},
            ],
            temperature=0.4,
        )

    def trend_scan(self, topic: str) -> str:
        sys = (
            "You are a trends analyst. For the topic, list 5 emerging trends, why they matter "
            "for a freelancer/marketer, and one concrete action to capitalize on each. Mark "
            "anything that needs live verification."
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": f"Topic: {topic}"}],
            temperature=0.6,
        )

    # ---------- LIVE WEB RESEARCH ----------
    def web_research(self, topic: str) -> str:
        return research_brief(topic, self.llm.chat)

    def live_competitor(self, competitor: str) -> str:
        results = search(f"{competitor} services pricing", n=5)
        if not results or "error" in results[0]:
            return "Live lookup unavailable: " + str(results[0] if results else "no results")
        snippets = "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
        sys = (
            "You are a competitive analyst. Using the live search results, produce a brief on "
            f"{competitor}: what they offer, apparent positioning, and 3 ways to differentiate. "
            "Flag anything to verify on their live site."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Search results:\n{snippets}"},
            ],
            temperature=0.4,
            max_tokens=1500,
        )

    def live_trend_scan(self, topic: str) -> str:
        results = search(f"{topic} marketing trends 2025", n=6)
        if not results or "error" in results[0]:
            return "Live lookup unavailable: " + str(results[0] if results else "no results")
        snippets = "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
        sys = (
            "You are a trends analyst. Using the live search results, list 5 current trends "
            "about the topic, why each matters for a freelancer/marketer, and one concrete "
            "action per trend. Cite source titles."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Topic: {topic}\n\nResults:\n{snippets}"},
            ],
            temperature=0.5,
            max_tokens=1800,
        )

    def upwork_feed(self, query: str) -> str:
        from ..integrations.upwork import search_jobs, summarize_jobs

        token = os.environ.get("UPWORK_ACCESS_TOKEN", "")
        payload = search_jobs(query, token)
        if "error" in payload:
            return "Upwork: " + payload["error"]
        jobs = summarize_jobs(payload)
        if not jobs:
            return "No Upwork jobs returned (check token / query)."
        listing = "\n".join(
            f"- {j['title']} | {j['country']} | skills: {', '.join(j['skills'])}"
            for j in jobs
        )
        sys = (
            "You are an Upwork bidding strategist. Given these live job listings, pick the 3 "
            "best-fit jobs for the user, explain why each is a good match, and suggest a one-line "
            "proposal angle for each. Do not invent job details."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Query: {query}\n\nJobs:\n{listing}"},
            ],
            temperature=0.4,
            max_tokens=1600,
        )
