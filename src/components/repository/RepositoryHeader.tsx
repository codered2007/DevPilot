import { useState } from "react";
import {
  Code2,
  ExternalLink,
  GitBranch,
  GitFork,
  LoaderCircle,
  Sparkles,
  Star,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { getRepositorySummary } from "../../services/api";

interface Props {
  repository: {
    owner: string;
    repo: string;
    name: string;
    description: string;
    stars: number;
    forks: number;
    branch: string;
    language: string;
  };
}

function RepositoryHeader({ repository }: Props) {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");

  async function analyzeRepository() {
    try {
      setLoading(true);
      setError("");

      const result = await getRepositorySummary(
        repository.owner,
        repository.repo
      );

      console.log(result.summary);
      setSummary(result.summary);
    } catch (err) {
      console.error(err);
      setError("Unable to analyze this repository.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Repository Header */}
      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-5 sm:p-6 lg:p-7">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between lg:gap-8">
          {/* Repository Information */}
          <div className="min-w-0 flex-1">
            {/* Breadcrumb */}
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-zinc-500">
                {repository.owner}
              </span>

              <span className="text-zinc-700">/</span>

              <span className="min-w-0 max-w-full truncate font-medium text-zinc-200">
                {repository.repo}
              </span>
            </div>

            {/* Title */}
            <div className="mt-4 flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
                <Code2 className="h-5 w-5 text-zinc-400" />
              </div>

              <h1
                className="min-w-0 truncate text-2xl font-bold tracking-tight text-white sm:text-3xl"
                title={repository.name}
              >
                {repository.name}
              </h1>
            </div>

            {/* Description */}
            {repository.description && (
              <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 sm:text-base">
                {repository.description}
              </p>
            )}

            {/* Repository Metadata */}
            <div className="mt-5 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-400 sm:px-3 sm:py-2 sm:text-sm">
                <Star className="h-3.5 w-3.5" />
                {repository.stars}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-400 sm:px-3 sm:py-2 sm:text-sm">
                <GitFork className="h-3.5 w-3.5" />
                {repository.forks}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-400 sm:px-3 sm:py-2 sm:text-sm">
                <GitBranch className="h-3.5 w-3.5" />
                {repository.branch}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-400 sm:px-3 sm:py-2 sm:text-sm">
                <Code2 className="h-3.5 w-3.5" />
                {repository.language || "Unknown"}
              </span>

              <a
                href={`https://github.com/${repository.owner}/${repository.repo}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 sm:px-3 sm:py-2 sm:text-sm"
              >
                GitHub
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          {/* Analyze Action */}
          <button
            type="button"
            onClick={analyzeRepository}
            disabled={loading}
            className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/10 transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50 lg:w-auto"
          >
            {loading ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                {summary
                  ? "Re-analyze"
                  : "Analyze Repository"}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-900/60 bg-red-950/20 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Repository Analysis */}
      {summary && (
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-5 sm:p-6 lg:p-7">
          <div className="mb-6 flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <Sparkles className="h-4 w-4 text-blue-400" />
            </div>

            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-white sm:text-xl">
                Repository Analysis
              </h2>

              <p className="mt-0.5 text-sm text-zinc-500">
                AI-generated overview of this codebase
              </p>
            </div>
          </div>

          <div className="prose prose-invert max-w-none overflow-x-auto prose-headings:text-white prose-p:text-zinc-300 prose-li:text-zinc-300 prose-a:text-blue-400">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {summary}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </>
  );
}

export default RepositoryHeader;