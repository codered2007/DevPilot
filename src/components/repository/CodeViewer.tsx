import { useEffect, useState } from "react";
import {
  Sparkles,
  Wrench,
  RefreshCw,
  Check,
  Copy,
  ExternalLink,
  BookOpen,
  WandSparkles,
} from "lucide-react";
import Editor, { DiffEditor } from "@monaco-editor/react";
import type { OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

import ReactMarkdown from "react-markdown";

import Breadcrumbs from "./Breadcrumbs";

import {
  explainCode,
  generateCodeAction,
  applyCodeToGitHub,
  createPullRequest,
} from "../../services/api";

interface CodeViewerProps {
  owner: string;
  repo: string;
  file?: string;
  fileName?: string;
  onApplyCode: (code: string) => void;
  reviewLine?: number | null;
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

type CodeAction = "fix" | "improve" | "refactor";

interface GitHubApplyResult {
  branch: string;
  base_branch: string;
  commit_sha: string;
  commit_url: string;
}

interface ReviewFixEventDetail {
  filePath: string;
  lineStart: number | null;
  code: string;
  modifiedCode: string;
}

function CodeViewer({
  owner,
  repo,
  file,
  fileName,
  onApplyCode,
  reviewLine,
}: CodeViewerProps) {
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [explanationError, setExplanationError] = useState("");

  const [codeAction, setCodeAction] = useState<CodeAction | null>(null);
  const [completedAction, setCompletedAction] =
    useState<CodeAction | null>(null);
  const [actionCode, setActionCode] = useState("");
  const [actionError, setActionError] = useState("");

  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState("");
  const [githubResult, setGithubResult] =
    useState<GitHubApplyResult | null>(null);

  const [pullRequestLoading, setPullRequestLoading] = useState(false);
  const [pullRequestResult, setPullRequestResult] = useState<{
    number: number;
    title: string;
    url: string;
  } | null>(null);
  const [pullRequestError, setPullRequestError] = useState("");

  const [editorInstance, setEditorInstance] =
    useState<editor.IStandaloneCodeEditor | null>(null);

  const handleEditorMount: OnMount = (editor) => {
    setEditorInstance(editor);
  };

  useEffect(() => {
    if (
      !editorInstance ||
      reviewLine === null ||
      reviewLine === undefined
    ) {
      return;
    }

    editorInstance.revealLineInCenter(reviewLine);

    editorInstance.setPosition({
      lineNumber: reviewLine,
      column: 1,
    });

    editorInstance.focus();
  }, [editorInstance, reviewLine]);

  useEffect(() => {
    setCodeAction(null);
    setCompletedAction(null);
    setActionCode("");
    setActionError("");
    setApplying(false);
    setApplyError("");
    setGithubResult(null);
    setPullRequestResult(null);
    setPullRequestError("");
  }, [fileName]);

  useEffect(() => {
    function handleReviewFix(event: Event) {
      const customEvent =
        event as CustomEvent<ReviewFixEventDetail>;

      const detail = customEvent.detail;

      if (!detail) {
        return;
      }

      setActionError("");
      setApplyError("");
      setGithubResult(null);
      setPullRequestResult(null);
      setPullRequestError("");
      setCodeAction(null);
      setCompletedAction("fix");
      setActionCode(detail.modifiedCode);
    }

    window.addEventListener(
      "devpilot-review-fix",
      handleReviewFix
    );

    return () => {
      window.removeEventListener(
        "devpilot-review-fix",
        handleReviewFix
      );
    };
  }, []);

  async function copyCode() {
    if (!file) return;

    await navigator.clipboard.writeText(file);
  }

  async function handleExplainCode() {
    if (!file || !fileName) {
      return;
    }

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
      setExplanationError("Failed to explain this code.");
    } finally {
      setExplaining(false);
    }
  }

  async function handleCodeAction(action: CodeAction) {
    if (!file || !fileName) {
      return;
    }

    try {
      setCodeAction(action);
      setCompletedAction(null);
      setActionError("");
      setActionCode("");
      setGithubResult(null);
      setApplyError("");
      setPullRequestResult(null);
      setPullRequestError("");

      const result = await generateCodeAction(
        owner,
        repo,
        fileName,
        file,
        action
      );

      setActionCode(result.modified_code);
      setCompletedAction(action);
      setCodeAction(null);
    } catch (err) {
      console.error(err);

      setActionError(
        `Failed to ${action} the code.`
      );

      setCodeAction(null);
    }
  }

  async function handleApplyCode() {
    if (
      !actionCode ||
      !fileName ||
      !completedAction
    ) {
      return;
    }

    try {
      setApplying(true);
      setApplyError("");
      setGithubResult(null);
      setPullRequestResult(null);
      setPullRequestError("");

      const result = await applyCodeToGitHub(
        owner,
        repo,
        fileName,
        actionCode,
        completedAction
      );

      onApplyCode(actionCode);

      setGithubResult({
        branch: result.branch,
        base_branch: result.base_branch,
        commit_sha: result.commit_sha,
        commit_url: result.commit_url,
      });

      setActionCode("");
    } catch (err) {
      console.error(err);

      setApplyError(
        err instanceof Error
          ? err.message
          : "Failed to apply changes to GitHub."
      );
    } finally {
      setApplying(false);
    }
  }

  function handleRejectCode() {
    if (applying) {
      return;
    }

    setActionCode("");
    setCompletedAction(null);
    setActionError("");
    setApplyError("");
    setGithubResult(null);
    setPullRequestResult(null);
    setPullRequestError("");
  }

  async function handleCreatePullRequest() {
    if (
      !githubResult ||
      !completedAction ||
      !fileName
    ) {
      return;
    }

    try {
      setPullRequestLoading(true);
      setPullRequestError("");
      setPullRequestResult(null);

      const result = await createPullRequest(
        owner,
        repo,
        `DevPilot: ${completedAction} ${fileName}`,
        `DevPilot generated a ${completedAction} change for \`${fileName}\`.\n\nThe changes were reviewed in DevPilot and committed to the \`${githubResult.branch}\` branch.`,
        githubResult.branch,
        githubResult.base_branch
      );

      setPullRequestResult({
        number: result.number,
        title: result.title,
        url: result.url,
      });
    } catch (err) {
      console.error(err);

      setPullRequestError(
        err instanceof Error
          ? err.message
          : "Failed to create Pull Request."
      );
    } finally {
      setPullRequestLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* Code Viewer */}
      <div className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950">
        {/* Editor Header */}
        <div className="border-b border-zinc-800/80 bg-zinc-900/80">
          <div className="flex flex-col gap-4 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />

                <h2 className="truncate text-sm font-semibold text-zinc-200">
                  {fileName
                    ? fileName.split("/").pop()
                    : "Code Viewer"}
                </h2>

                {file && (
                  <span className="rounded-md border border-zinc-800 bg-zinc-950 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-600">
                    Read only
                  </span>
                )}
              </div>

              <div className="mt-1.5 overflow-hidden text-xs text-zinc-600">
                <Breadcrumbs path={fileName ?? ""} />
              </div>
            </div>

            {file && (
              <div className="flex flex-wrap items-center gap-1.5">
                {/* Explain */}
                <button
                  type="button"
                  onClick={handleExplainCode}
                  disabled={explaining}
                  title="Explain this code"
                  className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <BookOpen className="h-3.5 w-3.5" />
                  {explaining ? "Explaining..." : "Explain"}
                </button>

                {/* Fix */}
                <button
                  type="button"
                  onClick={() => handleCodeAction("fix")}
                  disabled={codeAction !== null}
                  title="Fix code"
                  className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Wrench className="h-3.5 w-3.5" />
                  {codeAction === "fix" ? "Fixing..." : "Fix"}
                </button>

                {/* Improve */}
                <button
                  type="button"
                  onClick={() => handleCodeAction("improve")}
                  disabled={codeAction !== null}
                  title="Improve code"
                  className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {codeAction === "improve"
                    ? "Improving..."
                    : "Improve"}
                </button>

                {/* Refactor */}
                <button
                  type="button"
                  onClick={() => handleCodeAction("refactor")}
                  disabled={codeAction !== null}
                  title="Refactor code"
                  className="inline-flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <WandSparkles className="h-3.5 w-3.5" />
                  {codeAction === "refactor"
                    ? "Refactoring..."
                    : "Refactor"}
                </button>

                <div className="mx-1 hidden h-5 w-px bg-zinc-800 sm:block" />

                {/* Copy */}
                <button
                  type="button"
                  onClick={copyCode}
                  title="Copy code"
                  className="inline-flex items-center justify-center rounded-md border border-zinc-800 bg-zinc-950 p-2 text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-200"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Monaco Editor */}
        {file ? (
          <Editor
            height="700px"
            theme="vs-dark"
            language={getLanguage(fileName)}
            value={file}
            onMount={handleEditorMount}
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
          <div className="flex h-[700px] flex-col items-center justify-center bg-zinc-950 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
              <BookOpen className="h-5 w-5 text-zinc-600" />
            </div>

            <p className="mt-4 text-sm font-medium text-zinc-400">
              Select a file to view its code
            </p>

            <p className="mt-1 text-xs text-zinc-600">
              Choose a file from the Explorer.
            </p>
          </div>
        )}
      </div>

      {/* Explanation Loading */}
      {explaining && (
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
              <Sparkles className="h-4 w-4 animate-pulse text-blue-400" />
            </div>

            <div>
              <p className="text-sm font-medium text-zinc-200">
                Analyzing code
              </p>

              <p className="mt-0.5 text-xs text-zinc-500">
                DevPilot is generating an explanation...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Explanation Error */}
      {explanationError && (
        <div className="rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-sm text-red-400">
          {explanationError}
        </div>
      )}

      {/* Explanation */}
      {explanation && (
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <Sparkles className="h-4 w-4 text-blue-400" />
            </div>

            <div>
              <h2 className="text-lg font-semibold text-white">
                Code Explanation
              </h2>

              <p className="mt-0.5 text-xs text-zinc-500">
                AI-generated explanation of the selected file
              </p>
            </div>
          </div>

          <div className="prose prose-invert max-w-none text-zinc-300">
            <ReactMarkdown>{explanation}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Code Action Error */}
      {actionError && (
        <div className="rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-sm text-red-400">
          {actionError}
        </div>
      )}

      {/* Apply Error */}
      {applyError && (
        <div className="rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-sm text-red-400">
          {applyError}
        </div>
      )}

      {/* GitHub Success */}
      {githubResult && (
        <div className="rounded-2xl border border-emerald-900/50 bg-emerald-950/10 p-6">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
              <Check className="h-4 w-4 text-emerald-400" />
            </div>

            <div className="min-w-0">
              <h2 className="text-base font-semibold text-white">
                Changes committed to GitHub
              </h2>

              <p className="mt-2 text-sm text-zinc-500">
                Branch:
                <span className="ml-2 font-mono text-zinc-300">
                  {githubResult.branch}
                </span>
              </p>

              <p className="mt-1 text-sm text-zinc-500">
                Base:
                <span className="ml-2 font-mono text-zinc-300">
                  {githubResult.base_branch}
                </span>
              </p>

              {githubResult.commit_url && (
                <a
                  href={githubResult.commit_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300"
                >
                  View commit on GitHub
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}

              {!pullRequestResult && (
                <div className="mt-5">
                  <button
                    type="button"
                    onClick={handleCreatePullRequest}
                    disabled={pullRequestLoading}
                    className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {pullRequestLoading ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Creating Pull Request...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Create Pull Request
                      </>
                    )}
                  </button>
                </div>
              )}

              {pullRequestError && (
                <div className="mt-4 rounded-lg border border-red-900/60 bg-red-950/20 p-3 text-sm text-red-400">
                  {pullRequestError}
                </div>
              )}

              {pullRequestResult && (
                <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                      <Check className="h-4 w-4 text-emerald-400" />
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-white">
                        Pull Request created
                      </h3>

                      <p className="mt-1 text-sm text-zinc-500">
                        PR #{pullRequestResult.number}
                      </p>

                      <a
                        href={pullRequestResult.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300"
                      >
                        View Pull Request on GitHub
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Proposed Changes */}
      {actionCode && (
        <div className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-950">
          <div className="flex flex-col gap-4 border-b border-zinc-800/80 bg-zinc-900/80 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Wrench className="h-4 w-4 text-blue-400" />

                <h2 className="text-sm font-semibold text-white">
                  Proposed Changes
                </h2>
              </div>

              <p className="mt-1 text-xs text-zinc-500">
                DevPilot generated a proposed{" "}
                {completedAction} version of this code.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleRejectCode}
                disabled={applying}
                className="rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Reject
              </button>

              <button
                type="button"
                onClick={handleApplyCode}
                disabled={applying}
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {applying ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Applying...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    Apply to GitHub
                  </>
                )}
              </button>
            </div>
          </div>

          <DiffEditor
            height="700px"
            theme="vs-dark"
            language={getLanguage(fileName)}
            original={file ?? ""}
            modified={actionCode}
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
              renderSideBySide: true,
              padding: {
                top: 20,
              },
            }}
          />
        </div>
      )}
    </div>
  );
}

export default CodeViewer;