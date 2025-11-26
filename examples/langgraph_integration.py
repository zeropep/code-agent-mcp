"""
Example: LangGraph Integration with code-embedding-ai MCP Server

This example shows how to use MCP tools as LangChain tools in LangGraph.
"""

import asyncio
from typing import Any, Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import httpx


# ============================================================================
# Direct API Client (for LangGraph - bypasses MCP protocol)
# ============================================================================

class CodeEmbeddingAPIClient:
    """
    Direct HTTP client for LangGraph integration.
    Bypasses MCP protocol and calls FastAPI directly.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_code(
        self,
        query: str,
        project_id: str = None,
        top_k: int = 10,
        min_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """Semantic code search"""
        response = await self.client.post(
            f"{self.base_url}/search/semantic",
            json={
                "query": query,
                "project_id": project_id,
                "top_k": top_k,
                "min_similarity": min_similarity,
                "include_content": True
            }
        )
        response.raise_for_status()
        return response.json()

    async def find_similar_code(
        self,
        code_snippet: str,
        language: str,
        project_id: str = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Find similar code"""
        response = await self.client.post(
            f"{self.base_url}/search/similar-code",
            json={
                "code_snippet": code_snippet,
                "language": language,
                "project_id": project_id,
                "top_k": top_k
            }
        )
        response.raise_for_status()
        return response.json()

    async def list_projects(self) -> Dict[str, Any]:
        """List projects"""
        response = await self.client.get(f"{self.base_url}/projects/")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close client"""
        await self.client.aclose()


# ============================================================================
# LangChain Tool Adapters
# ============================================================================

class SearchCodeInput(BaseModel):
    """Input schema for search_code tool"""
    query: str = Field(description="Search query (natural language or code description)")
    project_id: str = Field(None, description="Optional project ID to search in")
    top_k: int = Field(10, description="Maximum number of results")
    min_similarity: float = Field(0.7, description="Minimum similarity score (0.0-1.0)")


class SearchCodeTool(BaseTool):
    """LangChain tool for semantic code search"""

    name: str = "search_code"
    description: str = "Search codebase using semantic search with natural language queries"
    args_schema: type[BaseModel] = SearchCodeInput
    api_client: CodeEmbeddingAPIClient = Field(default_factory=CodeEmbeddingAPIClient)

    def _run(self, query: str, project_id: str = None, top_k: int = 10, min_similarity: float = 0.7) -> str:
        """Synchronous version (calls async)"""
        return asyncio.run(self._arun(query, project_id, top_k, min_similarity))

    async def _arun(
        self,
        query: str,
        project_id: str = None,
        top_k: int = 10,
        min_similarity: float = 0.7
    ) -> str:
        """Async execution"""
        result = await self.api_client.search_code(query, project_id, top_k, min_similarity)

        if not result.get("results"):
            return "No results found."

        # Format results
        formatted = [f"Found {len(result['results'])} results:\n"]
        for r in result["results"]:
            formatted.append(
                f"\n**{r['file_path']}** (lines {r['line_start']}-{r['line_end']}, "
                f"similarity: {r.get('similarity', 0):.2f})\n"
                f"Type: {r.get('chunk_type', 'unknown')}\n"
                f"```\n{r['content']}\n```"
            )

        return "\n".join(formatted)


class FindSimilarCodeInput(BaseModel):
    """Input schema for find_similar_code tool"""
    code_snippet: str = Field(description="Code snippet to find similar patterns")
    language: str = Field(description="Programming language (python, java, javascript, etc.)")
    project_id: str = Field(None, description="Optional project ID")
    top_k: int = Field(5, description="Maximum number of results")


class FindSimilarCodeTool(BaseTool):
    """LangChain tool for finding similar code"""

    name: str = "find_similar_code"
    description: str = "Find code similar to a given snippet (for refactoring/duplicate detection)"
    args_schema: type[BaseModel] = FindSimilarCodeInput
    api_client: CodeEmbeddingAPIClient = Field(default_factory=CodeEmbeddingAPIClient)

    def _run(self, code_snippet: str, language: str, project_id: str = None, top_k: int = 5) -> str:
        """Synchronous version"""
        return asyncio.run(self._arun(code_snippet, language, project_id, top_k))

    async def _arun(self, code_snippet: str, language: str, project_id: str = None, top_k: int = 5) -> str:
        """Async execution"""
        result = await self.api_client.find_similar_code(code_snippet, language, project_id, top_k)

        if not result.get("results"):
            return "No similar code found."

        formatted = [f"Found {len(result['results'])} similar code snippets:\n"]
        for r in result["results"]:
            formatted.append(
                f"\n**{r['file_path']}** (similarity: {r.get('similarity', 0):.2f})\n"
                f"```\n{r['content']}\n```"
            )

        return "\n".join(formatted)


class ListProjectsTool(BaseTool):
    """LangChain tool for listing projects"""

    name: str = "list_projects"
    description: str = "List all registered code projects"
    api_client: CodeEmbeddingAPIClient = Field(default_factory=CodeEmbeddingAPIClient)

    def _run(self) -> str:
        """Synchronous version"""
        return asyncio.run(self._arun())

    async def _arun(self) -> str:
        """Async execution"""
        result = await self.api_client.list_projects()

        if not result.get("projects"):
            return "No projects registered."

        formatted = [f"Registered projects ({len(result['projects'])}):\n"]
        for p in result["projects"]:
            formatted.append(f"- **{p['name']}** (ID: {p['id']})\n  Path: {p.get('path', 'N/A')}")

        return "\n".join(formatted)


# ============================================================================
# LangGraph Usage Example
# ============================================================================

async def langgraph_example():
    """
    Example showing how to use the tools in a LangGraph workflow
    """
    from langchain_anthropic import ChatAnthropic
    from langgraph.prebuilt import create_react_agent

    # Initialize tools
    tools = [
        SearchCodeTool(),
        FindSimilarCodeTool(),
        ListProjectsTool()
    ]

    # Create LLM (requires ANTHROPIC_API_KEY environment variable)
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    # Create agent with tools
    agent = create_react_agent(llm, tools)

    print("=" * 60)
    print("LangGraph Agent with Code Search Tools")
    print("=" * 60)

    # Example 1: List projects
    print("\n1. Listing projects...")
    result = await agent.ainvoke({
        "messages": [("human", "List all available code projects")]
    })
    print(result["messages"][-1].content)

    # Example 2: Search for code
    print("\n2. Searching for authentication code...")
    result = await agent.ainvoke({
        "messages": [("human", "Find all authentication-related code")]
    })
    print(result["messages"][-1].content)

    # Example 3: Complex task with multiple tools
    print("\n3. Complex task: Find and analyze authentication patterns...")
    result = await agent.ainvoke({
        "messages": [(
            "human",
            "First list the projects, then search for authentication code, "
            "and summarize what authentication patterns are used"
        )]
    })
    print(result["messages"][-1].content)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


# ============================================================================
# Simpler Example (without LangGraph)
# ============================================================================

async def simple_example():
    """
    Simple example using tools directly without LangGraph
    """
    print("=" * 60)
    print("Simple Tool Usage (without LangGraph)")
    print("=" * 60)

    # Initialize tools
    search_tool = SearchCodeTool()
    similar_code_tool = FindSimilarCodeTool()
    list_projects_tool = ListProjectsTool()

    # Example 1: List projects
    print("\n1. Listing projects...")
    result = await list_projects_tool._arun()
    print(result)

    # Example 2: Search code
    print("\n2. Searching for user authentication...")
    result = await search_tool._arun(
        query="user authentication",
        top_k=3
    )
    print(result)

    # Example 3: Find similar code
    print("\n3. Finding similar code...")
    code = """
def login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None
    """
    result = await similar_code_tool._arun(
        code_snippet=code,
        language="python",
        top_k=3
    )
    print(result)

    # Cleanup
    await search_tool.api_client.close()
    await similar_code_tool.api_client.close()
    await list_projects_tool.api_client.close()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Code Embedding AI - LangGraph Integration")
    print("=" * 60)
    print("\nRunning simple example (no LangGraph required)...")

    # Run simple example
    asyncio.run(simple_example())

    # Uncomment to run LangGraph example (requires langchain, langgraph, anthropic)
    # asyncio.run(langgraph_example())
