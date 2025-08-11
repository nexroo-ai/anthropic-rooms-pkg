# Anthropic - AI Rooms Workflow Addon

## Overview

Claude-powered AI agent addon for Rooms AI, providing advanced conversational AI, file analysis, and web-enhanced responses.

**Addon Type:** `anthropic` ( 'agent' type addon )

## Features

- **Chat Completion**: Advanced conversational AI using Claude models with tool integration
- **File Analysis**: Upload and analyze documents, images, and other files with Claude
- **Web Search**: Enhanced responses with real-time web search capabilities and citations
- **Tool Registry**: Full support for external tools and workflow integration
- **Token Management**: Comprehensive token tracking and usage monitoring

## Add to Rooms AI using poetry

Using the script

```bash
poetry add git+https://github.com/synvex-ai/anthropic-rooms-pkg.git
```

In the web interface, follow online guide for adding an addon. You can still use JSON in web interface.


## Configuration

### Addon Configuration
Add this addon to your AI Rooms workflow configuration:

```json
{
  "addons": [
    {
      "id": "claude-assistant",
      "type": "anthropic",
      "name": "Claude AI Assistant",
      "enabled": true,
      "config": {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "temperature": 0.7
      },
      "secrets": {
        "anthropic_api_key": "ANTHROPIC_API_KEY"
      }
    }
  ]
}
```

### Configuration Fields

#### BaseAddonConfig Fields
All addons inherit these base configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier for the addon instance |
| `type` | string | Yes | - | Type of the addon ("template") |
| `name` | string | Yes | - | Display name of the addon |
| `description` | string | Yes | - | Description of the addon |
| `enabled` | boolean | No | true | Whether the addon is enabled |

#### CustomAddonConfig Fields (anthropic-specific)
This anthropic addon adds these specific configuration fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | No | "claude-3-5-sonnet-20241022" | Claude model to use |
| `max_tokens` | integer | No | 4096 | Maximum tokens for responses |
| `temperature` | float | No | 0.7 | Temperature for text generation (0.0-1.0) |

### Required Secrets

| Secret Key | Environment Variable | Description |
|------------|---------------------|-------------|
| `anthropic_api_key` | `ANTHROPIC_API_KEY` | Anthropic API key for Claude access |

### Environment Variables
Create a `.env` file in your workflow directory:

```bash
# .env file
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Available Actions

### `chat_completion`
Advanced conversational AI using Claude models with full tool integration support.

**Parameters:**
- `message` (string, required): User message to send to Claude
- `messages` (array, optional): Full conversation history with role/content pairs
- `max_tokens` (integer, optional): Override config default for max tokens
- `temperature` (float, optional): Override config default for temperature  
- `system` (string, optional): System prompt to guide Claude's behavior

**Output Structure:**
- `response` (string): Claude's response text
- `model` (string): Model used for the response
- `usage` (object): Token usage information (input_tokens, output_tokens, total_tokens)
- `stop_reason` (string): Why Claude stopped generating (end_turn, max_tokens, etc.)

**Workflow Usage:**
```json
{
  "id": "ai-conversation",
  "name": "Chat with Claude",
  "action": "claude-assistant::chat_completion",
  "parameters": {
    "message": "{{payload.user_question}}",
    "system": "You are a helpful assistant specialized in technical documentation."
  }
}
```

### `file_analysis`
Upload and analyze documents, images, and other files with Claude's multimodal capabilities.

**Parameters:**
- `message` (string, required): Question or instruction about the file
- `file_upload` (object, optional): File to upload and analyze
  - `file_path` (string, required): Path to file to upload
  - `filename` (string, optional): Custom filename
  - `purpose` (string, default: "analysis"): Purpose of file upload
- `file_id` (string, optional): ID of already uploaded file
- `max_tokens` (integer, optional): Override config default
- `temperature` (float, optional): Override config default

**Output Structure:**
- `response` (string): Claude's analysis response
- `file_info` (object): Information about the analyzed file
- `model` (string): Model used
- `usage` (object): Token usage information

**Workflow Usage:**
```json
{
  "id": "document-analysis",
  "name": "Analyze Document", 
  "action": "claude-assistant::file_analysis",
  "parameters": {
    "message": "Summarize the key points in this document",
    "file_upload": {
      "file_path": "{{payload.document_path}}",
      "purpose": "analysis"
    }
  }
}
```

### `web_search`
Enhanced responses with real-time web search capabilities and source citations.

**Parameters:**
- `query` (string, required): Search query or question
- `max_tokens` (integer, optional): Override config default
- `temperature` (float, optional): Override config default
- `system` (string, optional): System prompt

**Output Structure:**
- `response` (string): Claude's response enhanced with web information
- `citations` (array): List of sources Claude referenced
- `search_performed` (boolean): Whether web search was actually performed
- `model` (string): Model used
- `usage` (object): Token usage information

**Workflow Usage:**
```json
{
  "id": "web-enhanced-response",
  "name": "Web-Enhanced Answer",
  "action": "claude-assistant::web_search", 
  "parameters": {
    "query": "{{payload.user_question}}",
    "system": "Provide comprehensive answers with citations from recent sources."
  }
}
```

## Tools Support

This agent addon **supports tools** in the **`chat_completion`** action only.

### Tool Integration
The addon includes a comprehensive tool registry that allows external tools to be registered and used during Claude conversations. Tools are automatically passed to Claude when available.

**Tool-Supported Actions:**
- **`chat_completion`**: Full tool integration - Claude can call external tools during conversation

### Using Tools with Claude
When tools are registered via `useStorage` or `useContext`, they become available to Claude during `chat_completion`:

```json
{
  "id": "claude-with-tools",
  "name": "Claude with Database Tools",
  "action": "claude-assistant::chat_completion", 
  "useStorage": {
    "addonId": "my-mongo-db",
    "action": [
      {"name": "describe", "description": "Describe the database"},
      {"name": "insert", "description": "Insert a new document into the database"}
    ]
  },
  "parameters": {
    "message": "Please analyze our user database and create a summary report",
    "system": "You are a data analyst with access to database tools. Use them as needed."
  }
}
```

For detailed tool usage patterns, refer to the [AI Features documentation](../ai-rooms-script/docusaurus/docusaurus-docs/docs/ai-features.md). 


## Testing & Lint

Like all Rooms AI deployments, addons should be roughly tested.

A basic PyTest is setup with a cicd to require 90% coverage in tests. Else it will not deploy the new release.

We also have ruff set up in cicd.

### Running the Tests

```bash
poetry run pytest tests/ --cov=src/template_rooms_pkg --cov-report=term-missing
```

### Running the linter

```bash
poetry run ruff check . --fix
```

### Pull Requests & versioning

Like for all deployments, we use semantic versioning in cicd to automatize the versions.

For this, use the apprioriate commit message syntax for semantic release in github.


## Developers / Mainteners

- Adrien EPPLING :  [Contact me](adrienesofts@gmail.com)
