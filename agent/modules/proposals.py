"""Proposals & gig writing module (assisted — you review before posting)."""
from __future__ import annotations

from ..config import Config
from ..llm import LLM


class Proposals:
    def __init__(self, llm: LLM, config: Config):
        self.llm = llm
        self.config = config

    def _ctx(self) -> str:
        niche = self.config.business_niche or "general freelance services"
        voice = self.config.brand_voice
        return f"Business niche: {niche}. Brand voice: {voice}."

    def fiverr_gig(self, service: str, target_buyer: str = "", packages: bool = True) -> str:
        sys = (
            "You are an expert Fiverr seller consultant. Write a high-converting Fiverr gig. "
            "Return: a compelling title (max 80 chars), a search-optimized description with clear "
            "sections (What I offer, Why me, Process, FAQ), and 3 tiered packages "
            "(Basic/Standard/Premium) with deliverables and prices in "
            f"{self.config.currency}. Be specific, no fluff. " + self._ctx()
        )
        user = f"Service to offer: {service}"
        if target_buyer:
            user += f"\nTarget buyer: {target_buyer}"
        if not packages:
            user += "\nDo NOT include packages, just title + description."
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.6,
        )

    def upwork_proposal(self, job_title: str, job_description: str, your_value: str = "") -> str:
        sys = (
            "You are an expert Upwork freelancer. Write a tailored, client-ready cover letter "
            "for a job. Structure: 1) a hook referencing the client's specific need, "
            "2) proof/relevant experience, 3) how you'll approach it, 4) a clear call to action. "
            "Keep under 250 words, no templates, never lie about experience. " + self._ctx()
        )
        user = f"Job title: {job_title}\n\nJob description:\n{job_description}"
        if your_value:
            user += f"\n\nMy relevant experience / differentiators:\n{your_value}"
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.5,
        )

    def bid_strategy(self, job_description: str) -> str:
        sys = (
            "You are an Upwork bidding strategist. Given a job post, output: an estimated "
            "appropriate bid range in " + self.config.currency + ", recommended connects to spend, "
            "key proposal angle, red flags to watch, and whether to apply. " + self._ctx()
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": job_description},
            ],
            temperature=0.4,
        )
