import {
  Bot,
  Check,
  Copy,
  FileCode,
  User,
} from "lucide-react";
import { useState } from "react";

interface Props {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  onSelectFile?: (path: string) => void;
}

function ChatMessage({
  role,
  content,
  sources,
  onSelectFile,
}: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch (error) {
      console.error("Failed to copy message:", error);
    }
  }

  const isAssistant = role === "assistant";

  return (
    <div
      className={`group flex min-w-0 gap-2.5 ${
        isAssistant ? "justify-start" : "justify-end"
      }`}
    >
      {/* Assistant Avatar */}
      {isAssistant && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
          <Bot className="h-3.5 w-3.5 text-blue-400" />
        </div>
      )}

      <div
        className={`min-w-0 max-w-[calc(100%-2.5rem)] sm:max-w-[88%] ${
          isAssistant ? "" : "flex flex-col items-end"
        }`}
      >
        {/* Message */}
        <div
          className={`min-w-0 overflow-hidden rounded-xl px-3.5 py-3 text-sm leading-6 ${
            isAssistant
              ? "border border-zinc-800 bg-zinc-900 text-zinc-300"
              : "bg-blue-600 text-white"
          }`}
        >
          <div className="whitespace-pre-wrap break-words [overflow-wrap:anywhere]">
            {content}
          </div>

          {/* Sources */}
          {isAssistant &&
            sources &&
            sources.length > 0 && (
              <div className="mt-4 min-w-0 border-t border-zinc-800 pt-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                    Sources
                  </span>

                  <span className="rounded-full bg-zinc-800 px-1.5 py-0.5 text-[9px] text-zinc-500">
                    {sources.length}
                  </span>
                </div>

                <div className="space-y-1">
                  {sources.map((source) => (
                    <button
                      key={source}
                      type="button"
                      onClick={() =>
                        onSelectFile?.(source)
                      }
                      title={source}
                      className="flex min-w-0 w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-blue-400"
                    >
                      <FileCode className="h-3.5 w-3.5 shrink-0" />

                      <span className="min-w-0 truncate font-mono">
                        {source}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
        </div>

        {/* Assistant Actions */}
        {isAssistant && (
          <button
            type="button"
            onClick={copy}
            aria-label={
              copied
                ? "Message copied"
                : "Copy message"
            }
            className="mt-1.5 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] text-zinc-600 opacity-100 transition-all hover:bg-zinc-900 hover:text-zinc-300 sm:opacity-0 sm:group-hover:opacity-100"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Copy
              </>
            )}
          </button>
        )}
      </div>

      {/* User Avatar */}
      {!isAssistant && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900">
          <User className="h-3.5 w-3.5 text-zinc-500" />
        </div>
      )}
    </div>
  );
}

export default ChatMessage;