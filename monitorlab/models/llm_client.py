"""LLM client for interfacing with LM Studio via OpenAI-compatible API."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI, OpenAIError
from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with local LLM via LM Studio."""

    def __init__(self, settings: Optional[Any] = None):
        """Initialize LLM client.

        Args:
            settings: Optional settings object. If None, uses get_settings().
        """
        self.settings = settings or get_settings()
        self.client = AsyncOpenAI(
            base_url=self.settings.llm_api_base,
            api_key=self.settings.llm_api_key,
        )
        self.model = self.settings.llm_model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (default from settings)
            max_tokens: Maximum tokens to generate (default from settings)
            **kwargs: Additional parameters to pass to the API

        Returns:
            Generated text response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.settings.llm_temperature,
                max_tokens=max_tokens or self.settings.llm_max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""

        except OpenAIError as e:
            logger.error(f"LLM generation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LLM generation: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.settings.llm_temperature,
                max_tokens=max_tokens or self.settings.llm_max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            logger.error(f"LLM streaming error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LLM streaming: {e}")
            raise

    async def generate_with_context(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate a response with conversation context.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.settings.llm_temperature,
                max_tokens=max_tokens or self.settings.llm_max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""

        except OpenAIError as e:
            logger.error(f"LLM generation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LLM generation: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.generate(
                "Say 'OK' if you can read this.", max_tokens=10, temperature=0
            )
            return len(response) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate and extract JSON response from LLM.

        Args:
            prompt: User prompt requesting JSON
            system_prompt: Optional system prompt
            temperature: Lower temperature for more consistent JSON

        Returns:
            Parsed JSON dictionary
        """
        import json

        if system_prompt is None:
            system_prompt = "You are a helpful assistant that responds only with valid JSON."

        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        # Try to extract JSON from response
        try:
            # First try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Could not extract valid JSON from response: {response}")
