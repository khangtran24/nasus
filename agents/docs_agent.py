"""Documentation agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.docs_prompts import DOCS_AGENT_SYSTEM_PROMPT


class DocsAgent(BaseAgent):
    """Agent specialized in creating and maintaining documentation."""

    def __init__(self, api_key: str | None = None):
        """Initialize the documentation agent.

        Args:
            api_key: Optional Anthropic API key
        """
        super().__init__("docs_agent", api_key)

    def _get_system_prompt(self) -> str:
        """Get the documentation agent system prompt.

        Returns:
            System prompt for documentation creation
        """
        return DOCS_AGENT_SYSTEM_PROMPT
