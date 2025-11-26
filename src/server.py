"""
MCP Server for code-embedding-ai
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from typing import Any
import structlog
from .api_client import FastAPIClient
from .config import MCPConfig

logger = structlog.get_logger(__name__)

# 설정 로드
config = MCPConfig.from_file()

# MCP 서버 인스턴스 생성
app = Server("code-embedding-ai")

# API 클라이언트 인스턴스 (전역으로 유지)
api_client = FastAPIClient(base_url=config.api.base_url)


@app.list_tools()
async def list_tools():
    """사용 가능한 도구 목록"""
    return [
        {
            "name": "search_code",
            "description": "코드베이스에서 시맨틱 검색으로 관련 코드 찾기",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색 쿼리 (자연어 또는 코드 설명)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "프로젝트 ID (선택)"
                    },
                    "top_k": {
                        "type": "number",
                        "description": "반환할 최대 결과 수",
                        "default": 10
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "최소 유사도 (0.0-1.0)",
                        "default": 0.7
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "find_similar_code",
            "description": "특정 코드 스니펫과 유사한 코드 찾기 (리팩토링/중복 감지)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code_snippet": {
                        "type": "string",
                        "description": "비교할 코드 스니펫"
                    },
                    "language": {
                        "type": "string",
                        "description": "프로그래밍 언어 (java/kotlin/python 등)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "프로젝트 ID (선택)"
                    },
                    "top_k": {
                        "type": "number",
                        "description": "반환할 최대 결과 수",
                        "default": 5
                    }
                },
                "required": ["code_snippet", "language"]
            }
        },
        {
            "name": "get_function_implementation",
            "description": "함수 이름으로 구현 찾기",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "함수 이름"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "클래스 이름 (선택)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "프로젝트 ID (선택)"
                    }
                },
                "required": ["function_name"]
            }
        },
        {
            "name": "list_projects",
            "description": "등록된 프로젝트 목록 조회",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_project_stats",
            "description": "프로젝트 통계 조회 (청크 수, 파일 수, 언어 분포 등)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "프로젝트 ID"
                    }
                },
                "required": ["project_id"]
            }
        }
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[Any]:
    """도구 호출 핸들러"""
    try:
        if name == "search_code":
            # 시맨틱 코드 검색
            result = await api_client.search_semantic(
                query=arguments["query"],
                project_id=arguments.get("project_id"),
                top_k=arguments.get("top_k", 10),
                min_similarity=arguments.get("min_similarity", 0.7)
            )

            # 결과 포맷팅
            if result.get("results"):
                formatted_results = []
                for r in result["results"]:
                    formatted_results.append({
                        "file_path": r.get("file_path", ""),
                        "chunk_type": r.get("chunk_type", ""),
                        "content": r.get("content", ""),
                        "similarity": round(r.get("similarity", 0), 3),
                        "line_start": r.get("line_start"),
                        "line_end": r.get("line_end")
                    })

                return [{
                    "type": "text",
                    "text": f"Found {len(formatted_results)} results:\n\n" +
                           "\n\n".join([
                               f"**{r['file_path']}** (lines {r['line_start']}-{r['line_end']}, similarity: {r['similarity']})\n"
                               f"Type: {r['chunk_type']}\n```\n{r['content']}\n```"
                               for r in formatted_results
                           ])
                }]
            else:
                return [{"type": "text", "text": "No results found."}]

        elif name == "find_similar_code":
            # 유사 코드 검색
            result = await api_client.find_similar_code(
                code_snippet=arguments["code_snippet"],
                language=arguments["language"],
                project_id=arguments.get("project_id"),
                top_k=arguments.get("top_k", 5)
            )

            if result.get("results"):
                formatted_results = []
                for r in result["results"]:
                    formatted_results.append({
                        "file_path": r.get("file_path", ""),
                        "content": r.get("content", ""),
                        "similarity": round(r.get("similarity", 0), 3),
                        "line_start": r.get("line_start"),
                        "line_end": r.get("line_end")
                    })

                return [{
                    "type": "text",
                    "text": f"Found {len(formatted_results)} similar code snippets:\n\n" +
                           "\n\n".join([
                               f"**{r['file_path']}** (lines {r['line_start']}-{r['line_end']}, similarity: {r['similarity']})\n```\n{r['content']}\n```"
                               for r in formatted_results
                           ])
                }]
            else:
                return [{"type": "text", "text": "No similar code found."}]

        elif name == "get_function_implementation":
            # 함수 이름으로 검색
            function_name = arguments["function_name"]
            class_name = arguments.get("class_name")

            # 검색 쿼리 구성
            if class_name:
                query = f"class {class_name} function {function_name}"
            else:
                query = f"function {function_name}"

            # 메타데이터 필터로 함수 검색
            filters = {
                "chunk_type": "function",
                "name": function_name
            }
            if class_name:
                filters["class_name"] = class_name

            result = await api_client.search_by_metadata(
                filters=filters,
                top_k=5
            )

            if result.get("results"):
                formatted_results = []
                for r in result["results"]:
                    formatted_results.append({
                        "file_path": r.get("file_path", ""),
                        "content": r.get("content", ""),
                        "line_start": r.get("line_start"),
                        "line_end": r.get("line_end")
                    })

                return [{
                    "type": "text",
                    "text": f"Found {len(formatted_results)} implementations:\n\n" +
                           "\n\n".join([
                               f"**{r['file_path']}** (lines {r['line_start']}-{r['line_end']})\n```\n{r['content']}\n```"
                               for r in formatted_results
                           ])
                }]
            else:
                return [{"type": "text", "text": f"Function '{function_name}' not found."}]

        elif name == "list_projects":
            # 프로젝트 목록 조회
            result = await api_client.list_projects()

            if result.get("projects"):
                projects_text = "\n".join([
                    f"- **{p['name']}** (ID: {p['id']})\n  Path: {p.get('path', 'N/A')}"
                    for p in result["projects"]
                ])
                return [{
                    "type": "text",
                    "text": f"Registered projects ({len(result['projects'])}):\n\n{projects_text}"
                }]
            else:
                return [{"type": "text", "text": "No projects registered."}]

        elif name == "get_project_stats":
            # 프로젝트 통계 조회
            result = await api_client.get_project_stats(arguments["project_id"])

            stats_text = f"""Project Statistics:
- Total chunks: {result.get('total_chunks', 0)}
- Total files: {result.get('total_files', 0)}
- Languages: {', '.join(result.get('languages', []))}
- Chunk types: {', '.join(result.get('chunk_types', []))}
"""
            return [{"type": "text", "text": stats_text}]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error("Tool execution failed", tool=name, error=str(e))
        return [{
            "type": "text",
            "text": f"Error executing tool '{name}': {str(e)}"
        }]


@app.list_prompts()
async def list_prompts() -> list[dict]:
    """사용 가능한 프롬프트 템플릿 목록"""
    return [
        {
            "name": "code-review",
            "description": "Review code for quality, bugs, and improvements",
            "arguments": [
                {
                    "name": "code_query",
                    "description": "Description of the code to review (e.g., 'authentication logic', 'payment processing')",
                    "required": True
                },
                {
                    "name": "project_id",
                    "description": "Project ID to search in",
                    "required": False
                }
            ]
        },
        {
            "name": "refactor-code",
            "description": "Find code that needs refactoring and suggest improvements",
            "arguments": [
                {
                    "name": "code_snippet",
                    "description": "Code snippet to find similar patterns for refactoring",
                    "required": True
                },
                {
                    "name": "language",
                    "description": "Programming language",
                    "required": True
                },
                {
                    "name": "project_id",
                    "description": "Project ID to search in",
                    "required": False
                }
            ]
        },
        {
            "name": "fix-bug",
            "description": "Find relevant code to help fix a bug",
            "arguments": [
                {
                    "name": "bug_description",
                    "description": "Description of the bug",
                    "required": True
                },
                {
                    "name": "project_id",
                    "description": "Project ID to search in",
                    "required": False
                }
            ]
        },
        {
            "name": "write-tests",
            "description": "Find code that needs tests and suggest test cases",
            "arguments": [
                {
                    "name": "function_or_class",
                    "description": "Function or class name to write tests for",
                    "required": True
                },
                {
                    "name": "project_id",
                    "description": "Project ID to search in",
                    "required": False
                }
            ]
        },
        {
            "name": "explain-code",
            "description": "Find and explain how specific code works",
            "arguments": [
                {
                    "name": "code_description",
                    "description": "Description of the code to explain",
                    "required": True
                },
                {
                    "name": "project_id",
                    "description": "Project ID to search in",
                    "required": False
                }
            ]
        }
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> dict:
    """프롬프트 템플릿 가져오기"""
    try:
        if name == "code-review":
            code_query = arguments["code_query"]
            project_id = arguments.get("project_id")

            # 관련 코드 검색
            search_result = await api_client.search_semantic(
                query=code_query,
                project_id=project_id,
                top_k=5,
                min_similarity=0.7
            )

            code_sections = []
            if search_result.get("results"):
                for r in search_result["results"]:
                    code_sections.append(
                        f"File: {r['file_path']} (lines {r['line_start']}-{r['line_end']})\n```\n{r['content']}\n```"
                    )

            prompt_text = f"""You are conducting a code review for: {code_query}

Here is the relevant code found in the codebase:

{chr(10).join(code_sections) if code_sections else "No relevant code found."}

Please review this code for:
1. **Bugs and errors**: Identify any potential bugs or logical errors
2. **Code quality**: Assess readability, maintainability, and adherence to best practices
3. **Security**: Check for security vulnerabilities (SQL injection, XSS, etc.)
4. **Performance**: Suggest performance improvements
5. **Refactoring**: Recommend refactoring opportunities

Provide specific, actionable feedback."""

            return {
                "description": f"Code review for: {code_query}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "refactor-code":
            code_snippet = arguments["code_snippet"]
            language = arguments["language"]
            project_id = arguments.get("project_id")

            # 유사한 코드 검색
            similar_result = await api_client.find_similar_code(
                code_snippet=code_snippet,
                language=language,
                project_id=project_id,
                top_k=5
            )

            similar_sections = []
            if similar_result.get("results"):
                for r in similar_result["results"]:
                    similar_sections.append(
                        f"File: {r['file_path']} (similarity: {r.get('similarity', 0):.2f})\n```\n{r['content']}\n```"
                    )

            prompt_text = f"""You are refactoring the following code:

```{language}
{code_snippet}
```

Similar code patterns found in the codebase:

{chr(10).join(similar_sections) if similar_sections else "No similar code found."}

Please suggest refactoring improvements:
1. **DRY principle**: Identify code duplication and suggest extraction
2. **Design patterns**: Recommend applicable design patterns
3. **Naming**: Improve variable and function names
4. **Structure**: Suggest better code organization
5. **Consistency**: Ensure consistency with existing codebase patterns

Provide refactored code with explanations."""

            return {
                "description": f"Refactoring suggestions for {language} code",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "fix-bug":
            bug_description = arguments["bug_description"]
            project_id = arguments.get("project_id")

            # 버그 관련 코드 검색
            search_result = await api_client.search_semantic(
                query=f"bug: {bug_description}",
                project_id=project_id,
                top_k=5,
                min_similarity=0.6
            )

            code_sections = []
            if search_result.get("results"):
                for r in search_result["results"]:
                    code_sections.append(
                        f"File: {r['file_path']} (lines {r['line_start']}-{r['line_end']})\n```\n{r['content']}\n```"
                    )

            prompt_text = f"""You are debugging the following issue:

**Bug Description:** {bug_description}

Potentially relevant code:

{chr(10).join(code_sections) if code_sections else "No relevant code found. Try broadening the search."}

Please help fix this bug by:
1. **Root cause analysis**: Identify the likely cause of the bug
2. **Fix suggestion**: Provide a specific code fix
3. **Testing**: Suggest how to test the fix
4. **Prevention**: Recommend how to prevent similar bugs

Provide clear, actionable debugging steps and a proposed fix."""

            return {
                "description": f"Bug fix assistance for: {bug_description}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "write-tests":
            function_or_class = arguments["function_or_class"]
            project_id = arguments.get("project_id")

            # 함수/클래스 구현 검색
            search_result = await api_client.search_by_metadata(
                filters={"name": function_or_class},
                top_k=3
            )

            code_sections = []
            if search_result.get("results"):
                for r in search_result["results"]:
                    code_sections.append(
                        f"File: {r['file_path']}\n```\n{r['content']}\n```"
                    )

            prompt_text = f"""You are writing tests for: {function_or_class}

Implementation found:

{chr(10).join(code_sections) if code_sections else "Implementation not found. Please provide the code manually."}

Please write comprehensive tests:
1. **Unit tests**: Test individual functions/methods
2. **Edge cases**: Test boundary conditions and edge cases
3. **Error handling**: Test error scenarios
4. **Integration tests**: Test interaction with other components (if applicable)
5. **Test coverage**: Aim for high code coverage

Provide test code with clear assertions and descriptions."""

            return {
                "description": f"Test writing for: {function_or_class}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "explain-code":
            code_description = arguments["code_description"]
            project_id = arguments.get("project_id")

            # 코드 검색
            search_result = await api_client.search_semantic(
                query=code_description,
                project_id=project_id,
                top_k=3,
                min_similarity=0.7
            )

            code_sections = []
            if search_result.get("results"):
                for r in search_result["results"]:
                    code_sections.append(
                        f"File: {r['file_path']} (lines {r['line_start']}-{r['line_end']})\n```\n{r['content']}\n```"
                    )

            prompt_text = f"""Please explain how this code works: {code_description}

Code found:

{chr(10).join(code_sections) if code_sections else "Code not found. Try a different search query."}

Please provide a clear explanation covering:
1. **Purpose**: What does this code do?
2. **How it works**: Step-by-step explanation of the logic
3. **Key components**: Important functions, classes, and variables
4. **Dependencies**: What other code does this depend on?
5. **Usage**: How is this code used in the broader application?

Make the explanation accessible to developers unfamiliar with this code."""

            return {
                "description": f"Code explanation for: {code_description}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        else:
            raise ValueError(f"Unknown prompt: {name}")

    except Exception as e:
        logger.error("Failed to get prompt", prompt=name, error=str(e))
        raise


@app.list_resources()
async def list_resources() -> list[dict]:
    """사용 가능한 리소스 목록"""
    try:
        # 프로젝트 목록 가져오기
        projects_result = await api_client.list_projects()
        resources = []

        if projects_result.get("projects"):
            for project in projects_result["projects"]:
                project_id = project["id"]
                project_name = project["name"]

                # 각 프로젝트에 대한 리소스 등록
                resources.extend([
                    {
                        "uri": f"project://{project_id}",
                        "name": f"Project: {project_name}",
                        "description": f"Project information for {project_name}",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": f"project://{project_id}/stats",
                        "name": f"Stats: {project_name}",
                        "description": f"Statistics for {project_name}",
                        "mimeType": "application/json"
                    }
                ])

        return resources

    except Exception as e:
        logger.error("Failed to list resources", error=str(e))
        return []


@app.read_resource()
async def read_resource(uri: str) -> str:
    """리소스 읽기"""
    try:
        # URI 파싱: project://project_id 또는 project://project_id/stats
        if not uri.startswith("project://"):
            raise ValueError(f"Invalid resource URI: {uri}")

        path = uri[len("project://"):]
        parts = path.split("/")
        project_id = parts[0]

        if len(parts) == 1:
            # project://project_id - 프로젝트 정보
            projects_result = await api_client.list_projects()

            if projects_result.get("projects"):
                project = next(
                    (p for p in projects_result["projects"] if p["id"] == project_id),
                    None
                )
                if project:
                    import json
                    return json.dumps(project, indent=2)

            raise ValueError(f"Project not found: {project_id}")

        elif len(parts) == 2 and parts[1] == "stats":
            # project://project_id/stats - 프로젝트 통계
            stats_result = await api_client.get_project_stats(project_id)
            import json
            return json.dumps(stats_result, indent=2)

        else:
            raise ValueError(f"Invalid resource path: {uri}")

    except Exception as e:
        logger.error("Failed to read resource", uri=uri, error=str(e))
        raise


async def main():
    """MCP 서버 시작"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
