"""Requirement analysis agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.requirement_prompts import REQUIREMENT_ANALYZER_SYSTEM_PROMPT


class RequirementAnalyzerAgent(BaseAgent):
    """Agent specialized in analyzing requirements and specifications."""

    def __init__(self, api_key: str | None = None):
        """Initialize the requirement analyzer agent.

        Args:
            api_key: Optional Anthropic API key
        """
        super().__init__("requirement_analyzer", api_key)

    def _get_system_prompt(self) -> str:
        """Get the requirement analyzer agent system prompt.

        Returns:
            System prompt for requirement analysis
        """
        return REQUIREMENT_ANALYZER_SYSTEM_PROMPT
