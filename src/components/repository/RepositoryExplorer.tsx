import {
  ChevronDown,
  FileCode2,
  Folder,
} from "lucide-react";

import type { FileItem } from "../../types/file";

interface RepositoryExplorerProps {
  files: FileItem[];
  selectedFile: FileItem;
  onSelectFile: (file: FileItem) => void;
}

function RepositoryExplorer({
  files,
  selectedFile,
  onSelectFile,
}: RepositoryExplorerProps) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
      <h2 className="mb-6 text-lg font-semibold">
        Explorer
      </h2>

      <div className="space-y-3 text-sm">
        <div className="flex items-center gap-2">
          <ChevronDown size={16} />
          <Folder
            size={18}
            className="text-blue-400"
          />
          src
        </div>

        <div className="ml-6 space-y-2">
          {files.map((file) => (
            <button
              key={file.id}
              onClick={() => onSelectFile(file)}
              className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition ${
                selectedFile.id === file.id
                  ? "bg-blue-500/20 text-blue-400"
                  : "hover:bg-zinc-800"
              }`}
            >
              <FileCode2 size={18} />
              {file.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RepositoryExplorer;