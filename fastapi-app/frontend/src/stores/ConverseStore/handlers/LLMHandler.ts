import { Message, ConverseStreamOutput } from "@aws-sdk/client-bedrock-runtime";
import { MessageExtended } from "../../../app.types";
import { converseAgentConfig } from "../../../agents/converseAgent";

export interface StreamCallbacks {
  onStart?: () => void;
  onChunk?: (chunk: ConverseStreamOutput) => void;
  onComplete?: (fullMessage: Message) => void;
  onError?: (error: any) => void;
}

export class LLMHandler {
  private defaultModelId = import.meta.env.VITE_DEFAULT_MODEL;

  public async callLLMStream(
    messages: MessageExtended[],
    callbacks: StreamCallbacks,
    enabledTools?: string[],
    modelId?: string
  ): Promise<Message> {
    try {
      // Ensure we have a valid model ID
      if (!modelId) {
        console.warn(
          "No model ID provided, using default model:",
          this.defaultModelId
        );
      }

      const response = await fetch("/api/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          modelId: modelId || this.defaultModelId,
          messages,
          systemPrompt: converseAgentConfig.systemPrompt,
          enabledTools,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body from /api/ai");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      const accumulatedContent: any[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // Stream ended
          return {
            role: "assistant",
            content: accumulatedContent,
          };
        }

        // Decode partial chunk
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Process all complete lines except the last partial
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (!line) continue;

          let chunk: ConverseStreamOutput;
          try {
            chunk = JSON.parse(line);
          } catch (e) {
            callbacks.onError?.(e);
            continue;
          }

          // Always pass chunk up (so the caller sees contentBlockStart, etc.)
          callbacks.onChunk?.(chunk);

          // Check for text deltas
          if (chunk.contentBlockDelta?.delta?.text) {
            accumulatedContent.push({
              text: chunk.contentBlockDelta.delta.text,
            });
          }

          // Check for toolUse partial
          if (chunk.contentBlockDelta?.delta?.toolUse) {
            accumulatedContent.push({
              toolUse: chunk.contentBlockDelta.delta.toolUse,
            });
          }

          // Check for any error objects
          if (
            chunk.internalServerException ||
            chunk.modelStreamErrorException ||
            chunk.validationException ||
            chunk.throttlingException ||
            chunk.serviceUnavailableException
          ) {
            const error =
              chunk.internalServerException ||
              chunk.modelStreamErrorException ||
              chunk.validationException ||
              chunk.throttlingException ||
              chunk.serviceUnavailableException;
            callbacks.onError?.(error);
            throw new Error(error.message);
          }

          // If there's a messageStop
          if (chunk.messageStop) {
            // If it's tool_use, do NOT finalize (the caller handles it).
            if (chunk.messageStop.stopReason !== "tool_use") {
              // For other stops: finalize.
              const finalMessage: Message = {
                role: "assistant",
                content: accumulatedContent,
              };
              callbacks.onComplete?.(finalMessage);
              return finalMessage;
            }
          }
        }

        // Keep trailing partial line
        buffer = lines[lines.length - 1];
      }
    } catch (error) {
      callbacks.onError?.(error);
      throw error;
    }
  }

  // Old method for backward compat
  // public async callLLM(
  //   messages: MessageExtended[],
  //   enabledTools?: string[]
  // ): Promise<Message> {
  //   return this.callLLMStream(messages, {}, enabledTools);
  // }

  public async invoke(
    messages: Partial<MessageExtended[]> | Message[],
    systemPrompt: string,
    enabledTools?: string[],
    modelId?: string
  ): Promise<Message> {
    try {
      const finalModelId = modelId || this.defaultModelId;
      console.log("Using model ID for invoke:", finalModelId);

      const response = await fetch("/api/ai/invoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          modelId: finalModelId,
          messages,
          systemPrompt: systemPrompt,
          enabledTools,
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(
          `HTTP error! status: ${response.status}, ${errorData}`
        );
      }

      const result = await response.json();
      console.log("Invoke API response:", result);

      // Extract the message from the ConverseResponse structure
      if (result.output?.message) {
        return result.output.message;
      }

      // Fallback for backward compatibility
      if (result.role === "assistant" && Array.isArray(result.content)) {
        return result;
      }

      throw new Error("Invalid response format from /api/ai/invoke");
    } catch (error) {
      console.error("Invoke API error:", error);
      throw error;
    }
  }
}
