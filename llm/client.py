"""Anthropic Claude API client — supports direct API and AWS Bedrock."""

import json
import anthropic
from config import settings

# Bedrock model ID mapping (Bedrock uses different model IDs)
BEDROCK_MODEL_MAP = {
    "claude-sonnet-4-5": "us.anthropic.claude-sonnet-4-5-v2",
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6-v1",
    "claude-opus-4-6": "us.anthropic.claude-opus-4-6-v1",
    "claude-haiku-4-5": "us.anthropic.claude-haiku-4-5-v1",
}


class AnthropicClient:
    def __init__(self):
        self.use_bedrock = settings.USE_BEDROCK
        self.has_key = False
        self.client = None

        if self.use_bedrock:
            # Use AWS Bedrock — reads credentials from ~/.aws/credentials or env vars
            try:
                self.client = anthropic.AsyncAnthropicBedrock(
                    aws_region=settings.AWS_REGION,
                )
                self.has_key = True
            except Exception as e:
                print(f"[AnthropicClient] ERROR: Bedrock init failed: {e}", flush=True)
                self.client = None
        else:
            api_key = settings.ANTHROPIC_API_KEY or None
            self.has_key = bool(api_key)
            if self.has_key:
                self.client = anthropic.AsyncAnthropic(api_key=api_key)

    def _resolve_model(self, model: str) -> str:
        """Map standard model IDs to Bedrock model IDs if using Bedrock."""
        if self.use_bedrock:
            return BEDROCK_MODEL_MAP.get(model, model)
        return model

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 8192,
    ) -> dict:
        """Call Claude API and return parsed response.

        If credentials are not configured, returns a mock/placeholder response.
        """
        if not self.has_key or self.client is None:
            return {
                "content": json.dumps({
                    "root_cause": "Unable to perform LLM analysis — AI credentials not configured. This is a placeholder response.",
                    "affected_component": "unknown",
                    "impact": "Analysis unavailable without credentials.",
                    "fix_strategy": "Configure USE_BEDROCK=true with AWS credentials, or set ANTHROPIC_API_KEY.",
                    "confidence": 0.0,
                }),
                "model": "mock",
                "prompt_tokens": 0,
                "completion_tokens": 0,
            }

        resolved_model = self._resolve_model(model)
        response = await self.client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=120.0,
        )

        content = response.content[0].text if response.content else ""
        return {
            "content": content,
            "model": response.model,
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
        }

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-5",
    ) -> dict:
        """Call Claude and parse JSON from the response content."""
        result = await self.complete(system_prompt, user_prompt, model=model)
        content = result["content"]

        # Try to extract JSON from the response
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON block in markdown fences
            import re
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except json.JSONDecodeError:
                    parsed = {"raw_response": content, "parse_error": True}
            else:
                parsed = {"raw_response": content, "parse_error": True}

        return {
            "data": parsed,
            "model": result["model"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
        }
