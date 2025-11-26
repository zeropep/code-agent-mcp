"""
Tests for MCP server functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.api_client import FastAPIClient
from src.config import MCPConfig, ServerConfig, APIConfig, LoggingConfig


class TestAPIClient:
    """Tests for FastAPI client"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return FastAPIClient(base_url="http://localhost:8000")

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client.base_url == "http://localhost:8000"
        assert client.client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_search_semantic(self, client):
        """Test semantic search"""
        # Mock the HTTP response
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "results": [
                    {
                        "file_path": "test.py",
                        "content": "def test():\n    pass",
                        "similarity": 0.95,
                        "line_start": 1,
                        "line_end": 2,
                        "chunk_type": "function"
                    }
                ]
            }
            mock_post.return_value = mock_response

            result = await client.search_semantic(
                query="test function",
                top_k=10
            )

            assert "results" in result
            assert len(result["results"]) == 1
            assert result["results"][0]["file_path"] == "test.py"

        await client.close()

    @pytest.mark.asyncio
    async def test_list_projects(self, client):
        """Test list projects"""
        with patch.object(client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "projects": [
                    {
                        "id": "proj_123",
                        "name": "Test Project",
                        "path": "/test/path"
                    }
                ]
            }
            mock_get.return_value = mock_response

            result = await client.list_projects()

            assert "projects" in result
            assert len(result["projects"]) == 1
            assert result["projects"][0]["name"] == "Test Project"

        await client.close()


class TestConfig:
    """Tests for configuration management"""

    def test_server_config(self):
        """Test server configuration"""
        config = ServerConfig(
            name="test-server",
            version="1.0.0",
            description="Test server"
        )
        assert config.name == "test-server"
        assert config.version == "1.0.0"

    def test_api_config(self):
        """Test API configuration"""
        config = APIConfig(
            base_url="http://localhost:8000",
            timeout=30
        )
        assert config.base_url == "http://localhost:8000"
        assert config.timeout == 30

    def test_logging_config(self):
        """Test logging configuration"""
        config = LoggingConfig(
            level="DEBUG",
            format="json"
        )
        assert config.level == "DEBUG"
        assert config.format == "json"

    def test_mcp_config_defaults(self):
        """Test MCP config with defaults"""
        config = MCPConfig(
            server=ServerConfig(),
            api=APIConfig(),
            logging=LoggingConfig()
        )
        assert config.server.name == "code-embedding-ai"
        assert config.api.base_url == "http://localhost:8000"
        assert config.logging.level == "INFO"

    def test_mcp_config_to_dict(self):
        """Test config serialization"""
        config = MCPConfig(
            server=ServerConfig(),
            api=APIConfig(),
            logging=LoggingConfig()
        )
        data = config.to_dict()
        assert "server" in data
        assert "api" in data
        assert "logging" in data
        assert data["server"]["name"] == "code-embedding-ai"


class TestMCPTools:
    """Tests for MCP tool handlers"""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock(spec=FastAPIClient)
        client.search_semantic = AsyncMock(return_value={
            "results": [
                {
                    "file_path": "test.py",
                    "content": "def test(): pass",
                    "similarity": 0.9,
                    "line_start": 1,
                    "line_end": 1,
                    "chunk_type": "function"
                }
            ]
        })
        client.find_similar_code = AsyncMock(return_value={"results": []})
        client.list_projects = AsyncMock(return_value={
            "projects": [{"id": "proj_1", "name": "Test", "path": "/test"}]
        })
        client.get_project_stats = AsyncMock(return_value={
            "total_chunks": 100,
            "total_files": 10,
            "languages": ["python"],
            "chunk_types": ["function", "class"]
        })
        return client

    @pytest.mark.asyncio
    async def test_search_code_tool(self, mock_api_client):
        """Test search_code tool execution"""
        # Import here to avoid MCP server initialization
        from src import server

        # Patch the global api_client
        with patch.object(server, 'api_client', mock_api_client):
            result = await server.call_tool(
                "search_code",
                {"query": "test function", "top_k": 5}
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"
            assert "Found 1 results" in result[0]["text"]
            assert "test.py" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_list_projects_tool(self, mock_api_client):
        """Test list_projects tool execution"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            result = await server.call_tool("list_projects", {})

            assert len(result) == 1
            assert result[0]["type"] == "text"
            assert "Test" in result[0]["text"]
            assert "proj_1" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_get_project_stats_tool(self, mock_api_client):
        """Test get_project_stats tool execution"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            result = await server.call_tool(
                "get_project_stats",
                {"project_id": "proj_1"}
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"
            assert "100" in result[0]["text"]  # total_chunks
            assert "python" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_unknown_tool(self, mock_api_client):
        """Test handling of unknown tool"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            result = await server.call_tool("unknown_tool", {})

            assert len(result) == 1
            assert result[0]["type"] == "text"
            assert "Error" in result[0]["text"]


class TestMCPResources:
    """Tests for MCP resource handlers"""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock(spec=FastAPIClient)
        client.list_projects = AsyncMock(return_value={
            "projects": [
                {"id": "proj_1", "name": "Test Project", "path": "/test"}
            ]
        })
        client.get_project_stats = AsyncMock(return_value={
            "total_chunks": 100,
            "total_files": 10
        })
        return client

    @pytest.mark.asyncio
    async def test_list_resources(self, mock_api_client):
        """Test list_resources handler"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            resources = await server.list_resources()

            assert len(resources) == 2  # project info + stats
            assert resources[0]["uri"] == "project://proj_1"
            assert resources[1]["uri"] == "project://proj_1/stats"

    @pytest.mark.asyncio
    async def test_read_resource_project(self, mock_api_client):
        """Test reading project resource"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            content = await server.read_resource("project://proj_1")

            assert "proj_1" in content
            assert "Test Project" in content

    @pytest.mark.asyncio
    async def test_read_resource_stats(self, mock_api_client):
        """Test reading stats resource"""
        from src import server

        with patch.object(server, 'api_client', mock_api_client):
            content = await server.read_resource("project://proj_1/stats")

            assert "100" in content  # total_chunks
            assert "10" in content  # total_files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
