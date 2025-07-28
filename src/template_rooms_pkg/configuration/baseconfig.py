from typing import Any, Dict
from pydantic import BaseModel, Field


class BaseAddonConfig(BaseModel):    
    id: str = Field(..., description="Unique identifier for the addon")
    type: str = Field(..., description="Type of the addon")
    name: str = Field(..., description="Display name of the addon")
    description: str = Field(..., description="Description of the addon")
    enabled: bool = Field(True, description="Whether the addon is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="General configuration settings")
    secrets: Dict[str, str] = Field(default_factory=dict, description="Environment variable names for secrets")
    
    class Config:
        extra = "allow"
        validate_assignment = True