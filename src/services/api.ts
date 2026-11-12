
const API_URL = "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}
export interface Conversation {
  id: string;
  user_id: number;
  owner: string;
  repo: string;
  title: string;
  created_at: number;
  updated_at: number;
}

export interface ConversationHistoryMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sources: string[];
  created_at: number;
}
export interface RepositoryImportResponse {
  owner: string;
  repo: string;
  name: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  branch: string;
}

export async function importRepository(
  url: string
): Promise<RepositoryImportResponse> {
  const response = await fetch(
    `${API_URL}/repositories/import`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    }
  );

  if (!response.ok) {
    throw new Error("Import failed");
  }

  return response.json();
}

export interface RepositoryHistoryItem {
  owner: string;
  repo: string;
  name: string;
  description: string;
  last_opened_at: number;
}

export async function getRepositoryHistory(
  workspaceId: string
): Promise<RepositoryHistoryItem[]> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/repositories/history?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || "Failed to fetch repository history"
    );
  }

  const data = await response.json();
  return data.repositories;
}

export async function recordRepositoryOpen(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<void> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/repositories/history?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ owner, repo }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(
      error?.detail || "Failed to record repository history"
    );
  }
}


export async function getRepositoryTree(
  owner: string,
  repo: string
) {
  const response = await fetch(
    `${API_URL}/repositories/tree?owner=${encodeURIComponent(
      owner
    )}&repo=${encodeURIComponent(repo)}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch repository tree");
  }

  return response.json();
}

export async function getFileContent(
  owner: string,
  repo: string,
  path: string
) {
  const response = await fetch(
    `${API_URL}/repositories/file?owner=${encodeURIComponent(
      owner
    )}&repo=${encodeURIComponent(
      repo
    )}&path=${encodeURIComponent(path)}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch file");
  }

  return response.json();
}

export async function chatWithAI(
  owner: string,
  repo: string,
  message: string,
  history: ChatMessage[],
  conversationId: string,
  workspaceId: string
): Promise<ChatResponse> {
  const params = new URLSearchParams({ workspace_id: workspaceId });

  const response = await fetch(
    `${API_URL}/chat/?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo,
        message,
        history,
        conversation_id: conversationId,
      }),
    }
  );

  if (!response.ok) {
    let errorMessage = "AI request failed";

    try {
      const error = await response.json();
      if (error.detail) errorMessage = error.detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


export async function createConversation(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<Conversation> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/chat/conversations?${params}`,
    {
      method: "POST",
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to create conversation");
  }

  const data = await response.json();
  return data.conversation;
}


export async function getConversations(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<Conversation[]> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/chat/conversations?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to fetch conversations");
  }

  const data = await response.json();
  return data.conversations;
}

export async function getConversationMessages(
  conversationId: string,
  owner: string,
  repo: string,
  workspaceId: string
): Promise<ConversationHistoryMessage[]> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/chat/conversations/${encodeURIComponent(
      conversationId
    )}?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to fetch conversation messages");
  }

  const data = await response.json();
  return data.messages;
}


export async function deleteConversation(
  conversationId: string,
  owner: string,
  repo: string,
  workspaceId: string
): Promise<void> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/chat/conversations/${encodeURIComponent(
      conversationId
    )}?${params}`,
    {
      method: "DELETE",
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to delete conversation");
  }
}


export async function getRepositorySummary(
  owner: string,
  repo: string,
  workspaceId: string
) {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/summary/?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to analyze repository");
  }

  return response.json();
}



export async function explainCode(
  owner: string,
  repo: string,
  filePath: string,
  code: string,
  workspaceId: string
) {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/explain/?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo,
        file_path: filePath,
        code,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Code explanation failed");
  }

  return response.json();
}


export interface CodeActionResponse {
  original_code: string;
  modified_code: string;
  action: "fix" | "improve" | "refactor";
}


export async function generateCodeAction(
  owner: string,
  repo: string,
  filePath: string,
  code: string,
  action: "fix" | "improve" | "refactor",
  workspaceId: string
): Promise<CodeActionResponse> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/code-actions/?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo,
        file_path: filePath,
        code,
        action,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to generate code action");
  }

  return response.json();
}


export interface ApplyCodeResponse {
  message: string;
  owner: string;
  repo: string;
  file_path: string;
  action: "fix" | "improve" | "refactor";
  branch: string;
  base_branch: string;
  commit_sha: string;
  commit_url: string;
}


export async function applyCodeToGitHub(
  owner: string,
  repo: string,
  filePath: string,
  code: string,
  action: "fix" | "improve" | "refactor",
  workspaceId: string
): Promise<ApplyCodeResponse> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/apply-code/?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo,
        file_path: filePath,
        code,
        action,
      }),
    }
  );

  if (!response.ok) {
    let message = "Failed to apply code to GitHub.";

    try {
      const error = await response.json();

      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export interface PullRequestResponse {
  message: string;
  owner: string;
  repo: string;
  number: number;
  title: string;
  url: string;
  state: string;
  head: string;
  base: string;
}


export async function createPullRequest(
  owner: string,
  repo: string,
  title: string,
  body: string,
  head: string,
  base: string,
  workspaceId: string
): Promise<PullRequestResponse> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/pull-request/?${params}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo,
        title,
        body,
        head,
        base,
      }),
    }
  );

  if (!response.ok) {
    let message = "Failed to create Pull Request.";

    try {
      const error = await response.json();

      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export interface ReviewFinding {
  severity: "high" | "medium" | "low";
  title: string;
  description: string;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
}

export interface RepositoryReviewResponse {
  summary: string;
  findings: ReviewFinding[];
}


export async function reviewRepository(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<RepositoryReviewResponse> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/repository-review/?${params}`,
    {
      method: "POST",
      credentials: "include",
    }
  );

  if (!response.ok) {
    let message = "Failed to review repository.";

    try {
      const error = await response.json();

      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


/**
 * Repository Architecture Analysis
 */

export interface ArchitectureEntryPoint {
  file: string;
  reason: string;
}

export interface ArchitectureModule {
  name: string;
  paths: string[];
  description: string;
}

export interface ArchitectureDependency {
  source: string;
  target: string;
  type: string;
}

export interface ArchitectureAnalysisResponse {
  summary: string;
  entry_points: ArchitectureEntryPoint[];
  modules: ArchitectureModule[];
  dependencies: ArchitectureDependency[];
  observations: string[];
  unavailable_files: string[];
}


export async function analyzeRepositoryArchitecture(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<ArchitectureAnalysisResponse> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/architecture-analysis/?${params}`,
    {
      method: "POST",
      credentials: "include",
    }
  );

  if (!response.ok) {
    let message = "Failed to analyze repository architecture.";

    try {
      const error = await response.json();

      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


/**
 * Dependency Analysis
 */

export interface DependencyManifest {
  path: string;
  ecosystem: string;
}

export interface Dependency {
  name: string;
  version: string;
  scope: string;
  ecosystem: string;
  manifest: string;
}

export interface DependencyAnalysisSummary {
  manifest_count: number;
  dependency_count: number;
  ecosystems: string[];
}

export interface DependencyAnalysisResponse {
  manifests: DependencyManifest[];
  dependencies: Dependency[];
  summary: DependencyAnalysisSummary;
}


export async function analyzeRepositoryDependencies(
  owner: string,
  repo: string,
  workspaceId: string
): Promise<DependencyAnalysisResponse> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/dependency-analysis/?${params}`,
    {
      method: "POST",
      credentials: "include",
    }
  );

  if (!response.ok) {
    let message = "Failed to analyze repository dependencies.";

    try {
      const error = await response.json();

      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export interface Activity {
  id: string;
  user_id: number;
  owner: string;
  repo: string;
  action_type: string;
  title: string;
  status: "running" | "success" | "failed";
  details: Record<string, unknown>;
  created_at: number;
  completed_at: number | null;
}


export async function getRecentActivities(
  workspaceId: string,
  limit = 20
): Promise<Activity[]> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
    limit: String(limit),
  });

  const response = await fetch(
    `${API_URL}/activities/?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch recent activity");
  }

  const data: { activities: Activity[]; count: number } =
    await response.json();

  return data.activities;
}



export async function getRepositoryActivities(
  owner: string,
  repo: string,
  workspaceId: string,
  limit = 50
): Promise<Activity[]> {
  const params = new URLSearchParams({
    owner,
    repo,
    workspace_id: workspaceId,
    limit: String(limit),
  });

  const response = await fetch(
    `${API_URL}/activities/?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch repository activity");
  }

  const data: { activities: Activity[]; count: number } =
    await response.json();

  return data.activities;
}



export async function getActivity(
  activityId: string,
  workspaceId: string
): Promise<Activity> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/activities/${encodeURIComponent(activityId)}?${params}`,
    {
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch activity details");
  }

  const data: { activity: Activity } = await response.json();

  return data.activity;
}




export type SavedResultType =
  | "summary"
  | "review"
  | "architecture"
  | "dependency"
  | "security";

export interface SavedResult {
  id: string;
  user_id: number;
  workspace_id: string;
  owner: string;
  repo: string;
  result_type: SavedResultType;
  title: string;
  content: Record<string, unknown>;
  created_at: number;
  updated_at: number;
}

export interface SaveResultPayload {
  workspace_id: string;
  owner: string;
  repo: string;
  result_type: SavedResultType;
  title: string;
  content: Record<string, unknown>;
}

export async function saveResult(
  payload: SaveResultPayload
): Promise<SavedResult> {
  const response = await fetch(`${API_URL}/saved-results/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to save result.");
  }

  const data: { saved_result: SavedResult } = await response.json();
  return data.saved_result;
}

export async function getSavedResults(
  workspaceId: string,
  owner?: string,
  repo?: string,
  resultType?: SavedResultType
): Promise<SavedResult[]> {
  const params = new URLSearchParams();

  params.set("workspace_id", workspaceId);

  if (owner && repo) {
    params.set("owner", owner);
    params.set("repo", repo);
  }

  if (resultType) {
    params.set("result_type", resultType);
  }

  const response = await fetch(
    `${API_URL}/saved-results/?${params.toString()}`,
    { credentials: "include" }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to fetch saved results.");
  }

  const data: {
    saved_results: SavedResult[];
    count: number;
  } = await response.json();

  return data.saved_results;
}

export async function getSavedResult(
  resultId: string,
  workspaceId: string
): Promise<SavedResult> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/saved-results/${encodeURIComponent(resultId)}?${params.toString()}`,
    { credentials: "include" }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to fetch saved result.");
  }

  const data: { saved_result: SavedResult } = await response.json();
  return data.saved_result;
}

export async function deleteSavedResult(
  resultId: string,
  workspaceId: string
): Promise<void> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
  });

  const response = await fetch(
    `${API_URL}/saved-results/${encodeURIComponent(resultId)}?${params.toString()}`,
    {
      method: "DELETE",
      credentials: "include",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to delete saved result.");
  }
}

export interface UserPreferences {
  theme?: "dark" | "light" | "system";
  default_analysis?: "review" | "summary" | "architecture";
  response_detail?: "concise" | "balanced" | "detailed";
  notifications?: boolean;
  [key: string]: unknown;
}

export async function getUserPreferences(): Promise<UserPreferences> {
  const response = await fetch(`${API_URL}/preferences/`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch user preferences.");
  }

  const data: { preferences: UserPreferences } = await response.json();
  return data.preferences;
}

export async function updateUserPreferences(
  preferences: object
): Promise<UserPreferences> {
  const response = await fetch(`${API_URL}/preferences/`, {
    method: "PUT",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ preferences }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Failed to update user preferences.");
  }

  const data: { preferences: UserPreferences } = await response.json();
  return data.preferences;
}

export async function deleteUserPreferences(): Promise<void> {
  const response = await fetch(`${API_URL}/preferences/`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to delete user preferences.");
  }
}

export interface Workspace {
  id: string;
  user_id: number;
  name: string;
  created_at?: number;
  updated_at?: number;
}

export interface WorkspaceState {
  [key: string]: unknown;
}

export async function getWorkspaces(): Promise<Workspace[]> {
  const response = await fetch(`${API_URL}/workspaces`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch workspaces.");
  }

  const data: { workspaces: Workspace[] } = await response.json();
  return data.workspaces;
}

export async function createWorkspace(name: string): Promise<Workspace> {
  const response = await fetch(`${API_URL}/workspaces`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    throw new Error("Failed to create workspace.");
  }

  const data: { workspace: Workspace } = await response.json();
  return data.workspace;
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  const response = await fetch(
    `${API_URL}/workspaces/${encodeURIComponent(workspaceId)}`,
    {
      method: "DELETE",
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to delete workspace.");
  }
}

export async function getWorkspaceState(
  workspaceId: string
): Promise<WorkspaceState> {
  const response = await fetch(
    `${API_URL}/workspaces/${encodeURIComponent(workspaceId)}/state`,
    { credentials: "include" }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch workspace state.");
  }

  const data: { state: WorkspaceState } = await response.json();
  return data.state;
}

export async function updateWorkspaceState(
  workspaceId: string,
  stateKey: string,
  stateValue: Record<string, unknown>
): Promise<void> {
  const response = await fetch(
    `${API_URL}/workspaces/${encodeURIComponent(workspaceId)}/state/${encodeURIComponent(stateKey)}`,
    {
      method: "PUT",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ state_value: stateValue }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to update workspace state.");
  }
}

export async function deleteWorkspaceState(
  workspaceId: string,
  stateKey: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/workspaces/${encodeURIComponent(workspaceId)}/state/${encodeURIComponent(stateKey)}`,
    {
      method: "DELETE",
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to delete workspace state.");
  }
}