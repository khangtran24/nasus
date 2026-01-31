"""Claude Agent SDK provider implementation.

This provider allows using Claude Pro subscription through the Agent SDK.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from core.providers.base import BaseProvider, ModelRouterResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available for Claude Agent SDK provider")


class ClaudeAgentSDKProvider(BaseProvider):
    """Provider for Claude Agent SDK (supports Claude subscription).

    This provider uses the Anthropic SDK with special configuration to leverage
    Claude subscription benefits (Pro/Team) when available.

    Features:
    - Automatic use of Claude subscription features if available
    - Higher rate limits and priority access for subscribers
    - Access to latest Claude models
    - Supports all standard Claude API features
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        **kwargs
    ):
        """Initialize Claude Agent SDK provider.

        Args:
            api_key: Claude API key (supports Claude subscription)
            base_url: Optional base URL
            default_model: Default model to use
            **kwargs: Additional configuration
                - use_pro_features: Enable Claude subscription features (default: True)
                - pro_tier: Specify subscription tier if applicable
        """
        super().__init__(api_key, base_url, default_model, **kwargs)

        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic SDK is required for Claude Agent SDK provider. "
                "Install with: pip install anthropic"
            )

        # Pro subscription configuration
        self.use_pro_features = kwargs.get("use_pro_features", True)
        self.pro_tier = kwargs.get("pro_tier", None)

        # Initialize Anthropic client with Pro configuration
        client_kwargs = {}

        # Use API key from environment or parameter
        # Check CLAUDE_API_KEY first, then fall back to ANTHROPIC_API_KEY for backwards compatibility
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        elif "CLAUDE_API_KEY" in os.environ:
            client_kwargs["api_key"] = os.environ["CLAUDE_API_KEY"]
        elif "ANTHROPIC_API_KEY" in os.environ:
            client_kwargs["api_key"] = os.environ["ANTHROPIC_API_KEY"]
        else:
            raise ValueError(
                "API key must be provided or set in CLAUDE_API_KEY or ANTHROPIC_API_KEY"
            )

        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        # Add Pro-specific headers if enabled
        if self.use_pro_features:
            default_headers = {}

            # Add Pro tier header if specified
            if self.pro_tier:
                default_headers["anthropic-tier"] = self.pro_tier

            # Add SDK identifier
            default_headers["anthropic-client-type"] = "agent-sdk"

            if default_headers:
                client_kwargs["default_headers"] = default_headers

        self.client = AsyncAnthropic(**client_kwargs)

        logger.debug(
            f"Claude Agent SDK provider initialized "
            f"(Pro features: {self.use_pro_features})"
        )

    def get_provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        return "claude_agent_sdk"

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelRouterResponse:
        """Create a message using Claude Agent SDK.

        Args:
            messages: Conversation messages
            model: Model to use (defaults to latest Claude Sonnet)
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional parameters
                - temperature: Sampling temperature (0.0-1.0)
                - top_p: Nucleus sampling parameter
                - top_k: Top-k sampling parameter
                - stop_sequences: List of stop sequences
                - stream: Enable streaming (not yet supported in this wrapper)

        Returns:
            Unified response object
        """
        # Default to Claude Sonnet 4.5 if no model specified
        model = self._validate_model(
            model or "claude-sonnet-4-5-20250929"
        )

        params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        # Add optional parameters
        if "temperature" in kwargs:
            params["temperature"] = kwargs.pop("temperature")

        if "top_p" in kwargs:
            params["top_p"] = kwargs.pop("top_p")

        if "top_k" in kwargs:
            params["top_k"] = kwargs.pop("top_k")

        if "stop_sequences" in kwargs:
            params["stop_sequences"] = kwargs.pop("stop_sequences")

        # Add any remaining parameters
        params.update(kwargs)

        logger.debug(
            f"Calling Claude Agent SDK with model: {model}, "
            f"Pro features: {self.use_pro_features}"
        )

        # Make async API call
        response = await self.client.messages.create(**params)

        logger.debug(
            f"Claude Agent SDK response: {response.stop_reason}, "
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

    async def create_message_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """Create a streaming message using Claude Agent SDK.

        Args:
            messages: Conversation messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional parameters

        Yields:
            Streaming response chunks

        Note:
            This is a placeholder for future streaming support.
            Currently redirects to non-streaming version.
        """
        logger.warning("Streaming not yet implemented, using non-streaming response")
        response = await self.create_message(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            **kwargs
        )
        yield response
