"""Model router for handling multiple LLM providers.

This module provides a unified interface for working with different LLM providers
including Anthropic, OpenRouter, and Claude Agent SDK (Pro subscription support).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from core.providers import (
    AnthropicProvider,
    BaseProvider,
    ClaudeAgentSDKProvider,
    ModelRouterResponse,
    OpenRouterProvider,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

ProviderType = Literal["anthropic", "openrouter", "claude_agent_sdk"]


class ModelRouter:
    """Router for handling requests to different LLM providers.

    Supports:
    - anthropic: Direct Anthropic API access
    - openrouter: Multi-model access via OpenRouter
    - claude_agent_sdk: Claude Agent SDK with Pro subscription support

    Example:
        ```python
        # Using Anthropic
        router = ModelRouter(
            provider="anthropic",
            api_key="sk-ant-...",
            default_model="claude-sonnet-4-5-20250929"
        )

        # Using Claude Agent SDK (Pro subscription)
        router = ModelRouter(
            provider="claude_agent_sdk",
            api_key="sk-ant-...",
            default_model="claude-sonnet-4-5-20250929",
            use_pro_features=True
        )

        # Using OpenRouter
        router = ModelRouter(
            provider="openrouter",
            api_key="sk-or-...",
            default_model="anthropic/claude-sonnet-4-5"
        )

        # Make a request
        response = await router.create_message(
            messages=[{"role": "user", "content": "Hello!"}],
            system="You are a helpful assistant."
        )
        ```
    """

    def __init__(
        self,
        provider: ProviderType = "anthropic",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        **kwargs
    ):
        """Initialize the model router.

        Args:
            provider: LLM provider to use
            api_key: API key for the provider
            base_url: Optional base URL (provider-specific)
            default_model: Default model to use if not specified in requests
            **kwargs: Additional provider-specific configuration
                For claude_agent_sdk:
                    - use_pro_features: Enable Pro features (default: True)
                    - pro_tier: Specify Pro tier
                For openrouter:
                    - app_name: Application name for tracking
                    - site_url: Site URL for tracking
        """
        self.provider_type = provider
        self.provider = self._initialize_provider(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            **kwargs
        )

        logger.info(
            f"ModelRouter initialized with provider: {provider} "
            f"({self.provider.get_provider_name()})"
        )

    def _initialize_provider(
        self,
        provider: ProviderType,
        api_key: Optional[str],
        base_url: Optional[str],
        default_model: Optional[str],
        **kwargs
    ) -> BaseProvider:
        """Initialize the appropriate provider based on type.

        Args:
            provider: Provider type
            api_key: API key
            base_url: Base URL
            default_model: Default model
            **kwargs: Additional configuration

        Returns:
            Initialized provider instance

        Raises:
            ValueError: If provider type is unsupported
        """
        if provider == "anthropic":
            return AnthropicProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                **kwargs
            )

        elif provider == "openrouter":
            return OpenRouterProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                **kwargs
            )

        elif provider == "claude_agent_sdk":
            return ClaudeAgentSDKProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                **kwargs
            )

        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: anthropic, openrouter, claude_agent_sdk"
            )

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelRouterResponse:
        """Create a message using the selected provider.

        Args:
            messages: Conversation messages in format:
                [{"role": "user", "content": "Hello"}, ...]
            model: Model to use (uses default if not specified)
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions (Anthropic format)
            **kwargs: Additional provider-specific parameters

        Returns:
            Unified response object

        Raises:
            ValueError: If required parameters are missing
            Exception: If API call fails
        """
        return await self.provider.create_message(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            **kwargs
        )

    def get_provider_name(self) -> str:
        """Get the active provider name.

        Returns:
            Provider name
        """
        return self.provider.get_provider_name()

    def get_provider_type(self) -> ProviderType:
        """Get the provider type.

        Returns:
            Provider type
        """
        return self.provider_type
