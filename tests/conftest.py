import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def sample_config():
    return {
        "api_key": "test_key",
        "base_url": "https://test.com",
        "model": "test-model"
    }

@pytest.fixture
def sample_credentials():
    return {
        "API_KEY": "test_secret_key",
        "DATABASE_URL": "test_db_url"
    }

@pytest.fixture
def sample_tools():
    def test_tool(param1: str, param2: int = 5) -> dict:
        return {"tool": "test_tool", "param1": param1, "param2": param2}

    def another_tool() -> str:
        return "success"

    return {
        "test_tool": test_tool,
        "another_tool": another_tool
    }

@pytest.fixture
def sample_tool_descriptions():
    return {
        "test_tool": "A test tool for testing purposes",
        "another_tool": "Another test tool"
    }
