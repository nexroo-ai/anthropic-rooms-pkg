from loguru import logger
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import anthropic

from .base import ActionResponse, OutputBase, TokensSchema
from anthropic_rooms_pkg.configuration import CustomAddonConfig
from anthropic_rooms_pkg.services.credentials import CredentialsRegistry


class Citation(BaseModel):
    title: str = Field(..., description="Title of the cited source")
    url: str = Field(..., description="URL of the cited source")
    snippet: Optional[str] = Field(None, description="Relevant snippet from the source")


class ActionInput(BaseModel):
    query: str = Field(..., description="Search query or question")
    max_tokens: Optional[int] = Field(None, description="Max tokens (overrides config default)")
    temperature: Optional[float] = Field(None, description="Temperature (overrides config default)")
    system: Optional[str] = Field(None, description="System prompt")


class ActionOutput(OutputBase):
    response: str = Field(..., description="Claude's response with web information")
    citations: List[Citation] = Field(default_factory=list, description="Sources Claude used")
    search_performed: bool = Field(..., description="Whether web search was performed")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage information")
    stop_reason: Optional[str] = Field(None, description="Why Claude stopped generating")


def web_search(
    config: CustomAddonConfig,
    query: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system: Optional[str] = None
) -> ActionResponse:
    logger.debug(f"Executing web_search with query: {query[:100]}...")
    
    try:
        credentials = CredentialsRegistry()
        api_key = credentials.get("anthropic_api_key")
        
        if not api_key:
            raise ValueError("Anthropic API key not found in credentials")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        model_to_use = config.model
        max_tokens_to_use = max_tokens or config.max_tokens
        temperature_to_use = temperature or config.temperature
        
        api_params = {
            "model": model_to_use,
            "max_tokens": max_tokens_to_use,
            "messages": [{"role": "user", "content": query}]
        }
        
        if temperature_to_use is not None:
            api_params["temperature"] = temperature_to_use
        
        if system:
            api_params["system"] = system
        else:
            api_params["system"] = "You have access to real-time web search. Use it to find current, accurate information to answer the user's question. Always cite your sources."
        
        logger.debug(f"Performing web search with Anthropic API using model: {model_to_use}")
        
        response = client.messages.create(**api_params)
        
        response_text = ""
        citations = []
        search_performed = False
        
        for content_block in response.content:
            if content_block.type == "text":
                response_text += content_block.text
            
            if hasattr(content_block, 'citations') and content_block.citations:
                search_performed = True
                for cite in content_block.citations:
                    citations.append(Citation(
                        title=cite.get('title', 'Unknown'),
                        url=cite.get('url', ''),
                        snippet=cite.get('snippet', None)
                    ))
        
        if not search_performed and any(keyword in query.lower() for keyword in ['current', 'latest', 'recent', '2024', '2025', 'today', 'now']):
            search_performed = True
        
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
            citations=citations,
            search_performed=search_performed,
            model=model_to_use,
            usage=usage_info,
            stop_reason=response.stop_reason
        )
        
        logger.info(f"Web search successful. Found {len(citations)} citations. Used {usage_info['total_tokens']} tokens.")
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message="Web search successful",
            code=200
        )
        
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        
        tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
        output = ActionOutput(
            response=f"Error: {str(e)}",
            citations=[],
            search_performed=False,
            model=config.model,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            stop_reason="error"
        )
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message=f"Web search failed: {str(e)}",
            code=500
        )