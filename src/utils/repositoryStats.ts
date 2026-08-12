interface FileItem {
  path: string;
  type: string;
}

export function getRepositoryStats(
  files: FileItem[]
) {
  const stats = {
    folders: 0,
    files: 0,
    ts: 0,
    tsx: 0,
    js: 0,
    jsx: 0,
    json: 0,
    md: 0,
    py: 0,
    java: 0,
    cpp: 0,
    css: 0,
    html: 0,
  };

  for (const file of files) {
    if (file.type === "tree") {
      stats.folders++;
      continue;
    }

    stats.files++;

    const ext = file.path.split(".").pop()?.toLowerCase();

    switch (ext) {
      case "ts":
        stats.ts++;
        break;
      case "tsx":
        stats.tsx++;
        break;
      case "js":
        stats.js++;
        break;
      case "jsx":
        stats.jsx++;
        break;
      case "json":
        stats.json++;
        break;
      case "md":
        stats.md++;
        break;
      case "py":
        stats.py++;
        break;
      case "java":
        stats.java++;
        break;
      case "cpp":
        stats.cpp++;
        break;
      case "css":
        stats.css++;
        break;
      case "html":
        stats.html++;
        break;
    }
  }

  return stats;
}