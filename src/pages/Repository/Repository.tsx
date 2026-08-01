import { useEffect, useState } from "react";
import CodeViewer from "../../components/repository/CodeViewer";
import { useRepository } from "../../context/RepositoryContext";
import { getRepositoryTree } from "../../services/api";
import FileExplorer from "../../components/repository/FileExplorer";

interface FileItem {
  path: string;
  type: string;
}

function Repository() {
  const { repository } = useRepository();

  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedFile, setSelectedFile] =
  useState("");

  useEffect(() => {
    async function loadTree() {
      if (!repository) return;

      try {
        setLoading(true);

        const tree = await getRepositoryTree(
  repository.owner,
  repository.repo
);

        setFiles(tree);
      } catch (err) {
        console.error(err);
        setError("Failed to load repository tree.");
      } finally {
        setLoading(false);
      }
    }

    loadTree();
  }, [repository]);

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
      <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
        <h1 className="text-4xl font-bold">
          {repository.name}
        </h1>

        <p className="mt-3 text-zinc-400">
          {repository.description}
        </p>

        <div className="mt-8 flex flex-wrap gap-6 text-sm">
          <div className="rounded-full bg-zinc-800 px-4 py-2">
            ⭐ {repository.stars}
          </div>

          <div className="rounded-full bg-zinc-800 px-4 py-2">
            🍴 {repository.forks}
          </div>

          <div className="rounded-full bg-zinc-800 px-4 py-2">
            🌿 {repository.branch}
          </div>

          <div className="rounded-full bg-zinc-800 px-4 py-2">
            💻 {repository.language}
          </div>
        </div>
      </div>

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
        <div className="grid gap-6 xl:grid-cols-12">
  <div className="xl:col-span-4">
    <FileExplorer
      files={files}
      onSelectFile={setSelectedFile}
    />
  </div>

  <div className="xl:col-span-8">
    <CodeViewer file={selectedFile} />
  </div>
</div>
      )}
    </div>
  );
}

export default Repository;