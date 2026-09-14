const API_URL = "http://127.0.0.1:8000";


export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}


export interface ChatResponse {
  response: string;
  sources: string[];
}


export async function importRepository(
  url: string
) {
  const response = await fetch(
    `${API_URL}/repositories/import`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        url,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      "Import failed"
    );
  }

  return response.json();
}


export async function getRepositoryTree(
  owner: string,
  repo: string
) {
  const response = await fetch(
    `${API_URL}/repositories/tree?owner=${encodeURIComponent(
      owner
    )}&repo=${encodeURIComponent(repo)}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch repository tree"
    );
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
    )}&path=${encodeURIComponent(path)}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch file"
    );
  }

  return response.json();
}


export async function chatWithAI(
  owner: string,
  repo: string,
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> {

  const response = await fetch(
    `${API_URL}/chat/`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        owner,
        repo,
        message,
        history,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      "AI request failed"
    );
  }

  return response.json();
}


export async function getRepositorySummary(
  owner: string,
  repo: string
) {
  const response = await fetch(
    `${API_URL}/summary?owner=${encodeURIComponent(
      owner
    )}&repo=${encodeURIComponent(repo)}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to analyze repository"
    );
  }

  return response.json();
}


export async function explainCode(
  owner: string,
  repo: string,
  filePath: string,
  code: string
) {
  const response = await fetch(
    `${API_URL}/explain/`,
    {
      method: "POST",

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
    throw new Error(
      "Code explanation failed"
    );
  }

  return response.json();
}


export interface CodeActionResponse {
  original_code: string;
  modified_code: string;
  action:
    | "fix"
    | "improve"
    | "refactor";
}


export async function generateCodeAction(
  owner: string,
  repo: string,
  filePath: string,
  code: string,
  action:
    | "fix"
    | "improve"
    | "refactor"
): Promise<CodeActionResponse> {

  const response = await fetch(
    `${API_URL}/code-actions/`,
    {
      method: "POST",

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
    throw new Error(
      "Failed to generate code action"
    );
  }

  return response.json();
}


export interface ApplyCodeResponse {
  message: string;
  owner: string;
  repo: string;
  file_path: string;
  action:
    | "fix"
    | "improve"
    | "refactor";
  branch: string;
  commit_sha: string;
  commit_url: string;
}


export async function applyCodeToGitHub(
  owner: string,
  repo: string,
  filePath: string,
  code: string,
  action:
    | "fix"
    | "improve"
    | "refactor"
): Promise<ApplyCodeResponse> {

  const response = await fetch(
    `${API_URL}/apply-code/`,
    {
      method: "POST",

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

    let message =
      "Failed to apply code to GitHub.";

    try {

      const error =
        await response.json();

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
  base: string = "main"
): Promise<PullRequestResponse> {
  const response = await fetch(`${API_URL}/pull-request/`, {
    method: "POST",
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
  });

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
  repo: string
): Promise<RepositoryReviewResponse> {
  const response = await fetch(
    `${API_URL}/repository-review/?owner=${encodeURIComponent(
      owner
    )}&repo=${encodeURIComponent(repo)}`,
    {
      method: "POST",
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