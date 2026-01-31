"""Example script demonstrating different LLM providers."""

import asyncio
import os
from dotenv import load_dotenv

from core.model_router import ModelRouter
from utils.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)


def get_claude_api_key():
    """Get Claude API key from environment (CLAUDE_API_KEY or ANTHROPIC_API_KEY)."""
    return os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")


async def test_anthropic_provider():
    """Test Anthropic provider."""
    logger.info("=" * 60)
    logger.info("Testing Anthropic Provider")
    logger.info("=" * 60)

    api_key = get_claude_api_key()
    if not api_key:
        logger.warning("CLAUDE_API_KEY not set, skipping test")
        return

    router = ModelRouter(
        provider="anthropic",
        api_key=api_key,
        default_model="claude-sonnet-4-5-20250929"
    )

    messages = [
        {"role": "user", "content": "Say 'Hello from Anthropic!' in a creative way."}
    ]

    try:
        response = await router.create_message(
            messages=messages,
            system="You are a creative assistant.",
            max_tokens=100
        )

        logger.info(f"Response: {response.content[0].text}")
        logger.info(f"Tokens: {response.usage.input_tokens}/{response.usage.output_tokens}")
        logger.info(f"Model: {response.model}")
        logger.info("✅ Anthropic test passed\n")

    except Exception as e:
        logger.error(f"❌ Anthropic test failed: {e}\n")


async def test_openrouter_provider():
    """Test OpenRouter provider."""
    logger.info("=" * 60)
    logger.info("Testing OpenRouter Provider")
    logger.info("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set, skipping test")
        return

    router = ModelRouter(
        provider="openrouter",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_model="anthropic/claude-sonnet-4-5",
        app_name="Nasus Test Script",
        site_url="https://github.com/yourusername/nasus"
    )

    messages = [
        {"role": "user", "content": "Say 'Hello from OpenRouter!' in a creative way."}
    ]

    try:
        response = await router.create_message(
            messages=messages,
            system="You are a creative assistant.",
            max_tokens=100
        )

        logger.info(f"Response: {response.content[0].text}")
        logger.info(f"Tokens: {response.usage.input_tokens}/{response.usage.output_tokens}")
        logger.info(f"Model: {response.model}")
        logger.info("✅ OpenRouter test passed\n")

    except Exception as e:
        logger.error(f"❌ OpenRouter test failed: {e}\n")


async def test_claude_agent_sdk_provider():
    """Test Claude Agent SDK provider."""
    logger.info("=" * 60)
    logger.info("Testing Claude Agent SDK Provider (Pro Support)")
    logger.info("=" * 60)

    api_key = get_claude_api_key()
    if not api_key:
        logger.warning("CLAUDE_API_KEY not set, skipping test")
        return

    router = ModelRouter(
        provider="claude_agent_sdk",
        api_key=api_key,
        default_model="claude-sonnet-4-5-20250929",
        use_pro_features=True
    )

    messages = [
        {"role": "user", "content": "Say 'Hello from Claude Agent SDK!' in a creative way."}
    ]

    try:
        response = await router.create_message(
            messages=messages,
            system="You are a creative assistant.",
            max_tokens=100
        )

        logger.info(f"Response: {response.content[0].text}")
        logger.info(f"Tokens: {response.usage.input_tokens}/{response.usage.output_tokens}")
        logger.info(f"Model: {response.model}")
        logger.info("✅ Claude Agent SDK test passed\n")

    except Exception as e:
        logger.error(f"❌ Claude Agent SDK test failed: {e}\n")


async def test_provider_comparison():
    """Compare responses from different providers."""
    logger.info("=" * 60)
    logger.info("Provider Comparison Test")
    logger.info("=" * 60)

    question = "What is 2+2? Answer in one sentence."
    messages = [{"role": "user", "content": question}]
    system = "You are a helpful math assistant."

    providers = []

    # Test Anthropic
    claude_key = get_claude_api_key()
    if claude_key:
        providers.append({
            "name": "Anthropic",
            "router": ModelRouter(
                provider="anthropic",
                api_key=claude_key,
                default_model="claude-sonnet-4-5-20250929"
            )
        })

    # Test OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        providers.append({
            "name": "OpenRouter",
            "router": ModelRouter(
                provider="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                default_model="anthropic/claude-sonnet-4-5"
            )
        })

    # Test Claude Agent SDK
    if claude_key:
        providers.append({
            "name": "Claude Agent SDK",
            "router": ModelRouter(
                provider="claude_agent_sdk",
                api_key=claude_key,
                default_model="claude-sonnet-4-5-20250929",
                use_pro_features=True
            )
        })

    logger.info(f"Question: {question}\n")

    for provider_info in providers:
        try:
            response = await provider_info["router"].create_message(
                messages=messages,
                system=system,
                max_tokens=50
            )

            logger.info(f"{provider_info['name']}:")
            logger.info(f"  Answer: {response.content[0].text}")
            logger.info(
                f"  Tokens: {response.usage.input_tokens}/"
                f"{response.usage.output_tokens}"
            )
            logger.info("")

        except Exception as e:
            logger.error(f"{provider_info['name']}: Error - {e}\n")


async def main():
    """Run all provider tests."""
    logger.info("\n🚀 Starting Provider Tests\n")

    # Test individual providers
    await test_anthropic_provider()
    await test_openrouter_provider()
    await test_claude_agent_sdk_provider()

    # Compare providers
    await test_provider_comparison()

    logger.info("=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
