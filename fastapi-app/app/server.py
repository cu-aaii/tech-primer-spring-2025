from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Import our Tool-Bot router
from .toolbot.router import router as ai_router

"""
FastAPI application entry point with Tool-Bot integration.

This server serves as a minimal pass-through for Tool-Bot, with all actual
tool implementations remaining in TypeScript. No Python tool implementations
should exist in this codebase.

The TypeScript tools are located in tool-bot/tools/ and are executed client-side.
This server only handles API transformations and credential management.
"""

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize any resources here
    # This will run when the app starts
    print("🚀 Starting FastAPI application with Tool-Bot integration")
    yield
    # Clean up any resources here
    # This will run when the app shuts down
    print("💤 Shutting down FastAPI application")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the AI router - Note: prefix is already set in the router
app.include_router(ai_router)

# Add a static files mount for Tool-Bot frontend
toolbot_static_dir = os.path.join(os.path.dirname(__file__), "toolbot/static")
if os.path.exists(toolbot_static_dir):
    app.mount("/", StaticFiles(directory=toolbot_static_dir, html=True), name="toolbot")

@app.get('/health')
async def health():
    return {'status': 'healthy'}

@app.get('/api')
async def api_info():
    return {
        'message': 'FastAPI server is running',
        'endpoints': {
            'health': '/health',
            'ai': '/api/ai',
            'ai_invoke': '/api/ai/invoke'
        }
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
