from typing import Dict, List, Callable, Any


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tools(self, tools_dict: Dict[str, Dict[str, Any]], tool_functions: Dict[str, Callable], context: str):
        for tool_name, tool_config in tools_dict.items():
            if "action" in tool_config:
                actions = tool_config["action"]
                if isinstance(actions, list):
                    for action in actions:
                        if action in tool_functions:
                            self.tools[action] = {
                                "function": tool_functions[action],
                                "context": context,
                                "input_schema": tool_functions[action].__annotations__ if hasattr(tool_functions[action], '__annotations__') else {}
                            }
                elif isinstance(actions, str):
                    if actions in tool_functions:
                        self.tools[actions] = {
                            "function": tool_functions[actions],
                            "context": context,
                            "input_schema": tool_functions[actions].__annotations__ if hasattr(tool_functions[actions], '__annotations__') else {}
                        }
    
    def get_tools_for_action(self) -> Dict[str, Any]:
        return self.tools.copy()
    
    def clear(self):
        self.tools.clear()