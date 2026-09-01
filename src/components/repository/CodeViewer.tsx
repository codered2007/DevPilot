import { useState } from "react";
import Editor from "@monaco-editor/react";
import { Clipboard, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Breadcrumbs from "./Breadcrumbs";

import { explainCode } from "../../services/api";

interface CodeViewerProps {
  owner: string;
  repo: string;
  file?: string;
  fileName?: string;
}

function getLanguage(fileName?: string) {
  if (!fileName) return "plaintext";

  const extension = fileName.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "ts":
    case "tsx":
      return "typescript";

    case "js":
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
  owner,
  repo,
  file,
  fileName,
}: CodeViewerProps) {
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [explanationError, setExplanationError] = useState("");

  async function copyCode() {
    if (!file) return;

    await navigator.clipboard.writeText(file);
  }

  async function handleExplainCode() {
    if (!file || !fileName) return;

    try {
      setExplaining(true);
      setExplanationError("");
      setExplanation("");

      const result = await explainCode(
        owner,
        repo,
        fileName,
        file
      );

      setExplanation(result.response);
    } catch (err) {
      console.error(err);

      setExplanationError(
        "Failed to explain this code."
      );
    } finally {
      setExplaining(false);
    }
  }

  return (
    <div className="space-y-6">
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
            <div className="flex items-center gap-3">
              <button
                onClick={handleExplainCode}
                disabled={explaining}
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Sparkles size={18} />

                {explaining
                  ? "Explaining..."
                  : "Explain Code"}
              </button>

              <button
                onClick={copyCode}
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700"
              >
                <Clipboard size={18} />
                Copy
              </button>
            </div>
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

      {explaining && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="flex items-center gap-3">
            <Sparkles size={20} />

            <p className="text-zinc-400">
              DevPilot is analyzing the selected code...
            </p>
          </div>
        </div>
      )}

      {explanationError && (
        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-6 text-red-400">
          {explanationError}
        </div>
      )}

      {explanation && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="mb-6 flex items-center gap-2">
            <Sparkles size={20} />

            <h2 className="text-xl font-bold">
              Code Explanation
            </h2>
          </div>

          <div className="prose prose-invert max-w-none text-zinc-300">
            <ReactMarkdown>
              {explanation}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default CodeViewer;