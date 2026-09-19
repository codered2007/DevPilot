import { useEffect, useState } from "react";
import { Base64 } from "js-base64";

import RepositoryHeader from "../../components/repository/RepositoryHeader";
import RepositoryStats from "../../components/repository/RepositoryStats";
import FileTree from "../../components/repository/FileTree";
import CodeViewer from "../../components/repository/CodeViewer";
import AIChatPanel from "../../components/repository/AIChatPanel";

import { useRepository } from "../../context/useRepository";

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
  AlertTriangle,
  CircleAlert,
  CircleCheck,
  Download,
  RefreshCw,
  Sparkles,
  Wrench,
} from "lucide-react";


interface FileItem {
  path: string;
  type: string;
}


interface ReviewHistoryEntry
  extends RepositoryReviewResponse {
  reviewedAt: string;
}

type ReviewFindingStatus =
  | "open"
  | "acknowledged"
  | "in-progress"
  | "resolved";

type ReviewFindingStatuses = Record<string, ReviewFindingStatus>;


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


  /*
   * Review dashboard filter.
   */
  const [reviewFilter, setReviewFilter] =
    useState<
      "all" | "high" | "medium" | "low"
    >("all");


  /*
   * Review history.
   *
   * Reviews are stored locally per repository.
   */
  const [reviewHistory, setReviewHistory] =
    useState<ReviewHistoryEntry[]>([]);

  const [selectedHistoryIndex, setSelectedHistoryIndex] =
    useState<number | null>(null);

  const [findingStatuses, setFindingStatuses] =
    useState<ReviewFindingStatuses>({});

  const tree = buildFileTree(files);

  const stats = getRepositoryStats(files);


  /*
   * Normalize AI-generated severity values.
   * Gemini may return HIGH / Medium / low, so all dashboard
   * calculations use one canonical lowercase representation.
   */
  const normalizeSeverity = (severity: string) =>
    severity.toLowerCase() as "high" | "medium" | "low";


  /*
   * Derived review data.
   */
  const reviewFindings =
    reviewResult?.findings ?? [];


  const reviewCounts = {

    high: reviewFindings.filter(
      (finding) =>
        normalizeSeverity(finding.severity) === "high"
    ).length,

    medium: reviewFindings.filter(
      (finding) =>
        normalizeSeverity(finding.severity) === "medium"
    ).length,

    low: reviewFindings.filter(
      (finding) =>
        normalizeSeverity(finding.severity) === "low"
    ).length,

  };

  const comparisonIndex =
    selectedHistoryIndex ?? 0;

  const previousReview =
    reviewHistory[comparisonIndex + 1] ??
    null;


const previousReviewFindings =
  previousReview?.findings ?? [];


const getFindingKey = (
  finding: (typeof reviewFindings)[number]
) =>
  `${normalizeSeverity(finding.severity)}:${finding.file_path}:${finding.title}`;


  function getReviewFindingStatus(
    finding: (typeof reviewFindings)[number]
  ): ReviewFindingStatus {
    return findingStatuses[getFindingKey(finding)] ?? "open";
  }

  function handleFindingStatus(
    finding: (typeof reviewFindings)[number],
    status: ReviewFindingStatus
  ) {
    if (!repository) return;

    const key = getFindingKey(finding);
    const updatedStatuses = {
      ...findingStatuses,
      [key]: status,
    };

    const storageKey =
      `devpilot-review-status:${repository.owner}/${repository.repo}`;

    localStorage.setItem(
      storageKey,
      JSON.stringify(updatedStatuses)
    );

    setFindingStatuses(updatedStatuses);
  }


const currentFindingKeys =
  new Set(
    reviewFindings.map(
      getFindingKey
    )
  );


const previousFindingKeys =
  new Set(
    previousReviewFindings.map(
      getFindingKey
    )
  );


const newFindings =
  reviewFindings.filter(
    (finding) =>
      !previousFindingKeys.has(
        getFindingKey(finding)
      )
  );


const resolvedFindings =
  previousReviewFindings.filter(
    (finding) =>
      !currentFindingKeys.has(
        getFindingKey(finding)
      )
  );


const persistentFindings =
  reviewFindings.filter(
    (finding) =>
      previousFindingKeys.has(
        getFindingKey(finding)
      )
  );
  const reviewTrend =
    [...reviewHistory]
      .reverse()
      .map((entry) => {
        const high = entry.findings.filter(
          (finding) => normalizeSeverity(finding.severity) === "high"
        ).length;

        const medium = entry.findings.filter(
          (finding) => normalizeSeverity(finding.severity) === "medium"
        ).length;

        const low = entry.findings.filter(
          (finding) => normalizeSeverity(finding.severity) === "low"
        ).length;

        return {
          reviewedAt: entry.reviewedAt,
          total: entry.findings.length,
          high,
          medium,
          low,
        };
      });

  const latestTrend =
    reviewTrend.length > 0
      ? reviewTrend[reviewTrend.length - 1]
      : null;

  const previousTrend =
    reviewTrend.length > 1
      ? reviewTrend[reviewTrend.length - 2]
      : null;

  const trendDelta =
    latestTrend && previousTrend
      ? latestTrend.total - previousTrend.total
      : null;


  const filteredReviewFindings =
    reviewFindings.filter((finding) => {

      if (reviewFilter === "all") {
        return true;
      }

      return (
        normalizeSeverity(finding.severity) ===
        reviewFilter
      );

    });


  function handleExportReview() {

    if (!repository || !reviewResult) return;

    const reviewedAt =
      selectedHistoryIndex !== null && reviewHistory[selectedHistoryIndex]
        ? reviewHistory[selectedHistoryIndex].reviewedAt
        : new Date().toISOString();

    const lines = [
      `# DevPilot Repository Review`,
      ``,
      `Repository: ${repository.owner}/${repository.repo}`,
      `Reviewed: ${new Date(reviewedAt).toLocaleString()}`,
      ``,
      `## Overview`,
      ``,
      `- Total findings: ${reviewFindings.length}`,
      `- High: ${reviewCounts.high}`,
      `- Medium: ${reviewCounts.medium}`,
      `- Low: ${reviewCounts.low}`,
      ``,
      `## AI Summary`,
      ``,
      reviewResult.summary || "No summary was provided.",
      ``,
    ];

    if (previousReview) {
      lines.push(
        `## Comparison with Previous Review`,
        ``,
        `- New findings: ${newFindings.length}`,
        `- Resolved findings: ${resolvedFindings.length}`,
        `- Persistent findings: ${persistentFindings.length}`,
        ``,
      );
    }

    lines.push(`## Findings`, ``);

    reviewFindings.forEach((finding, index) => {
      const severity = normalizeSeverity(finding.severity).toUpperCase();
      const location = finding.line_start
        ? `${finding.file_path}:${finding.line_start}${finding.line_end ? `-${finding.line_end}` : ""}`
        : finding.file_path;

      lines.push(
        `### ${index + 1}. ${finding.title}`,
        ``,
        `- Severity: ${severity}`,
        `- Location: ${location}`,
        ``,
        finding.description,
        ``,
      );
    });

    const blob = new Blob([lines.join("\n")], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = `devpilot-review-${repository.repo}-${new Date(reviewedAt).toISOString().slice(0, 10)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }


  /*
   * Load review history whenever the
   * selected repository changes.
   */
  useEffect(() => {

    if (!repository) {
      setReviewHistory([]);
      setSelectedHistoryIndex(null);
      return;
    }


    const storageKey =
      `devpilot-review-history:${repository.owner}/${repository.repo}`;


    try {

      const stored =
        localStorage.getItem(storageKey);


      if (!stored) {

        setReviewHistory([]);
        setSelectedHistoryIndex(null);

        return;

      }


      const parsed =
        JSON.parse(stored);


      if (Array.isArray(parsed)) {

        setReviewHistory(
          parsed
        );

      } else {

        setReviewHistory([]);

      }


      setSelectedHistoryIndex(null);

    } catch (err) {

      console.error(
        "Failed to load review history:",
        err
      );

      setReviewHistory([]);
      setSelectedHistoryIndex(null);

    }

  }, [repository]);


  useEffect(() => {
    if (!repository) {
      setFindingStatuses({});
      return;
    }

    const storageKey =
      `devpilot-review-status:${repository.owner}/${repository.repo}`;

    try {
      const stored = localStorage.getItem(storageKey);

      if (!stored) {
        setFindingStatuses({});
        return;
      }

      const parsed = JSON.parse(stored);

      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        setFindingStatuses(parsed as ReviewFindingStatuses);
      } else {
        setFindingStatuses({});
      }
    } catch (err) {
      console.error(
        "Failed to load review finding statuses:",
        err
      );
      setFindingStatuses({});
    }
  }, [repository]);


  /*
   * Load repository tree.
   */
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


  /*
   * Select and load a repository file.
   */
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


  /*
   * Apply code from CodeViewer.
   */
  function handleApplyCode(
    code: string
  ) {

    setFileContent(code);

  }


  /*
   * Run repository review.
   */
  async function handleReviewRepository() {

    if (!repository) return;


    try {

      setReviewing(true);

      setReviewError("");

      setReviewResult(null);

      setReviewLine(null);

      setFixError("");

      setFixingFinding(null);

      setReviewFilter("all");

      setSelectedHistoryIndex(null);


      const result =
        await reviewRepository(
          repository.owner,
          repository.repo
        );


      /*
       * Save the completed review into
       * local history.
       */
      const storageKey =
        `devpilot-review-history:${repository.owner}/${repository.repo}`;


      const reviewEntry: ReviewHistoryEntry = {
        ...result,
        reviewedAt:
          new Date().toISOString(),
      };


      const updatedHistory = [
        reviewEntry,
        ...reviewHistory,
      ].slice(0, 5);


      localStorage.setItem(
        storageKey,
        JSON.stringify(
          updatedHistory
        )
      );


      setReviewHistory(
        updatedHistory
      );

      setSelectedHistoryIndex(0);

      setReviewResult(
        result
      );

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


  /*
   * Open the file associated with a
   * review finding.
   */
  async function handleReviewFinding(
    filePath: string,
    lineStart: number | null
  ) {

    setReviewLine(lineStart);

    await handleSelectFile(
      filePath
    );

  }


  /*
   * Generate an AI fix for a finding.
   */
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
       * Load the file directly here instead
       * of relying on React state updating first.
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
       * Store the generated result so
       * CodeViewer can consume it.
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
       * Trigger a custom browser event so
       * the currently mounted CodeViewer
       * can react immediately.
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


  /*
   * Restore an older review.
   */
  function handleRestoreReview(
    entry: ReviewHistoryEntry,
    index: number
  ) {

    setReviewResult(entry);

    setReviewFilter("all");

    setSelectedHistoryIndex(index);

    setReviewLine(null);

    setFixError("");

    setFixingFinding(null);

  }


  /*
   * Delete a single history entry.
   */
  function handleDeleteHistoryEntry(
    index: number
  ) {

    if (!repository) return;


    const storageKey =
      `devpilot-review-history:${repository.owner}/${repository.repo}`;


    const updatedHistory =
      reviewHistory.filter(
        (_, historyIndex) =>
          historyIndex !== index
      );


    localStorage.setItem(
      storageKey,
      JSON.stringify(
        updatedHistory
      )
    );


    setReviewHistory(
      updatedHistory
    );


    if (
      selectedHistoryIndex === index
    ) {

      setSelectedHistoryIndex(
        null
      );

    } else if (
      selectedHistoryIndex !== null &&
      selectedHistoryIndex > index
    ) {

      setSelectedHistoryIndex(
        selectedHistoryIndex - 1
      );

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


              {/* Review Overview */}

              <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                <div className="flex flex-col gap-5">

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

                    <div className="flex items-center gap-2">

                      <Sparkles size={20} />

                      <h2 className="text-xl font-bold">
                        Repository Review
                      </h2>

                    </div>

                    <button
                      type="button"
                      onClick={handleExportReview}
                      disabled={!reviewResult}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <Download size={16} />
                      Export Markdown
                    </button>

                  </div>


                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">


                    {/* Total */}

                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">

                      <div className="flex items-center justify-between">

                        <span className="text-sm text-zinc-400">
                          Total Findings
                        </span>

                        <AlertTriangle
                          size={19}
                          className="text-zinc-400"
                        />

                      </div>


                      <p className="mt-3 text-3xl font-bold">
                        {
                          reviewFindings.length
                        }
                      </p>

                    </div>


                    {/* High */}

                    <div className="rounded-2xl border border-red-900/50 bg-red-950/20 p-5">

                      <div className="flex items-center justify-between">

                        <span className="text-sm text-red-400">
                          High
                        </span>

                        <CircleAlert
                          size={19}
                          className="text-red-400"
                        />

                      </div>


                      <p className="mt-3 text-3xl font-bold text-red-400">
                        {
                          reviewCounts.high
                        }
                      </p>

                    </div>


                    {/* Medium */}

                    <div className="rounded-2xl border border-yellow-900/50 bg-yellow-950/20 p-5">

                      <div className="flex items-center justify-between">

                        <span className="text-sm text-yellow-400">
                          Medium
                        </span>

                        <AlertTriangle
                          size={19}
                          className="text-yellow-400"
                        />

                      </div>


                      <p className="mt-3 text-3xl font-bold text-yellow-400">
                        {
                          reviewCounts.medium
                        }
                      </p>

                    </div>


                    {/* Low */}

                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">

                      <div className="flex items-center justify-between">

                        <span className="text-sm text-zinc-400">
                          Low
                        </span>

                        <CircleCheck
                          size={19}
                          className="text-zinc-400"
                        />

                      </div>


                      <p className="mt-3 text-3xl font-bold text-zinc-300">
                        {
                          reviewCounts.low
                        }
                      </p>

                    </div>

                  </div>


                  {/* AI Summary */}

                  <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">

                    <div className="flex items-center gap-2">

                      <Sparkles
                        size={17}
                      />

                      <h3 className="font-semibold">
                        AI Summary
                      </h3>

                    </div>


                    <p className="mt-3 leading-7 text-zinc-300">

                      {
                        reviewResult.summary
                      }

                    </p>

                  </div>

                </div>

              </div>


              {/* Review History */}

              {reviewHistory.length > 0 && (

                <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                  <div className="flex flex-col gap-1">

                    <h2 className="text-xl font-bold">
                      Review History
                    </h2>

                    <p className="text-sm text-zinc-400">
                      Your five most recent repository
                      reviews are stored locally.
                    </p>

                  </div>


                  <div className="mt-5 space-y-3">

                    {reviewHistory.map(
                      (entry, index) => {

                        const entryFindings =
                          entry.findings ?? [];


                        const high =
                          entryFindings.filter(
                            (finding) =>
                              normalizeSeverity(finding.severity) ===
                              "high"
                          ).length;


                        const medium =
                          entryFindings.filter(
                            (finding) =>
                              normalizeSeverity(finding.severity) ===
                              "medium"
                          ).length;


                        const low =
                          entryFindings.filter(
                            (finding) =>
                              normalizeSeverity(finding.severity) ===
                              "low"
                          ).length;


                        const isSelected =
                          selectedHistoryIndex ===
                          index;


                        return (

                          <div
                            key={
                              `${entry.reviewedAt}-${index}`
                            }
                            className={`rounded-2xl border p-4 transition ${
                              isSelected
                                ? "border-zinc-500 bg-zinc-800/70"
                                : "border-zinc-800 bg-zinc-950"
                            }`}
                          >

                            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

                              <div>

                                <p className="text-sm font-medium text-zinc-200">

                                  {new Date(
                                    entry.reviewedAt
                                  ).toLocaleString()}

                                </p>


                                <p className="mt-1 text-xs text-zinc-500">

                                  {
                                    entryFindings.length
                                  }{" "}
                                  total findings

                                </p>

                              </div>


                              <div className="flex flex-wrap items-center gap-2">

                                <span className="rounded-full bg-red-900/40 px-3 py-1 text-xs font-medium text-red-400">

                                  High {high}

                                </span>


                                <span className="rounded-full bg-yellow-900/40 px-3 py-1 text-xs font-medium text-yellow-400">

                                  Medium {medium}

                                </span>


                                <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs font-medium text-zinc-400">

                                  Low {low}

                                </span>

                              </div>


                              <div className="flex gap-2">

                                <button
                                  type="button"
                                  onClick={() =>
                                    handleRestoreReview(
                                      entry,
                                      index
                                    )
                                  }
                                  className="rounded-lg bg-zinc-100 px-3 py-2 text-xs font-medium text-zinc-900 transition hover:bg-white"
                                >

                                  View Review

                                </button>


                                <button
                                  type="button"
                                  onClick={() =>
                                    handleDeleteHistoryEntry(
                                      index
                                    )
                                  }
                                  className="rounded-lg bg-zinc-800 px-3 py-2 text-xs text-zinc-400 transition hover:bg-zinc-700 hover:text-zinc-200"
                                >

                                  Delete

                                </button>

                              </div>

                            </div>

                          </div>

                        );

                      }
                    )}

                  </div>

                </div>

              )}


              {/* Review Comparison */}

              {previousReview && (

                <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                  <div className="flex flex-col gap-1">
                    <h2 className="text-xl font-bold">Review Comparison</h2>
                    <p className="text-sm text-zinc-400">Comparing this review with the previous repository review.</p>
                  </div>

                  <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                      <p className="text-sm text-zinc-400">Findings Change</p>
                      <div className="mt-2 flex items-end gap-2">
                        <p className="text-3xl font-bold">{reviewFindings.length}</p>
                        <p className="pb-1 text-sm text-zinc-500">from {previousReviewFindings.length}</p>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm text-zinc-400">New Findings</p>
                        <span className="rounded-full bg-red-900/40 px-2.5 py-1 text-xs font-semibold text-red-400">{newFindings.length}</span>
                      </div>
                      <p className="mt-2 text-sm text-zinc-500">Issues not present in the previous review.</p>
                    </div>

                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm text-zinc-400">Resolved Findings</p>
                        <span className="rounded-full bg-emerald-900/40 px-2.5 py-1 text-xs font-semibold text-emerald-400">{resolvedFindings.length}</span>
                      </div>
                      <p className="mt-2 text-sm text-zinc-500">Issues present before but absent now.</p>
                    </div>

                    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm text-zinc-400">Persistent Findings</p>
                        <span className="rounded-full bg-yellow-900/40 px-2.5 py-1 text-xs font-semibold text-yellow-400">{persistentFindings.length}</span>
                      </div>
                      <p className="mt-2 text-sm text-zinc-500">Findings that remain from the previous review.</p>
                    </div>
                  </div>

                  {(newFindings.length > 0 || resolvedFindings.length > 0) && (
                    <div className="mt-5 grid gap-4 lg:grid-cols-2">
                      {newFindings.length > 0 && (
                        <div className="rounded-2xl border border-red-900/40 bg-red-950/10 p-5">
                          <h3 className="font-semibold text-red-400">New Findings</h3>
                          <div className="mt-3 space-y-2">
                            {newFindings.slice(0, 5).map((finding, index) => (
                              <button key={`new-${finding.file_path}-${finding.title}-${index}`} type="button" onClick={() => handleReviewFinding(finding.file_path, finding.line_start)} className="w-full rounded-xl bg-zinc-950 px-4 py-3 text-left transition hover:bg-zinc-800">
                                <p className="text-sm font-medium text-zinc-200">{finding.title}</p>
                                <p className="mt-1 font-mono text-xs text-zinc-500">{finding.file_path}</p>
                              </button>
                            ))}
                          </div>
                          {newFindings.length > 5 && <p className="mt-3 text-xs text-zinc-500">+{newFindings.length - 5} more new findings</p>}
                        </div>
                      )}

                      {resolvedFindings.length > 0 && (
                        <div className="rounded-2xl border border-emerald-900/40 bg-emerald-950/10 p-5">
                          <h3 className="font-semibold text-emerald-400">Resolved Findings</h3>
                          <div className="mt-3 space-y-2">
                            {resolvedFindings.slice(0, 5).map((finding, index) => (
                              <div key={`resolved-${finding.file_path}-${finding.title}-${index}`} className="rounded-xl bg-zinc-950 px-4 py-3">
                                <p className="text-sm font-medium text-zinc-200">{finding.title}</p>
                                <p className="mt-1 font-mono text-xs text-zinc-500">{finding.file_path}</p>
                              </div>
                            ))}
                          </div>
                          {resolvedFindings.length > 5 && <p className="mt-3 text-xs text-zinc-500">+{resolvedFindings.length - 5} more resolved findings</p>}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}


              {/* Review Trend */}

              {reviewTrend.length > 0 && (
                <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                  <div className="flex flex-col gap-1">
                    <h2 className="text-xl font-bold">Review Trend</h2>
                    <p className="text-sm text-zinc-400">
                      Finding counts across your recent repository reviews.
                    </p>
                  </div>

                  <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">

                    <div className="flex min-h-52 items-end gap-3 overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                      {reviewTrend.map((entry, index) => {
                        const maxTotal = Math.max(
                          ...reviewTrend.map((item) => item.total),
                          1
                        );

                        const height = Math.max(
                          12,
                          (entry.total / maxTotal) * 100
                        );

                        return (
                          <div
                            key={`${entry.reviewedAt}-${index}`}
                            className="flex min-w-14 flex-1 flex-col items-center justify-end gap-2"
                            title={`${entry.total} findings — ${new Date(entry.reviewedAt).toLocaleString()}`}
                          >
                            <span className="text-xs font-semibold text-zinc-300">
                              {entry.total}
                            </span>

                            <div className="flex h-32 w-full items-end justify-center">
                              <div
                                className="w-full max-w-12 rounded-t-lg bg-zinc-700 transition hover:bg-zinc-600"
                                style={{ height: `${height}%` }}
                              />
                            </div>

                            <span className="text-[10px] text-zinc-500">
                              R{index + 1}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 lg:w-72 lg:grid-cols-1">

                      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                        <p className="text-sm text-zinc-400">
                          Latest Review
                        </p>
                        <p className="mt-2 text-3xl font-bold">
                          {latestTrend?.total ?? 0}
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {latestTrend
                            ? new Date(latestTrend.reviewedAt).toLocaleString()
                            : "No review yet"}
                        </p>
                      </div>

                      {trendDelta !== null && (
                        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
                          <p className="text-sm text-zinc-400">
                            Change vs Previous
                          </p>
                          <p className="mt-2 text-3xl font-bold">
                            {trendDelta > 0 ? "+" : ""}{trendDelta}
                          </p>
                          <p className="mt-1 text-xs text-zinc-500">
                            Total findings difference
                          </p>
                        </div>
                      )}

                    </div>

                  </div>

                </div>
              )}


              {/* Findings */}

              <div className="space-y-4">

                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                  <h2 className="text-xl font-bold">
                    Findings
                  </h2>


                  {/* Filters */}

                  <div className="flex flex-wrap gap-2">

                    <button
                      type="button"
                      onClick={() =>
                        setReviewFilter(
                          "all"
                        )
                      }
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                        reviewFilter ===
                        "all"
                          ? "bg-zinc-100 text-zinc-900"
                          : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                      }`}
                    >

                      All{" "}

                      {reviewFindings.length}

                    </button>


                    <button
                      type="button"
                      onClick={() =>
                        setReviewFilter(
                          "high"
                        )
                      }
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                        reviewFilter ===
                        "high"
                          ? "bg-red-500/20 text-red-400 ring-1 ring-red-500/40"
                          : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                      }`}
                    >

                      High{" "}

                      {reviewCounts.high}

                    </button>


                    <button
                      type="button"
                      onClick={() =>
                        setReviewFilter(
                          "medium"
                        )
                      }
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                        reviewFilter ===
                        "medium"
                          ? "bg-yellow-500/20 text-yellow-400 ring-1 ring-yellow-500/40"
                          : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                      }`}
                    >

                      Medium{" "}

                      {reviewCounts.medium}

                    </button>


                    <button
                      type="button"
                      onClick={() =>
                        setReviewFilter(
                          "low"
                        )
                      }
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                        reviewFilter ===
                        "low"
                          ? "bg-zinc-700 text-zinc-200 ring-1 ring-zinc-600"
                          : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                      }`}
                    >

                      Low{" "}

                      {reviewCounts.low}

                    </button>

                  </div>

                </div>


                {filteredReviewFindings.length > 0 ? (

                  filteredReviewFindings.map(
                    (finding) => {

                      const originalIndex =
                        reviewFindings.indexOf(
                          finding
                        );


                      const findingKey =
                        `${finding.file_path}-${originalIndex}`;


                      const isFixing =
                        fixingFinding ===
                        finding.file_path;


                      return (

                        <div
                          key={
                            findingKey
                          }
                          className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6 transition hover:border-zinc-700"
                        >

                          <div className="flex flex-col gap-5">


                            {/* Header */}

                            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">

                              <div className="flex items-start gap-3">

                                <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-zinc-800 px-2 text-xs font-semibold text-zinc-400">

                                  #
                                  {
                                    originalIndex +
                                    1
                                  }

                                </span>


                                <div>

                                  <div className="flex flex-wrap items-center gap-3">

                                    <span
                                      className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                                        normalizeSeverity(finding.severity) ===
                                        "high"
                                          ? "bg-red-900/40 text-red-400"
                                          : normalizeSeverity(finding.severity) ===
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

                                </div>

                              </div>

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

                              <div className="flex flex-col gap-1">

                                <p className="font-mono text-sm text-zinc-300">

                                  {
                                    finding.file_path
                                  }

                                </p>


                                {finding.line_start !==
                                  null && (

                                  <p className="text-xs text-zinc-500">

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


                                <p className="mt-1 text-xs text-zinc-600">

                                  Click to open file

                                </p>

                              </div>

                            </button>


                            {/* Workflow Status */}

                            <div className="flex flex-col gap-3 rounded-2xl border border-zinc-800 bg-zinc-950 p-4 sm:flex-row sm:items-center sm:justify-between">

                              <div>
                                <p className="text-xs uppercase tracking-wide text-zinc-500">
                                  Workflow Status
                                </p>
                                <p className="mt-1 text-sm text-zinc-400">
                                  Track your progress on this finding.
                                </p>
                              </div>

                              <div className="flex flex-wrap gap-2">
                                {[
                                  ["open", "Open"],
                                  ["acknowledged", "Acknowledged"],
                                  ["in-progress", "In Progress"],
                                  ["resolved", "Resolved"],
                                ].map(([status, label]) => {
                                  const active =
                                    getReviewFindingStatus(finding) === status;

                                  return (
                                    <button
                                      key={status}
                                      type="button"
                                      onClick={() =>
                                        handleFindingStatus(
                                          finding,
                                          status as ReviewFindingStatus
                                        )
                                      }
                                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                                        active
                                          ? "bg-zinc-100 text-zinc-900"
                                          : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                                      }`}
                                    >
                                      {label}
                                    </button>
                                  );
                                })}
                              </div>

                            </div>


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
                  )

                ) : (

                  <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">

                    <p className="text-zinc-400">

                      No findings match the
                      selected severity.

                    </p>

                  </div>

                )}

              </div>

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