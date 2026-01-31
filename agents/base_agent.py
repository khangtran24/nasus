"""Base agent implementation that all specialized agents inherit from."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from anthropic.types import ToolUseBlock

from config import settings
from core.model_router import ModelRouter, ModelRouterResponse
from core.types import AgentResponse, AgentTask, ContextSummary, MCPTool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents.

    All specialized agents must inherit from this class and implement
    the _get_system_prompt() method.
    """

    def __init__(self, name: str, api_key: Optional[str] = None):
        """Initialize the base agent.

        Args:
            name: Agent name
            api_key: Optional API key (uses settings if not provided based on provider)
        """
        self.name = name

        # Determine which provider to use and get appropriate API key
        provider = settings.model_provider
        if not api_key:
            if provider == "anthropic":
                api_key = settings.get_claude_api_key()
            elif provider == "openrouter":
                api_key = settings.openrouter_api_key
            elif provider == "claude_agent_sdk":
                api_key = settings.get_claude_api_key()  # Uses Claude/Anthropic key

        # Prepare provider-specific kwargs
        provider_kwargs = {}

        if provider == "openrouter":
            provider_kwargs["base_url"] = settings.openrouter_base_url
        elif provider == "claude_agent_sdk":
            provider_kwargs["use_pro_features"] = settings.claude_agent_sdk_use_pro_features
            if settings.claude_agent_sdk_pro_tier:
                provider_kwargs["pro_tier"] = settings.claude_agent_sdk_pro_tier

        # Initialize ModelRouter
        self.client = ModelRouter(
            provider=provider,
            api_key=api_key,
            default_model=settings.default_model,
            **provider_kwargs
        )

        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the agent-specific system prompt.

        Returns:
            System prompt for this agent
        """
        pass

    async def execute(
        self,
        task: AgentTask,
        context: ContextSummary,
        tools: List[MCPTool]
    ) -> AgentResponse:
        """Execute an agent task with context and tools.

        Args:
            task: Task to execute
            context: Current session context
            tools: Available MCP tools

        Returns:
            Agent response with results
        """
        logger.info(f"[{self.name}] Executing task: {task.task_id}")

        try:
            # Build messages from task and context
            messages = self._build_messages(task, context)

            # Format tools for Claude
            formatted_tools = self._format_tools(tools)

            # Call Claude
            response = await self._call_claude(
                messages=messages,
                tools=formatted_tools if formatted_tools else None
            )

            # Handle tool calls if any
            tool_calls = []
            actions_taken = []

            if response.stop_reason == "tool_use":
                tool_calls, actions_taken = await self._handle_tool_calls(
                    response,
                    messages,
                    formatted_tools
                )

            # Extract result text
            result = self._extract_result(response)

            # Calculate tokens used
            tokens_used = (
                response.usage.input_tokens +
                response.usage.output_tokens
            )

            return AgentResponse(
                task_id=task.task_id,
                status="success",
                result=result,
                actions_taken=actions_taken,
                tokens_used=tokens_used,
                tool_calls=tool_calls
            )

        except Exception as e:
            logger.error(f"[{self.name}] Error executing task: {e}")
            return AgentResponse(
                task_id=task.task_id,
                status="failed",
                result=None,
                actions_taken=[],
                tokens_used=0,
                tool_calls=[],
                errors=[str(e)]
            )

    async def _call_claude(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096
    ) -> ModelRouterResponse:
        """Call LLM API via ModelRouter.

        Args:
            messages: Conversation messages
            tools: Optional tools definition
            max_tokens: Maximum tokens to generate

        Returns:
            Model response
        """
        response = await self.client.create_message(
            messages=messages,
            system=self.system_prompt,
            max_tokens=max_tokens,
            tools=tools
        )
        return response

    def _build_messages(
        self,
        task: AgentTask,
        context: ContextSummary
    ) -> List[Dict[str, Any]]:
        """Build conversation messages from task and context.

        Args:
            task: Current task
            context: Session context

        Returns:
            List of messages for Claude
        """
        messages = []

        # Add context summary if available
        if context.conversation_summary:
            messages.append({
                "role": "user",
                "content": f"Previous conversation summary:\n{context.conversation_summary}\n\n"
            })
            messages.append({
                "role": "assistant",
                "content": "I understand the previous context."
            })

        # Add recent turns if available
        for turn in context.recent_turns[-2:]:  # Last 2 turns
            messages.append({
                "role": "user",
                "content": turn.user
            })
            messages.append({
                "role": "assistant",
                "content": turn.assistant
            })

        # Add current task
        task_content = task.user_query

        # Add active files context if relevant
        if context.active_files:
            files_info = "\n".join([
                f"  - {filename}: {summary}"
                for filename, summary in context.active_files.items()
            ])
            task_content += f"\n\nActive files:\n{files_info}"

        messages.append({
            "role": "user",
            "content": task_content
        })

        return messages

    def _format_tools(self, tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """Format MCP tools for Claude API.

        Args:
            tools: List of MCP tools

        Returns:
            Formatted tools for Claude
        """
        if not tools:
            return []

        formatted = []
        for tool in tools:
            formatted.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })

        return formatted

    async def _handle_tool_calls(
        self,
        response: ModelRouterResponse,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Handle tool calls from model response.

        Args:
            response: Model response with tool uses
            messages: Current conversation messages
            tools: Available tools

        Returns:
            Tuple of (tool_calls, actions_taken)
        """
        tool_calls = []
        actions_taken = []

        # Extract tool use blocks
        tool_blocks = [
            block for block in response.content
            if isinstance(block, ToolUseBlock)
        ]

        for tool_block in tool_blocks:
            # Record tool call
            tool_call = {
                "type": "tool_use",
                "tool": tool_block.name,
                "input": tool_block.input,
                "tool_use_id": tool_block.id
            }
            tool_calls.append(tool_call)
            actions_taken.append(f"Used tool: {tool_block.name}")

            logger.info(f"[{self.name}] Tool call: {tool_block.name}")

        return tool_calls, actions_taken

    def _extract_result(self, response: ModelRouterResponse) -> str:
        """Extract text result from model response.

        Args:
            response: Model response

        Returns:
            Extracted text
        """
        text_parts = []

        for block in response.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)

        return "\n".join(text_parts) if text_parts else ""

    def _count_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to count

        Returns:
            Estimated token count (rough approximation)
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
