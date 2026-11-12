import { useCallback, useEffect, useState } from "react";
import {
  createWorkspace,
  getWorkspaces,
  type Workspace,
} from "../services/api";
import { WorkspaceContext } from "./WorkspaceContext";

interface WorkspaceProviderProps {
  children: React.ReactNode;
}

const STORAGE_PREFIX = "devpilot_workspace:";

export function WorkspaceProvider({
  children,
}: WorkspaceProviderProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [userLogin, setUserLogin] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshWorkspaces = useCallback(async () => {
    try {
      setError("");

      let availableWorkspaces = await getWorkspaces();

      if (availableWorkspaces.length === 0) {
        const newWorkspace = await createWorkspace("My Workspace");
        availableWorkspaces = [newWorkspace];
      }

      setWorkspaces(availableWorkspaces);

      setWorkspace((currentWorkspace) => {
        if (
          currentWorkspace &&
          availableWorkspaces.some(
            (item) => item.id === currentWorkspace.id
          )
        ) {
          return currentWorkspace;
        }

        const savedId = userLogin
          ? localStorage.getItem(
              `${STORAGE_PREFIX}${userLogin}`
            )
          : null;

        return (
          availableWorkspaces.find((item) => item.id === savedId) ??
          availableWorkspaces[0] ??
          null
        );
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load workspaces."
      );
    }
  }, [userLogin]);

  // Load authenticated user and restore their selected workspace.
  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const response = await fetch(
          "http://localhost:8000/auth/me",
          { credentials: "include" }
        );

        if (!response.ok) {
          throw new Error("Unable to authenticate user.");
        }

        const data = await response.json();
        const login = data?.user?.login;

        if (typeof login !== "string" || !login.trim()) {
          throw new Error("Invalid GitHub account.");
        }

        const normalizedLogin = login.toLowerCase();

        let availableWorkspaces = await getWorkspaces();

        if (availableWorkspaces.length === 0) {
          const newWorkspace = await createWorkspace("My Workspace");
          availableWorkspaces = [newWorkspace];
        }

        if (cancelled) return;

        setUserLogin(normalizedLogin);
        setWorkspaces(availableWorkspaces);

        const savedId = localStorage.getItem(
          `${STORAGE_PREFIX}${normalizedLogin}`
        );

        const selectedWorkspace =
          availableWorkspaces.find((item) => item.id === savedId) ??
          availableWorkspaces[0] ??
          null;

        setWorkspace(selectedWorkspace);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to initialize workspace."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  // Persist workspace selection for the authenticated account.
  useEffect(() => {
    if (!userLogin || !workspace) return;

    localStorage.setItem(
      `${STORAGE_PREFIX}${userLogin}`,
      workspace.id
    );
  }, [workspace, userLogin]);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        workspace,
        loading,
        error,
        setWorkspace,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}