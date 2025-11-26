"""
Example: Using code-embedding-ai MCP server with Claude Code

This example shows how to use the MCP server programmatically
with the Claude Agent SDK (used by Claude Code).
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Main example function"""

    # Configure MCP server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
        cwd="/absolute/path/to/code-agent-mcp",  # Update this path
        env={"PYTHONPATH": "/absolute/path/to/code-agent-mcp"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            print("=" * 60)
            print("MCP Client Connected to code-embedding-ai")
            print("=" * 60)

            # Example 1: List available tools
            print("\n1. Listing available tools...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Example 2: List projects
            print("\n2. Listing projects...")
            result = await session.call_tool("list_projects", {})
            print(result.content[0].text)

            # Example 3: Search for code
            print("\n3. Searching for authentication code...")
            result = await session.call_tool(
                "search_code",
                {
                    "query": "user authentication",
                    "top_k": 3,
                    "min_similarity": 0.7
                }
            )
            print(result.content[0].text)

            # Example 4: Get function implementation
            print("\n4. Finding function implementation...")
            result = await session.call_tool(
                "get_function_implementation",
                {
                    "function_name": "authenticate_user"
                }
            )
            print(result.content[0].text)

            # Example 5: List resources
            print("\n5. Listing resources...")
            resources = await session.list_resources()
            print(f"Found {len(resources.resources)} resources:")
            for resource in resources.resources:
                print(f"  - {resource.name}: {resource.uri}")

            # Example 6: Read a resource
            if resources.resources:
                print("\n6. Reading first resource...")
                first_resource = resources.resources[0]
                content = await session.read_resource(first_resource.uri)
                print(f"Resource {first_resource.uri}:")
                print(content.contents[0].text[:200] + "...")

            # Example 7: List prompts
            print("\n7. Listing prompts...")
            prompts = await session.list_prompts()
            print(f"Found {len(prompts.prompts)} prompts:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")

            # Example 8: Get a prompt
            print("\n8. Getting code-review prompt...")
            prompt_result = await session.get_prompt(
                "code-review",
                {
                    "code_query": "authentication logic"
                }
            )
            print(f"Prompt: {prompt_result.description}")
            print(f"Message preview: {prompt_result.messages[0].content.text[:200]}...")

            print("\n" + "=" * 60)
            print("All examples completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    # Note: Update the server_params.cwd path above before running
    asyncio.run(main())
