"""Agent registration and discovery system."""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for managing and discovering agents."""

    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
        self.capabilities: Dict[str, Set[str]] = {}
        self.intent_mappings: Dict[str, List[str]] = {
            # Intent -> Agent names
            "code_generation": ["coder"],
            "code_review": ["coder", "qa_checker"],
            "test_writing": ["test_writer"],
            "test_generation": ["test_writer"],
            "requirement_analysis": ["requirement_analyzer"],
            "requirements": ["requirement_analyzer"],
            "qa_checking": ["qa_checker"],
            "quality_assurance": ["qa_checker"],
            "code_quality": ["qa_checker"],
            "documentation": ["docs_agent"],
            "docs": ["docs_agent"],
            "jira": ["requirement_analyzer"],
            "confluence": ["requirement_analyzer", "docs_agent"],
            "slack": ["docs_agent"],
            # CI/CD and DevOps intents
            "ci_cd": ["devops"],
            "cicd": ["devops"],
            "deployment": ["devops"],
            "deploy": ["devops"],
            "release": ["devops"],
            "release_management": ["devops"],
            "github_actions": ["devops"],
            "workflow": ["devops"],
            "pipeline": ["devops"],
            "docker": ["devops"],
            "dockerfile": ["devops"],
            "containerization": ["devops"],
            "infrastructure": ["devops"],
            "devops": ["devops"],
            "ship": ["devops"],
            "production": ["devops"],
        }

    def register_agent(
        self,
        agent: BaseAgent,
        capabilities: List[str]
    ) -> None:
        """Register an agent with its capabilities.

        Args:
            agent: Agent to register
            capabilities: List of capability tags
        """
        self.agents[agent.name] = agent
        self.capabilities[agent.name] = set(capabilities)
        logger.info(f"Registered agent: {agent.name} with capabilities: {capabilities}")

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None
        """
        return self.agents.get(name)

    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents.

        Returns:
            List of all agents
        """
        return list(self.agents.values())

    def get_agents_for_intent(self, intent: str) -> List[BaseAgent]:
        """Get agents capable of handling an intent.

        Args:
            intent: Intent classification

        Returns:
            List of agents that can handle this intent
        """
        # Normalize intent
        intent = intent.lower().strip()

        # Direct mapping
        if intent in self.intent_mappings:
            agent_names = self.intent_mappings[intent]
            agents = [
                self.agents[name]
                for name in agent_names
                if name in self.agents
            ]
            return agents

        # Fallback: search for partial matches
        for key, agent_names in self.intent_mappings.items():
            if key in intent or intent in key:
                agents = [
                    self.agents[name]
                    for name in agent_names
                    if name in self.agents
                ]
                if agents:
                    return agents

        # No match: return empty list
        logger.warning(f"No agents found for intent: {intent}")
        return []

    def add_intent_mapping(self, intent: str, agent_names: List[str]) -> None:
        """Add a new intent mapping.

        Args:
            intent: Intent keyword
            agent_names: List of agent names for this intent
        """
        self.intent_mappings[intent.lower()] = agent_names
        logger.info(f"Added intent mapping: {intent} -> {agent_names}")

    def get_agent_by_capability(self, capability: str) -> List[BaseAgent]:
        """Get agents with a specific capability.

        Args:
            capability: Capability tag

        Returns:
            List of agents with this capability
        """
        agents = []
        for agent_name, caps in self.capabilities.items():
            if capability in caps:
                agent = self.agents.get(agent_name)
                if agent:
                    agents.append(agent)
        return agents

    def list_agents(self) -> Dict[str, List[str]]:
        """List all agents and their capabilities.

        Returns:
            Dict mapping agent names to capability lists
        """
        return {
            name: list(caps)
            for name, caps in self.capabilities.items()
        }

    def is_registered(self, agent_name: str) -> bool:
        """Check if an agent is registered.

        Args:
            agent_name: Name to check

        Returns:
            True if registered
        """
        return agent_name in self.agents
