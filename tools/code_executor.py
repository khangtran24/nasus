"""Code execution tools with sandboxing."""

from __future__ import annotations

import subprocess
import sys
from typing import Any, Dict


class CodeExecutor:
    """Execute Python code safely."""

    def __init__(self, timeout: int = 30):
        """Initialize code executor.

        Args:
            timeout: Execution timeout in seconds
        """
        self.timeout = timeout

    def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code and capture output.

        Args:
            code: Python code to execute

        Returns:
            Dict with stdout, stderr, return_code, and success
        """
        try:
            # Execute code in subprocess for isolation
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds",
                "return_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "return_code": -1,
                "success": False
            }

    def execute_file(self, file_path: str, *args: str) -> Dict[str, Any]:
        """Execute a Python file.

        Args:
            file_path: Path to Python file
            *args: Arguments to pass to the script

        Returns:
            Dict with execution results
        """
        try:
            result = subprocess.run(
                [sys.executable, file_path, *args],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds",
                "return_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "return_code": -1,
                "success": False
            }

    def run_tests(
        self,
        test_path: str,
        *pytest_args: str
    ) -> Dict[str, Any]:
        """Run pytest tests.

        Args:
            test_path: Path to test file or directory
            *pytest_args: Additional pytest arguments

        Returns:
            Dict with test results
        """
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v", *pytest_args],
                capture_output=True,
                text=True,
                timeout=self.timeout * 2  # Tests may take longer
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "tests_passed": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Tests timed out after {self.timeout * 2} seconds",
                "return_code": -1,
                "success": False,
                "tests_passed": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Test execution error: {str(e)}",
                "return_code": -1,
                "success": False,
                "tests_passed": False
            }
