# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an anime recommendation AI agent built in Python that uses SQLite database for storing anime data and provides recommendations based on tags, ratings, and filters. The system integrates with a local Lemonade Server for AI model inference.

## Development Environment Setup

### Virtual Environment (using uv)
```bash
# Create virtual environment (if not exists)
uv venv .venv

# Activate virtual environment (Windows)
.\.venv\Scripts\Activate.ps1
# or
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Environment Configuration
The project uses `.env` file for configuration. Key environment variables:
- `LEMONADE_BASE_URL`: URL to the local Lemonade Server API
- `LEMONADE_API_KEY`: API key for authentication
- `DEFAULT_MODEL`: Default AI model to use (e.g., "Qwen-2.5-7B-Instruct-NPU")
- `BRAVE_API_KEY`: API key for Brave Search (web search functionality)

## Core Architecture

### Database Layer (`utils/database/`)
- **SQLite Database**: `anime_database.db` stores all anime information
- **Schema**: Anime table with fields: id, title, episodes, duration_minutes, genres (JSON), description, studio, source, demographic, rating, member_count, season
- **Database Creation**: Run `utils/database/create_database.py` to initialize database
- **Data Import**: Use `utils/database/import_data.py` to import CSV data from `raw_data/` directory

### AI Client Layer (`models/`)
- **LemonadeClient**: Wrapper around OpenAI client for local Lemonade Server
- **Configuration**: Loads settings from `config.py` which reads from `.env`
- **Usage**: Import `lemonade` instance from `models.client` for AI interactions

### Data Sources (`raw_data/`)
Contains seasonal anime CSV files (2024_fall.csv, 2024_spring.csv, etc.) with anime metadata including titles, ratings, genres, and technical details.

### MCP Integration
- **MCP Fetch** (`mcp_fetch/`): Model Context Protocol fetch functionality
- **MCP Web Search** (`mcp_web_search/`): Web search capabilities via Brave Search API
  - Uses Brave Search MCP server for web search functionality
  - Supports both web and local search types
  - Automatically saves search results to txt files
  - Integrates with Lemonade Server for intelligent question answering

## Common Development Commands

### Database Operations
```bash
# Initialize database and import all CSV data
python utils/database/import_data.py

# Create empty database structure only
python utils/database/create_database.py
```

### Testing AI Client
```bash
# Test Lemonade Server connection and model interaction
python models/client.py
```

### Web Search Operations
```bash
# Test Brave Search MCP connection
python mcp_web_search/debug_brave_search.py

# Perform web search with automatic txt saving and AI answering
python mcp_web_search/test_brave_search.py "your search query"

# Advanced search with custom parameters (query, count, offset, search_type)
python mcp_web_search/test_brave_search.py "AI news" 15 0 web

# Legacy SmartSearch testing (backup)
python mcp_web_search/debug_mcp.py
python mcp_web_search/test_web_search.py
```

### MCP Testing
```bash
# Test MCP fetch functionality
python mcp_fetch/test_mcp_client.py
```

## Key Files and Dependencies

### Dependencies (requirements.txt)
- `pandas==2.3.2`: Data manipulation for CSV processing
- `python-dotenv`: Environment variable management
- `mcp`: Model Context Protocol client library
- `openai`: OpenAI-compatible client for Lemonade Server integration

### Configuration Files
- `config.py`: Centralized configuration loading from environment variables
- `.env`: Environment-specific settings (not in git)

## Database Query Patterns

The system uses tag-based filtering with SQLite LIKE queries:
- Genres are stored as JSON strings in the database
- Query building uses dynamic WHERE clauses for multiple tag filtering
- Results are ordered by rating in descending order
- Supports LIMIT for controlling result count

## Web Search Integration

### Brave Search MCP Architecture
- **Primary Search Engine**: Uses Brave Search via MCP server (`@modelcontextprotocol/server-brave-search`)
- **Plain Text Parsing**: Brave Search returns results in plain text format, parsed by `parse_brave_plain_text()`
- **Automatic File Saving**: All search results are automatically saved to timestamped txt files in `mcp_web_search/`
- **AI-Powered Answering**: Qwen model analyzes search results and provides intelligent answers to user queries
- **Dual Search Types**: Supports both web search (`brave_web_search`) and local business search (`brave_local_search`)

### Search Workflow
1. Query submitted via command line
2. Brave Search MCP server called with search parameters
3. Plain text results parsed into structured format
4. Results displayed to user and saved to txt file
5. Top results sent to Qwen for intelligent question answering
6. Final answer displayed with source citations

## Development Notes

- The project uses Chinese comments and documentation in some files
- All paths should use the project root as the working directory
- Database operations include proper connection handling and error management
- The LemonadeClient provides both simple and complex chat interfaces for AI interactions
- Web search results are automatically archived in `mcp_web_search/` directory with descriptive filenames
- Qwen system prompt is optimized for analyzing web search results and providing accurate, cited answers