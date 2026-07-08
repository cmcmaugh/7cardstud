from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .agents import AgentDecision, DecisionRequest


class ChatGPTStudAgent:
    """OpenAI-backed opponent that keeps one response session per seat."""

    def __init__(self, name: str, model: str = "gpt-5-mini", api_key: str | None = None) -> None:
        self.name = name
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.previous_response_id: str | None = None
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for ChatGPTStudAgent")

    def decide(self, request: DecisionRequest) -> AgentDecision:
        payload: dict[str, object] = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You are a disciplined 7-card stud limit poker opponent. "
                        "Return compact JSON with action and reason. Never choose an illegal action."
                    ),
                },
                {"role": "user", "content": request.to_prompt()},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "stud_decision",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "action": {"type": "string", "enum": request.legal_actions},
                            "reason": {"type": "string"},
                        },
                        "required": ["action", "reason"],
                    },
                }
            },
        }
        if self.previous_response_id:
            payload["previous_response_id"] = self.previous_response_id

        data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=45) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {error.code} {details}") from error

        self.previous_response_id = response_body.get("id") or self.previous_response_id
        content = _extract_text(response_body)
        parsed = json.loads(content)
        return AgentDecision(action=parsed["action"], reason=parsed.get("reason", ""))


def _extract_text(response_body: dict[str, object]) -> str:
    if isinstance(response_body.get("output_text"), str):
        return str(response_body["output_text"])
    output = response_body.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    return content["text"]
    raise RuntimeError("OpenAI response did not contain text output")
