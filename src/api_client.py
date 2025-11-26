"""
FastAPI client for communicating with code-embedding-ai server
"""
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
