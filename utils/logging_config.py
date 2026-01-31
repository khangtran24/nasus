"""Logging configuration for the multi-agent system."""

import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
from rich.console import Console

from config import settings


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs."""

    SENSITIVE_PATTERNS = [
        'api_key',
        'api_token',
        'password',
        'secret',
        'token',
        'authorization',
        'bearer',
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log messages.

        Args:
            record: Log record to filter

        Returns:
            True to allow the record to be logged
        """
        message = record.getMessage().lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = str(record.msg).replace(
                    record.msg,
                    f"[REDACTED - {pattern.upper()}]"
                )
        return True


def setup_logging(
    use_rich_console: bool = True,
    enable_rotation: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Configure logging for the application.

    Args:
        use_rich_console: Use Rich library for prettier console output
        enable_rotation: Enable log file rotation
        max_bytes: Maximum size of log file before rotation (default 10MB)
        backup_count: Number of backup log files to keep (default 5)
    """
    # Create logs directory if it doesn't exist
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Parse log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create detailed formatter for file logs
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    if enable_rotation:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')

    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(SensitiveDataFilter())

    # Console handler
    if use_rich_console:
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=log_level == logging.DEBUG
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(simple_formatter)

    console_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure third-party loggers
    _configure_third_party_loggers()

    logging.info("Logging configured successfully")


def _configure_third_party_loggers() -> None:
    """Configure log levels for third-party libraries."""
    third_party_configs = {
        "anthropic": logging.WARNING,
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
        "openai": logging.WARNING,
        "urllib3": logging.WARNING,
        "asyncio": logging.WARNING,
        "aiohttp": logging.WARNING,
    }

    for logger_name, level in third_party_configs.items():
        logging.getLogger(logger_name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance

    Example:
        ```python
        from utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request")
        logger.debug("Debug details: %s", data)
        ```
    """
    return logging.getLogger(name)


def create_timed_rotating_handler(
    log_file: Optional[str] = None,
    when: str = 'midnight',
    interval: int = 1,
    backup_count: int = 30
) -> TimedRotatingFileHandler:
    """Create a time-based rotating file handler.

    Useful for creating daily log files with automatic rotation.

    Args:
        log_file: Path to log file (defaults to settings.log_file)
        when: When to rotate ('midnight', 'H', 'D', 'W0'-'W6')
        interval: Interval between rotations
        backup_count: Number of backup files to keep

    Returns:
        Configured TimedRotatingFileHandler

    Example:
        ```python
        # Create daily rotating logs
        handler = create_timed_rotating_handler(
            log_file='logs/daily.log',
            when='midnight',
            backup_count=30
        )
        logging.getLogger().addHandler(handler)
        ```
    """
    if log_file is None:
        log_file = settings.log_file

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(
        log_path,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding='utf-8'
    )

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    return handler
