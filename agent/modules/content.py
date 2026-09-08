"""Content & social media module (draft + plan, you approve & post)."""
from __future__ import annotations

from ..config import Config
from ..llm import LLM


class Content:
    def __init__(self, llm: LLM, config: Config):
        self.llm = llm
        self.config = config

    def _ctx(self) -> str:
        niche = self.config.business_niche or "your business"
        return f"Niche: {niche}. Brand voice: {self.config.brand_voice}."

    def post(self, topic: str, platform: str = "Instagram", cta: str = "") -> str:
        sys = (
            "You are a social media copywriter. Write one engaging post for the given platform "
            "with a scroll-stopping hook, 2-4 short body lines, 3-5 relevant hashtags, and an "
            "optional CTA. Match the brand voice. " + self._ctx()
        )
        user = f"Platform: {platform}\nTopic: {topic}"
        if cta:
            user += f"\nDesired CTA: {cta}"
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.8,
        )

    def calendar(self, goal: str, days: int = 7, platforms: str = "Instagram, LinkedIn, X") -> str:
        sys = (
            "You are a content strategist. Produce a " + str(days) + "-day content calendar as a "
            "markdown table (Date | Platform | Content idea | Hook | CTA) covering platforms: "
            f"{platforms}. Tie it to this goal. " + self._ctx()
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Goal: {goal}"},
            ],
            temperature=0.6,
            max_tokens=2000,
        )

    def repurpose(self, source: str) -> str:
        sys = (
            "You are a content repurposing expert. Given a piece of long-form content, produce: "
            "3 short social posts, 1 email newsletter draft, and 5 blog title ideas. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": source}],
            temperature=0.7,
        )

    def ad_copy(self, product: str, audience: str = "", platform: str = "Facebook") -> str:
        sys = (
            "You are a paid-ad copywriter. Write 3 ad variants (primary text + headline + CTA) "
            f"for {platform}, each with a different angle. " + self._ctx()
        )
        user = f"Product/service: {product}"
        if audience:
            user += f"\nTarget audience: {audience}"
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.7,
        )
