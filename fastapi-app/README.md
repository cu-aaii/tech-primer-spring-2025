# FastAPI Application

This directory contains the FastAPI application that serves as a backend for our integrated tools system. The application is designed as a thin pass-through layer that securely connects to AI providers like OpenAI while serving a TypeScript-based frontend.

## Architecture

```
┌───────────────────┐    ┌───────────────────────────────────────┐    ┌───────────────┐
│                   │    │           FastAPI Application          │    │               │
│     Frontend      │    │                                       │    │   LLM APIs    │
│  (TypeScript/Vite)├────►  Router ───► Format  ───► AWS Secrets ├────►  (OpenAI/AWS) │
│                   │    │              Transform     Management  │    │               │
└───────────────────┘    └───────────────────────────────────────┘    └───────────────┘
```

The application follows a simple architecture:

1. **Client Request**: The browser-based TypeScript frontend sends requests to the FastAPI endpoints
2. **Router Handling**: The FastAPI router receives and processes the request
3. **Format Transformation**: Requests are transformed from AWS Bedrock format to OpenAI format
4. **API Calling**: The request is forwarded to the OpenAI API with proper authentication
5. **Response Transformation**: The response is transformed back to AWS Bedrock format
6. **Client Response**: The properly formatted response is sent back to the client

### Model ID Handling

An important aspect of the architecture is how model IDs are handled:

1. **Frontend Control**: Model IDs are configured and controlled entirely by the frontend via environment variables
2. **Pass-Through Approach**: The server passes model IDs directly to the LLM API without modification
3. **No Server Assumptions**: The server makes no assumptions about valid model names
4. **Environment Configuration**: Available models are defined in the frontend's `.env` file

This architecture ensures that model selection is fully controlled by the frontend configuration, making it easy to update or change available models without server-side code changes.

## Core Components

- **Server (`app/server.py`)**: Main FastAPI application entry point
- **Router (`app/toolbot/router.py`)**: API routing and request handling
- **Tools Config (`app/toolbot/tools.py`)**: Tool definitions for OpenAI API
- **Static Files (`app/toolbot/static/`)**: Compiled frontend assets

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai` | POST | Main AI endpoint for chat messages |
| `/api/ai/invoke` | POST | Tool invocation endpoint |
| `/health` | GET | Health check endpoint |
| `/api` | GET | API information endpoint |

## Environment Variables

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for authentication | (Required) |
| `OPENAI_API_BASE` | Base URL for OpenAI API | https://api.openai.com/v1 |
| `APPLICATION` | Application name for AWS Secrets | tech-primer |

### Frontend (Vite) Environment Variables

Environment variables for the frontend are defined in `frontend/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_AWS_LLM_OPTIONS` | AWS LLM model options | (Empty) |
| `VITE_OPENAI_LLM_OPTIONS` | OpenAI model options | anthropic.claude-3.5-sonnet.v2,openai.gpt-4o |
| `VITE_DEFAULT_MODEL` | Default model to use | anthropic.claude-3.5-sonnet.v2 |
| `VITE_API_ENDPOINT` | API endpoint for AI requests | /api/ai |
| `VITE_AI_PROVIDER` | AI Provider configuration | openai |

## Running the Application

### Development Mode

To run the application in development mode with hot-reloading:

```bash
cd fastapi-app
uvicorn app.server:app --reload
```

### Production Mode

For production deployment:

```bash
cd fastapi-app
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

**Open the browser and navigate to `http://localhost:8000` to view the application.**

## Building the Frontend

The frontend is built using Vite and requires Node.js version 20 or higher.

### Installing Node.js 20.x

If you need to build the frontend, first install Node.js:

```bash
# Add NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -

# Install Node.js and npm
apt-get install -y nodejs

# Verify installation
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x or higher
```

### Building the Frontend

Once Node.js is installed, you can build the frontend:

```bash
cd fastapi-app/frontend
npm install
npm run build
```

The build output will be placed in `app/toolbot/static/`.

### Development Mode

For development with hot-reloading:

```bash
cd fastapi-app/frontend
npm install
npm run dev
```

This will start the Vite development server, which proxies API requests to the FastAPI backend.

### Note

The repository ships with prebuilt static files, so you only need to install Node.js and rebuild if you're making changes to the frontend code.

## Deployment

For deployment options and Docker configuration, please refer to the main [Project README](../README.md) in the root of this repository.

## Secrets Management

The application integrates with AWS Secrets Manager through the `thisapp.secrets` module:

1. Import the module: `from thisapp.secrets import Secrets`
2. Apply secrets to environment: `Secrets.apply_environment_secrets()`
3. Access through environment variables: `os.environ.get("OPENAI_API_KEY")`

**Important Note:** If credentials in AWS Secrets Manager are updated or reset, you may need to restart the FastAPI server for the changes to take effect. This is because credentials are loaded at server startup time. If you encounter authentication errors after credential changes, try restarting the server.

## Format Transformation

The application handles bidirectional format transformation between:

1. **Frontend Format**: AWS Bedrock-compatible JSON format
2. **Backend Format**: OpenAI API format

This transformation is handled in `router.py` through the `transform_bedrock_to_openai` and `transform_openai_to_bedrock` functions.
