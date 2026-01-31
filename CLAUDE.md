# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a multi-agent AI system powered by Claude that provides specialized software development assistance. The system uses an orchestrator to intelligently route user requests to specialized agents, each with expertise in different development tasks.

## Running the Application

### Basic Usage

```bash
# Interactive mode
python main.py

# Single query mode
python main.py -q "Your request here"

# List available agents
python main.py --list-agents

# Verbose logging
python main.py -v
```

### Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add required API keys
```

### Development Commands

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy core/ agents/ tools/

# Linting
ruff check .
pylint core/ agents/ tools/

# Code formatting
black .
```

## Architecture

### Core Request Flow

```
User Request
    ↓
Orchestrator (classifies intent using Claude)
    ↓
Agent Selection (based on intent classification)
    ↓
Context Manager (retrieves session context with summarization)
    ↓
Agent Execution (specialized agent with MCP tools)
    ↓
Response Aggregation
    ↓
Context Update (with automatic summarization if threshold reached)
```

### Key Components

**Orchestrator** (`core/orchestrator.py`)
- Main coordinator that routes requests to appropriate agents
- Performs intent classification using Claude
- Manages agent execution (sequential by default, parallel execution configurable)
- Aggregates responses from multiple agents
- Entry point for all user requests

**Context Manager** (`core/context_manager.py`)
- Maintains conversation history with intelligent summarization
- Automatically summarizes when token count exceeds threshold (default: 80% of 4000 tokens)
- Keeps last 3 conversation turns in full detail (configurable via `RECENT_TURNS_TO_KEEP`)
- Persists sessions to disk in `sessions/` directory
- Tracks active files and task history

**MCP Manager** (`core/mcp_manager.py`)
- Manages Model Context Protocol server lifecycle
- Integrates with Jira, Confluence, and Slack (when configured)
- Note: Current implementation is a placeholder - full MCP protocol communication needs to be implemented
- Tool discovery and execution framework is in place

**Model Router** (`core/model_router.py`)
- Abstraction layer supporting multiple LLM providers
- Plugin-based architecture with separate provider implementations
- Supports Anthropic (direct), OpenRouter (multi-model), and Claude Agent SDK (Pro subscription)
- Provides unified response format across all providers
- Provider configured via `MODEL_PROVIDER` env var (anthropic/openrouter/claude_agent_sdk)
- See [PROVIDERS.md](docs/PROVIDERS.md) for detailed provider documentation

**Provider System** (`core/providers/`)
- `base.py` - Abstract base class for all providers
- `anthropic_provider.py` - Direct Anthropic API access
- `openrouter_provider.py` - Multi-model access via OpenRouter
- `claude_agent_sdk_provider.py` - Claude with Pro subscription support
- All providers implement unified `BaseProvider` interface

**Agent Registry** (`core/agent_registry.py`)
- Maintains registry of all available agents and their capabilities
- Enables lookup by name or capability

### Specialized Agents

All agents inherit from `BaseAgent` (`agents/base_agent.py`) and must implement `_get_system_prompt()`.

**Available Agents:**
- `coder`: Code generation, modification, debugging, refactoring
- `test_writer`: Test generation with pytest
- `requirement_analyzer`: Requirements analysis, Jira/Confluence integration
- `qa_checker`: Code quality checks, linting, security analysis
- `docs_agent`: Documentation creation, Slack summaries

Each agent:
- Lives in `agents/` directory
- Has a corresponding prompt file in `prompts/`
- Uses ModelRouter for LLM calls (supports provider switching)
- Can access MCP tools for external integrations
- Returns standardized `AgentResponse` objects

### Tools

Tools are available to agents for various operations:
- `file_operations.py`: Read/write/edit files
- `code_executor.py`: Execute Python code safely
- `linters.py`: Run pylint, ruff, mypy
- `web_search.py`: DuckDuckGo search integration

### Configuration

**Environment Variables** (`.env`):
- `MODEL_PROVIDER`: Choose between "anthropic", "openrouter", or "claude_agent_sdk"
- `ANTHROPIC_API_KEY`: Required for Anthropic and Claude Agent SDK providers
- `OPENROUTER_API_KEY`: Required if using OpenRouter provider
- `DEFAULT_MODEL`: Model to use (default: claude-sonnet-4-5-20250929)
- `CLAUDE_AGENT_SDK_USE_PRO_FEATURES`: Enable Pro features (default: true)
- `CLAUDE_AGENT_SDK_PRO_TIER`: Optional Pro tier specification
- `MAX_CONTEXT_TOKENS`: Maximum tokens before summarization (default: 4000)
- `SUMMARIZATION_THRESHOLD`: Percentage threshold to trigger summarization (default: 0.8)
- `RECENT_TURNS_TO_KEEP`: Number of recent turns kept in full (default: 3)
- `ENABLE_PARALLEL_EXECUTION`: Enable parallel agent execution (default: false)
- Optional: Jira, Confluence, Slack credentials for MCP integrations

**Configuration object** (`config.py`):
- Uses Pydantic Settings for type-safe configuration
- Auto-creates necessary directories (logs/, sessions/)
- Provides helper methods: `has_jira_config()`, `has_confluence_config()`, `has_slack_config()`

## Important Implementation Details

### Intent Classification

The orchestrator uses Claude to classify user intent and select appropriate agents:
1. Calls Claude with `INTENT_CLASSIFICATION_PROMPT` system prompt
2. Expects JSON response with: `intent`, `confidence`, `agents`, `reasoning`
3. Falls back to keyword-based heuristics if classification fails
4. Routes to single or multiple agents based on classification

### Context Management Strategy

- **Recent Turns**: Last N turns (default 3) kept in full detail
- **Summarization**: Triggered when context exceeds 80% of max tokens
- **Summary Generation**: Uses Claude to create concise technical summaries
- **Active Files Tracking**: Automatically tracks files modified during session
- **Task History**: Maintains list of actions taken
- **Persistence**: All session data saved to JSON files in `sessions/`

### Session Resumption

Sessions are automatically persisted. To resume:
```bash
python main.py -s <session_id>
```

Session files are JSON format in `sessions/` directory.

### Adding New Agents

1. Create agent class in `agents/` inheriting from `BaseAgent`
2. Implement `_get_system_prompt()` method
3. Create corresponding prompt file in `prompts/`
4. Register in `Orchestrator._register_agents()` with capabilities
5. Update intent classification logic in `orchestrator_prompts.py` if needed

### MCP Integration Notes

Current MCP implementation is a **placeholder**. To fully implement:
1. Implement proper MCP protocol communication in `MCPManager`
2. Add actual tool discovery via MCP protocol
3. Implement `call_tool()` to send requests via MCP stdio protocol
4. Handle MCP responses and error cases
5. Consider using `mcp` Python package for protocol handling

## Testing Strategy

When writing tests:
- Use pytest with async support (`pytest-asyncio`)
- Mock external API calls (Anthropic, MCP servers)
- Test agent behavior with sample contexts
- Test context summarization logic
- Verify tool formatting and execution

## Provider Selection Guide

### When to Use Each Provider

**Anthropic (Default)**
- Best for: Production use, latest features
- Pros: Direct API access, official SDK, no markup
- Cons: Single provider only

**OpenRouter**
- Best for: Experimentation, multi-model access
- Pros: Access to many models, unified billing
- Cons: Slight pricing markup, model name differences

**Claude Agent SDK**
- Best for: High-volume production, Pro subscribers
- Pros: 5x higher rate limits, priority access, Pro benefits
- Cons: Requires Pro subscription for full benefits
- See [PROVIDERS.md](docs/PROVIDERS.md) for detailed comparison

## Common Pitfalls

1. **API Keys**: Ensure correct API key is set based on `MODEL_PROVIDER` setting
2. **Provider Names**: OpenRouter models need provider prefix (e.g., `anthropic/claude-sonnet-4-5`)
3. **Context Overflow**: Monitor token usage; adjust `MAX_CONTEXT_TOKENS` if needed
4. **MCP Servers**: Current implementation is placeholder; tool calls won't execute without full MCP integration
5. **Model Compatibility**: When switching providers, verify model names are correct for that provider
6. **Session Persistence**: Ensure `sessions/` directory has write permissions
7. **Pro Features**: Claude Agent SDK Pro features require valid Pro subscription API key
