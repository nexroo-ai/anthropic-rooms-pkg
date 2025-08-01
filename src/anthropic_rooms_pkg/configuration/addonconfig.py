from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig


class CustomAddonConfig(BaseAddonConfig):
    model: str = Field("claude-3-5-sonnet-20241022", description="Default Anthropic model to use")
    max_tokens: int = Field(4096, description="Maximum tokens for responses")
    temperature: float = Field(0.7, description="Temperature for text generation")
    
    @model_validator(mode='after')
    def validate_anthropic_secrets(self):
        required_secrets = ["anthropic_api_key"]
        missing = [s for s in required_secrets if s not in self.secrets]
        if missing:
            raise ValueError(f"Missing Anthropic secrets: {missing}")
        return self