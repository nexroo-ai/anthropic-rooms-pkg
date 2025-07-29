from pydantic import Field, model_validator
from ..baseconfig import BaseAddonConfig


class CustomAddonConfig(BaseAddonConfig):
    """LLM addon - just inherit and add what you need"""
    
    # Override type with specific value
    type: str = Field("llm", description="LLM addon type")
    
    # Add new required fields
    provider: str = Field(..., description="LLM provider (openai, anthropic, etc)")
    model: str = Field(..., description="Model name")
    
    # Add optional fields with defaults
    temperature: float = Field(0.7, description="Temperature setting")
    max_tokens: int = Field(1000, description="Max tokens")
    
    @model_validator(mode='after')
    def validate_required_secrets(self):
        """Ensure required secrets are present"""
        if "api_key" not in self.secrets:
            raise ValueError("api_key secret is required")
        return self