import { useState } from "react";
import { Plus, Trash2, RefreshCw, Briefcase } from "lucide-react";

import { useWorkspace } from "../../context/useWorkspace";
import {
  createWorkspace,
  deleteWorkspace,
} from "../../services/api";

function WorkspaceManagement() {
  const {
    workspaces,
    workspace,
    loading,
    error,
    setWorkspace,
    refreshWorkspaces,
  } = useWorkspace();

  const [workspaceName, setWorkspaceName] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");

  async function handleCreate() {
    if (!workspaceName.trim()) {
      setActionError("Enter a workspace name.");
      return;
    }

    try {
      setSaving(true);
      setActionError("");
      setMessage("");

      const newWorkspace = await createWorkspace(workspaceName.trim());

      await refreshWorkspaces();
      setWorkspace(newWorkspace);
      setWorkspaceName("");
      setMessage("Workspace created successfully.");
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to create workspace."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!workspace) return;

    if (
      !window.confirm(
        `Delete "${workspace.name}"? Its saved workspace state will also be deleted.`
      )
    ) {
      return;
    }

    try {
      setDeleting(true);
      setActionError("");
      setMessage("");

      await deleteWorkspace(workspace.id);
      await refreshWorkspaces();

      setMessage("Workspace deleted successfully.");
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to delete workspace."
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
      <div className="border-b border-zinc-800 px-4 py-4 sm:px-6 sm:py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <Briefcase className="h-4 w-4 text-blue-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-white">
              Workspace management
            </h2>
            <p className="mt-0.5 text-xs text-zinc-500">
              Create, switch, and manage your workspaces.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-5 p-4 sm:p-6">
        {loading ? (
          <p className="text-sm text-zinc-500">Loading workspaces...</p>
        ) : error ? (
          <p className="text-sm text-red-400">{error}</p>
        ) : (
          <>
            <div>
              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-500">
                Active workspace
              </label>

              <select
                value={workspace?.id ?? ""}
                onChange={(event) => {
                  const selected = workspaces.find(
                    (item) => item.id === event.target.value
                  );

                  if (selected) setWorkspace(selected);
                }}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500"
              >
                {workspaces.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="border-t border-zinc-800 pt-5">
              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-500">
                Create workspace
              </label>

              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  value={workspaceName}
                  onChange={(event) => setWorkspaceName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !saving) {
                      void handleCreate();
                    }
                  }}
                  placeholder="Enter workspace name"
                  maxLength={100}
                  className="min-w-0 flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-blue-500"
                />

                <button
                  type="button"
                  onClick={() => void handleCreate()}
                  disabled={saving}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
                >
                  <Plus className="h-4 w-4" />
                  {saving ? "Creating..." : "Create"}
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-3 border-t border-zinc-800 pt-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-200">
                  {workspace?.name ?? "No active workspace"}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {workspaces.length} workspace(s) available
                </p>
              </div>

              <button
                type="button"
                onClick={() => void handleDelete()}
                disabled={!workspace || deleting || workspaces.length <= 1}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-red-500/20 px-3 py-2 text-sm text-red-400 transition-colors hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Trash2 className="h-4 w-4" />
                {deleting ? "Deleting..." : "Delete active workspace"}
              </button>
            </div>

            {workspaces.length <= 1 && (
              <p className="text-xs text-zinc-600">
                Create another workspace before deleting the only existing one.
              </p>
            )}
          </>
        )}

        {message && (
          <p className="text-sm text-emerald-400">{message}</p>
        )}

        {actionError && (
          <p className="text-sm text-red-400">{actionError}</p>
        )}

        <button
          type="button"
          onClick={() => void refreshWorkspaces()}
          disabled={loading}
          className="inline-flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 disabled:opacity-50"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh workspaces
        </button>
      </div>
    </section>
  );
}

export default WorkspaceManagement;