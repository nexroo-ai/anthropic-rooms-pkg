from loguru import logger
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import anthropic

from .base import ActionResponse, OutputBase, TokensSchema
from anthropic_rooms_pkg.configuration import CustomAddonConfig


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ActionInput(BaseModel):
    message: str = Field(..., description="User message to send to Claude")
    messages: Optional[List[ChatMessage]] = Field(None, description="Full conversation history")
    max_tokens: Optional[int] = Field(None, description="Max tokens (overrides config default)")
    temperature: Optional[float] = Field(None, description="Temperature (overrides config default)")
    system: Optional[str] = Field(None, description="System prompt")


class ActionOutput(OutputBase):
    response: str = Field(..., description="Claude's response")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage information")
    stop_reason: Optional[str] = Field(None, description="Why Claude stopped generating")


def chat_completion(
    config: CustomAddonConfig,
    message: str,
    messages: Optional[List[ChatMessage]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system: Optional[str] = None
) -> ActionResponse:
    logger.debug(f"Executing chat_completion with message: {message[:100]}...")
    
    try:
        # credentials = CredentialsRegistry()
        # api_key = credentials.get("anthropic_api_key")
        logger.debug(f'SECRETS: {config.secrets}')
        api_key = config.secrets['anthropic_api_key']
        if not api_key:
            raise ValueError("Anthropic API key not found in credentials")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        model_to_use = config.model
        max_tokens_to_use = max_tokens or config.max_tokens
        temperature_to_use = temperature or config.temperature
        
        conversation_messages = []
        
        if messages:
            for msg in messages:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        conversation_messages.append({
            "role": "user",
            "content": message
        })
        
        api_params = {
            "model": model_to_use,
            "max_tokens": max_tokens_to_use,
            "messages": conversation_messages
        }
        
        if temperature_to_use is not None:
            api_params["temperature"] = temperature_to_use
        
        if system:
            api_params["system"] = system
        
        logger.debug(f"Calling Anthropic API with model: {model_to_use}")
        
        response = client.messages.create(**api_params)
        
        response_text = ""
        if response.content and len(response.content) > 0:
            response_text = response.content[0].text
        
        usage_info = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
        
        tokens = TokensSchema(
            stepAmount=usage_info["output_tokens"],
            totalCurrentAmount=usage_info["total_tokens"]
        )
        
        output = ActionOutput(
            response=response_text,
            model=model_to_use,
            usage=usage_info,
            stop_reason=response.stop_reason
        )
        
        logger.info(f"Chat completion successful. Used {usage_info['total_tokens']} tokens.")
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message="Chat completion successful",
            code=200
        )
        
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        
        tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
        output = ActionOutput(
            response=f"Error: {str(e)}",
            model=config.model,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            stop_reason="error"
        )
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message=f"Chat completion failed: {str(e)}",
            code=500
        )