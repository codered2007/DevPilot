import Editor from "@monaco-editor/react";
import { Clipboard } from "lucide-react";
import Breadcrumbs from "./Breadcrumbs";

interface CodeViewerProps {
  file?: string;
  fileName?: string;
}

function getLanguage(fileName?: string) {
  if (!fileName) return "plaintext";

  const extension = fileName.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "ts":
      return "typescript";
    case "tsx":
      return "typescript";
    case "js":
      return "javascript";
    case "jsx":
      return "javascript";
    case "py":
      return "python";
    case "json":
      return "json";
    case "md":
      return "markdown";
    case "html":
      return "html";
    case "css":
      return "css";
    case "java":
      return "java";
    case "cpp":
      return "cpp";
    case "c":
      return "c";
    case "go":
      return "go";
    case "rs":
      return "rust";
    case "yml":
    case "yaml":
      return "yaml";
    default:
      return "plaintext";
  }
}
function CodeViewer({
  file,
  fileName,
}: CodeViewerProps) {
  async function copyCode() {
    if (!file) return;

    await navigator.clipboard.writeText(file);
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
  <h2 className="text-xl font-bold">
    {fileName 
      ? fileName.split("/").pop()
      : "Code Viewer"}
  </h2>

  <Breadcrumbs path={fileName ?? ""} />

  <p className="text-sm text-zinc-500">
    Read-only
  </p>
</div>

        {file && (
          <button
            onClick={copyCode}
            className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700"
          >
            <Clipboard size={18} />
            Copy
          </button>
        )}
      </div>

      {file ? (
        <Editor
          height="700px"
          theme="vs-dark"
          language={getLanguage(fileName)}
          value={file}
          options={{
            readOnly: true,
            minimap: {
              enabled: false,
            },
            fontSize: 14,
            fontLigatures: true,
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            padding: {
              top: 20,
            },
          }}
        />
      ) : (
        <div className="flex h-[700px] items-center justify-center text-zinc-500">
          Select a file from the explorer.
        </div>
      )}
    </div>
  );
}

export default CodeViewer;