# MCP Server Guide

Complete guide to the code-embedding-ai MCP server architecture and usage.

## Architecture Overview

```
AI Client (Claude/LangGraph/etc)
    ↓ MCP Protocol (stdio/SSE)
MCP Server (this project)
    ↓ HTTP (httpx)
FastAPI Server (code-embedding-ai)
    ↓
ChromaDB + Vector Embeddings
```

## MCP Protocol

The server implements the Model Context Protocol (MCP) specification, providing:

- **Tools**: Callable functions that AI agents can invoke
- **Resources**: Read-only data sources (project information)
- **Prompts**: Pre-defined prompt templates for common tasks

### Communication

- **Transport:** stdio (standard input/output)
- **Format:** JSON-RPC 2.0
- **Async:** All operations are asynchronous

## Tools

### 1. search_code

**Description:** Semantic code search using natural language

**Parameters:**
```json
{
  "query": "string (required)",
  "project_id": "string (optional)",
  "top_k": "number (optional, default: 10)",
  "min_similarity": "number (optional, default: 0.7)"
}
```

**Example:**
```json
{
  "name": "search_code",
  "arguments": {
    "query": "user authentication logic",
    "top_k": 5,
    "min_similarity": 0.75
  }
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Found 5 results:\n\n**src/auth/login.py** (lines 12-45, similarity: 0.89)\nType: function\n```python\ndef authenticate_user(...):\n    ...\n```"
}
```

### 2. find_similar_code

**Description:** Find code snippets similar to a given code

**Parameters:**
```json
{
  "code_snippet": "string (required)",
  "language": "string (required)",
  "project_id": "string (optional)",
  "top_k": "number (optional, default: 5)"
}
```

**Use Cases:**
- Finding code duplicates
- Identifying refactoring opportunities
- Discovering similar patterns

**Example:**
```json
{
  "name": "find_similar_code",
  "arguments": {
    "code_snippet": "def calculate_total(items):\n    return sum(item.price for item in items)",
    "language": "python"
  }
}
```

### 3. get_function_implementation

**Description:** Find function implementation by name

**Parameters:**
```json
{
  "function_name": "string (required)",
  "class_name": "string (optional)",
  "project_id": "string (optional)"
}
```

**Example:**
```json
{
  "name": "get_function_implementation",
  "arguments": {
    "function_name": "process_payment",
    "class_name": "PaymentService"
  }
}
```

### 4. list_projects

**Description:** List all registered projects

**Parameters:** None

**Example:**
```json
{
  "name": "list_projects",
  "arguments": {}
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Registered projects (2):\n\n- **Frontend** (ID: proj_abc123)\n  Path: /path/to/frontend\n- **Backend** (ID: proj_def456)\n  Path: /path/to/backend"
}
```

### 5. get_project_stats

**Description:** Get project statistics

**Parameters:**
```json
{
  "project_id": "string (required)"
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Project Statistics:\n- Total chunks: 1234\n- Total files: 89\n- Languages: python, javascript\n- Chunk types: function, class, import"
}
```

## Resources

Resources provide read-only access to project data via URI patterns.

### Project Information

**URI:** `project://{project_id}`

**Description:** Get project metadata

**Response:**
```json
{
  "id": "proj_abc123",
  "name": "Frontend",
  "path": "/path/to/frontend",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-15T12:00:00"
}
```

### Project Statistics

**URI:** `project://{project_id}/stats`

**Description:** Get detailed project statistics

**Response:**
```json
{
  "total_chunks": 1234,
  "total_files": 89,
  "languages": ["python", "javascript", "typescript"],
  "chunk_types": ["function", "class", "import", "variable"],
  "file_extensions": [".py", ".js", ".ts"],
  "avg_chunk_size": 145
}
```

## Prompts

Pre-defined prompt templates that automatically gather relevant code context.

### 1. code-review

**Arguments:**
- `code_query` (required): Description of code to review
- `project_id` (optional): Project to search in

**Usage:**
```json
{
  "name": "code-review",
  "arguments": {
    "code_query": "authentication middleware"
  }
}
```

**What it does:**
1. Searches for relevant code
2. Constructs a detailed review prompt
3. Provides structured review checklist

### 2. refactor-code

**Arguments:**
- `code_snippet` (required): Code to refactor
- `language` (required): Programming language
- `project_id` (optional): Project context

**What it does:**
1. Finds similar code patterns
2. Identifies duplication opportunities
3. Suggests design patterns and improvements

### 3. fix-bug

**Arguments:**
- `bug_description` (required): Description of the bug
- `project_id` (optional): Project to search in

**What it does:**
1. Searches for related code
2. Constructs debugging prompt
3. Provides root cause analysis framework

### 4. write-tests

**Arguments:**
- `function_or_class` (required): Name of function/class
- `project_id` (optional): Project to search in

**What it does:**
1. Finds the implementation
2. Suggests test cases
3. Provides testing framework

### 5. explain-code

**Arguments:**
- `code_description` (required): What to explain
- `project_id` (optional): Project to search in

**What it does:**
1. Finds relevant code
2. Constructs explanation prompt
3. Provides structured explanation framework

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

### Environment Variables

- `API_BASE_URL`: Override API base URL (default: `http://localhost:8000`)
- `LOG_LEVEL`: Override logging level (default: `INFO`)

## Error Handling

All tools handle errors gracefully and return error messages:

```json
{
  "type": "text",
  "text": "Error executing tool 'search_code': Connection refused to localhost:8000"
}
```

Common errors:
- **Connection refused**: FastAPI server not running
- **Project not found**: Invalid project ID
- **No results found**: Query didn't match any code
- **Timeout**: Query took too long (increase timeout in config)

## Performance

### Response Times

Typical response times (depends on codebase size):

- `search_code`: 100-500ms
- `find_similar_code`: 150-600ms
- `get_function_implementation`: 50-200ms
- `list_projects`: 10-50ms
- `get_project_stats`: 20-100ms

### Optimization Tips

1. **Use project_id filter**: Narrow searches to specific projects
2. **Adjust top_k**: Request fewer results for faster responses
3. **Increase min_similarity**: Filter out low-quality matches
4. **Use local embeddings**: Avoid API latency (see code-embedding-ai setup)

## Development

### Running the Server

```bash
# Development mode
cd code-agent-mcp
python -m src.server

# The server reads from stdin and writes to stdout
# Use with MCP clients that support stdio transport
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Test specific tool
pytest tests/test_mcp_server.py::test_search_code
```

### Logging

Enable debug logging:

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "json"
  }
}
```

Logs include:
- Tool invocations
- API calls
- Response times
- Errors and stack traces

## Integration Examples

See `examples/` directory for:
- `claude_code_integration.py`: Using with Claude Code
- `langgraph_integration.py`: LangChain/LangGraph integration

## API Client

The `FastAPIClient` class (`src/api_client.py`) provides async methods for communicating with the FastAPI backend:

```python
from src.api_client import FastAPIClient

client = FastAPIClient(base_url="http://localhost:8000")

# Semantic search
results = await client.search_semantic(
    query="authentication logic",
    top_k=10
)

# Similar code
results = await client.find_similar_code(
    code_snippet="def login(...):\n    ...",
    language="python"
)

# Metadata search
results = await client.search_by_metadata(
    filters={"chunk_type": "function", "name": "login"}
)

# Projects
projects = await client.list_projects()
stats = await client.get_project_stats(project_id="proj_123")

# Cleanup
await client.close()
```

## Security

- **Local only**: Server only connects to localhost
- **No external requests**: All operations are local
- **No data sharing**: Code stays on your machine
- **stdio transport**: Secure local communication

## Limitations

- **Single FastAPI instance**: Only supports one backend server
- **No authentication**: Assumes trusted local environment
- **Synchronous backend calls**: Sequential API requests (could be parallelized)
- **No caching**: Each request hits the API (could add caching layer)

## Roadmap

Future improvements:
- Request caching for repeated queries
- Parallel API calls for better performance
- Streaming responses for large results
- Multi-backend support
- Authentication/authorization
- Metrics and monitoring

## Support

For issues and questions:
- GitHub Issues: [code-embedding-ai](https://github.com/your-org/code-embedding-ai)
- Documentation: See `docs/` directory
- Examples: See `examples/` directory
