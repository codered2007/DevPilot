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
    return <Package size={16} />;
  }

  if (ecosystem === "pip") {
    return <Server size={16} />;
  }

  return <Box size={16} />;
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
    <div className="grid grid-cols-[minmax(0,2fr)_minmax(100px,1fr)_110px_110px] items-center gap-4 border-b border-white/5 px-4 py-3 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-gray-200">
            {getEcosystemIcon(
              dependency.ecosystem
            )}
          </span>

          <span
            className="truncate text-sm font-medium text-white"
            title={dependency.name}
          >
            {dependency.name}
          </span>
        </div>

        <div
          className="mt-1 truncate text-xs text-gray-500"
          title={dependency.manifest}
        >
          {dependency.manifest}
        </div>
      </div>

      <div className="truncate font-mono text-xs text-gray-400">
        {dependency.version}
      </div>

      <div>
        <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-gray-400">
          {getScopeLabel(
            dependency.scope
          )}
        </span>
      </div>

      <div className="text-xs uppercase tracking-wide text-gray-500">
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
    useState<DependencyAnalysisResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [showAll, setShowAll] =
    useState(false);

  async function runAnalysis() {
    setLoading(true);
    setError(null);

    try {
      const result =
        await analyzeRepositoryDependencies(
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

  const dependencies =
    analysis?.dependencies ?? [];

  const visibleDependencies = showAll
    ? dependencies
    : dependencies.slice(0, 12);

  return (
    <section className="rounded-xl border border-white/10 bg-[#111111] shadow-lg">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <Package
              size={18}
              className="text-gray-300"
            />

            <h2 className="text-base font-semibold text-white">
              Dependency Analysis
            </h2>
          </div>

          <p className="mt-1 text-xs text-gray-500">
            Inspect package dependencies,
            ecosystems, manifests, and scopes.
          </p>
        </div>

        <button
          type="button"
          onClick={runAnalysis}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-gray-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={
              loading
                ? "animate-spin"
                : ""
            }
          />

          {loading
            ? "Analyzing..."
            : analysis
              ? "Refresh"
              : "Analyze"}
        </button>
      </div>

      {error && (
        <div className="mx-5 mt-5 flex items-start gap-3 rounded-lg border border-red-500/20 bg-red-500/5 p-4">
          <AlertTriangle
            size={17}
            className="mt-0.5 shrink-0 text-red-400"
          />

          <div>
            <p className="text-sm font-medium text-red-300">
              Dependency analysis failed
            </p>

            <p className="mt-1 text-xs text-red-300/70">
              {error}
            </p>
          </div>
        </div>
      )}

      {!analysis && !loading && !error && (
        <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
          <div className="mb-4 rounded-full border border-white/10 bg-white/5 p-4">
            <Package
              size={24}
              className="text-gray-400"
            />
          </div>

          <h3 className="text-sm font-medium text-gray-200">
            No dependency analysis yet
          </h3>

          <p className="mt-1 max-w-md text-xs leading-5 text-gray-500">
            Analyze this repository to discover
            package manifests and dependency
            declarations.
          </p>
        </div>
      )}

      {analysis && (
        <div className="p-5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Package size={14} />
                Dependencies
              </div>

              <p className="mt-2 text-2xl font-semibold text-white">
                {
                  analysis.summary
                    .dependency_count
                }
              </p>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <FileCode2 size={14} />
                Manifests
              </div>

              <p className="mt-2 text-2xl font-semibold text-white">
                {
                  analysis.summary
                    .manifest_count
                }
              </p>
            </div>

            <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Server size={14} />
                Ecosystems
              </div>

              <div className="mt-2 flex flex-wrap gap-2">
                {analysis.summary.ecosystems.map(
                  (ecosystem) => (
                    <span
                      key={ecosystem}
                      className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs font-medium uppercase text-gray-300"
                    >
                      {ecosystem}
                    </span>
                  )
                )}
              </div>
            </div>
          </div>

          <div className="mt-5">
            <h3 className="mb-3 text-sm font-medium text-gray-200">
              Manifests
            </h3>

            <div className="flex flex-wrap gap-2">
              {analysis.manifests.map(
                (manifest) => (
                  <div
                    key={manifest.path}
                    className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2"
                  >
                    {getEcosystemIcon(
                      manifest.ecosystem
                    )}

                    <span className="text-xs text-gray-300">
                      {manifest.path}
                    </span>

                    <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase text-gray-500">
                      {manifest.ecosystem}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="mt-6 overflow-hidden rounded-lg border border-white/10">
            <div className="grid grid-cols-[minmax(0,2fr)_minmax(100px,1fr)_110px_110px] gap-4 border-b border-white/10 bg-white/[0.03] px-4 py-3 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
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

          {dependencies.length > 12 && (
            <button
              type="button"
              onClick={() =>
                setShowAll((current) => !current)
              }
              className="mx-auto mt-4 flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-gray-300 transition hover:bg-white/10"
            >
              {showAll ? (
                <>
                  <ChevronUp size={14} />
                  Show fewer
                </>
              ) : (
                <>
                  <ChevronDown size={14} />
                  Show all{" "}
                  {dependencies.length}{" "}
                  dependencies
                </>
              )}
            </button>
          )}
        </div>
      )}
    </section>
  );
}