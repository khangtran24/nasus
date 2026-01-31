#!/usr/bin/env python3
"""
Enhanced Stop Hook for Claude Code
Generates session summary and prepares for cleanup.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime


def count_observations(memory_dir: Path) -> dict:
    """Count observations by type."""
    counts = {
        'tool_uses': 0,
        'decisions': 0,
        'preferences': 0,
        'total': 0
    }

    try:
        files_to_check = [
            'conversation_memories.jsonl',
            'tool_observations.jsonl'
        ]

        for filename in files_to_check:
            file_path = memory_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            obs = json.loads(line.strip())
                            obs_type = obs.get('type', 'unknown')

                            if obs_type == 'tool_use':
                                counts['tool_uses'] += 1
                            elif obs_type == 'decision':
                                counts['decisions'] += 1
                            elif obs_type == 'preference':
                                counts['preferences'] += 1

                            counts['total'] += 1
                        except json.JSONDecodeError:
                            continue

        return counts

    except Exception as e:
        return counts


def create_session_summary(memory_dir: Path) -> dict:
    """Create a summary of the session."""
    counts = count_observations(memory_dir)

    summary = {
        'timestamp': datetime.now().isoformat(),
        'observations': counts,
        'summary_text': f"Session ended. Captured {counts['total']} observations: "
                       f"{counts['tool_uses']} tool uses, {counts['decisions']} decisions, "
                       f"{counts['preferences']} preferences."
    }

    # Save summary
    summary_file = memory_dir / 'session_summaries.jsonl'
    with open(summary_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(summary) + '\n')

    return summary


def main():
    """Main hook entry point."""
    try:
        # Get memory directory
        memory_dir = Path(os.getcwd()) / '.claude' / 'memory'

        # Create session summary
        summary = create_session_summary(memory_dir)

        # Return success response
        print(json.dumps({
            'success': True,
            'message': summary['summary_text'],
            'observations': summary['observations']
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
