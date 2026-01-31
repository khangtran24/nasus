"""
Integrated Memory Manager combining SQLite, Vector Search, and AI Summarization.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from database import MemoryDatabase
from vector_store import VectorStore, HybridSearch
from summarizer import MemorySummarizer


class MemoryManager:
    """
    Unified interface for memory management.
    Combines SQLite storage, vector search, and AI summarization.
    """

    def __init__(self, memory_dir: Path):
        """
        Initialize the memory manager.

        Args:
            memory_dir: Directory for memory storage
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.db = MemoryDatabase(self.memory_dir / "memories.db")
        self.vector_store = VectorStore(self.memory_dir / "vectors")
        self.hybrid_search = HybridSearch(self.db, self.vector_store)
        self.summarizer = MemorySummarizer()

        self.current_session_id = None

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new memory session.

        Args:
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.db.create_session(session_id, metadata)
        self.current_session_id = session_id
        return session_id

    def end_session(self, summary: Optional[str] = None):
        """
        End the current session.

        Args:
            summary: Optional session summary
        """
        if self.current_session_id:
            self.db.end_session(self.current_session_id, summary)

    def add_observation(
        self,
        obs_type: str,
        content: str,
        tool_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_summarize: bool = False,
        add_to_vector_store: bool = True
    ) -> int:
        """
        Add an observation to memory.

        Args:
            obs_type: Observation type (tool_use, decision, etc.)
            content: Observation content
            tool_name: Tool name if applicable
            metadata: Optional metadata
            auto_summarize: Whether to generate AI summary
            add_to_vector_store: Whether to add to vector search

        Returns:
            Observation ID
        """
        session_id = self.current_session_id or "default"

        # Generate summary if requested
        summary = None
        if auto_summarize:
            try:
                summary = asyncio.run(
                    self.summarizer.summarize_observation({
                        'type': obs_type,
                        'content': content,
                        'tool_name': tool_name
                    })
                )
            except Exception:
                summary = None

        # Add to database
        obs_id = self.db.add_observation(
            session_id=session_id,
            obs_type=obs_type,
            content=content,
            tool_name=tool_name,
            metadata=metadata,
            summary=summary
        )

        # Add to vector store
        if add_to_vector_store:
            try:
                text = f"{obs_type}: {content}"
                if summary:
                    text = f"{summary} | {text}"

                self.vector_store.add(
                    text=text,
                    doc_id=str(obs_id),
                    doc_type=obs_type,
                    metadata=metadata
                )
            except Exception:
                pass  # Vector store is optional

        return obs_id

    def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Search memories.

        Args:
            query: Search query
            limit: Maximum results
            search_type: Search type ("keyword", "semantic", or "hybrid")

        Returns:
            List of matching results
        """
        if search_type == "keyword":
            return self.db.search_observations(query, limit)
        elif search_type == "semantic":
            return self.vector_store.search(query, limit)
        elif search_type == "hybrid":
            return self.hybrid_search.search(query, limit)
        else:
            raise ValueError(f"Unknown search type: {search_type}")

    def get_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent observations.

        Args:
            limit: Maximum results

        Returns:
            List of recent observations
        """
        return self.db.get_recent_observations(limit)

    def get_session_summary(
        self,
        session_id: Optional[str] = None
    ) -> str:
        """
        Get AI-generated summary for a session.

        Args:
            session_id: Session ID (uses current if not specified)

        Returns:
            Session summary
        """
        sid = session_id or self.current_session_id
        if not sid:
            return "No active session"

        observations = self.db.get_session_observations(sid)

        if not observations:
            return "No observations in session"

        try:
            summary = asyncio.run(
                self.summarizer.summarize_session(observations)
            )
            return summary
        except Exception as e:
            return f"Unable to generate summary: {str(e)[:100]}"

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics.

        Returns:
            Statistics dict
        """
        db_stats = self.db.get_stats()
        vector_stats = self.vector_store.get_stats()

        return {
            **db_stats,
            'vector_store': vector_stats,
            'current_session': self.current_session_id
        }

    def close(self):
        """Close all connections."""
        self.db.close()
