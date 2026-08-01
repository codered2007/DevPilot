interface FileItem {
  path: string;
  type: string;
}

interface FileExplorerProps {
  files: FileItem[];
  onSelectFile?: (path: string) => void;
}

function FileExplorer({
  files,
  onSelectFile,
}: FileExplorerProps) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
      <h2 className="mb-6 text-xl font-bold">
        Repository Files
      </h2>

      <div className="max-h-[650px] space-y-1 overflow-y-auto">
        {files.map((file) => (
          <button
            key={file.path}
            onClick={() => onSelectFile?.(file.path)}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition hover:bg-zinc-800"
          >
            <span>
              {file.type === "tree" ? "📂" : "📄"}
            </span>

            <span className="truncate">
              {file.path}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default FileExplorer;