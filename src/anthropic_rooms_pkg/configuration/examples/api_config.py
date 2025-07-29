from pydantic import Field, model_validator
from ..baseconfig import BaseAddonConfig


class CustomAddonConfig(BaseAddonConfig):
    """API addon example"""
    
    type: str = Field("api", description="API addon type")
    
    # Required API fields
    endpoint: str = Field(..., description="API endpoint URL")
    method: str = Field("GET", description="HTTP method")
    timeout: int = Field(30, description="Request timeout")
    
    @model_validator(mode='after')
    def validate_api_config(self):
        """Validate API configuration"""
        if "api_key" not in self.secrets:
            raise ValueError("api_key secret is required")
        
        if not self.endpoint.startswith(('http://', 'https://')):
            raise ValueError("endpoint must be a valid URL")
        
        return self