"""
OpenAI Utilities for Tool-Bot

This module contains utility functions for working with OpenAI's API:
1. Client initialization
2. Format transformation between Bedrock and OpenAI messages
3. Common streaming response generators
"""

import os
import json
import time
import openai
import asyncio
from typing import Dict, Any, List, Optional, Union, AsyncGenerator

from fastapi.responses import StreamingResponse

def initialize_openai_client():
    """Initialize OpenAI client using environment variables loaded from AWS Secrets."""
    try:
        # Get API key from environment (should be loaded by AWS Secrets Manager)
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE")

        if not api_key:
            print("ERROR: No OpenAI API key found in environment variables")
            return None

        # Create client with credentials from environment
        client = openai.OpenAI(
            api_key=api_key,
            base_url=api_base if api_base else None
        )
        print("Successfully initialized OpenAI client")

        # Log the API base URL for debugging
        print(f"Using API base URL: {api_base if api_base else 'default OpenAI endpoint'}")

        return client
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None

def transform_bedrock_to_openai(bedrock_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform Bedrock format messages to OpenAI format.

    The client sends messages in various formats:
    1. Regular user/assistant messages:
       {
           "id": "msg_1",
           "role": "user",
           "content": [{"text": "hi"}],
           "metadata": {...}
       }

    2. Tool use by assistant:
       {
           "role": "assistant",
           "content": [
               {"text": "I'll calculate that"},
               {"toolUse": {"name": "math", "toolUseId": "tool_123", "input": {"expression": "sqrt(277)"}}}
           ]
       }

    3. Tool result from user:
       {
           "role": "user",
           "content": [
               {"toolResult": {"toolUseId": "tool_123", "content": [{"text": "{\"result\":16.64...}"}], "status": "success"}}
           ]
       }

    We need to transform these to OpenAI format.
    """
    # Debug the incoming messages
    for i, msg in enumerate(bedrock_messages):
        print(f"[DEBUG] Incoming message {i}: role={msg.get('role', 'unknown')}")
        if msg.get("content") and isinstance(msg.get("content"), list):
            for content_item in msg.get("content"):
                if content_item.get("toolUse"):
                    print(f"  - Contains toolUse: {content_item.get('toolUse').get('name')}")
                elif content_item.get("toolResult"):
                    print(f"  - Contains toolResult: {content_item.get('toolResult').get('toolUseId')}")

    openai_messages = []

    for i, message in enumerate(bedrock_messages):
        role = message.get("role", "user")
        content_blocks = message.get("content", [])

        # Check for tool results in user messages (convert to tool response)
        if role == "user" and isinstance(content_blocks, list):
            has_tool_result = False
            for block in content_blocks:
                if isinstance(block, dict) and "toolResult" in block:
                    has_tool_result = True
                    tool_result = block.get("toolResult", {})
                    tool_use_id = tool_result.get("toolUseId", "")
                    result_content = ""

                    # Extract the result content
                    for content_item in tool_result.get("content", []):
                        if isinstance(content_item, dict) and "text" in content_item:
                            result_content += content_item.get("text", "")

                    # Add a tool message instead of a user message
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_use_id,
                        "content": result_content.strip()
                    })
                    print(f"[DEBUG] Transformed tool result to tool message: {tool_use_id}")

            # Skip to next message if we handled a tool result
            if has_tool_result:
                continue

        # Handle regular content and tool use in assistant messages
        if isinstance(content_blocks, list):
            # Extract regular text content
            text_content = []
            tool_use = None

            for block in content_blocks:
                if isinstance(block, dict):
                    if "text" in block:
                        text_content.append(block.get("text", ""))
                    elif "toolUse" in block:
                        tool_use = block.get("toolUse", {})

            # Combine text content
            combined_text = " ".join(text_content).strip()

            # Create message based on content type
            if role == "assistant" and tool_use:
                # Assistant with tool use
                openai_message = {
                    "role": "assistant",
                    "content": combined_text if combined_text else None,
                    "tool_calls": [{
                        "id": tool_use.get("toolUseId", ""),
                        "type": "function",
                        "function": {
                            "name": tool_use.get("name", ""),
                            "arguments": json.dumps(tool_use.get("input", {}))
                        }
                    }]
                }
                print(f"[DEBUG] Created assistant message with tool call: {tool_use.get('name', '')}")
            else:
                # Regular message
                openai_message = {
                    "role": role,
                    "content": combined_text
                }
                print(f"[DEBUG] Created regular {role} message")

            openai_messages.append(openai_message)
        elif isinstance(content_blocks, str):
            # Handle simple string content
            openai_messages.append({
                "role": role,
                "content": content_blocks
            })

    # Validate the final result
    if openai_messages and openai_messages[-1].get("role") == "assistant":
        # Remove the last message if it's an assistant to prevent errors
        openai_messages = openai_messages[:-1]
        print("[DEBUG] Warning: Removed trailing assistant message to avoid validation error")

    print(f"[DEBUG] Final transformed messages ({len(openai_messages)}):")
    for i, msg in enumerate(openai_messages):
        print(f"  {i}: role={msg.get('role')}, tool_calls={bool(msg.get('tool_calls'))}")

    return openai_messages

def transform_openai_to_bedrock(openai_response: Dict[str, Any], start_time: float = None) -> Dict[str, Any]:
    """
    Transform an OpenAI response to a format compatible with the client.

    The client expects a response in this format:
    {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Hello! How can I help you today?"
            }
        ]
    }

    Or for tool calls:
    {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll create a visualization for you."
            }
        ],
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "html",
                    "arguments": "{\"html\":\"<div>...</div>\",\"css\":\"...\",\"javascript\":\"...\"}"
                }
            }
        ]
    }
    """
    if not start_time:
        start_time = time.time()

    # Extract message from OpenAI response
    message = openai_response.choices[0].message
    message_content = message.content or ""

    # Start with basic message structure
    result = {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": message_content
            }
        ]
    }

    # If there are tool calls, add them to the response
    if hasattr(message, 'tool_calls') and message.tool_calls:
        tool_calls = []
        for tool_call in message.tool_calls:
            tool_calls.append({
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            })

        result["tool_calls"] = tool_calls

    return result

async def create_error_stream(error_msg: str) -> AsyncGenerator[str, None]:
    """
    Create a standardized error stream in the Bedrock format.

    Args:
        error_msg: The error message to include in the stream

    Returns:
        An async generator that yields formatted JSON strings
    """
    # Send message start
    yield json.dumps({
        "messageStart": {
            "role": "assistant",
        },
    }) + "\n"

    # Send error content
    yield json.dumps({
        "contentBlockDelta": {
            "contentBlockIndex": 0,
            "delta": {
                "text": f"Error: {error_msg}",
            },
        },
    }) + "\n"

    # Send message stop
    yield json.dumps({
        "messageStop": {
            "stopReason": "error",
        },
    }) + "\n"

def create_streaming_error_response(error_msg: str) -> StreamingResponse:
    """
    Create a StreamingResponse with a standardized error message.

    Args:
        error_msg: The error message to include in the stream

    Returns:
        A FastAPI StreamingResponse object
    """
    return StreamingResponse(
        create_error_stream(error_msg),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }
    )

async def generate_bedrock_format_stream(openai_stream):
    """
    Generate a stream of JSON chunks in Bedrock format from an OpenAI stream.

    Each chunk is yielded immediately as it's received from the OpenAI API,
    with no buffering, ensuring real-time streaming to the client.

    Args:
        openai_stream: The OpenAI streaming response object

    Returns:
        An async generator that yields formatted JSON strings
    """
    # Initialize variables to track state
    is_first_chunk = True
    tool_use_started = False
    current_tool_id = None

    try:
        # Send the initial messageStart immediately
        start_chunk = json.dumps({
            "messageStart": {
                "role": "assistant",
            },
        }) + "\n"
        yield start_chunk
        await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

        # Create an async iterator from the OpenAI stream
        async def process_stream():
            for chunk in openai_stream:
                yield chunk
                await asyncio.sleep(0)

        # Process chunks as they arrive
        async for chunk in process_stream():
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Handle content - yield immediately
            if delta.content:
                content_chunk = json.dumps({
                    "contentBlockDelta": {
                        "contentBlockIndex": 0,
                        "delta": {
                            "text": delta.content,
                        },
                    },
                }) + "\n"
                yield content_chunk
                await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

            # Handle tool calls - yield each part immediately
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    # Check if we need to start a new tool use block
                    if not tool_use_started:
                        tool_use_started = True
                        current_tool_id = tool_call.id

                        # Send contentBlockStart for tool use
                        start_tool_chunk = json.dumps({
                            "contentBlockStart": {
                                "contentBlockIndex": 1,
                                "start": {
                                    "toolUse": {
                                        "name": tool_call.function.name,
                                        "toolUseId": tool_call.id
                                    }
                                }
                            }
                        }) + "\n"
                        yield start_tool_chunk
                        await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

                    # Tool argument updates
                    if tool_call.function and tool_call.function.arguments:
                        arg_chunk = json.dumps({
                            "contentBlockDelta": {
                                "contentBlockIndex": 1,
                                "delta": {
                                    "toolUse": {
                                        "input": tool_call.function.arguments
                                    }
                                }
                            }
                        }) + "\n"
                        yield arg_chunk
                        await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

            # Handle completion - yield immediately
            if finish_reason:
                # Close tool content block if it was started
                if tool_use_started:
                    stop_tool_chunk = json.dumps({
                        "contentBlockStop": {
                            "contentBlockIndex": 1
                        }
                    }) + "\n"
                    yield stop_tool_chunk
                    await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

                # Send message stop
                stop_reason = "tool_use" if finish_reason == "tool_calls" else ("end_turn" if finish_reason == "stop" else finish_reason)
                stop_chunk = json.dumps({
                    "messageStop": {
                        "stopReason": stop_reason
                    },
                }) + "\n"
                yield stop_chunk
                await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

    except Exception as stream_error:
        print(f"Streaming error: {str(stream_error)}")
        error_chunk = json.dumps({
            "contentBlockDelta": {
                "contentBlockIndex": 0,
                "delta": {
                    "text": f"Error during streaming: {str(stream_error)}",
                },
            },
        }) + "\n"
        yield error_chunk
        await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately

        stop_error_chunk = json.dumps({
            "messageStop": {
                "stopReason": "error",
            },
        }) + "\n"
        yield stop_error_chunk
        await asyncio.sleep(0)  # Ensure the event loop processes this chunk immediately
