"""Main orchestrator for coordinating agents."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import List, Optional

from core.model_router import ModelRouter
from agents.coder import CoderAgent
from agents.devops_agent import DevOpsAgent
from agents.docs_agent import DocsAgent
from agents.qa_checker import QACheckerAgent
from agents.requirement_analyzer import RequirementAnalyzerAgent
from agents.test_writer import TestWriterAgent
from config import settings
from core.agent_registry import AgentRegistry
from core.context_manager import ContextManager
from core.mcp_manager import MCPManager
from core.types import AgentTask, IntentClassification
from prompts.orchestrator_prompts import INTENT_CLASSIFICATION_PROMPT

# Import Claude Agent SDK components
try:
    from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator that coordinates all agents."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the orchestrator.

        Args:
            api_key: Optional API key (provider-specific)
        """
        # Initialize ModelRouter with provider system
        provider = settings.model_provider
        api_key = api_key or self._get_api_key_for_provider(provider)

        self.client = ModelRouter(
            provider=provider,
            api_key=api_key,
            default_model=settings.default_model,
            **self._get_provider_kwargs(provider)
        )

        # Initialize managers
        self.context_manager = ContextManager(self.client)
        self.mcp_manager = MCPManager()
        self.agent_registry = AgentRegistry()

        # Register all agents
        self._register_agents()

    def _get_api_key_for_provider(self, provider: str) -> str:
        """Get API key for the specified provider.

        Args:
            provider: Provider name

        Returns:
            API key

        Raises:
            ValueError: If provider is unknown
        """
        if provider == "claude_agent_sdk":
            return settings.get_claude_api_key()
        elif provider == "openrouter":
            return settings.openrouter_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _get_provider_kwargs(self, provider: str) -> dict:
        """Get provider-specific kwargs.

        Args:
            provider: Provider name

        Returns:
            Dict of provider-specific configuration
        """
        if provider == "claude_agent_sdk":
            return {
                "use_pro_features": settings.claude_agent_sdk_use_pro_features,
                "pro_tier": settings.claude_agent_sdk_pro_tier
            }
        elif provider == "openrouter":
            return {"base_url": settings.openrouter_base_url}
        return {}

    def _register_agents(self) -> None:
        """Register all specialized agents."""
        # Create agents (they will use settings to determine API key)
        coder = CoderAgent()
        test_writer = TestWriterAgent()
        req_analyzer = RequirementAnalyzerAgent()
        qa_checker = QACheckerAgent()
        docs = DocsAgent()
        devops = DevOpsAgent()

        # Register with capabilities
        agents_config = [
            (coder, ["code_generation", "code_modification", "debugging", "refactoring"]),
            (test_writer, ["test_generation", "test_improvement", "test_coverage"]),
            (req_analyzer, ["requirement_analysis", "jira", "confluence", "specification"]),
            (qa_checker, ["code_review", "quality_check", "linting", "security"]),
            (docs, ["documentation", "slack_summary", "user_guides", "api_docs"]),
            (devops, ["ci_cd", "deployment", "release_management", "github_actions", "docker", "infrastructure"])
        ]

        for agent, capabilities in agents_config:
            self.agent_registry.register_agent(agent, capabilities)
            logger.debug(f"Registered agent: {agent.name} with {len(capabilities)} capabilities")

        logger.info(f"Initialized {len(agents_config)} specialized agents")

    async def initialize(self) -> None:
        """Initialize the orchestrator and all managers."""
        logger.debug("Initializing orchestrator...")
        await self.mcp_manager.initialize()
        logger.debug("Orchestrator ready")

    async def process_request(
        self,
        user_query: str,
        session_id: Optional[str] = None
    ) -> str:
        """Process a user request through the appropriate agent(s).

        Args:
            user_query: User's query/request
            session_id: Optional session ID (creates new if not provided)

        Returns:
            Final response string
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"Processing request for session {session_id}")

        try:
            # 1. Get current context
            context = self.context_manager.get_context(session_id)

            # 2. Classify intent
            classification = await self._classify_intent(user_query, context)
            logger.info(
                f"Intent classified as: {classification.intent} "
                f"(confidence: {classification.confidence})"
            )

            # 3. Get agents for this intent
            agents = [
                self.agent_registry.get_agent(name)
                for name in classification.agents
            ]
            agents = [a for a in agents if a]  # Filter out None

            if not agents:
                return (
                    "I'm not sure how to handle that request. "
                    "Could you please rephrase or provide more details?"
                )

            # 4. Get available tools
            tools = self.mcp_manager.get_all_tools()

            # 5. Execute agents
            responses = await self._execute_agents(
                agents,
                user_query,
                context,
                tools,
                classification.intent
            )

            # 6. Aggregate responses
            final_response = await self._aggregate_responses(responses)

            # 7. Calculate total tokens
            total_tokens = sum(r.tokens_used for r in responses)

            # 8. Update context
            self.context_manager.update_context(
                session_id,
                user_query,
                final_response,
                responses,
                total_tokens
            )

            # 9. Check if summarization needed
            if self.context_manager.should_summarize(session_id):
                logger.info("Context threshold reached, summarizing...")
                await self.context_manager.summarize_context(session_id)

            return final_response

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return f"An error occurred while processing your request: {str(e)}"

    async def _parse_sdk_response(self, client: "ClaudeSDKClient") -> str:
        """Parse response from Claude Agent SDK.

        Args:
            client: Claude SDK client instance

        Returns:
            Extracted text from response
        """
        result_text = ""
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text
        return result_text

    async def _classify_intent(
        self,
        user_query: str,
        context
    ) -> IntentClassification:
        """Classify user intent using Claude Agent SDK.

        Args:
            user_query: User's query
            context: Current session context

        Returns:
            Intent classification
        """
        # Build context for classification
        context_info = ""
        if context.conversation_summary:
            context_info = f"\n\nPrevious context: {context.conversation_summary}"

        # Call Claude for intent classification using SDK
        try:
            # Use Claude Agent SDK if available
            if CLAUDE_SDK_AVAILABLE and settings.model_provider == "claude_agent_sdk":
                async with ClaudeSDKClient() as client:
                    # Send classification request
                    await client.query(
                        f"Classify this request:\n\n{user_query}{context_info}",
                        system_prompt=INTENT_CLASSIFICATION_PROMPT,
                        max_tokens=500
                    )

                    # Parse response using separate method
                    result_text = await self._parse_sdk_response(client)
            else:
                # Fallback to ModelRouter for other providers
                response = await self.client.create_message(
                    model=settings.default_model,
                    max_tokens=500,
                    system=INTENT_CLASSIFICATION_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": f"Classify this request:\n\n{user_query}{context_info}"
                    }]
                )

                # Parse response from ModelRouter
                result_text = ""
                content_blocks = response.content
                for block in content_blocks:
                    if hasattr(block, 'text'):
                        result_text = block.text
                        break
                    elif hasattr(block, 'type') and block.type == 'text':
                        result_text = block.text if hasattr(block, 'text') else str(block)
                        break

            # Try to extract JSON from response
            try:
                # Find JSON in response
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result_text[start:end]
                    result = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    raise ValueError("No JSON found in response")

                return IntentClassification(
                    intent=result.get("intent", "unknown"),
                    confidence=result.get("confidence", 0.5),
                    agents=result.get("agents", ["coder"]),
                    reasoning=result.get("reasoning", "")
                )

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"JSON parsing failed: {e}, using fallback")
                # Fallback to simple heuristics
                return self._fallback_classification(user_query)

        except Exception as e:
            logger.warning(f"Intent classification failed: {e}, using fallback")
            return self._fallback_classification(user_query)

    def _fallback_classification(self, query: str) -> IntentClassification:
        """Fallback intent classification using simple heuristics.

        Args:
            query: User query

        Returns:
            Intent classification
        """
        query_lower = query.lower()

        # Simple keyword matching
        if any(word in query_lower for word in ["test", "pytest", "unittest"]):
            return IntentClassification(
                intent="test_writing",
                confidence=0.7,
                agents=["test_writer"],
                reasoning="Query mentions testing"
            )
        elif any(word in query_lower for word in ["jira", "ticket", "requirement", "spec"]):
            return IntentClassification(
                intent="requirement_analysis",
                confidence=0.7,
                agents=["requirement_analyzer"],
                reasoning="Query mentions requirements or Jira"
            )
        elif any(word in query_lower for word in ["lint", "quality", "review", "check"]):
            return IntentClassification(
                intent="qa_checking",
                confidence=0.7,
                agents=["qa_checker"],
                reasoning="Query mentions code quality"
            )
        elif any(word in query_lower for word in ["document", "docs", "readme", "slack"]):
            return IntentClassification(
                intent="documentation",
                confidence=0.7,
                agents=["docs_agent"],
                reasoning="Query mentions documentation"
            )
        else:
            # Default to coder
            return IntentClassification(
                intent="code_generation",
                confidence=0.6,
                agents=["coder"],
                reasoning="Default to code generation"
            )

    async def _execute_agents(
        self,
        agents,
        user_query: str,
        context,
        tools,
        intent: str
    ):
        """Execute one or more agents.

        Args:
            agents: List of agents to execute
            user_query: User's query
            context: Session context
            tools: Available tools
            intent: Classified intent

        Returns:
            List of agent responses
        """
        responses = []

        # For now, execute sequentially
        # TODO: Implement parallel execution for independent tasks
        for agent in agents:
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                user_query=user_query,
                intent=intent,
                parameters={}
            )

            logger.info(f"Executing {agent.name} agent...")
            response = await agent.execute(task, context, tools)
            responses.append(response)

            # If agent failed, stop execution
            if response.status == "failed":
                logger.error(f"Agent {agent.name} failed, stopping execution")
                break

        return responses

    async def _aggregate_responses(self, responses) -> str:
        """Aggregate responses from multiple agents.

        Args:
            responses: List of agent responses

        Returns:
            Aggregated response string
        """
        if not responses:
            return "No response generated."

        if len(responses) == 1:
            # Single agent response
            return responses[0].result or "Task completed."

        # Multiple agent responses - combine them
        parts = []
        for i, resp in enumerate(responses, 1):
            agent_name = resp.task_id.split('-')[0] if '-' in resp.task_id else f"Agent {i}"
            parts.append(f"## {agent_name.title()}\n\n{resp.result}\n")

        return "\n".join(parts)

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and cleanup resources."""
        logger.info("Shutting down orchestrator...")
        await self.mcp_manager.shutdown()
        logger.info("Orchestrator shutdown complete")
