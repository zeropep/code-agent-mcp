# Claude Desktop Setup Guide

This guide explains how to integrate the code-embedding-ai MCP server with Claude Desktop.

## Prerequisites

- Claude Desktop installed
- Python 3.10+ installed
- code-embedding-ai FastAPI server running on `localhost:8000`

## Installation Steps

### 1. Install MCP Server Dependencies

**Option A: Using Virtual Environment (Recommended)**

```bash
cd code-agent-mcp
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Option B: System-wide Installation**

```bash
cd code-agent-mcp
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Claude Desktop reads MCP server configurations from a JSON file.

**Location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

**If using virtual environment (Recommended):**

```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "/absolute/path/to/code-agent-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/code-agent-mcp"
      }
    }
  }
}
```

**Windows Example:**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "C:/bin/work/vector/code-agent-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "C:/bin/work/vector/code-agent-mcp",
      "env": {
        "PYTHONPATH": "C:/bin/work/vector/code-agent-mcp"
      }
    }
  }
}
```

**macOS/Linux Example:**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "/Users/username/code-agent-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/username/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/Users/username/code-agent-mcp"
      }
    }
  }
}
```

**If using system-wide Python:**

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

**Important:**
- Replace paths with actual absolute paths to your `code-agent-mcp` directory
- For virtual environment setup, use the full path to the Python executable in `.venv`
- On Windows, use forward slashes (`/`) or escaped backslashes (`\\`) in JSON
- The virtual environment approach is recommended to avoid dependency conflicts

### 3. Start the FastAPI Server

Before using the MCP server, ensure the FastAPI backend is running:

```bash
cd ../code-embedding-ai
python -m src.cli server start --host localhost --port 8000
```

### 4. Restart Claude Desktop

After modifying the configuration file, restart Claude Desktop to load the MCP server.

## Verification

### Check MCP Server Status

1. Open Claude Desktop
2. Look for the MCP icon or server indicator in the UI
3. The `code-embedding-ai` server should appear as available

### Test Tools

Try using the MCP tools in a conversation:

```
Can you search for authentication-related code in my project?
```

Claude should use the `search_code` tool to find relevant code.

### Available Capabilities

Once configured, Claude Desktop can use:

**Tools:**
- `search_code` - Semantic code search
- `find_similar_code` - Find code duplicates
- `get_function_implementation` - Find function definitions
- `list_projects` - List registered projects
- `get_project_stats` - Project statistics

**Resources:**
- `project://{project_id}` - Project information
- `project://{project_id}/stats` - Project statistics

**Prompts:**
- `code-review` - Code review assistance
- `refactor-code` - Refactoring suggestions
- `fix-bug` - Bug fixing help
- `write-tests` - Test generation
- `explain-code` - Code explanation

## Troubleshooting

### Server Not Loading

1. **Check Python path:**
   ```bash
   which python  # macOS/Linux
   where python  # Windows
   ```
   Use the full path in the configuration if needed.

2. **Check logs:**
   - Claude Desktop logs are typically in the application's log directory
   - Look for MCP server initialization errors

3. **Test manually:**
   ```bash
   cd code-agent-mcp
   python -m src.server
   ```
   The server should start without errors.

### Tools Not Working

1. **Verify FastAPI server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check configuration:**
   - Ensure `base_url` in `mcp_config.json` matches your FastAPI server
   - Default is `http://localhost:8000`

3. **Check project registration:**
   - Projects must be registered in the FastAPI server first
   - Use the CLI to add projects:
     ```bash
     cd ../code-embedding-ai
     python -m src.cli project add /path/to/project
     ```

### Connection Timeouts

If you see timeout errors:

1. Increase timeout in `mcp_config.json`:
   ```json
   {
     "api": {
       "base_url": "http://localhost:8000",
       "timeout": 60
     }
   }
   ```

2. Check if the FastAPI server is responsive:
   ```bash
   curl -w "@-" http://localhost:8000/projects/
   ```

## Example Usage

### Code Search
```
User: Find all database connection code
Claude: [Uses search_code tool]
       Found 12 results with database connection logic...
```

### Code Review
```
User: Review the authentication logic
Claude: [Uses code-review prompt]
       Analyzing authentication code for security issues...
```

### Find Similar Code
```
User: Find code similar to this function: [paste code]
Claude: [Uses find_similar_code tool]
       Found 5 similar code patterns that could be refactored...
```

## Advanced Configuration

### Multiple Projects

To work with multiple projects, register them all in the FastAPI server:

```bash
python -m src.cli project add /path/to/project1 --name "Frontend"
python -m src.cli project add /path/to/project2 --name "Backend"
```

Then specify which project to search in your queries:

```
Search for user authentication in the Backend project
```

### Custom Logging

Configure logging level in `mcp_config.json`:

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "json"
  }
}
```

Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## Security Notes

- The MCP server runs locally and only connects to `localhost:8000`
- No external network requests are made
- Code is never sent to external services
- All vector embeddings are computed locally (if using local model)

## Next Steps

- Explore [MCP Server Guide](MCP_SERVER_GUIDE.md) for detailed API documentation
- See [LangGraph Integration](LANGGRAPH_INTEGRATION.md) for programmatic usage
- Check the [README](../README.md) for additional features
