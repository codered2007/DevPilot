import {
  ArrowRight,
  FileCode2,
  FolderGit2,
  GitBranch,
  Star,
} from "lucide-react";
import { Link } from "react-router-dom";

import Button from "../ui/Button";

interface RepositoryCardProps {
  name: string;
  description: string;
  branch: string;
  stars: number;
  files: number;
  indexed: boolean;
}

function RepositoryCard({
  name,
  description,
  branch,
  stars,
  files,
  indexed,
}: RepositoryCardProps) {
  return (
    <Link
      to="/dashboard/repository"
      className="block"
    >
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-blue-500 hover:shadow-xl hover:shadow-blue-500/10">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <FolderGit2 className="text-blue-400" />

              <h2 className="text-xl font-semibold text-white">
                {name}
              </h2>
            </div>

            <p className="mt-3 text-zinc-400">
              {description}
            </p>
          </div>

          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              indexed
                ? "bg-green-500/20 text-green-400"
                : "bg-yellow-500/20 text-yellow-400"
            }`}
          >
            {indexed ? "Indexed" : "Indexing"}
          </span>
        </div>

        {/* Repository Info */}
        <div className="mt-6 flex flex-wrap gap-6 text-sm text-zinc-400">
          <div className="flex items-center gap-2">
            <GitBranch size={18} />
            <span>{branch}</span>
          </div>

          <div className="flex items-center gap-2">
            <Star size={18} />
            <span>{stars}</span>
          </div>

          <div className="flex items-center gap-2">
            <FileCode2 size={18} />
            <span>{files} files</span>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 flex items-center justify-between">
          <p className="text-sm text-zinc-500">
            Last analyzed 2 minutes ago
          </p>

          <Button
            variant="secondary"
            className="flex items-center gap-2"
          >
            Open Repository
            <ArrowRight size={16} />
          </Button>
        </div>
      </div>
    </Link>
  );
}

export default RepositoryCard;