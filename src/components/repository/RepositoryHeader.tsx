import { useState } from "react";
import { Sparkles, LoaderCircle } from "lucide-react";
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
      <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-4xl font-bold">
              {repository.name}
            </h1>

            <p className="mt-3 text-zinc-400">
              {repository.description}
            </p>

            <div className="mt-6 flex flex-wrap gap-4 text-sm">
              <div className="rounded-full bg-zinc-800 px-4 py-2">
                ⭐ {repository.stars}
              </div>

              <div className="rounded-full bg-zinc-800 px-4 py-2">
                🍴 {repository.forks}
              </div>

              <div className="rounded-full bg-zinc-800 px-4 py-2">
                🌿 {repository.branch}
              </div>

              <div className="rounded-full bg-zinc-800 px-4 py-2">
                💻 {repository.language}
              </div>
            </div>
          </div>

          <button
            onClick={analyzeRepository}
            disabled={loading}
            className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-medium transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <LoaderCircle
                  size={18}
                  className="animate-spin"
                />
                Analyzing Repository...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                {summary
                  ? "Re-Analyze"
                  : "Analyze Repository"}
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-red-700 bg-red-950/40 p-5 text-red-400">
          {error}
        </div>
      )}

      {summary && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
          <h2 className="mb-6 text-2xl font-bold">
            ✨ Repository Analysis
          </h2>

          <div className="prose prose-invert max-w-none prose-headings:text-white prose-p:text-zinc-300 prose-li:text-zinc-300">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
            >
              {summary}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </>
  );
}

export default RepositoryHeader;