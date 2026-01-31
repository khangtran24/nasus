"""Code generation agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.coder_prompts import CODER_SYSTEM_PROMPT


class CoderAgent(BaseAgent):
    """Agent specialized in code generation and modification."""

    def __init__(self, api_key: str | None = None):
        """Initialize the coder agent.

        Args:
            api_key: Optional Anthropic API key
        """
        super().__init__("coder", api_key)

    def _get_system_prompt(self) -> str:
        """Get the coder agent system prompt.

        Returns:
            System prompt for code generation
        """
        return CODER_SYSTEM_PROMPT
