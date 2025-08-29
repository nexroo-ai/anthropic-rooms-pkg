from unittest.mock import patch

import pytest

from anthropic_rooms_pkg.services.example import demo_service


class TestServicesExample:
    @patch('anthropic_rooms_pkg.services.example.logger')
    def test_demo_service(self, mock_logger):
        result = demo_service()

        assert result == {"service": "running", "port": 8080}
        mock_logger.debug.assert_called_once_with(
            "Template rooms package - Demo service started successfully!"
        )

    def test_demo_service_return_type(self):
        result = demo_service()

        assert isinstance(result, dict)
        assert "service" in result
        assert "port" in result
        assert result["service"] == "running"
        assert result["port"] == 8080
