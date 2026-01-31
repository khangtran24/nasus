"""Configuration management for the multi-agent system."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model Provider Configuration
    model_provider: str = Field(
        default="claude_agent_sdk",
        description="LLM provider to use (claude_agent_sdk or openrouter)"
    )

    # Claude API Configuration
    claude_api_key: str = Field(
        default="",
        description="Claude API key (Anthropic API key for Claude access)"
    )

    # OpenRouter API Configuration
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for multi-model access"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )

    # Claude Agent SDK Configuration
    claude_agent_sdk_use_pro_features: bool = Field(
        default=True,
        description="Enable Claude Pro subscription features when using claude_agent_sdk"
    )
    claude_agent_sdk_pro_tier: str = Field(
        default="",
        description="Optional Pro tier specification for claude_agent_sdk"
    )

    # Model Configuration
    default_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Default model to use"
    )

    # Context Management
    max_context_tokens: int = Field(
        default=4000,
        description="Maximum tokens before triggering summarization"
    )
    summarization_threshold: float = Field(
        default=0.8,
        description="Trigger summarization at this % of max_context_tokens"
    )
    recent_turns_to_keep: int = Field(
        default=3,
        description="Number of recent conversation turns to keep in full detail"
    )

    # Jira Configuration
    jira_url: Optional[str] = Field(
        default=None,
        description="Jira instance URL"
    )
    jira_email: Optional[str] = Field(
        default=None,
        description="Jira user email"
    )
    jira_api_token: Optional[str] = Field(
        default=None,
        description="Jira API token"
    )

    # Confluence Configuration
    confluence_url: Optional[str] = Field(
        default=None,
        description="Confluence instance URL"
    )
    confluence_email: Optional[str] = Field(
        default=None,
        description="Confluence user email"
    )
    confluence_api_token: Optional[str] = Field(
        default=None,
        description="Confluence API token"
    )

    # Slack Configuration
    slack_bot_token: Optional[str] = Field(
        default=None,
        description="Slack bot token"
    )
    slack_app_token: Optional[str] = Field(
        default=None,
        description="Slack app token"
    )

    # GitHub CI Configuration
    github_token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token for CI/CD operations"
    )
    github_owner: Optional[str] = Field(
        default=None,
        description="Default GitHub repository owner/organization"
    )
    github_repo: Optional[str] = Field(
        default=None,
        description="Default GitHub repository name"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_file: str = Field(
        default="logs/agent.log",
        description="Path to log file"
    )
    log_rotation_enabled: bool = Field(
        default=True,
        description="Enable log file rotation"
    )
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum log file size before rotation (bytes)"
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    log_use_rich_console: bool = Field(
        default=True,
        description="Use Rich library for prettier console output"
    )

    # Session Storage
    session_storage_path: str = Field(
        default="sessions/",
        description="Directory for session storage"
    )

    # Memory Storage
    memory_storage_path: str = Field(
        default=".claude/memory/session_conversations/",
        description="Directory for conversation memory storage (used by hooks)"
    )

    # Agent Configuration
    enable_parallel_execution: bool = Field(
        default=False,
        description="Enable parallel agent execution for independent tasks"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retries for failed operations"
    )
    timeout_seconds: int = Field(
        default=300,
        description="Timeout for agent operations in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        # Create logs directory
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create session storage directory
        session_dir = Path(self.session_storage_path)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create memory storage directory
        memory_dir = Path(self.memory_storage_path)
        memory_dir.mkdir(parents=True, exist_ok=True)

    def has_jira_config(self) -> bool:
        """Check if Jira is configured."""
        return all([
            self.jira_url,
            self.jira_email,
            self.jira_api_token
        ])

    def has_confluence_config(self) -> bool:
        """Check if Confluence is configured."""
        return all([
            self.confluence_url,
            self.confluence_email,
            self.confluence_api_token
        ])

    def has_slack_config(self) -> bool:
        """Check if Slack is configured."""
        return all([
            self.slack_bot_token,
            self.slack_app_token
        ])

    def has_github_ci_config(self) -> bool:
        """Check if GitHub CI is configured."""
        return all([
            self.github_token,
            self.github_owner,
            self.github_repo
        ])

    def get_claude_api_key(self) -> str:
        """Get the Claude API key.

        Returns:
            Claude API key (Anthropic API key)
        """
        return self.claude_api_key


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
