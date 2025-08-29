from unittest.mock import Mock, patch

import pytest

from anthropic_rooms_pkg.addon import AnthropicRoomsAddon


class TestAnthropicRoomsAddon:
    def test_addon_initialization(self):
        addon = AnthropicRoomsAddon()

        assert addon.type == "agent"
        assert addon.modules == ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        assert addon.config == {}
        assert addon.credentials is not None
        assert addon.tool_registry is not None
        assert addon.observer_callback is None
        assert addon.addon_id is None

    def test_logger_property(self):
        addon = AnthropicRoomsAddon()
        logger = addon.logger

        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert logger.addon_type == "agent"


    def test_load_tools(self, sample_tools, sample_tool_descriptions):
        addon = AnthropicRoomsAddon()

        with patch.object(addon.tool_registry, 'register_tools') as mock_register, \
             patch.object(addon.tool_registry, 'get_tools_for_action', return_value={"tool1": {}, "tool2": {}}):

            addon.loadTools(sample_tools, sample_tool_descriptions)

            mock_register.assert_called_once_with(sample_tools, sample_tool_descriptions, None)

    def test_get_tools(self):
        addon = AnthropicRoomsAddon()
        expected_tools = {"tool1": {"name": "tool1"}, "tool2": {"name": "tool2"}}

        with patch.object(addon.tool_registry, 'get_tools_for_action', return_value=expected_tools):
            result = addon.getTools()

            assert result == expected_tools

    def test_clear_tools(self):
        addon = AnthropicRoomsAddon()

        with patch.object(addon.tool_registry, 'clear') as mock_clear:
            addon.clearTools()

            mock_clear.assert_called_once()

    def test_set_observer_callback(self):
        addon = AnthropicRoomsAddon()
        callback = Mock()
        addon_id = "test_addon"

        addon.setObserverCallback(callback, addon_id)

        assert addon.observer_callback == callback
        assert addon.addon_id == addon_id

    def test_load_addon_config_success(self, sample_config):
        addon = AnthropicRoomsAddon()

        with patch('anthropic_rooms_pkg.configuration.CustomAddonConfig') as MockConfig:
            mock_config_instance = Mock()
            MockConfig.return_value = mock_config_instance

            result = addon.loadAddonConfig(sample_config)

            MockConfig.assert_called_once_with(**sample_config)
            assert addon.config == mock_config_instance
            assert result is True

    def test_load_addon_config_failure(self):
        addon = AnthropicRoomsAddon()

        with patch('anthropic_rooms_pkg.configuration.CustomAddonConfig', side_effect=Exception("Config error")):
            result = addon.loadAddonConfig({})

            assert result is False

    def test_load_credentials_success(self, sample_credentials):
        addon = AnthropicRoomsAddon()

        with patch.object(addon.credentials, 'store_multiple') as mock_store:
            result = addon.loadCredentials(**sample_credentials)

            mock_store.assert_called_once_with(sample_credentials)
            assert result is True

    def test_load_credentials_with_config_validation(self, sample_credentials):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        mock_config.secrets = {"API_KEY": "required", "DATABASE_URL": "required"}
        addon.config = mock_config

        with patch.object(addon.credentials, 'store_multiple') as mock_store:
            result = addon.loadCredentials(**sample_credentials)

            mock_store.assert_called_once_with(sample_credentials)
            assert result is True

    def test_load_credentials_missing_required_secrets(self):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        mock_config.secrets = {"REQUIRED_SECRET": "required", "ANOTHER_SECRET": "required"}
        addon.config = mock_config

        result = addon.loadCredentials(REQUIRED_SECRET="value")

        assert result is False

    def test_load_credentials_failure(self, sample_credentials):
        addon = AnthropicRoomsAddon()

        with patch.object(addon.credentials, 'store_multiple', side_effect=Exception("Store error")):
            result = addon.loadCredentials(**sample_credentials)

            assert result is False

    def test_test_method_success(self):
        addon = AnthropicRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.__all__ = ['TestComponent']
            mock_module.TestComponent = Mock()
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

    def test_test_method_import_error(self):
        addon = AnthropicRoomsAddon()

        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = addon.test()

            assert result is False

    def test_test_method_general_error(self):
        addon = AnthropicRoomsAddon()

        with patch('importlib.import_module', side_effect=Exception("General error")):
            result = addon.test()

            assert result is False

    def test_test_method_component_skip_pydantic(self):
        addon = AnthropicRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            from pydantic import BaseModel

            class TestModel(BaseModel):
                pass

            mock_module = Mock()
            mock_module.__all__ = ['TestModel']
            mock_module.TestModel = TestModel
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

    def test_test_method_component_skip_known_models(self):
        addon = AnthropicRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.__all__ = ['ActionInput', 'ActionOutput']
            mock_module.ActionInput = Mock
            mock_module.ActionOutput = Mock
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

    @patch('anthropic_rooms_pkg.addon.chat_completion')
    def test_chat_completion_with_tools(self, mock_chat_completion):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        addon.config = mock_config

        tools = {"test_tool": {"name": "test_tool"}}
        with patch.object(addon, 'getTools', return_value=tools):
            addon.chat_completion("test message", temperature=0.5)

            mock_chat_completion.assert_called_once()
            call_args = mock_chat_completion.call_args
            assert call_args[0][0] == mock_config
            assert call_args[1]['message'] == "test message"
            assert call_args[1]['tools'] == tools
            assert call_args[1]['tool_registry'] == addon.tool_registry
            assert call_args[1]['temperature'] == 0.5

    @patch('anthropic_rooms_pkg.addon.chat_completion')
    def test_chat_completion_without_tools(self, mock_chat_completion):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        addon.config = mock_config

        with patch.object(addon, 'getTools', return_value={}):
            addon.chat_completion("test message")

            mock_chat_completion.assert_called_once()
            call_args = mock_chat_completion.call_args
            assert 'tools' not in call_args[1]
            assert 'tool_registry' not in call_args[1]

    @patch('anthropic_rooms_pkg.addon.chat_completion')
    def test_chat_completion_with_observer(self, mock_chat_completion):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        addon.config = mock_config
        addon.observer_callback = Mock()
        addon.addon_id = "test_id"

        with patch.object(addon, 'getTools', return_value={}):
            addon.chat_completion("test message")

            call_args = mock_chat_completion.call_args
            assert call_args[1]['observer_callback'] == addon.observer_callback
            assert call_args[1]['addon_id'] == "test_id"

    @patch('anthropic_rooms_pkg.addon.file_analysis')
    def test_file_analysis(self, mock_file_analysis):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        addon.config = mock_config

        addon.file_analysis("analyze file", file_id="file123")

        mock_file_analysis.assert_called_once_with(
            mock_config,
            message="analyze file",
            file_id="file123"
        )

    @patch('anthropic_rooms_pkg.addon.web_search')
    def test_web_search(self, mock_web_search):
        addon = AnthropicRoomsAddon()
        mock_config = Mock()
        addon.config = mock_config

        addon.web_search("search query", max_tokens=500)

        mock_web_search.assert_called_once_with(
            mock_config,
            query="search query",
            max_tokens=500
        )

