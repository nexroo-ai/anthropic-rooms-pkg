import pytest
from unittest.mock import patch

from anthropic_rooms_pkg.storage.example import demo_storage


class TestStorageExample:
    @patch('anthropic_rooms_pkg.storage.example.logger')
    def test_demo_storage(self, mock_logger):
        result = demo_storage()
        
        assert result == {"service": "running", "port": 8080}
        mock_logger.debug.assert_called_once_with(
            "Template rooms package - Demo storage started successfully!"
        )

    def test_demo_storage_return_type(self):
        result = demo_storage()
        
        assert isinstance(result, dict)
        assert "service" in result
        assert "port" in result
        assert result["service"] == "running"
        assert result["port"] == 8080