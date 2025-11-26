# M2: MCP 서버 구현 상세 계획

## 프로젝트 개요

### 목표
AI Agent가 대규모 코드베이스 작업 시 **토큰 99% 절감** 및 **속도 10배 향상**

### 핵심 가치 제안
```
기존 방식: 전체 코드 읽기 → 50만 토큰 소모 → 5분
MCP 방식:  벡터 검색      → 5천 토큰 소모  → 0.5초
```

### 지원 플랫폼
- ✅ **Claude Desktop** (MCP 네이티브 지원)
- ✅ **Claude Code** (MCP SDK 사용)
- ✅ **LangGraph** (MCP Tools를 LangChain Tool로 변환)
- ✅ **Codex/기타** (REST API fallback)

---

## 아키텍처

### 전체 구조

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
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Server (localhost:8000)               │
│  /search/semantic │ /search/similar-code │ /projects   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              ChromaDB + Embeddings                      │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: MCP 서버 기본 구조

### Task 1.1: 프로젝트 구조 설정

**체크리스트:**
- [ ] 디렉토리 구조 생성
- [ ] MCP SDK 설치
- [ ] 기본 설정 파일 작성

**디렉토리 구조:**
```
code-agent-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py            # MCP 서버 메인
│   ├── tools.py             # MCP Tools 정의
│   ├── resources.py         # MCP Resources
│   ├── prompts.py           # MCP Prompts
│   ├── api_client.py        # FastAPI 클라이언트
│   └── config.py            # MCP 설정
├── tests/
│   └── test_mcp_server.py
├── examples/
│   ├── claude_code_integration.py
│   └── langgraph_integration.py
├── docs/
│   ├── MCP_SERVER_GUIDE.md
│   └── CLAUDE_DESKTOP_SETUP.md
├── mcp_config.json          # MCP 서버 설정
├── requirements.txt         # 의존성
├── README.md
└── .gitignore
```

**의존성 추가:**
```txt
# requirements.txt
mcp>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
python-dotenv>=1.0.0
structlog>=24.0.0
```

**설치 명령:**
```bash
pip install -r requirements.txt
```

**파일:**
- 생성: `requirements.txt`
- 생성: `mcp_config.json`
- 생성: `src/` 디렉토리

---

### Task 1.2: MCP 서버 기본 구현

**체크리스트:**
- [ ] MCP Server 클래스 구현
- [ ] FastAPI 클라이언트 구현
- [ ] 에러 핸들링
- [ ] 로깅 설정

**구현:**

```python
# src/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
import structlog

logger = structlog.get_logger(__name__)

# MCP 서버 인스턴스 생성
app = Server("code-embedding-ai")

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
```

```python
# src/api_client.py
import httpx
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger(__name__)

class FastAPIClient:
    """FastAPI 서버와 통신하는 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_semantic(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 10,
        min_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """시맨틱 검색"""
        try:
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
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            raise

    async def find_similar_code(
        self,
        code_snippet: str,
        language: str,
        project_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """유사 코드 검색"""
        try:
            response = await self.client.post(
                f"{self.base_url}/search/similar-code",
                json={
                    "code_snippet": code_snippet,
                    "language": language,
                    "project_id": project_id,
                    "top_k": top_k,
                    "min_similarity": 0.7
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Similar code search failed", error=str(e))
            raise

    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        top_k: int = 10
    ) -> Dict[str, Any]:
        """메타데이터 검색"""
        try:
            response = await self.client.post(
                f"{self.base_url}/search/metadata",
                params={"top_k": top_k},
                json=filters
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Metadata search failed", error=str(e))
            raise

    async def list_projects(self) -> Dict[str, Any]:
        """프로젝트 목록 조회"""
        try:
            response = await self.client.get(f"{self.base_url}/projects/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("List projects failed", error=str(e))
            raise

    async def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """프로젝트 통계 조회"""
        try:
            response = await self.client.get(
                f"{self.base_url}/projects/{project_id}/stats"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Get project stats failed", error=str(e))
            raise

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()
```

**파일:**
- 생성: `src/server.py`
- 생성: `src/api_client.py`
- 생성: `src/__init__.py`

---

(계속 Phase 2-7까지 동일한 내용...)

## 완료 체크리스트

### Phase 1: MCP 서버 기본 구조
- [ ] Task 1.1: 프로젝트 구조 설정
- [ ] Task 1.2: MCP 서버 기본 구현

### Phase 2: MCP Tools 구현
- [ ] Task 2.1: search_code Tool
- [ ] Task 2.2: Tools 핸들러 연결

### Phase 3: MCP Resources 구현
- [ ] Task 3.1: Resources 정의

### Phase 4: MCP Prompts 구현
- [ ] Task 4.1: 코드 작업 Prompts

### Phase 5: Claude Desktop/Code 연동
- [ ] Task 5.1: Claude Desktop 설정
- [ ] Task 5.2: Claude Code 연동

### Phase 6: LangGraph 연동
- [ ] Task 6.1: LangChain Tool 어댑터

### Phase 7: 테스트 및 문서화
- [ ] Task 7.1: 통합 테스트
- [ ] Task 7.2: 사용자 문서

---

## 다음 단계 (M3)

M2 완료 후:
- 성능 최적화 (파일 해시, 캐싱)
- 실시간 업데이트 (Git hook)
- 모니터링 대시보드
- 프로덕션 배포
