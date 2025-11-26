# MCP 서버 가이드

code-embedding-ai MCP 서버 아키텍처 및 사용법에 대한 완전한 가이드입니다.

## 아키텍처 개요

```
AI 클라이언트 (Claude/LangGraph/etc)
    ↓ MCP Protocol (stdio/SSE)
MCP Server (이 프로젝트)
    ↓ HTTP (httpx)
FastAPI Server (code-embedding-ai)
    ↓
ChromaDB + Vector Embeddings
```

## MCP 프로토콜

서버는 Model Context Protocol (MCP) 사양을 구현하며 다음을 제공합니다:

- **Tools**: AI 에이전트가 호출할 수 있는 함수
- **Resources**: 읽기 전용 데이터 소스 (프로젝트 정보)
- **Prompts**: 일반적인 작업을 위한 사전 정의된 프롬프트 템플릿

### 통신

- **전송:** stdio (표준 입출력)
- **형식:** JSON-RPC 2.0
- **비동기:** 모든 작업이 비동기

## Tools (도구)

### 1. search_code

**설명:** 자연어를 사용한 시맨틱 코드 검색

**매개변수:**
```json
{
  "query": "string (필수)",
  "project_id": "string (선택)",
  "top_k": "number (선택, 기본값: 10)",
  "min_similarity": "number (선택, 기본값: 0.7)"
}
```

**예시:**
```json
{
  "name": "search_code",
  "arguments": {
    "query": "사용자 인증 로직",
    "top_k": 5,
    "min_similarity": 0.75
  }
}
```

**응답:**
```json
{
  "type": "text",
  "text": "5개의 결과를 찾았습니다:\n\n**src/auth/login.py** (lines 12-45, similarity: 0.89)\nType: function\n```python\ndef authenticate_user(...):\n    ...\n```"
}
```

### 2. find_similar_code

**설명:** 주어진 코드와 유사한 코드 스니펫 찾기

**매개변수:**
```json
{
  "code_snippet": "string (필수)",
  "language": "string (필수)",
  "project_id": "string (선택)",
  "top_k": "number (선택, 기본값: 5)"
}
```

**사용 사례:**
- 코드 중복 찾기
- 리팩토링 기회 식별
- 유사한 패턴 발견

**예시:**
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

**설명:** 이름으로 함수 구현 찾기

**매개변수:**
```json
{
  "function_name": "string (필수)",
  "class_name": "string (선택)",
  "project_id": "string (선택)"
}
```

**예시:**
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

**설명:** 등록된 모든 프로젝트 목록 조회

**매개변수:** 없음

**예시:**
```json
{
  "name": "list_projects",
  "arguments": {}
}
```

**응답:**
```json
{
  "type": "text",
  "text": "등록된 프로젝트 (2개):\n\n- **Frontend** (ID: proj_abc123)\n  Path: /path/to/frontend\n- **Backend** (ID: proj_def456)\n  Path: /path/to/backend"
}
```

### 5. get_project_stats

**설명:** 프로젝트 통계 조회

**매개변수:**
```json
{
  "project_id": "string (필수)"
}
```

**응답:**
```json
{
  "type": "text",
  "text": "프로젝트 통계:\n- 전체 청크: 1234\n- 전체 파일: 89\n- 언어: python, javascript\n- 청크 타입: function, class, import"
}
```

## Resources (리소스)

리소스는 URI 패턴을 통해 프로젝트 데이터에 대한 읽기 전용 접근을 제공합니다.

### 프로젝트 정보

**URI:** `project://{project_id}`

**설명:** 프로젝트 메타데이터 가져오기

**응답:**
```json
{
  "id": "proj_abc123",
  "name": "Frontend",
  "path": "/path/to/frontend",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-15T12:00:00"
}
```

### 프로젝트 통계

**URI:** `project://{project_id}/stats`

**설명:** 상세한 프로젝트 통계 가져오기

**응답:**
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

## Prompts (프롬프트)

관련 코드 컨텍스트를 자동으로 수집하는 사전 정의된 프롬프트 템플릿입니다.

### 1. code-review

**인자:**
- `code_query` (필수): 리뷰할 코드 설명
- `project_id` (선택): 검색할 프로젝트

**사용법:**
```json
{
  "name": "code-review",
  "arguments": {
    "code_query": "인증 미들웨어"
  }
}
```

**동작:**
1. 관련 코드 검색
2. 상세한 리뷰 프롬프트 구성
3. 구조화된 리뷰 체크리스트 제공

### 2. refactor-code

**인자:**
- `code_snippet` (필수): 리팩토링할 코드
- `language` (필수): 프로그래밍 언어
- `project_id` (선택): 프로젝트 컨텍스트

**동작:**
1. 유사한 코드 패턴 찾기
2. 중복 기회 식별
3. 디자인 패턴 및 개선사항 제안

### 3. fix-bug

**인자:**
- `bug_description` (필수): 버그 설명
- `project_id` (선택): 검색할 프로젝트

**동작:**
1. 관련 코드 검색
2. 디버깅 프롬프트 구성
3. 근본 원인 분석 프레임워크 제공

### 4. write-tests

**인자:**
- `function_or_class` (필수): 함수/클래스 이름
- `project_id` (선택): 검색할 프로젝트

**동작:**
1. 구현 찾기
2. 테스트 케이스 제안
3. 테스팅 프레임워크 제공

### 5. explain-code

**인자:**
- `code_description` (필수): 설명할 내용
- `project_id` (선택): 검색할 프로젝트

**동작:**
1. 관련 코드 찾기
2. 설명 프롬프트 구성
3. 구조화된 설명 프레임워크 제공

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

### 환경 변수

- `API_BASE_URL`: API 베이스 URL 오버라이드 (기본값: `http://localhost:8000`)
- `LOG_LEVEL`: 로깅 레벨 오버라이드 (기본값: `INFO`)

## 오류 처리

모든 도구는 오류를 우아하게 처리하고 오류 메시지를 반환합니다:

```json
{
  "type": "text",
  "text": "'search_code' 도구 실행 오류: localhost:8000에 연결 거부됨"
}
```

일반적인 오류:
- **연결 거부됨**: FastAPI 서버가 실행되지 않음
- **프로젝트를 찾을 수 없음**: 잘못된 프로젝트 ID
- **결과를 찾을 수 없음**: 쿼리가 코드와 일치하지 않음
- **타임아웃**: 쿼리가 너무 오래 걸림 (설정에서 타임아웃 증가)

## 성능

### 응답 시간

일반적인 응답 시간 (코드베이스 크기에 따라 다름):

- `search_code`: 100-500ms
- `find_similar_code`: 150-600ms
- `get_function_implementation`: 50-200ms
- `list_projects`: 10-50ms
- `get_project_stats`: 20-100ms

### 최적화 팁

1. **project_id 필터 사용**: 특정 프로젝트로 검색 범위 좁히기
2. **top_k 조정**: 더 적은 결과 요청으로 빠른 응답
3. **min_similarity 증가**: 낮은 품질의 매치 필터링
4. **로컬 임베딩 사용**: API 지연 회피 (code-embedding-ai 설정 참조)

## 개발

### 서버 실행

```bash
# 개발 모드
cd code-agent-mcp
python -m src.server

# 서버는 stdin에서 읽고 stdout에 씁니다
# stdio 전송을 지원하는 MCP 클라이언트와 함께 사용
```

### 테스트

```bash
# 테스트 의존성 설치
pip install pytest pytest-asyncio

# 테스트 실행
pytest tests/

# 특정 도구 테스트
pytest tests/test_mcp_server.py::test_search_code
```

### 로깅

디버그 로깅 활성화:

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "json"
  }
}
```

로그 포함 사항:
- 도구 호출
- API 호출
- 응답 시간
- 오류 및 스택 트레이스

## 통합 예제

`examples/` 디렉토리 참조:
- `claude_code_integration.py`: Claude Code와 함께 사용
- `langgraph_integration.py`: LangChain/LangGraph 통합

## API 클라이언트

`FastAPIClient` 클래스 (`src/api_client.py`)는 FastAPI 백엔드와 통신하기 위한 비동기 메서드를 제공합니다:

```python
from src.api_client import FastAPIClient

client = FastAPIClient(base_url="http://localhost:8000")

# 시맨틱 검색
results = await client.search_semantic(
    query="인증 로직",
    top_k=10
)

# 유사 코드
results = await client.find_similar_code(
    code_snippet="def login(...):\n    ...",
    language="python"
)

# 메타데이터 검색
results = await client.search_by_metadata(
    filters={"chunk_type": "function", "name": "login"}
)

# 프로젝트
projects = await client.list_projects()
stats = await client.get_project_stats(project_id="proj_123")

# 정리
await client.close()
```

## 보안

- **로컬 전용**: 서버는 localhost에만 연결
- **외부 요청 없음**: 모든 작업이 로컬
- **데이터 공유 없음**: 코드가 컴퓨터를 벗어나지 않음
- **stdio 전송**: 안전한 로컬 통신

## 제한사항

- **단일 FastAPI 인스턴스**: 하나의 백엔드 서버만 지원
- **인증 없음**: 신뢰할 수 있는 로컬 환경 가정
- **동기 백엔드 호출**: 순차적 API 요청 (병렬화 가능)
- **캐싱 없음**: 각 요청이 API에 도달 (캐싱 계층 추가 가능)

## 로드맵

향후 개선사항:
- 반복 쿼리를 위한 요청 캐싱
- 더 나은 성능을 위한 병렬 API 호출
- 대용량 결과를 위한 스트리밍 응답
- 다중 백엔드 지원
- 인증/권한 부여
- 메트릭 및 모니터링

## 지원

문제 및 질문:
- GitHub Issues: [code-embedding-ai](https://github.com/your-org/code-embedding-ai)
- 문서: `docs/` 디렉토리 참조
- 예제: `examples/` 디렉토리 참조
