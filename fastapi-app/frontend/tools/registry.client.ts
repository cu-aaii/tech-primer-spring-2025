import { ClientTool, ClientToolRegistry } from "./client/tool.interface.js";
import { htmlTool } from "./html-tool/client/html.client.js";
import { mathTool } from "./math-tool/client/math.client.js";
// Make dataStore available globally for tools
// @todo have a tool-data-store that the client can subscribe to.
declare global {
  interface Window {
    availableData?: Record<string, any>[];
  }
}
class ToolRegistry {
  private tools: ClientToolRegistry = {};

  constructor() {
    /** Register Client tools here */
    this.registerTool(htmlTool);
    this.registerTool(mathTool);
  }

  private registerTool(tool: ClientTool): void {
    this.tools[tool.name] = tool;
    console.log(`Registered client tool: ${tool.name}`);
  }

  public getTool(name: string): ClientTool | undefined {
    return this.tools[name];
  }

  public getAllTools(): ClientToolRegistry {
    return { ...this.tools };
  }
}

export const clientRegistry = new ToolRegistry();
