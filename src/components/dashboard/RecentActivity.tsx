
import { useEffect, useState } from "react";
import {
  Activity as ActivityIcon,
  CheckCircle2,
  CircleAlert,
  Clock3,
  ExternalLink,
  FolderGit2,
  Loader2,
  RefreshCw,
  X,
  Eye,
  FileCode2,
} from "lucide-react";

import {
  getRecentActivities,
  getActivity,
  type Activity,
} from "../../services/api";
import { useWorkspace } from "../../context/useWorkspace";

interface RecentActivityProps {
  onOpenRepository: (owner: string, repo: string) => void;
}

function getActivityUrl(activity: Activity): string | null {
  const url = activity.details.url ?? activity.details.commit_url;

  return typeof url === "string" && url.trim()
    ? url
    : null;
}

function getStatusLabel(status: Activity["status"]): string {
  switch (status) {
    case "success":
      return "Successful";
    case "failed":
      return "Failed";
    default:
      return "Running";
  }
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function isCodeField(key: string): boolean {
  return [
    "original_code",
    "modified_code",
    "explanation",
    "summary",
  ].includes(key);
}

function RecentActivity({
  onOpenRepository,
}: RecentActivityProps) {
  const { workspace } = useWorkspace();
  const workspaceId = workspace?.id;

  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedActivity, setSelectedActivity] =
    useState<Activity | null>(null);
  const [viewingId, setViewingId] = useState<string | null>(null);
  const [viewError, setViewError] = useState("");

  async function loadActivities() {
    if (!workspaceId) {
      setActivities([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const result = await getRecentActivities(workspaceId, 20);
      setActivities(result);
    } catch (err) {
      console.error("Failed to load recent activity:", err);
      setError("Unable to load recent activity.");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewResult(activityId: string) {
    if (!workspaceId) return;

    setViewerOpen(true);
    setSelectedActivity(null);
    setViewingId(activityId);
    setViewError("");

    try {
      const activity = await getActivity(activityId, workspaceId);
      setSelectedActivity(activity);
    } catch (err) {
      console.error("Failed to load activity result:", err);
      setViewError("Unable to load this activity result.");
    } finally {
      setViewingId(null);
    }
  }

  function closeViewer() {
    setViewerOpen(false);
    setSelectedActivity(null);
    setViewingId(null);
    setViewError("");
  }

  useEffect(() => {
    void loadActivities();
  }, [workspaceId]);

  return (
    <section className="min-w-0">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white">
            <ActivityIcon className="h-5 w-5 text-blue-400" />
            Recent activity
          </h2>

          <p className="mt-1 text-sm leading-5 text-zinc-500">
            Your latest analyses, code changes, and repository operations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadActivities()}
          disabled={loading}
          title="Refresh activity"
          className="rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-zinc-400 transition-colors hover:border-zinc-700 hover:text-white disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 text-sm text-zinc-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading recent activity...
        </div>
      ) : error ? (
        <div className="flex flex-col gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-5">
          <p className="text-sm text-red-400">{error}</p>

          <button
            type="button"
            onClick={() => void loadActivities()}
            className="w-fit text-sm font-medium text-blue-400 hover:text-blue-300"
          >
            Try again
          </button>
        </div>
      ) : activities.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 text-center">
          <Clock3 className="mx-auto h-7 w-7 text-zinc-600" />

          <p className="mt-3 text-sm font-medium text-zinc-300">
            No activity yet
          </p>

          <p className="mt-1 text-sm text-zinc-500">
            Your repository analyses and code operations will appear here.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-800/80 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/30">
          {activities.map((activity) => {
            const externalUrl = getActivityUrl(activity);
            const hasSavedDetails =
              Object.keys(activity.details ?? {}).length > 0;

            return (
              <div
                key={activity.id}
                className="flex min-w-0 flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex min-w-0 items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    {activity.status === "success" ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    ) : activity.status === "failed" ? (
                      <CircleAlert className="h-5 w-5 text-red-400" />
                    ) : (
                      <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                    )}
                  </div>

                  <div className="min-w-0">
                    <p className="break-words text-sm font-medium text-white">
                      {activity.title}
                    </p>

                    <p className="mt-1 flex items-center gap-1.5 truncate text-xs text-zinc-500">
                      <FolderGit2 className="h-3.5 w-3.5 shrink-0" />
                      {activity.owner}/{activity.repo}
                    </p>

                    <p className="mt-1.5 text-xs text-zinc-600">
                      {getStatusLabel(activity.status)}
                      {" · "}
                      {new Date(
                        activity.created_at * 1000
                      ).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex shrink-0 flex-wrap items-center gap-2 pl-8 sm:pl-0">
                  {activity.status === "success" && hasSavedDetails && (
                    <button
                      type="button"
                      onClick={() => void handleViewResult(activity.id)}
                      className="flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs font-medium text-blue-400 transition-colors hover:bg-blue-500/20"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      View result
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() =>
                      onOpenRepository(activity.owner, activity.repo)
                    }
                    className="rounded-lg border border-zinc-700 px-3 py-2 text-xs font-medium text-zinc-300 transition-colors hover:border-zinc-600 hover:bg-zinc-800"
                  >
                    Open repository
                  </button>

                  {externalUrl && (
                    <a
                      href={externalUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs font-medium text-blue-400 transition-colors hover:bg-blue-500/20"
                    >
                      Open result
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {viewerOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeViewer();
            }
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="activity-result-title"
            className="flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-950 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4 border-b border-zinc-800 p-5">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <FileCode2 className="h-5 w-5 shrink-0 text-blue-400" />
                  <h2
                    id="activity-result-title"
                    className="text-lg font-semibold text-white"
                  >
                    Saved activity result
                  </h2>
                </div>

                {selectedActivity && (
                  <>
                    <p className="mt-2 break-words text-sm text-zinc-300">
                      {selectedActivity.title}
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {selectedActivity.owner}/{selectedActivity.repo}
                    </p>
                  </>
                )}
              </div>

              <button
                type="button"
                onClick={closeViewer}
                aria-label="Close result viewer"
                className="shrink-0 rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              {viewingId ? (
                <div className="flex items-center justify-center gap-3 py-12 text-sm text-zinc-400">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Loading saved result...
                </div>
              ) : viewError ? (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-400">
                  {viewError}
                  <button
                    type="button"
                    onClick={() => {
                      if (selectedActivity) {
                        void handleViewResult(selectedActivity.id);
                      }
                    }}
                    className="ml-3 font-medium text-blue-400 hover:text-blue-300"
                  >
                    Try again
                  </button>
                </div>
              ) : selectedActivity ? (
                <div className="space-y-4">
                  {Object.entries(selectedActivity.details ?? {}).map(
                    ([key, value]) => {
                      const displayValue = formatValue(value);
                      const codeField = isCodeField(key);

                      return (
                        <div
                          key={key}
                          className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50"
                        >
                          <div className="border-b border-zinc-800 px-4 py-3">
                            <h3 className="text-sm font-semibold text-zinc-200">
                              {formatLabel(key)}
                            </h3>
                          </div>

                          {typeof value === "number" ||
                          typeof value === "boolean" ? (
                            <p className="px-4 py-3 text-sm text-zinc-200">
                              {displayValue}
                            </p>
                          ) : (
                            <pre
                              className={`max-h-[420px] overflow-auto whitespace-pre-wrap break-words p-4 text-sm leading-6 text-zinc-300 ${
                                codeField
                                  ? "bg-black/30 font-mono text-xs"
                                  : "font-sans"
                              }`}
                            >
                              {displayValue}
                            </pre>
                          )}
                        </div>
                      );
                    }
                  )}

                  {Object.keys(selectedActivity.details ?? {}).length === 0 && (
                    <p className="py-10 text-center text-sm text-zinc-500">
                      No saved result details are available for this activity.
                    </p>
                  )}
                </div>
              ) : null}
            </div>

            <div className="flex justify-end border-t border-zinc-800 p-4">
              <button
                type="button"
                onClick={closeViewer}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default RecentActivity;
