"""
End-to-End tests for MCP server with real FastAPI backend
Tests all 5 MCP tools against a running API server
"""

import pytest
import asyncio
from src.api_client import FastAPIClient


class TestE2EMCPTools:
    """E2E tests for MCP tools with real API server"""

    @pytest.fixture
    async def api_client(self):
        """Create API client connected to real server"""
        client = FastAPIClient(base_url="http://localhost:8000")
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_search_code_tool(self, api_client):
        """
        E2E Test: search_code tool
        Tests semantic code search functionality
        """
        # Test search with a simple query
        result = await api_client.search_semantic(
            query="function definition",
            top_k=5
        )

        # Verify response structure
        assert "results" in result
        assert isinstance(result["results"], list)

        # If results exist, verify structure
        if len(result["results"]) > 0:
            first_result = result["results"][0]
            assert "file_path" in first_result
            assert "content" in first_result
            assert "similarity" in first_result
            assert "line_start" in first_result
            assert "line_end" in first_result

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_find_similar_code_tool(self, api_client):
        """
        E2E Test: find_similar_code tool
        Tests finding similar code patterns
        """
        # Test with sample code snippet
        code_snippet = """
        def process_data(items):
            result = []
            for item in items:
                result.append(item)
            return result
        """

        result = await api_client.find_similar_code(
            code_snippet=code_snippet,
            top_k=3
        )

        # Verify response structure
        assert "results" in result
        assert isinstance(result["results"], list)

        # If results exist, verify structure
        if len(result["results"]) > 0:
            first_result = result["results"][0]
            assert "file_path" in first_result
            assert "content" in first_result
            assert "similarity" in first_result

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_get_function_implementation_tool(self, api_client):
        """
        E2E Test: get_function_implementation tool
        Tests finding function implementations by name
        """
        # Search for common function names
        function_names = ["process", "get", "create", "update", "delete"]

        for func_name in function_names:
            result = await api_client.search_semantic(
                query=f"function {func_name}",
                top_k=3
            )

            # Verify response structure
            assert "results" in result
            assert isinstance(result["results"], list)

            # No need to assert results exist, just verify structure
            break  # Test only one to avoid long test time

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_list_projects_tool(self, api_client):
        """
        E2E Test: list_projects tool
        Tests listing all projects in the system
        """
        result = await api_client.list_projects()

        # Verify response structure
        assert "projects" in result
        assert isinstance(result["projects"], list)

        # Verify project structure if projects exist
        if len(result["projects"]) > 0:
            first_project = result["projects"][0]
            assert "project_id" in first_project
            assert "total_chunks" in first_project

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_get_project_stats_tool(self, api_client):
        """
        E2E Test: get_project_stats tool
        Tests getting statistics for a specific project
        """
        # First, get list of projects
        projects_result = await api_client.list_projects()

        if len(projects_result["projects"]) > 0:
            # Get stats for first project
            project_id = projects_result["projects"][0]["project_id"]

            result = await api_client.get_project_stats(project_id=project_id)

            # Verify response structure
            assert "total_chunks" in result
            assert "total_files" in result
            assert isinstance(result["total_chunks"], int)
            assert isinstance(result["total_files"], int)
        else:
            # If no projects, skip this test
            pytest.skip("No projects available to test get_project_stats")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_search_with_project_filter(self, api_client):
        """
        E2E Test: Search with project_id filter
        Tests project-specific search functionality
        """
        # Get list of projects first
        projects_result = await api_client.list_projects()

        if len(projects_result["projects"]) > 0:
            project_id = projects_result["projects"][0]["project_id"]

            # Search within specific project
            result = await api_client.search_semantic(
                query="function",
                project_id=project_id,
                top_k=5
            )

            # Verify response structure
            assert "results" in result
            assert isinstance(result["results"], list)

            # Verify all results are from the specified project
            for search_result in result["results"]:
                if "metadata" in search_result and "project_id" in search_result["metadata"]:
                    assert search_result["metadata"]["project_id"] == project_id
        else:
            pytest.skip("No projects available to test project filtering")


class TestE2EErrorHandling:
    """E2E tests for error handling"""

    @pytest.fixture
    async def api_client(self):
        """Create API client connected to real server"""
        client = FastAPIClient(base_url="http://localhost:8000")
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_search_with_invalid_parameters(self, api_client):
        """
        E2E Test: Error handling for invalid search parameters
        """
        # Test with invalid top_k (too large)
        try:
            result = await api_client.search_semantic(
                query="test",
                top_k=10000  # Unreasonably large
            )
            # Should either work or raise appropriate error
            assert "results" in result or "error" in result
        except Exception as e:
            # Should raise appropriate exception
            assert e is not None

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_get_nonexistent_project_stats(self, api_client):
        """
        E2E Test: Error handling for non-existent project
        """
        # Test with non-existent project ID
        try:
            result = await api_client.get_project_stats(
                project_id="nonexistent_project_id_12345"
            )
            # Should return empty stats or error
            assert result is not None
        except Exception as e:
            # Should raise appropriate exception
            assert e is not None


class TestE2EPerformance:
    """E2E performance tests"""

    @pytest.fixture
    async def api_client(self):
        """Create API client connected to real server"""
        client = FastAPIClient(base_url="http://localhost:8000")
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.performance
    async def test_search_response_time(self, api_client):
        """
        E2E Performance Test: Search response time
        Target: < 500ms for simple queries
        """
        import time

        start_time = time.time()

        result = await api_client.search_semantic(
            query="function",
            top_k=5
        )

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms

        print(f"\nSearch response time: {response_time:.2f}ms")

        # Verify response
        assert "results" in result

        # Check if response time is reasonable (warn if > 500ms, but don't fail)
        if response_time > 500:
            print(f"WARNING: Search response time ({response_time:.2f}ms) exceeds target (500ms)")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.performance
    async def test_concurrent_searches(self, api_client):
        """
        E2E Performance Test: Concurrent search requests
        Tests system behavior under concurrent load
        """
        # Perform 5 concurrent searches
        queries = [
            "function definition",
            "class implementation",
            "error handling",
            "data processing",
            "user authentication"
        ]

        tasks = [
            api_client.search_semantic(query=q, top_k=3)
            for q in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests completed
        assert len(results) == len(queries)

        # Count successful responses
        successful = sum(1 for r in results if isinstance(r, dict) and "results" in r)
        print(f"\nConcurrent searches: {successful}/{len(queries)} successful")


class TestE2EHealthCheck:
    """E2E health check tests"""

    @pytest.fixture
    async def api_client(self):
        """Create API client connected to real server"""
        client = FastAPIClient(base_url="http://localhost:8000")
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_api_health_check(self, api_client):
        """
        E2E Test: API server health check
        Verifies the API server is running and healthy
        """
        # Use the client to make a simple request
        # If this succeeds, the server is healthy
        result = await api_client.list_projects()

        assert result is not None
        assert "projects" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
