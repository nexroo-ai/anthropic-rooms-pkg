# Engine Integration Guide

This document describes how workflow engines should integrate with the anthropic-rooms-pkg to provide tools to actions.

## Overview

The engine integration follows a simple 3-step process:
1. **Load Tools**: Register tools with the addon
2. **Execute Action**: Call the desired action
3. **Cleanup**: Clear registered tools

## Step-by-Step Integration

### 1. Initialize Addon

```python
from anthropic_rooms_pkg.addon import AnthropicRoomsAddon

addon = AnthropicRoomsAddon()

# Load configuration
addon.loadAddonConfig({
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "temperature": 0.7,
    "secrets": {"anthropic_api_key": "placeholder"}
})

# Load credentials
addon.loadCredentials(anthropic_api_key="your-api-key")
```

### 2. Prepare Tools

Define your tools dictionary with action mappings:

```python
tools_dict = {
    "useStorage": {
        "action": ["storage-mongo-1::read", "storage-mongo-1::write"],
        "addonId": "storage-mongo-1", 
        "collection": "claude_responses",
        "behavior": ["log", "knowledge", "cache", "results"]
    },
    "useAPI": {
        "action": ["api-client::get", "api-client::post"],
        "addonId": "api-client",
        "baseUrl": "https://api.example.com"
    }
}
```

Define your tool functions:

```python
def storage_read(collection: str, query: dict) -> dict:
    # Implementation for reading from storage
    pass

def storage_write(collection: str, data: dict) -> bool:
    # Implementation for writing to storage  
    pass

def api_get(endpoint: str, params: dict = None) -> dict:
    # Implementation for API GET requests
    pass

def api_post(endpoint: str, data: dict) -> dict:
    # Implementation for API POST requests
    pass

tool_functions = {
    "storage-mongo-1::read": storage_read,
    "storage-mongo-1::write": storage_write,
    "api-client::get": api_get,
    "api-client::post": api_post
}
```

Define context for the tools:

```python
context = """
Available tools:
- Storage operations: Read and write data to MongoDB collections
- API operations: Make HTTP GET/POST requests to external APIs

Use storage tools for persisting conversation data and API tools for fetching external information.
"""
```

### 3. Execute Workflow

```python
# Load tools into the addon
addon.loadTools(tools_dict, tool_functions, context)

# Execute action - tools are automatically included
result = addon.chat_completion(
    message="Can you store this conversation and fetch user data?",
    system="You are a helpful assistant with access to storage and API tools."
)

# Clear tools when done
addon.clearTools()
```

## Tool Dictionary Structure

Each tool entry in `tools_dict` must contain:

- **action** (required): Array of strings mapping to functions in `tool_functions`
- Additional fields: Any other configuration needed by your tools

Example structure:
```python
{
    "customToolName": {  # This name is internal to your engine
        "action": ["namespace::function1", "namespace::function2"],  # Required
        "customField1": "value1",  # Optional
        "customField2": ["array", "of", "values"],  # Optional
        "customField3": {"nested": "object"}  # Optional
    }
}
```

## Function Signatures

Tool functions should use type annotations for automatic schema generation:

```python
def my_tool_function(param1: str, param2: int, optional_param: dict = None) -> dict:
    """
    Function docstring is used as tool description.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2  
        optional_param: Optional parameter with default
        
    Returns:
        Dictionary with operation results
    """
    return {"result": "success"}
```

## Error Handling

The addon handles errors gracefully:

- Invalid tool configurations are logged and skipped
- Missing functions in `tool_functions` are ignored
- Action execution continues even if some tools fail to register

## Best Practices

1. **Namespace Actions**: Use namespaced action names (e.g., `"storage-mongo-1::read"`) to avoid conflicts
2. **Clear Tools**: Always call `clearTools()` after action execution to prevent tool leakage
3. **Type Annotations**: Use proper type hints for automatic schema generation
4. **Error Handling**: Implement proper error handling in your tool functions
5. **Context**: Provide clear context strings to help the AI understand tool usage

## Multiple Tool Groups

You can register multiple tool groups by calling `loadTools()` multiple times:

```python
# Load storage tools
addon.loadTools(storage_tools_dict, storage_functions, storage_context)

# Load API tools  
addon.loadTools(api_tools_dict, api_functions, api_context)

# Execute action - all tools available
result = addon.chat_completion(message="Use both storage and API")

# Clear all tools
addon.clearTools()
```

## Supported Actions

Currently, these actions support tools:

- **chat_completion**: Full tool support with Anthropic's function calling
- **file_analysis**: Tool support planned
- **web_search**: Tool support planned

Check action documentation for specific tool integration details.