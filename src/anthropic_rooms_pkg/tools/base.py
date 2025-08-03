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
        """Convert function annotations to JSON schema format for Anthropic API"""
        if not hasattr(func, '__annotations__'):
            return {"type": "object", "properties": {}}
        
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
            if param_type == str:
                schema["properties"][param_name] = {"type": "string"}
            elif param_type == int:
                schema["properties"][param_name] = {"type": "integer"}
            elif param_type == float:
                schema["properties"][param_name] = {"type": "number"}
            elif param_type == bool:
                schema["properties"][param_name] = {"type": "boolean"}
            else:
                # Default to string for other types
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