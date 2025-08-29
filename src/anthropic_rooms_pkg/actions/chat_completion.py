from datetime import datetime
from typing import Dict, List, Optional

import anthropic
from loguru import logger
from pydantic import BaseModel, Field

from anthropic_rooms_pkg.configuration import CustomAddonConfig

from .base import ActionResponse, OutputBase, TokensSchema


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


### ADD TOOL REGISTERY FIRST BEFORE CHAT COMPLETION ##

def _parse_tool_input(tool_input: Dict, tool_name: str, tools: Dict) -> Dict:
    import json

    if not tool_input or tool_name not in tools:
        return tool_input

    tool_schema = tools[tool_name].get('input_schema', {})
    properties = tool_schema.get('properties', {})

    if not properties:
        return tool_input

    parsed_input = {}

    for param_name, param_value in tool_input.items():
        parsed_input[param_name] = param_value

        if param_name not in properties or not isinstance(param_value, str):
            continue

        param_schema = properties[param_name]
        param_type = param_schema.get('type')

        if param_type in ['object', 'array']:
            if param_value.strip().startswith(('{', '[')):
                parsed_value = None

                try:
                    parsed_value = json.loads(param_value)
                except json.JSONDecodeError:
                    try:
                        import ast
                        parsed_value = ast.literal_eval(param_value)
                    except (ValueError, SyntaxError):
                        pass

                if parsed_value is not None:
                    parsed_input[param_name] = parsed_value
                    logger.debug(f"Auto-parsed JSON for '{param_name}' in '{tool_name}'")
                else:
                    logger.warning(f"Could not parse JSON/literal for '{param_name}' in '{tool_name}'")
                    continue
            elif param_value.strip() in ['null', 'None', '']:
                parsed_input[param_name] = None if param_schema.get('default') is None else param_value

    return parsed_input

def _determine_tool_success(tool_result) -> bool:
    if hasattr(tool_result, 'code'):
        return tool_result.code < 400
    elif isinstance(tool_result, dict):
        code = tool_result.get('code')
        if code is not None and code >= 400:
            return False
    return True

def _extract_error_message(tool_result) -> str:
    if hasattr(tool_result, 'message') and hasattr(tool_result, 'code') and tool_result.code >= 400:
        return tool_result.message
    elif isinstance(tool_result, dict):
        code = tool_result.get('code')
        if code is not None and code >= 400:
            return tool_result.get('message', 'Tool execution completed with errors')
    return None

def _execute_tool_with_retries(tool_name, tool_input, tool_registry, tools, tool_retry_counts, conversation_messages, observer_callback, addon_id):
    max_retries = tool_registry.get_max_retries(tool_name)
    current_retry = tool_retry_counts.get(tool_name, 0)

    tool_function = tool_registry.get_function(tool_name)
    if not tool_function:
        return None, f"Tool {tool_name} not found"

    start_time = datetime.now()
    try:
        parsed_input = _parse_tool_input(tool_input, tool_name, tools)
        tool_result = tool_function(**parsed_input)
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        success = _determine_tool_success(tool_result)
        error_message = _extract_error_message(tool_result) if not success else None

        if observer_callback and addon_id:
            observer_callback(
                tool_name=tool_name,
                addon_id=addon_id,
                input_parameters=parsed_input,
                output_data=tool_result if isinstance(tool_result, dict) else {"result": tool_result},
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message,
                retry_attempt=current_retry,
                max_retries=max_retries
            )

        if success or current_retry >= max_retries:
            return tool_result, error_message
        else:
            tool_retry_counts[tool_name] = current_retry + 1
            if error_message:
                retry_message = f"The {tool_name} tool failed with error: {error_message}. Please try again with corrected parameters."
                conversation_messages.append({
                    "role": "user",
                    "content": retry_message
                })
            return "RETRY", error_message

    except Exception as e:
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        error_msg = str(e)

        if observer_callback and addon_id:
            observer_callback(
                tool_name=tool_name,
                addon_id=addon_id,
                input_parameters=parsed_input if 'parsed_input' in locals() else tool_input,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=error_msg,
                retry_attempt=current_retry,
                max_retries=max_retries
            )

        if current_retry >= max_retries:
            return None, error_msg
        else:
            tool_retry_counts[tool_name] = current_retry + 1
            retry_message = f"The {tool_name} tool failed with error: {error_msg}. Please try again with corrected parameters."
            conversation_messages.append({
                "role": "user",
                "content": retry_message
            })
            return "RETRY", error_msg

def chat_completion(
    config: CustomAddonConfig,
    message: str,
    messages: Optional[List[ChatMessage]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
    tools: Optional[Dict] = None,
    tool_registry = None,
    observer_callback = None,
    addon_id: str = None
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

        if tools:
            logger.debug(f"Using tools: {list(tools.keys())}")
            logger.debug(f"Tool definitions: {tools}")
            logger.debug(f"Tools being sent to AI model: {list(tools.keys())}")

            for tool_name, tool_def in tools.items():
                logger.debug(f"Tool '{tool_name}' description: {tool_def.get('description', 'No description')}")
                logger.debug(f"Tool '{tool_name}' input schema: {tool_def.get('input_schema', 'No schema')}")
            formatted_tools = []
            for action, tool_data in tools.items():
                formatted_tools.append(tool_data)
            api_params["tools"] = formatted_tools

        logger.debug(f"Calling Anthropic API with model: {model_to_use}")

        response = client.messages.create(**api_params)

        response_text = ""
        tool_results = []
        tool_retry_counts = {}

        if response.content:
            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
                elif content_block.type == "tool_use" and tool_registry:
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_id = content_block.id
                    logger.debug(f"Executing tool: {tool_name} with input: {tool_input}")

                    tool_result, error_message = _execute_tool_with_retries(
                        tool_name, tool_input, tool_registry, tools, tool_retry_counts,
                        conversation_messages, observer_callback, addon_id
                    )

                    if tool_result == "RETRY":
                        should_retry = True
                        continue
                    elif tool_result is not None:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": str(tool_result)
                        })
                        logger.debug(f"Tool {tool_name} executed successfully")
                    else:
                        logger.error(f"Tool {tool_name} execution failed: {error_message}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error executing tool: {error_message}"
                        })

        all_responses = [response]
        current_response = response

        should_retry = False
        while tool_results or should_retry:
            if not should_retry:
                conversation_messages.append({
                    "role": "assistant",
                    "content": current_response.content
                })

                conversation_messages.append({
                    "role": "user",
                    "content": tool_results
                })

            should_retry = False

            next_api_params = {
                "model": model_to_use,
                "max_tokens": max_tokens_to_use,
                "messages": conversation_messages
            }

            if temperature_to_use is not None:
                next_api_params["temperature"] = temperature_to_use

            if system:
                next_api_params["system"] = system

            if tools:
                formatted_tools = []
                for action, tool_data in tools.items():
                    formatted_tools.append(tool_data)
                next_api_params["tools"] = formatted_tools

            logger.debug("Calling Anthropic API again with tool results")
            current_response = client.messages.create(**next_api_params)
            all_responses.append(current_response)

            logger.debug(f"Second API response stop_reason: {current_response.stop_reason}")
            logger.debug(f"Second API response content blocks: {len(current_response.content)}")
            for i, block in enumerate(current_response.content):
                logger.debug(f"Content block {i}: type={block.type}")
                if block.type == "tool_use":
                    logger.debug(f"Tool use block: name={block.name}, input={block.input}")

            tool_results = []
            if current_response.content:
                for content_block in current_response.content:
                    if content_block.type == "text":
                        response_text += content_block.text
                    elif content_block.type == "tool_use" and tool_registry:
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_id = content_block.id

                        logger.debug(f"Executing additional tool: {tool_name} with input: {tool_input}")

                        tool_result, error_message = _execute_tool_with_retries(
                            tool_name, tool_input, tool_registry, tools, tool_retry_counts,
                            conversation_messages, observer_callback, addon_id
                        )

                        if tool_result == "RETRY":
                            should_retry = True
                            continue
                        elif tool_result is not None:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": str(tool_result)
                            })
                            logger.debug(f"Additional tool {tool_name} executed successfully")
                        else:
                            logger.error(f"Additional tool {tool_name} execution failed: {error_message}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": f"Error executing tool: {error_message}"
                            })

        if len(all_responses) > 1:
            usage_info = {
                "input_tokens": sum(r.usage.input_tokens for r in all_responses),
                "output_tokens": sum(r.usage.output_tokens for r in all_responses),
                "total_tokens": sum(r.usage.input_tokens + r.usage.output_tokens for r in all_responses)
            }
        else:
            usage_info = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

        tokens = TokensSchema(
            stepAmount=usage_info["total_tokens"],
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
