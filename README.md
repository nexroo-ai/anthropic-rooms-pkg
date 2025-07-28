# Template Rooms Package

A template Python package for the AI rooms script addon system.

## Overview

This package provides a basic template implementation for creating addon packages that can be loaded by the AI rooms script. It includes an addon class with a `test()` method that validates the package functionality.

## Installation

```bash
pip install -e .
```

## Usage

This package is designed to be imported by the AI rooms script's `loadAddons` functionality. The package provides an addon class that can be instantiated and used:

```python
from template_rooms_pkg.addon import TemplateRoomsAddon

# Instantiate the addon
addon = TemplateRoomsAddon()

# Test the addon functionality
result = addon.test()
```

The AI rooms script automatically discovers and instantiates the addon class from the `addon.py` module, so manual instantiation is typically not required in production use.

## Creating a New Addon from Template

To create a new addon package using this template:

1. **Clone or fork this repository**
2. **Rename the package directory and references:**
   - Rename `src/template_rooms_pkg/` to `src/{your_addon_name}_rooms_pkg/`
   - Update `pyproject.toml`:
     - Change package name from `template-rooms-pkg` to `{your-addon-name}-rooms-pkg`
     - Update module path in `[tool.setuptools.packages.find]`
   - Update imports in `src/{your_addon_name}_rooms_pkg/addon.py`
3. **Update the addon class:**
   - Rename `TemplateRoomsAddon` to `{YourAddonName}RoomsAddon` in `addon.py`
   - Customize the `test()` method and add your addon functionality
4. **Create configuration schema:**
   - Define your addon's configuration schema in `configuration/` directory
   - Inherit from `BaseAddonConfig` for validation
5. **Update documentation:**
   - Modify this README.md with your addon's specific information
   - Update the CHANGELOG.md

### Required File Structure
```
src/
└── {your_addon_name}_rooms_pkg/
    ├── __init__.py
    ├── addon.py              # Contains your addon class
    ├── actions/
    ├── configuration/
    ├── memory/
    ├── services/
    ├── storage/
    ├── tools/
    └── utils/
```

## CI/CD

The project uses semantic release for automated versioning and publishing:

- **Automated Versioning**: Semantic release analyzes commit messages to determine version bumps
- **Automated Publishing**: Releases are triggered automatically on pushes to the main branch
- **Commit Message Format**: Follow conventional commits format:
  - `feat:` for new features (minor version)
  - `fix:` for bug fixes (patch version)  
  - `BREAKING CHANGE:` for breaking changes (major version)

### Release Process
1. Push changes to main branch
2. Semantic release automatically:
   - Analyzes commit history
   - Determines next version number
   - Generates changelog
   - Creates GitHub release
   - Publishes to PyPI (if configured)

## Addon Configuration

### Setup Configuration Schema

1. **Create your config class** in `configuration/addonconfig.py`:

```python
from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig

class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("your_addon_type", description="Your addon type")
    
    # Add required fields
    required_field: str = Field(..., description="Required field")
    
    # Add optional fields with defaults
    optional_field: int = Field(30, description="Optional field")
    
    @model_validator(mode='after')
    def validate_configuration(self):
        # Validate required secrets
        if "required_secret" not in self.secrets:
            raise ValueError("required_secret is missing")
        
        # Add custom validation
        if self.optional_field < 0:
            raise ValueError("optional_field must be positive")
            
        return self
```

2. **Update** `configuration/__init__.py`:

```python
from .baseconfig import BaseAddonConfig
from .addonconfig import CustomAddonConfig

__all__ = ["BaseAddonConfig", "CustomAddonConfig"]
```

### Examples

See `configuration/examples/` for reference implementations:
- `llm_config.py` - LLM addon configuration
- `database_config.py` - Database addon configuration  
- `api_config.py` - API addon configuration

### JSON Configuration

The AI rooms script automatically validates this JSON against your schema during addon loading:

```json
{
    "id": "your-addon-1",
    "type": "your_addon_type",
    "name": "Your Addon",
    "description": "Your addon description",
    "enabled": true,
    "required_field": "value",
    "optional_field": 60,
    "config": {
        "extra_setting": "value"
    },
    "secrets": {
        "required_secret": "ENV_VAR_NAME"
    }
}
```

## Configuration Validation

The AI rooms script automatically handles configuration validation:

1. **Automatic Discovery**: The script automatically discovers your `CustomAddonConfig` class from `configuration/addonconfig.py`
2. **Validation During Loading**: Configuration is validated when the addon is loaded by the AI rooms script
3. **Error Reporting**: Detailed validation errors are displayed if configuration is invalid
4. **Fallback Support**: If `CustomAddonConfig` is not found, falls back to `BaseAddonConfig`

### Validation Process

```python
# The AI rooms script automatically does this:
from your_addon_rooms_pkg.configuration.addonconfig import CustomAddonConfig

# Validates your JSON configuration
validated_config = CustomAddonConfig(**your_json_config)
```

### Configuration Fields

All addon configurations inherit from `BaseAddonConfig` which provides:

- `id`: Unique identifier for the addon
- `type`: Type of the addon  
- `name`: Display name of the addon
- `description`: Description of the addon
- `enabled`: Whether the addon is enabled
- `config`: General configuration settings (Dict)
- `secrets`: Environment variable names for secrets (Dict)

Your `CustomAddonConfig` can add additional required or optional fields as needed.

## Credentials Configuration

When your addon requires secrets (API keys, passwords, etc.), configure them in your `CustomAddonConfig`:

### 1. Define Required Secrets

Use the `@model_validator` to specify which secrets your addon needs:

```python
from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig

class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("your_addon_type", description="Your addon type")
    
    # Your addon fields...
    host: str = Field(..., description="Database host")
    
    @model_validator(mode='after')
    def validate_secrets(self):
        # Define required secrets for your addon
        required_secrets = ["db_password", "db_user", "api_key"]
        missing = [s for s in required_secrets if s not in self.secrets]
        if missing:
            raise ValueError(f"Missing required secrets: {missing}")
        return self
```

### 2. Using Credentials in Actions

Access stored credentials from any action using the `CredentialsRegistry`:

```python
from template_rooms_pkg.services.credentials import CredentialsRegistry

def your_action(config: CustomAddonConfig, param1: str) -> ActionResponse:
    credentials = CredentialsRegistry()
    
    # Get required credentials
    db_password = credentials.get("db_password")
    api_key = credentials.get("api_key")
    
    # Check if credential exists before using
    if credentials.has("optional_secret"):
        optional_value = credentials.get("optional_secret")
    
    # Use credentials in your logic
    # ...
```

### 3. JSON Configuration Example

In your addon's JSON configuration, specify the environment variable names in the `secrets` field:

```json
{
    "id": "my-addon-1",
    "type": "your_addon_type", 
    "name": "My Addon",
    "description": "My addon description",
    "host": "localhost",
    "secrets": {
        "db_password": "DATABASE_PASSWORD",
        "db_user": "DATABASE_USER", 
        "api_key": "MY_API_KEY"
    }
}
```

The ai-rooms service will read the environment variables (`DATABASE_PASSWORD`, `DATABASE_USER`, `MY_API_KEY`) and pass their actual values to your addon.

### Credentials Registry API

The `CredentialsRegistry` provides these methods for accessing credentials:

- `get(key: str) -> Optional[str]` - Retrieve credential value
- `has(key: str) -> bool` - Check if credential exists  
- `keys() -> list` - Get list of available credential keys

**Note**: Credentials are automatically loaded and validated by the ai-rooms service. Your addon only needs to define what secrets it requires and how to use them.

## Actions Development

Actions are the core functionality of your addon. Each action is a function that processes inputs and returns standardized outputs.

### Action Structure

Every action must follow this structure:

```python
from loguru import logger
from typing import Optional
from pydantic import BaseModel

from .base import ActionResponse, OutputBase, TokensSchema
from template_rooms_pkg.configuration import CustomAddonConfig
from template_rooms_pkg.services.credentials import CredentialsRegistry

class ActionInput(BaseModel):
    param1: str
    param2: Optional[str] = None

class ActionOutput(OutputBase):
    result: str
    data: Optional[dict] = None

def your_action_name(config: CustomAddonConfig, param1: str, param2: str = None) -> ActionResponse:
    logger.debug(f"Executing your_action_name with params: {param1}, {param2}")
    
    # Access credentials if needed
    credentials = CredentialsRegistry()
    api_key = credentials.get("api_key")
    
    # Your action logic here
    result = f"Processed {param1}"
    
    # Create response
    tokens = TokensSchema(stepAmount=100, totalCurrentAmount=1000)
    output = ActionOutput(result=result, data={"processed": True})
    
    return ActionResponse(
        output=output,
        tokens=tokens,
        message="Action completed successfully",
        code=200
    )
```

### Required Components

1. **ActionInput** (Pydantic model): Defines expected input parameters
2. **ActionOutput** (inherits from `OutputBase`): Defines the structure of returned data
3. **Action function**: Must match the filename (e.g., `your_action_name.py` → `your_action_name()` function)

### ActionResponse Schema

Every action must return an `ActionResponse` with:

- `output: OutputBase` - Your custom output data
- `tokens: TokensSchema` - Token usage information:
  - `stepAmount: int` - Tokens used by this action
  - `totalCurrentAmount: int` - Total tokens used so far
- `message: Optional[str]` - Human-readable status message
- `code: Optional[int]` - HTTP-style status code (200 = success)

### Adding Actions to Addon

Register your actions in the main addon class (`addon.py`):

```python
from .actions.your_action_name import your_action_name

class TemplateRoomsAddon:
    def your_action_name(self, param1: str, param2: str = None) -> dict:
        return your_action_name(self.config, param1=param1, param2=param2)
```

### Action File Naming

- Action files should be named with snake_case: `my_action.py`
- The function inside must have the same name: `def my_action(...)`
- Register in addon class with the same name: `def my_action(...)`

## Development

### Code Quality Tools

This template includes automated code quality tools:

- **Ruff**: Fast Python linter and formatter that replaces multiple tools (flake8, black, isort, etc.)
- **Pre-commit**: Runs quality checks automatically before each commit to ensure consistent code quality

#### Using Ruff
```bash
# Lint and format code
ruff check .          # Check for linting issues
ruff format .         # Format code automatically
```

#### Pre-commit Setup
Pre-commit hooks are automatically installed when you install the package. They run Ruff checks before each commit:

```bash
# Manual pre-commit run
pre-commit run --all-files
```

The hooks will automatically fix formatting issues and prevent commits with linting errors.

### Release Process

The project uses semantic release for automated versioning. Releases are triggered automatically on pushes to the main branch.

## License

MIT