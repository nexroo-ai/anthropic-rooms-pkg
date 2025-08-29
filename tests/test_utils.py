from unittest.mock import patch

import pytest

from anthropic_rooms_pkg.utils.example import demo_util


class TestUtilsExample:
    @patch('anthropic_rooms_pkg.utils.example.logger')
    def test_demo_util(self, mock_logger):
        result = demo_util()

        assert result == {"utility": "helper", "status": "ready"}
        mock_logger.debug.assert_called_once_with(
            "Template rooms package - Demo utility function executed successfully!"
        )

    def test_demo_util_return_type(self):
        result = demo_util()

        assert isinstance(result, dict)
        assert "utility" in result
        assert "status" in result
        assert result["utility"] == "helper"
        assert result["status"] == "ready"
