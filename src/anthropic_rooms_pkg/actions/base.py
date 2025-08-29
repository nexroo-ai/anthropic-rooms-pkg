from typing import Optional

from pydantic import BaseModel


class TokensSchema(BaseModel):
    stepAmount: int
    totalCurrentAmount: int


class OutputBase(BaseModel):
    """for output. Should be overwritted per action."""
    pass


class ActionResponse(BaseModel):
    output: OutputBase
    tokens: TokensSchema
    message: Optional[str] = None
    code: Optional[int] = None
