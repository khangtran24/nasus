#!/usr/bin/env python3
"""
Enhanced Session Start Hook for Claude Code
Initializes memory system and loads recent context.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime


def load_recent_memories(memory_dir: Path, limit: int = 10) -> list:
    """Load recent memories for context."""
    memories = []

    try:
        # Load from various memory files
        files_to_check = [
            'conversation_memories.jsonl',
            'tool_observations.jsonl',
            'session_summaries.jsonl'
        ]

        for filename in files_to_check:
            file_path = memory_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Read last N lines
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        try:
                            memory = json.loads(line.strip())
                            memories.append(memory)
                        except json.JSONDecodeError:
                            continue

        return memories[-limit:]  # Return most recent

    except Exception as e:
        return []


def create_session_metadata(memory_dir: Path) -> dict:
    """Create metadata for the new session."""
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    metadata = {
        'session_id': session_id,
        'started_at': datetime.now().isoformat(),
        'memory_dir': str(memory_dir)
    }

    # Save session metadata
    session_file = memory_dir / f'session_{session_id}.json'
    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, 'w', encoding='utf-8') as f:
        json.dumps(metadata, f, indent=2)

    return metadata


def main():
    """Main hook entry point."""
    try:
        # Setup memory directory from environment or use default
        memory_path = os.getenv('MEMORY_STORAGE_PATH', '.claude/memory/session_conversations/')
        memory_dir = Path(os.getcwd()) / memory_path
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create session metadata
        session_metadata = create_session_metadata(memory_dir)

        # Load recent memories
        recent_memories = load_recent_memories(memory_dir, limit=10)

        # Create summary for user
        memory_count = len(recent_memories)
        memory_summary = ""

        if memory_count > 0:
            tool_uses = len([m for m in recent_memories if m.get('type') == 'tool_use'])
            decisions = len([m for m in recent_memories if m.get('type') == 'decision'])

            memory_summary = f"Loaded {memory_count} recent memories ({tool_uses} tool uses, {decisions} decisions)"
        else:
            memory_summary = "Starting fresh session - no previous memories"

        # Return success response
        print(json.dumps({
            'success': True,
            'session_id': session_metadata['session_id'],
            'memories_loaded': memory_count,
            'message': memory_summary
        }))

        return 0

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        return 1


if __name__ == '__main__':
    sys.exit(main())
