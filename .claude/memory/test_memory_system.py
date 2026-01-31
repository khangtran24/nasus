#!/usr/bin/env python3
"""
Comprehensive test for the memory system.
Tests all phases: hooks, database, vector search, and AI summarization.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from memory_manager import MemoryManager
from database import MemoryDatabase
from vector_store import VectorStore
from summarizer import MemorySummarizer


def test_database():
    """Test SQLite database with FTS5."""
    print("\n=== Testing SQLite Database ===")

    memory_dir = Path(__file__).parent
    db_path = memory_dir / "test_memories.db"

    # Clean up old test database
    if db_path.exists():
        db_path.unlink()

    db = MemoryDatabase(db_path)

    # Create session
    session_id = "test_20260131_120000"
    db.create_session(session_id, {"test": True})
    print(f"[OK] Created session: {session_id}")

    # Add observations
    obs1 = db.add_observation(
        session_id=session_id,
        obs_type="tool_use",
        content="User executed Read tool to view database.py file",
        tool_name="Read",
        metadata={"file": "database.py"}
    )
    print(f"[OK] Added observation {obs1}")

    obs2 = db.add_observation(
        session_id=session_id,
        obs_type="decision",
        content="Decided to implement SQLite with FTS5 for full-text search",
        metadata={"component": "storage"}
    )
    print(f"[OK] Added observation {obs2}")

    # Full-text search
    results = db.search_observations("SQLite FTS5", limit=5)
    print(f"[OK] FTS5 search returned {len(results)} results")

    if results:
        print(f"     First result: {results[0]['content'][:80]}...")

    # Get recent observations
    recent = db.get_recent_observations(limit=10)
    print(f"[OK] Retrieved {len(recent)} recent observations")

    # Get stats
    stats = db.get_stats()
    print(f"[OK] Database stats: {stats}")

    db.close()
    return True


def test_vector_store():
    """Test vector storage and semantic search."""
    print("\n=== Testing Vector Store ===")

    memory_dir = Path(__file__).parent / "test_vectors"

    try:
        vector_store = VectorStore(memory_dir)

        # Add documents
        vector_store.add(
            text="Implemented SQLite database with FTS5 full-text search",
            doc_id="1",
            doc_type="tool_use",
            metadata={"tool": "Write"}
        )

        vector_store.add(
            text="Created vector embeddings using sentence-transformers",
            doc_id="2",
            doc_type="tool_use",
            metadata={"tool": "Write"}
        )

        vector_store.add(
            text="Added AI-powered summarization with ModelRouter",
            doc_id="3",
            doc_type="decision",
            metadata={}
        )

        print("[OK] Added 3 documents to vector store")

        # Semantic search
        results = vector_store.search("database implementation", limit=3)
        print(f"[OK] Semantic search returned {len(results)} results")

        if results:
            for i, result in enumerate(results):
                print(f"     {i+1}. (score: {result['similarity']:.3f}) {result['text'][:60]}...")

        # Stats
        stats = vector_store.get_stats()
        print(f"[OK] Vector store stats: {stats}")

        return True

    except ImportError as e:
        print(f"[SKIP] Vector store test skipped (dependency missing): {e}")
        print("       Install with: pip install sentence-transformers")
        return False


async def test_summarizer():
    """Test AI summarization."""
    print("\n=== Testing AI Summarization ===")

    try:
        summarizer = MemorySummarizer()

        # Test observation summarization
        observation = {
            'type': 'tool_use',
            'tool_name': 'Read',
            'content': 'Read the database.py file which contains the MemoryDatabase class with methods for creating sessions, adding observations, and performing full-text search using SQLite FTS5.'
        }

        summary = await summarizer.summarize_observation(observation)
        print(f"[OK] Observation summary: {summary}")

        # Test session summarization
        observations = [
            {'type': 'tool_use', 'content': 'Created database schema with SQLite'},
            {'type': 'tool_use', 'content': 'Implemented vector search with sentence-transformers'},
            {'type': 'decision', 'content': 'Decided to use hybrid search combining keyword and semantic'},
        ]

        session_summary = await summarizer.summarize_session(observations)
        print(f"[OK] Session summary: {session_summary}")

        return True

    except Exception as e:
        print(f"[SKIP] Summarization test skipped: {e}")
        print(f"       Check ModelRouter configuration in .env")
        return False


def test_integrated_manager():
    """Test integrated MemoryManager."""
    print("\n=== Testing Integrated Memory Manager ===")

    memory_dir = Path(__file__).parent / "test_integrated"
    manager = MemoryManager(memory_dir)

    # Start session
    session_id = manager.start_session({"test": "integrated"})
    print(f"[OK] Started session: {session_id}")

    # Add observations
    obs1 = manager.add_observation(
        obs_type="tool_use",
        content="Testing integrated memory manager with all components",
        tool_name="Test",
        auto_summarize=False,  # Skip AI for faster testing
        add_to_vector_store=True
    )
    print(f"[OK] Added observation {obs1}")

    obs2 = manager.add_observation(
        obs_type="decision",
        content="Memory system successfully integrates SQLite, vectors, and AI",
        auto_summarize=False,
        add_to_vector_store=True
    )
    print(f"[OK] Added observation {obs2}")

    # Search
    results = manager.search("memory manager", limit=5, search_type="keyword")
    print(f"[OK] Keyword search returned {len(results)} results")

    # Get recent
    recent = manager.get_recent(limit=10)
    print(f"[OK] Retrieved {len(recent)} recent observations")

    # Get stats
    stats = manager.get_stats()
    print(f"[OK] System stats: {stats}")

    # End session
    manager.end_session("Test session completed successfully")
    print(f"[OK] Session ended")

    manager.close()
    return True


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("  Memory System Comprehensive Test Suite")
    print("=" * 60)

    results = {
        'database': False,
        'vector_store': False,
        'summarizer': False,
        'integrated': False
    }

    try:
        results['database'] = test_database()
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")

    try:
        results['vector_store'] = test_vector_store()
    except Exception as e:
        print(f"[ERROR] Vector store test failed: {e}")

    try:
        results['summarizer'] = await test_summarizer()
    except Exception as e:
        print(f"[ERROR] Summarizer test failed: {e}")

    try:
        results['integrated'] = test_integrated_manager()
    except Exception as e:
        print(f"[ERROR] Integrated manager test failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  Test Results Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL/SKIP]"
        print(f"{status} {test_name}")

    print(f"\n{passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
