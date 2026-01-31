# Claude Code Memory System

A minimal implementation inspired by [claude-mem](https://github.com/thedotmack/claude-mem), providing persistent memory across Claude coding sessions.

## Features

### ✅ Phase 1: Enhanced Hook Capture
- **Session Start Hook**: Initializes memory system and loads recent context
- **Post Tool Use Hook**: Captures detailed tool execution observations
- **Stop Hook**: Generates session summaries and cleanup

### ✅ Phase 2: SQLite Storage with FTS5
- **SQLite Database**: Persistent storage for sessions, observations, and memories
- **FTS5 Full-Text Search**: Fast keyword-based search across all observations
- **Session Management**: Track sessions with start/end times and summaries
- **Observation Storage**: Store tool uses, decisions, preferences with metadata

### ✅ Phase 3: Hybrid Search (Keyword + Semantic)
- **Vector Embeddings**: Using sentence-transformers (all-MiniLM-L6-v2 model)
- **Semantic Search**: Find similar observations by meaning, not just keywords
- **Hybrid Search**: Combines keyword (FTS5) and semantic (vector) search
- **Optimized Storage**: Lightweight vector store with numpy

### ✅ Phase 4: AI Summarization
- **Observation Summaries**: AI-generated concise summaries for each observation
- **Session Summaries**: Comprehensive summaries of entire coding sessions
- **Batch Processing**: Efficient concurrent summarization
- **ModelRouter Integration**: Works with Anthropic, OpenRouter, or Claude Agent SDK

## Architecture

```
┌─────────────────┐
│  Claude Hooks   │
│  (Lifecycle)    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Memory Manager  │  ← Unified interface
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────────┐
    v         v             v              v
┌───────┐ ┌────────┐  ┌──────────┐  ┌────────────┐
│SQLite │ │Vector  │  │ Hybrid   │  │    AI      │
│+ FTS5 │ │ Store  │  │ Search   │  │Summarizer  │
└───────┘ └────────┘  └──────────┘  └────────────┘
```

## File Structure

```
.claude/
├── hooks/
│   ├── enhanced_session_start.py    # Initialize memory system
│   ├── enhanced_post_tool_use.py    # Capture tool observations
│   └── enhanced_on_stop.py          # Generate session summary
│
├── memory/
│   ├── database.py                  # SQLite with FTS5
│   ├── vector_store.py              # Semantic search
│   ├── summarizer.py                # AI summarization
│   ├── memory_manager.py            # Unified interface
│   ├── memory_utils.py              # Utility functions
│   ├── test_memory_system.py        # Comprehensive tests
│   └── README.md                    # This file
│
└── settings.json                    # Hook configuration
```

## Setup

### 1. Install Dependencies

```bash
# Install required packages
uv pip install sentence-transformers numpy

# Or add to requirements.txt:
# sentence-transformers>=2.2.0
# numpy>=1.24.0
```

### 2. Configure API Key

For AI summarization, set your API key in `.env`:

```bash
# For Anthropic
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# For OpenRouter
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...

# For Claude Agent SDK (Pro)
MODEL_PROVIDER=claude_agent_sdk
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Test the System

```bash
uv run python .claude/memory/test_memory_system.py
```

## Usage

### Automatic (via Hooks)

The hooks automatically capture observations during your Claude Code sessions:
- Session start/end are tracked
- Tool uses are recorded
- Summaries are generated

### Programmatic (Python)

```python
from pathlib import Path
from .claude.memory.memory_manager import MemoryManager

# Initialize manager
manager = MemoryManager(Path(".claude/memory"))

# Start session
session_id = manager.start_session({"project": "my-app"})

# Add observations
manager.add_observation(
    obs_type="tool_use",
    content="Read database.py file",
    tool_name="Read",
    auto_summarize=True,
    add_to_vector_store=True
)

# Search memories
results = manager.search("database implementation", limit=5, search_type="hybrid")

# Get session summary
summary = manager.get_session_summary()

# Get stats
stats = manager.get_stats()

# End session
manager.end_session(summary)
manager.close()
```

## Search Types

### Keyword Search (FTS5)
```python
results = manager.search("SQLite database", search_type="keyword")
```
- Fast exact and partial matches
- Good for specific terms and tool names

### Semantic Search (Vectors)
```python
results = manager.search("data persistence", search_type="semantic")
```
- Finds similar concepts by meaning
- Good for exploratory queries

### Hybrid Search (Recommended)
```python
results = manager.search("implement storage", search_type="hybrid")
```
- Combines both approaches
- Balanced results with relevance scoring

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    start_time TEXT,
    end_time TEXT,
    summary TEXT,
    metadata TEXT
)
```

### Observations Table
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    type TEXT,              -- tool_use, decision, preference
    tool_name TEXT,
    content TEXT,
    metadata TEXT,
    summary TEXT            -- AI-generated summary
)
```

### FTS5 Virtual Tables
- `observations_fts`: Full-text search on observations
- `memories_fts`: Full-text search on memories

## Performance

- **SQLite + FTS5**: < 10ms for keyword searches
- **Vector Search**: ~50-100ms (depends on vector count)
- **Hybrid Search**: ~100-150ms
- **AI Summarization**: ~1-2s per observation (with API call)

## Differences from claude-mem

| Feature | claude-mem | This Implementation |
|---------|------------|---------------------|
| Backend Service | Bun HTTP server | Integrated Python |
| Database | SQLite + Chroma | SQLite + sentence-transformers |
| Vector DB | ChromaDB | Lightweight numpy-based |
| API | REST endpoints | Python API |
| UI | Web viewer | CLI/Python only |
| Complexity | High (worker service) | Low (library) |
| Dependencies | Node.js, Bun, Chroma | Python packages only |

## Troubleshooting

### "No module named 'sentence_transformers'"
```bash
uv pip install sentence-transformers numpy
```

### "Could not resolve authentication method"
Set your API key in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### "Vector store model not loading"
The first run downloads the sentence-transformer model (~90MB). This is normal and happens once.

### Slow semantic search
- Vector search gets slower with more observations
- Consider using keyword search for large datasets
- Hybrid search automatically balances performance

## Testing

Run the comprehensive test suite:
```bash
uv run python .claude/memory/test_memory_system.py
```

Tests cover:
- ✅ SQLite database with FTS5
- ✅ Vector store and semantic search
- ✅ AI summarization (requires API key)
- ✅ Integrated memory manager

## Future Enhancements

Potential improvements (not yet implemented):
- [ ] Web UI for browsing memories
- [ ] Advanced timeline view
- [ ] Memory expiration and cleanup
- [ ] Multi-project support
- [ ] Export to markdown/JSON
- [ ] Advanced filtering and sorting
- [ ] Memory importance scoring
- [ ] Automatic memory consolidation

## License

Same as parent project (AGPL-3.0)
