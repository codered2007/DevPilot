import { createContext } from "react";
import type { Workspace } from "../services/api";

export interface WorkspaceContextType {
  workspaces: Workspace[];
  workspace: Workspace | null;
  loading: boolean;
  error: string;
  setWorkspace: (workspace: Workspace | null) => void;
  refreshWorkspaces: () => Promise<void>;
}

export const WorkspaceContext =
  createContext<WorkspaceContextType | undefined>(undefined);