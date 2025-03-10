# Tool-Bot Frontend

This directory contains the TypeScript frontend for the Tool-Bot application that communicates with the FastAPI backend. This document provides comprehensive details about the frontend architecture, implementation, and development workflow.

## Architecture Overview

The Tool-Bot frontend is built with a minimalist, framework-free approach that emphasizes:

1. **Client-First Design**: All tool implementations are in TypeScript and execute directly in the browser
2. **Reactive State Management**: Using signals (@preact/signals-core) for reactive data flow without a heavy framework
3. **AWS Bedrock Compatible Format**: All API communication uses AWS Bedrock message format
4. **Vanilla TypeScript/HTML/CSS**: No frameworks like React or Angular - just plain TypeScript with HTML templates

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Architecture                     │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────┐  ┌────────────────┐  ┌───────────────────┐│
│ │     Main      │  │    API Client  │  │   Tool Registry   ││
│ │  Application  │←→│  (Bedrock      │←→│   (TypeScript)    ││
│ │  (UI Layer)   │  │   Format)      │  │                   ││
│ └───────────────┘  └────────────────┘  └───────────────────┘│
│         ↑                  ↑                     ↑           │
│         ↓                  ↓                     ↓           │
│ ┌───────────────┐  ┌────────────────┐  ┌───────────────────┐│
│ │   Reactive    │  │     Agent      │  │  Tool Execution   ││
│ │   Stores      │←→│   Components   │←→│   (Client-side)   ││
│ │  (Signals)    │  │                │  │                   ││
│ └───────────────┘  └────────────────┘  └───────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            ↑
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                      │
│             (API pass-through with format conversion)        │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       OpenAI/AWS APIs                        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies
npm install

# Start development server with hot-reloading
npm run dev

# Build for production (outputs to ../app/toolbot/static/)
npm run build
```

## Complete Directory Structure

```
frontend/
├── src/                     # Main source code
│   ├── MainApplication/     # Core application components
│   │   ├── MainApplication.ts  # Main controller
│   │   └── types.ts            # Type definitions
│   ├── agents/              # AI agent implementation
│   │   └── Conversation.ts     # Manages AI conversation
│   ├── components/          # UI components
│   │   ├── WorkArea/           # Workspace component
│   │   └── Conversation/       # Chat interface
│   ├── stores/              # Reactive state management
│   │   └── DataStore/          # Data persistence
│   │       ├── DataStore.ts    # Store implementation
│   │       └── types.ts        # Data type definitions
│   ├── styles/              # CSS styles
│   │   ├── main.css            # Main styles
│   │   └── components/         # Component-specific styles
│   ├── types/               # TypeScript type definitions
│   │   └── api.types.ts        # API type definitions
│   ├── utils/               # Utility functions
│   │   ├── dom.ts              # DOM manipulation
│   │   └── formatting.ts       # Text formatting
│   ├── app.types.ts         # Application type definitions
│   ├── apiClient.ts         # API communication layer
│   └── main.ts              # Application entry point
├── tools/                   # All tool implementations
│   ├── client/              # Tool interfaces
│   │   └── tool.interface.ts   # Tool interface definition
│   ├── html-tool/           # HTML rendering tool
│   │   ├── client/             # Client implementation
│   │   └── config.ts           # Tool configuration
│   ├── math-tool/           # Math calculation tool
│   ├── registry.client.ts   # Client-side tool registry
│   └── registry.server.ts   # Server-side tool config (for reference)
├── index.html               # Main HTML entry point
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite build configuration
├── .env                     # Environment variables
└── package.json             # Dependencies and scripts
```

## HTML Implementation

The frontend uses a minimal HTML approach with the main template defined in `index.html`. This file contains:

1. **HTML Templates**: Using the native `<template>` element for components
2. **Content Structure**: Basic DOM structure for the application layout
3. **CSS Imports**: Links to stylesheets
4. **Script Imports**: The main TypeScript entry point

Example template usage:

```html
<!-- Template for a UI component -->
<template id="conversation-message-template">
  <div class="message">
    <div class="message-header">
      <span class="message-role"></span>
      <span class="message-timestamp"></span>
    </div>
    <div class="message-content"></div>
  </div>
</template>
```

Components are instantiated in TypeScript by cloning these templates and manipulating the DOM:

```typescript
const template = document.getElementById('conversation-message-template') as HTMLTemplateElement;
const messageNode = template.content.cloneNode(true) as DocumentFragment;
// Manipulate the DOM nodes...
```

## CSS Architecture

The CSS is organized in a modular fashion:

1. **Base Styles**: Foundational styles in `main.css`
2. **Component Styles**: Specific styles for each component
3. **Utility Classes**: Helper classes for common styling needs

Key styling principles:

- **CSS Variables**: For consistent theming and easy customization
- **BEM Naming**: For clear component organization
- **Mobile-First**: Responsive design using media queries
- **No CSS Frameworks**: Pure CSS for minimal bundle size

Example CSS structure:

```css
/* CSS variables for theming */
:root {
  --primary-color: #3a7bec;
  --secondary-color: #2c3e50;
  --text-color: #333;
  --background-color: #f8f9fa;
}

/* Component styling using BEM */
.conversation {
  display: flex;
  flex-direction: column;
}

.conversation__message {
  margin-bottom: 1rem;
  padding: 0.5rem;
  border-radius: 4px;
}

.conversation__message--user {
  align-self: flex-end;
  background-color: var(--primary-color);
  color: white;
}
```

## TypeScript Architecture

The TypeScript implementation follows these principles:

1. **Class-Based Components**: For organized, encapsulated functionality
2. **Signals for State Management**: Reactive programming using @preact/signals-core
3. **Strong Typing**: Comprehensive TypeScript interfaces and types
4. **Event Delegation**: Efficient event handling
5. **Module Pattern**: Clean separation of concerns

### MainApplication

The `MainApplication` class (`src/MainApplication/MainApplication.ts`) is the core controller that initializes the application and coordinates between components:

```typescript
export class MainApplication {
  private conversation!: Conversation;
  private workAreaComponent!: WorkArea;

  constructor() {
    this.initializeDOMElements();
    this.initializeComponents();
    this.initializeUILayout();
    this.initializeTabs();
  }

  private initializeComponents(): void {
    // Initialize conversation component
    this.conversation = new Conversation({
      containerElement: document.getElementById("conversation-container")!,
      onSendMessage: (message) => {
        // Handle message sending
      }
    });

    // Initialize work area
    this.workAreaComponent = new WorkArea({
      containerElement: document.getElementById("work-area-container")!
    });
  }

  // Additional methods for application management
}
```

### Reactive State with Signals

The frontend uses signals from @preact/signals-core for reactive state management without a full framework:

```typescript
import { signal, computed, effect } from "@preact/signals-core";

// Create a signal (reactive state)
const count = signal(0);

// Create a computed value (derived state)
const doubleCount = computed(() => count.value * 2);

// Create an effect that runs when dependencies change
effect(() => {
  console.log(`Count: ${count.value}, Double: ${doubleCount.value}`);
  // Update DOM or perform side effects
  document.getElementById("counter")!.textContent = String(count.value);
});

// Update the signal - automatically triggers the effect
function increment() {
  count.value++;
}
```

### API Communication

The API client (`src/apiClient.ts`) handles communication with the FastAPI backend:

```typescript
import { Message, ConverseResponse } from "@aws-sdk/client-bedrock-runtime";

export async function postMessage(
  modelId: string,
  messages: Message[],
  systemPrompt: string
): Promise<ConverseResponse> {
  const response = await fetch("/api/ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modelId, messages, systemPrompt }),
  });

  if (!response.ok) {
    throw new Error(`Bedrock server error: ${await response.text()}`);
  }

  return await response.json();
}
```

For streaming responses, the implementation uses the native `fetch` API with streaming:

```typescript
export async function* streamMessage(
  modelId: string,
  messages: Message[],
  systemPrompt: string
): AsyncGenerator<any, void, unknown> {
  const response = await fetch("/api/ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modelId, messages, systemPrompt, stream: true }),
  });

  if (!response.ok) {
    throw new Error(`Stream error: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      // Process the received chunk
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        try {
          const data = JSON.parse(line);
          yield data;
        } catch (e) {
          console.error('Error parsing JSON:', e);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
```

## Client-Side Tool System

Tools are implemented entirely on the client-side using TypeScript. Each tool follows a consistent structure:

### Tool Interface

```typescript
// tools/client/tool.interface.ts
export interface ClientTool {
  name: string;
  execute: (parameters: any) => Promise<any>;
}
```

### Tool Implementation Example

```typescript
// tools/math-tool/client/math.client.ts
import { ClientTool } from '../../client/tool.interface';
import * as mathjs from 'mathjs';

export const mathTool: ClientTool = {
  name: "math",
  execute: async (parameters: { expression: string }): Promise<any> => {
    try {
      const result = mathjs.evaluate(parameters.expression);
      return { result };
    } catch (error) {
      return { error: String(error) };
    }
  }
};
```

### Tool Registry

The registry (`tools/registry.client.ts`) manages all available tools:

```typescript
import { mathTool } from './math-tool/client/math.client';
import { htmlTool } from './html-tool/client/html.client';
import { ClientTool } from './client/tool.interface';

class ToolRegistry {
  private tools: Record<string, ClientTool> = {};

  constructor() {
    this.registerBuiltInTools();
  }

  private registerBuiltInTools(): void {
    this.register(mathTool);
    this.register(htmlTool);
  }

  public register(tool: ClientTool): void {
    this.tools[tool.name] = tool;
  }

  public get(name: string): ClientTool | undefined {
    return this.tools[name];
  }

  public async execute(name: string, parameters: any): Promise<any> {
    const tool = this.get(name);
    if (!tool) {
      throw new Error(`Tool '${name}' not found`);
    }
    return await tool.execute(parameters);
  }
}

export const toolRegistry = new ToolRegistry();
```

## Development Workflow

### Environment Setup

The frontend uses environment variables in `.env` for configuration:

```
# Available OpenAI models (comma-separated list)
VITE_OPENAI_LLM_OPTIONS=anthropic.claude-3.5-sonnet.v2,openai.gpt-4o

# Default model
VITE_DEFAULT_MODEL=anthropic.claude-3.5-sonnet.v2

# API endpoint (relative to the server)
VITE_API_ENDPOINT=/api/ai

# AI Provider to use
VITE_AI_PROVIDER=openai
```

#### Model ID Configuration

The environment variables above control the model IDs used throughout the application:

1. **`VITE_OPENAI_LLM_OPTIONS`**: Defines the list of available models shown in project settings
2. **`VITE_DEFAULT_MODEL`**: Sets the default model used when no specific model is selected
3. **`VITE_AI_PROVIDER`**: Configures the backend provider (openai or bedrock)

These environment variables are the single source of truth for model configuration in the application. The server passes these model IDs directly to the LLM API without modification. Any invalid model IDs will result in API errors that are passed back to the client.

### Creating a New Tool

1. Create a tool directory in `tools/` with the following structure:
   ```
   tools/
   └── your-tool-name/
       ├── client/
       │   └── your-tool.client.ts   # Client implementation
       └── config.ts                 # Tool configuration
   ```

2. Implement the client interface according to the ClientTool interface:
   ```typescript
   import { ClientTool } from '../../client/tool.interface';

   export const yourTool: ClientTool = {
     name: "your-tool-name",
     execute: async (parameters: any): Promise<any> => {
       // Tool implementation
       return { result: "success" };
     }
   };
   ```

3. Register the tool in `registry.client.ts`:
   ```typescript
   import { yourTool } from './your-tool-name/client/your-tool.client';

   // In the registerBuiltInTools() method:
   this.register(yourTool);
   ```

4. Add corresponding tool configuration in the backend's `tools.py` file:
   ```python
   YOUR_TOOL = {
       "type": "function",
       "function": {
           "name": "your-tool-name",
           "description": "Description of your tool",
           "parameters": {
               "type": "object",
               "properties": {
                   "param1": {
                       "type": "string",
                       "description": "Parameter description"
                   }
               },
               "required": ["param1"]
           }
       }
   }

   # Add to TOOL_CONFIGS dictionary
   TOOL_CONFIGS = {
       # ... existing tools
       "your-tool-name": YOUR_TOOL
   }
   ```

## Client-Server Communication

The frontend communicates with the FastAPI backend via:

1. **Main AI Endpoint** (`/api/ai`): For AI chat interactions
2. **Tool Invocation** (`/api/ai/invoke`): For reporting tool usage

All communication uses the AWS Bedrock message format for consistency, while the FastAPI backend handles the transformation between the Bedrock format and OpenAI's API format.

### AWS Bedrock Message Format

```typescript
// Example of a user message in AWS Bedrock format
const userMessage = {
  role: "user",
  content: [
    {
      text: "How can I calculate the square root of 256?"
    }
  ]
};

// Example of an assistant message with tool use
const assistantMessage = {
  role: "assistant",
  content: [
    {
      text: "I'll calculate that for you."
    },
    {
      toolUse: {
        name: "math",
        toolUseId: "tool_123",
        input: {
          expression: "sqrt(256)"
        }
      }
    }
  ]
};

// Example of a tool result message
const toolResultMessage = {
  role: "user",
  content: [
    {
      toolResult: {
        toolUseId: "tool_123",
        content: [
          {
            text: '{"result": 16}'
          }
        ],
        status: "success"
      }
    }
  ]
};
```

## Build Output

When built, the frontend outputs to `../app/toolbot/static/`, which the FastAPI server serves as static content. The build process:

1. Compiles TypeScript to JavaScript
2. Bundles all dependencies
3. Optimizes assets
4. Generates source maps
5. Copies static files
6. Outputs to the FastAPI static directory

## Dependencies

Key dependencies include:
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tooling
- **@preact/signals-core**: Reactive state management without a framework
- **@aws-sdk/client-bedrock-runtime**: AWS Bedrock client and types
- **marked**: Markdown parsing for formatting responses
- **mathjs**: Math operations for the math tool

## Troubleshooting

- **Vite Build Issues**: Ensure Node.js is version 16+ and all dependencies are installed
- **TypeScript Errors**: Check interfaces match between tool implementations
- **API Connection Issues**: Verify the FastAPI server is running and endpoint matches `VITE_API_ENDPOINT`
- **Tool Execution Problems**: Check browser console for errors and verify tool registration
- **API Format Errors**: Ensure messages follow the AWS Bedrock format

## See Also

- [TOOLBOT_MIGRATION.md](../../TOOLBOT_MIGRATION.md): Complete system architecture and migration guide
- [tools/README.md](tools/README.md): Detailed tool development guidance
- [FastAPI README](../README.md): Backend server documentation
