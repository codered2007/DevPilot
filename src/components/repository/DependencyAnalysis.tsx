import {
  AlertTriangle,
  Box,
  ChevronDown,
  ChevronUp,
  FileCode2,
  Package,
  RefreshCw,
  Server,
} from "lucide-react";
import { useState } from "react";

import {
  analyzeRepositoryDependencies,
  type Dependency,
  type DependencyAnalysisResponse,
} from "../../services/api";

interface DependencyAnalysisProps {
  owner: string;
  repo: string;
}

function getEcosystemIcon(ecosystem: string) {
  if (ecosystem === "npm") {
    return <Package className="h-4 w-4" />;
  }

  if (ecosystem === "pip") {
    return <Server className="h-4 w-4" />;
  }

  return <Box className="h-4 w-4" />;
}

function getScopeLabel(scope: string) {
  if (scope === "devDependencies") {
    return "Development";
  }

  if (scope === "optionalDependencies") {
    return "Optional";
  }

  if (scope === "peerDependencies") {
    return "Peer";
  }

  return "Runtime";
}

function DependencyRow({
  dependency,
}: {
  dependency: Dependency;
}) {
  return (
    <div className="grid grid-cols-[minmax(0,2fr)_minmax(100px,1fr)_110px_90px] items-center gap-4 border-b border-zinc-800/70 px-4 py-3 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="shrink-0 text-zinc-500">
            {getEcosystemIcon(dependency.ecosystem)}
          </span>

          <span
            className="truncate text-sm font-medium text-zinc-200"
            title={dependency.name}
          >
            {dependency.name}
          </span>
        </div>

        <div
          className="mt-1 truncate pl-6 text-[11px] text-zinc-600"
          title={dependency.manifest}
        >
          {dependency.manifest}
        </div>
      </div>

      <div className="truncate font-mono text-xs text-zinc-400">
        {dependency.version}
      </div>

      <div>
        <span className="inline-flex rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-[11px] text-zinc-500">
          {getScopeLabel(dependency.scope)}
        </span>
      </div>

      <div className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
        {dependency.ecosystem}
      </div>
    </div>
  );
}

export default function DependencyAnalysis({
  owner,
  repo,
}: DependencyAnalysisProps) {
  const [analysis, setAnalysis] =
    useState<DependencyAnalysisResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  async function runAnalysis() {
    setLoading(true);
    setError(null);

    try {
      const result = await analyzeRepositoryDependencies(
        owner,
        repo
      );

      setAnalysis(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze dependencies."
      );
    } finally {
      setLoading(false);
    }
  }

  const dependencies = analysis?.dependencies ?? [];

  const visibleDependencies = showAll
    ? dependencies
    : dependencies.slice(0, 12);

  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/60">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-zinc-800/80 bg-zinc-900/80 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <Package className="h-4 w-4 text-blue-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Dependency Analysis
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Inspect packages, ecosystems, manifests, and scopes.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={runAnalysis}
          disabled={loading}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${
              loading ? "animate-spin" : ""
            }`}
          />

          {loading
            ? "Analyzing..."
            : analysis
              ? "Refresh"
              : "Analyze"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mt-5 flex items-start gap-3 rounded-xl border border-red-900/60 bg-red-950/20 p-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />

          <div>
            <p className="text-sm font-medium text-red-300">
              Dependency analysis failed
            </p>

            <p className="mt-1 text-xs leading-5 text-red-400/70">
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysis && !loading && !error && (
        <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950">
            <Package className="h-5 w-5 text-zinc-600" />
          </div>

          <h3 className="mt-4 text-sm font-medium text-zinc-300">
            No dependency analysis yet
          </h3>

          <p className="mt-1 max-w-md text-xs leading-5 text-zinc-600">
            Analyze this repository to discover package manifests
            and dependency declarations.
          </p>
        </div>
      )}

      {/* Results */}
      {analysis && (
        <div className="p-5">
          {/* Summary */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <div className="flex items-center gap-2 text-xs text-zinc-600">
                <Package className="h-3.5 w-3.5" />
                Dependencies
              </div>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {analysis.summary.dependency_count}
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <div className="flex items-center gap-2 text-xs text-zinc-600">
                <FileCode2 className="h-3.5 w-3.5" />
                Manifests
              </div>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {analysis.summary.manifest_count}
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <div className="flex items-center gap-2 text-xs text-zinc-600">
                <Server className="h-3.5 w-3.5" />
                Ecosystems
              </div>

              <div className="mt-2 flex flex-wrap gap-1.5">
                {analysis.summary.ecosystems.map(
                  (ecosystem) => (
                    <span
                      key={ecosystem}
                      className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-400"
                    >
                      {ecosystem}
                    </span>
                  )
                )}
              </div>
            </div>
          </div>

          {/* Manifests */}
          <div className="mt-7">
            <div className="mb-3">
              <h3 className="text-sm font-medium text-zinc-200">
                Manifests
              </h3>

              <p className="mt-1 text-xs text-zinc-600">
                Dependency sources detected in the repository.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {analysis.manifests.map((manifest) => (
                <div
                  key={manifest.path}
                  className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/50 px-3 py-2"
                >
                  <span className="text-zinc-500">
                    {getEcosystemIcon(manifest.ecosystem)}
                  </span>

                  <span className="text-xs text-zinc-300">
                    {manifest.path}
                  </span>

                  <span className="rounded bg-zinc-900 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-zinc-600">
                    {manifest.ecosystem}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Dependency Table */}
          <div className="mt-7 overflow-hidden rounded-xl border border-zinc-800/80">
            <div className="grid grid-cols-[minmax(0,2fr)_minmax(100px,1fr)_110px_90px] gap-4 border-b border-zinc-800/80 bg-zinc-950/70 px-4 py-3 text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
              <span>Dependency</span>
              <span>Version</span>
              <span>Scope</span>
              <span>Ecosystem</span>
            </div>

            {visibleDependencies.map(
              (dependency, index) => (
                <DependencyRow
                  key={`${dependency.manifest}-${dependency.name}-${dependency.scope}-${index}`}
                  dependency={dependency}
                />
              )
            )}
          </div>

          {/* Show More */}
          {dependencies.length > 12 && (
            <button
              type="button"
              onClick={() =>
                setShowAll((current) => !current)
              }
              className="mx-auto mt-4 flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-2 text-xs font-medium text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-200"
            >
              {showAll ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" />
                  Show fewer
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" />
                  Show all {dependencies.length} dependencies
                </>
              )}
            </button>
          )}
        </div>
      )}
    </section>
  );
}