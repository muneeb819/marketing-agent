"""Configuration loaded from environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # LLM provider: "openai" | "anthropic" | "ollama"
    llm_provider: str = field(default="ollama")
    openai_api_key: str = field(default="")
    openai_model: str = field(default="gpt-4o-mini")
    openai_base_url: str = field(default="")
    anthropic_api_key: str = field(default="")
    anthropic_model: str = field(default="claude-3-5-sonnet-latest")
    ollama_base_url: str = field(default="http://localhost:11434")
    ollama_model: str = field(default="llama3.1")
    ollama_api_key: str = field(default="")

    # Agent identity / branding
    agent_name: str = field(default="MarketingOps Agent")
    business_niche: str = field(default="")
    brand_voice: str = field(default="professional, friendly, concise")
    currency: str = field(default="USD")

    # Storage
    data_dir: str = field(default="data")
    db_path: str = field(default="data/memory.db")

    # Web server
    host: str = field(default="0.0.0.0")
    port: int = field(default=8000)

    @classmethod
    def load(cls) -> "Config":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass

        def env(name: str, default):
            val = os.environ.get(name)
            if val is None or val == "":
                return default
            return val

        return cls(
            llm_provider=env("LLM_PROVIDER", "ollama"),
            openai_api_key=env("OPENAI_API_KEY", ""),
            openai_model=env("OPENAI_MODEL", "gpt-4o-mini"),
            openai_base_url=env("OPENAI_BASE_URL", ""),
            anthropic_api_key=env("ANTHROPIC_API_KEY", ""),
            anthropic_model=env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            ollama_base_url=env("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=env("OLLAMA_MODEL", "llama3.1"),
            ollama_api_key=env("OLLAMA_API_KEY", ""),
            agent_name=env("AGENT_NAME", "MarketingOps Agent"),
            business_niche=env("BUSINESS_NICHE", ""),
            brand_voice=env("BRAND_VOICE", "professional, friendly, concise"),
            currency=env("CURRENCY", "USD"),
            data_dir=env("DATA_DIR", "data"),
            db_path=env("DB_PATH", "data/memory.db"),
            host=env("HOST", "0.0.0.0"),
            port=int(env("PORT", "8000")),
        )

    def as_dict(self) -> dict:
        return {
            "llm_provider": self.llm_provider,
            "openai_model": self.openai_model,
            "anthropic_model": self.anthropic_model,
            "ollama_model": self.ollama_model,
            "agent_name": self.agent_name,
            "business_niche": self.business_niche,
            "brand_voice": self.brand_voice,
            "currency": self.currency,
        }
