"""Analytics & reporting module (you paste data, it interprets)."""
from __future__ import annotations

from ..config import Config
from ..llm import LLM


class Analytics:
    def __init__(self, llm: LLM, config: Config):
        self.llm = llm
        self.config = config

    def report(self, data: str, period: str = "last month") -> str:
        sys = (
            "You are a marketing analyst. Given raw performance data (earnings, views, clicks, "
            "proposals sent, conversions, etc.), produce a clear report: headline metrics, what "
            "improved, what declined, root-cause hypotheses, and 3 prioritized actions. Use "
            f"{self.config.currency} for money. Be direct."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Period: {period}\n\nData:\n{data}"},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

    def kpi_dashboard_template(self) -> str:
        sys = (
            "You are a freelance business analyst. Output a ready-to-use KPI tracking template "
            "as a markdown table: Metric | Target | How to measure | Frequency, focused on "
            "Fiverr/Upwork + social marketing."
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": "Generate template."}],
            temperature=0.3,
        )

    def funnel_diagnosis(self, funnel: str) -> str:
        sys = (
            "You are a conversion optimization expert. Given a description of a marketing/sales "
            "funnel and where leads drop off, identify the weakest stage and give 3 fixes with "
            "expected impact."
        )
        return self.llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": funnel}],
            temperature=0.4,
        )
