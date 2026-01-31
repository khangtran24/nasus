#!/usr/bin/env python3
"""
Test script to verify ModelRouter integration works.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.model_router import ModelRouter


async def test_model_router():
    """Test ModelRouter connectivity and basic functionality."""
    print("Testing ModelRouter Integration\n")

    # Check configuration
    print(f"Provider: {settings.model_provider}")
    print(f"Model: {settings.default_model}")

    if settings.model_provider == "anthropic":
        if not settings.anthropic_api_key:
            print("[ERROR] ANTHROPIC_API_KEY not set in .env")
            return False
        api_key = settings.anthropic_api_key
    elif settings.model_provider == "openrouter":
        if not settings.openrouter_api_key:
            print("[ERROR] OPENROUTER_API_KEY not set in .env")
            return False
        api_key = settings.openrouter_api_key
    else:
        print(f"[ERROR] Unsupported provider: {settings.model_provider}")
        return False

    print(f"API Key: {api_key[:10]}...{api_key[-4:]}\n")

    # Initialize router
    try:
        router = ModelRouter(
            provider=settings.model_provider,
            api_key=api_key,
            default_model=settings.default_model
        )
        print(f"[OK] Router initialized: {router.get_provider_name()}\n")
    except Exception as e:
        print(f"[ERROR] Failed to initialize router: {e}")
        return False

    # Test simple message
    print("Testing simple message generation...")
    try:
        response = await router.create_message(
            messages=[
                {"role": "user", "content": "Say 'Hello, memory system!' in exactly those words."}
            ],
            max_tokens=100
        )

        # Extract text from content blocks
        text_content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text_content += block.text

        print(f"[OK] Response received:")
        print(f"   Content: {text_content[:100]}...")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {getattr(response.usage, 'input_tokens', 0)} input, {getattr(response.usage, 'output_tokens', 0)} output\n")

    except Exception as e:
        print(f"[ERROR] Failed to create message: {e}")
        return False

    # Test summarization capability
    print("Testing summarization capability...")
    try:
        long_text = """
        User executed the following actions:
        1. Created a new file called database.py
        2. Added SQLite connection logic
        3. Ran tests for the database module
        4. Fixed a bug in the connection pooling
        5. Updated documentation

        The session was focused on implementing database functionality.
        """

        response = await router.create_message(
            messages=[
                {"role": "user", "content": f"Summarize this in one concise sentence:\n\n{long_text}"}
            ],
            max_tokens=150
        )

        # Extract text from content blocks
        summary_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                summary_text += block.text

        print(f"[OK] Summarization works:")
        print(f"   Summary: {summary_text}\n")

    except Exception as e:
        print(f"[ERROR] Summarization test failed: {e}")
        return False

    print("[OK] All tests passed! ModelRouter is working correctly.")
    return True


if __name__ == "__main__":
    result = asyncio.run(test_model_router())
    sys.exit(0 if result else 1)
