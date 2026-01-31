"""Test generation agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.test_writer_prompts import TEST_WRITER_SYSTEM_PROMPT


class TestWriterAgent(BaseAgent):
    """Agent specialized in writing comprehensive tests."""

    def __init__(self, api_key: str | None = None):
        """Initialize the test writer agent.

        Args:
            api_key: Optional Anthropic API key
        """
        super().__init__("test_writer", api_key)

    def _get_system_prompt(self) -> str:
        """Get the test writer agent system prompt.

        Returns:
            System prompt for test generation
        """
        return TEST_WRITER_SYSTEM_PROMPT
