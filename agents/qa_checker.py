"""Quality assurance agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.qa_prompts import QA_CHECKER_SYSTEM_PROMPT


class QACheckerAgent(BaseAgent):
    """Agent specialized in code quality checks and reviews."""

    def __init__(self, api_key: str | None = None):
        """Initialize the QA checker agent.

        Args:
            api_key: Optional Anthropic API key
        """
        super().__init__("qa_checker", api_key)

    def _get_system_prompt(self) -> str:
        """Get the QA checker agent system prompt.

        Returns:
            System prompt for quality assurance
        """
        return QA_CHECKER_SYSTEM_PROMPT
