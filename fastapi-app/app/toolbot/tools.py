"""
Tool configurations for the Tool-Bot FastAPI server.

This module defines the tool configurations in the OpenAI function calling format:
https://platform.openai.com/docs/guides/function-calling

Each tool configuration includes:
- type: Always "function" for function calling
- function: The function definition containing:
  - name: The tool name
  - description: A detailed description of the tool's functionality
  - parameters: The schema for the tool's input parameters in JSON Schema format

Note: While the client-side uses AWS Bedrock's ToolConfiguration format, this server-side
implementation uses OpenAI's function calling format(a simple map can be used to convert between the two, the specs are very similiar). The router.py module handles
bidirectional transformation between these formats.

For more information on the transformation process, see the toolbot/README.md file.
"""

HTML_TOOL = {
    "type": "function",
    "function": {
        "name": "html",
        "description": """
Render HTML content in an isolated iframe environment. The iframe:
  - Receives HTML, CSS, and JavaScript inline and executes them securely.
  - Sends console output (console.log) back to the parent via postMessage.
  - Does not preserve state across render calls.

Requirements:
  - If loading images make sure to use : crossOrigin = "anonymous"
  - Escape special characters.
  - Use HTML5, CSS3, and modern ES6+ JavaScript.
  - Keep responses concise and inline.
  - No comments.

If additional data is provided:
  - It is accessible via `window.availableData`.
  - Wrap JavaScript in an IIFE that gracefully handles errors.
  - Keep the HTML a reusable template; place the JavaScript in a separate script tag to dynamically update the content with the data.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "Raw HTML markup"
                },
                "css": {
                    "type": "string",
                    "description": "CSS styles"
                },
                "javascript": {
                    "type": "string",
                    "description": "JavaScript code to execute; use console.log for output"
                },
                "libraries": {
                    "type": "array",
                    "description": "List of CDN libraries to include in the iframe",
                    "items": {
                        "type": "string",
                        "enum": [
                            "https://docs.opencv.org/4.8.0/opencv.js",
                            "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js",
                            "https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js",
                            "https://unpkg.com/react@18/umd/react.production.min.js",
                            "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js",
                            "https://cdn.jsdelivr.net/npm/vue@3.2.37/dist/vue.global.prod.js",
                            "https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js",
                            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML",
                        ]
                    }
                }
            },
            "required": ["html"]
        }
    }
}

MATH_TOOL = {
    "type": "function",
    "function": {
        "name": "math",
        "description": "Perform mathematical calculations and evaluations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }
}

# Dictionary mapping tool names to their configurations
TOOL_CONFIGS = {
    "html": HTML_TOOL,
    "math": MATH_TOOL
}

def get_tool_config(tool_name):
    """
    Get the configuration for a specific tool.

    Args:
        tool_name: The name of the tool to get the configuration for.

    Returns:
        The tool configuration or None if the tool is not found.
    """
    return TOOL_CONFIGS.get(tool_name)

def get_enabled_tools(enabled_tool_names):
    """
    Get the configurations for the enabled tools.

    Args:
        enabled_tool_names: List of enabled tool names.

    Returns:
        List of tool configurations for the enabled tools.
    """
    if not enabled_tool_names:
        return []

    return [TOOL_CONFIGS[name] for name in enabled_tool_names if name in TOOL_CONFIGS]
