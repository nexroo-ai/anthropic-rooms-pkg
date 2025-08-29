from unittest.mock import patch

import pytest

from anthropic_rooms_pkg.memory.example import demo_memory


class TestMemoryExample:
    @patch('anthropic_rooms_pkg.memory.example.logger')
    def test_demo_memory(self, mock_logger):
        result = demo_memory()

        assert result == {"memory_status": "active", "entries": 0}
        mock_logger.debug.assert_called_once_with(
            "Template rooms package - Demo memory system initialized successfully!"
        )

    def test_demo_memory_return_type(self):
        result = demo_memory()

        assert isinstance(result, dict)
        assert "memory_status" in result
        assert "entries" in result
        assert result["memory_status"] == "active"
        assert result["entries"] == 0
