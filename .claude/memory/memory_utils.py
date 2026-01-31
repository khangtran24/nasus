"""
Utility functions for memory capture and processing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def extract_text_from_content(content: Any) -> str:
    """
    Extract text from various content formats.

    Args:
        content: Content in various formats (str, dict, list)

    Returns:
        Extracted text string
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
            elif isinstance(item, str):
                text_parts.append(item)
        return ' '.join(text_parts)

    if isinstance(content, dict):
        if content.get('type') == 'text':
            return content.get('text', '')
        # Try to extract any text field
        for key in ['text', 'content', 'message']:
            if key in content:
                return str(content[key])

    return str(content)


def parse_transcript_entry(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single line from the transcript file.

    Args:
        line: JSON line from transcript

    Returns:
        Parsed entry dict or None if invalid
    """
    try:
        entry = json.loads(line.strip())
        return entry
    except json.JSONDecodeError:
        return None


def extract_tool_observation(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract tool usage observation from a transcript entry.

    Args:
        entry: Transcript entry

    Returns:
        Tool observation dict or None
    """
    if entry.get('type') not in ['tool_use', 'tool_result']:
        return None

    timestamp = entry.get('timestamp', datetime.now().isoformat())

    if entry.get('type') == 'tool_use':
        message = entry.get('message', {})
        content = message.get('content', [])

        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                return {
                    'type': 'tool_use',
                    'tool_name': block.get('name'),
                    'tool_id': block.get('id'),
                    'input': block.get('input', {}),
                    'timestamp': timestamp
                }

    elif entry.get('type') == 'tool_result':
        content = entry.get('content', [])

        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get('type') == 'tool_result':
                return {
                    'type': 'tool_result',
                    'tool_id': block.get('tool_use_id'),
                    'content': extract_text_from_content(block.get('content', '')),
                    'is_error': block.get('is_error', False),
                    'timestamp': timestamp
                }

    return None


def create_observation(
    observation_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized observation object.

    Args:
        observation_type: Type of observation (tool_use, user_input, decision, etc.)
        content: Main content of the observation
        metadata: Additional metadata
        timestamp: ISO format timestamp (defaults to now)

    Returns:
        Observation dict
    """
    return {
        'type': observation_type,
        'content': content,
        'metadata': metadata or {},
        'timestamp': timestamp or datetime.now().isoformat()
    }


def save_observation_to_jsonl(observation: Dict[str, Any], file_path: Path) -> None:
    """
    Save an observation to a JSONL file.

    Args:
        observation: Observation dict
        file_path: Path to JSONL file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(observation) + '\n')


def load_observations_from_jsonl(file_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load observations from a JSONL file.

    Args:
        file_path: Path to JSONL file
        limit: Maximum number of observations to load (most recent first)

    Returns:
        List of observation dicts
    """
    if not file_path.exists():
        return []

    observations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            obs = parse_transcript_entry(line)
            if obs:
                observations.append(obs)

    # Return most recent first
    observations.reverse()

    if limit:
        observations = observations[:limit]

    return observations


def summarize_observations(observations: List[Dict[str, Any]]) -> str:
    """
    Create a simple text summary of observations.

    Args:
        observations: List of observations

    Returns:
        Summary string
    """
    if not observations:
        return "No observations recorded."

    tool_uses = [o for o in observations if o.get('type') == 'tool_use']
    decisions = [o for o in observations if o.get('type') == 'decision']
    preferences = [o for o in observations if o.get('type') == 'preference']

    summary_parts = []

    if tool_uses:
        tools = [o.get('metadata', {}).get('tool_name', 'unknown') for o in tool_uses]
        unique_tools = list(set(tools))
        summary_parts.append(f"Used {len(tool_uses)} tools: {', '.join(unique_tools[:5])}")

    if decisions:
        summary_parts.append(f"Made {len(decisions)} decisions")

    if preferences:
        summary_parts.append(f"Captured {len(preferences)} preferences")

    return "; ".join(summary_parts) if summary_parts else "Session activity recorded."
