import {
  ArrowUpRight,
  FileCode2,
  FolderGit2,
  GitBranch,
  Star,
} from "lucide-react";
import { Link } from "react-router-dom";

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
      className="group block h-full"
    >
      <article className="flex h-full min-h-[250px] flex-col rounded-xl border border-zinc-800 bg-[#111418] p-5 transition-all duration-200 hover:border-zinc-700 hover:bg-zinc-900/70 sm:p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
                <FolderGit2 className="h-[18px] w-[18px] text-blue-400" />
              </div>

              <div className="min-w-0">
                <h2
                  className="truncate text-base font-semibold text-white"
                  title={name}
                >
                  {name}
                </h2>

                <p className="mt-0.5 text-xs text-zinc-500">
                  GitHub repository
                </p>
              </div>
            </div>
          </div>

          <span
            className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${
              indexed
                ? "border-emerald-500/20 bg-emerald-500/[0.08] text-emerald-400"
                : "border-yellow-500/20 bg-yellow-500/[0.08] text-yellow-400"
            }`}
          >
            {indexed ? "Indexed" : "Indexing"}
          </span>
        </div>

        {/* Description */}
        <p className="mt-5 line-clamp-2 text-sm leading-6 text-zinc-400">
          {description || "No repository description available."}
        </p>

        {/* Repository metadata */}
        <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-zinc-800/70 pt-5 text-xs text-zinc-500">
          <span className="inline-flex items-center gap-2">
            <GitBranch className="h-3.5 w-3.5 text-zinc-600" />
            {branch}
          </span>

          <span className="inline-flex items-center gap-2">
            <Star className="h-3.5 w-3.5 text-zinc-600" />
            {stars}
          </span>

          <span className="inline-flex items-center gap-2">
            <FileCode2 className="h-3.5 w-3.5 text-zinc-600" />
            {files} files
          </span>
        </div>

        {/* Footer */}
        <div className="mt-auto flex items-center justify-between gap-4 pt-6">
          <span className="text-xs text-zinc-600">
            Ready to analyze
          </span>

          <span className="inline-flex items-center gap-2 text-sm font-medium text-zinc-300 transition-colors group-hover:text-white">
            Open repository

            <ArrowUpRight className="h-4 w-4 text-zinc-500 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-blue-400" />
          </span>
        </div>
      </article>
    </Link>
  );
}

export default RepositoryCard;