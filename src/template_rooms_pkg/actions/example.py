from loguru import logger
from typing import Optional
from pydantic import BaseModel

from .base import ActionResponse, OutputBase, TokensSchema
from template_rooms_pkg.configuration import CustomAddonConfig
from template_rooms_pkg.services.credentials import CredentialsRegistry

class ActionInput(BaseModel):
    param1: str
    param2: str

class ActionOutput(OutputBase):
    data: Optional[dict] = None

# entrypoint is always the same name as the action file name.
# the script use the function name, to simplify we will use the same name as the file.
def example(config: CustomAddonConfig, param1: str, param2: str) -> ActionResponse:
    # if not isinstance(inputs, ActionInput):
    #     raise ValueError("Invalid input type. Expected ActionInput.")
    logger.debug("Template rooms package - Example action executed successfully!")
    logger.debug(f"Input received: {param1}, {param2}")
    logger.debug(f"Config: {config}")
    credentials = CredentialsRegistry()
    if credentials.has("db_user"):
        logger.debug(f"Database user available: {credentials.get('db_user')}")
    
    tokens = TokensSchema(stepAmount=2000, totalCurrentAmount=16236)
    message = "Action executed successfully"
    code = 200
    output = ActionOutput(data={"processed": param1 + "- processed -"})
    return ActionResponse(output=output, tokens=tokens, message=message, code=code)