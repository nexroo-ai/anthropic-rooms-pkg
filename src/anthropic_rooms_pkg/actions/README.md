# Actions

This directory contains action functions that can be called by workflow engines using this package. Actions are the main interface between external systems and the anthropic-rooms-pkg functionality.

## Available Actions

### chat_completion
Performs chat completion using Anthropic's Claude API with optional tool support.

**Parameters:**
- `message` (str): User message to send to Claude
- `messages` (Optional[List[ChatMessage]]): Full conversation history
- `max_tokens` (Optional[int]): Max tokens (overrides config default)
- `temperature` (Optional[float]): Temperature (overrides config default)
- `system` (Optional[str]): System prompt
- `tools` (Optional[Dict]): Tools dictionary (automatically provided by tool registry)

### file_analysis
Analyzes files using Claude API.

### web_search
Performs web search operations.

## Tool System

The actions support a dynamic tool registration system that allows workflow engines to provide custom tools at runtime.

### How It Works

1. **Tool Registration**: Tools are registered via the `ToolRegistry` class in `tools/base.py`
2. **Tool Loading**: The addon's `loadTools()` method registers tools before action execution
3. **Tool Usage**: Actions automatically receive registered tools and can use them
4. **Cleanup**: Tools are cleared after action completion

### Tool Structure

Tools are registered with:
- **tools_dict**: Dictionary containing tool configurations with `action` arrays
- **tool_functions**: Dictionary mapping action names to callable functions
- **context**: String describing how to use the tools

Example tools_dict:
```python
{
    "storageOperation": {
        "action": ["storage-mongo-1::read", "storage-mongo-1::write"],
        "addonId": "storage-mongo-1",
        "collection": "claude_responses",
        "behavior": ["log", "knowledge", "cache", "results"]
    }
}
```

### Integration with Actions

Actions that support tools (like `chat_completion`) automatically:
1. Retrieve registered tools via the tool registry
2. Format tools for the underlying API (e.g., Anthropic's tool format)
3. Include tools in API calls
4. Handle tool responses

The tool formatting converts registered tools to the appropriate API format:
```python
{
    "name": "action_name",
    "description": "context_string", 
    "input_schema": function_annotations
}
```

## Usage Flow

1. Load configuration: `addon.loadAddonConfig(config)`
2. Load credentials: `addon.loadCredentials(**credentials)`
3. Load tools: `addon.loadTools(tools_dict, tool_functions, context)`
4. Execute action: `addon.chat_completion(message="Hello")`
5. Clear tools: `addon.clearTools()`