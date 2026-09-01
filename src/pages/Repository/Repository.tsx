import { useEffect, useState } from "react";
import { Base64 } from "js-base64";

import RepositoryHeader from "../../components/repository/RepositoryHeader";
import RepositoryStats from "../../components/repository/RepositoryStats";
import FileTree from "../../components/repository/FileTree";
import CodeViewer from "../../components/repository/CodeViewer";
import AIChatPanel from "../../components/repository/AIChatPanel";

import { useRepository } from "../../context/RepositoryContext";

import {
  getRepositoryTree,
  getFileContent,
} from "../../services/api";

import { buildFileTree } from "../../utils/buildFileTree";
import { getRepositoryStats } from "../../utils/repositoryStats";

interface FileItem {
  path: string;
  type: string;
}

function Repository() {
  const { repository } = useRepository();

  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedFilePath, setSelectedFilePath] = useState("");
  const [fileContent, setFileContent] = useState("");

  const tree = buildFileTree(files);
  const stats = getRepositoryStats(files);

  useEffect(() => {
    async function loadTree() {
      if (!repository) return;

      try {
        setLoading(true);
        setError("");

        const tree = await getRepositoryTree(
          repository.owner,
          repository.repo
        );

        console.log("Repository tree:", tree);

        setFiles(tree);
      } catch (err) {
        console.error("Failed to load repository tree:", err);
        setError("Failed to load repository tree.");
      } finally {
        setLoading(false);
      }
    }

    loadTree();
  }, [repository]);

  async function handleSelectFile(path: string) {
    console.log("Selected file path:", path);

    if (!path) {
      console.error("No file path was provided.");
      return;
    }

    if (!repository) {
      console.error("No repository is currently selected.");
      return;
    }

    try {
      setSelectedFilePath(path);
      setFileContent("");

      const file = await getFileContent(
        repository.owner,
        repository.repo,
        path
      );

      if (!file || !file.content) {
        throw new Error("File content was not returned.");
      }

      const decoded = Base64.decode(file.content);

      setFileContent(decoded);
    } catch (err) {
      console.error("Failed to load file:", err);
      setFileContent("Unable to load file.");
    }
  }

  if (!repository) {
    return (
      <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-10 text-center">
        <h1 className="text-3xl font-bold">
          No Repository Imported
        </h1>

        <p className="mt-4 text-zinc-400">
          Go back to the dashboard and import a repository.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <RepositoryHeader repository={repository} />

      {loading && (
        <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
          Loading repository files...
        </div>
      )}

      {error && (
        <div className="rounded-3xl border border-red-700 bg-red-900/20 p-8 text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="grid gap-6 xl:grid-cols-12">
            <div className="xl:col-span-3">
              <FileTree
                nodes={tree}
                onSelectFile={handleSelectFile}
              />
            </div>

            <div className="xl:col-span-6">
              <CodeViewer
                owner={repository.owner}
                repo={repository.repo}
                file={fileContent}
                fileName={selectedFilePath}
              />
            </div>

            <div className="xl:col-span-3">
              <AIChatPanel
                owner={repository.owner}
                repo={repository.repo}
              />
            </div>
          </div>

          <RepositoryStats stats={stats} />
        </>
      )}
    </div>
  );
}

export default Repository;
