
import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Bug,
  FileText,
  RefreshCw,
  Send,
  Sparkles,
  Zap,
  Plus,
  MessageSquare,
} from "lucide-react";

import ChatMessage from "./ChatMessage";

import {
  chatWithAI,
  createConversation,
  getConversations,
  getConversationMessages,
  type Conversation,
} from "../../services/api";

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
    prompt: "Find bugs, edge cases and potential issues in this repository.",
    icon: Bug,
  },
  {
    label: "Improve",
    prompt: "Suggest improvements for performance, readability and maintainability.",
    icon: Zap,
  },
  {
    label: "Document",
    prompt: "Generate professional documentation for this repository in Markdown.",
    icon: FileText,
  },
  {
    label: "Refactor",
    prompt: "Suggest refactoring opportunities using modern best practices.",
    icon: RefreshCw,
  },
];

function AIChatPanel({
  owner,
  repo,
  onSelectFile,
}: AIChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);

  const [conversations, setConversations] = useState<Conversation[]>([]);

  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [conversationError, setConversationError] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const greeting: Message = {
    role: "assistant",
    content: "Hi! I'm DevPilot AI. Ask me anything about this repository.",
  };

  // Load conversations whenever the repository changes.
  useEffect(() => {
    let cancelled = false;

    async function initializeChat() {
      setInitializing(true);
      setConversationError("");
      setActiveConversationId(null);
      setMessages([]);

      try {
        const savedConversations = await getConversations(owner, repo);

        if (cancelled) return;

        setConversations(savedConversations);

        if (savedConversations.length > 0) {
          const latestConversation = savedConversations[0];

          const savedMessages = await getConversationMessages(
            latestConversation.id,
            owner,
            repo
          );

          if (cancelled) return;

          setActiveConversationId(latestConversation.id);

          setMessages(
            savedMessages.length > 0
              ? savedMessages.map((message) => ({
                  role: message.role,
                  content: message.content,
                  sources: message.sources,
                }))
              : [greeting]
          );
        } else {
          setMessages([greeting]);
        }
      } catch (error) {
        console.error("Failed to initialize chat:", error);

        if (!cancelled) {
          setConversationError(
            "Unable to load conversation history."
          );
          setMessages([greeting]);
        }
      } finally {
        if (!cancelled) {
          setInitializing(false);
        }
      }
    }

    initializeChat();

    return () => {
      cancelled = true;
    };
  }, [owner, repo]);

  // Automatically scroll to the latest message.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  // Create a new conversation.
  async function startNewConversation() {
    if (loading || initializing) return;

    setInitializing(true);
    setConversationError("");

    try {
      const conversation = await createConversation(owner, repo);

      setConversations((previous) => [
        conversation,
        ...previous,
      ]);

      setActiveConversationId(conversation.id);
      setMessages([greeting]);
      setInput("");
    } catch (error) {
      console.error("Failed to create conversation:", error);

      setConversationError(
        "Unable to create a new conversation."
      );
    } finally {
      setInitializing(false);
    }
  }

  // Switch to an existing conversation.
  async function switchConversation(conversationId: string) {
    if (
      loading ||
      initializing ||
      conversationId === activeConversationId
    ) {
      return;
    }

    setInitializing(true);
    setConversationError("");

    try {
      const savedMessages = await getConversationMessages(
        conversationId,
        owner,
        repo
      );

      setActiveConversationId(conversationId);

      setMessages(
        savedMessages.length > 0
          ? savedMessages.map((message) => ({
              role: message.role,
              content: message.content,
              sources: message.sources,
            }))
          : [greeting]
      );

      setInput("");
    } catch (error) {
      console.error("Failed to restore conversation:", error);

      setConversationError(
        "Unable to open this conversation."
      );
    } finally {
      setInitializing(false);
    }
  }

  // Send a message and persist it through the backend.
  async function sendMessage(customPrompt?: string) {
    const prompt = customPrompt ?? input;

    if (
      !prompt.trim() ||
      loading ||
      initializing
    ) {
      return;
    }

    setLoading(true);
    setConversationError("");

    const previousHistory = messages
      .filter((message) => message.content !== greeting.content)
      .map((message) => ({
        role: message.role,
        content: message.content,
      }));

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: prompt,
      },
    ]);

    setInput("");

    try {
      let conversationId = activeConversationId;

      // Automatically create a conversation for the first message.
      if (!conversationId) {
        const conversation = await createConversation(owner, repo);

        conversationId = conversation.id;

        setActiveConversationId(conversationId);

        setConversations((previous) => [
          conversation,
          ...previous,
        ]);
      }

      const result = await chatWithAI(
        owner,
        repo,
        prompt,
        previousHistory,
        conversationId
      );

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.response,
          sources: result.sources,
        },
      ]);

      // Refresh metadata so the latest conversation appears first.
      const updatedConversations = await getConversations(
        owner,
        repo
      );

      setConversations(updatedConversations);
    } catch (error) {
      console.error("Chat request failed:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? `Error: ${error.message}`
              : "Something went wrong while contacting the AI.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function formatTimestamp(timestamp: number) {
    return new Date(timestamp * 1000).toLocaleString(
      undefined,
      {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  return (
    <div className="flex min-w-0 h-[600px] flex-col overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950 sm:h-[650px] lg:h-[700px]">

      {/* Header */}
      <div className="shrink-0 border-b border-zinc-800/80 bg-zinc-900/80 px-4 py-3.5">

        <div className="flex items-center justify-between gap-3">

          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Bot className="h-4 w-4 text-blue-400" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-sm font-semibold text-zinc-200">
                  DevPilot AI
                </h2>

                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
              </div>

              <p className="mt-0.5 truncate text-xs text-zinc-600">
                Repo-aware codebase assistant
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={startNewConversation}
            disabled={loading || initializing}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-300 transition-colors hover:border-blue-500/50 hover:text-blue-400 disabled:opacity-40"
          >
            <Plus className="h-3.5 w-3.5" />
            New Chat
          </button>

        </div>

        {/* Conversation selector */}
        <div className="mt-3 flex items-center gap-2">
          <MessageSquare className="h-3.5 w-3.5 shrink-0 text-zinc-500" />

          <select
            value={activeConversationId ?? ""}
            onChange={(event) =>
              switchConversation(event.target.value)
            }
            disabled={
              loading ||
              initializing ||
              conversations.length === 0
            }
            className="min-w-0 flex-1 rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-400 outline-none focus:border-blue-500/50 disabled:opacity-50"
          >
            <option value="" disabled>
              {conversations.length === 0
                ? "No saved conversations"
                : "Select a conversation"}
            </option>

            {conversations.map((conversation) => (
              <option
                key={conversation.id}
                value={conversation.id}
              >
                {conversation.title} ·{" "}
                {formatTimestamp(conversation.updated_at)}
              </option>
            ))}
          </select>
        </div>

      </div>

      {/* Conversation error */}
      {conversationError && (
        <div className="shrink-0 border-b border-red-900/40 bg-red-950/20 px-4 py-2 text-xs text-red-400">
          {conversationError}
        </div>
      )}

      {/* Messages */}
      <div className="min-h-0 flex-1 space-y-4 overflow-x-hidden overflow-y-auto p-3 sm:p-4">

        {initializing ? (
          <div className="flex h-full items-center justify-center text-xs text-zinc-500">
            Loading conversation history...
          </div>
        ) : (
          <>
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
          </>
        )}

      </div>

      {/* Composer */}
      <div className="shrink-0 border-t border-zinc-800/80 bg-zinc-900/60 p-3">

        {/* Quick Actions */}
        <div className="mb-3 flex gap-1.5 overflow-x-auto pb-1">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;

            return (
              <button
                key={action.label}
                type="button"
                onClick={() => sendMessage(action.prompt)}
                disabled={loading || initializing}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-[11px] font-medium text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-300 disabled:pointer-events-none disabled:opacity-40"
              >
                <Icon className="h-3 w-3" />
                {action.label}
              </button>
            );
          })}
        </div>

        {/* Input */}
        <div className="flex min-w-0 items-end gap-2 rounded-xl border border-zinc-800 bg-zinc-950 p-2 transition-colors focus-within:border-zinc-700">

          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !loading &&
                !initializing
              ) {
                event.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask about this repository..."
            disabled={loading || initializing}
            rows={1}
            className="max-h-24 min-h-[40px] min-w-0 flex-1 resize-none bg-transparent px-2 py-2 text-sm text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-50"
          />

          <button
            type="button"
            onClick={() => sendMessage()}
            disabled={
              loading ||
              initializing ||
              !input.trim()
            }
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
