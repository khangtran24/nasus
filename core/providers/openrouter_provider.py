"""OpenRouter provider implementation."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import aiohttp

from core.providers.base import BaseProvider, ModelRouterResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter API (multi-model access)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter base URL (defaults to https://openrouter.ai/api/v1)
            default_model: Default model to use
            **kwargs: Additional configuration (app_name, site_url, etc.)
        """
        super().__init__(
            api_key,
            base_url or "https://openrouter.ai/api/v1",
            default_model,
            **kwargs
        )

        # Extract optional metadata
        self.app_name = kwargs.get("app_name", "Nasus Agent System")
        self.site_url = kwargs.get("site_url", "https://github.com/yourusername/nasus")

        logger.info("OpenRouter provider initialized")

    def get_provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        return "openrouter"

    async def create_message(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ModelRouterResponse:
        """Create a message using OpenRouter API.

        Args:
            messages: Conversation messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions
            **kwargs: Additional OpenRouter-specific parameters

        Returns:
            Unified response object
        """
        model = self._validate_model(model)

        # Build OpenAI-compatible messages
        openai_messages = []

        # Add system message if provided
        if system:
            openai_messages.append({
                "role": "system",
                "content": system
            })

        # Add conversation messages
        openai_messages.extend(messages)

        # Build request payload
        payload = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens
        }

        # Convert Anthropic-style tools to OpenAI format if provided
        if tools:
            payload["tools"] = self._convert_tools_to_openai(tools)

        # Add additional parameters
        payload.update(kwargs)

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name
        }

        logger.debug(f"Calling OpenRouter API with model: {model}")

        # Make HTTP request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"OpenRouter API error ({response.status}): {error_text}"
                    )
                    raise Exception(
                        f"OpenRouter API error ({response.status}): {error_text}"
                    )

                data = await response.json()

        # Convert OpenRouter response to unified format
        choice = data["choices"][0]
        message = choice["message"]

        # Convert content to Anthropic-style content blocks
        content_blocks = []

        if message.get("content"):
            content_blocks.append(
                type('TextBlock', (), {
                    'type': 'text',
                    'text': message["content"]
                })()
            )

        # Handle tool calls if present
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                content_blocks.append(
                    type('ToolUseBlock', (), {
                        'type': 'tool_use',
                        'id': tool_call["id"],
                        'name': tool_call["function"]["name"],
                        'input': json.loads(tool_call["function"]["arguments"])
                    })()
                )

        # Map OpenAI finish reasons to Anthropic-style stop reasons
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
            "content_filter": "stop_sequence",
            "function_call": "tool_use"
        }

        finish_reason = choice.get("finish_reason", "stop")
        stop_reason = stop_reason_map.get(finish_reason, finish_reason)

        # Extract usage information
        usage = data.get("usage", {})

        logger.debug(
            f"OpenRouter response: {stop_reason}, "
            f"tokens: {usage.get('prompt_tokens', 0)}/{usage.get('completion_tokens', 0)}"
        )

        return ModelRouterResponse(
            content=content_blocks,
            stop_reason=stop_reason,
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0)
            },
            model=data.get("model", model),
            id=data.get("id", "unknown"),
            role="assistant"
        )

    def _convert_tools_to_openai(
        self,
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert Anthropic-style tools to OpenAI format.

        Args:
            tools: Anthropic-style tool definitions

        Returns:
            OpenAI-style tool definitions
        """
        openai_tools = []

        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            })

        return openai_tools
