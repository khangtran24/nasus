#!/usr/bin/env python3
"""
Memory Capture Hook for Claude Code
Captures important information from conversations for long-term memory.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

def extract_memories(transcript_path):
    """Extract important information from transcript."""
    try:
        if not os.path.exists(transcript_path):
            return []

        memories = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Extract user preferences, decisions, and important facts
                    if entry.get('role') == 'user':
                        content = entry.get('content', '')
                        if any(keyword in content.lower() for keyword in
                               ['prefer', 'always', 'never', 'remember', 'note that']):
                            memories.append({
                                'type': 'preference',
                                'content': content,
                                'timestamp': entry.get('timestamp', datetime.now().isoformat())
                            })

                    # Extract decisions and outcomes from assistant
                    elif entry.get('role') == 'assistant':
                        content = entry.get('content', '')
                        if any(keyword in content.lower() for keyword in
                               ['decided', 'implemented', 'created', 'configured']):
                            memories.append({
                                'type': 'decision',
                                'content': content[:500],  # Limit length
                                'timestamp': entry.get('timestamp', datetime.now().isoformat())
                            })

                except json.JSONDecodeError:
                    continue

        return memories

    except Exception as e:
        print(f"Error extracting memories: {e}", file=sys.stderr)
        return []

def store_memories(memories, project_root):
    """Store memories in the project's memory file."""
    try:
        memory_dir = Path(project_root) / '.claude' / 'memory'
        memory_dir.mkdir(parents=True, exist_ok=True)

        memory_file = memory_dir / 'conversation_memories.jsonl'

        with open(memory_file, 'a', encoding='utf-8') as f:
            for memory in memories:
                f.write(json.dumps(memory) + '\n')

        return len(memories)

    except Exception as e:
        print(f"Error storing memories: {e}", file=sys.stderr)
        return 0

def main():
    """Main hook entry point."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        transcript_path = input_data.get('transcript_path')
        if not transcript_path:
            print(json.dumps({
                'success': False,
                'error': 'No transcript_path provided'
            }))
            return 1

        # Get project root (parent of .claude directory)
        project_root = os.getcwd()

        # Extract memories from transcript
        memories = extract_memories(transcript_path)

        # Store memories
        count = store_memories(memories, project_root)

        # Return success response
        print(json.dumps({
            'success': True,
            'memories_captured': count,
            'message': f'Captured {count} memories from conversation'
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
