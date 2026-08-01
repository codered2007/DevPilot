import {
  FolderGit2,
  GitBranch,
  Star,
  Clock3,
} from "lucide-react";

function RepositoryHeader() {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <FolderGit2 className="text-blue-400" />

            <h1 className="text-3xl font-bold">
              DevPilot
            </h1>
          </div>

          <p className="mt-3 text-zinc-400">
            AI Software Engineering Workspace
          </p>
        </div>

        <span className="rounded-full bg-green-500/20 px-4 py-2 text-sm text-green-400">
          Indexed
        </span>
      </div>

      <div className="mt-8 flex flex-wrap gap-8 text-zinc-400">
        <div className="flex items-center gap-2">
          <GitBranch size={18} />
          main
        </div>

        <div className="flex items-center gap-2">
          <Star size={18} />
          15
        </div>

        <div className="flex items-center gap-2">
          <Clock3 size={18} />
          Updated 2 mins ago
        </div>
      </div>
    </div>
  );
}

export default RepositoryHeader;