import Button from "../ui/Button";
import Input from "../ui/Input";

import type { FileItem } from "../../types/file";

interface AIChatPanelProps {
  selectedFile: FileItem;
}

function AIChatPanel({
  selectedFile,
}: AIChatPanelProps) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
      <h2 className="mb-6 text-lg font-semibold">
        AI Chat
      </h2>

      <p className="mb-4 text-sm text-zinc-400">
        Currently viewing:
        <span className="ml-2 text-blue-400">
          {selectedFile.name}
        </span>
      </p>

      <div className="rounded-xl bg-[#0B0D10] p-4 text-zinc-300">
        Ask questions about the selected file.

        <div className="mt-4 rounded-lg bg-zinc-800 p-3">
          Example:
          <br />
          Explain how this file works.
        </div>
      </div>

      <div className="mt-6 flex gap-3">
        <Input placeholder="Ask DevPilot..." />
        <Button>Send</Button>
      </div>
    </div>
  );
}

export default AIChatPanel;