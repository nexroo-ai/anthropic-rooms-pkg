from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig, RequiredSecretsBase


class CustomRequiredSecrets(RequiredSecretsBase):
    anthropic_api_key: str = Field(..., description="Anthropic API key environment variable name")


class CustomAddonConfig(BaseAddonConfig):
    model: str = Field("claude-3-5-sonnet-20241022", description="Default Anthropic model to use")
    max_tokens: int = Field(4096, description="Maximum tokens for responses")
    temperature: float = Field(0.7, description="Temperature for text generation")
    
    @classmethod
    def get_required_secrets(cls) -> CustomRequiredSecrets:
        return CustomRequiredSecrets(anthropic_api_key="anthropic_api_key")
    
    @model_validator(mode='after')
    def validate_anthropic_secrets(self):
        required_secrets_config = self.get_required_secrets()
        required_secrets = list(required_secrets_config.model_fields.keys())
        missing = [s for s in required_secrets if s not in self.secrets]
        if missing:
            raise ValueError(f"Missing Anthropic secrets: {missing}")
        return self