import httpx
import json

payload = {
    "model": "qwen3.6:latest",
    "stream": False,
    "format": "json",
    "think": False,
    "prompt": """
You are TradingOS.

Return ONLY valid JSON.

{
  "recommendation": "BUY",
  "confidence": 82,
  "risk": "MEDIUM",
  "trade_strength": "STRONG",
  "suggested_position_size": 2,
  "reward_risk": 2.5,
  "reasoning": [
    "EMA crossover confirmed",
    "Momentum bullish",
    "Volume supports breakout"
  ]
}

Do not explain.
Do not think.
Do not use markdown.
Return exactly one JSON object.
"""
}

response = httpx.post(
    "http://host.docker.internal:11434/api/generate",
    json=payload,
    timeout=180,
)

print("=" * 80)
print("HTTP STATUS")
print("=" * 80)
print(response.status_code)

print()
print("=" * 80)
print("RAW RESPONSE")
print("=" * 80)
print(json.dumps(response.json(), indent=2))