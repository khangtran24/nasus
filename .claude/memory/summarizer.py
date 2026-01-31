"""
AI-powered summarization using ModelRouter.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.model_router import ModelRouter


class MemorySummarizer:
    """AI-powered memory summarization using ModelRouter."""

    def __init__(self):
        """Initialize the summarizer with ModelRouter."""
        # Determine which API key to use based on provider
        if settings.model_provider == "anthropic":
            api_key = settings.anthropic_api_key
        elif settings.model_provider == "openrouter":
            api_key = settings.openrouter_api_key
        elif settings.model_provider == "claude_agent_sdk":
            api_key = settings.anthropic_api_key
        else:
            api_key = None

        self.router = ModelRouter(
            provider=settings.model_provider,
            api_key=api_key,
            default_model=settings.default_model
        )

    async def summarize_observation(
        self,
        observation: Dict[str, Any],
        max_length: int = 100
    ) -> str:
        """
        Summarize a single observation.

        Args:
            observation: Observation dict
            max_length: Maximum summary length in tokens

        Returns:
            Summary string
        """
        content = observation.get('content', '')
        obs_type = observation.get('type', 'unknown')
        tool_name = observation.get('tool_name', '')

        prompt = f"""Summarize this {obs_type} observation in one concise sentence (max 20 words):

Tool: {tool_name}
Content: {content[:500]}

Summary:"""

        try:
            response = await self.router.create_message(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length
            )

            # Extract text from response
            summary = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    summary += block.text

            return summary.strip() or "No summary available"

        except Exception as e:
            return f"Summarization error: {str(e)[:50]}"

    async def summarize_session(
        self,
        observations: List[Dict[str, Any]],
        max_length: int = 300
    ) -> str:
        """
        Summarize an entire session.

        Args:
            observations: List of observation dicts
            max_length: Maximum summary length in tokens

        Returns:
            Session summary string
        """
        if not observations:
            return "No observations in session."

        # Group observations by type
        tool_uses = [o for o in observations if o.get('type') == 'tool_use']
        decisions = [o for o in observations if o.get('type') == 'decision']
        preferences = [o for o in observations if o.get('type') == 'preference']

        # Create summary prompt
        obs_summary = f"""Session had {len(observations)} total observations:
- {len(tool_uses)} tool uses
- {len(decisions)} decisions
- {len(preferences)} preferences

Sample observations:
"""

        # Add sample observations
        for i, obs in enumerate(observations[:5]):
            obs_type = obs.get('type', 'unknown')
            content = obs.get('content', '')[:100]
            obs_summary += f"{i+1}. [{obs_type}] {content}\n"

        prompt = f"""Summarize this coding session in 2-3 concise sentences:

{obs_summary}

Summary:"""

        try:
            response = await self.router.create_message(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length
            )

            # Extract text from response
            summary = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    summary += block.text

            return summary.strip() or "Session completed."

        except Exception as e:
            return f"Session with {len(observations)} observations. Summarization unavailable."

    async def batch_summarize(
        self,
        observations: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> Dict[int, str]:
        """
        Summarize multiple observations in batches.

        Args:
            observations: List of observations to summarize
            batch_size: Number of observations to process concurrently

        Returns:
            Dict mapping observation IDs to summaries
        """
        summaries = {}

        for i in range(0, len(observations), batch_size):
            batch = observations[i:i + batch_size]

            # Create tasks for concurrent summarization
            tasks = [
                self.summarize_observation(obs)
                for obs in batch
            ]

            # Execute batch
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Map results to observation IDs
                for obs, summary in zip(batch, results):
                    obs_id = obs.get('id')
                    if isinstance(summary, Exception):
                        summaries[obs_id] = f"Error: {str(summary)[:50]}"
                    else:
                        summaries[obs_id] = summary

            except Exception as e:
                # If batch fails, mark all as failed
                for obs in batch:
                    summaries[obs.get('id')] = f"Batch error: {str(e)[:50]}"

        return summaries


def summarize_sync(
    observations: List[Dict[str, Any]],
    summary_type: str = "session"
) -> str:
    """
    Synchronous wrapper for summarization.

    Args:
        observations: List of observations
        summary_type: Type of summary ("session" or "batch")

    Returns:
        Summary string or dict
    """
    summarizer = MemorySummarizer()

    if summary_type == "session":
        return asyncio.run(summarizer.summarize_session(observations))
    elif summary_type == "batch":
        return asyncio.run(summarizer.batch_summarize(observations))
    else:
        raise ValueError(f"Unknown summary type: {summary_type}")
