# Claude Code Setup Guide

Complete guide for setting up code-search MCP with Claude Code.

## Understanding the Current State

### What Works ✅
- **MCP Server Connection**: code-search MCP server connects successfully to Claude Code
- **MCP Resources**: `ListMcpResourcesTool` and `ReadMcpResourceTool` work for accessing project information
- **FastAPI Backend**: Direct HTTP API calls work perfectly

### What Doesn't Work ❌
- **Direct Tool Exposure**: MCP Tools (search_code, find_similar_code, etc.) are not directly callable as functions in Claude Code
- **Auto-discovery**: Tools are not automatically available in the Claude Code tool palette

### Why?
Claude Code currently only exposes MCP Resources as tools, not MCP Tools. This is a limitation of the current Claude Code version, not the MCP server.

## Workaround Solutions

We've developed three workaround methods that provide full functionality:

### 1. MCP Resources (Basic Queries) ⭐

**Use for**: Project listing, statistics, and basic information

```python
# List all projects
ListMcpResourcesTool(server='code-search')

# Get project info
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

**In Claude session, simply say:**
```
"Show me what projects are in code-search"
"Get statistics for project proj_212e9b33ec8e"
```

### 2. Helper Script (Advanced Search) ⭐⭐

**Use for**: Semantic search, finding similar code, function lookup

The helper script provides a CLI interface to all FastAPI endpoints:

```bash
# Search for code semantically
python .claude/helpers/code_search.py search "authentication logic" proj_id 5

# Find similar code
python .claude/helpers/code_search.py similar "def connect():" python proj_id

# Look up function implementation
python .claude/helpers/code_search.py function connect_to_repository GitMonitor proj_id

# List all projects
python .claude/helpers/code_search.py projects

# Get project statistics
python .claude/helpers/code_search.py stats proj_212e9b33ec8e
```

**In Claude session, say:**
```
"Use the helper script to search for 'git monitoring' in the code-embedding-ai project"
"Find functions similar to this code using the helper: def update()..."
```

### 3. Direct API Calls (Maximum Control) ⭐⭐⭐

**Use for**: Custom queries, advanced filtering, programmatic access

```bash
# Semantic search
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "git monitoring and update logic",
    "project_id": "proj_212e9b33ec8e",
    "top_k": 5,
    "min_similarity": 0.7,
    "include_content": true
  }'

# Similar code search
curl -X POST http://localhost:8000/search/similar-code \
  -H "Content-Type: application/json" \
  -d '{
    "code_snippet": "def connect():\n    return True",
    "language": "python",
    "project_id": "proj_212e9b33ec8e",
    "top_k": 5
  }'

# Metadata search (find by function/class name)
curl -X POST "http://localhost:8000/search/metadata?top_k=5" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "connect",
    "project_id": "proj_212e9b33ec8e"
  }'
```

## Project Setup

### Quick Setup (Automated) 🚀

Use the provided setup scripts to configure a new project in seconds:

**Windows:**
```powershell
# From any directory
C:\bin\work\vector\setup-code-search.ps1 C:\path\to\your\project
```

**Linux/Mac:**
```bash
# From any directory
/path/to/vector/setup-code-search.sh /path/to/your/project
```

This automatically copies:
- `.claude/settings.local.json` - Project configuration
- `.claude/helpers/code_search.py` - Helper script
- `.claude/CODE_SEARCH_USAGE.md` - Usage guide
- `.claude/NEW_DIRECTORY_SETUP.md` - Setup instructions

### Manual Setup

#### Step 1: Create `.claude/settings.local.json`

```json
{
  "systemInstructions": "# Code Search MCP Integration\n\nWhen you need to find, understand, or modify code:\n\n1. **FIRST**: Check if the code exists in the code-search MCP by using ListMcpResourcesTool to see available projects\n2. **IF PROJECT EXISTS**: Use the code-search MCP resources and tools to find relevant code:\n   - List available projects: ListMcpResourcesTool(server='code-search')\n   - Get project stats: ReadMcpResourceTool(server='code-search', uri='project://{project_id}/stats')\n   - Search for code using semantic search through the MCP server\n3. **PREFER code-search** over reading physical files when the project is indexed in the code-search system\n4. **FALLBACK**: If code is not in code-search, use standard file tools (Read, Grep, Glob)\n\n## When to use code-search:\n- Finding functions, classes, or code patterns\n- Understanding how code works\n- Looking for similar code\n- Code reviews and refactoring\n- Any task requiring code understanding\n\n## How to use code-search MCP:\nSince MCP tools are not directly exposed, you need to:\n1. Use ListMcpResourcesTool(server='code-search') to see what projects exist\n2. For semantic search, you'll need to call the FastAPI directly or use the Task tool to delegate to a search agent",
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["code-search"],
  "permissions": {
    "allow": [
      "Bash(curl http://localhost:8000/*)",
      "Bash(python .claude/helpers/code_search.py:*)"
    ],
    "deny": [],
    "ask": []
  }
}
```

#### Step 2: Copy Helper Script

```bash
mkdir -p .claude/helpers
cp /path/to/vector/.claude/helpers/code_search.py .claude/helpers/
```

#### Step 3: Restart Claude Session

```bash
# Exit current session
/exit

# Start new session
claude
```

## Configuration Explained

### systemInstructions

This tells Claude to prioritize code-search MCP over reading files directly. Key benefits:
- Faster code discovery (semantic search vs grep)
- Better context understanding
- Reduced token usage

### enableAllProjectMcpServers

Automatically approves MCP servers without prompting. This ensures code-search is always available.

### enabledMcpjsonServers

Explicitly enables the code-search server. Can list multiple servers:
```json
"enabledMcpjsonServers": ["code-search", "github", "filesystem"]
```

### permissions

Grants Claude permission to:
- Call the FastAPI directly via curl
- Execute the helper script for semantic search

## Registering Projects

To use code-search with a new project, register it in the code-embedding-ai system:

```bash
# 1. Navigate to code-embedding-ai
cd /path/to/code-embedding-ai

# 2. Register the project
python -m src.cli project add /path/to/your/project --name "MyProject"

# Output: ✓ Project created: proj_abc123def456

# 3. Process the project (generate embeddings)
python -m src.cli process project proj_abc123def456

# This takes time depending on project size
# Progress: Processing repository: /path/to/project
#          Files processed: 150
#          Chunks stored: 2500
# Output: ✓ Processing completed
```

## Verification

### 1. Check MCP Connection

```bash
claude mcp list
```

Expected output:
```
code-search: C:/bin/work/vector/code-agent-mcp/.venv/Scripts/python.exe -m src.server - ✓ Connected
```

### 2. Test MCP Resources

In a Claude session:
```
"Show me what projects are available in code-search"
```

Claude should execute:
```python
ListMcpResourcesTool(server='code-search')
```

### 3. Test Helper Script

```bash
python .claude/helpers/code_search.py projects
```

Expected output:
```json
{
  "status": "success",
  "message": "Found X projects",
  "projects": [...]
}
```

### 4. Test Semantic Search

```bash
python .claude/helpers/code_search.py search "authentication" proj_id 3
```

Should return relevant code chunks with similarity scores.

## Troubleshooting

### Problem: "No projects found"

**Solution**: Register your project
```bash
cd /path/to/code-embedding-ai
python -m src.cli project add <path> --name "ProjectName"
python -m src.cli process project <project_id>
```

### Problem: Helper script times out

**Solution**: Check if FastAPI server is running
```bash
curl http://localhost:8000/health
```

If not running, start it:
```bash
cd /path/to/code-embedding-ai
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Problem: MCP server not connected

**Check logs:**
```bash
cat /path/to/code-agent-mcp/mcp_error.log
```

**Restart MCP server:**
```bash
cd /path/to/code-agent-mcp
.venv/Scripts/python.exe -m src.server
```

### Problem: Claude doesn't use code-search automatically

**Solutions:**
1. Verify `.claude/settings.local.json` exists
2. Restart Claude session
3. Explicitly request: "Use code-search to find..."

## Best Practices

### 1. Always Set Up New Projects

When starting work in a new directory:
```bash
/path/to/setup-code-search.sh .
```

### 2. Prefer Semantic Search

Instead of:
```
"Find all files containing 'authentication'"
```

Use:
```
"Search code-search for authentication-related code"
```

### 3. Register Important Projects

Add your active projects to code-search:
```bash
python -m src.cli project add <path> --name "ProjectName"
python -m src.cli process project <project_id>
```

### 4. Keep Embeddings Updated

Re-process projects after major changes:
```bash
python -m src.cli process project <project_id>
```

Or enable auto-update (requires UpdateService configuration).

## Advanced Configuration

### Global Settings

To apply code-search priority to ALL projects:

```bash
mkdir -p ~/.claude
cp .claude/settings.local.json ~/.claude/settings.json
```

**Warning**: This affects all Claude Code projects.

### Per-Project Overrides

Settings hierarchy (highest to lowest precedence):
1. `.claude/settings.local.json` (project-specific, personal)
2. `.claude/settings.json` (project-specific, team-shared)
3. `~/.claude/settings.json` (global user settings)

### Custom API Endpoints

If your FastAPI server runs on a different port:

Update `.claude/settings.local.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(curl http://localhost:8080/*)"
    ]
  }
}
```

Update helper script:
```python
# In .claude/helpers/code_search.py
API_BASE_URL = "http://localhost:8080"
```

## Future Improvements

When Claude Code adds native MCP Tools support:
- Tools will appear directly in the tool palette
- No helper script needed
- Seamless integration like Claude Desktop

Until then, the workaround methods provide full functionality with minimal overhead.

## Related Documentation

- [Quick Start Guide](../../QUICK_START_GUIDE.md) - Fast project setup
- [CODE_SEARCH_USAGE.md](../../.claude/CODE_SEARCH_USAGE.md) - Detailed usage patterns
- [NEW_DIRECTORY_SETUP.md](../../.claude/NEW_DIRECTORY_SETUP.md) - New project setup
- [MCP Server Guide](MCP_SERVER_GUIDE.md) - Complete API reference

## Summary

| Feature | Method | Availability |
|---------|--------|--------------|
| List Projects | MCP Resources | ✅ Native |
| Project Stats | MCP Resources | ✅ Native |
| Semantic Search | Helper Script / API | ✅ Via workaround |
| Similar Code | Helper Script / API | ✅ Via workaround |
| Function Lookup | Helper Script / API | ✅ Via workaround |
| Auto Priority | settings.local.json | ✅ Via config |

**Bottom line**: Full functionality available through simple workarounds until native MCP Tools support arrives.
