import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Send,
  Sparkles,
  Bug,
  Zap,
  FileText,
  RefreshCw,
} from "lucide-react";

import ChatMessage from "./ChatMessage";
import { chatWithAI } from "../../services/api";

interface AIChatPanelProps {
  owner: string;
  repo: string;
  onSelectFile: (path: string) => void;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

const QUICK_ACTIONS = [
  {
    label: "Explain",
    prompt: "Explain this repository in detail.",
    icon: Sparkles,
  },
  {
    label: "Find Bugs",
    prompt:
      "Find bugs, edge cases and potential issues in this repository.",
    icon: Bug,
  },
  {
    label: "Improve",
    prompt:
      "Suggest improvements for performance, readability and maintainability.",
    icon: Zap,
  },
  {
    label: "Document",
    prompt:
      "Generate professional documentation for this repository in Markdown.",
    icon: FileText,
  },
  {
    label: "Refactor",
    prompt:
      "Suggest refactoring opportunities using modern best practices.",
    icon: RefreshCw,
  },
];

function AIChatPanel({
  owner,
  repo,
  onSelectFile,
}: AIChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm DevPilot AI. Ask me anything about this repository.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function sendMessage(customPrompt?: string) {
    const prompt = customPrompt ?? input;

    if (!prompt.trim() || loading) {
      return;
    }

    const history = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: prompt,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const result = await chatWithAI(
        owner,
        repo,
        prompt,
        history
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.response,
          sources: result.sources,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Something went wrong while contacting the AI.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[700px] flex-col overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950">
      {/* Header */}
      <div className="border-b border-zinc-800/80 bg-zinc-900/80 px-4 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
            <Bot className="h-4 w-4 text-blue-400" />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-zinc-200">
                DevPilot AI
              </h2>

              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            </div>

            <p className="mt-0.5 truncate text-xs text-zinc-600">
              Repo-aware codebase assistant
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
            sources={message.sources}
            onSelectFile={onSelectFile}
          />
        ))}

        {loading && (
          <div className="flex items-center gap-2 px-1 py-2 text-xs text-zinc-500">
            <div className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-400" />
              <span
                className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-400"
                style={{ animationDelay: "120ms" }}
              />
              <span
                className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-400"
                style={{ animationDelay: "240ms" }}
              />
            </div>

            <span>DevPilot is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer */}
      <div className="border-t border-zinc-800/80 bg-zinc-900/60 p-3">
        {/* Quick Actions */}
        <div className="mb-3 flex gap-1.5 overflow-x-auto pb-1">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;

            return (
              <button
                key={action.label}
                type="button"
                onClick={() => sendMessage(action.prompt)}
                disabled={loading}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-[11px] font-medium text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-300 disabled:pointer-events-none disabled:opacity-40"
              >
                <Icon className="h-3 w-3" />
                {action.label}
              </button>
            );
          })}
        </div>

        {/* Input */}
        <div className="flex items-end gap-2 rounded-xl border border-zinc-800 bg-zinc-950 p-2 transition-colors focus-within:border-zinc-700">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !loading
              ) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask about this repository..."
            disabled={loading}
            rows={1}
            className="max-h-24 min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-50"
          />

          <button
            type="button"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            aria-label="Send message"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-500 disabled:pointer-events-none disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-2 px-1 text-[10px] text-zinc-700">
          Enter to send · Shift + Enter for a new line
        </p>
      </div>
    </div>
  );
}

export default AIChatPanel;