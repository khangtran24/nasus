"""Input validation utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class Validators:
    """Common validation functions."""

    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> bool:
        """Validate a file path.

        Args:
            path: File path to validate
            must_exist: Whether file must exist

        Returns:
            True if valid

        Raises:
            ValueError: If path is invalid
        """
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")

        # Check for suspicious patterns
        if ".." in path:
            raise ValueError("Path contains directory traversal")

        if must_exist:
            p = Path(path)
            if not p.exists():
                raise ValueError(f"Path does not exist: {path}")

        return True

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate a session ID.

        Args:
            session_id: Session ID to validate

        Returns:
            True if valid

        Raises:
            ValueError: If session ID is invalid
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Session ID must be a non-empty string")

        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise ValueError(
                "Session ID must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )

        if len(session_id) > 100:
            raise ValueError("Session ID too long (max 100 characters)")

        return True

    @staticmethod
    def validate_agent_name(name: str) -> bool:
        """Validate an agent name.

        Args:
            name: Agent name to validate

        Returns:
            True if valid

        Raises:
            ValueError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Agent name must be a non-empty string")

        # Allow alphanumeric and underscores
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            raise ValueError(
                "Agent name must start with lowercase letter and contain "
                "only lowercase letters, numbers, and underscores"
            )

        if len(name) > 50:
            raise ValueError("Agent name too long (max 50 characters)")

        return True

    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """Sanitize user input.

        Args:
            text: Text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        if len(text) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")

        # Remove null bytes and other control characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())

        return text.strip()

    @staticmethod
    def validate_dict(
        data: Any,
        required_keys: list[str] | None = None
    ) -> bool:
        """Validate a dictionary structure.

        Args:
            data: Data to validate
            required_keys: Required keys in the dict

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        if required_keys:
            missing = set(required_keys) - set(data.keys())
            if missing:
                raise ValueError(f"Missing required keys: {missing}")

        return True
