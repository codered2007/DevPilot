import { useEffect, useState } from "react";
import { Base64 } from "js-base64";

import RepositoryHeader from "../../components/repository/RepositoryHeader";
import RepositoryStats from "../../components/repository/RepositoryStats";
import FileTree from "../../components/repository/FileTree";
import CodeViewer from "../../components/repository/CodeViewer";
import AIChatPanel from "../../components/repository/AIChatPanel";

import { useRepository } from "../../context/RepositoryContext";

import {
  getRepositoryTree,
  getFileContent,
  reviewRepository,
  generateCodeAction,
} from "../../services/api";

import type {
  RepositoryReviewResponse,
} from "../../services/api";

import { buildFileTree } from "../../utils/buildFileTree";
import { getRepositoryStats } from "../../utils/repositoryStats";

import {
  RefreshCw,
  Sparkles,
  Wrench,
} from "lucide-react";


interface FileItem {
  path: string;
  type: string;
}


function Repository() {

  const { repository } = useRepository();


  const [files, setFiles] = useState<FileItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const [selectedFilePath, setSelectedFilePath] =
    useState("");

  const [fileContent, setFileContent] =
    useState("");


  const [reviewing, setReviewing] =
    useState(false);

  const [reviewResult, setReviewResult] =
    useState<RepositoryReviewResponse | null>(
      null
    );

  const [reviewError, setReviewError] =
    useState("");


  const [reviewLine, setReviewLine] =
    useState<number | null>(null);


  const [fixingFinding, setFixingFinding] =
    useState<string | null>(null);

  const [fixError, setFixError] =
    useState("");


  const tree = buildFileTree(files);

  const stats = getRepositoryStats(files);


  useEffect(() => {

    async function loadTree() {

      if (!repository) return;

      try {

        setLoading(true);
        setError("");

        const tree =
          await getRepositoryTree(
            repository.owner,
            repository.repo
          );

        console.log(
          "Repository tree:",
          tree
        );

        setFiles(tree);

      } catch (err) {

        console.error(
          "Failed to load repository tree:",
          err
        );

        setError(
          "Failed to load repository tree."
        );

      } finally {

        setLoading(false);

      }
    }

    loadTree();

  }, [repository]);


  async function handleSelectFile(
    path: string
  ) {

    console.log(
      "Selected file path:",
      path
    );


    if (!path) {

      console.error(
        "No file path was provided."
      );

      return;
    }


    if (!repository) {

      console.error(
        "No repository is currently selected."
      );

      return;
    }


    try {

      setSelectedFilePath(path);

      setFileContent("");

      setReviewLine(null);


      const file =
        await getFileContent(
          repository.owner,
          repository.repo,
          path
        );


      if (!file || !file.content) {

        throw new Error(
          "File content was not returned."
        );

      }


      const decoded =
        Base64.decode(
          file.content
        );


      setFileContent(decoded);

    } catch (err) {

      console.error(
        "Failed to load file:",
        err
      );

      setFileContent(
        "Unable to load file."
      );

    }
  }


  function handleApplyCode(
    code: string
  ) {

    setFileContent(code);

  }


  async function handleReviewRepository() {

    if (!repository) return;


    try {

      setReviewing(true);

      setReviewError("");

      setReviewResult(null);

      setReviewLine(null);

      setFixError("");

      setFixingFinding(null);


      const result =
        await reviewRepository(
          repository.owner,
          repository.repo
        );


      setReviewResult(result);

    } catch (err) {

      console.error(
        "Failed to review repository:",
        err
      );


      setReviewError(
        err instanceof Error
          ? err.message
          : "Failed to review repository."
      );

    } finally {

      setReviewing(false);

    }
  }


  async function handleReviewFinding(
    filePath: string,
    lineStart: number | null
  ) {

    setReviewLine(lineStart);

    await handleSelectFile(
      filePath
    );

  }


  async function handleFixFinding(
    filePath: string,
    lineStart: number | null
  ) {

    if (!repository) return;


    try {

      setFixingFinding(filePath);

      setFixError("");

      setReviewLine(lineStart);


      /*
       * Load the file directly here instead of
       * relying on React state updating first.
       */
      setSelectedFilePath(filePath);

      setFileContent("");


      const file =
        await getFileContent(
          repository.owner,
          repository.repo,
          filePath
        );


      if (!file || !file.content) {

        throw new Error(
          "File content was not returned."
        );

      }


      const decoded =
        Base64.decode(
          file.content
        );


      setFileContent(decoded);


      /*
       * Generate a Fix proposal using the
       * existing AI code-action system.
       */
      const result =
        await generateCodeAction(
          repository.owner,
          repository.repo,
          filePath,
          decoded,
          "fix"
        );


      /*
       * CodeViewer currently starts code actions
       * from its own buttons.
       *
       * For now, store the generated result in
       * sessionStorage so CodeViewer can consume
       * the proposal on the next step.
       */
      sessionStorage.setItem(
        "devpilot_review_fix",
        JSON.stringify({
          filePath,
          lineStart,
          code: decoded,
          modifiedCode:
            result.modified_code,
        })
      );


      /*
       * Trigger a custom browser event so the
       * currently mounted CodeViewer can react
       * immediately.
       */
      window.dispatchEvent(
        new CustomEvent(
          "devpilot-review-fix",
          {
            detail: {
              filePath,
              lineStart,
              code: decoded,
              modifiedCode:
                result.modified_code,
            },
          }
        )
      );

    } catch (err) {

      console.error(
        "Failed to fix review finding:",
        err
      );


      setFixError(
        err instanceof Error
          ? err.message
          : "Failed to generate a fix."
      );

    } finally {

      setFixingFinding(null);

    }
  }


  if (!repository) {

    return (

      <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-10 text-center">

        <h1 className="text-3xl font-bold">
          No Repository Imported
        </h1>

        <p className="mt-4 text-zinc-400">
          Go back to the dashboard and
          import a repository.
        </p>

      </div>

    );

  }


  return (

    <div className="space-y-8">


      <RepositoryHeader
        repository={repository}
      />


      {/* Repository Review */}

      <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <div className="flex items-center gap-2">

              <Sparkles size={20} />

              <h2 className="text-xl font-bold">
                AI Code Review
              </h2>

            </div>


            <p className="mt-2 text-sm text-zinc-400">
              Analyze the repository for bugs,
              security issues, performance problems,
              and maintainability concerns.
            </p>

          </div>


          <button
            onClick={
              handleReviewRepository
            }
            disabled={reviewing}
            className="flex shrink-0 items-center justify-center gap-2 rounded-lg bg-zinc-100 px-5 py-2.5 text-zinc-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
          >

            {reviewing ? (

              <>

                <RefreshCw
                  size={18}
                  className="animate-spin"
                />

                Reviewing...

              </>

            ) : (

              <>

                <Sparkles size={18} />

                Review Repository

              </>

            )}

          </button>

        </div>


        {reviewError && (

          <div className="mt-5 rounded-2xl border border-red-700 bg-red-900/20 p-5 text-red-400">

            {reviewError}

          </div>

        )}


        {fixError && (

          <div className="mt-5 rounded-2xl border border-red-700 bg-red-900/20 p-5 text-red-400">

            {fixError}

          </div>

        )}

      </div>


      {loading && (

        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">

          Loading repository files...

        </div>

      )}


      {error && (

        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-8 text-red-400">

          {error}

        </div>

      )}


      {!loading && !error && (

        <>

          <div className="grid gap-6 xl:grid-cols-12">


            <div className="xl:col-span-3">

              <FileTree
                nodes={tree}
                onSelectFile={
                  handleSelectFile
                }
              />

            </div>


            <div className="xl:col-span-6">

              <CodeViewer
                owner={
                  repository.owner
                }
                repo={
                  repository.repo
                }
                file={
                  fileContent
                }
                fileName={
                  selectedFilePath
                }
                onApplyCode={
                  handleApplyCode
                }
                reviewLine={
                  reviewLine
                }
              />

            </div>


            <div className="xl:col-span-3">

              <AIChatPanel
                owner={
                  repository.owner
                }
                repo={
                  repository.repo
                }
                onSelectFile={
                  handleSelectFile
                }
              />

            </div>

          </div>


          {/* Review Results */}

          {reviewResult && (

            <div className="space-y-6">


              {/* Summary */}

              <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                <div className="flex items-center gap-2">

                  <Sparkles size={20} />

                  <h2 className="text-xl font-bold">
                    Repository Review
                  </h2>

                </div>


                <p className="mt-4 leading-7 text-zinc-300">

                  {reviewResult.summary}

                </p>

              </div>


              {/* Findings */}

              {reviewResult.findings.length > 0 ? (

                <div className="space-y-4">

                  <h2 className="text-xl font-bold">
                    Findings
                  </h2>


                  {reviewResult.findings.map(
                    (finding, index) => {

                      const findingKey =
                        `${finding.file_path}-${index}`;


                      const isFixing =
                        fixingFinding ===
                        finding.file_path;


                      return (

                        <div
                          key={
                            findingKey
                          }
                          className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6"
                        >

                          <div className="flex flex-col gap-4">


                            {/* Severity + Title */}

                            <div className="flex flex-wrap items-center gap-3">

                              <span
                                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                                  finding.severity ===
                                  "high"
                                    ? "bg-red-900/40 text-red-400"
                                    : finding.severity ===
                                      "medium"
                                    ? "bg-yellow-900/40 text-yellow-400"
                                    : "bg-zinc-800 text-zinc-400"
                                }`}
                              >

                                {
                                  finding.severity
                                }

                              </span>


                              <h3 className="text-lg font-semibold">

                                {
                                  finding.title
                                }

                              </h3>

                            </div>


                            {/* Description */}

                            <p className="leading-7 text-zinc-400">

                              {
                                finding.description
                              }

                            </p>


                            {/* File */}

                            <button
                              type="button"
                              onClick={() =>
                                handleReviewFinding(
                                  finding.file_path,
                                  finding.line_start
                                )
                              }
                              className="w-full rounded-xl bg-zinc-950 px-4 py-3 text-left transition hover:bg-zinc-800"
                            >

                              <p className="font-mono text-sm text-zinc-300">

                                {
                                  finding.file_path
                                }

                              </p>


                              {finding.line_start !==
                                null && (

                                <p className="mt-1 text-xs text-zinc-500">

                                  Lines{" "}

                                  {
                                    finding.line_start
                                  }


                                  {finding.line_end !==
                                    null &&
                                    finding.line_end !==
                                      finding.line_start
                                    ? `-${finding.line_end}`
                                    : ""}

                                </p>

                              )}


                              <p className="mt-2 text-xs text-zinc-600">

                                Click to open file

                              </p>

                            </button>


                            {/* Actions */}

                            <div className="flex flex-wrap gap-3">


                              {/* Fix with DevPilot */}

                              <button
                                type="button"
                                onClick={() =>
                                  handleFixFinding(
                                    finding.file_path,
                                    finding.line_start
                                  )
                                }
                                disabled={
                                  fixingFinding !==
                                    null ||
                                  reviewing
                                }
                                className="flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                              >

                                {isFixing ? (

                                  <>

                                    <RefreshCw
                                      size={17}
                                      className="animate-spin"
                                    />

                                    Generating Fix...

                                  </>

                                ) : (

                                  <>

                                    <Wrench
                                      size={17}
                                    />

                                    Fix with DevPilot

                                  </>

                                )}

                              </button>


                              {/* Open File */}

                              <button
                                type="button"
                                onClick={() =>
                                  handleReviewFinding(
                                    finding.file_path,
                                    finding.line_start
                                  )
                                }
                                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm transition hover:bg-zinc-700"
                              >

                                Open File

                              </button>

                            </div>

                          </div>

                        </div>

                      );

                    }
                  )}

                </div>

              ) : (

                <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                  <p className="text-zinc-400">

                    No significant issues were
                    identified in the reviewed code.

                  </p>

                </div>

              )}

            </div>

          )}


          <RepositoryStats
            stats={stats}
          />

        </>

      )}

    </div>

  );

}


export default Repository;