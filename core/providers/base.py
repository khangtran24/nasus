"""Base provider interface for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelRouterResponse:
    """Unified response format across all providers."""

    def __init__(
        self,
        content: List[Any],
        stop_reason: str,
        usage: Dict[str, int],
        model: str,
        id: str,
        role: str = "assistant"
    ):
        """Initialize the response.

        Args:
            content: Response content blocks
            stop_reason: Reason the model stopped
            usage: Token usage information
            model: Model that generated the response
            id: Response ID
            role: Role of the responder
        """
        self.content = content
        self.stop_reason = stop_reason
        self.usage = type('Usage', (), usage)()  # Convert dict to object
        self.model = model
        self.id = id
        self.role = role

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ModelRouterResponse(model={self.model}, "
            f"stop_reason={self.stop_reason}, "
            f"usage={self.usage})"
        )


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        **kwargs
    ):
        """Initialize the provider.

        Args:
            api_key: API key for authentication
            base_url: Optional base URL for API
            default_model: Default model to use
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.extra_config = kwargs

    @abstractmethod
    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelRouterResponse:
        """Create a message using the provider.

        Args:
            messages: Conversation messages
            model: Model to use (uses default if not specified)
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional provider-specific parameters

        Returns:
            Unified response object

        Raises:
            ValueError: If required parameters are missing
            Exception: If API call fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name (e.g., "anthropic", "openrouter")
        """
        pass

    def _validate_model(self, model: Optional[str]) -> str:
        """Validate and return the model to use.

        Args:
            model: Model specified in request

        Returns:
            Model to use

        Raises:
            ValueError: If no model is specified
        """
        result = model or self.default_model
        if not result:
            raise ValueError(
                "Model must be specified either in request or as default"
            )
        return result
