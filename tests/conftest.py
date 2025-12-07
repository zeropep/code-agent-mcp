"""
Pytest configuration and shared fixtures for MCP server tests
"""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_code_snippet():
    """Sample code snippet for testing"""
    return """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""


@pytest.fixture
def sample_search_queries():
    """Sample search queries for testing"""
    return [
        "function definition",
        "class implementation",
        "error handling",
        "data validation",
        "user authentication"
    ]


@pytest.fixture
def mock_project_data():
    """Mock project data for testing"""
    return {
        "project_id": "test_project",
        "project_name": "Test Project",
        "path": "/test/path",
        "total_chunks": 100,
        "total_files": 10,
        "languages": ["python", "java"],
        "chunk_types": ["function", "class", "method"]
    }


def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests requiring running API server"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip E2E tests if API server is not running"""
    import httpx

    # Check if API server is running
    api_running = False
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2.0)
        api_running = response.status_code == 200
    except:
        pass

    # Skip E2E tests if API server is not running
    skip_e2e = pytest.mark.skip(reason="API server not running (http://localhost:8000)")

    for item in items:
        if "e2e" in item.keywords and not api_running:
            item.add_marker(skip_e2e)
