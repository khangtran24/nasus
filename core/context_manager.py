"""Context management and summarization for conversation sessions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from anthropic import Anthropic

from config import settings
from core.types import AgentResponse, ContextSummary, ConversationTurn


class ContextManager:
    """Manages conversation context with intelligent summarization."""

    def __init__(self, client: Optional[Anthropic] = None):
        """Initialize the context manager.

        Args:
            client: Optional Anthropic client (creates new one if not provided)
        """
        self.client = client or Anthropic(api_key=settings.anthropic_api_key)
        self.sessions: Dict[str, ContextSummary] = {}
        self.max_tokens = settings.max_context_tokens
        self.summarization_threshold = int(
            settings.max_context_tokens * settings.summarization_threshold
        )

    def get_context(self, session_id: str) -> ContextSummary:
        """Retrieve or create context for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Context summary for the session
        """
        if session_id not in self.sessions:
            # Try to load from disk
            context = self._load_from_disk(session_id)
            if context:
                self.sessions[session_id] = context
            else:
                # Create new context
                self.sessions[session_id] = ContextSummary(
                    session_id=session_id
                )

        return self.sessions[session_id]

    def update_context(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
        agent_responses: List[AgentResponse],
        tokens_used: int = 0
    ) -> None:
        """Update context with a new conversation turn.

        Args:
            session_id: Session identifier
            user_query: User's query
            assistant_response: Assistant's response
            agent_responses: Responses from agents
            tokens_used: Tokens consumed in this turn
        """
        context = self.get_context(session_id)

        # Create conversation turn
        turn = ConversationTurn(
            user=user_query,
            assistant=assistant_response,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used
        )

        # Add to recent turns
        context.recent_turns.append(turn)

        # Keep only the N most recent turns
        if len(context.recent_turns) > settings.recent_turns_to_keep:
            context.recent_turns = context.recent_turns[-settings.recent_turns_to_keep:]

        # Update active files from agent responses
        for agent_resp in agent_responses:
            for tool_call in agent_resp.tool_calls:
                if tool_call.get("type") == "file_operation":
                    filename = tool_call.get("filename")
                    if filename:
                        context.active_files[filename] = tool_call.get(
                            "summary",
                            f"Modified by {agent_resp.task_id}"
                        )

        # Update task history
        for agent_resp in agent_responses:
            context.task_history.extend(agent_resp.actions_taken)

        # Update token usage
        context.total_tokens_used += tokens_used
        context.updated_at = datetime.now().isoformat()

        # Save to disk
        self._save_to_disk(context)

    def should_summarize(self, session_id: str) -> bool:
        """Check if context should be summarized.

        Args:
            session_id: Session identifier

        Returns:
            True if context exceeds threshold
        """
        context = self.get_context(session_id)
        current_tokens = self._estimate_context_tokens(context)
        return current_tokens > self.summarization_threshold

    async def summarize_context(self, session_id: str) -> None:
        """Summarize context using Claude.

        Args:
            session_id: Session identifier
        """
        context = self.get_context(session_id)

        # Build full context for summarization
        full_context = self._build_full_context(context)

        # Call Claude for summarization
        try:
            response = await self.client.messages.create(
                model=settings.default_model,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"""Summarize this conversation, preserving:
- Key technical decisions and specifications
- Files that have been created or modified
- Tasks that have been completed
- Current work-in-progress items
- Any errors or issues encountered

Be concise but retain all important technical details.

Previous summary:
{context.conversation_summary or "None"}

Recent conversation:
{full_context}

Provide a comprehensive summary that incorporates both the previous summary and new information."""
                }]
            )

            # Extract summary text
            summary_text = response.content[0].text

            # Update context with new summary
            context.conversation_summary = summary_text

            # Keep only the last turn in full detail
            if context.recent_turns:
                context.recent_turns = [context.recent_turns[-1]]

            # Save updated context
            self._save_to_disk(context)

        except Exception as e:
            # Log error but don't fail - continue with unsummarized context
            print(f"Warning: Failed to summarize context: {e}")

    def _estimate_context_tokens(self, context: ContextSummary) -> int:
        """Estimate token count for context.

        Args:
            context: Context to estimate

        Returns:
            Estimated token count (rough approximation)
        """
        # Rough estimation: 1 token ≈ 4 characters
        full_context = self._build_full_context(context)
        return len(full_context) // 4

    def _build_full_context(self, context: ContextSummary) -> str:
        """Build full context string for summarization.

        Args:
            context: Context to build from

        Returns:
            Full context as string
        """
        parts = []

        # Add recent turns
        for turn in context.recent_turns:
            parts.append(f"User: {turn.user}")
            parts.append(f"Assistant: {turn.assistant}")
            parts.append("")

        # Add active files
        if context.active_files:
            parts.append("Active Files:")
            for filename, summary in context.active_files.items():
                parts.append(f"  - {filename}: {summary}")
            parts.append("")

        # Add recent task history
        if context.task_history:
            recent_tasks = context.task_history[-10:]  # Last 10 tasks
            parts.append("Recent Actions:")
            for task in recent_tasks:
                parts.append(f"  - {task}")
            parts.append("")

        return "\n".join(parts)

    def _save_to_disk(self, context: ContextSummary) -> None:
        """Save context to disk.

        Args:
            context: Context to save
        """
        try:
            session_path = Path(settings.session_storage_path)
            session_path.mkdir(parents=True, exist_ok=True)

            file_path = session_path / f"{context.session_id}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                # Convert to dict
                context_dict = {
                    "session_id": context.session_id,
                    "conversation_summary": context.conversation_summary,
                    "recent_turns": [
                        {
                            "user": turn.user,
                            "assistant": turn.assistant,
                            "timestamp": turn.timestamp,
                            "tokens_used": turn.tokens_used
                        }
                        for turn in context.recent_turns
                    ],
                    "active_files": context.active_files,
                    "task_history": context.task_history,
                    "total_tokens_used": context.total_tokens_used,
                    "created_at": context.created_at,
                    "updated_at": context.updated_at
                }
                json.dump(context_dict, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save context to disk: {e}")

    def _load_from_disk(self, session_id: str) -> Optional[ContextSummary]:
        """Load context from disk.

        Args:
            session_id: Session identifier

        Returns:
            Loaded context or None if not found
        """
        try:
            file_path = Path(settings.session_storage_path) / f"{session_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct context
            context = ContextSummary(
                session_id=data["session_id"],
                conversation_summary=data.get("conversation_summary", ""),
                recent_turns=[
                    ConversationTurn(
                        user=turn["user"],
                        assistant=turn["assistant"],
                        timestamp=turn["timestamp"],
                        tokens_used=turn.get("tokens_used", 0)
                    )
                    for turn in data.get("recent_turns", [])
                ],
                active_files=data.get("active_files", {}),
                task_history=data.get("task_history", []),
                total_tokens_used=data.get("total_tokens_used", 0),
                created_at=data.get("created_at", datetime.now().isoformat()),
                updated_at=data.get("updated_at", datetime.now().isoformat())
            )

            return context

        except Exception as e:
            print(f"Warning: Failed to load context from disk: {e}")
            return None

    def clear_session(self, session_id: str) -> None:
        """Clear a session from memory and disk.

        Args:
            session_id: Session to clear
        """
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]

        # Remove from disk
        try:
            file_path = Path(settings.session_storage_path) / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete session file: {e}")
