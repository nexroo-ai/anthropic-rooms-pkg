from pydantic import Field, model_validator
from .baseconfig import BaseAddonConfig


class CustomAddonConfig(BaseAddonConfig):
    type: str = Field("database", description="Database addon type")
    host: str = Field(..., description="Database host")
    database: str = Field(..., description="Database name")
    port: int = Field(5432, description="Database port")
    
    @model_validator(mode='after')
    def validate_db_secrets(self):
        required_secrets = ["db_password", "db_user"]
        missing = [s for s in required_secrets if s not in self.secrets]
        if missing:
            raise ValueError(f"Missing database secrets: {missing}")
        return self