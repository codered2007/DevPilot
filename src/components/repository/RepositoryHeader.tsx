import { useState } from "react";
import {
  Sparkles,
  LoaderCircle,
  ExternalLink,
  GitFork,
  Star,
  GitBranch,
  Code2,
} from "lucide-react";
import { getRepositorySummary } from "../../services/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 lg:p-7">
        <div className="flex flex-col gap-7 lg:flex-row lg:items-start lg:justify-between">
          {/* Repository Information */}
          <div className="min-w-0">
            {/* Breadcrumb */}
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-zinc-500">{repository.owner}</span>

              <span className="text-zinc-700">/</span>

              <span className="font-medium text-zinc-200">
                {repository.repo}
              </span>
            </div>

            {/* Title */}
            <div className="mt-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
                <Code2 className="h-5 w-5 text-zinc-400" />
              </div>

              <h1 className="truncate text-3xl font-bold tracking-tight text-white">
                {repository.name}
              </h1>
            </div>

            {/* Description */}
            {repository.description && (
              <p className="mt-4 max-w-3xl leading-6 text-zinc-400">
                {repository.description}
              </p>
            )}

            {/* Repository Metadata */}
            <div className="mt-6 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400">
                <Star className="h-3.5 w-3.5" />
                {repository.stars}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400">
                <GitFork className="h-3.5 w-3.5" />
                {repository.forks}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400">
                <GitBranch className="h-3.5 w-3.5" />
                {repository.branch}
              </span>

              <span className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400">
                <Code2 className="h-3.5 w-3.5" />
                {repository.language || "Unknown"}
              </span>

              <a
                href={`https://github.com/${repository.owner}/${repository.repo}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200"
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
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/10 transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                {summary ? "Re-analyze" : "Analyze Repository"}
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
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 lg:p-7">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <Sparkles className="h-4 w-4 text-blue-400" />
            </div>

            <div>
              <h2 className="text-xl font-semibold text-white">
                Repository Analysis
              </h2>

              <p className="mt-0.5 text-sm text-zinc-500">
                AI-generated overview of this codebase
              </p>
            </div>
          </div>

          <div className="prose prose-invert max-w-none prose-headings:text-white prose-p:text-zinc-300 prose-li:text-zinc-300 prose-a:text-blue-400">
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