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

def normalize_path(path):
    """Normalize path to work on Windows."""
    # Convert /c/Users/... to C:/Users/...
    if path.startswith('/') and len(path) > 2 and path[2] == '/':
        path = path[1].upper() + ':' + path[2:]
    return path

def extract_memories(transcript_path):
    """Extract important information from transcript."""
    try:
        # Normalize path for Windows compatibility
        transcript_path = normalize_path(transcript_path)

        if not os.path.exists(transcript_path):
            return []

        memories = []
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())

                    # Skip non-message entries
                    if entry.get('type') != 'user' and entry.get('type') != 'assistant':
                        continue

                    message = entry.get('message', {})
                    role = message.get('role')
                    timestamp = entry.get('timestamp', datetime.now().isoformat())

                    # Extract text content from content array
                    content_array = message.get('content', [])
                    text_content = ''
                    for content_item in content_array:
                        if isinstance(content_item, dict) and content_item.get('type') == 'text':
                            text_content += content_item.get('text', '') + ' '

                    text_content = text_content.strip()
                    if not text_content:
                        continue

                    # Extract user preferences, decisions, and important facts
                    if role == 'user':
                        if any(keyword in text_content.lower() for keyword in
                               ['prefer', 'always', 'never', 'remember', 'note that', 'important']):
                            memories.append({
                                'type': 'preference',
                                'content': text_content[:500],
                                'timestamp': timestamp
                            })

                    # Extract decisions and outcomes from assistant
                    elif role == 'assistant':
                        if any(keyword in text_content.lower() for keyword in
                               ['decided', 'implemented', 'created', 'configured', 'added', 'updated', 'fixed']):
                            memories.append({
                                'type': 'decision',
                                'content': text_content[:500],  # Limit length
                                'timestamp': timestamp
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
        # Get memory path from environment or use default
        memory_path = os.getenv('MEMORY_STORAGE_PATH', '.claude/memory/session_conversations/')
        memory_dir = Path(project_root) / memory_path
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
        raw_input = sys.stdin.read()

        # Debug: Log what we received
        memory_path = os.getenv('MEMORY_STORAGE_PATH', '.claude/memory/session_conversations/')
        debug_file = Path(os.getcwd()) / memory_path / 'debug.log'
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now().isoformat()}] Received input:\n{raw_input}\n")

        input_data = json.loads(raw_input)

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
