"""LLM client with support for OpenAI and Claude (via OpenAI SDK compatibility)"""
from openai import OpenAI
from typing import Type, TypeVar, List, Dict, Any
from pydantic import BaseModel
import os

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Wrapper for LLM APIs with Structured Outputs support.

    Supports both OpenAI and Anthropic Claude via OpenAI SDK compatibility.
    Configure provider via LLM_PROVIDER env var ('openai' or 'anthropic').

    Uses Structured Outputs for 100% schema adherence.
    No validation/retry needed - the model guarantees valid JSON.
    """

    # Default models for each provider
    DEFAULT_MODELS = {
        "openai": "gpt-4.1",
        "anthropic": "claude-sonnet-4-5"
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        provider: str | None = None
    ):
        """
        Initialize LLM client.

        Args:
            api_key: API key (defaults to provider-specific env var)
            model: Model to use (defaults to provider-specific default, or LLM_MODEL env var)
            provider: Provider to use: 'openai' or 'anthropic' (defaults to LLM_PROVIDER env var)
        """
        # Determine provider
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        if self.provider not in ["openai", "anthropic"]:
            raise ValueError(f"Invalid provider '{self.provider}'. Must be 'openai' or 'anthropic'")

        # Get API key based on provider
        if self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")
            base_url = None  # Use default OpenAI base URL
        else:  # anthropic
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var or pass api_key parameter.")
            base_url = "https://api.anthropic.com/v1/"

        # Initialize OpenAI client (works for both providers)
        if base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=self.api_key)

        # Determine model
        self.model = model or os.getenv("LLM_MODEL") or self.DEFAULT_MODELS[self.provider]

    def structured_completion(
        self,
        system_prompt: str,
        user_message: str,
        response_schema: Type[T],
        temperature: float = 0.0
    ) -> T:
        """
        Call LLM with structured JSON output.

        For OpenAI: Uses response_format with json_schema for guaranteed compliance.
        For Anthropic: Adds JSON schema to prompt (response_format is ignored by Claude).

        Args:
            system_prompt: System message defining behavior
            user_message: User's input message
            response_schema: Pydantic model class for response structure
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Parsed Pydantic model instance

        Raises:
            API exceptions if request fails
        """
        try:
            import json

            # Get JSON schema from Pydantic model
            json_schema = response_schema.model_json_schema()

            # For Anthropic, we need to include the schema in the prompt
            # since response_format is ignored
            if self.provider == "anthropic":
                schema_str = json.dumps(json_schema, indent=2)
                enhanced_system_prompt = f"""{system_prompt}

You must respond with valid JSON that matches this exact schema:
{schema_str}

Respond ONLY with the JSON object, no other text."""

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature
                )
            else:
                # OpenAI: use response_format for structured outputs
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_schema.__name__,
                            "schema": json_schema,
                            "strict": False  # Disable strict mode to allow additionalProperties
                        }
                    },
                    temperature=temperature
                )

            # Parse JSON response into Pydantic model
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from model")

            # Strip markdown code fences if present (Claude often wraps JSON in ```json ... ```)
            content = content.strip()
            if content.startswith("```"):
                # Remove opening fence (```json or ```)
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            parsed_json = json.loads(content)
            parsed = response_schema.model_validate(parsed_json)

            return parsed

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> str:
        """
        Standard chat completion without structured outputs.

        Use this for generating free-form text responses.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")
