from fastapi import APIRouter, Request
from typing import Dict, Any, List, Optional, Union
import boto3
import json
import os
import openai
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import time
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio

# Import tool configurations
from .tools import get_enabled_tools

# Import OpenAI utilities
from .openai_utils import (
    initialize_openai_client,
    transform_bedrock_to_openai,
    transform_openai_to_bedrock,
    create_error_stream,
    create_streaming_error_response,
    generate_bedrock_format_stream
)

"""
Tool-Bot FastAPI Router

This module serves as a thin pass-through API layer for the Tool-Bot system.
Important implementation notes:

1. All tools are implemented in TypeScript and executed client-side in the browser
2. No tool execution happens in this Python server
3. This server only handles:
   - LLM API credential management via AWS Secrets
   - Format transformation between OpenAI and Bedrock
   - Secure pass-through of requests/responses
4. The /invoke endpoint merely acknowledges tool invocation requests
   but doesn't execute any tools (execution happens in client TypeScript)
"""

# Load environment variables from .env file if present
load_dotenv()

# Import the secrets management module
try:
    from thisapp.secrets import Secrets
    HAS_SECRETS = True
    print("Successfully imported thisapp.secrets module")
except ImportError:
    print("Warning: Could not import thisapp.secrets module. Using environment variables for credentials.")
    Secrets = None
    HAS_SECRETS = False

# Create router with tags but without prefix to allow direct route mapping
router = APIRouter(tags=["ai"])

# Get AI provider from environment (default: openai)
AI_PROVIDER = "openai"  # Force to openai as requested

# Apply secrets to environment if available
if HAS_SECRETS:
    try:
        print("Applying secrets from AWS Secrets Manager...")
        # Important: Set APPLICATION variable if required by secrets module
        if not os.environ.get('APPLICATION'):
            os.environ['APPLICATION'] = 'tech-primer'  # Adjust application name if needed

        Secrets.apply_environment_secrets()
        print("Successfully applied secrets from AWS Secrets Manager")
    except Exception as e:
        print(f"Warning: Failed to apply secrets: {e}")

# Print API key for debugging (masked for security)
api_key = os.environ.get("OPENAI_API_KEY", "")
if api_key:
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
    print(f"Using OpenAI API key: {masked_key}")
else:
    print("WARNING: No OpenAI API key found in environment variables")

# Initialize OpenAI client as None initially
openai_client = None

# Try to initialize Bedrock client
try:
    if AI_PROVIDER == "bedrock" or os.environ.get("AWS_ACCESS_KEY"):
        bedrock_client = boto3.client(service_name='bedrock-runtime')
except Exception as e:
    print(f"Warning: Could not initialize Bedrock client: {e}")

# Try to initialize OpenAI client
try:
    if AI_PROVIDER == "openai" or os.environ.get("OPENAI_API_KEY"):
        # Using OpenAI client with credentials from environment (set by Secrets.apply_environment_secrets())
        openai_client = openai.OpenAI()  # No explicit parameters needed as they're read from environment
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")

@router.post("/api/ai")  # Main AI endpoint
async def handle_chat(request: Request):
    """
    Main AI endpoint that matches the original Express API.
    """
    try:
        # Parse the request body
        body = await request.json()

        # Client always sends data in Bedrock format
        messages = body.get("messages", [])
        model_id = body.get("modelId", "")
        stream = True  # Always use streaming mode for consistent response structure
        system_prompt = body.get("systemPrompt", "You are a helpful assistant. (toolKit)")
        enabled_tools = body.get("enabledTools", [])

        # Require model_id to be provided by client
        if not model_id:
            error_msg = "Model ID is required. Please provide a valid model ID."
            print(f"Error: {error_msg}")
            return StreamingResponse(
                create_error_stream(error_msg),
                media_type="application/json",
                headers={"Cache-Control": "no-cache"}
            )

        # Log request information
        print(f"Received request for model: {model_id}")
        print(f"System prompt provided: {bool(system_prompt)}")
        print(f"Enabled tools: {enabled_tools}")

        # Initialize OpenAI client for this request
        client = initialize_openai_client()
        if not client:
            error_msg = "Failed to initialize OpenAI client"
            print(error_msg)
            return StreamingResponse(
                create_error_stream(error_msg),
                media_type="application/json",
                headers={"Cache-Control": "no-cache"}
            )

        # Transform from Bedrock format to OpenAI format
        openai_messages = transform_bedrock_to_openai(messages)

        # Debug logging for message transformation
        print(f"Original messages count: {len(messages)}")
        print(f"Transformed messages count: {len(openai_messages)}")
        print(f"Last message role: {openai_messages[-1]['role'] if openai_messages else 'none'}")

        # Use system prompt if provided
        if system_prompt:
            openai_messages.insert(0, {"role": "system", "content": system_prompt})
            print(f"Added system prompt, new message count: {len(openai_messages)}")

        # Ensure the conversation is valid
        if not openai_messages:
            error_msg = "No valid messages to process"
            return StreamingResponse(
                create_error_stream(error_msg),
                media_type="application/json",
                headers={"Cache-Control": "no-cache"}
            )

        try:
            start_time = time.time()

            # Get the tool configurations for the enabled tools
            tools_config = get_enabled_tools(enabled_tools)

            # Create a streaming response using OpenAI's streaming API
            openai_stream = client.chat.completions.create(
                model=model_id,  # Use the model ID provided by the client
                messages=openai_messages,
                tools=tools_config if tools_config else None,
                tool_choice="auto" if tools_config else None,
                stream=True  # Always stream from OpenAI
            )

            # Return a streaming response with proper headers to prevent buffering
            return StreamingResponse(
                generate_bedrock_format_stream(openai_stream),
                media_type="application/json",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "Connection": "keep-alive",
                    "Transfer-Encoding": "chunked"
                }
            )

        except openai.BadRequestError as api_error:
            print(f"OpenAI API error: {str(api_error)}")
            error_msg = f"Error code: {api_error.status_code} - {api_error.response.json()}"
            return create_streaming_error_response(error_msg)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            error_msg = f"Unexpected error: {str(e)}"
            return create_streaming_error_response(error_msg)
    except Exception as e:
        print(f"Global error in handle_chat: {str(e)}")
        error_msg = f"Server error: {str(e)}"
        return create_streaming_error_response(error_msg)

@router.post("/api/ai/invoke")  # Tool invocation endpoint
async def invoke_tool(request: Request):
    """
    Simple chat completion endpoint for non-streaming summary requests.
    Returns responses in AWS Bedrock ConverseResponse format.
    """
    try:
        # Parse the request body
        body = await request.json()

        # Initialize OpenAI client for this request
        client = initialize_openai_client()
        if not client:
            error_msg = "Failed to initialize OpenAI client"
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": error_msg}]
                    }
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                },
                "metrics": {
                    "latencyMs": 0
                }
            }

        # Get required fields
        messages = body.get("messages", [])
        model_id = body.get("modelId", "")
        system_prompt = body.get("systemPrompt", "")

        # Require model_id to be provided by client
        if not model_id:
            error_msg = "Model ID is required. Please provide a valid model ID."
            print(f"Error: {error_msg}")
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": f"Error: {error_msg}"}]
                    }
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                },
                "metrics": {
                    "latencyMs": 0
                }
            }

        # Log the received model ID
        print(f"Received model ID: '{model_id}'")

        # Use model ID exactly as provided by the client
        # Do not modify or transform the model ID
        start_time = time.time()

        # Transform from Bedrock format to OpenAI format
        openai_messages = transform_bedrock_to_openai(messages)

        # Add system prompt if provided
        if system_prompt:
            openai_messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            # Call OpenAI API without streaming
            print(f"Calling OpenAI API with model ID: '{model_id}'")
            response = client.chat.completions.create(
                model=model_id,  # Use the model ID exactly as provided by the client
                messages=openai_messages,
                stream=False
            )

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract the message content and return in AWS Bedrock ConverseResponse format
            assistant_message = response.choices[0].message

            # Format in AWS Bedrock ConverseResponse structure
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": assistant_message.content}]
                    }
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": response.usage.prompt_tokens,
                    "outputTokens": response.usage.completion_tokens,
                    "totalTokens": response.usage.total_tokens
                },
                "metrics": {
                    "latencyMs": latency_ms
                }
            }

        except Exception as api_error:
            # Handle API errors specifically
            error_msg = f"Error code: {getattr(api_error, 'status_code', 400)} - {str(api_error)}"
            print(f"API error: {error_msg}")
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": f"Error: {error_msg}"}]
                    }
                },
                "stopReason": "end_turn",
                "usage": {
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "totalTokens": 0
                },
                "metrics": {
                    "latencyMs": int((time.time() - start_time) * 1000)
                }
            }

    except Exception as e:
        print(f"Chat completion error: {str(e)}")
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": f"Error: {str(e)}"}]
                }
            },
            "stopReason": "end_turn",
            "usage": {
                "inputTokens": 0,
                "outputTokens": 0,
                "totalTokens": 0
            },
            "metrics": {
                "latencyMs": 0
            }
        }
