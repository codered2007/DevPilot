import { useEffect, useRef } from "react";
import { useRepository } from "./useRepository";
import { useWorkspace } from "./useWorkspace";
import {
  getWorkspaceState,
  updateWorkspaceState,
} from "../services/api";

export function WorkspaceSync() {
  const { repository, setRepository } = useRepository();
  const { workspace, loading } = useWorkspace();

  const initializedWorkspace = useRef<string | null>(null);

  useEffect(() => {
    if (loading || !workspace) return;

    let cancelled = false;
    const activeWorkspace = workspace;

    async function initializeWorkspace() {
      try {
        const state = await getWorkspaceState(activeWorkspace.id);

        if (cancelled) return;

        const savedRepository = state.active_repository;

        if (
          savedRepository &&
          typeof savedRepository === "object" &&
          "owner" in savedRepository &&
          "repo" in savedRepository
        ) {
          setRepository(
            savedRepository as Parameters<typeof setRepository>[0]
          );
        } else if (repository) {
          await updateWorkspaceState(
            activeWorkspace.id,
            "active_repository",
            repository as unknown as Record<string, unknown>
          );
        }

        if (!cancelled) {
          initializedWorkspace.current = activeWorkspace.id;
        }
      } catch (error) {
        console.error("Workspace initialization failed:", error);
      }
    }

    if (initializedWorkspace.current !== activeWorkspace.id) {
      void initializeWorkspace();
    }

    return () => {
      cancelled = true;
    };
  }, [workspace, loading, setRepository]);

  useEffect(() => {
    if (
      loading ||
      !workspace ||
      initializedWorkspace.current !== workspace.id
    ) {
      return;
    }

    const stateValue = repository
      ? (repository as unknown as Record<string, unknown>)
      : {};

    updateWorkspaceState(
      workspace.id,
      "active_repository",
      stateValue
    ).catch((error) => {
      console.error("Failed to save workspace repository:", error);
    });
  }, [repository, workspace, loading]);

  return null;
}