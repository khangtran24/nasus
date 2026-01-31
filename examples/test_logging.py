"""Example script to test the logging configuration."""

import asyncio
from utils.logging_config import get_logger, setup_logging
from config import settings


def test_basic_logging():
    """Test basic logging functionality."""
    logger = get_logger(__name__)

    logger.debug("This is a DEBUG message - only visible with LOG_LEVEL=DEBUG")
    logger.info("This is an INFO message - general information")
    logger.warning("This is a WARNING message - something unexpected")
    logger.error("This is an ERROR message - something went wrong")
    logger.critical("This is a CRITICAL message - serious problem")


def test_sensitive_data_filtering():
    """Test that sensitive data is redacted."""
    logger = get_logger(__name__)

    # These should be redacted
    logger.info("API Key: sk-ant-1234567890")
    logger.info("Password: my_secret_password")
    logger.info("Bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")

    # These should NOT be redacted
    logger.info("User ID: 12345")
    logger.info("Session started successfully")


def test_exception_logging():
    """Test exception logging with traceback."""
    logger = get_logger(__name__)

    try:
        # Intentional error
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error("Division by zero occurred", exc_info=True)
        # Or use exception() which automatically includes traceback
        logger.exception("Using exception() method")


def test_structured_logging():
    """Test structured logging with context."""
    logger = get_logger(__name__)

    # Good practice: use lazy formatting
    user_id = "user_123"
    action = "login"
    logger.info("User action: %s by user %s", action, user_id)

    # Include context in logs
    request_id = "req_abc123"
    logger.info(f"[{request_id}] Processing request")
    logger.debug(f"[{request_id}] Request headers validated")
    logger.info(f"[{request_id}] Request completed")


async def test_async_logging():
    """Test logging in async context."""
    logger = get_logger(__name__)

    logger.info("Starting async operation")

    # Simulate async work
    await asyncio.sleep(0.1)
    logger.debug("Async operation in progress")

    await asyncio.sleep(0.1)
    logger.info("Async operation completed")


def main():
    """Run all logging tests."""
    print("=" * 60)
    print("Logging Configuration Test")
    print("=" * 60)
    print(f"Log Level: {settings.log_level}")
    print(f"Log File: {settings.log_file}")
    print(f"Rich Console: {settings.log_use_rich_console}")
    print(f"Rotation Enabled: {settings.log_rotation_enabled}")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging(
        use_rich_console=settings.log_use_rich_console,
        enable_rotation=settings.log_rotation_enabled,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count
    )

    # Run tests
    print("1. Testing basic logging levels...")
    test_basic_logging()
    print()

    print("2. Testing sensitive data filtering...")
    test_sensitive_data_filtering()
    print()

    print("3. Testing exception logging...")
    test_exception_logging()
    print()

    print("4. Testing structured logging...")
    test_structured_logging()
    print()

    print("5. Testing async logging...")
    asyncio.run(test_async_logging())
    print()

    print("=" * 60)
    print(f"Check the log file at: {settings.log_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
