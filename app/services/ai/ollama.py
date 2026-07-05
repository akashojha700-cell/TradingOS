"""Ollama AI provider.

Talks to a local (or host-mapped) Ollama daemon via HTTP. On Windows / Mac,
Docker containers cannot reach the host loopback — use ``host.docker.internal``
(configured in ``.env`` via ``OLLAMA_HOST``).

Reasoning-model handling
------------------------

Newer "thinking" models (qwen3-thinking, gpt-oss, deepseek-r1, …) return the
JSON payload in the ``thinking`` field while leaving ``response`` empty. Two
mitigations:

1. **``think: false``** is sent in the request body by default so the daemon
   disables reasoning on capable models. Models that don't recognise the flag
   silently ignore it.
2. If ``response`` still comes back empty, we fall back to ``thinking``. The
   downstream :class:`app.services.ai.json_validator.JsonValidator` then
   handles Markdown fences, prose, and partial-field recovery.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from app.core.logging import get_logger
from app.services.ai.schemas import ProviderResponse

logger = get_logger("tradingos.ai.ollama")


class OllamaProviderError(RuntimeError):
    """Raised when Ollama cannot be reached or returned a non-success status."""


class OllamaProvider:
    """Ollama HTTP provider using the ``/api/generate`` endpoint."""

    name: str = "ollama"

    def __init__(
        self,
        *,
        host: str,
        model: str,
        timeout_seconds: float = 60.0,
        request_json_mode: bool = True,
        disable_reasoning: bool = True,
    ) -> None:
        self._host = host.rstrip("/")
        self.model = model
        self._timeout = timeout_seconds
        self._json_mode = request_json_mode
        self._disable_reasoning = disable_reasoning

    def generate(self, prompt: str, *, system: Optional[str] = None) -> ProviderResponse:
        """Send the prompt to Ollama and return a :class:`ProviderResponse`."""
        url = self._host + "/api/generate"
        # qwen3-family soft switch: appending ``/no_think`` forces the model to
        # skip its <think> phase and answer directly. This is what actually makes
        # reasoning models fast and JSON-clean — the API ``think:false`` flag is
        # honoured by newer Ollama builds but silently ignored by some model
        # tags (which then burn the whole budget thinking and time out / return
        # an empty ``response``). ``/no_think`` is plain text to non-qwen models.
        effective_prompt = f"{prompt}\n\n/no_think" if self._disable_reasoning else prompt
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": effective_prompt,
            "stream": False,
            # Low temperature → more deterministic, well-formed JSON.
            "options": {"temperature": 0.2},
        }
        if system:
            body["system"] = system
        if self._json_mode:
            body["format"] = "json"
        if self._disable_reasoning:
            body["think"] = False

        start = time.monotonic()
        try:
            # Explicit per-phase timeout. The whole budget goes to the READ
            # phase because a local LLM streams nothing until generation
            # finishes — this is what a slow reasoning model actually needs.
            # A short connect timeout still fails fast if Ollama is down.
            timeout = httpx.Timeout(self._timeout, connect=10.0)
            with httpx.Client(timeout=timeout) as client:
                r = client.post(url, json=body)
        except httpx.TimeoutException as exc:
            latency = int((time.monotonic() - start) * 1000)
            logger.warning("ai.ollama.timeout", host=self._host, ms=latency)
            raise OllamaProviderError(
                f"Ollama timeout after {latency}ms at {self._host}"
            ) from exc
        except httpx.HTTPError as exc:
            latency = int((time.monotonic() - start) * 1000)
            logger.warning(
                "ai.ollama.network_error",
                host=self._host, error=str(exc), ms=latency,
            )
            raise OllamaProviderError(f"Ollama HTTP error: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        if r.status_code >= 400:
            logger.warning(
                "ai.ollama.bad_status",
                host=self._host,
                status=r.status_code,
                body_preview=(r.text or "")[:180],
            )
            raise OllamaProviderError(
                f"Ollama returned {r.status_code}: {(r.text or '')[:160]}"
            )

        try:
            data = r.json()
        except ValueError as exc:
            raise OllamaProviderError(
                f"Ollama returned non-JSON envelope: {exc}"
            ) from exc

        # Extract candidate texts from every field a model might populate.
        # ``/api/generate`` uses ``response`` (+ ``thinking`` on reasoning
        # models); some builds mirror ``/api/chat`` and nest ``message.content``.
        response_text = str(data.get("response") or "")
        thinking_text = str(data.get("thinking") or "")
        message_text = ""
        _msg = data.get("message")
        if isinstance(_msg, dict):
            message_text = str(_msg.get("content") or "")

        # --- DIAGNOSTICS: raw Ollama envelope (lengths never truncated) ------
        logger.info(
            "ai.ollama.raw_response",
            status=r.status_code,
            top_level_keys=sorted(data.keys()),
            response_len=len(response_text),
            thinking_len=len(thinking_text),
            message_len=len(message_text),
            response_preview=response_text[:300],
            thinking_preview=thinking_text[:300],
        )

        def _looks_like_json(s: str) -> bool:
            return "{" in s and "}" in s

        # Prefer whichever field actually *contains* a JSON object; otherwise
        # fall back to the first non-empty field so the validator can still try.
        candidates = (
            ("response", response_text),
            ("message", message_text),
            ("thinking", thinking_text),
        )
        text, source_field = "", "empty"
        for _name, _val in candidates:
            if _looks_like_json(_val):
                text, source_field = _val, _name
                break
        else:
            for _name, _val in candidates:
                if _val.strip():
                    text, source_field = _val, _name
                    break

        # --- DIAGNOSTICS: exact string handed to the JSON validator ---------
        logger.info(
            "ai.ollama.validator_input",
            source_field=source_field,
            length=len(text),
            value=text[:1000],
        )

        prompt_tokens     = int(data.get("prompt_eval_count") or 0)
        completion_tokens = int(data.get("eval_count") or 0)
        thinking_tokens   = int(data.get("thinking_eval_count") or 0)
        total_tokens      = (prompt_tokens + completion_tokens + thinking_tokens) or None

        logger.info(
            "ai.ollama.ok",
            host=self._host, model=self.model, ms=latency_ms,
            tokens=total_tokens, source_field=source_field,
            think_disabled=self._disable_reasoning,
        )
        return ProviderResponse(
            text=text,
            model=self.model,
            latency_ms=latency_ms,
            token_count=total_tokens,
            provider=self.name,
        )
