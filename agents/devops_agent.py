"""DevOps agent for CI/CD, deployment, and release management."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.devops_prompts import DEVOPS_SYSTEM_PROMPT


class DevOpsAgent(BaseAgent):
    """Agent specialized in DevOps, CI/CD, and deployment operations.

    Capabilities:
    - Create and manage GitHub Actions workflows
    - Trigger CI/CD pipelines
    - Monitor workflow runs and logs
    - Create releases and tags
    - Manage deployments to different environments
    - Configure secrets and environment variables
    - Implement Docker containerization
    - Set up infrastructure as code
    """

    def __init__(self, api_key: str | None = None):
        """Initialize the DevOps agent.

        Args:
            api_key: Optional API key for LLM provider
        """
        super().__init__(name="devops", api_key=api_key)

    def _get_system_prompt(self) -> str:
        """Get the DevOps agent system prompt.

        Returns:
            System prompt for DevOps operations
        """
        return DEVOPS_SYSTEM_PROMPT
