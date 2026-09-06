import {
  Bot,
  Clipboard,
  FileCode,
  User,
} from "lucide-react";

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
  async function copy() {
    await navigator.clipboard.writeText(content);
  }

  return (
    <div
      className={`flex gap-3 ${
        role === "user"
          ? "justify-end"
          : "justify-start"
      }`}
    >
      {role === "assistant" && (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600">
          <Bot size={20} />
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-2xl p-4 ${
          role === "assistant"
            ? "bg-zinc-800"
            : "bg-blue-600"
        }`}
      >
        <div className="whitespace-pre-wrap">
          {content}
        </div>

        {role === "assistant" &&
          sources &&
          sources.length > 0 && (
            <div className="mt-4 border-t border-zinc-700 pt-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Sources
              </p>

              <div className="space-y-1">
                {sources.map((source) => (
                  <button
                    key={source}
                    onClick={() =>
                      onSelectFile?.(source)
                    }
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs text-zinc-400 transition hover:bg-zinc-700 hover:text-white"
                  >
                    <FileCode
                      size={14}
                      className="shrink-0"
                    />

                    <span className="truncate">
                      {source}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

        {role === "assistant" && (
          <button
            onClick={copy}
            className="mt-3 flex items-center gap-2 text-xs text-zinc-400 hover:text-white"
          >
            <Clipboard size={14} />
            Copy
          </button>
        )}
      </div>

      {role === "user" && (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-700">
          <User size={20} />
        </div>
      )}
    </div>
  );
}

export default ChatMessage;