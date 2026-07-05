"""OllamaProvider tests — HTTP behaviour and error mapping.

We stub the httpx.Client used inside the provider so no real network calls
happen. The provider is treated as a thin adapter over ``/api/generate``.
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.services.ai.ollama import OllamaProvider, OllamaProviderError


class _StubResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body) if isinstance(body, dict) else str(body)
    def json(self):
        if isinstance(self._body, dict):
            return self._body
        raise ValueError("non-JSON body")


class _StubClient:
    def __init__(self, response=None, raises=None, **_):
        self._response = response
        self._raises = raises
    def __enter__(self): return self
    def __exit__(self, *_a): return False
    def post(self, url, json=None):
        if self._raises:
            raise self._raises
        return self._response


def test_ok_response(monkeypatch: pytest.MonkeyPatch) -> None:
    body = {"response": '{"ok": true}', "prompt_eval_count": 5, "eval_count": 10}
    def factory(*a, **kw):
        return _StubClient(response=_StubResponse(200, body))
    monkeypatch.setattr(httpx, "Client", factory)

    p = OllamaProvider(host="http://x:11434", model="qwen3:8b")
    r = p.generate("prompt goes here")
    assert r.text == '{"ok": true}'
    assert r.model == "qwen3:8b"
    assert r.provider == "ollama"
    assert r.token_count == 15
    assert r.latency_ms >= 0


def test_error_status_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def factory(*a, **kw):
        return _StubClient(response=_StubResponse(500, {"error": "boom"}))
    monkeypatch.setattr(httpx, "Client", factory)

    p = OllamaProvider(host="http://x:11434", model="qwen3:8b")
    with pytest.raises(OllamaProviderError):
        p.generate("prompt")


def test_timeout_maps_to_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def factory(*a, **kw):
        return _StubClient(raises=httpx.ReadTimeout("slow"))
    monkeypatch.setattr(httpx, "Client", factory)

    p = OllamaProvider(host="http://x:11434", model="qwen3:8b", timeout_seconds=0.001)
    with pytest.raises(OllamaProviderError):
        p.generate("prompt")


# ---- reasoning-model field selection + /no_think soft switch -------------


def _stub(monkeypatch, body):
    import httpx as _h
    def factory(*a, **kw):
        return _StubClient(response=_StubResponse(200, body))
    monkeypatch.setattr(_h, "Client", factory)


def test_json_only_in_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub(monkeypatch, {"response": '{"recommendation":"BUY"}', "thinking": ""})
    p = OllamaProvider(host="http://x:11434", model="qwen3.6:latest")
    r = p.generate("prompt")
    assert r.text == '{"recommendation":"BUY"}'


def test_empty_response_json_in_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub(monkeypatch, {"response": "", "thinking": 'reasoning... {"recommendation":"SELL"}'})
    p = OllamaProvider(host="http://x:11434", model="qwen3.6:latest")
    r = p.generate("prompt")
    assert "SELL" in r.text and "{" in r.text


def test_json_in_nested_message_content(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub(monkeypatch, {"response": "", "message": {"content": '{"recommendation":"HOLD"}'}})
    p = OllamaProvider(host="http://x:11434", model="qwen3.6:latest")
    r = p.generate("prompt")
    assert r.text == '{"recommendation":"HOLD"}'


def test_no_think_soft_switch_appended(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}
    class _CapClient(_StubClient):
        def post(self, url, json=None):
            captured["body"] = json
            return self._response
    def factory(*a, **kw):
        return _CapClient(response=_StubResponse(200, {"response": "{}"}))
    monkeypatch.setattr(httpx, "Client", factory)
    p = OllamaProvider(host="http://x:11434", model="qwen3.6:latest")
    p.generate("analyse this")
    assert captured["body"]["prompt"].rstrip().endswith("/no_think")
    assert captured["body"]["think"] is False
    assert captured["body"]["format"] == "json"
