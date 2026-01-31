"""File operation tools with safety checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class FileOperations:
    """Safe file read/write operations."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize file operations.

        Args:
            base_path: Optional base path for file operations (defaults to cwd)
        """
        self.base_path = Path(base_path or os.getcwd())

    def read_file(self, file_path: str) -> str:
        """Read a file safely.

        Args:
            file_path: Path to file (relative to base_path)

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If no read permission
        """
        full_path = self._resolve_path(file_path)
        self._validate_path(full_path, must_exist=True)

        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, file_path: str, content: str) -> None:
        """Write to a file safely.

        Args:
            file_path: Path to file (relative to base_path)
            content: Content to write

        Raises:
            PermissionError: If no write permission
        """
        full_path = self._resolve_path(file_path)
        self._validate_path(full_path, must_exist=False)

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def append_file(self, file_path: str, content: str) -> None:
        """Append to a file safely.

        Args:
            file_path: Path to file (relative to base_path)
            content: Content to append
        """
        full_path = self._resolve_path(file_path)
        self._validate_path(full_path, must_exist=False)

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists
        """
        full_path = self._resolve_path(file_path)
        return full_path.exists() and full_path.is_file()

    def list_files(
        self,
        directory: str = ".",
        pattern: str = "*",
        recursive: bool = False
    ) -> list[str]:
        """List files in directory.

        Args:
            directory: Directory to list (relative to base_path)
            pattern: Glob pattern (e.g., "*.py")
            recursive: Recursive search

        Returns:
            List of relative file paths
        """
        dir_path = self._resolve_path(directory)
        self._validate_path(dir_path, must_exist=True)

        if recursive:
            files = dir_path.rglob(pattern)
        else:
            files = dir_path.glob(pattern)

        # Convert to relative paths
        return [
            str(f.relative_to(self.base_path))
            for f in files
            if f.is_file()
        ]

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path to absolute path.

        Args:
            file_path: Relative or absolute path

        Returns:
            Absolute Path object
        """
        path = Path(file_path)

        if path.is_absolute():
            return path

        return (self.base_path / path).resolve()

    def _validate_path(self, path: Path, must_exist: bool = False) -> None:
        """Validate a file path for safety.

        Args:
            path: Path to validate
            must_exist: Whether path must exist

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If must_exist=True and path doesn't exist
        """
        # Ensure path is within base_path (prevent directory traversal)
        try:
            path.relative_to(self.base_path)
        except ValueError:
            raise ValueError(
                f"Path {path} is outside base path {self.base_path}"
            )

        if must_exist and not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
