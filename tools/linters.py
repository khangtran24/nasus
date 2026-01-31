"""Linter and formatter tool wrappers."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, List


class Linters:
    """Wrapper for various Python linting tools."""

    def __init__(self, timeout: int = 60):
        """Initialize linter tools.

        Args:
            timeout: Execution timeout in seconds
        """
        self.timeout = timeout

    def run_pylint(self, file_path: str) -> Dict[str, Any]:
        """Run pylint on a file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict with lint results
        """
        try:
            result = subprocess.run(
                ["pylint", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse JSON output
            try:
                issues = json.loads(result.stdout) if result.stdout else []
            except json.JSONDecodeError:
                issues = []

            return {
                "tool": "pylint",
                "file": file_path,
                "issues": issues,
                "issue_count": len(issues),
                "success": True
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "pylint",
                "file": file_path,
                "error": "Timeout",
                "success": False
            }
        except FileNotFoundError:
            return {
                "tool": "pylint",
                "file": file_path,
                "error": "pylint not installed",
                "success": False
            }
        except Exception as e:
            return {
                "tool": "pylint",
                "file": file_path,
                "error": str(e),
                "success": False
            }

    def run_ruff(self, file_path: str) -> Dict[str, Any]:
        """Run ruff linter on a file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict with lint results
        """
        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse JSON output
            try:
                issues = json.loads(result.stdout) if result.stdout else []
            except json.JSONDecodeError:
                issues = []

            return {
                "tool": "ruff",
                "file": file_path,
                "issues": issues,
                "issue_count": len(issues),
                "success": True
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "ruff",
                "file": file_path,
                "error": "Timeout",
                "success": False
            }
        except FileNotFoundError:
            return {
                "tool": "ruff",
                "file": file_path,
                "error": "ruff not installed",
                "success": False
            }
        except Exception as e:
            return {
                "tool": "ruff",
                "file": file_path,
                "error": str(e),
                "success": False
            }

    def run_mypy(self, file_path: str) -> Dict[str, Any]:
        """Run mypy type checker on a file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict with type check results
        """
        try:
            result = subprocess.run(
                ["mypy", file_path, "--show-error-codes"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse output (mypy doesn't have JSON format)
            issues = []
            for line in result.stdout.split('\n'):
                if line.strip() and ':' in line:
                    issues.append({
                        "message": line.strip(),
                        "type": "type-error"
                    })

            return {
                "tool": "mypy",
                "file": file_path,
                "issues": issues,
                "issue_count": len(issues),
                "output": result.stdout,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "mypy",
                "file": file_path,
                "error": "Timeout",
                "success": False
            }
        except FileNotFoundError:
            return {
                "tool": "mypy",
                "file": file_path,
                "error": "mypy not installed",
                "success": False
            }
        except Exception as e:
            return {
                "tool": "mypy",
                "file": file_path,
                "error": str(e),
                "success": False
            }

    def run_black(self, file_path: str, check_only: bool = True) -> Dict[str, Any]:
        """Run black formatter on a file.

        Args:
            file_path: Path to Python file
            check_only: Only check formatting (don't modify)

        Returns:
            Dict with formatting results
        """
        try:
            args = ["black", file_path]
            if check_only:
                args.extend(["--check", "--diff"])

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "tool": "black",
                "file": file_path,
                "formatted": result.returncode != 0 and not check_only,
                "would_reformat": result.returncode != 0 and check_only,
                "diff": result.stdout if check_only else "",
                "success": True
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "black",
                "file": file_path,
                "error": "Timeout",
                "success": False
            }
        except FileNotFoundError:
            return {
                "tool": "black",
                "file": file_path,
                "error": "black not installed",
                "success": False
            }
        except Exception as e:
            return {
                "tool": "black",
                "file": file_path,
                "error": str(e),
                "success": False
            }

    def run_all(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Run all linters on a file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict with results from all linters
        """
        return {
            "pylint": self.run_pylint(file_path),
            "ruff": self.run_ruff(file_path),
            "mypy": self.run_mypy(file_path),
            "black": self.run_black(file_path)
        }
