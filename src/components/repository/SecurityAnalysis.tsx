import { useState } from "react";
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
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
  { badge: string; icon: typeof ShieldAlert }
> = {
  CRITICAL: {
    badge: "bg-red-500/15 text-red-400 border-red-500/30",
    icon: ShieldAlert,
  },
  HIGH: {
    badge: "bg-orange-500/15 text-orange-400 border-orange-500/30",
    icon: ShieldAlert,
  },
  MEDIUM: {
    badge: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
    icon: AlertTriangle,
  },
  LOW: {
    badge: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    icon: Bug,
  },
  UNKNOWN: {
    badge: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
    icon: Bug,
  },
};

export default function SecurityAnalysis({
  owner,
  repo,
}: SecurityAnalysisProps) {
  const [result, setResult] = useState<SecurityAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);

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

      const data: SecurityAnalysisResult = await response.json();

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
    setExpandedFinding((current) => (current === id ? null : id));
  };

  const getSeverityStyle = (severity: string) => {
    return (
      severityStyles[severity.toUpperCase()] ?? severityStyles.UNKNOWN
    );
  };

  return (
    <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />

            <h2 className="text-lg font-semibold text-white">
              Security Analysis
            </h2>
          </div>

          <p className="mt-1 text-sm text-zinc-400">
            Scan repository dependencies for known vulnerabilities.
          </p>
        </div>

        <button
          onClick={runAnalysis}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.06] px-4 py-2 text-sm font-medium text-white transition hover:bg-white/[0.1] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />

          {loading ? "Scanning..." : "Run Security Scan"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />

            <div>
              <p className="font-medium text-red-300">
                Security scan failed
              </p>

              <p className="mt-1 text-sm text-red-300/80">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-6 space-y-5">
          {/* Scan statistics */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs text-zinc-500">Scanned</p>

              <p className="mt-1 text-2xl font-semibold text-white">
                {result.scanned_dependencies}
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs text-zinc-500">Vulnerabilities</p>

              <p className="mt-1 text-2xl font-semibold text-white">
                {result.summary.total}
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs text-zinc-500">High / Critical</p>

              <p className="mt-1 text-2xl font-semibold text-white">
                {result.summary.high + result.summary.critical}
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs text-zinc-500">Skipped</p>

              <p className="mt-1 text-2xl font-semibold text-white">
                {result.skipped_dependencies}
              </p>
            </div>
          </div>

          {/* Clean result */}
          {result.findings.length === 0 && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-5">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-emerald-400" />

                <div>
                  <h3 className="font-semibold text-emerald-300">
                    No known vulnerabilities found
                  </h3>

                  <p className="mt-1 text-sm text-emerald-300/70">
                    The scanned dependency versions did not return known
                    vulnerabilities from the security database.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Findings */}
          {result.findings.length > 0 && (
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-white">
                  Vulnerability Findings
                </h3>

                <span className="text-sm text-zinc-500">
                  {result.findings.length} finding
                  {result.findings.length === 1 ? "" : "s"}
                </span>
              </div>

              <div className="space-y-3">
                {result.findings.map((finding) => {
                  const severity = finding.severity.toUpperCase();
                  const style = getSeverityStyle(severity);
                  const SeverityIcon = style.icon;
                  const isExpanded =
                    expandedFinding === finding.id;

                  return (
                    <div
                      key={finding.id}
                      className="overflow-hidden rounded-xl border border-white/10 bg-black/10"
                    >
                      <button
                        onClick={() => toggleFinding(finding.id)}
                        className="flex w-full items-center gap-4 p-4 text-left transition hover:bg-white/[0.03]"
                      >
                        <SeverityIcon
                          className="h-5 w-5 shrink-0 text-zinc-400"
                        />

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-white">
                              {finding.dependency}
                            </span>

                            <span className="text-sm text-zinc-500">
                              {finding.resolved_version ||
                                finding.version}
                            </span>

                            <span
                              className={`rounded-md border px-2 py-0.5 text-xs font-medium ${style.badge}`}
                            >
                              {severity}
                            </span>
                          </div>

                          <p className="mt-1 line-clamp-2 text-sm text-zinc-400">
                            {finding.summary}
                          </p>
                        </div>

                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5 shrink-0 text-zinc-500" />
                        ) : (
                          <ChevronDown className="h-5 w-5 shrink-0 text-zinc-500" />
                        )}
                      </button>

                      {isExpanded && (
                        <div className="border-t border-white/10 px-4 py-4">
                          <div className="space-y-4">
                            {finding.details && (
                              <div>
                                <p className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-500">
                                  Details
                                </p>

                                <p className="text-sm leading-6 text-zinc-300">
                                  {finding.details}
                                </p>
                              </div>
                            )}

                            <div className="grid gap-4 sm:grid-cols-2">
                              <div>
                                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                                  Ecosystem
                                </p>

                                <p className="mt-1 text-sm text-zinc-300">
                                  {finding.ecosystem || "Unknown"}
                                </p>
                              </div>

                              <div>
                                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                                  Version
                                </p>

                                <p className="mt-1 text-sm text-zinc-300">
                                  {finding.resolved_version ||
                                    finding.version ||
                                    "Unknown"}
                                </p>
                              </div>
                            </div>

                            {finding.fixed_version && (
                              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
                                <p className="text-xs font-medium uppercase tracking-wide text-emerald-400">
                                  Fixed Version
                                </p>

                                <p className="mt-1 text-sm text-emerald-300">
                                  {finding.fixed_version}
                                </p>
                              </div>
                            )}

                            {finding.aliases &&
                              finding.aliases.length > 0 && (
                                <div>
                                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                                    References
                                  </p>

                                  <div className="flex flex-wrap gap-2">
                                    {finding.aliases.map((alias) => (
                                      <span
                                        key={alias}
                                        className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs text-zinc-400"
                                      >
                                        {alias}
                                      </span>
                                    ))}
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