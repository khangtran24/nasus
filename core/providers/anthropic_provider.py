"""Anthropic provider implementation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic
from anthropic.types import Message as AnthropicMessage

from core.providers.base import BaseProvider, ModelRouterResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        **kwargs
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            base_url: Optional base URL (defaults to Anthropic's API)
            default_model: Default model to use
            **kwargs: Additional configuration
        """
        super().__init__(api_key, base_url, default_model, **kwargs)

        # Initialize Anthropic async client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = AsyncAnthropic(**client_kwargs)
        logger.info("Anthropic provider initialized")

    def get_provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        return "anthropic"

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelRouterResponse:
        """Create a message using Anthropic API.

        Args:
            messages: Conversation messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            Unified response object
        """
        model = self._validate_model(model)

        params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        # Add any additional parameters
        params.update(kwargs)

        logger.debug(f"Calling Anthropic API with model: {model}")

        # Make async call using AsyncAnthropic
        response: AnthropicMessage = await self.client.messages.create(**params)

        logger.debug(
            f"Anthropic response: {response.stop_reason}, "
            f"tokens: {response.usage.input_tokens}/{response.usage.output_tokens}"
        )

        return ModelRouterResponse(
            content=response.content,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            model=response.model,
            id=response.id,
            role=response.role
        )
