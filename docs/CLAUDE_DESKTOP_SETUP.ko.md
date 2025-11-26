# Claude Desktop 설정 가이드

이 가이드는 code-embedding-ai MCP 서버를 Claude Desktop과 통합하는 방법을 설명합니다.

## 사전 요구사항

- Claude Desktop 설치됨
- Python 3.10+ 설치됨
- `localhost:8000`에서 실행 중인 code-embedding-ai FastAPI 서버

## 설치 단계

### 1. MCP 서버 의존성 설치

```bash
cd code-agent-mcp
pip install -r requirements.txt
```

### 2. Claude Desktop 설정

Claude Desktop은 JSON 파일에서 MCP 서버 설정을 읽습니다.

**위치:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**설정:**

```json
{
  "mcpServers": {
    "code-embedding-ai": {
      "command": "python",
      "args": [
        "-m",
        "src.server"
      ],
      "cwd": "/절대/경로/code-agent-mcp",
      "env": {
        "PYTHONPATH": "/절대/경로/code-agent-mcp"
      }
    }
  }
}
```

**중요:**
- `/절대/경로/code-agent-mcp`를 실제 `code-agent-mcp` 디렉토리의 절대 경로로 변경하세요
- Windows에서는 이중 백슬래시 사용: `C:\\bin\\work\\vector\\code-agent-mcp`

### 3. FastAPI 서버 시작

MCP 서버를 사용하기 전에 FastAPI 백엔드가 실행 중인지 확인하세요:

```bash
cd ../code-embedding-ai
python -m src.cli server start --host localhost --port 8000
```

### 4. Claude Desktop 재시작

설정 파일을 수정한 후 Claude Desktop을 재시작하여 MCP 서버를 로드합니다.

## 검증

### MCP 서버 상태 확인

1. Claude Desktop 열기
2. UI에서 MCP 아이콘 또는 서버 표시기 찾기
3. `code-embedding-ai` 서버가 사용 가능으로 표시되어야 함

### 도구 테스트

대화에서 MCP 도구 사용 시도:

```
내 프로젝트에서 인증 관련 코드를 검색해줘
```

Claude가 `search_code` 도구를 사용하여 관련 코드를 찾아야 합니다.

### 사용 가능한 기능

설정이 완료되면 Claude Desktop에서 사용할 수 있는 기능:

**Tools (도구):**
- `search_code` - 시맨틱 코드 검색
- `find_similar_code` - 코드 중복 찾기
- `get_function_implementation` - 함수 정의 찾기
- `list_projects` - 등록된 프로젝트 목록
- `get_project_stats` - 프로젝트 통계

**Resources (리소스):**
- `project://{project_id}` - 프로젝트 정보
- `project://{project_id}/stats` - 프로젝트 통계

**Prompts (프롬프트):**
- `code-review` - 코드 리뷰 지원
- `refactor-code` - 리팩토링 제안
- `fix-bug` - 버그 수정 도움
- `write-tests` - 테스트 생성
- `explain-code` - 코드 설명

## 문제 해결

### 서버가 로드되지 않음

1. **Python 경로 확인:**
   ```bash
   which python  # macOS/Linux
   where python  # Windows
   ```
   필요한 경우 설정에서 전체 경로 사용

2. **로그 확인:**
   - Claude Desktop 로그는 일반적으로 애플리케이션 로그 디렉토리에 있음
   - MCP 서버 초기화 오류 찾기

3. **수동 테스트:**
   ```bash
   cd code-agent-mcp
   python -m src.server
   ```
   서버가 오류 없이 시작되어야 함

### 도구가 작동하지 않음

1. **FastAPI 서버 실행 확인:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **설정 확인:**
   - `mcp_config.json`의 `base_url`이 FastAPI 서버와 일치하는지 확인
   - 기본값은 `http://localhost:8000`

3. **프로젝트 등록 확인:**
   - 프로젝트가 먼저 FastAPI 서버에 등록되어야 함
   - CLI를 사용하여 프로젝트 추가:
     ```bash
     cd ../code-embedding-ai
     python -m src.cli project add /path/to/project
     ```

### 연결 타임아웃

타임아웃 오류가 발생하는 경우:

1. `mcp_config.json`에서 타임아웃 증가:
   ```json
   {
     "api": {
       "base_url": "http://localhost:8000",
       "timeout": 60
     }
   }
   ```

2. FastAPI 서버의 응답 확인:
   ```bash
   curl -w "@-" http://localhost:8000/projects/
   ```

## 사용 예시

### 코드 검색
```
사용자: 데이터베이스 연결 코드를 모두 찾아줘
Claude: [search_code 도구 사용]
       데이터베이스 연결 로직이 있는 12개의 결과를 찾았습니다...
```

### 코드 리뷰
```
사용자: 인증 로직을 리뷰해줘
Claude: [code-review 프롬프트 사용]
       보안 문제에 대한 인증 코드를 분석 중입니다...
```

### 유사 코드 찾기
```
사용자: 이 함수와 유사한 코드를 찾아줘: [코드 붙여넣기]
Claude: [find_similar_code 도구 사용]
       리팩토링할 수 있는 5개의 유사한 코드 패턴을 찾았습니다...
```

## 고급 설정

### 다중 프로젝트

여러 프로젝트로 작업하려면 모두 FastAPI 서버에 등록하세요:

```bash
python -m src.cli project add /path/to/project1 --name "Frontend"
python -m src.cli project add /path/to/project2 --name "Backend"
```

그런 다음 쿼리에서 검색할 프로젝트를 지정하세요:

```
Backend 프로젝트에서 사용자 인증을 검색해줘
```

### 커스텀 로깅

`mcp_config.json`에서 로깅 레벨 설정:

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "json"
  }
}
```

레벨: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## 보안 참고사항

- MCP 서버는 로컬에서 실행되며 `localhost:8000`에만 연결됩니다
- 외부 네트워크 요청이 이루어지지 않습니다
- 코드가 외부 서비스로 전송되지 않습니다
- 모든 벡터 임베딩은 로컬에서 계산됩니다 (로컬 모델 사용 시)

## 다음 단계

- 상세 API 문서는 [MCP 서버 가이드](MCP_SERVER_GUIDE.ko.md) 참조
- 프로그래밍 방식 사용은 [LangGraph 통합](LANGGRAPH_INTEGRATION.md) 참조
- 추가 기능은 [README](../README.ko.md) 확인
