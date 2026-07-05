"""
TradingOS - Ollama JSON Test

Usage:
    python test_ollama_json.py
"""

import json
import httpx

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"

payload = {
    "model": "qwen3.6:latest",
    "stream": False,
    "format": "json",
    "think": False,
    "prompt": """
You are TradingOS.

Return ONLY valid JSON.

Schema:

{
  "recommendation":"BUY",
  "confidence":80,
  "risk":"MEDIUM",
  "reasoning":[
    "Reason 1",
    "Reason 2"
  ]
}

Do not explain.
Do not use markdown.
Do not output anything except JSON.
""",
}

print("=" * 80)
print("Sending request to Ollama...")
print("=" * 80)

response = httpx.post(
    OLLAMA_URL,
    json=payload,
    timeout=180,
)

print(f"HTTP Status : {response.status_code}")
print()

envelope = response.json()

print("=" * 80)
print("FULL OLLAMA RESPONSE")
print("=" * 80)

print(json.dumps(envelope, indent=2))

response_text = (envelope.get("response") or "").strip()
thinking_text = (envelope.get("thinking") or "").strip()

print()
print("=" * 80)
print("FIELD ANALYSIS")
print("=" * 80)

print("response length :", len(response_text))
print("thinking length :", len(thinking_text))


def looks_like_json(text: str) -> bool:
    return text.startswith("{") or text.startswith("[")


if looks_like_json(response_text):
    selected = response_text
    source = "response"

elif looks_like_json(thinking_text):
    selected = thinking_text
    source = "thinking"

elif response_text:
    selected = response_text
    source = "response"

elif thinking_text:
    selected = thinking_text
    source = "thinking"

else:
    selected = ""
    source = "empty"

print()
print("=" * 80)
print("SELECTED FIELD")
print("=" * 80)

print(source)
print()

print(selected)

print()
print("=" * 80)
print("JSON VALIDATION")
print("=" * 80)

try:
    parsed = json.loads(selected)

    print("SUCCESS")
    print(json.dumps(parsed, indent=2))

except Exception as ex:
    print("FAILED")
    print(ex)