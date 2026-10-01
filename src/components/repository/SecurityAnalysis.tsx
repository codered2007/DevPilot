import { useState } from "react";
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

interface SecurityFinding {
  id: string;
  dependency: string;
  version: string;
  resolved_version?: string;
  severity: string;
  summary: string;
  details?: string;
  aliases?: string[];
  ecosystem?: string;
  fixed_version?: string | null;
}

interface SecuritySummary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  unknown: number;
}

interface SecurityAnalysisResult {
  findings: SecurityFinding[];
  summary: SecuritySummary;
  scanned_dependencies: number;
  skipped_dependencies: number;
}

interface SecurityAnalysisProps {
  owner: string;
  repo: string;
}

const severityStyles: Record<
  string,
  {
    badge: string;
    icon: typeof ShieldAlert;
    iconColor: string;
  }
> = {
  CRITICAL: {
    badge:
      "border-red-900/60 bg-red-950/30 text-red-400",
    icon: ShieldAlert,
    iconColor: "text-red-400",
  },
  HIGH: {
    badge:
      "border-orange-900/60 bg-orange-950/30 text-orange-400",
    icon: ShieldAlert,
    iconColor: "text-orange-400",
  },
  MEDIUM: {
    badge:
      "border-yellow-900/60 bg-yellow-950/30 text-yellow-400",
    icon: AlertTriangle,
    iconColor: "text-yellow-400",
  },
  LOW: {
    badge:
      "border-blue-900/60 bg-blue-950/30 text-blue-400",
    icon: Bug,
    iconColor: "text-blue-400",
  },
  UNKNOWN: {
    badge:
      "border-zinc-800 bg-zinc-950 text-zinc-500",
    icon: Bug,
    iconColor: "text-zinc-500",
  },
};

export default function SecurityAnalysis({
  owner,
  repo,
}: SecurityAnalysisProps) {
  const [result, setResult] =
    useState<SecurityAnalysisResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedFinding, setExpandedFinding] =
    useState<string | null>(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/security-analysis/?owner=${encodeURIComponent(
          owner
        )}&repo=${encodeURIComponent(repo)}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Security analysis failed with status ${response.status}`
        );
      }

      const data: SecurityAnalysisResult =
        await response.json();

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to run security analysis."
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleFinding = (id: string) => {
    setExpandedFinding((current) =>
      current === id ? null : id
    );
  };

  const getSeverityStyle = (severity: string) => {
    return (
      severityStyles[severity.toUpperCase()] ??
      severityStyles.UNKNOWN
    );
  };

  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/60">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-zinc-800/80 bg-zinc-900/80 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/10">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Security Analysis
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Scan repository dependencies for known vulnerabilities.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={runAnalysis}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${
              loading ? "animate-spin" : ""
            }`}
          />

          {loading ? "Scanning..." : "Run Security Scan"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mt-5 rounded-xl border border-red-900/60 bg-red-950/20 p-4">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />

            <div>
              <p className="text-sm font-medium text-red-300">
                Security scan failed
              </p>

              <p className="mt-1 text-xs leading-5 text-red-400/70">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-7 p-5">
          {/* Statistics */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <p className="text-xs text-zinc-600">
                Scanned
              </p>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {result.scanned_dependencies}
              </p>

              <p className="mt-1 text-[10px] text-zinc-700">
                Dependencies checked
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <p className="text-xs text-zinc-600">
                Vulnerabilities
              </p>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {result.summary.total}
              </p>

              <p className="mt-1 text-[10px] text-zinc-700">
                Known findings
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <p className="text-xs text-zinc-600">
                High / Critical
              </p>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {result.summary.high +
                  result.summary.critical}
              </p>

              <p className="mt-1 text-[10px] text-zinc-700">
                Higher severity findings
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4">
              <p className="text-xs text-zinc-600">
                Skipped
              </p>

              <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                {result.skipped_dependencies}
              </p>

              <p className="mt-1 text-[10px] text-zinc-700">
                Dependencies not scanned
              </p>
            </div>
          </div>

          {/* Clean Result */}
          {result.findings.length === 0 && (
            <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/10 p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-emerald-300">
                    No known vulnerabilities found
                  </h3>

                  <p className="mt-1 text-xs leading-5 text-emerald-400/60">
                    The scanned dependency versions did not
                    return known vulnerabilities from the
                    security database.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Findings */}
          {result.findings.length > 0 && (
            <div>
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-zinc-200">
                    Vulnerability Findings
                  </h3>

                  <p className="mt-1 text-xs text-zinc-600">
                    Review detected security issues and
                    available fixes.
                  </p>
                </div>

                <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-[10px] font-medium text-zinc-500">
                  {result.findings.length}{" "}
                  {result.findings.length === 1
                    ? "finding"
                    : "findings"}
                </span>
              </div>

              <div className="space-y-2">
                {result.findings.map((finding) => {
                  const severity =
                    finding.severity.toUpperCase();

                  const style =
                    getSeverityStyle(severity);

                  const SeverityIcon = style.icon;

                  const isExpanded =
                    expandedFinding === finding.id;

                  return (
                    <div
                      key={finding.id}
                      className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950/40"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          toggleFinding(finding.id)
                        }
                        className="flex w-full items-center gap-3 p-4 text-left transition-colors hover:bg-zinc-900/70"
                      >
                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${style.badge}`}
                        >
                          <SeverityIcon
                            className={`h-3.5 w-3.5 ${style.iconColor}`}
                          />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-zinc-200">
                              {finding.dependency}
                            </span>

                            <span className="font-mono text-xs text-zinc-600">
                              {finding.resolved_version ||
                                finding.version}
                            </span>

                            <span
                              className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${style.badge}`}
                            >
                              {severity}
                            </span>
                          </div>

                          <p className="mt-1 line-clamp-2 text-xs leading-5 text-zinc-500">
                            {finding.summary}
                          </p>
                        </div>

                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 shrink-0 text-zinc-600" />
                        ) : (
                          <ChevronDown className="h-4 w-4 shrink-0 text-zinc-600" />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="border-t border-zinc-800/80 px-4 py-4">
                          <div className="space-y-5">
                            {finding.details && (
                              <div>
                                <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                                  Details
                                </p>

                                <p className="text-sm leading-6 text-zinc-400">
                                  {finding.details}
                                </p>
                              </div>
                            )}

                            <div className="grid gap-4 sm:grid-cols-2">
                              <div>
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                                  Ecosystem
                                </p>

                                <p className="mt-1 font-mono text-sm text-zinc-300">
                                  {finding.ecosystem ||
                                    "Unknown"}
                                </p>
                              </div>

                              <div>
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                                  Version
                                </p>

                                <p className="mt-1 font-mono text-sm text-zinc-300">
                                  {finding.resolved_version ||
                                    finding.version ||
                                    "Unknown"}
                                </p>
                              </div>
                            </div>

                            {finding.fixed_version && (
                              <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 p-3">
                                <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-500">
                                  Fixed Version
                                </p>

                                <p className="mt-1 font-mono text-sm text-emerald-300">
                                  {finding.fixed_version}
                                </p>
                              </div>
                            )}

                            {finding.aliases &&
                              finding.aliases.length > 0 && (
                                <div>
                                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-600">
                                    References
                                  </p>

                                  <div className="flex flex-wrap gap-1.5">
                                    {finding.aliases.map(
                                      (alias) => (
                                        <span
                                          key={alias}
                                          className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 font-mono text-[10px] text-zinc-500"
                                        >
                                          {alias}
                                        </span>
                                      )
                                    )}
                                  </div>
                                </div>
                              )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}