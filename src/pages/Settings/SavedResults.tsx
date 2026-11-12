
import { useEffect, useState } from "react";
import {
  Bookmark,
  Trash2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from "lucide-react";
import {
  deleteSavedResult,
  getSavedResults,
  type SavedResult,
  type SavedResultType,
} from "../../services/api";
import { useWorkspace } from "../../context/useWorkspace";

const resultTypes: {
  value: SavedResultType | "all";
  label: string;
}[] = [
  { value: "all", label: "All results" },
  { value: "summary", label: "Summaries" },
  { value: "review", label: "Reviews" },
  { value: "architecture", label: "Architecture" },
  { value: "dependency", label: "Dependencies" },
  { value: "security", label: "Security" },
];

function SavedResults() {
  const { workspace, loading: workspaceLoading } = useWorkspace();

  const [results, setResults] = useState<SavedResult[]>([]);
  const [filter, setFilter] = useState<SavedResultType | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadResults = async () => {
    if (workspaceLoading) return;

    if (!workspace?.id) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await getSavedResults(
        workspace.id,
        undefined,
        undefined,
        filter === "all" ? undefined : filter
      );

      setResults(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load saved results."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadResults();
  }, [filter, workspace?.id, workspaceLoading]);

  const handleDelete = async (id: string) => {
    if (!workspace?.id) {
      setError("Select a workspace first.");
      return;
    }

    if (!window.confirm("Delete this saved result permanently?")) {
      return;
    }

    setDeletingId(id);
    setError("");

    try {
      await deleteSavedResult(id, workspace.id);

      setResults((current) =>
        current.filter((result) => result.id !== id)
      );

      if (expandedId === id) {
        setExpandedId(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete saved result."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (timestamp: number) =>
    new Date(timestamp * 1000).toLocaleString();

  return (
    <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
      <div className="flex flex-col gap-4 border-b border-zinc-800 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <Bookmark className="h-4 w-4 text-blue-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-white">
              Saved Results
            </h2>
            <p className="mt-0.5 text-xs text-zinc-500">
              Your saved repository analyses and reports.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadResults()}
          disabled={loading || workspaceLoading}
          className="inline-flex w-fit items-center gap-2 rounded-lg border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition-colors hover:bg-zinc-900 disabled:opacity-50"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${
              loading ? "animate-spin" : ""
            }`}
          />
          Refresh
        </button>
      </div>

      <div className="border-b border-zinc-800/70 px-4 py-4 sm:px-6">
        <label
          htmlFor="saved-result-filter"
          className="mb-2 block text-xs font-medium text-zinc-500"
        >
          Filter by result type
        </label>

        <select
          id="saved-result-filter"
          value={filter}
          onChange={(event) =>
            setFilter(event.target.value as SavedResultType | "all")
          }
          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-blue-500 sm:max-w-xs"
        >
          {resultTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div className="p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-red-500/20 bg-red-500/[0.06] px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        {workspaceLoading || loading ? (
          <p className="py-8 text-center text-sm text-zinc-500">
            Loading saved results...
          </p>
        ) : !workspace ? (
          <div className="py-10 text-center">
            <Bookmark className="mx-auto h-7 w-7 text-zinc-700" />
            <p className="mt-3 text-sm font-medium text-zinc-300">
              No workspace selected
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Select a workspace to view its saved results.
            </p>
          </div>
        ) : results.length === 0 ? (
          <div className="py-10 text-center">
            <Bookmark className="mx-auto h-7 w-7 text-zinc-700" />
            <p className="mt-3 text-sm font-medium text-zinc-300">
              No saved results yet
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Save an analysis from a repository to see it here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((result) => {
              const expanded = expandedId === result.id;

              return (
                <div
                  key={result.id}
                  className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950/50"
                >
                  <div className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between sm:p-4">
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedId(expanded ? null : result.id)
                      }
                      className="min-w-0 flex-1 text-left"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-md border border-blue-500/20 bg-blue-500/[0.08] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-blue-400">
                          {result.result_type}
                        </span>
                        <span className="truncate text-sm font-medium text-zinc-200">
                          {result.title}
                        </span>
                      </div>

                      <p className="mt-2 truncate text-xs text-zinc-500">
                        {result.owner}/{result.repo}
                      </p>

                      <p className="mt-1 text-[11px] text-zinc-600">
                        Updated {formatDate(result.updated_at)}
                      </p>
                    </button>

                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedId(expanded ? null : result.id)
                        }
                        className="rounded-lg border border-zinc-800 p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white"
                        aria-label={
                          expanded ? "Collapse result" : "Expand result"
                        }
                      >
                        {expanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => void handleDelete(result.id)}
                        disabled={deletingId === result.id}
                        className="rounded-lg border border-zinc-800 p-2 text-zinc-500 transition-colors hover:border-red-500/30 hover:bg-red-500/[0.06] hover:text-red-400 disabled:opacity-50"
                        aria-label="Delete saved result"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {expanded && (
                    <div className="border-t border-zinc-800 p-3 sm:p-4">
                      <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/30 p-3 font-mono text-xs leading-6 text-zinc-300">
                        {JSON.stringify(result.content, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

export default SavedResults;
