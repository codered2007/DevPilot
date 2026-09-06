import { useEffect, useRef, useState } from "react";

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
    label: "📝 Explain",
    prompt: "Explain this repository in detail.",
  },
  {
    label: "🐞 Find Bugs",
    prompt:
      "Find bugs, edge cases and potential issues in this repository.",
  },
  {
    label: "⚡ Improve",
    prompt:
      "Suggest improvements for performance, readability and maintainability.",
  },
  {
    label: "📄 Document",
    prompt:
      "Generate professional documentation for this repository in Markdown.",
  },
  {
    label: "🔄 Refactor",
    prompt:
      "Suggest refactoring opportunities using modern best practices.",
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
        "👋 Hi! Ask me anything about this repository.",
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
        prompt
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
    <div className="flex h-[700px] flex-col overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900">
      <div className="border-b border-zinc-800 p-5">
        <h2 className="text-xl font-bold">
          🤖 DevPilot AI
        </h2>

        <p className="mt-1 text-sm text-zinc-500">
          Ask questions about this repository.
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-5">
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
          <ChatMessage
            role="assistant"
            content="🤖 Thinking..."
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-zinc-800 p-4">
        <div className="mb-4 flex flex-wrap gap-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              onClick={() =>
                sendMessage(action.prompt)
              }
              disabled={loading}
              className="rounded-lg bg-zinc-800 px-3 py-2 text-sm transition hover:bg-zinc-700 disabled:opacity-50"
            >
              {action.label}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
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
            placeholder="Ask anything about this repository..."
            disabled={loading}
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 outline-none disabled:opacity-50"
          />

          <button
            onClick={() => sendMessage()}
            disabled={
              loading || !input.trim()
            }
            className="rounded-lg bg-blue-600 px-5 py-3 transition hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default AIChatPanel;