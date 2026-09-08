"""Full-funnel digital marketing module: SEO/blog, email, paid ads, landing pages, strategy."""
from __future__ import annotations

from ..config import Config
from ..llm import LLM


class Growth:
    def __init__(self, llm: LLM, config: Config):
        self.llm = llm
        self.config = config

    def _ctx(self) -> str:
        niche = self.config.business_niche or "your business"
        return f"Niche: {niche}. Brand voice: {self.config.brand_voice}."

    def blog_post(self, topic: str, keywords: str = "", length: str = "medium") -> str:
        sys = (
            "You are an SEO content writer. Write a complete, original, long-form blog post. "
            "Structure: SEO title, meta description, H1, engaging intro, 4-6 H2 sections with "
            "practical detail, a conclusion, and 3 FAQs. Naturally use the keywords. " + self._ctx()
        )
        user = f"Topic: {topic}\nKeywords: {keywords}\nLength: {length}"
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.7, max_tokens=2500,
        )

    def seo_keywords(self, niche: str) -> str:
        sys = (
            "You are an SEO strategist. Produce a keyword plan as a markdown table: "
            "Keyword | Search intent | Difficulty (1-100) | Where to use (blog / ad / page). "
            "Give 15 high-intent keywords for the niche, mixing head and long-tail. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": f"Niche: {niche}"}],
            temperature=0.5,
        )

    def meta_tags(self, page: str, keywords: str = "") -> str:
        sys = (
            "You are an SEO specialist. Write on-page SEO meta tags for a page: a title (<=60 chars), "
            "a meta description (<=155 chars), and 5 focus keywords. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Page: {page}\nKeywords: {keywords}"}],
            temperature=0.5,
        )

    def email_newsletter(self, topic: str, goal: str = "") -> str:
        sys = (
            "You are an email marketer. Write a newsletter: 2 subject-line A/B variants, preview text, "
            "warm greeting, one value paragraph, one story/offer paragraph, a single clear CTA, sign-off. "
            + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Topic: {topic}\nGoal: {goal}"}],
            temperature=0.7,
        )

    def email_sequence(self, topic: str, steps: int = 5) -> str:
        sys = (
            f"You are an email marketer. Write a {steps}-email nurture sequence. For each email give: "
            "Subject, Body (short), CTA. Number them clearly. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Topic: {topic}"}],
            temperature=0.7,
        )

    def ad_pack(self, product: str, audience: str = "") -> str:
        sys = (
            "You are a paid-media copywriter. Produce a full paid-ad pack with 2 variants each for: "
            "Meta (Facebook/Instagram), Google Search, and TikTok. Each variant: Primary text, Headline, "
            "CTA. " + self._ctx()
        )
        user = f"Product/service: {product}"
        if audience:
            user += f"\nTarget audience: {audience}"
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.7, max_tokens=2000,
        )

    def landing_page(self, product: str, goal: str = "") -> str:
        sys = (
            "You are a conversion copywriter. Write a landing page: hero headline + subhead, 3 benefit "
            "bullets, a social-proof line, a 4-item features list, a strong CTA, and a P.S. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Product/service: {product}\nGoal: {goal}"}],
            temperature=0.7,
        )

    def social_strategy(self, goal: str, platforms: str = "Instagram, TikTok, LinkedIn, X, Facebook") -> str:
        sys = (
            "You are a social media strategist. For each platform produce: posting frequency, best content "
            "formats, hook style, and one example idea. Return as a markdown section per platform. " + self._ctx()
        )
        return self.llm.chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": f"Goal: {goal}\nPlatforms: {platforms}"}],
            temperature=0.6,
        )
