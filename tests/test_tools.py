from unittest.mock import Mock, patch

import pytest

from anthropic_rooms_pkg.tools.base import ToolRegistry


class TestToolRegistry:
    def test_tool_registry_initialization(self):
        registry = ToolRegistry()

        assert registry.functions == {}
        assert registry.tool_definitions == {}
        assert registry.tool_max_retries == {}

    def test_register_tools_basic(self, sample_tools):
        registry = ToolRegistry()

        registry.register_tools(sample_tools)

        assert len(registry.functions) == 2
        assert "test_tool" in registry.functions
        assert "another_tool" in registry.functions
        assert len(registry.tool_definitions) == 2

    def test_register_tools_with_descriptions(self, sample_tools, sample_tool_descriptions):
        registry = ToolRegistry()

        registry.register_tools(sample_tools, sample_tool_descriptions)

        assert registry.tool_definitions["test_tool"]["description"] == "A test tool for testing purposes"
        assert registry.tool_definitions["another_tool"]["description"] == "Another test tool"

    def test_register_tools_with_max_retries(self, sample_tools):
        registry = ToolRegistry()
        max_retries = {"test_tool": 3, "another_tool": 1}

        registry.register_tools(sample_tools, tool_max_retries=max_retries)

        assert registry.tool_max_retries["test_tool"] == 3
        assert registry.tool_max_retries["another_tool"] == 1

    def test_register_tools_with_addon_namespace(self):
        registry = ToolRegistry()

        def test_action():
            return "success"

        tools = {"test_addon::test_action": test_action}
        registry.register_tools(tools)

        expected_desc = "Execute test_action action from test_addon addon"
        assert registry.tool_definitions["test_addon::test_action"]["description"] == expected_desc

    def test_register_single_tool(self):
        registry = ToolRegistry()

        def test_func(param: str) -> str:
            return param

        registry._register_single_tool("test_func", test_func, "Test function")

        assert registry.functions["test_func"] == test_func
        assert registry.tool_definitions["test_func"]["name"] == "test_func"
        assert registry.tool_definitions["test_func"]["description"] == "Test function"
        assert "input_schema" in registry.tool_definitions["test_func"]

    def test_convert_annotations_to_schema_with_pydantic(self):
        registry = ToolRegistry()

        def test_func(param1: str, param2: int = 5) -> str:
            return f"{param1}_{param2}"

        with patch('pydantic.create_model') as mock_create_model:
            mock_model = Mock()
            mock_model.model_json_schema.return_value = {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"}
                },
                "required": ["param1"]
            }
            mock_create_model.return_value = mock_model

            schema = registry._convert_annotations_to_schema(test_func)

            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

    def test_convert_annotations_to_schema_fallback(self):
        registry = ToolRegistry()

        def test_func(param1: str, param2: int) -> str:
            return f"{param1}_{param2}"

        with patch('pydantic.create_model', side_effect=Exception("Pydantic error")):
            schema = registry._convert_annotations_to_schema(test_func)

            assert schema["type"] == "object"
            assert "param1" in schema["properties"]
            assert "param2" in schema["properties"]
            assert schema["properties"]["param1"]["type"] == "string"
            assert schema["properties"]["param2"]["type"] == "integer"

    def test_basic_type_converter_various_types(self):
        registry = ToolRegistry()

        def test_func(str_param: str, int_param: int, float_param: float, bool_param: bool, dict_param: dict) -> str:
            return "test"

        schema = registry._basic_type_converter(test_func)

        assert schema["properties"]["str_param"]["type"] == "string"
        assert schema["properties"]["int_param"]["type"] == "integer"
        assert schema["properties"]["float_param"]["type"] == "number"
        assert schema["properties"]["bool_param"]["type"] == "boolean"
        assert schema["properties"]["dict_param"]["type"] == "object"
        assert len(schema["required"]) == 5

    def test_basic_type_converter_unknown_type(self):
        registry = ToolRegistry()

        def test_func(unknown_param) -> str:
            return "test"

        test_func.__annotations__ = {"unknown_param": object, "return": str}

        with patch('loguru.logger') as mock_logger:
            schema = registry._basic_type_converter(test_func)

            assert schema["properties"]["unknown_param"]["type"] == "string"
            mock_logger.warning.assert_called()

    def test_basic_type_converter_no_annotations(self):
        registry = ToolRegistry()

        def test_func():
            return "test"

        schema = registry._basic_type_converter(test_func)

        assert schema == {"type": "object", "properties": {}, "required": []}

    def test_get_tools_for_action(self, sample_tools):
        registry = ToolRegistry()
        registry.register_tools(sample_tools)

        tools = registry.get_tools_for_action()

        assert len(tools) == 2
        assert "test_tool" in tools
        assert "another_tool" in tools
        assert tools is not registry.tool_definitions

    def test_get_function(self, sample_tools):
        registry = ToolRegistry()
        registry.register_tools(sample_tools)

        func = registry.get_function("test_tool")

        assert func == sample_tools["test_tool"]

    def test_get_function_nonexistent(self):
        registry = ToolRegistry()

        func = registry.get_function("nonexistent")

        assert func is None

    def test_get_max_retries(self, sample_tools):
        registry = ToolRegistry()
        max_retries = {"test_tool": 3}
        registry.register_tools(sample_tools, tool_max_retries=max_retries)

        retries = registry.get_max_retries("test_tool")
        assert retries == 3

        retries = registry.get_max_retries("another_tool")
        assert retries == 0

        retries = registry.get_max_retries("nonexistent")
        assert retries == 0

    def test_clear(self, sample_tools):
        registry = ToolRegistry()
        registry.register_tools(sample_tools)

        assert len(registry.functions) > 0
        assert len(registry.tool_definitions) > 0

        registry.clear()

        assert len(registry.functions) == 0
        assert len(registry.tool_definitions) == 0
        assert len(registry.tool_max_retries) == 0

    def test_convert_annotations_empty_parameters(self):
        registry = ToolRegistry()

        def no_params_func():
            return "test"

        schema = registry._convert_annotations_to_schema(no_params_func)

        assert schema == {"type": "object", "properties": {}, "required": []}

    def test_convert_annotations_with_empty_annotation(self):
        registry = ToolRegistry()

        def func_with_empty_annotation(param):
            return param

        func_with_empty_annotation.__annotations__ = {}

        with patch('pydantic.create_model') as mock_create_model:
            mock_model = Mock()
            mock_model.model_json_schema.return_value = {"type": "object"}
            mock_create_model.return_value = mock_model

            schema = registry._convert_annotations_to_schema(func_with_empty_annotation)

            assert schema["properties"] == {}
            assert schema["required"] == []
            assert schema["type"] == "object"

    def test_convert_annotations_schema_missing_fields(self):
        registry = ToolRegistry()

        def test_func(param: str) -> str:
            return param

        with patch('pydantic.create_model') as mock_create_model:
            mock_model = Mock()
            mock_model.model_json_schema.return_value = {}
            mock_create_model.return_value = mock_model

            schema = registry._convert_annotations_to_schema(test_func)

            assert "properties" in schema
            assert "required" in schema
            assert "type" in schema

    def test_basic_type_converter_no_annotations_attribute(self):
        registry = ToolRegistry()

        def no_annotations_func():
            return "test"

        if hasattr(no_annotations_func, '__annotations__'):
            delattr(no_annotations_func, '__annotations__')

        schema = registry._basic_type_converter(no_annotations_func)

        assert schema == {"type": "object", "properties": {}, "required": []}
