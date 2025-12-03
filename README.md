# Code Embedding AI - MCP Server

MCP (Model Context Protocol) server for AI-powered code search and analysis using vector embeddings.

## Overview

This MCP server provides AI agents with efficient access to large codebases through vector-based semantic search, reducing token usage by ~99% and improving response times by 10x.

### Value Proposition

```
Traditional approach: Read entire codebase → 500K tokens → 5 minutes
MCP approach:        Vector search        → 5K tokens   → 0.5 seconds
```

**Result:** 99% token reduction + 10x speed improvement

## Features

### Tools
- **search_code**: Semantic code search using natural language
- **find_similar_code**: Find code duplicates and refactoring opportunities
- **get_function_implementation**: Quick function lookup by name
- **list_projects**: List all registered projects
- **get_project_stats**: Get project statistics (files, chunks, languages)

### Resources
- **project://{id}**: Access project information
- **project://{id}/stats**: Access project statistics

### Prompts
- **code-review**: Automated code review with context
- **refactor-code**: Refactoring suggestions with similar code patterns
- **fix-bug**: Debug assistance with relevant code context
- **write-tests**: Test generation with implementation context
- **explain-code**: Code explanation with full context

### Platform Support
- **Claude Desktop**: Native MCP integration
- **Claude Code**: MCP SDK integration
- **LangGraph**: LangChain tool adapter
- **REST API**: Direct HTTP access fallback

## Quick Start

### 1. Prerequisites

- Python 3.10+
- code-embedding-ai FastAPI server running on `localhost:8000`

### 2. Installation

```bash
cd code-agent-mcp
pip install -r requirements.txt
```

### 3. Start FastAPI Server

```bash
cd ../code-embedding-ai
python -m src.cli server start --host localhost --port 8000
```

### 4. Register a Project

```bash
python -m src.cli project add /path/to/your/project --name "MyProject"
python -m src.cli process project <project_id>
```

### 5. Run MCP Server

```bash
cd ../code-agent-mcp
python -m src.server
```

The server will run in stdio mode, ready for MCP client connections.

## Configuration

### mcp_config.json

```json
{
  "server": {
    "name": "code-embedding-ai",
    "version": "1.0.0",
    "description": "MCP server for AI-powered code search"
  },
  "api": {
    "base_url": "http://localhost:8000",
    "timeout": 30
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

**Configuration Options:**
- `api.base_url`: FastAPI server URL (default: `http://localhost:8000`)
- `api.timeout`: Request timeout in seconds (default: 30)
- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `logging.format`: Log format (json, text)

## Important: Claude Code Integration

### MCP Tools Exposure in Claude Code

**Current Limitation**: MCP Tools (search_code, find_similar_code, etc.) are **not directly exposed** as callable functions in Claude Code. Only Resources are accessible via `ListMcpResourcesTool` and `ReadMcpResourceTool`.

### Workaround Solutions

#### 1. Use MCP Resources (Basic)

```python
# List available projects
ListMcpResourcesTool(server='code-search')

# Get project information
ReadMcpResourceTool(
    server='code-search',
    uri='project://proj_212e9b33ec8e'
)

# Get project statistics
ReadMcpResourceTool(
    server='code-search',
    uri='project://proj_212e9b33ec8e/stats'
)
```

#### 2. Direct FastAPI Calls (Advanced)

Use the helper script provided in `.claude/helpers/code_search.py`:

```bash
# Search code
python .claude/helpers/code_search.py search "authentication logic" proj_id 5

# Find similar code
python .claude/helpers/code_search.py similar "def connect():" python

# Get function implementation
python .claude/helpers/code_search.py function connect GitMonitor

# List projects
python .claude/helpers/code_search.py projects

# Get stats
python .claude/helpers/code_search.py stats proj_212e9b33ec8e
```

#### 3. Project Configuration

To enable code-search priority in Claude Code projects:

1. **Copy configuration files** to your project:
   ```bash
   # Windows
   .\setup-code-search.ps1 C:\path\to\your\project

   # Linux/Mac
   ./setup-code-search.sh /path/to/your/project
   ```

2. **Or manually create** `.claude/settings.local.json`:
   ```json
   {
     "systemInstructions": "When finding or modifying code, FIRST check code-search MCP using ListMcpResourcesTool...",
     "enableAllProjectMcpServers": true,
     "enabledMcpjsonServers": ["code-search"],
     "permissions": {
       "allow": [
         "Bash(curl http://localhost:8000/*)",
         "Bash(python .claude/helpers/code_search.py:*)"
       ]
     }
   }
   ```

See [QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md) for detailed setup instructions.

---

## Usage Examples

### Claude Desktop

Configure in `claude_desktop_config.json`:

**Using virtual environment (Recommended):**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "/path/to/code-agent-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/path/to/code-agent-mcp"
      }
    }
  }
}
```

**Using system Python:**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/code-agent-mcp"
      }
    }
  }
}
```

Then in Claude Desktop:
```
Find all authentication-related code in my project
```

### Claude Code

**Setup for new projects:**

```bash
# Quick setup (automated)
cd /path/to/your/project
/path/to/vector/setup-code-search.sh .

# Or copy configuration manually
mkdir -p .claude/helpers
cp /path/to/vector/.claude/settings.local.json .claude/
cp /path/to/vector/.claude/helpers/code_search.py .claude/helpers/
```

**Using in Claude Code sessions:**

Since MCP Tools are not directly exposed, use one of these methods:

```bash
# Method 1: MCP Resources (basic queries)
# In Claude session, say:
"List projects in code-search"
# Claude will use: ListMcpResourcesTool(server='code-search')

# Method 2: Helper script (advanced search)
# In Claude session, say:
"Search for 'authentication logic' in code using the helper script"
# Claude will run: python .claude/helpers/code_search.py search "..." proj_id

# Method 3: Direct API call
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "project_id": "proj_id", "top_k": 5}'
```

**Programmatic usage (MCP SDK):**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "src.server"],
    cwd="/path/to/code-agent-mcp"
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Search for code
        result = await session.call_tool(
            "search_code",
            {"query": "user authentication", "top_k": 5}
        )
        print(result.content[0].text)
```

### LangGraph

```python
from examples.langgraph_integration import SearchCodeTool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

tools = [SearchCodeTool(), FindSimilarCodeTool()]
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
agent = create_react_agent(llm, tools)

result = await agent.ainvoke({
    "messages": [("human", "Find authentication code and review it")]
})
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AI Clients                          │
│  Claude Desktop │ Claude Code │ LangGraph │ Custom App  │
└────────┬────────────────┬─────────────┬────────────┬────┘
         │                │             │            │
         │ MCP Protocol   │ MCP SDK     │ Adapter    │ REST API
         │                │             │            │
         ▼                ▼             ▼            ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server (stdio/SSE)                     │
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │   Tools      │  Resources   │   Prompts    │        │
│  └──────────────┴──────────────┴──────────────┘        │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (httpx)
                         ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Server (localhost:8000)               │
│  /search/semantic │ /search/similar-code │ /projects   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              ChromaDB + Embeddings                      │
│         (Local or API-based embeddings)                 │
└─────────────────────────────────────────────────────────┘
```

## Documentation

Comprehensive guides available:

- **[Quick Start Guide](../QUICK_START_GUIDE.md)**: Fast setup for new projects ⭐
- **[Claude Code Setup](docs/CLAUDE_CODE_SETUP.md)**: Complete Claude Code integration guide ⭐
- **[MCP Server Guide](docs/MCP_SERVER_GUIDE.md)**: Complete API reference and architecture
- **[Claude Desktop Setup](docs/CLAUDE_DESKTOP_SETUP.md)**: Step-by-step integration guide
- **[M2 Implementation Plan](M2_MCP_SERVER.md)**: Detailed development roadmap

Project-specific documentation (in `.claude/` after setup):

- **[CODE_SEARCH_USAGE.md](.claude/CODE_SEARCH_USAGE.md)**: Usage patterns and examples
- **[NEW_DIRECTORY_SETUP.md](.claude/NEW_DIRECTORY_SETUP.md)**: Setting up new projects

## Examples

See `examples/` directory:

- **[claude_code_integration.py](examples/claude_code_integration.py)**: Using with Claude Agent SDK
- **[langgraph_integration.py](examples/langgraph_integration.py)**: LangChain/LangGraph integration

## Testing

Run tests with pytest:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_mcp_server.py::TestAPIClient::test_search_semantic -v
```

## Troubleshooting

### Server won't start

1. Check Python version: `python --version` (requires 3.10+)
2. Check dependencies: `pip install -r requirements.txt`
3. Test server manually: `python -m src.server`

### Tools not working

1. Verify FastAPI server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check project registration:
   ```bash
   cd ../code-embedding-ai
   python -m src.cli project list
   ```

3. Process project if needed:
   ```bash
   python -m src.cli process project <project_id>
   ```

### Connection timeouts

- Increase timeout in `mcp_config.json`:
  ```json
  {"api": {"timeout": 60}}
  ```

- Check FastAPI server logs for errors

## Performance

### Response Times

Typical response times (varies by codebase size):

- `search_code`: 100-500ms
- `find_similar_code`: 150-600ms
- `get_function_implementation`: 50-200ms
- `list_projects`: 10-50ms
- `get_project_stats`: 20-100ms

### Optimization Tips

1. **Filter by project_id**: Narrow searches to specific projects
2. **Adjust top_k**: Request fewer results for faster responses
3. **Use min_similarity**: Filter low-quality matches
4. **Local embeddings**: Use local model to avoid API latency

## Security

- **Local only**: Server only connects to localhost
- **No external requests**: All operations are local
- **No data sharing**: Code never leaves your machine
- **stdio transport**: Secure local communication

## Development

### Project Structure

```
code-agent-mcp/
├── src/
│   ├── server.py           # MCP server main
│   ├── api_client.py       # FastAPI client
│   ├── config.py           # Configuration
│   └── __init__.py
├── tests/
│   └── test_mcp_server.py  # Unit tests
├── examples/
│   ├── claude_code_integration.py
│   └── langgraph_integration.py
├── docs/
│   ├── MCP_SERVER_GUIDE.md
│   └── CLAUDE_DESKTOP_SETUP.md
├── mcp_config.json         # Configuration
├── requirements.txt        # Dependencies
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest tests/ -v`
6. Submit a pull request

## Roadmap

Future improvements:

- [ ] Request caching for repeated queries
- [ ] Parallel API calls for performance
- [ ] Streaming responses for large results
- [ ] Multi-backend support
- [ ] Authentication/authorization
- [ ] Metrics and monitoring dashboard
- [ ] Git webhook integration for real-time updates

## License

MIT

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/code-embedding-ai/issues)
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory

## Related Projects

- **[code-embedding-ai](../code-embedding-ai)**: FastAPI backend with vector embeddings
- **[MCP Specification](https://github.com/modelcontextprotocol/specification)**: Official MCP protocol docs
