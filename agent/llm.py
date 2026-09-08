"""LLM provider abstraction: OpenAI, Anthropic, or local Ollama."""
from __future__ import annotations

import json
import re

from .config import Config


class LLM:
    def __init__(self, config: Config):
        self.config = config
        self.provider = config.llm_provider.lower()
        self._openai = None
        self._anthropic = None

    @staticmethod
    def _strip(text: str) -> str:
        # remove <think>...</think> reasoning leaks from some models
        return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()

    def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """messages: list of {"role": "system|user|assistant", "content": "..."}"""
        try:
            if self.provider == "openai":
                return self._strip(self._chat_openai(messages, temperature, max_tokens))
            if self.provider == "anthropic":
                return self._strip(self._chat_anthropic(messages, temperature, max_tokens))
            if self.provider == "ollama":
                return self._strip(self._chat_ollama(messages, temperature, max_tokens))
        except Exception as e:  # surface friendly error, never crash the agent
            return f"[LLM error: {e}]\n\nCheck your API key / Ollama server, or switch LLM_PROVIDER."
        return f"[Unknown provider: {self.provider}]"

    def _chat_openai(self, messages, temperature, max_tokens) -> str:
        from openai import OpenAI

        kwargs = {"api_key": self.config.openai_api_key}
        if self.config.openai_base_url:
            kwargs["base_url"] = self.config.openai_base_url
            if "openrouter" in self.config.openai_base_url:
                kwargs["default_headers"] = {
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "MarketingOps Agent",
                }
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=self.config.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    def _chat_anthropic(self, messages, temperature, max_tokens) -> str:
        if self._anthropic is None:
            import anthropic

            self._anthropic = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        # Anthropic separates system from messages
        system = ""
        convo = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                convo.append({"role": m["role"], "content": m["content"]})
        resp = self._anthropic.messages.create(
            model=self.config.anthropic_model,
            system=system,
            messages=convo,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return "".join(block.text for block in resp.content).strip()

    def _chat_ollama(self, messages, temperature, max_tokens) -> str:
        import requests, subprocess

        url = f"{self.config.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.config.ollama_model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"

        r = requests.post(url, json=payload, headers=headers, timeout=180)
        if not r.ok:
            # model may be missing locally -> try to pull it, then retry once
            try:
                subprocess.run(
                    ["ollama", "pull", self.config.ollama_model],
                    check=True, timeout=900,
                )
                r = requests.post(url, json=payload, headers=headers, timeout=180)
            except Exception as pull_err:
                detail = self._ollama_error(r, pull_err)
                return (
                    f"[LLM error: {detail}]\n\n"
                    f"The local model '{self.config.ollama_model}' could not be loaded. "
                    f"Run 'ollama pull {self.config.ollama_model}' once, then retry."
                )
        if not r.ok:
            detail = self._ollama_error(r, None)
            return f"[LLM error: {detail}]\n\nCheck your Ollama server, or switch LLM_PROVIDER."
        return r.json()["message"]["content"].strip()

    @staticmethod
    def _ollama_error(r, pull_err) -> str:
        if r is not None:
            try:
                body = r.json().get("error", r.text)
            except Exception:
                body = r.text
            return f"Ollama {r.status_code}: {body}"
        return f"pull failed: {pull_err}"

    def models_available(self) -> bool:
        if self.provider == "ollama":
            try:
                import requests, subprocess

                base = self.config.ollama_base_url.rstrip("/")
                r = requests.get(f"{base}/api/tags", timeout=5)
                if r.status_code != 200:
                    return False
                tags = [m["name"] for m in r.json().get("models", [])]
                if not self._model_present(tags, self.config.ollama_model):
                    # auto-pull missing model so the agent is ready on first launch
                    try:
                        subprocess.run(
                            ["ollama", "pull", self.config.ollama_model],
                            check=True, timeout=900,
                        )
                        r2 = requests.get(f"{base}/api/tags", timeout=5)
                        tags = [m["name"] for m in r2.json().get("models", [])]
                    except Exception:
                        return False
                return self._model_present(tags, self.config.ollama_model)
            except Exception:
                return False
        return bool(
            (self.provider == "openai" and self.config.openai_api_key)
            or (self.provider == "anthropic" and self.config.anthropic_api_key)
        )

    @staticmethod
    def _model_present(tags, name: str) -> bool:
        return any(t == name or t.startswith(name + ":") for t in tags)
