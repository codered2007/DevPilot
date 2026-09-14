import {
  useEffect,
  useState,
} from "react";

import Editor, {
  DiffEditor,
} from "@monaco-editor/react";

import type { OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

import {
  Clipboard,
  Sparkles,
  Wrench,
  RefreshCw,
  Check,
} from "lucide-react";

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

  const extension = fileName
    .split(".")
    .pop()
    ?.toLowerCase();

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


type CodeAction =
  | "fix"
  | "improve"
  | "refactor";


interface GitHubApplyResult {
  branch: string;
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

  const [explaining, setExplaining] =
    useState(false);

  const [explanation, setExplanation] =
    useState("");

  const [explanationError, setExplanationError] =
    useState("");


  const [codeAction, setCodeAction] =
    useState<CodeAction | null>(null);

  const [completedAction, setCompletedAction] =
    useState<CodeAction | null>(null);

  const [actionCode, setActionCode] =
    useState("");

  const [actionError, setActionError] =
    useState("");


  const [applying, setApplying] =
    useState(false);

  const [applyError, setApplyError] =
    useState("");

  const [githubResult, setGithubResult] =
    useState<GitHubApplyResult | null>(null);


  const [pullRequestLoading, setPullRequestLoading] =
    useState(false);

  const [pullRequestResult, setPullRequestResult] =
    useState<{
      number: number;
      title: string;
      url: string;
    } | null>(null);

  const [pullRequestError, setPullRequestError] =
    useState("");


  const [editorInstance, setEditorInstance] =
    useState<editor.IStandaloneCodeEditor | null>(
      null
    );


  const handleEditorMount: OnMount = (
    editor
  ) => {
    setEditorInstance(editor);
  };


  /*
   * Jump to the line reported by
   * Repository Code Review.
   */
  useEffect(() => {

    if (
      !editorInstance ||
      reviewLine === null ||
      reviewLine === undefined
    ) {
      return;
    }

    editorInstance.revealLineInCenter(
      reviewLine
    );

    editorInstance.setPosition({
      lineNumber: reviewLine,
      column: 1,
    });

    editorInstance.focus();

  }, [
    editorInstance,
    reviewLine,
  ]);


  /*
   * Clear any previous AI proposal
   * when the user switches files.
   */
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


  /*
   * Listen for a fix generated from
   * an AI Code Review finding.
   *
   * Repository.tsx generates the fix and
   * dispatches this browser event.
   */
  useEffect(() => {

    function handleReviewFix(
      event: Event
    ) {

      const customEvent =
        event as CustomEvent<ReviewFixEventDetail>;

      const detail =
        customEvent.detail;


      if (!detail) {
        return;
      }


      /*
       * Clear any previous action state.
       */
      setActionError("");
      setApplyError("");

      setGithubResult(null);

      setPullRequestResult(null);
      setPullRequestError("");

      setCodeAction(null);


      /*
       * This proposal came from the
       * Repository Code Review, so the
       * action is always "fix".
       */
      setCompletedAction("fix");

      setActionCode(
        detail.modifiedCode
      );

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

    await navigator.clipboard.writeText(
      file
    );
  }


  async function handleExplainCode() {

    if (!file || !fileName) {
      return;
    }


    try {

      setExplaining(true);

      setExplanationError("");

      setExplanation("");


      const result =
        await explainCode(
          owner,
          repo,
          fileName,
          file
        );


      setExplanation(
        result.response
      );

    } catch (err) {

      console.error(err);

      setExplanationError(
        "Failed to explain this code."
      );

    } finally {

      setExplaining(false);

    }
  }


  async function handleCodeAction(
    action: CodeAction
  ) {

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


      const result =
        await generateCodeAction(
          owner,
          repo,
          fileName,
          file,
          action
        );


      setActionCode(
        result.modified_code
      );


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


      const result =
        await applyCodeToGitHub(
          owner,
          repo,
          fileName,
          actionCode,
          completedAction
        );


      /*
       * Update the local code viewer
       * with the applied version.
       */
      onApplyCode(
        actionCode
      );


      setGithubResult({
        branch: result.branch,
        commit_sha: result.commit_sha,
        commit_url: result.commit_url,
      });


      /*
       * Clear the proposed code after
       * successful application.
       *
       * Keep completedAction so the user
       * can still create a Pull Request.
       */
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


      const result =
        await createPullRequest(
          owner,
          repo,
          `DevPilot: ${completedAction} ${fileName}`,
          `DevPilot generated a ${completedAction} change for \`${fileName}\`.\n\nThe changes were reviewed in DevPilot and committed to the \`${githubResult.branch}\` branch.`,
          githubResult.branch,
          "main"
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

    <div className="space-y-6">


      {/* Code Viewer */}

      <div className="overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900">


        <div className="flex flex-col gap-4 border-b border-zinc-800 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">


          <div>

            <h2 className="text-xl font-bold">

              {fileName
                ? fileName.split("/").pop()
                : "Code Viewer"}

            </h2>


            <Breadcrumbs
              path={fileName ?? ""}
            />


            <p className="text-sm text-zinc-500">
              Read-only
            </p>

          </div>


          {file && (

            <div className="flex flex-wrap items-center gap-3">


              {/* Explain */}

              <button
                onClick={
                  handleExplainCode
                }
                disabled={
                  explaining
                }
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                <Sparkles
                  size={18}
                />

                {explaining
                  ? "Explaining..."
                  : "Explain Code"}

              </button>


              {/* Fix */}

              <button
                onClick={() =>
                  handleCodeAction(
                    "fix"
                  )
                }
                disabled={
                  codeAction !== null
                }
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                <Wrench
                  size={18}
                />

                {codeAction ===
                "fix"
                  ? "Fixing..."
                  : "Fix"}

              </button>


              {/* Improve */}

              <button
                onClick={() =>
                  handleCodeAction(
                    "improve"
                  )
                }
                disabled={
                  codeAction !== null
                }
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                <Sparkles
                  size={18}
                />

                {codeAction ===
                "improve"
                  ? "Improving..."
                  : "Improve"}

              </button>


              {/* Refactor */}

              <button
                onClick={() =>
                  handleCodeAction(
                    "refactor"
                  )
                }
                disabled={
                  codeAction !== null
                }
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                <RefreshCw
                  size={18}
                />

                {codeAction ===
                "refactor"
                  ? "Refactoring..."
                  : "Refactor"}

              </button>


              {/* Copy */}

              <button
                onClick={copyCode}
                className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700"
              >

                <Clipboard
                  size={18}
                />

                Copy

              </button>

            </div>

          )}

        </div>


        {/* Monaco Editor */}

        {file ? (

          <Editor
            height="700px"
            theme="vs-dark"
            language={
              getLanguage(
                fileName
              )
            }
            value={file}
            onMount={
              handleEditorMount
            }
            options={{
              readOnly: true,

              minimap: {
                enabled: false,
              },

              fontSize: 14,

              fontLigatures: true,

              scrollBeyondLastLine:
                false,

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


      {/* Explanation Loading */}

      {explaining && (

        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

          <div className="flex items-center gap-3">

            <Sparkles
              size={20}
            />

            <p className="text-zinc-400">

              DevPilot is analyzing the
              selected code...

            </p>

          </div>

        </div>

      )}


      {/* Explanation Error */}

      {explanationError && (

        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-6 text-red-400">

          {explanationError}

        </div>

      )}


      {/* Explanation */}

      {explanation && (

        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">


          <div className="mb-6 flex items-center gap-2">

            <Sparkles
              size={20}
            />

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


      {/* Code Action Error */}

      {actionError && (

        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-6 text-red-400">

          {actionError}

        </div>

      )}


      {/* Apply Error */}

      {applyError && (

        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-6 text-red-400">

          {applyError}

        </div>

      )}


      {/* GitHub Success */}

      {githubResult && (

        <div className="rounded-3xl border border-zinc-700 bg-zinc-900 p-6">


          <div className="flex items-start gap-3">


            <div className="mt-0.5 rounded-full bg-zinc-800 p-2">

              <Check
                size={18}
              />

            </div>


            <div>

              <h2 className="text-lg font-bold">
                Changes committed to GitHub
              </h2>


              <p className="mt-1 text-sm text-zinc-400">

                Branch:

                <span className="ml-2 font-mono text-zinc-300">

                  {githubResult.branch}

                </span>

              </p>


              {githubResult.commit_url && (

                <a
                  href={
                    githubResult.commit_url
                  }
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-sm underline"
                >
                  View commit on GitHub
                </a>

              )}


              {/* Create Pull Request */}

              {!pullRequestResult && (

                <div className="mt-5">

                  <button
                    type="button"
                    onClick={
                      handleCreatePullRequest
                    }
                    disabled={
                      pullRequestLoading
                    }
                    className="flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                  >

                    {pullRequestLoading ? (

                      <>

                        <RefreshCw
                          size={17}
                          className="animate-spin"
                        />

                        Creating Pull Request...

                      </>

                    ) : (

                      <>

                        <Sparkles
                          size={17}
                        />

                        Create Pull Request

                      </>

                    )}

                  </button>

                </div>

              )}


              {/* Pull Request Error */}

              {pullRequestError && (

                <div className="mt-4 rounded-xl border border-red-700 bg-red-900/20 p-4 text-sm text-red-400">

                  {pullRequestError}

                </div>

              )}


              {/* Pull Request Success */}

              {pullRequestResult && (

                <div className="mt-5 rounded-2xl border border-zinc-700 bg-zinc-950 p-5">


                  <div className="flex items-start gap-3">


                    <div className="mt-0.5 rounded-full bg-zinc-800 p-2">

                      <Check
                        size={18}
                      />

                    </div>


                    <div>

                      <h3 className="font-semibold">
                        Pull Request created
                      </h3>


                      <p className="mt-1 text-sm text-zinc-400">

                        PR #
                        {
                          pullRequestResult.number
                        }

                      </p>


                      <a
                        href={
                          pullRequestResult.url
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 inline-block text-sm underline"
                      >
                        View Pull Request on GitHub
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

        <div className="overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900">


          <div className="flex flex-col gap-4 border-b border-zinc-800 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">


            <div>

              <h2 className="text-xl font-bold">
                Proposed Changes
              </h2>


              <p className="text-sm text-zinc-500">

                DevPilot generated a proposed{" "}

                {completedAction}

                {" "}version of this code.

              </p>

            </div>


            <div className="flex flex-wrap items-center gap-3">


              {/* Reject */}

              <button
                onClick={
                  handleRejectCode
                }
                disabled={
                  applying
                }
                className="rounded-lg bg-zinc-800 px-4 py-2 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
              >

                Reject

              </button>


              {/* Apply */}

              <button
                onClick={
                  handleApplyCode
                }
                disabled={
                  applying
                }
                className="flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-zinc-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
              >

                {applying ? (

                  <>

                    <RefreshCw
                      size={18}
                      className="animate-spin"
                    />

                    Applying...

                  </>

                ) : (

                  <>

                    <Check
                      size={18}
                    />

                    Apply to GitHub

                  </>

                )}

              </button>

            </div>

          </div>


          {/* Monaco Diff Editor */}

          <DiffEditor
            height="700px"
            theme="vs-dark"
            language={
              getLanguage(
                fileName
              )
            }
            original={
              file ?? ""
            }
            modified={
              actionCode
            }
            options={{
              readOnly: true,

              minimap: {
                enabled: false,
              },

              fontSize: 14,

              fontLigatures: true,

              scrollBeyondLastLine:
                false,

              wordWrap: "on",

              automaticLayout: true,

              renderSideBySide:
                true,

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