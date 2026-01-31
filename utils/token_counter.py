"""Token counting utilities."""

from __future__ import annotations


class TokenCounter:
    """Utility for estimating token counts."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text.

        This is a rough approximation. For accurate counts, use
        the tiktoken library.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        # This is conservative for English text
        return len(text) // 4

    @staticmethod
    def estimate_tokens_from_messages(messages: list[dict]) -> int:
        """Estimate tokens for a list of messages.

        Args:
            messages: List of message dicts with 'content'

        Returns:
            Estimated token count
        """
        total = 0

        for message in messages:
            # Count content
            content = message.get("content", "")
            total += TokenCounter.estimate_tokens(content)

            # Add overhead for message structure (~4 tokens per message)
            total += 4

        return total

    @staticmethod
    def fits_in_context(
        text: str,
        max_tokens: int = 4096
    ) -> bool:
        """Check if text fits in a context window.

        Args:
            text: Text to check
            max_tokens: Maximum tokens allowed

        Returns:
            True if text fits
        """
        estimated = TokenCounter.estimate_tokens(text)
        return estimated <= max_tokens

    @staticmethod
    def truncate_to_tokens(
        text: str,
        max_tokens: int,
        suffix: str = "..."
    ) -> str:
        """Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        estimated = TokenCounter.estimate_tokens(text)

        if estimated <= max_tokens:
            return text

        # Calculate approximate character limit
        char_limit = max_tokens * 4 - len(suffix)

        return text[:char_limit] + suffix
