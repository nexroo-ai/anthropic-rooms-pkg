from loguru import logger
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
import anthropic
import os
from pathlib import Path

from .base import ActionResponse, OutputBase, TokensSchema
from anthropic_rooms_pkg.configuration import CustomAddonConfig
from anthropic_rooms_pkg.services.credentials import CredentialsRegistry


class FileUpload(BaseModel):
    file_path: str = Field(..., description="Path to file to upload")
    filename: Optional[str] = Field(None, description="Custom filename (uses file_path basename if not provided)")
    purpose: str = Field("analysis", description="Purpose of file upload")


class ActionInput(BaseModel):
    message: str = Field(..., description="Question or instruction about the file")
    file_upload: Optional[FileUpload] = Field(None, description="File to upload and analyze")
    file_id: Optional[str] = Field(None, description="ID of already uploaded file")
    max_tokens: Optional[int] = Field(None, description="Max tokens (overrides config default)")
    temperature: Optional[float] = Field(None, description="Temperature (overrides config default)")


class FileInfo(BaseModel):
    id: str = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="File type")


class ActionOutput(OutputBase):
    response: str = Field(..., description="Claude's analysis of the file")
    file_info: Optional[FileInfo] = Field(None, description="Information about uploaded file")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage information")
    stop_reason: Optional[str] = Field(None, description="Why Claude stopped generating")


def file_analysis(
    config: CustomAddonConfig,
    message: str,
    file_upload: Optional[FileUpload] = None,
    file_id: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> ActionResponse:
    logger.debug(f"Executing file_analysis with message: {message[:100]}...")
    
    if not file_upload and not file_id:
        raise ValueError("Either file_upload or file_id must be provided")
    
    if file_upload and file_id:
        raise ValueError("Cannot provide both file_upload and file_id")
    
    try:
        credentials = CredentialsRegistry()
        api_key = credentials.get("anthropic_api_key")
        
        if not api_key:
            raise ValueError("Anthropic API key not found in credentials")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        model_to_use = config.model
        max_tokens_to_use = max_tokens or config.max_tokens
        temperature_to_use = temperature or config.temperature
        
        uploaded_file_info = None
        current_file_id = file_id
        
        if file_upload:
            logger.debug(f"Uploading file: {file_upload.file_path}")
            
            if not os.path.exists(file_upload.file_path):
                raise ValueError(f"File not found: {file_upload.file_path}")
            
            filename = file_upload.filename or Path(file_upload.file_path).name
            
            with open(file_upload.file_path, "rb") as f:
                file_response = client.files.create(
                    file=f,
                    purpose=file_upload.purpose
                )
            
            current_file_id = file_response.id
            uploaded_file_info = FileInfo(
                id=file_response.id,
                filename=filename,
                size_bytes=file_response.size_bytes,
                type=file_response.type
            )
            
            logger.info(f"File uploaded successfully: {filename} (ID: {current_file_id})")
        
        api_params = {
            "model": model_to_use,
            "max_tokens": max_tokens_to_use,
            "messages": [{"role": "user", "content": message}]
        }
        
        if current_file_id:
            try:
                api_params["attachments"] = [{"file_id": current_file_id, "tools": [{"type": "file_search"}]}]
            except Exception:
                api_params["files"] = [{"id": current_file_id, "purpose": "analysis"}]
        
        if temperature_to_use is not None:
            api_params["temperature"] = temperature_to_use
        
        logger.debug(f"Analyzing file with Anthropic API using model: {model_to_use}")
        
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
            file_info=uploaded_file_info,
            model=model_to_use,
            usage=usage_info,
            stop_reason=response.stop_reason
        )
        
        logger.info(f"File analysis successful. Used {usage_info['total_tokens']} tokens.")
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message="File analysis successful",
            code=200
        )
        
    except Exception as e:
        logger.error(f"File analysis failed: {str(e)}")
        
        tokens = TokensSchema(stepAmount=0, totalCurrentAmount=0)
        output = ActionOutput(
            response=f"Error: {str(e)}",
            file_info=None,
            model=config.model,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            stop_reason="error"
        )
        
        return ActionResponse(
            output=output,
            tokens=tokens,
            message=f"File analysis failed: {str(e)}",
            code=500
        )