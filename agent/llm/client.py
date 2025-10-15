"""OpenAI LLM client with Structured Outputs support"""
from openai import OpenAI
from typing import Type, TypeVar, List, Dict, Any
from pydantic import BaseModel
import os

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    Wrapper for OpenAI API with Structured Outputs.

    Uses GPT-4o with Structured Outputs for 100% schema adherence.
    No validation/retry needed - the model guarantees valid JSON.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4.1"
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4.1 with Structured Outputs)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def structured_completion(
        self,
        system_prompt: str,
        user_message: str,
        response_schema: Type[T],
        temperature: float = 0.0
    ) -> T:
        """
        Call OpenAI with Structured Outputs for 100% schema adherence.

        This uses the beta.chat.completions.parse API which guarantees
        the response will match the Pydantic schema exactly.

        Args:
            system_prompt: System message defining behavior
            user_message: User's input message
            response_schema: Pydantic model class for response structure
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Parsed Pydantic model instance

        Raises:
            OpenAI API exceptions if request fails
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=response_schema,
                temperature=temperature
            )

            # Extract parsed response (guaranteed to match schema)
            parsed = response.choices[0].message.parsed

            # Handle refusals (safety filtering)
            if response.choices[0].message.refusal:
                raise ValueError(f"Model refused: {response.choices[0].message.refusal}")

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
