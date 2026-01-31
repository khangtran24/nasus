#!/usr/bin/env python3
"""
Enhanced Post Tool Use Hook for Claude Code
Captures detailed tool execution observations.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Add project root and memory utils to path
project_root = Path(os.getcwd())
memory_path = project_root / '.claude' / 'memory'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(memory_path))

try:
    from memory_utils import (
        extract_tool_observation,
        create_observation,
        save_observation_to_jsonl
    )
except ImportError:
    # Fallback if memory_utils not available
    def extract_tool_observation(entry):
        return None

    def create_observation(obs_type, content, metadata=None, timestamp=None):
        return {
            'type': obs_type,
            'content': content,
            'metadata': metadata or {},
            'timestamp': timestamp or datetime.now().isoformat()
        }

    def save_observation_to_jsonl(obs, file_path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obs) + '\n')


def process_tool_use(input_data: dict) -> dict:
    """Process tool use and capture observations."""
    observations_captured = 0

    try:
        # Get paths from environment or use default
        memory_path = os.getenv('MEMORY_STORAGE_PATH', '.claude/memory/session_conversations/')
        memory_dir = Path(os.getcwd()) / memory_path
        observations_file = memory_dir / 'tool_observations.jsonl'

        # Extract tool information from input
        tool_name = input_data.get('tool_name', 'unknown')
        tool_input = input_data.get('tool_input', {})
        tool_output = input_data.get('tool_output', '')
        is_error = input_data.get('is_error', False)

        # Create observation
        observation = create_observation(
            observation_type='tool_use',
            content=f"Tool: {tool_name}",
            metadata={
                'tool_name': tool_name,
                'input': tool_input,
                'output': str(tool_output)[:500],  # Limit output size
                'is_error': is_error
            }
        )

        # Save observation
        save_observation_to_jsonl(observation, observations_file)
        observations_captured = 1

        return {
            'success': True,
            'observations_captured': observations_captured,
            'message': f'Captured tool use: {tool_name}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'observations_captured': 0
        }


def main():
    """Main hook entry point."""
    try:
        # Read input from stdin
        raw_input = sys.stdin.read()

        # Debug logging
        memory_path = os.getenv('MEMORY_STORAGE_PATH', '.claude/memory/session_conversations/')
        debug_file = Path(os.getcwd()) / memory_path / 'post_tool_debug.log'
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now().isoformat()}] Received:\n{raw_input}\n")

        # Parse input
        if raw_input.strip():
            input_data = json.loads(raw_input)
        else:
            input_data = {}

        # Process the tool use
        result = process_tool_use(input_data)

        # Return result
        print(json.dumps(result))
        return 0

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        return 1


if __name__ == '__main__':
    sys.exit(main())
