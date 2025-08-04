from typing import Dict, Callable, Any


class ToolRegistry:
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.tool_definitions: Dict[str, Dict[str, Any]] = {}
    
    def register_tools(self, tools_dict: Dict[str, Dict[str, Any]], tool_functions: Dict[str, Callable], context: str):
        for tool_name, tool_config in tools_dict.items():
            if "action" in tool_config:
                actions = tool_config["action"]
                if isinstance(actions, list):
                    for action in actions:
                        if action in tool_functions:
                            self._register_single_tool(action, tool_functions[action], context)
                elif isinstance(actions, str):
                    if actions in tool_functions:
                        self._register_single_tool(actions, tool_functions[actions], context)
    
    def _register_single_tool(self, action_name: str, func: Callable, context: str):
        """Register a single tool with proper Anthropic API format"""
        # Store the function for execution
        self.functions[action_name] = func
        
        # Create tool definition for Anthropic API
        self.tool_definitions[action_name] = {
            "name": action_name,
            "description": context or f"Execute {action_name} action",
            "input_schema": self._convert_annotations_to_schema(func)
        }
    
    def _convert_annotations_to_schema(self, func: Callable) -> Dict[str, Any]:
        try:
            from pydantic import create_model
            import inspect
            
            sig = inspect.signature(func)
            if not sig.parameters:
                return {"type": "object", "properties": {}, "required": []}
            
            fields = {}
            for param_name, param in sig.parameters.items():
                if param.annotation == inspect.Parameter.empty:
                    fields[param_name] = (Any, ...)
                else:
                    if param.default == inspect.Parameter.empty:
                        fields[param_name] = (param.annotation, ...)
                    else:
                        fields[param_name] = (param.annotation, param.default)
            
            DynamicModel = create_model('DynamicToolSchema', **fields)
            schema = DynamicModel.model_json_schema()
            
            if "properties" not in schema:
                schema["properties"] = {}
            if "required" not in schema:
                schema["required"] = []
            if "type" not in schema:
                schema["type"] = "object"
                
            return schema
            
        except Exception as e:
            from loguru import logger
            logger.warning(f"Pydantic schema generation failed for function '{func.__name__}': {str(e)}")
            logger.warning(f"Falling back to basic type converter for function '{func.__name__}'")
            return self._basic_type_converter(func)
    
    def _basic_type_converter(self, func: Callable) -> Dict[str, Any]:
        import inspect
        
        if not hasattr(func, '__annotations__'):
            return {"type": "object", "properties": {}, "required": []}
        
        annotations = func.__annotations__
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param_type in annotations.items():
            if param_name == 'return':
                continue
            
            # Convert Python types to JSON schema types
            if param_type is str:
                schema["properties"][param_name] = {"type": "string"}
            elif param_type is int:
                schema["properties"][param_name] = {"type": "integer"}
            elif param_type is float:
                schema["properties"][param_name] = {"type": "number"}
            elif param_type is bool:
                schema["properties"][param_name] = {"type": "boolean"}
            elif param_type is dict or str(param_type) == "<class 'dict'>":
                schema["properties"][param_name] = {"type": "object"}
            else:
                from loguru import logger
                logger.warning(f"Unknown type '{param_type}' for parameter '{param_name}' in function '{func.__name__}', defaulting to string")
                schema["properties"][param_name] = {"type": "string"}
            
            schema["required"].append(param_name)
        
        return schema
    
    def get_tools_for_action(self) -> Dict[str, Any]:
        """Get tools formatted for Anthropic API"""
        return self.tool_definitions.copy()
    
    def get_function(self, action_name: str) -> Callable:
        """Get the actual function for execution"""
        return self.functions.get(action_name)
    
    def clear(self):
        self.functions.clear()
        self.tool_definitions.clear()