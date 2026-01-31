"""Type definitions and protocols for the multi-agent system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class AgentTask:
    """Task to be executed by an agent.

    Attributes:
        task_id: Unique identifier for the task
        user_query: Original user query/request
        intent: Classified intent (e.g., "code_generation", "test_writing")
        parameters: Additional task-specific parameters
        priority: Task priority (higher number = higher priority)
    """
    task_id: str
    user_query: str
    intent: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0


@dataclass
class AgentResponse:
    """Response from an agent after task execution.

    Attributes:
        task_id: ID of the completed task
        status: Execution status ("success", "partial", "failed")
        result: Main result/output from the agent
        actions_taken: List of actions performed during execution
        tokens_used: Total tokens consumed (input + output)
        tool_calls: List of tool calls made during execution
        errors: Optional list of error messages
        metadata: Additional response metadata
    """
    task_id: str
    status: str
    result: Any
    actions_taken: List[str]
    tokens_used: int
    tool_calls: List[Dict[str, Any]]
    errors: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """A single turn in the conversation.

    Attributes:
        user: User's message
        assistant: Assistant's response
        timestamp: When this turn occurred
        tokens_used: Tokens consumed in this turn
    """
    user: str
    assistant: str
    timestamp: str
    tokens_used: int = 0


@dataclass
class ContextSummary:
    """Summarized context for a conversation session.

    Attributes:
        session_id: Unique session identifier
        conversation_summary: High-level summary of the conversation
        recent_turns: Last N conversation turns (full detail)
        active_files: Currently relevant files (filename -> summary)
        task_history: List of completed tasks/actions
        total_tokens_used: Cumulative token usage for the session
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    """
    session_id: str
    conversation_summary: str = ""
    recent_turns: List[ConversationTurn] = field(default_factory=list)
    active_files: Dict[str, str] = field(default_factory=dict)
    task_history: List[str] = field(default_factory=list)
    total_tokens_used: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPTool:
    """Definition of an MCP tool.

    Attributes:
        name: Tool name
        description: What the tool does
        input_schema: JSON schema for tool input
        server: MCP server providing this tool
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str


@dataclass
class IntentClassification:
    """Result of intent classification.

    Attributes:
        intent: Primary intent category
        confidence: Confidence score (0.0-1.0)
        agents: List of agent names to handle this intent
        reasoning: Explanation of classification
    """
    intent: str
    confidence: float
    agents: List[str]
    reasoning: str = ""


class AgentProtocol(Protocol):
    """Protocol defining the interface all agents must implement."""

    name: str

    async def execute(
        self,
        task: AgentTask,
        context: ContextSummary,
        tools: List[MCPTool]
    ) -> AgentResponse:
        """Execute an agent task with context and available tools.

        Args:
            task: Task to execute
            context: Current session context
            tools: Available MCP tools

        Returns:
            Response containing results and metadata
        """
        ...


class ToolProtocol(Protocol):
    """Protocol for tool implementations."""

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result
        """
        ...
