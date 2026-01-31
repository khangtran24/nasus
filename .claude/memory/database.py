"""
SQLite database for memory storage with FTS5 full-text search.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryDatabase:
    """SQLite database for storing and searching memories."""

    def __init__(self, db_path: Path):
        """
        Initialize the database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize database schema with FTS5 support."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                summary TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Observations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                tool_name TEXT,
                content TEXT NOT NULL,
                metadata TEXT,
                summary TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')

        # Create FTS5 virtual table for full-text search on observations
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
                id UNINDEXED,
                type,
                tool_name,
                content,
                summary,
                content=observations,
                content_rowid=id
            )
        ''')

        # Trigger to keep FTS5 table in sync with observations table
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
                INSERT INTO observations_fts(id, type, tool_name, content, summary)
                VALUES (new.id, new.type, new.tool_name, new.content, new.summary);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
                DELETE FROM observations_fts WHERE id = old.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS observations_au AFTER UPDATE ON observations BEGIN
                UPDATE observations_fts SET
                    type = new.type,
                    tool_name = new.tool_name,
                    content = new.content,
                    summary = new.summary
                WHERE id = new.id;
            END
        ''')

        # Memories table (for user preferences, decisions, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # FTS5 for memories
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                type,
                content,
                content=memories,
                content_rowid=id
            )
        ''')

        # Triggers for memories FTS
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(id, type, content)
                VALUES (new.id, new.type, new.content);
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE id = old.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                UPDATE memories_fts SET type = new.type, content = new.content
                WHERE id = new.id;
            END
        ''')

        # Create indices for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_observations_session ON observations(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_observations_type ON observations(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_observations_timestamp ON observations(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)')

        self.conn.commit()

    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata

        Returns:
            Session row ID
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (session_id, start_time, metadata)
            VALUES (?, ?, ?)
        ''', (session_id, datetime.now().isoformat(), json.dumps(metadata or {})))

        self.conn.commit()
        row_id = cursor.lastrowid

        logger.info(
            f"Created session in database: session_id={session_id}, "
            f"row_id={row_id}, has_metadata={metadata is not None}"
        )

        return row_id

    def end_session(self, session_id: str, summary: Optional[str] = None):
        """
        Mark a session as ended.

        Args:
            session_id: Session identifier
            summary: Optional session summary
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions
            SET end_time = ?, summary = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), summary, session_id))

        self.conn.commit()

    def add_observation(
        self,
        session_id: str,
        obs_type: str,
        content: str,
        tool_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> int:
        """
        Add an observation to the database.

        Args:
            session_id: Session identifier
            obs_type: Observation type (tool_use, user_input, decision, etc.)
            content: Observation content
            tool_name: Tool name if applicable
            metadata: Optional metadata
            summary: Optional AI-generated summary
            timestamp: ISO format timestamp (defaults to now)

        Returns:
            Observation row ID
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO observations (session_id, timestamp, type, tool_name, content, metadata, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            timestamp or datetime.now().isoformat(),
            obs_type,
            tool_name,
            content,
            json.dumps(metadata or {}),
            summary
        ))

        self.conn.commit()
        return cursor.lastrowid

    def add_memory(
        self,
        mem_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> int:
        """
        Add a memory (preference, decision, etc.).

        Args:
            mem_type: Memory type
            content: Memory content
            metadata: Optional metadata
            timestamp: ISO format timestamp (defaults to now)

        Returns:
            Memory row ID
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO memories (type, content, metadata, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            mem_type,
            content,
            json.dumps(metadata or {}),
            timestamp or datetime.now().isoformat()
        ))

        self.conn.commit()
        return cursor.lastrowid

    def search_observations(
        self,
        query: str,
        limit: int = 10,
        obs_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Full-text search observations using FTS5.

        Args:
            query: Search query
            limit: Maximum results
            obs_type: Optional filter by observation type

        Returns:
            List of matching observations
        """
        cursor = self.conn.cursor()

        if obs_type:
            cursor.execute('''
                SELECT o.* FROM observations o
                INNER JOIN observations_fts fts ON o.id = fts.id
                WHERE observations_fts MATCH ? AND o.type = ?
                ORDER BY rank
                LIMIT ?
            ''', (query, obs_type, limit))
        else:
            cursor.execute('''
                SELECT o.* FROM observations o
                INNER JOIN observations_fts fts ON o.id = fts.id
                WHERE observations_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (query, limit))

        return [dict(row) for row in cursor.fetchall()]

    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search memories using FTS5.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.* FROM memories m
            INNER JOIN memories_fts fts ON m.id = fts.id
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_observations(
        self,
        limit: int = 20,
        obs_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent observations.

        Args:
            limit: Maximum results
            obs_type: Optional filter by type

        Returns:
            List of recent observations
        """
        cursor = self.conn.cursor()

        if obs_type:
            cursor.execute('''
                SELECT * FROM observations
                WHERE type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (obs_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM observations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_session_observations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all observations for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of observations
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM observations
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))

        return [dict(row) for row in cursor.fetchall()]

    def update_observation_summary(self, obs_id: int, summary: str):
        """
        Update an observation's AI-generated summary.

        Args:
            obs_id: Observation ID
            summary: Summary text
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE observations
            SET summary = ?
            WHERE id = ?
        ''', (summary, obs_id))

        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics dict
        """
        cursor = self.conn.cursor()

        stats = {}

        # Count sessions
        cursor.execute('SELECT COUNT(*) FROM sessions')
        stats['total_sessions'] = cursor.fetchone()[0]

        # Count observations
        cursor.execute('SELECT COUNT(*) FROM observations')
        stats['total_observations'] = cursor.fetchone()[0]

        # Count by type
        cursor.execute('SELECT type, COUNT(*) FROM observations GROUP BY type')
        stats['observations_by_type'] = dict(cursor.fetchall())

        # Count memories
        cursor.execute('SELECT COUNT(*) FROM memories')
        stats['total_memories'] = cursor.fetchone()[0]

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
