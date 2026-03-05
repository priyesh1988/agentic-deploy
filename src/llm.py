import json
from typing import Any, Dict
import httpx
from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"

class AnthropicLLM:
    def __init__(self, api_key: str = ANTHROPIC_API_KEY, model: str = ANTHROPIC_MODEL):
        self.api_key = api_key
        self.model = model

    async def complete_json(self, system: str, user: str, schema_hint: Dict[str, Any]) -> Dict[str, Any]:
        """Return a JSON object. If no API key is set, return a deterministic local fallback."""
        if not self.api_key:
            return self._fallback(system, user, schema_hint)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 600,
            "system": system,
            "messages": [{"role":"user","content": user}],
        }

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(ANTHROPIC_MESSAGES_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        # Anthropic returns content blocks; pull text and parse JSON
        text = ""
        for blk in data.get("content", []):
            if blk.get("type") == "text":
                text += blk.get("text", "")
        # Try to extract JSON from text
        return _extract_json(text) or self._fallback(system, user, schema_hint)

    def _fallback(self, system: str, user: str, schema_hint: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic stub: still "Anthropic everywhere" but safe offline.
        return {
            "note": "anthropic_mock_mode_no_api_key",
            **schema_hint
        }

def _extract_json(text: str):
    # very small extractor: first {...} block
    import re, json
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
