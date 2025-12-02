# Code Embedding AI - MCP 서버

벡터 임베딩을 사용한 AI 기반 코드 검색 및 분석을 위한 MCP (Model Context Protocol) 서버입니다.

## 개요

이 MCP 서버는 벡터 기반 시맨틱 검색을 통해 AI 에이전트가 대규모 코드베이스에 효율적으로 접근할 수 있게 하여, 토큰 사용량을 ~99% 줄이고 응답 시간을 10배 향상시킵니다.

### 가치 제안

```
기존 방식: 전체 코드 읽기 → 50만 토큰 → 5분
MCP 방식:  벡터 검색      → 5천 토큰  → 0.5초
```

**결과:** 99% 토큰 절감 + 10배 속도 향상

## 기능

### Tools (도구)
- **search_code**: 자연어를 사용한 시맨틱 코드 검색
- **find_similar_code**: 코드 중복 및 리팩토링 기회 발견
- **get_function_implementation**: 함수 이름으로 빠른 검색
- **list_projects**: 등록된 모든 프로젝트 목록 조회
- **get_project_stats**: 프로젝트 통계 조회 (파일, 청크, 언어)

### Resources (리소스)
- **project://{id}**: 프로젝트 정보 접근
- **project://{id}/stats**: 프로젝트 통계 접근

### Prompts (프롬프트)
- **code-review**: 컨텍스트를 포함한 자동 코드 리뷰
- **refactor-code**: 유사 코드 패턴과 함께 리팩토링 제안
- **fix-bug**: 관련 코드 컨텍스트를 포함한 디버깅 지원
- **write-tests**: 구현 컨텍스트를 포함한 테스트 생성
- **explain-code**: 전체 컨텍스트를 포함한 코드 설명

### 플랫폼 지원
- **Claude Desktop**: 네이티브 MCP 통합
- **Claude Code**: MCP SDK 통합
- **LangGraph**: LangChain 도구 어댑터
- **REST API**: 직접 HTTP 접근 폴백

## 빠른 시작

### 1. 사전 요구사항

- Python 3.10+
- `localhost:8000`에서 실행 중인 code-embedding-ai FastAPI 서버

### 2. 설치

```bash
cd code-agent-mcp
pip install -r requirements.txt
```

### 3. FastAPI 서버 시작

```bash
cd ../code-embedding-ai
python -m src.cli server start --host localhost --port 8000
```

### 4. 프로젝트 등록

```bash
python -m src.cli project add /path/to/your/project --name "MyProject"
python -m src.cli process project <project_id>
```

### 5. MCP 서버 실행

```bash
cd ../code-agent-mcp
python -m src.server
```

서버는 stdio 모드로 실행되어 MCP 클라이언트 연결을 기다립니다.

## 설정

### mcp_config.json

```json
{
  "server": {
    "name": "code-embedding-ai",
    "version": "1.0.0",
    "description": "AI 기반 코드 검색을 위한 MCP 서버"
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

**설정 옵션:**
- `api.base_url`: FastAPI 서버 URL (기본값: `http://localhost:8000`)
- `api.timeout`: 요청 타임아웃 (초 단위, 기본값: 30)
- `logging.level`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
- `logging.format`: 로그 형식 (json, text)

## 사용 예시

### Claude Desktop

`claude_desktop_config.json`에서 설정:

**가상환경 사용 시 (권장):**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "/경로/code-agent-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "/경로/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/경로/code-agent-mcp"
      }
    }
  }
}
```

**시스템 Python 사용 시:**
```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/절대/경로/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/절대/경로/code-agent-mcp"
      }
    }
  }
}
```

Claude Desktop에서 사용:
```
내 프로젝트에서 인증 관련 코드를 모두 찾아줘
```

### Claude Code (프로그래밍 방식)

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

        # 코드 검색
        result = await session.call_tool(
            "search_code",
            {"query": "사용자 인증", "top_k": 5}
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
    "messages": [("human", "인증 코드를 찾아서 리뷰해줘")]
})
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     AI 클라이언트                        │
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
│         (로컬 또는 API 기반 임베딩)                      │
└─────────────────────────────────────────────────────────┘
```

## 문서

`docs/` 디렉토리에서 상세 가이드 확인:

- **[MCP 서버 가이드](docs/MCP_SERVER_GUIDE.ko.md)**: 완전한 API 레퍼런스 및 아키텍처
- **[Claude Desktop 설정](docs/CLAUDE_DESKTOP_SETUP.ko.md)**: 단계별 통합 가이드
- **[M2 구현 계획](M2_MCP_SERVER.md)**: 상세 개발 로드맵

## 예제

`examples/` 디렉토리 참조:

- **[claude_code_integration.py](examples/claude_code_integration.py)**: Claude Agent SDK 사용
- **[langgraph_integration.py](examples/langgraph_integration.py)**: LangChain/LangGraph 통합

## 테스트

pytest로 테스트 실행:

```bash
# 테스트 의존성 설치
pip install pytest pytest-asyncio

# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트 실행
pytest tests/test_mcp_server.py::TestAPIClient::test_search_semantic -v
```

## 문제 해결

### 서버가 시작되지 않음

1. Python 버전 확인: `python --version` (3.10+ 필요)
2. 의존성 확인: `pip install -r requirements.txt`
3. 서버 수동 테스트: `python -m src.server`

### 도구가 작동하지 않음

1. FastAPI 서버 실행 확인:
   ```bash
   curl http://localhost:8000/health
   ```

2. 프로젝트 등록 확인:
   ```bash
   cd ../code-embedding-ai
   python -m src.cli project list
   ```

3. 필요시 프로젝트 처리:
   ```bash
   python -m src.cli process project <project_id>
   ```

### 연결 타임아웃

- `mcp_config.json`에서 타임아웃 증가:
  ```json
  {"api": {"timeout": 60}}
  ```

- FastAPI 서버 로그에서 오류 확인

## 성능

### 응답 시간

일반적인 응답 시간 (코드베이스 크기에 따라 다름):

- `search_code`: 100-500ms
- `find_similar_code`: 150-600ms
- `get_function_implementation`: 50-200ms
- `list_projects`: 10-50ms
- `get_project_stats`: 20-100ms

### 최적화 팁

1. **project_id로 필터링**: 특정 프로젝트로 검색 범위 좁히기
2. **top_k 조정**: 더 적은 결과 요청으로 빠른 응답
3. **min_similarity 사용**: 낮은 품질의 매칭 필터링
4. **로컬 임베딩**: 로컬 모델 사용으로 API 지연 회피

## 보안

- **로컬 전용**: 서버는 localhost에만 연결
- **외부 요청 없음**: 모든 작업이 로컬에서 수행
- **데이터 공유 없음**: 코드가 컴퓨터를 벗어나지 않음
- **stdio 전송**: 안전한 로컬 통신

## 개발

### 프로젝트 구조

```
code-agent-mcp/
├── src/
│   ├── server.py           # MCP 서버 메인
│   ├── api_client.py       # FastAPI 클라이언트
│   ├── config.py           # 설정
│   └── __init__.py
├── tests/
│   └── test_mcp_server.py  # 단위 테스트
├── examples/
│   ├── claude_code_integration.py
│   └── langgraph_integration.py
├── docs/
│   ├── MCP_SERVER_GUIDE.ko.md
│   └── CLAUDE_DESKTOP_SETUP.ko.md
├── mcp_config.json         # 설정
├── requirements.txt        # 의존성
└── README.ko.md
```

### 기여하기

1. 저장소 포크
2. 기능 브랜치 생성
3. 변경사항 작성
4. 새 기능에 대한 테스트 추가
5. 테스트 실행: `pytest tests/ -v`
6. Pull Request 제출

## 로드맵

향후 개선사항:

- [ ] 반복 쿼리를 위한 요청 캐싱
- [ ] 성능을 위한 병렬 API 호출
- [ ] 대용량 결과를 위한 스트리밍 응답
- [ ] 다중 백엔드 지원
- [ ] 인증/권한 부여
- [ ] 메트릭 및 모니터링 대시보드
- [ ] 실시간 업데이트를 위한 Git 웹훅 통합

## 라이선스

MIT

## 지원

- **이슈**: [GitHub Issues](https://github.com/your-org/code-embedding-ai/issues)
- **문서**: `docs/` 디렉토리 참조
- **예제**: `examples/` 디렉토리 참조

## 관련 프로젝트

- **[code-embedding-ai](../code-embedding-ai)**: 벡터 임베딩을 사용하는 FastAPI 백엔드
- **[MCP Specification](https://github.com/modelcontextprotocol/specification)**: 공식 MCP 프로토콜 문서
