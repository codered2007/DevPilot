import { Bot, Clipboard, User } from "lucide-react";

interface Props {
  role: "user" | "assistant";
  content: string;
}

function ChatMessage({
  role,
  content,
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
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
          <Bot size={20} />
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-2xl p-4 whitespace-pre-wrap ${
          role === "assistant"
            ? "bg-zinc-800"
            : "bg-blue-600"
        }`}
      >
        {content}

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
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-700">
          <User size={20} />
        </div>
      )}
    </div>
  );
}

export default ChatMessage;