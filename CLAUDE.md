# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an anime recommendation AI agent built in Python that uses SQLite for data storage and integrates with multiple external services via Model Context Protocol (MCP). The system combines traditional database queries with LLM-driven natural language query generation.

## Environment Setup

The project uses `uv` for package management. Set up the environment:

```powershell
# Install uv (Windows)
irm https://astral.sh/uv/install.ps1 | iex

# Create and activate virtual environment
uv venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r requirements.txt
```

## Core Architecture

### Database Layer
- **SQLite Database**: `anime_database.db` stores anime metadata including titles, ratings, genres (JSON), platforms (JSON), and synopsis
- **Schema Management**: `utils/database/create_schema.py` handles database initialization and schema migrations
- **Data Import**: `utils/database/import_single_csv.py` for importing anime data from CSV files

### LLM Integration
- **Lemonade Server Client**: `models/client.py` provides OpenAI-compatible client for local LLM server
- **Configuration**: `config.py` and `.env` manage server endpoints and API keys
- **Default Model**: Qwen-2.5-7B-Instruct-NPU

### MCP (Model Context Protocol) Integration

The project integrates multiple MCP servers for different functionalities:

#### Web Search (Brave Search)
- **Location**: `mcp_web_search/`
- **Main Script**: `test_brave_search.py`
- **Functionality**: Web search with automatic text file saving and AI-powered question answering
- **Key Feature**: Handles both JSON and plain text response formats from Brave Search MCP server

#### SQLite Database Access
- **Location**: `mcp_sqlite/`
- **Traditional Approach**: `test_sqlite.py` - Uses hardcoded SQL queries
- **LLM-Driven Approach**: `test_sqlite_llm.py` - Uses LLM to generate SQL queries from natural language

## Key Commands

### Database Operations
```bash
# Create/migrate database schema
python utils/database/create_schema.py

# Import anime data from CSV
python utils/database/import_single_csv.py
```

### MCP Server Operations

**Install MCP servers** (required for database and web search functionality):
```bash
# SQLite MCP server
uvx mcp-server-sqlite --help

# Install Brave Search MCP server (if not already available)
# Check project documentation for specific installation instructions
```

### Testing and Development

**Test Lemonade Server connection**:
```bash
python models/client.py
```

**Test traditional SQLite MCP queries**:
```bash
# Run all examples
python mcp_sqlite/test_sqlite.py

# Search specific genre with limit
python mcp_sqlite/test_sqlite.py 奇幻 5
```

**Test LLM-driven SQLite queries**:
```bash
# Run example queries
python mcp_sqlite/test_sqlite_llm.py

# Interactive mode
python mcp_sqlite/test_sqlite_llm.py --interactive

# Single query
python mcp_sqlite/test_sqlite_llm.py "找出評分最高的5部奇幻動漫"
```

**Test web search functionality**:
```bash
# Basic search
python mcp_web_search/test_brave_search.py

# Custom search
python mcp_web_search/test_brave_search.py "your search query"
```

**Debug MCP connections**:
```bash
# Test SQLite MCP server connection
python mcp_sqlite/debug_sqlite.py

# Debug MCP response formats
python mcp_sqlite/debug_mcp_format.py

# Debug web search MCP
python mcp_web_search/debug_brave_search.py
```

## Important Technical Details

### MCP Response Parsing
- SQLite MCP server returns Python dictionary format strings, not JSON
- Use `ast.literal_eval()` as fallback when `json.loads()` fails
- Web search MCP may return either JSON or plain text format

### LLM SQL Generation System
The `test_sqlite_llm.py` implements a sophisticated natural language to SQL conversion system:

- **System Prompt Generation**: Creates detailed database schema descriptions for the LLM
- **Safety Checks**: Prevents dangerous SQL operations (DROP, DELETE, UPDATE, etc.)
- **Natural Language Processing**: Converts queries like "找出評分最高的5部奇幻動漫" to appropriate SQL
- **MCP Tool Integration**: Uses MCP server tools (`read_query`, `list_tables`, `describe_table`)

### Environment Variables
Required environment variables in `.env`:
```
LEMONADE_BASE_URL=http://192.168.1.10:8000/api/v1
LEMONADE_API_KEY=lemonade
DEFAULT_MODEL=Qwen-2.5-7B-Instruct-NPU
BRAVE_API_KEY=your-brave-api-key
```

## Development Workflow

### Git Branching Strategy
- Main branch: `main` (stable, deployable)
- Feature branches: short-lived, merged via PR or direct merge
- Use `git rebase` for linear history or `git merge --no-ff` for merge commits

### Adding New Features
1. Create feature branch: `git checkout -b feature/<description>`
2. Implement and test changes
3. Update requirements.txt if new dependencies added: `uv pip freeze > requirements.txt`
4. Merge back to main using one of the documented merge strategies

## Common Issues and Solutions

### Unicode Encoding Issues
If encountering Unicode errors on Windows, set environment variable:
```powershell
$env:PYTHONIOENCODING="utf-8"
```

### MCP Server Installation
- Use `uvx` instead of `npm` for SQLite MCP server installation
- Ensure MCP dependencies are installed: `uv pip install mcp`

### Database Schema Updates
The schema management system automatically handles migrations, but manually run `create_schema.py` after major changes to ensure consistency.