const API_URL = "http://127.0.0.1:8000";

export async function importRepository(url: string) {
  const response = await fetch(
    `${API_URL}/repositories/import`,
    {
      method: "POST",
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

export async function getRepositoryTree(
  owner: string,
  repo: string
) {
  const response = await fetch(
    `${API_URL}/repositories/tree?owner=${owner}&repo=${repo}`
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
    `${API_URL}/repositories/file?owner=${owner}&repo=${repo}&path=${encodeURIComponent(path)}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch file");
  }

  return response.json();
}

export async function chatWithAI(
  owner: string,
  repo: string,
  message: string
) {
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
      }),
    }
  );

  if (!response.ok) {
    throw new Error("AI request failed");
  }

  return response.json();
}

export async function getRepositorySummary(
  owner: string,
  repo: string
) {
  const response = await fetch(
    `${API_URL}/summary?owner=${owner}&repo=${repo}`
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
    throw new Error("Code explanation failed");
  }

  return response.json();
}