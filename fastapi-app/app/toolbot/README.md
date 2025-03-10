# Tool-Bot Implementation

This module implements a thin pass-through API layer between a frontend that uses AWS Bedrock formats and the OpenAI API. It provides bidirectional format transformations while maintaining compatibility with existing client-side tools.

## Design Philosophy

The core philosophy of this implementation is:

1. **Client-First Approach**: Keep all tool implementations in the frontend (TypeScript)
2. **Format Compatibility**: Handle format differences between the client and OpenAI
3. **Secure API Key Management**: Use AWS Secrets Manager for API credentials
4. **Minimal Server Logic**: Keep the server as thin as possible
5. **Frontend-Driven Model Selection**: Model IDs are fully controlled by the frontend

## Model ID Handling

The server follows a strict pass-through approach for model IDs:

1. **Direct Forwarding**: Model IDs from the client are passed directly to the LLM API
2. **No Modification**: The server never modifies, transforms, or validates model IDs
3. **Client Configuration**: Available models are defined in the frontend's environment variables
4. **Error Transparency**: API errors related to invalid model IDs are returned directly to the client

This approach gives complete control to the frontend configuration and avoids embedding model assumptions in the server code, making the system more flexible and maintainable.

## Why Use AWS Bedrock Format?

We've chosen to maintain the AWS Bedrock format in the client for several reasons:

1. **Future Compatibility**: The AWS Bedrock format is robust and may be adopted more widely in the future
2. **Existing Client Code**: The frontend was already designed with this format in mind
3. **Flexible Architecture**: This approach allows us to switch between OpenAI and AWS Bedrock backends without client changes
4. **Easier Migration**: It's cleaner to transform formats server-side than to rewrite the entire client

While the current implementation uses OpenAI, the architecture is designed to allow seamless switching to AWS Bedrock or other providers in the future.

## Core Components

### Router (`router.py`)

The main router handles:
- Request parsing and validation
- Format transformation (bidirectional)
- API client management
- Error handling and streaming
- Tool configuration injection
- Pass-through model ID handling

The router implements two key endpoints:

1. **`/api/ai`**: Main chat endpoint that:
   - Extracts the model ID from the request (`modelId` parameter)
   - Passes it directly to the OpenAI API without validation or transformation
   - Supports streaming responses with proper AWS Bedrock format
   - Returns errors in a consistent Bedrock-compatible format

2. **`/api/ai/invoke`**: Non-streaming completion endpoint that:
   - Uses the exact model ID from the request
   - Returns responses in the AWS Bedrock ConverseResponse format
   - Provides detailed logging about the model ID being used

Both endpoints require a model ID to be provided by the client and will return an appropriate error if one is missing.

### Tool Definitions (`tools.py`)

Contains parallel definitions of tools for OpenAI compatibility:
- HTML tool for rendering web content
- Math tool for calculations

These definitions follow the OpenAI function calling format while the actual implementations remain in TypeScript.

## Format Transformation Challenges

### Bedrock to OpenAI

The transformation from AWS Bedrock format to OpenAI format involves:

1. **Message Structure**: Converting nested content blocks to flat content strings
2. **Tool Use**: Transforming `toolUse` blocks to OpenAI's `tool_calls` format
3. **Tool Results**: Converting user messages with `toolResult` to OpenAI's `tool` role messages

A critical challenge was handling tool results correctly, as OpenAI uses a different message structure (`role: "tool"`) compared to Bedrock's approach (user messages with `toolResult`).

### OpenAI to Bedrock

The reverse transformation involves:

1. **Content Structure**: Converting flat content to nested content blocks
2. **Streaming Chunks**: Formatting streaming responses with proper Bedrock-compatible events
3. **Tool Calls**: Converting OpenAI tool calls to Bedrock's toolUse format

Streaming proved particularly challenging, requiring careful event sequencing for `messageStart`, `contentBlockDelta`, and `messageStop` events.

## Streaming Implementation

Streaming responses required careful handling:

1. **Buffering Prevention**: Custom headers to prevent nginx/proxy buffering
2. **Async Handling**: Using `asyncio.sleep(0)` to ensure immediate chunk processing
3. **Tool Use States**: Tracking when tool use blocks start and end
4. **Chunked Transfer**: Proper line-delimited JSON chunks with newlines

## Validation Requirements

We discovered several validation requirements:

1. **Message Ordering**: OpenAI API rejects conversations where the final message is from the assistant
2. **Tool Conversion**: Tool results must be properly converted to the OpenAI tool format
3. **Content Block Markers**: Tool use streaming requires precise start/stop markers

## Error Handling Strategy

Errors are handled at multiple levels:

1. **API Errors**: Errors from the OpenAI API are caught and formatted for the client
2. **Streaming Errors**: Streaming-specific errors are embedded in the stream
3. **Format Errors**: Message format validation errors are prevented proactively
4. **Server Errors**: Unexpected errors are properly formatted for client consumption

## Future Enhancements

Potential future enhancements include:

1. **Pure AWS Backend**: Option to use AWS Bedrock directly without format transformation
2. **Caching**: Response caching for improved performance
3. **Rate Limiting**: Protection against excessive API usage
4. **Additional Tool Support**: Adding more tool types as needed
5. **Streaming Optimization**: Further improvements to streaming performance

## Related Documentation

- [FastAPI Application README](../../README.md): Overall application architecture and setup
- [Frontend Tools Documentation](../../../frontend/tools/README.md): Client-side tool implementations
- [TOOLBOT_MIGRATION.md](../../../../TOOLBOT_MIGRATION.md): Migration documentation
